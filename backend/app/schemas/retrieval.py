from pydantic import BaseModel
from typing import Optional


class RetrievedChunk(BaseModel):
    
    score: float
    document_id: str
    filename: str
    chunk_id: int
    text: str
    page: Optional[int] = None
    collection: Optional[str] = "default"
    source: Optional[str] = None