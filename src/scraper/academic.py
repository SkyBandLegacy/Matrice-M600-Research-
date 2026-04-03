"""
Academic database scrapers.

Sources:
  - Google Scholar (via SerpAPI or direct HTML — no API key required for HTML)
  - Semantic Scholar API (free, no key required for basic queries)
  - arXiv API

All results include DOI/URL for citation generation.
"""

import logging
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlencode, quote_plus

from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)

ACADEMIC_QUERIES = [
    ("DJI Matrice 600 UAV", "M600", "hardware"),
    ("DJI M600 unmanned aerial vehicle architecture", "M600", "hardware"),
    ("DJI Ground Station Pro mission planning", "GS Pro", "use_case"),
    ("Matrice 600 flight controller A3", "M600", "hardware"),
    ("DJI Lightbridge 2 communication protocol", "M600", "protocol"),
    ("DJI onboard SDK OSDK protocol", "M600", "protocol"),
    ("UAV precision agriculture M600", "M600", "use_case"),
    ("multirotor heavy-lift drone research", "M600", "use_case"),
    ("DJI waypoint autonomous flight", "GS Pro", "use_case"),
]

MAX_RESULTS_PER_QUERY = 5


class SemanticScholarScraper(BaseScraper):
    """Uses the free Semantic Scholar API — no API key needed."""

    name = "Semantic Scholar"
    API_BASE = "https://api.semanticscholar.org/graph/v1"

    FIELDS = "title,authors,year,abstract,externalIds,url,venue,publicationTypes"

    def _search(self, query: str, limit: int = MAX_RESULTS_PER_QUERY) -> list[dict]:
        url = f"{self.API_BASE}/paper/search?query={quote_plus(query)}&limit={limit}&fields={self.FIELDS}"
        try:
            resp = self.get(url)
            data = resp.json()
            return data.get("data", [])
        except Exception as exc:
            logger.warning("Semantic Scholar query failed for '%s': %s", query, exc)
            return []

    def _paper_to_item(self, paper: dict, product: str, category: str) -> ScrapedItem:
        title = paper.get("title", "Unknown")
        abstract = paper.get("abstract") or ""
        year = paper.get("year", "")
        authors = [a.get("name", "") for a in paper.get("authors", [])]
        venue = paper.get("venue", "")
        url = paper.get("url", "")
        external_ids = paper.get("externalIds", {})
        doi = external_ids.get("DOI", "")
        arxiv_id = external_ids.get("ArXiv", "")

        content = f"{title}\n\nAbstract:\n{abstract}"
        if not content.strip():
            content = title

        return ScrapedItem(
            source_url=url or f"https://doi.org/{doi}" if doi else "",
            source_name=self.name,
            category=category,
            title=title,
            content=content,
            product=product,
            metadata={
                "authors": authors,
                "year": year,
                "venue": venue,
                "doi": doi,
                "arxiv_id": arxiv_id,
                "paper_id": paper.get("paperId", ""),
            },
        )

    def scrape(self) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []
        seen_ids: set[str] = set()

        for query, product, category in ACADEMIC_QUERIES:
            logger.info("[Semantic Scholar] Querying: %s", query)
            papers = self._search(query)

            for paper in papers:
                pid = paper.get("paperId", "")
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
                item = self._paper_to_item(paper, product, category)
                if item.content.strip():
                    items.append(item)
                    logger.info("  -> %s (%s)", item.title[:60], paper.get("year"))

        return items


class ArXivScraper(BaseScraper):
    """Queries the arXiv API for relevant UAV/DJI papers."""

    name = "arXiv"
    API_URL = "http://export.arxiv.org/api/query"

    ARXIV_QUERIES = [
        ("DJI Matrice UAV", "M600", "hardware"),
        ("DJI Ground Station autonomous flight", "GS Pro", "use_case"),
        ("hexacopter flight controller protocol", "M600", "protocol"),
        ("UAV mission planning waypoint", "GS Pro", "use_case"),
    ]

    def _query_arxiv(self, query: str, max_results: int = 5) -> list[dict]:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
        }
        url = f"{self.API_URL}?{urlencode(params)}"
        try:
            resp = self.get(url)
            return self._parse_atom(resp.text)
        except Exception as exc:
            logger.warning("arXiv query failed for '%s': %s", query, exc)
            return []

    def _parse_atom(self, xml_text: str) -> list[dict]:
        NS = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        papers = []
        for entry in root.findall("atom:entry", NS):
            def txt(tag):
                el = entry.find(tag, NS)
                return el.text.strip() if el is not None and el.text else ""

            arxiv_id_raw = txt("atom:id").split("/abs/")[-1]
            authors = [
                a.find("atom:name", NS).text.strip()
                for a in entry.findall("atom:author", NS)
                if a.find("atom:name", NS) is not None
            ]
            papers.append(
                {
                    "arxiv_id": arxiv_id_raw,
                    "title": txt("atom:title").replace("\n", " "),
                    "abstract": txt("atom:summary").replace("\n", " "),
                    "authors": authors,
                    "published": txt("atom:published")[:10],
                    "url": f"https://arxiv.org/abs/{arxiv_id_raw}",
                }
            )
        return papers

    def scrape(self) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []
        seen: set[str] = set()

        for query, product, category in self.ARXIV_QUERIES:
            logger.info("[arXiv] Querying: %s", query)
            papers = self._query_arxiv(query)

            for p in papers:
                aid = p["arxiv_id"]
                if aid in seen:
                    continue
                seen.add(aid)

                content = f"{p['title']}\n\nAbstract:\n{p['abstract']}"
                item = ScrapedItem(
                    source_url=p["url"],
                    source_name=self.name,
                    category=category,
                    title=p["title"],
                    content=content,
                    product=product,
                    metadata={
                        "arxiv_id": aid,
                        "authors": p["authors"],
                        "published": p["published"],
                    },
                )
                items.append(item)
                logger.info("  -> %s (%s)", item.title[:60], p["published"][:4])

        return items


class GoogleScholarScraper(BaseScraper):
    """
    Scrapes Google Scholar search result pages (HTML, no API key).

    NOTE: Scholar rate-limits aggressively. This scraper uses conservative
    delays and a modest result count. For high-volume use, consider the
    SerpAPI (paid) or Semantic Scholar API instead.
    """

    name = "Google Scholar"
    SEARCH_URL = "https://scholar.google.com/scholar"

    SCHOLAR_QUERIES = [
        ("DJI Matrice 600 specifications", "M600", "spec"),
        ("DJI GS Pro ground control station", "GS Pro", "software"),
        ("DJI onboard SDK communication protocol", "M600", "protocol"),
    ]

    def __init__(self, **kwargs):
        super().__init__(delay=5.0, **kwargs)  # Extra polite to Scholar

    def _search(self, query: str) -> list[dict]:
        params = {"q": query, "num": 5}
        url = f"{self.SEARCH_URL}?{urlencode(params)}"
        try:
            html = self.fetch_html(url)
        except Exception as exc:
            logger.warning("Google Scholar request failed for '%s': %s", query, exc)
            return []

        soup = BeautifulSoup(html, "lxml")
        results = []

        for div in soup.select(".gs_ri"):
            title_el = div.select_one(".gs_rt a")
            snippet_el = div.select_one(".gs_rs")
            author_el = div.select_one(".gs_a")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            url_link = title_el.get("href", "")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            author_line = author_el.get_text(strip=True) if author_el else ""

            results.append(
                {
                    "title": title,
                    "url": url_link,
                    "snippet": snippet,
                    "author_line": author_line,
                }
            )

        return results

    def _parse_author_line(self, line: str) -> tuple[list[str], str, str]:
        """Parse 'Author A, Author B - Journal, Year - Publisher' format."""
        parts = line.split(" - ")
        authors = [a.strip() for a in parts[0].split(",")] if parts else []
        venue = parts[1].strip() if len(parts) > 1 else ""
        year_match = re.search(r"\b(19|20)\d{2}\b", line)
        year = year_match.group() if year_match else ""
        return authors, venue, year

    def scrape(self) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []

        for query, product, category in self.SCHOLAR_QUERIES:
            logger.info("[Google Scholar] Querying: %s", query)
            results = self._search(query)

            for r in results:
                authors, venue, year = self._parse_author_line(r["author_line"])
                content = r["snippet"] or r["title"]
                item = ScrapedItem(
                    source_url=r["url"],
                    source_name=self.name,
                    category=category,
                    title=r["title"],
                    content=content,
                    product=product,
                    metadata={
                        "authors": authors,
                        "venue": venue,
                        "year": year,
                        "search_query": query,
                    },
                )
                items.append(item)
                logger.info("  -> %s", r["title"][:60])

        return items
