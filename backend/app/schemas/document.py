from pydantic import BaseModel


class ChunkResponse(BaseModel):
    id: int
    text: str


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    indexed_chunks: int
    chunks: list[ChunkResponse]