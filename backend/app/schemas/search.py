from pydantic import BaseModel


class SearchResult(BaseModel):
    score: float
    chunk_id: int
    filename: str
    text: str


class SearchResponse(BaseModel):
    query: str
    total: int
    matches: list[SearchResult]