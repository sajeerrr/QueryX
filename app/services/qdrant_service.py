from qdrant_client.models import VectorParams,Distance
from app.db.qdrant import client
from app.core.config import COLLECTION_NAME
from qdrant_client.models import PointStruct
from qdrant_client.models import Filter


VECTOR_SIZE = 384


def create_collection():

    collections = client.get_collections()
    names = [
        c.name
        for c in collections.collections
    ]

    if COLLECTION_NAME in names:
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )