"""
Orchestrates all scrapers and stores results to the database.

Usage:
    python -m src.scraper.runner [--sources all|dji|pdf|forums|academic]
"""

import argparse
import logging
import sys
from pathlib import Path

from src.scraper.dji_official import DJIOfficialScraper
from src.scraper.pdf_parser import PDFParser
from src.scraper.forums import DJIForumScraper, PhantomPilotsScraper
from src.scraper.academic import SemanticScholarScraper, ArXivScraper, GoogleScholarScraper
from src.database.store import ResearchDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
PDF_DIR = Path("data/pdfs")
DB_PATH = Path("data/research.db")


def run_all(sources: str = "all") -> int:
    db = ResearchDatabase(DB_PATH)
    total = 0

    scrapers = []
    if sources in ("all", "dji"):
        scrapers.append(DJIOfficialScraper(raw_dir=RAW_DIR))
    if sources in ("all", "pdf"):
        scrapers.append(PDFParser(pdf_dir=PDF_DIR, raw_dir=RAW_DIR))
    if sources in ("all", "forums"):
        scrapers.append(DJIForumScraper(raw_dir=RAW_DIR))
        scrapers.append(PhantomPilotsScraper(raw_dir=RAW_DIR))
    if sources in ("all", "academic"):
        scrapers.append(SemanticScholarScraper(raw_dir=RAW_DIR))
        scrapers.append(ArXivScraper(raw_dir=RAW_DIR))
        scrapers.append(GoogleScholarScraper(raw_dir=RAW_DIR))

    for scraper in scrapers:
        logger.info("=== Running: %s ===", scraper.name)
        try:
            with scraper:
                items = scraper.scrape()
            saved = db.save_items(items)
            logger.info("  Saved %d / %d items (duplicates skipped)", saved, len(items))
            total += saved
        except Exception as exc:
            logger.error("Scraper %s crashed: %s", scraper.name, exc, exc_info=True)

    logger.info("=== Done. Total new items saved: %d ===", total)
    db.print_summary()
    return total


def main():
    parser = argparse.ArgumentParser(description="Run DJI M600 research scrapers")
    parser.add_argument(
        "--sources",
        choices=["all", "dji", "pdf", "forums", "academic"],
        default="all",
        help="Which scrapers to run (default: all)",
    )
    args = parser.parse_args()
    run_all(args.sources)


if __name__ == "__main__":
    main()
