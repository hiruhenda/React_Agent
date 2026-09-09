import os
import re
from typing import List
from app.schemas.tools import SearchResultItem


def _load_facts() -> List[SearchResultItem]:
    filepath = os.path.join("data", "search-facts.md")
    if not os.path.exists(filepath):
        return []
    
    items: List[SearchResultItem] = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue
            parts = [p.strip() for p in line.split("|")]
            # Filter empty strings from leading/trailing pipe split
            parts = [p for p in parts if p != ""]
            if len(parts) >= 3:
                # Skip header row and divider
                if parts[0].startswith("-") or parts[0].lower() in ["#", "number"]:
                    continue
                keywords = parts[1]
                snippet = parts[2]
                items.append(SearchResultItem(topic=keywords, fact=snippet))
    return items


def search_facts(query: str) -> List[SearchResultItem]:
    """Matches search query keywords against loaded fact items."""
    query_tokens = set(re.findall(r"\w+", query.lower()))
    facts = _load_facts()
    matches: List[SearchResultItem] = []
    
    for item in facts:
        text = f"{item.topic} {item.fact}".lower()
        matched = sum(1 for token in query_tokens if token in text)
        if matched > 0:
            matches.append(item)
    return matches
