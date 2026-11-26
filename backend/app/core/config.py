from dotenv import load_dotenv
from pathlib import Path
import os
import tempfile

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "queryx_documents")

API_KEY = os.getenv("API_KEY") or os.getenv("GROQ_API_KEY")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama-3.3-70b-versatile")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

HYBRID_TOP_K = int(os.getenv("HYBRID_TOP_K", 20))
EPHEMERAL_DOCUMENTS = os.getenv("EPHEMERAL_DOCUMENTS", "true").lower() in ("1", "true", "yes")

# Upload directory for PDF files
UPLOAD_DIR = Path(os.getenv("QUERYX_UPLOAD_DIR", Path(tempfile.gettempdir()) / "queryx_uploads"))

# Auto-delete settings for uploaded PDF files
AUTO_DELETE_AFTER_SECONDS = int(os.getenv("QUERYX_AUTO_DELETE_AFTER_SECONDS", 86400))  # 24 hours
AUTO_DELETE_CHECK_INTERVAL = int(os.getenv("QUERYX_AUTO_DELETE_CHECK_INTERVAL", 3600))  # 1 hour
