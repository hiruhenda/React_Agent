from typing import Any
from pydantic import BaseModel, Field


class AgentStepTrace(BaseModel):
    """Diagnostic trace of a single ReAct step."""
    step: int
    thought: str = Field(..., description="The internal reasoning emitted by the model.")
    action: str = Field(..., description="The tool name selected by the model.")
    action_input: str | dict[str, Any] = Field(
        ..., description="The raw input arguments passed to the tool."
    )
    observation: str = Field(..., description="The string output returned by the tool.")


class QueryRequest(BaseModel):
    """Incoming request payload to the agent API."""
    query: str = Field(..., min_length=1, description="The user's question.")
    max_iterations: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="Override the default loop safety limit.",
    )


class QueryResponse(BaseModel):
    """Contract response returned by POST /query."""
    query: str
    answer: str
    steps: list[AgentStepTrace] = Field(default_factory=list)
    iterations: int
    error: str | None = None