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


# ==========================================
# PERFORMANCE OPTIMIZATIONS (Optional)
# ==========================================

# Set to False to disable multi-query generation
# Saves ~6-8 seconds per query but may reduce retrieval quality
ENABLE_MULTI_QUERY = os.getenv("ENABLE_MULTI_QUERY", "false").lower() == "true"

# Set to False to disable reranking
# Saves ~3-5 seconds per query but may reduce ranking quality
ENABLE_RERANKING = os.getenv("ENABLE_RERANKING", "false").lower() == "true"