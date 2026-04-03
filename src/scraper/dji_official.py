"""
Scraper for DJI official documentation pages.

Targets:
  - M600 Pro product page & specs
  - GS Pro product page & specs
  - DJI Developer documentation (SDK, protocols)
  - DJI Download Center (manuals list)
"""

import logging
from pathlib import Path

from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)

# Public DJI pages with stable paths
DJI_TARGETS = [
    {
        "url": "https://www.dji.com/matrice600-pro/info",
        "product": "M600",
        "category": "spec",
        "title": "DJI Matrice 600 Pro - Specs",
    },
    {
        "url": "https://www.dji.com/matrice600-pro",
        "product": "M600",
        "category": "hardware",
        "title": "DJI Matrice 600 Pro - Overview",
    },
    {
        "url": "https://www.dji.com/ground-station-pro",
        "product": "GS Pro",
        "category": "software",
        "title": "DJI GS Pro - Overview",
    },
    {
        "url": "https://www.dji.com/ground-station-pro/info",
        "product": "GS Pro",
        "category": "spec",
        "title": "DJI GS Pro - Specs",
    },
    {
        "url": "https://developer.dji.com/mobile-sdk/documentation/introduction/product_introduction.html",
        "product": "both",
        "category": "protocol",
        "title": "DJI Mobile SDK - Product Introduction",
    },
    {
        "url": "https://developer.dji.com/onboard-sdk/documentation/introduction/index.html",
        "product": "M600",
        "category": "protocol",
        "title": "DJI Onboard SDK - Introduction",
    },
]

# CSS selectors used to pull meaningful content blocks
CONTENT_SELECTORS = [
    "article",
    "main",
    '[class*="spec"]',
    '[class*="feature"]',
    '[class*="content"]',
    '[class*="param"]',
    "table",
    "section",
]


class DJIOfficialScraper(BaseScraper):
    name = "DJI Official"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _extract_text(self, soup: BeautifulSoup, url: str) -> str:
        """Extract meaningful text from a DJI page."""
        # Try structured selectors first
        for sel in CONTENT_SELECTORS:
            blocks = soup.select(sel)
            if blocks:
                texts = [b.get_text(separator=" ", strip=True) for b in blocks]
                combined = "\n\n".join(t for t in texts if len(t) > 50)
                if combined:
                    return combined
        # Fallback: body text
        body = soup.find("body")
        return body.get_text(separator=" ", strip=True) if body else ""

    def _extract_specs_table(self, soup: BeautifulSoup) -> dict:
        """Extract key-value spec tables into a dict."""
        specs = {}
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["th", "td"])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    val = cells[1].get_text(strip=True)
                    if key and val:
                        specs[key] = val
        return specs

    def scrape(self) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []

        for target in DJI_TARGETS:
            url = target["url"]
            logger.info("[DJI Official] Scraping: %s", url)
            try:
                html = self.fetch_html(url)
                soup = BeautifulSoup(html, "lxml")

                # Remove script/style noise
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()

                text = self._extract_text(soup, url)
                specs = self._extract_specs_table(soup)

                if not text.strip():
                    logger.warning("No content extracted from %s", url)
                    continue

                item = ScrapedItem(
                    source_url=url,
                    source_name=self.name,
                    category=target["category"],
                    title=target["title"],
                    content=text,
                    product=target["product"],
                    metadata={"specs_table": specs} if specs else {},
                )
                items.append(item)
                logger.info("  -> Extracted %d chars", len(text))

            except Exception as exc:
                logger.error("Failed to scrape %s: %s", url, exc)

        return items
