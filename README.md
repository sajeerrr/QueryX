# QueryX

QueryX is an AI-powered Retrieval-Augmented Generation (RAG) application that allows users to upload PDF documents and ask questions in natural language. It retrieves relevant information using Hybrid Search and generates context-aware answers using LLM.

## Features

- Upload and process PDF documents
- Automatic text extraction and chunking
- Hybrid Search (Dense + BM25 + RRF)
- Query Rewriting
- AI-powered answer generation with LLM
- Streaming responses
- Session-based chat memory
- Confidence score
- Document management (List & Delete)
- Docker support

---

## Tech Stack

**Backend**
- FastAPI
- Python
- Qdrant
- Sentence Transformers
- Groq LLM

**Frontend**
- HTML
- CSS
- JavaScript

**Deployment**
- Docker
- Nginx

---

## Architecture

```
User
 │
 ▼
Frontend
 │
 ▼
FastAPI
 │
 ├── Query Rewriter
 ├── Hybrid Retrieval (Dense + BM25 + RRF)
 ├── Groq LLM
 │
 ▼
Qdrant
```

---

## Project Structure

```
QueryX/
│
├── backend/
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── css/
│   ├── js/
│   ├── index.html
│   ├── Dockerfile
│   └── nginx.conf
│
└── docker-compose.yml
```

---

## Installation

Clone the repository

```bash
git clone https://github.com/yourusername/queryx.git
cd queryx
```

### Backend

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend:

```
http://localhost:8000
```

API Docs:

```
http://localhost:8000/docs
```

### Frontend

Open `frontend/index.html` or serve it using any static web server.

---

## Docker

```bash
docker compose build

docker compose up -d
```

Stop:

```bash
docker compose down
```

---

## Environment Variables

```env
GROQ_API_KEY=your_api_key
QDRANT_URL=http://qdrant:6333
COLLECTION_NAME=queryx_documents
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload PDF |
| POST | `/api/chat` | Ask questions |
| GET | `/api/documents` | List documents |
| DELETE | `/api/documents/{id}` | Delete document |
| GET | `/health` | Health check |

---
