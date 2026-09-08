from pydantic import BaseModel, Field


class SearchInput(BaseModel):
    """Input for the mock world search tool."""
    query: str = Field(
        ...,
        description="The search query or keyword phrase to search in general world facts.",
        min_length=1,
    )


class SearchOutput(BaseModel):
    """Output returned by the mock world search tool."""
    query: str
    results: list[str] = Field(default_factory=list)
    found: bool


class CalculatorInput(BaseModel):
    """Input for the safe mathematical expression evaluator."""
    expression: str = Field(
        ...,
        description="A mathematical expression using basic operators (+, -, *, /, **, %, parentheses).",
        min_length=1,
    )


class CalculatorOutput(BaseModel):
    """Output returned by the safe calculator tool."""
    expression: str
    result: float | int | None = None
    error: str | None = None


class RetrieveInput(BaseModel):
    """Input for the Tideline internal corpus retriever."""
    query: str = Field(
        ...,
        description="The semantic search query to look up inside Tideline technical documentation and RFCs.",
        min_length=1,
    )
    k: int = Field(
        default=3,
        description="Number of relevant document chunks to return.",
        ge=1,
        le=10,
    )


class RetrievedChunk(BaseModel):
    """A single retrieved document chunk from ChromaDB."""
    content: str
    source_document: str
    score: float | None = None


class RetrieveOutput(BaseModel):
    """Output returned by the Tideline corpus retriever."""
    query: str
    chunks: list[RetrievedChunk] = Field(default_factory=list)