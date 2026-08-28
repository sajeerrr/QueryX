from dotenv import load_dotenv
from pathlib import Path
import os

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

QDRANT_URL = os.getenv("QDRANT_URL")

COLLECTION_NAME = os.getenv(
    "COLLECTION_NAME",
    "queryx_documents"
)

API_KEY = os.getenv("API_KEY")

CHAT_MODEL = os.getenv("CHAT_MODEL")

HYBRID_TOP_K = 20