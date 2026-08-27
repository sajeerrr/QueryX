from app.core.config import COLLECTION_NAME
from app.db.qdrant import client
from qdrant_client.http.models import Filter, FieldCondition, MatchValue


def list_documents():
    """
    Return one entry per indexed document.
    """

    response = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=1000,
        with_payload=True,
        with_vectors=False,
    )

    documents = {}

    for point in response[0]:

        payload = point.payload
        doc_id = payload["document_id"]

        if doc_id not in documents:

            documents[doc_id] = {
                "document_id": doc_id,
                "filename": payload["filename"],
                "chunks": 1,
            }

        else:
            documents[doc_id]["chunks"] += 1

    return list(documents.values())


def delete_document(document_id: str):

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        ),
    )

    return {
        "deleted": True,
        "document_id": document_id,
    }