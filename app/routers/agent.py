from fastapi import APIRouter, HTTPException, status
from app.agent.core import ReActAgent, TOOL_MAP
from app.config import settings
from app.schemas.agent import AgentRequest, AgentResponse
from app.services.session import session_store

router = APIRouter(prefix="/agent", tags=["Agent"])

_agent_instance: ReActAgent | None = None


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


@router.get("/info")
def get_agent_info():
    """Reports registered tools, active model, and configured iteration limits."""
    return {
        "model": settings.gemini_model,
        "max_iterations_default": settings.max_iterations_default,
        "tools": list(TOOL_MAP.keys()),
    }


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    """Retrieves conversation history and turns for a given session."""
    session = session_store.get_or_create(session_id)
    return {
        "session_id": session.session_id,
        "turns_count": len(session.turns),
        "turns": session.turns,
    }


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Resets conversational memory for a given session."""
    session_store.clear(session_id)
    return {"status": "cleared", "session_id": session_id}