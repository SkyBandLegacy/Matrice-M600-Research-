"""
Forum scrapers for DJI Forum and Phantom Pilots.

Focuses on threads tagged with M600 / GS Pro technical topics:
  - Hardware troubleshooting → hardware category
  - Protocol/communication questions → protocol category
  - Flight planning with GS Pro → use_case category
"""

import logging
import re
from urllib.parse import urljoin, urlencode

from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)

# Search queries to run on each forum
SEARCH_QUERIES = [
    ("M600 communication protocol", "M600", "protocol"),
    ("Matrice 600 hardware components", "M600", "hardware"),
    ("Matrice 600 Pro specifications", "M600", "spec"),
    ("GS Pro mission planning", "GS Pro", "use_case"),
    ("GS Pro waypoint protocol", "GS Pro", "protocol"),
    ("M600 onboard SDK", "M600", "protocol"),
    ("M600 flight controller", "M600", "hardware"),
    ("Matrice 600 battery", "M600", "hardware"),
    ("DJI A3 flight controller", "M600", "hardware"),
    ("Lightbridge 2 datalink", "M600", "protocol"),
]

MAX_THREADS_PER_QUERY = 3  # Stay polite


class DJIForumScraper(BaseScraper):
    """Scrapes forum.dji.com search results."""

    name = "DJI Forum"
    base_url = "https://forum.dji.com"

    SEARCH_URL = "https://forum.dji.com/search.php"

    def _search_threads(self, query: str) -> list[str]:
        """Return thread URLs for a search query."""
        params = {"q": query, "t": "thread"}
        try:
            html = self.fetch_html(f"{self.SEARCH_URL}?{urlencode(params)}")
        except Exception as exc:
            logger.warning("DJI Forum search failed for '%s': %s", query, exc)
            return []

        soup = BeautifulSoup(html, "lxml")
        links = []
        for a in soup.select("a[href*='thread']"):
            href = a.get("href", "")
            full = urljoin(self.base_url, href)
            if full not in links:
                links.append(full)
        return links[:MAX_THREADS_PER_QUERY]

    def _parse_thread(self, url: str) -> tuple[str, list[str]]:
        """Return (title, [post_texts]) from a forum thread page."""
        try:
            html = self.fetch_html(url)
        except Exception as exc:
            logger.warning("Could not fetch thread %s: %s", url, exc)
            return ("", [])

        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        title_el = soup.find(["h1", "h2", '[class*="title"]'])
        title = title_el.get_text(strip=True) if title_el else url

        posts = []
        for post_div in soup.select('[class*="post-message"], [class*="message-content"], article'):
            text = post_div.get_text(separator=" ", strip=True)
            if len(text) > 80:
                posts.append(text)

        return title, posts

    def scrape(self) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []

        for query, product, category in SEARCH_QUERIES:
            logger.info("[DJI Forum] Searching: %s", query)
            thread_urls = self._search_threads(query)

            for url in thread_urls:
                title, posts = self._parse_thread(url)
                if not posts:
                    continue
                combined = "\n\n---\n\n".join(posts)
                item = ScrapedItem(
                    source_url=url,
                    source_name=self.name,
                    category=category,
                    title=title or query,
                    content=combined,
                    product=product,
                    metadata={"search_query": query, "post_count": len(posts)},
                )
                items.append(item)
                logger.info("  -> %d posts from: %s", len(posts), title[:60])

        return items


class PhantomPilotsScraper(BaseScraper):
    """Scrapes phantompilots.com for M600/GS Pro technical threads."""

    name = "Phantom Pilots Forum"
    base_url = "https://phantompilots.com"
    SEARCH_URL = "https://phantompilots.com/search/"

    def _search_threads(self, query: str) -> list[str]:
        params = {"q": query, "t": "post"}
        try:
            html = self.fetch_html(f"{self.SEARCH_URL}?{urlencode(params)}")
        except Exception as exc:
            logger.warning("PhantomPilots search failed for '%s': %s", query, exc)
            return []

        soup = BeautifulSoup(html, "lxml")
        links = []
        for a in soup.select("a[href*='/threads/']"):
            href = a.get("href", "")
            full = urljoin(self.base_url, href)
            # Deduplicate (strip page anchors)
            base_link = full.split("#")[0]
            if base_link not in links:
                links.append(base_link)
        return links[:MAX_THREADS_PER_QUERY]

    def _parse_thread(self, url: str) -> tuple[str, list[str]]:
        try:
            html = self.fetch_html(url)
        except Exception as exc:
            logger.warning("Could not fetch thread %s: %s", url, exc)
            return ("", [])

        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()

        title_el = soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else url

        posts = []
        for el in soup.select(".message-body, .bbWrapper, article .content"):
            text = el.get_text(separator=" ", strip=True)
            if len(text) > 80:
                posts.append(text)

        return title, posts

    def scrape(self) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []

        for query, product, category in SEARCH_QUERIES:
            logger.info("[Phantom Pilots] Searching: %s", query)
            thread_urls = self._search_threads(query)

            for url in thread_urls:
                title, posts = self._parse_thread(url)
                if not posts:
                    continue
                combined = "\n\n---\n\n".join(posts)
                item = ScrapedItem(
                    source_url=url,
                    source_name=self.name,
                    category=category,
                    title=title or query,
                    content=combined,
                    product=product,
                    metadata={"search_query": query, "post_count": len(posts)},
                )
                items.append(item)

        return items
