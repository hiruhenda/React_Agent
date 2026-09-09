from langchain_core.tools import tool
from app.services.search import search_facts

@tool
def search_world_facts(query: str) -> str:
    """Useful for looking up real-world knowledge facts, constants, countries, or populations.
    Input must be a concise keyword query, e.g. 'France population' or 'Germany area'.
    Do NOT use this tool for Tideline technical architecture, retention, or RFCs.
    """
    try:
        matches = search_facts(query)
        if not matches:
            return "No matching world facts found."
        lines = [f"- {m.topic}: {m.fact}" for m in matches]
        return "\n".join(lines)
    except Exception as e:
        return f"Search Error: {str(e)}"
