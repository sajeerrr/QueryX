from qdrant_client.models import Filter, FieldCondition, MatchValue


def build_filter(document_ids=None):

    if not document_ids:
        return None

    return Filter(
        should=[
            FieldCondition(
                key="document_id",
                match=MatchValue(value=doc_id)
            )
            for doc_id in document_ids
        ]
    )