from langchain_core.tools import tool
from app.services.retriever import retrieve_documents

@tool
def retrieve_tideline_docs(query: str) -> str:
    """Useful for retrieving Tideline technical documentation, RFCs, retention policies,
    pricing FAQ tiers, onboarding guides, and postmortems.
    Input must be a search string query about Tideline.
    """
    try:
        chunks = retrieve_documents(query=query, top_k=3)
        if not chunks:
            return "No relevant documentation found."
        formatted = []
        for i, c in enumerate(chunks, 1):
            formatted.append(f"[{i}] Source: {c.source_filename} (relevance: {c.score})\n{c.content}")
        return "\n\n".join(formatted)
    except Exception as e:
        return f"Retrieval Error: {str(e)}"
