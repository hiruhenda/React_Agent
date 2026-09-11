from typing import List, Optional
from pydantic import BaseModel, Field


# --- Tool 1: Calculator Schemas ---

class CalculateRequest(BaseModel):
    expression: str = Field(
        ...,
        description="Mathematical expression to evaluate safely (e.g., '14 * 24' or '68170000 / 357022')",
        examples=["14 * 24"],
    )


class CalculateResponse(BaseModel):
    expression: str
    result: float
    error: Optional[str] = None


# --- Tool 2: Fact Search Schemas ---

class SearchResultItem(BaseModel):
    topic: str
    fact: str


FactMatch = SearchResultItem


class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        description="Search string to match against seed fact repository",
        examples=["population of France"],
    )


class SearchResponse(BaseModel):
    query: str
    matches: List[SearchResultItem] = Field(default_factory=list)
    results: List[SearchResultItem] = Field(default_factory=list)
    total_matches: int = 0

    def __init__(self, **data):
        if "matches" in data and "results" not in data:
            data["results"] = data["matches"]
        elif "results" in data and "matches" not in data:
            data["matches"] = data["results"]
        super().__init__(**data)


# --- Tool 3: Document Retrieval Schemas ---

class DocumentChunk(BaseModel):
    source_filename: str = Field(default="unknown", description="Source document name")
    chunk_index: int = Field(default=0, description="Sequential index of chunk within source")
    content: str = Field(..., description="Text content of the retrieved chunk")
    score: float = Field(default=0.0, description="Cosine similarity score")

    @property
    def source(self) -> str:
        return self.source_filename

    @property
    def chunk_id(self) -> int:
        return self.chunk_index


class RetrieveRequest(BaseModel):
    query: str = Field(
        ...,
        description="Natural language semantic search query",
        examples=["Raw tier retention duration"],
    )
    top_k: Optional[int] = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of document chunks to return",
    )
    source_filter: Optional[str] = Field(
        default=None,
        description="Optional filter to restrict retrieval to a specific document filename",
    )


class RetrieveResponse(BaseModel):
    query: str
    results: List[DocumentChunk]
    total_retrieved: int = Field(default=0, description="Total chunks returned")

    def __init__(self, **data):
        if "total_found" in data and "total_retrieved" not in data:
            data["total_retrieved"] = data["total_found"]
        super().__init__(**data)

    @property
    def total_found(self) -> int:
        return self.total_retrieved

    @property
    def chunks(self) -> List[DocumentChunk]:
        return self.results


# --- Stage 3: Ingestion Schemas ---

class CollectionStats(BaseModel):
    total_chunks: int
    unique_documents: int


class IngestResponse(BaseModel):
    document_id: str
    source_filename: str
    chunk_count: int
    collection_stats: CollectionStats
    message: str
