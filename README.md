
# RAG Chatbot

An intelligent Q&A chatbot based on LangChain, Azure OpenAI, FAISS and Neo4j, supporting structured understanding and Q&A of products on [MadeWithNestle.ca](https://www.madewithnestle.ca/). The system integrates standard RAG and GraphRAG retrieval mechanisms, supports graphical query of brand, product, features, ingredients and nutritional information, and has real-time dialog capability, which is suitable for product recommendation, nutritional content query, and other scenarios.


## Tech Stack Overview

| Parts             | Tech/Frameworks                      |
|-------------------|--------------------------------------|
| Frontend          | React, Markdown render               |
| Backend           | Django, LangChain, REST API          |
| Vector Retrieve   | FAISS, Azure OpenAI Embedding Model  |
| Graph QA          | Neo4j, LangChain GraphRAG            |
| LLM Support       | Azure OpenAI GPT                     |
| Data Storage      | FAISS, Neo4j                         |
| Deployment        | Azure Web App, Azure Static Web Apps |


## Basic Project Structure

```
ChatBot/
├── chatbot/                # Django Basic App Initialization
├── config/                 # Django Configurations
├── frontend/               # React Frontend
├── rag/                    # Standard RAG modules (text chunking, vector search)
│   ├── faiss_index/        # Store the FAISS vector files
│   │   ├── index.faiss
│   │   └── index.pkl
├── graph/                  # GraphRAG Module with MVP (Support Neo4j Graph QA)
├── .env                    # Environmental variables (not provided)
├── manage.py
└── requirements.txt
```


## Core Functions
- **Vector Retrieval** with Azure OpenAI Embedding Models
- **Indexing** the product knowledge base using FAISS
- Leverage Neo4j to store brand and products related information maps and **access LangChain GraphRAG**.
- **Support markdown hyperlinks** for answer formatting
- React front-end support for **user-customized nicknames and avatars**.


## ⚠️ Limitations and Precautions

- Currently **only part of the brand and product information** on [MadeWithNestle.ca](https://www.madewithnestle.ca/) is scraped and supported, **not the full information from website**.
- Graph queries are based on **structured data that has already been parsed**, and will need to be **re-scraped** if the structure of the page changes.
- **LLM may generate context-independent answers**, it is recommended to add stricter context control logic in the deployment.
- React front-end default style is suitable for desktop browsing, **mobile style is not yet adapted**.


## Local Deployment
### 1. Clone Repository

```bash
git clone https://github.com/lewisning/ChatBot.git
cd ChatBot
```

### 2. Install Dependencies

```bash
# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 3. Configure Environmental Variables
Create an `.env` file in the root directory and fill it with the following (example):

```env
AZURE_OPENAI_API_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_EMBEDDING_NAME=embedding-model-name
AZURE_OPENAI_LLM_NAME=large-language-model-name
NEO4J_URI=bolt://localhost:7687 (or Aura Instance)
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

### 4. Start the app

```bash
# Start the backend
python3 manage.py runserver

# Start the frontend
cd frontend
npm start
```


## Author
Developed and maintained by [Xuyang (Lewis) Ning](https://www.linkedin.com/in/lewisning/)
