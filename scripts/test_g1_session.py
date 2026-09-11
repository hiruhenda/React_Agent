import sys
import os
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from starlette.testclient import TestClient
from app.main import app

def test_g1_multiturn():
    client = TestClient(app)
    session_id = f"g1_test_{int(time.time())}"
    
    turns = [
        "What is the data retention period for the Raw tier in Tideline?",
        "How many hours is that retention duration in total?",
        "Which document did you find that information in?"
    ]
    
    print(f"--- Running G1 Multi-Turn Conversation (Session: {session_id}) ---")
    
    for i, user_query in enumerate(turns, 1):
        print(f"\n[Turn {i}] User: {user_query}")
        res = client.post("/agent/query", json={
            "query": user_query,
            "session_id": session_id,
            "max_iterations": 8
        })
        assert res.status_code == 200, f"Failed turn {i}: {res.text}"
        data = res.json()
        print(f"[Turn {i}] Agent: {data.get('answer')}")
        print(f"[Turn {i}] Iterations: {data.get('iterations')} | Reason: {data.get('stop_reason')}")

    # Check history endpoint (Requirement 3.8)
    hist_res = client.get(f"/agent/history/{session_id}")
    print(f"\n[History Check] Status: {hist_res.status_code}")
    assert hist_res.status_code == 200
    history = hist_res.json()
    print(f"Recorded {len(history)} turns in session memory.")

if __name__ == "__main__":
    test_g1_multiturn()
