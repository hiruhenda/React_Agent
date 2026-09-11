# ReAct Agent REST API — Halcyon Labs / Tideline Research Assistant

A Reasoning + Acting (ReAct) agent exposed via a FastAPI REST interface, implementing tool orchestration over a ChromaDB vector store, structured factual search, and safe AST-based arithmetic execution.

---

## 1. Setup from Scratch

### Prerequisites
- Python 3.11+
- Virtual environment (`venv`)

### Installation
```bash
# Clone or navigate to the repository
git clone <repo-url>
cd react-agent

# Create and activate virtual environment
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt


2. Environment Variables
Create a .env file in the project root based on .env.example:
GEMINI_API_KEY="your_api_key_here"
CHROMA_PERSIST_DIR="chroma_db"
AGENT_TIMEOUT_SECONDS=60
DEFAULT_MAX_ITERATIONS=10


3. Ingesting the Corpus
All corpus documents must be indexed via the POST /ingest API endpoint:
python scripts/ingest_corpus.py


4. Running the Evaluation Harness
Execute the unattended 21-question evaluation runner. 
python scripts/run_eval.py
results are saved to eval/results.md and summarized in the terminal


5. API Usage & Example Requests
Start the development server:
uvicorn app.main:app --reload --port 8000
Interactive documentation is accessible at 
http://127.0.0.1:8000/docs


Example 1: Pure Calculation
Request:
curl -X POST "[http://127.0.0.1:8000/agent/query](http://127.0.0.1:8000/agent/query)" \
     -H "Content-Type: application/json" \
     -d '{"query": "Calculate 14 * 24"}'

Response:
{
  "query": "Calculate 14 * 24",
  "answer": "14 * 24 is 336.",
  "iterations": 2,
  "latency_ms": 1120.4,
  "stop_reason": "final_answer"
}


Example 2: Corupus Retrieval with claim attribution
Request:
curl -X POST "[http://127.0.0.1:8000/agent/query](http://127.0.0.1:8000/agent/query)" \
     -H "Content-Type: application/json" \
     -d '{"query": "What is the retention period for the Raw tier in Tideline?"}'

Response:
{
  "query": "What is the retention period for the Raw tier in Tideline?",
  "answer": "The data retention period for the Raw tier in Tideline is 14 days.",
  "iterations": 2,
  "latency_ms": 1845.2,
  "stop_reason": "final_answer"
}


Example 3: Multi-Turn Conversation & History
curl -X GET "[http://127.0.0.1:8000/agent/history/g1_test_1789037542](http://127.0.0.1:8000/agent/history/g1_test_1789037542)"

Response:
{
  "session_id": "g1_test_1789037542",
  "turns_count": 3,
  "turns": [
    {
      "query": "What is the data retention period for the Raw tier in Tideline?",
      "answer": "The data retention period for the Raw tier in Tideline is 14 days.",
      "timestamp": "2026-09-10T10:52:22.000Z"
    },
    {
      "query": "How many hours is that retention duration in total?",
      "answer": "The 14-day retention period is equivalent to 336 hours in total.",
      "timestamp": "2026-09-10T10:52:28.000Z"
    },
    {
      "query": "Which document did you find that information in?",
      "answer": "The information regarding the Raw tier retention period of 14 days was found in the document `02-rfc-014-retention-and-downsampling.md` as well as `policy.txt`.",
      "timestamp": "2026-09-10T10:52:35.000Z"
    }
  ]
}
