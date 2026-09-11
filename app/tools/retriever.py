from langchain_core.tools import tool
from app.services.retriever import retrieve_documents


@tool
def retrieve_tideline_docs(query: str) -> str:
    """Useful for retrieving Tideline technical documentation, RFCs, retention policies,
    pricing FAQ tiers, onboarding guides, and postmortems.
    Input must be a search string query about Tideline.
    """
    try:
        response = retrieve_documents(query=query, top_k=3)
        
        # Unpack chunks if returned as RetrieveResponse or dict
        if hasattr(response, "results"):
            chunks = response.results
        elif isinstance(response, dict):
            chunks = response.get("results", [])
        elif isinstance(response, (list, tuple)):
            chunks = response
        else:
            chunks = []

        if not chunks:
            return "No relevant documentation found."

        formatted = []
        for i, c in enumerate(chunks, 1):
            if hasattr(c, "source_filename"):
                source = c.source_filename
                score = getattr(c, "score", 0.0)
                content = getattr(c, "content", "")
            elif isinstance(c, dict):
                source = c.get("source_filename", c.get("source", "unknown"))
                score = c.get("score", 0.0)
                content = c.get("content", "")
            elif isinstance(c, (list, tuple)) and len(c) >= 2:
                source = str(c[0])
                score = 0.0
                content = str(c[1])
            else:
                source = "unknown"
                score = 0.0
                content = str(c)

            formatted.append(f"[{i}] Source: {source} (relevance: {score})\n{content}")

        return "\n\n".join(formatted)
    except Exception as e:
        return f"Retrieval Error: {str(e)}"
