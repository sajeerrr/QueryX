# QueryX

QueryX is a full-stack Retrieval-Augmented Generation (RAG) web application for chatting with PDF documents. Upload a PDF, ask questions in natural language, and receive streamed, context-grounded answers powered by **Hybrid Search** (Dense Vector Search + BM25 + Reciprocal Rank Fusion) and **Groq LLM**.

---

## Features

- **In-Memory PDF Ingestion** — Extracts and cleans PDF text with PyMuPDF (`fitz`) and splits it into overlapping semantic chunks (`800` chars, `160` overlap) without saving raw PDFs to disk.
- **Fast Preloaded Embeddings** — Uses `BAAI/bge-small-en-v1.5` via Sentence Transformers, preloaded from local cache at server startup for sub-second document indexing.
- **Hybrid Search + RRF** — Combines dense semantic search in **Qdrant** with thread-safe **BM25** lexical search (`rank-bm25`), merged via **Reciprocal Rank Fusion (RRF)**.
- **Streaming Answers & Session Memory** — Streams responses token-by-token from **Groq** (`llama-3.3-70b-versatile` by default) while maintaining per-session conversation history.
- **Ephemeral Document Lifecycle** — Automatically clears uploaded document vectors, BM25 index, and session memory when you close the browser tab (`pagehide` / `beforeunload` beacon) or stop/restart the backend (`EPHEMERAL_DOCUMENTS=true`).
- **Upload Cancellation** — Supports stopping in-progress document uploads mid-flight with automatic rollback.
- **Docker & Local Dev Ready** — Runs seamlessly via Docker Compose (Nginx + FastAPI + Qdrant) or locally with `uvicorn` and a static frontend server (e.g. VS Code Live Server).

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend API** | FastAPI, Uvicorn, Python 3.11+ |
| **Vector Database** | Qdrant (`qdrant-client`) |
| **Embeddings** | Sentence Transformers (`BAAI/bge-small-en-v1.5`, 384-dim Cosine) |
| **Lexical Search** | `rank-bm25` (BM25Okapi) + Reciprocal Rank Fusion |
| **PDF & Chunking** | PyMuPDF (`fitz`), `langchain-text-splitters` |
| **LLM** | Groq API via OpenAI-compatible SDK |
| **Frontend** | Vanilla HTML, CSS, JavaScript |
| **Deployment** | Docker, Docker Compose, Nginx |

---

## Architecture

```
  Browser (Frontend)
     │
     ├── Static / Nginx (:3000 or :5500) ──► /api/* ──► FastAPI (:8000)
     │
     ▼
  FastAPI Backend
     ├── /api/upload        ──► PyMuPDF ──► Chunker ──► Embeddings ──► Qdrant + BM25
     ├── /api/chat(/stream) ──► Hybrid Search (Qdrant + BM25 + RRF) ──► Groq LLM
     ├── /api/search        ──► Qdrant Vector Search
     └── /api/documents     ──► List / Delete / Clear (Qdrant + BM25 + Memory)
```

---

## Project Structure

```text
QueryX/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py           # /api/chat and /api/chat/stream endpoints
│   │   │   ├── documents.py      # /api/documents, DELETE, and /clear endpoints
│   │   │   ├── search.py         # /api/search endpoint
│   │   │   └── upload.py         # /api/upload, /stream, and /cancel endpoints
│   │   ├── core/
│   │   │   ├── config.py         # Environment configuration
│   │   │   └── logger.py         # Structured stdout logging
│   │   ├── db/
│   │   │   └── qdrant.py         # Lazy Qdrant client & collection initialization
│   │   ├── llm/
│   │   │   ├── groq.py           # Groq completion & streaming client
│   │   │   └── prompt.py         # RAG prompt builder
│   │   ├── memory/
│   │   │   └── store.py          # Per-session conversation store & manager
│   │   ├── rag/
│   │   │   ├── bm25_index.py     # Thread-safe in-memory BM25 index
│   │   │   ├── chunker.py        # Recursive character splitter with cancellation
│   │   │   ├── embeddings.py     # Cached SentenceTransformer wrapper & preloader
│   │   │   ├── hybrid.py         # Hybrid dense + BM25 + RRF retrieval
│   │   │   ├── indexer.py        # Qdrant upsert + background BM25 rebuild
│   │   │   ├── pipeline.py       # End-to-end RAG run & streaming pipeline
│   │   │   ├── retriever.py      # Dense Qdrant retrieval & payload filters
│   │   │   └── rrf.py            # Reciprocal Rank Fusion
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/
│   │   │   └── document_service.py  # Ingestion, rollback, list, delete, clear
│   │   ├── utils/
│   │   │   ├── pdf.py            # PDF text extraction
│   │   │   └── text.py           # Text normalization
│   │   └── main.py               # FastAPI app & lifespan hooks
│   ├── tests/
│   │   └── test_core_and_rag.py  # Unit tests
│   ├── .dockerignore
│   ├── .env.example
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── css/style.css
│   ├── js/
│   │   ├── api.js                # API client (auto-routes :5500 -> :8000 or /api)
│   │   ├── app.js                # UI state, sidebar, drag-and-drop, unload cleanup
│   │   ├── chat.js               # Markdown rendering & streaming chat UI
│   │   ├── documents.js          # Initial document list sync
│   │   └── upload.js             # Upload progress & cancellation UI
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── index.html
│   └── nginx.conf
├── .gitignore
└── docker-compose.yml
```

---

## Getting Started

### Prerequisites

- **Groq API Key** (from [console.groq.com](https://console.groq.com))
- **Docker** (for running Qdrant or the full containerized stack)
- **Python 3.11+** (if running the backend locally)

### 1. Configure Environment Variables

Copy the example environment file and add your Groq API key:

```bash
cp backend/.env.example backend/.env
```

```env
HOST=0.0.0.0
PORT=8000

QDRANT_URL=http://localhost:6333
COLLECTION_NAME=queryx_documents

# Groq API key (GROQ_API_KEY is also supported)
API_KEY=your_groq_api_key
CHAT_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
HYBRID_TOP_K=20
EPHEMERAL_DOCUMENTS=true
```

---

### Option A: Run with Docker Compose

`docker-compose.yml` starts **Qdrant**, **FastAPI Backend**, and **Nginx Frontend** together (and overrides `QDRANT_URL=http://qdrant:6333` automatically):

```bash
docker compose up --build -d
```

- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **API Docs (Swagger)**: `http://localhost:8000/docs`

Stop containers:

```bash
docker compose down
```

---

### Option B: Run Locally (Development)

1. **Start Qdrant** (if not already running):

   ```bash
   docker compose up -d qdrant
   ```

2. **Start the Backend**:

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

3. **Open the Frontend**:

   Serve `frontend/index.html` using VS Code Live Server (e.g. `http://127.0.0.1:5500/frontend/index.html`) or any local static server. `frontend/js/api.js` automatically detects local dev ports (`5500`, `5173`, `8080`, etc.) and forwards API calls to port `8000`.

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Uvicorn bind host |
| `PORT` | `8000` | Uvicorn bind port |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `COLLECTION_NAME` | `queryx_documents` | Qdrant collection name |
| `API_KEY` / `GROQ_API_KEY` | — | Groq API key (**required** for chat) |
| `CHAT_MODEL` | `llama-3.3-70b-versatile` | Groq chat completion model |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | SentenceTransformer embedding model |
| `HYBRID_TOP_K` | `20` | Candidate chunks fetched per retriever before RRF |
| `EPHEMERAL_DOCUMENTS` | `true` | Clears Qdrant & BM25 on app startup/shutdown |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root status message |
| `GET` | `/health` | Health check |
| `POST` | `/api/upload` | Upload and index a PDF (`X-Upload-Id` supported) |
| `POST` | `/api/upload/stream` | Upload a PDF with NDJSON progress events |
| `POST` | `/api/upload/cancel/{upload_id}` | Cancel an active upload |
| `POST` | `/api/chat` | Ask a question (JSON answer + sources) |
| `POST` | `/api/chat/stream` | Stream an answer token-by-token (`text/plain`) |
| `GET` | `/api/search?query=...` | Semantic vector search over indexed chunks |
| `GET` | `/api/documents` | List currently indexed documents |
| `DELETE` | `/api/documents/{document_id}` | Delete a document from Qdrant & refresh BM25 |
| `POST` | `/api/documents/clear` | Clear session/all documents and chat memory |

---

## Running Tests

From the `backend/` directory:

```bash
python -m unittest discover -s tests -v
```
