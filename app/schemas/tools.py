from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# --- Search Tool Schemas ---

class SearchRequest(BaseModel):
    """Payload for searching the factual world knowledge table."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query terms or question.",
        examples=["capital of France"]
    )

    @field_validator("query")
    @classmethod
    def reject_whitespace_only(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Query cannot be empty or contain only whitespace.")
        return stripped


class SearchResultItem(BaseModel):
    """A matched fact entry from the world facts table."""
    topic: str = Field(..., description="Fact category or subject.", examples=["France"])
    fact: str = Field(..., description="Factual detail.", examples=["Capital is Paris; population is roughly 67 million."])


class SearchResponse(BaseModel):
    """Response returned by the search tool endpoint."""
    query: str = Field(..., description="The query searched.")
    results: List[SearchResultItem] = Field(
        default_factory=list,
        description="List of matching facts. Returns empty list if no matches found."
    )
    total_matches: int = Field(..., description="Total count of matching items.")


# --- Retrieve Tool Schemas ---

class RetrieveRequest(BaseModel):
    """Payload for semantic document retrieval over Tideline corpus."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query to match against Tideline documentation.",
        examples=["Raw tier retention lifetime"]
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of most relevant chunks to return.",
        examples=[3]
    )
    source_filter: Optional[str] = Field(
        default=None,
        description="Optional filename to restrict search to a single document.",
        examples=["02-rfc-014-retention-and-downsampling.md"]
    )

    @field_validator("query")
    @classmethod
    def reject_whitespace_only(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Query cannot be empty or contain only whitespace.")
        return stripped


class DocumentChunk(BaseModel):
    """A retrieved document snippet with source metadata."""
    content: str = Field(..., description="The text content of the chunk.")
    source_filename: str = Field(..., description="Filename from which the chunk originated.", examples=["02-rfc-014-retention-and-downsampling.md"])
    score: float = Field(..., description="Relevance similarity score (lower distance / higher relevance).", examples=[0.4915])
    chunk_index: Optional[int] = Field(default=None, description="Index position of the chunk in the source document.")


class RetrieveResponse(BaseModel):
    """Response returned by the document retrieval endpoint."""
    query: str = Field(..., description="The search query submitted.")
    chunks: List[DocumentChunk] = Field(
        default_factory=list,
        description="Ranked list of matching document chunks."
    )
    total_retrieved: int = Field(..., description="Number of chunks retrieved.")


# --- Calculate Tool Schemas ---

class CalculateRequest(BaseModel):
    """Payload for safe arithmetic evaluation."""
    expression: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Mathematical expression to evaluate.",
        examples=["14 * 24"]
    )

    @field_validator("expression")
    @classmethod
    def reject_whitespace_only(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Expression cannot be empty or contain only whitespace.")
        return stripped


class CalculateResponse(BaseModel):
    """Response returned by the arithmetic evaluation endpoint."""
    expression: str = Field(..., description="The evaluated expression string.")
    result: str = Field(..., description="The computed numerical result as a string.", examples=["336"])