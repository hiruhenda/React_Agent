from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class AgentRequest(BaseModel):
    """Incoming request payload to the agent API."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The user query or question.",
        examples=["What is the lifetime in days of the Raw tier in RFC-014, and what is that multiplied by 24?"]
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session identifier for multi-turn conversation tracking.",
        examples=["session-abc-123"]
    )
    max_iterations: int = Field(
        default=10,
        ge=1,
        le=25,
        description="Safety bound on maximum ReAct reasoning loops.",
        examples=[10]
    )
    return_trace: bool = Field(
        default=True,
        description="Flag controlling whether the detailed reasoning trace is included in the response.",
        examples=[True]
    )

    @field_validator("query")
    @classmethod
    def reject_whitespace_only(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Query cannot be empty or contain only whitespace.")
        return stripped


class ThoughtStep(BaseModel):
    """Represents a single loop iteration in the ReAct trace."""
    step: int = Field(..., description="Iteration number.", examples=[1])
    thought: str = Field(..., description="Internal reasoning emitted by the model.", examples=["I need to retrieve RFC-014."])
    action: str = Field(..., description="Tool selected to execute.", examples=["retrieve_tideline_docs"])
    action_input: str = Field(..., description="Input argument string passed to the tool.", examples=["Raw tier retention"])
    observation: str = Field(..., description="Result returned from the tool.", examples=["Raw tier lifetime: 14 days"])


class AgentResponse(BaseModel):
    """Contract response returned by POST /agent/query."""
    query: str = Field(..., description="The original user query.")
    answer: str = Field(..., description="Synthesized final answer from the agent.")
    steps: List[ThoughtStep] = Field(
        default_factory=list,
        description="Diagnostic trace of steps taken. Empty if return_trace is False."
    )
    iterations: int = Field(..., description="Total ReAct loop iterations executed.")
    latency_ms: float = Field(..., description="End-to-end execution latency in milliseconds.")
    stop_reason: str = Field(
        ...,
        description="Machine-readable termination reason: final_answer | max_iterations | timeout | error",
        examples=["final_answer"]
    )