# Decisions Log

## Stage 1: Foundation

### 1. Tech Stack
- Python 3.11.9
- FastAPI 0.111.0 
- Pydantic v2 (2.7.4)
- ChromaDB 0.5
- LangChain 0.2.6


### 2. LLM Selection
- Google Gemini
Reason - Accessible free tier has strong reasoning performance.

### 3. ChromaDB Retriever.
- ChromaDB Vector database
-Rejected remote API to avoid rate limits, network latency etc. 
- Stored locally and reproducible execution that runs without any external embedding quotas.


## Issues Faced

8/9
- Had to change python versions from 3.14.7 to 3.11.9 due to mismatches with ChromaDB and other extensions.

- Loose Overlapping allowed inaccurate answers to return from search_fact.mb

9/9 
- Tried to install FastEmbed . Unsuccessful due to windows filesystem priviledge issues.

