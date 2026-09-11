from typing import Optional
from fastapi import APIRouter, HTTPException, status
from app.agent.core import ReActAgent, TOOL_MAP
from app.config import settings
from app.schemas.agent import (
    AgentRequest,
    AgentResponse,
    SessionHistoryResponse,
    SessionTurn as SchemaSessionTurn,
)
from app.services.session import session_store

router = APIRouter(prefix="/agent", tags=["Agent"])

_agent_instance: Optional[ReActAgent] = None


def get_agent() -> ReActAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ReActAgent()
    return _agent_instance


@router.post("/query", response_model=AgentResponse)
def run_query(request: AgentRequest):
    """Executes multi-step ReAct reasoning loop over registered tools."""
    agent = get_agent()
    try:
        return agent.run(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}",
        )


@router.get("/history/{session_id}", response_model=SessionHistoryResponse)
def get_session_history(session_id: str):
    """Retrieves conversation history and turns for a given session.
    Returns 404 if session is unknown.
    """
    session = session_store.get(session_id)
    if session is None or not session.turns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )
    
    turns = [
        SchemaSessionTurn(
            query=turn.query,
            answer=turn.answer,
            timestamp=turn.timestamp,
        )
        for turn in session.turns
    ]
    return SessionHistoryResponse(
        session_id=session.session_id,
        turns_count=len(turns),
        turns=turns,
    )


@router.delete("/history/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str):
    """Clears conversation history for a given session."""
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )
    session_store.clear(session_id)
    return None

from app.schemas.agent import AgentInfoResponse, ToolInfo
from app.agent.core import TOOLS
from app.config import settings

@router.get("/info", response_model=AgentInfoResponse)
def get_agent_info():
    """Reports live registered tools, LLM model, and execution constraints without drift."""
    registered_tools = [
        ToolInfo(name=tool.name, description=tool.description.strip())
        for tool in TOOLS
    ]
    return AgentInfoResponse(
        model=settings.gemini_model,
        default_max_iterations=settings.max_iterations_default,
        max_iteration_limit=25,
        timeout_seconds=60.0,
        tools=registered_tools,
    )
