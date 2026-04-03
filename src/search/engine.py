"""
Search and retrieval engine.

Provides:
  - keyword search across the database
  - category / product filters
  - ranked results with relevance scoring
  - natural-language query shortcuts (e.g. "M600 communication protocols")
"""

import re
import logging
from typing import Optional

from src.database.store import ResearchDatabase

logger = logging.getLogger(__name__)

# Maps common natural-language phrases → (product, category, keywords)
QUERY_SHORTCUTS = [
    # M600 communication / protocols
    (r"m600.*(comm|protocol|link|datalink|lightbridge|mavlink|osdk)", "M600", "protocol", None),
    (r"(comm|protocol|link|datalink).*(m600|matrice)", "M600", "protocol", None),
    # M600 hardware
    (r"m600.*hardware|matrice.*component|m600.*part", "M600", "hardware", None),
    (r"hardware.*(m600|matrice 600)", "M600", "hardware", None),
    # M600 specs
    (r"m600.*spec|matrice.*spec|m600.*weight|m600.*payload|m600.*range", "M600", "spec", None),
    # GS Pro general
    (r"gs pro.*mission|ground station.*mission|gspro", "GS Pro", "use_case", None),
    (r"gs pro.*waypoint|ground station.*waypoint", "GS Pro", "protocol", None),
    (r"gs pro.*spec|ground station.*spec", "GS Pro", "spec", None),
    # Use cases
    (r"use case|application|deployment|agriculture|survey|inspect", None, "use_case", None),
]


def _score(item: dict, tokens: list[str]) -> float:
    """Simple TF-style relevance score."""
    text = (item["title"] + " " + item["content"]).lower()
    score = 0.0
    for tok in tokens:
        count = text.count(tok)
        if count:
            score += 1 + 0.1 * min(count, 10)
        # Title hits worth more
        if tok in item["title"].lower():
            score += 2
    return score


def _tokenise(query: str) -> list[str]:
    words = re.sub(r"[^\w\s]", " ", query.lower()).split()
    stopwords = {"the", "a", "an", "and", "or", "of", "for", "in", "on", "to", "with", "show", "me", "list", "find", "all"}
    return [w for w in words if w not in stopwords and len(w) > 1]


class SearchEngine:
    def __init__(self, db: ResearchDatabase):
        self.db = db

    def _interpret_query(self, query: str) -> tuple[Optional[str], Optional[str], str]:
        """
        Parse a natural-language query.
        Returns (product_filter, category_filter, cleaned_keyword).
        """
        ql = query.lower()

        for pattern, product, category, _ in QUERY_SHORTCUTS:
            if re.search(pattern, ql):
                return product, category, query

        # Infer product
        product = None
        if re.search(r"m600|matrice 600", ql):
            product = "M600"
        elif re.search(r"gs pro|ground station", ql):
            product = "GS Pro"

        # Infer category
        category = None
        if re.search(r"protocol|comm|link|sdk|mavlink|lightbridge", ql):
            category = "protocol"
        elif re.search(r"hardware|component|motor|battery|esc|frame|arm", ql):
            category = "hardware"
        elif re.search(r"software|app|firmware|sdk|api", ql):
            category = "software"
        elif re.search(r"spec|weight|payload|range|endurance|speed", ql):
            category = "spec"
        elif re.search(r"use case|mission|application|survey|inspect", ql):
            category = "use_case"

        return product, category, query

    def search(
        self,
        query: str,
        product: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """
        Search the database.

        If product/category are not passed, they are inferred from the query text.
        Results are sorted by relevance score.
        """
        inferred_product, inferred_category, clean_query = self._interpret_query(query)

        final_product = product or inferred_product
        final_category = category or inferred_category

        logger.debug(
            "Search: query=%r product=%s category=%s",
            clean_query,
            final_product,
            final_category,
        )

        # Build a concise keyword for the DB ILIKE filter.
        # Use only meaningful technical tokens, not the full NL sentence.
        tokens = _tokenise(query)
        # Pick the longest (most specific) token as the DB filter keyword,
        # falling back to None if we already have product+category filters.
        db_keyword: Optional[str] = None
        if tokens:
            if not (final_product and final_category):
                # No specific filters — use the most specific token to narrow results
                db_keyword = max(tokens, key=len)
            else:
                # We have both product + category; only filter on a keyword if it's
                # genuinely a technical term (not generic like "show", "list")
                tech_tokens = [t for t in tokens if len(t) > 4]
                if tech_tokens:
                    db_keyword = max(tech_tokens, key=len)

        items = self.db.query_items(
            product=final_product,
            category=final_category,
            keyword=db_keyword,
            limit=200,  # Fetch more, then re-rank
        )

        tokens = _tokenise(query)
        if tokens:
            items.sort(key=lambda i: _score(i, tokens), reverse=True)

        return items[:limit]

    def show_protocols(self, product: str = "M600") -> list[dict]:
        return self.search(f"{product} communication protocols", product=product, category="protocol")

    def show_hardware(self, product: str = "M600") -> list[dict]:
        return self.search(f"{product} hardware components", product=product, category="hardware")

    def show_specs(self, product: str = "M600") -> list[dict]:
        return self.search(f"{product} specifications", product=product, category="spec")

    def show_mission_planning(self) -> list[dict]:
        return self.search("GS Pro mission planning", product="GS Pro", category="use_case")

    def show_software(self, product: Optional[str] = None) -> list[dict]:
        return self.search("software SDK API", product=product, category="software")
