# QueryX

QueryX is an AI-powered Retrieval-Augmented Generation (RAG) application that allows users to upload PDF documents and ask questions in natural language. It retrieves relevant information using Hybrid Search (Dense Embeddings + BM25 + RRF) and generates context-aware answers using Groq LLM.

## Features

- Upload and process PDF documents (with cancellation support)
- Automatic text extraction and chunking
- Hybrid Search (Dense + BM25 + Reciprocal Rank Fusion)
- AI-powered answer generation with Groq LLM
- Streaming responses
- Session-based chat memory
- Document management (List & Delete)
- Docker & Docker Compose support

---

## Tech Stack

**Backend**
- FastAPI
- Python 3.11+
- Qdrant
- Sentence Transformers (`BAAI/bge-small-en-v1.5`)
- Groq LLM (via OpenAI-compatible SDK)

**Frontend**
- HTML
- CSS
- Vanilla JavaScript

**Deployment**
- Docker
- Nginx

---

## Architecture

```
User
 │
 ▼
Frontend (Nginx)
 │  /api/*
 ▼
FastAPI Backend
 │
 ├── Hybrid Retrieval (Dense + BM25 + RRF)
 ├── Session Memory
 ├── Groq LLM
 │
 ▼
Qdrant Vector Store
```

---

## Project Structure

```
QueryX/
│
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI route handlers (upload, chat, search, documents)
│   │   ├── core/           # Configuration and logging
│   │   ├── db/             # Qdrant client & collection management
│   │   ├── llm/            # Groq client & prompt builder
│   │   ├── memory/         # Session conversation memory
│   │   ├── rag/            # Chunker, embeddings, BM25, RRF, hybrid pipeline
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── services/       # Document lifecycle service
│   │   ├── utils/          # PDF and text helpers
│   │   └── main.py         # FastAPI application entrypoint
│   ├── tests/              # Unit tests
│   ├── .env.example        # Environment variable template
│   ├── .dockerignore
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── api.js          # Backend API client
│   │   ├── app.js          # Core UI state, views, and file sidebar
│   │   ├── chat.js         # Chat rendering and streaming
│   │   ├── documents.js    # Initial document sync
│   │   └── upload.js       # PDF upload & cancellation lifecycle
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── index.html
│   └── nginx.conf
│
├── .gitignore
└── docker-compose.yml
```

---

## Installation (Local Development)

Clone the repository:

```bash
git clone https://github.com/yourusername/queryx.git
cd QueryX
```

### Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your Groq API key and QDRANT_URL (e.g. http://localhost:6333)

python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend: `http://localhost:8000`  
API Docs: `http://localhost:8000/docs`

### Frontend

Serve `frontend/` behind Nginx (or any static server that proxies `/api/` to the backend).

---

## Docker

Create `backend/.env` from `backend/.env.example`, then run:

```bash
docker compose build
docker compose up -d
```

Frontend: `http://localhost:3000`  
Backend: `http://localhost:8000`

Stop:

```bash
docker compose down
```

---

## Environment Variables

See `backend/.env.example`:

```env
HOST=0.0.0.0
PORT=8000
QDRANT_URL=http://qdrant:6333
COLLECTION_NAME=queryx_documents
API_KEY=your_groq_api_key
CHAT_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
HYBRID_TOP_K=20
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload & index PDF |
| POST | `/api/upload/cancel/{upload_id}` | Cancel active upload processing |
| POST | `/api/upload/stream` | Upload PDF with NDJSON progress stream |
| POST | `/api/chat` | Ask questions |
| POST | `/api/chat/stream` | Stream chat response |
| GET | `/api/search` | Semantic search over chunks |
| GET | `/api/documents` | List indexed documents |
| DELETE | `/api/documents/{id}` | Delete document |
| POST | `/api/documents/clear` | Clear session/all documents on close |
| GET | `/health` | Health check |
