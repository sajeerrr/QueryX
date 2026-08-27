from dotenv import load_dotenv
import os

load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

QDRANT_URL = os.getenv("QDRANT_URL")

COLLECTION_NAME = os.getenv(
    "COLLECTION_NAME",
    "queryx_documents"
)

API_KEY = os.getenv("API_KEY")

CHAT_MODEL = os.getenv("CHAT_MODEL")


#for hybrid search
RERANK_TOP_K = 5

HYBRID_TOP_K = 20

RERANK_THRESHOLD = 0.2