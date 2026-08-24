from qdrant_client.models import VectorParams,Distance
from app.db.qdrant import client
from app.core.config import COLLECTION_NAME
from qdrant_client.models import PointStruct
from qdrant_client.models import Filter


VECTOR_SIZE = 4


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


def insert_demo_data():

    points = [
        PointStruct(
            id=1,
            vector=[1.0,0.0,0.0,0.0],
            payload={
                "text":"FastAPI is a modern Python framework."
            }
        ),
        PointStruct(
            id=2,
            vector=[0.0,1.0,0.0,0.0],
            payload={
                "text":"Qdrant stores vector embeddings."
            }
        ),
        PointStruct(
            id=3,
            vector=[0.0,0.0,1.0,0.0],
            payload={
                "text":"Grok is an LLM."
            }
        )
    ]

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )


def search_demo():

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=[1.0,0.0,0.0,0.0],
        limit=3
    )

    return results