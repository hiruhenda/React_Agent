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

class SessionTurn(BaseModel):
    query: str = Field(..., description="User query submitted in this turn")
    answer: str = Field(..., description="Agent final answer for this turn")
    timestamp: str = Field(..., description="ISO 8601 timestamp of when the turn completed")


class SessionHistoryResponse(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    turns: List[SessionTurn] = Field(default_factory=list, description="Ordered list of conversation turns")
    turns_count: int = Field(..., description="Total number of turns recorded")

class ToolInfo(BaseModel):
    name: str = Field(description="Unique name of the tool")
    description: str = Field(description="Operational specification read by the agent")

class AgentInfoResponse(BaseModel):
    model: str = Field(description="Configured LLM identifier")
    default_max_iterations: int = Field(description="Default loop iteration cap")
    max_iteration_limit: int = Field(description="Maximum allowed iteration bound")
    timeout_seconds: float = Field(description="Configured execution timeout bound")
    tools: List[ToolInfo] = Field(description="Live registered tools available to the agent")

class HealthResponse(BaseModel):
    status: str = Field(description="Overall health status", example="ok")
    datastore_connected: bool = Field(description="True if ChromaDB connection is verified")
    collection_size: int = Field(description="Number of ingested vector chunks in the active collection")
