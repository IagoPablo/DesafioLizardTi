
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import google.generativeai as genai
import json
import fitz  #PyMuPDF
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
from typing import List

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do MongoDB
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI) #Inserir string de conexão MongoDB Atlas aqui.
db = client["PdfProject"]
collection = db["pdf_texts"]  
chat_collection = db["chat_history"]
logger.info("Conexão com o MongoDB foi estabelecida com sucesso.")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY) # Inserir gemini api key aqui
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config={
        'temperature': 0.6,
        'top_k': 0,
        'top_p': 0.95,
        'max_output_tokens': 2000
    },
    safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    }
)


class AskRequest(BaseModel):
    pdf_id: str = Field(..., example="60f6e8b3a5c28e0c401c81d2")
    question: str = Field(..., example="Qual é a empresa contratante?")


class Interaction(BaseModel):
    pdf_id: str = Field(..., example="60f6e8b3a5c28e0c401c81d2")
    question: str = Field(..., example="Qual é a empresa contratante?")
    response: dict = Field(..., example={"resposta": "empresa X", "explicação": "informações relevantes", "contexto": "contexto aqui"})

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    logger.info(f"Recebendo arquivo: {file.filename} com tipo: {file.content_type}")

    if file.content_type != "application/pdf":
        logger.warning(f"Arquivo enviado não é um PDF: {file.content_type}")
        raise HTTPException(status_code=400, detail="O arquivo enviado não é um PDF.")

    pdf_content = await file.read()
    logger.info(f"Conteúdo do PDF lido com sucesso. Tamanho: {len(pdf_content)} bytes")

    document = fitz.open(stream=pdf_content, filetype="pdf")
    text = ""
    for page_num, page in enumerate(document):
        page_text = page.get_text()
        logger.info(f"Texto extraído da página {page_num}: {page_text[:100]}...")
        text += page_text
    document.close()

    # Salvar o texto extraído no MongoDB
    if text:
        pdf_entry = {"text": text}
        result = collection.insert_one(pdf_entry)
        logger.info(f"Texto salvo no MongoDB com sucesso. ID do documento: {result.inserted_id}")

        return {"text": text, "pdf_id": str(result.inserted_id)}
    else:
        logger.warning("Nenhum texto foi extraído do PDF.")
        raise HTTPException(status_code=400, detail="Nenhum texto foi extraído do PDF.")

async def ask_gemini(text, question):

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
                {'text': question}
            ]
        }
    ])


    gemini.send_message(question)

    resposta = gemini.last.text.strip()

    try:

        if resposta.startswith('```json'):
            resposta = resposta[7:-3].strip()
        resposta_json = json.loads(resposta)


        return resposta_json
    
    except json.JSONDecodeError:
        return {
            "resposta": "Desculpe, não consegui entender a resposta da IA.",
            "explicação": "",
            "contexto": ""
        }

@app.post("/ask/")
async def ask_about_pdf(request: AskRequest):
    pdf_entry = collection.find_one({"_id": ObjectId(request.pdf_id)})
    if not pdf_entry:
        return {"error": "PDF não encontrado."}

    pdf_text = pdf_entry["text"]


    response = await ask_gemini(pdf_text, request.question)
    
    if "resposta" not in response or "explicação" not in response:
        raise HTTPException(status_code=500, detail="Resposta da IA está no formato inválido.")

    chat_entry = {
        "pdf_id": ObjectId(request.pdf_id),
        "question": request.question,
        "resposta": response["resposta"],
        "explicação": response["explicação"],
        "timestamp": datetime.utcnow()
    }

    try:
        chat_collection.insert_one(chat_entry)
        logger.info("Interação salva no chat_history com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao salvar interação no chat_history: {e}")
        raise HTTPException(status_code=500, detail="Erro ao salvar interação no banco de dados.")

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

class InteractionResponse(BaseModel):
    pdf_id: str
    question: str
    resposta: str
    explicação: str
    timestamp: datetime

@app.get("/interactions/", response_model=List[InteractionResponse])
async def get_interactions(pdf_id: str = None):
    if pdf_id:
        interactions = chat_collection.find({"pdf_id": ObjectId(pdf_id)})
    else:
        interactions = chat_collection.find()

    result = []
    for interaction in interactions:
        result.append(InteractionResponse(
            pdf_id=str(interaction["pdf_id"]),
            question=interaction["question"],
            resposta=interaction["resposta"],
            explicação=interaction["explicação"],
            timestamp=interaction["timestamp"]
        ))

    return result