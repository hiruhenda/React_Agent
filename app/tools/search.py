import re
from pathlib import Path
from langchain.tools import tool
from app.schemas.tools import SearchInput, SearchOutput

DATA_PATH = Path("data/search-facts.md")

STOPWORDS = {
    "what", "is", "the", "of", "in", "for", "and", "a", "an",
    "to", "how", "much", "many", "does", "are", "about", "as"
}


def load_facts() -> list[str]:
    """Reads factual sentences from data/search-facts.md."""
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
    return [line for line in lines if line and not line.startswith(("#", "---"))]


def tokenize(text: str) -> set[str]:
    """Extracts alphanumeric words in lowercase, excluding common stopwords."""
    words = re.findall(r"\b[a-z0-9]+\b", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 1}


def search_facts(query: str) -> SearchOutput:
    """Matches facts based on strict keyword token overlap.
    
    Defense:
    - If the query contains specific discriminative terms (e.g., 'Germany', 'area'),
      all meaningful tokens must appear in the fact.
    - If the query is a single broad topic (e.g., 'population'), all matching
      facts are returned.
    """
    facts = load_facts()
    query_tokens = tokenize(query)

    if not query_tokens:
        return SearchOutput(query=query, results=[], found=False)

    matches = []
    for fact in facts:
        fact_tokens = tokenize(fact)

        # Full subset match: all significant query tokens exist in the fact
        if query_tokens.issubset(fact_tokens):
            matches.append(fact)
            continue

        # If query has only 1 token (e.g., 'population'), return any fact containing it
        if len(query_tokens) == 1 and query_tokens.intersection(fact_tokens):
            matches.append(fact)

    return SearchOutput(
        query=query,
        results=matches,
        found=len(matches) > 0
    )


@tool(args_schema=SearchInput)
def search_world_facts(query: str) -> str:
    """Useful for looking up general world knowledge, facts, populations, and constants.
    Do NOT use this tool for Tideline-specific database documentation, pricing, or internal RFCs.
    """
    output = search_facts(query)
    if not output.found:
        return f"No world facts found matching query: '{query}'."
    return "\n".join(output.results)