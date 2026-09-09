\# Tideline Research Assistant (ReAct Agent API)



A production-grade, multi-stage ReAct (Reasoning + Acting) AI agent service built with \*\*FastAPI\*\*, \*\*LangChain\*\*, and Google's \*\*Gemini API\*\* (`gemini-2.5-flash`). The service coordinates specialized tools (semantic document retrieval, keyword fact search, and safe arithmetic) over a persistent vector store of Tideline documentation.



\---



\## 1. Architecture Highlights



\- \*\*Text-Parsing ReAct Loop\*\*: Implements the canonical ReAct pattern using structured plain-text prompt parsing (`Thought`, `Action`, `Action Input`, `Observation`, `Final Answer`) with temperature fixed to `0.0`.

\- \*\*Decoupled Service Layer (Constraint #3)\*\*: All core domain logic resides in framework-agnostic Python functions under `app/services/`. Both standalone FastAPI HTTP endpoints (`app/routers/tools.py`) and agent tool wrappers (`app/tools/`) consume the identical service tier without circular dependencies.

\- \*\*Persistent Vector Store (ChromaDB)\*\*: Ingests Tideline markdown documentation (`corpus/\*.md`) into persistent storage using `sentence-transformers/all-MiniLM-L6-v2`. Seeding runs idempotently on FastAPI startup lifecycle events (`lifespan`).

\- \*\*AST-Guarded Arithmetic\*\*: The calculation service evaluates math strictly via Abstract Syntax Tree (AST) node parsing—eliminating remote code execution (RCE) hazards from `eval()` and capping exponentiation attacks.

\- \*\*Fail-Safe \& Bounded Execution\*\*:

&#x20; - Request-level timeouts (default 60s) returning partial traces with `stop\_reason="timeout"`.

&#x20; - Configurable iteration limits (default 10, max 20) returning `stop\_reason="max\_iterations"`.

&#x20; - Strict Pydantic v2 schemas validating inputs and sanitizing whitespace.



\---



\## 2. Directory Structure



text

React\_Agent/

├── app/

│   ├── agent/

│   │   ├── core.py             # ReAct reasoning loop \& Gemini text parsing

│   │   └── prompts.py          # Strict system prompt templates

│   ├── routers/

│   │   ├── agent.py            # /agent/query \& /agent/info routes

│   │   └── tools.py            # Standalone /tools/\* routes (Req 1.7-1.9)

│   ├── schemas/

│   │   ├── agent.py            # AgentRequest, ThoughtStep, AgentResponse

│   │   └── tools.py            # Search, Retrieve, Calculate schemas

│   ├── services/

│   │   ├── calculator.py       # Safe AST math evaluator

│   │   ├── retriever.py        # ChromaDB client \& sliding-window chunker

│   │   ├── search.py           # Markdown table fact search engine

│   │   └── session.py          # Conversational memory state store

│   ├── tools/

│   │   ├── calculator.py       # LangChain wrapper for calculator service

│   │   ├── retriever.py        # LangChain wrapper for retriever service

│   │   └── search.py           # LangChain wrapper for search service

│   ├── config.py               # Pydantic BaseSettings management

│   └── main.py                 # FastAPI application factory \& lifespan

├── corpus/                     # Tideline technical documentation (.md)

├── data/                       # Mock search world facts (search-facts.md)

├── tests/

│   └── test\_api.py             # Contract \& unit test suite (pytest)

├── requirements.txt

├── ARCHITECTURE.md

└── README.md





\## 3. Setup \& Installation



\### Prerequisites

\- Python 3.10+ (tested on Python 3.11)

\- Windows PowerShell or Bash terminal

\- Active Gemini API Key



\### Installation Steps



1\. \*\*Clone the repository and navigate to root:

bash

cd React\_Agent





2\. \*\*Create and activate a virtual environment:\*\*

powershell

python -m venv venv

.\\venv\\Scripts\\Activate.ps1





3\. \*\*Install dependencies:\*\*

bash

pip install -r requirements.txt





4\. \*\*Configure Environment Variables:\*\*

Create a `.env` file in the root directory:

env

GEMINI\_API\_KEY="your\_actual\_gemini\_api\_key\_here"

GEMINI\_MODEL="gemini-2.5-flash"

AGENT\_TIMEOUT\_SECONDS=60

MAX\_ITERATIONS\_DEFAULT=10



\---



\## 4. Running the Service



Start the FastAPI application using `uvicorn`:

powershell

uvicorn app.main:app --reload --port 8000





Once running, interactive API documentation is available at:

\- \*\*Swagger UI\*\*: \[http://localhost:8000/docs](http://localhost:8000/docs)

\- \*\*ReDoc\*\*: \[http://localhost:8000/redoc](http://localhost:8000/redoc)



\---



\## 5. API Reference



\### Health \& Metadata

\- \*\*`GET /health`\*\*: Returns datastore readiness and count of indexed chunks.

\- \*\*`GET /agent/info`\*\*: Returns active model name, configured iteration limits, and registered tool names.



\### Agent Loop

\- \*\*`POST /agent/query`\*\*: Executes the multi-step ReAct agent.

&#x20; - \*\*Payload\*\*:

json{"query": "What is the lifetime in days of the Raw tier in RFC-014, and what is that multiplied by 24?","max\_iterations": 10,"return\_trace": true}- \*\*Response\*\*: Includes `answer`, `iterations`, `latency\_ms`, `stop\_reason` (`"final\_answer"`, `"max\_iterations"`, `"timeout"`), and intermediate `steps` array.



\### Standalone Tools

\- \*\*`POST /tools/calculate`\*\*: Safe arithmetic evaluation (`{"expression": "14 \* 24"}`).

\- \*\*`POST /tools/search`\*\*: Keyword lookup across world facts table (`{"query": "France population"}`).

\- \*\*`POST /tools/retrieve`\*\*: Vector similarity search over Tideline documents (`{"query": "Raw tier retention", "top\_k": 3}`).



\---



\## 6. Running Tests



Run the unit and contract test suite with `pytest`:



powershellpytest -v -m "not integration"

To run all tests including live API integration tests:



powershellpytest -v

4.Save and close Notepad:In Notepad, press Ctrl + S to save the file, then close the Notepad window.5.Confirm the file in PowerShell:Run this in your PowerShell window to confirm it saved properly:PowerShellGet-Item README.md







