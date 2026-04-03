"""Base scraper class with rate limiting, retry logic, and shared utilities."""

import time
import logging
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# Polite delay between requests (seconds)
DEFAULT_DELAY = 2.0
REQUEST_TIMEOUT = 30


@dataclass
class ScrapedItem:
    """A single piece of extracted research data."""
    source_url: str
    source_name: str          # e.g. "DJI Official", "DJI Forum", "Google Scholar"
    category: str             # hardware / software / protocol / spec / use_case
    title: str
    content: str
    product: str              # "M600" | "GS Pro" | "both"
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    content_hash: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]


class BaseScraper(ABC):
    """Abstract base for all scrapers in this system."""

    name: str = "BaseScraper"
    base_url: str = ""

    def __init__(self, delay: float = DEFAULT_DELAY, raw_dir: Optional[Path] = None):
        self.delay = delay
        self.raw_dir = raw_dir or Path("data/raw")
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self._last_request: float = 0.0
        self.session = httpx.Client(
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; AcademicResearchBot/1.0; "
                    "+https://github.com/research/dji-m600)"
                )
            },
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )

    def _throttle(self):
        elapsed = time.time() - self._last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
    )
    def get(self, url: str, **kwargs) -> httpx.Response:
        self._throttle()
        logger.debug("GET %s", url)
        resp = self.session.get(url, **kwargs)
        resp.raise_for_status()
        return resp

    def cache_path(self, url: str) -> Path:
        slug = hashlib.md5(url.encode()).hexdigest()
        domain = urlparse(url).netloc.replace(".", "_")
        return self.raw_dir / f"{domain}_{slug}.html"

    def get_cached(self, url: str) -> Optional[str]:
        p = self.cache_path(url)
        if p.exists():
            logger.debug("Cache hit: %s", url)
            return p.read_text(encoding="utf-8")
        return None

    def save_cache(self, url: str, content: str):
        self.cache_path(url).write_text(content, encoding="utf-8")

    def fetch_html(self, url: str) -> str:
        cached = self.get_cached(url)
        if cached:
            return cached
        resp = self.get(url)
        html = resp.text
        self.save_cache(url, html)
        return html

    @abstractmethod
    def scrape(self) -> list[ScrapedItem]:
        """Perform the full scrape and return a list of ScrapedItems."""

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
