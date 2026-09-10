\# Tideline Research Assistant — Architecture \& Design Document



\## 1. Executive Summary \& Design Principles



The Tideline Research Assistant is a modular reasoning service implementing the canonical \*\*ReAct (Reasoning + Acting)\*\* paradigm. Built atop FastAPI and Google Gemini (`gemini-2.5-flash`), the system orchestrates domain retrieval over Tideline technical documentation, general fact search, and safe mathematical evaluation.



The system is engineered around four core principles:

1\. \*\*Separation of Concerns (Constraint #3)\*\*: Framework-agnostic services remain entirely decoupled from HTTP routes and agent tool bindings.

2\. \*\*Deterministic, Bounded Reasoning\*\*: The agent loop is constrained by strict plain-text parsing, explicit iteration limits, and execution timeouts.

3\. \*\*Defense in Depth\*\*: Arithmetic evaluation uses whitelist Abstract Syntax Tree (AST) traversal to eliminate Remote Code Execution (RCE) hazards.

4\. \*\*Idempotent Storage Operations\*\*: Persistent vector embeddings are initialized once at application startup without duplicating chunks across server reloads.



\---



\## 2. Decoupled Service Architecture



To prevent vendor lock-in and eliminate circular dependencies, the codebase enforces a strict unidirectional dependency hierarchy:

\[ HTTP Routers (FastAPI) ]       \[ Agent Framework (LangChain) ]

\\                                   /

\\                                 /

\[ app/routers/tools.py ]     \[ app/tools/\*.py ]

\\                 /

\\               /

\[ Core Domain Services (app/services/) ]

├── calculator.py (AST Evaluator)

├── retriever.py  (ChromaDB + SentenceTransformers)

└── search.py     (Markdown Keyword Matcher)

|

\[ Storage / Vector DB ]

└── chroma\_db/ (Persistent On-Disk)





\### Invariant Enforcements:

\- \*\*Zero Framework Leakage\*\*: Functions under `app/services/` take primitive Python arguments (strings, integers) and return Pydantic models. They contain no imports from `fastapi` or `langchain`.

\- \*\*Dual Exposure\*\*: The same underlying function (e.g., `retrieve\_documents()`) serves both the standalone REST endpoint (`POST /tools/retrieve`) and the agent's LangChain tool (`retrieve\_tideline\_docs`).



\---



\## 3. ReAct Reasoning Loop Design



\### Text-Parsing vs. Native Function Calling

The agent uses a text-parsing ReAct loop over prompt instructions rather than native tool-calling APIs. This architecture was selected to:

\- Maintain complete diagnostic visibility over the model's scratchpad (`Thought`, `Action`, `Action Input`, `Observation`).

\- Provide an auditable, step-by-step trace returned directly in the `AgentResponse` schema.

\- Prevent model lock-in, enabling alternative LLM backends without refactoring tool definitions.



\### Prompt \& Scratchpad Lifecycle

1\. \*\*System Prompt\*\*: Defines role boundaries, registered tool signatures, input formatting rules, and the termination condition (`Final Answer:`).

2\. \*\*Execution Loop\*\*:

&#x20;  - Compiles cumulative history: `Question: <query>\\n<scratchpad>`.

&#x20;  - Generates next step with Gemini at `temperature=0.0`.

&#x20;  - Parses `Thought` and `Action`.

&#x20;  - Executes matched tool from `TOOL\_MAP`.

&#x20;  - Appends `Observation: <result>` to the scratchpad.

3\. \*\*Loop Termination\*\*:

&#x20;  - Detection of `Final Answer:` yields `stop\_reason="final\_answer"`.

&#x20;  - Iterations reaching `max\_iterations` yields `stop\_reason="max\_iterations"`.

&#x20;  - Total runtime exceeding `settings.agent\_timeout\_seconds` yields `stop\_reason="timeout"`.



\---



\## 4. Retrieval-Augmented Generation (RAG) \& Vector Store



\### Vector Pipeline

\- \*\*Embedding Model\*\*: `all-MiniLM-L6-v2` via HuggingFace/SentenceTransformers (fast, local execution, 384-dimensional dense vectors).

\- \*\*Datastore\*\*: ChromaDB (`PersistentClient` stored at `chroma\_db/`).

\- \*\*Chunking Strategy\*\*: Character-based sliding window with a chunk size of 600 characters and an overlap of 100 characters. This maintains contextual continuity across Markdown sections while keeping retrieval chunks compact.



\### Startup Ingestion Lifespan

ChromaDB seeding runs inside FastAPI's `lifespan` handler. The function checks `collection.count() > 0` before reading `corpus/\*.md`. If already populated, ingestion is skipped, guaranteeing idempotency during development reloads (`--reload`).



\---



\## 5. Security \& Threat Modeling



| Threat Vector | Mitigation Strategy | Implementation |

| :--- | :--- | :--- |

| \*\*Remote Code Execution (RCE)\*\* | Ban `eval()`, `exec()`, and shell calls. | `app/services/calculator.py` parses math expressions into an AST, traversing only permitted nodes (`ast.Add`, `ast.Sub`, `ast.Mult`, `ast.Div`, `ast.Pow`, `ast.USub`). |

| \*\*Denial of Service (CPU Exhaustion)\*\* | Exponent attack prevention (e.g., `9\*\*99999999`). | AST visitor rejects exponent values greater than `10,000`. |

| \*\*Agent Infinite Loops\*\* | Iteration bounding and execution timeouts. | Bounded by `max\_iterations` (1–20) and a hard timeout check (default 60s) returning partial traces. |

| \*\*Prompt Injection via Retrieval\*\* | Separation of system instructions from observation context. | Retrieved chunks are prefixed strictly under `Observation:` markers within the prompt scratchpad. |



\---



\## 6. Testing Strategy



The test suite (`tests/test\_api.py`) verifies:

\- \*\*System Health\*\*: Verifies collection readiness and document count on `/health`.

\- \*\*Contract Integrity\*\*: Validates Pydantic schema rejection for empty strings, whitespace queries, and out-of-range iteration limits.

\- \*\*Tool Isolation\*\*: Direct unit tests for calculation (division by zero, syntax errors), search keyword matches, and vector retrieval.

\- \*\*Agent Mocking\*\*: Verifies end-to-end API response contact serialization using mocked agent runs without consuming API credits.

