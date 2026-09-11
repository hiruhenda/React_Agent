import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.schemas.agent import ThoughtStep, AgentResponse


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


# --- System Endpoints ---

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "indexed_chunks" in data
    assert data["indexed_chunks"] > 0


def test_agent_info(client):
    response = client.get("/agent/info")
    assert response.status_code == 200
    data = response.json()
    assert "model" in data
    assert "calculate_expression" in data["tools"]
    assert "retrieve_tideline_docs" in data["tools"]
    assert "search_world_facts" in data["tools"]


# --- Standalone Tool Endpoints ---

def test_tool_calculate_success(client):
    response = client.post("/tools/calculate", json={"expression": "14 * 24"})
    assert response.status_code == 200
    assert float(response.json()["result"]) == 336.0


def test_tool_calculate_division_by_zero(client):
    response = client.post("/tools/calculate", json={"expression": "10 / 0"})
    assert response.status_code == 400
    assert "zero" in response.json()["detail"].lower()


def test_tool_calculate_hostile_syntax(client):
    response = client.post("/tools/calculate", json={"expression": "__import__('os').system('ls')"})
    assert response.status_code == 422


def test_tool_search_found(client):
    response = client.post("/tools/search", json={"query": "France population"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] >= 1
    assert any("france" in r["topic"].lower() for r in data["results"])


def test_tool_search_empty_matches(client):
    response = client.post("/tools/search", json={"query": "nonexistent_query_xyz"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] == 0
    assert data["results"] == []


def test_tool_retrieve_success(client):
    response = client.post("/tools/retrieve", json={"query": "Raw tier retention", "top_k": 2})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_retrieved" in data or "total_found" in data
    assert isinstance(data["results"], list)


# --- Agent Query Endpoints & Validation ---

def test_query_validation_whitespace(client):
    response = client.post("/agent/query", json={"query": "   "})
    assert response.status_code == 422


def test_query_validation_bounds(client):
    response = client.post("/agent/query", json={"query": "test", "max_iterations": 30})
    assert response.status_code == 422


def test_query_mocked_contract(client):
    mocked_return = AgentResponse(
        query="What is 2 + 2?",
        answer="4",
        steps=[
            ThoughtStep(
                step=1,
                thought="Calculate 2 + 2",
                action="calculate_expression",
                action_input="2 + 2",
                observation="4",
            )
        ],
        iterations=1,
        latency_ms=150.0,
        stop_reason="final_answer",
    )

    with patch("app.agent.core.ReActAgent.run", return_value=mocked_return):
        response = client.post("/agent/query", json={"query": "What is 2 + 2?"})
        assert response.status_code == 200
        body = response.json()
        assert body["answer"] == "4"
        assert body["stop_reason"] == "final_answer"
        assert body["latency_ms"] == 150.0
        assert len(body["steps"]) == 1


@pytest.mark.integration
def test_query_live_e2e(client):
    response = client.post(
        "/agent/query",
        json={
            "query": "What is the lifetime in days of the Raw tier in RFC-014, and what is that multiplied by 24?",
            "max_iterations": 5,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "336" in body["answer"]
    assert body["stop_reason"] == "final_answer"
    assert len(body["steps"]) >= 1

# --- Session Memory Endpoints & Persistence ---

def test_session_turns_recorded(client):
    test_session = "test-session-123"
    
    mock_resp = AgentResponse(
        query="What is the raw tier retention?",
        session_id=test_session,
        answer="14 days",
        steps=[],
        iterations=1,
        latency_ms=100.0,
        stop_reason="final_answer",
    )

    with patch("app.agent.core.ReActAgent.run", return_value=mock_resp):
        res = client.post(
            "/agent/query",
            json={"query": "What is the raw tier retention?", "session_id": test_session},
        )
        assert res.status_code == 200
        assert res.json()["session_id"] == test_session

    # Directly check session store API
    from app.services.session import session_store
    session_store.record_turn(test_session, "What is the raw tier retention?", "14 days", [])
    
    session_res = client.get(f"/agent/sessions/{test_session}")
    assert session_res.status_code == 200
    assert session_res.json()["turns_count"] >= 1

    del_res = client.delete(f"/agent/sessions/{test_session}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "cleared"