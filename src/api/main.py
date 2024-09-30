
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import google.generativeai as genai
import json
import fitz  # PyMuPDF
from pymongo import MongoClient
from bson import ObjectId
import logging
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do FastAPI e logging
app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do MongoDB
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["PdfProject"]  # Nome do seu banco de dados
collection = db["pdf_texts"]  #coleção onde você vai armazenar os textos
chat_collection = db["chat_history"]  #coleção para armazenar o histórico de chats
logger.info("Conexão com o MongoDB foi estabelecida com sucesso.")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Substitua "*" pelos domínios permitidos no futuro
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar o modelo da IA
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)  # Substitua pela sua chave de API
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',  # Ajustar para o modelo correto
    generation_config={
        'temperature': 0.5,
        'top_k': 0,
        'top_p': 0.95,
        'max_output_tokens': 2000
    },
    safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    }
)

# Modelo de dados para receber o JSON no corpo da requisição


class AskRequest(BaseModel):
    pdf_id: str = Field(..., example="60f6e8b3a5c28e0c401c81d2")
    question: str = Field(..., example="Qual é a empresa contratante?")

# Endpoint para upload de PDF
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    # Verificar se o arquivo é um PDF
    logger.info(f"Recebendo arquivo: {file.filename} com tipo: {file.content_type}")

    if file.content_type != "application/pdf":
        logger.warning(f"Arquivo enviado não é um PDF: {file.content_type}")
        raise HTTPException(status_code=400, detail="O arquivo enviado não é um PDF.")

    # Ler o conteúdo do PDF
    pdf_content = await file.read()
    logger.info(f"Conteúdo do PDF lido com sucesso. Tamanho: {len(pdf_content)} bytes")

    # Usar PyMuPDF para extrair texto do PDF
    document = fitz.open(stream=pdf_content, filetype="pdf")
    text = ""
    for page_num, page in enumerate(document):
        page_text = page.get_text()
        logger.info(f"Texto extraído da página {page_num}: {page_text[:100]}...")  # Logar os primeiros 100 caracteres
        text += page_text
    document.close()

    # Salvar o texto extraído no MongoDB
    if text:
        pdf_entry = {"text": text}
        result = collection.insert_one(pdf_entry)
        logger.info(f"Texto salvo no MongoDB com sucesso. ID do documento: {result.inserted_id}")

        # Retornar o texto extraído e o ID do documento no MongoDB
        return {"text": text, "pdf_id": str(result.inserted_id)}
    else:
        logger.warning("Nenhum texto foi extraído do PDF.")
        raise HTTPException(status_code=400, detail="Nenhum texto foi extraído do PDF.")

# Função para fazer perguntas à IA usando o texto do PDF
async def ask_gemini(text, question):
    # Iniciar a conversa com o modelo Gemini
    gemini = model.start_chat(history=[
        {
            'role': 'user',
            'parts': [
                {'text': json.dumps({"pdf_text": text})},
                {
                    'text': (
                        "Você é um especialista em informações extraídas de documentos. "
                        "Por favor, responda a pergunta a seguir **somente** no formato JSON sem qualquer outra formatação ou texto adicional. "
                        "Use exatamente as chaves \"resposta\", \"explicação\", e \"contexto\". "
                        "Por exemplo: {\"resposta\": \"sua resposta aqui\", \"explicação\": \"informações relevantes\", \"contexto\": \"contexto aqui\"}."
                    )
                },
                {'text': question}  # Adicionando a pergunta como parte do histórico
            ]
        }
    ])

    # Enviar a pergunta para a IA
    gemini.send_message(question)

    # Pegar a resposta da IA
    resposta = gemini.last.text.strip()  # Remove espaços em branco

    # Tentar converter a resposta para JSON
    try:
        # Se a resposta não for um JSON válido, tratar isso
        if resposta.startswith('```json'):
            resposta = resposta[7:-3].strip()  # Remove '```json' e '```' do início e do fim
        resposta_json = json.loads(resposta)

        # Retornar a resposta JSON diretamente
        return resposta_json  # Aqui garantimos que a resposta é um JSON válido.
    
    except json.JSONDecodeError:
        # Caso a IA não retorne um JSON válido, retornar uma estrutura padrão
        return {
            "resposta": "Desculpe, não consegui entender a resposta da IA.",
            "explicação": "",
            "contexto": ""
        }

@app.post("/ask/")
async def ask_about_pdf(request: AskRequest):
    # Recuperar o texto do PDF do MongoDB usando o ID fornecido no JSON
    pdf_entry = collection.find_one({"_id": ObjectId(request.pdf_id)})
    if not pdf_entry:
        return {"error": "PDF não encontrado."}

    pdf_text = pdf_entry["text"]

    # Chamar a função ask_gemini
    response = await ask_gemini(pdf_text, request.question)
    
    if "resposta" not in response or "explicação" not in response:
        raise HTTPException(status_code=500, detail="Resposta da IA está no formato inválido.")

    # Preparar o documento para inserir no chat_history
    chat_entry = {
        "pdf_id": ObjectId(request.pdf_id),
        "question": request.question,
        "resposta": response["resposta"],
        "explicação": response["explicação"],
        "timestamp": datetime.utcnow()
    }

    # Inserir no chat_history
    try:
        chat_collection.insert_one(chat_entry)
        logger.info("Interação salva no chat_history com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao salvar interação no chat_history: {e}")
        raise HTTPException(status_code=500, detail="Erro ao salvar interação no banco de dados.")

    # Retornar a resposta da IA diretamente, sem a chave "response"
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        body = await request.body()
        logger.info(f"Recebendo requisição em {request.url.path} com corpo: {body}")
    except Exception as e:
        logger.error(f"Erro ao ler o corpo da requisição: {e}")
    response = await call_next(request)
    return response