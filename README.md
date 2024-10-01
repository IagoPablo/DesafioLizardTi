# Desafio LizardTi

## 📄 Descrição

No **Desafio LizardTi**, desenvolvi uma aplicação que implementa uma API utilizando **FastAPI**. Esta API é projetada para receber arquivos PDF, processá-los com a ajuda da IA Generativa Gemini e extrair informações relevantes. O foco central da aplicação está na **Engenharia de Prompt**, que visa ajustar as respostas da IA de acordo com os dados contidos no PDF, retornando um objeto JSON estruturado com as informações extraídas. O objetivo foi criar uma solução eficiente e acessível para análise de dados contidos em documentos PDF.

### 🏗️ Estrutura do Projeto

A aplicação foi desenvolvida utilizando duas plataformas:

- **Google Colab**: para o desenvolvimento e testes da API com FastAPI, permitindo interações diretas no ambiente do Colab.
- **Visual Studio Code**: para o desenvolvimento do front-end e integração com a API, proporcionando uma melhor experiência de desenvolvimento. (RECOMENDADO)

## 🎯 Algumas das Funcionalidades

- Receber e processar arquivos PDF.
- Integrar a API com uma IA Generativa para análise e extração de dados.
- Extrair informações do PDF e retornar em formato JSON estruturado.
- Armazenar resultados da interação no banco de dados MongoDB Atlas.
- Copiar ou baixar em formato JSON a resposta da IA (VS CODE)

## 🚀 Tecnologias Utilizadas

- **Backend**:
  - FastAPI
  - Uvicorn
  - AI Generativa (Gemini)

- **Banco de Dados**:
  - MongoDB Atlas

- **Frontend**:
  - React
  - CSS (para estilização)
  - React Icons (para ícones)

- **Ambientes de Desenvolvimento**:
  - VSCode (para desenvolvimento do front-end e integração com a API)
  - Google Colab (para desenvolvimento do backend e testes)

- **Controle de Versão**:
  - Git
  - GitHub

## 🛠️ Pré-requisitos

Antes de iniciar, certifique-se de ter instalado em sua máquina:

- [Python](https://www.python.org/) (versão 3.8 ou superior)
- [Node.js](https://nodejs.org/) (para eventuais ferramentas de frontend)
- [Git](https://git-scm.com/)
- Conta no [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) para gerenciamento do banco de dados

## 📥 Dependências

### 1. Visual Studio Code

Para garantir que todas as dependências do projeto sejam instaladas corretamente no VS Code, siga os passos abaixo:

- **Instalação das Dependências**:
  - Navegue até o diretório do projeto:
    ```bash
    cd DesafioLizardTi
    ```
  - Instale as dependências do backend usando o arquivo `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
  - Para o front-end, instale o pacote `react-icons`, que é utilizado para ícones:
    ```bash
    npm install react-icons
    ```

### 2. Google Colab

As dependências necessárias para o funcionamento da API e da interação com a IA estão documentadas diretamente no próprio notebook do Google Colab. Basta executar as células apropriadas para instalar as bibliotecas requeridas.


## 🔑 Configurações Adicionais

Antes de executar a aplicação, é importante configurar algumas informações sensíveis:

### 1. Chaves de API e String de Conexão do MongoDB

- **Chave da API do Gemini**: Insira sua chave de API da Gemini no código da aplicação. Certifique-se de que a chave esteja corretamente configurada para que a API funcione sem problemas.

- **String de Conexão do MongoDB**: A string de conexão para o MongoDB deve ser inserida no código. Não se esqueça de substituí-la pela sua string de conexão fornecida pelo MongoDB Atlas.

### 2. Configurações de IP no MongoDB

- No Google Colab, ao conectar-se ao MongoDB Atlas, pode ser necessário configurar o acesso ao banco de dados para aceitar conexões de IPs. Para realizar testes, você pode usar `0.0.0.0` para permitir acesso de todos os IPs, mas tenha em mente que isso não é recomendado para produção.

  - Acesse a seção de configurações do seu cluster no MongoDB Atlas e adicione `0.0.0.0/0` nas configurações de IP, permitindo que o Colab acesse seu banco de dados durante os testes.

  - Após os testes, é recomendável restringir o acesso apenas aos IPs necessários para garantir a segurança do seu banco de dados.

## 📦 Instalação

### 1. Clonar o Repositório

```bash
git clone https://github.com/IagoPablo/DesafioLizardTi.git
cd DesafioLizardTi
