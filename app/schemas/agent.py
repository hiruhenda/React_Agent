from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class AgentRequest(BaseModel):
    query: str = Field(..., description="Natural language question to answer")
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session key for multi-turn conversation memory",
    )
    max_iterations: Optional[int] = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum reasoning loop iterations allowed",
    )
    return_trace: Optional[bool] = Field(
        default=True,
        description="Whether to return the list of intermediate thought/action steps",
    )

    @field_validator("query")
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Query string must not be empty or whitespace only")
        return cleaned


class ThoughtStep(BaseModel):
    step: int
    thought: str
    action: str
    action_input: str
    observation: str


class AgentResponse(BaseModel):
    query: str
    session_id: Optional[str] = None
    answer: str
    steps: List[ThoughtStep] = Field(default_factory=list)
    iterations: int
    latency_ms: float
    stop_reason: Literal["final_answer", "max_iterations", "timeout"]