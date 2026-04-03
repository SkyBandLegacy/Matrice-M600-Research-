"""
High-level database interface.

Wraps SQLAlchemy sessions behind simple save/query methods so that the
rest of the application doesn't need to know SQLAlchemy details.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.database.schema import Base, ItemTag, ResearchItem, Source, Tag, init_db
from src.scraper.base import ScrapedItem

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"hardware", "software", "protocol", "spec", "use_case"}
VALID_PRODUCTS = {"M600", "GS Pro", "both"}


def _normalise_category(cat: str) -> str:
    cat = cat.lower().strip()
    mapping = {
        "hardware": "hardware",
        "software": "software",
        "protocol": "protocol",
        "spec": "spec",
        "specifications": "spec",
        "use_case": "use_case",
        "use case": "use_case",
        "application": "use_case",
    }
    return mapping.get(cat, "hardware")


class ResearchDatabase:
    def __init__(self, db_path: Path = Path("data/research.db")):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = init_db(f"sqlite:///{db_path}")

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save_items(self, items: list[ScrapedItem]) -> int:
        """Save a list of ScrapedItems; skip duplicates. Returns count saved."""
        saved = 0
        with Session(self.engine) as session:
            for item in items:
                if not item.content.strip():
                    continue

                # Upsert source
                source = (
                    session.query(Source)
                    .filter_by(url=item.source_url, source_name=item.source_name)
                    .first()
                )
                if source is None:
                    source = Source(
                        url=item.source_url,
                        source_name=item.source_name,
                    )
                    # Populate citation fields from metadata if available
                    meta = item.metadata or {}
                    source.authors = meta.get("authors")
                    source.year = str(meta.get("year", "")) or None
                    source.title = item.title
                    source.venue = meta.get("venue")
                    source.doi = meta.get("doi")
                    source.arxiv_id = meta.get("arxiv_id")
                    session.add(source)
                    session.flush()

                # Skip duplicate content
                existing = (
                    session.query(ResearchItem)
                    .filter_by(content_hash=item.content_hash)
                    .first()
                )
                if existing:
                    continue

                # scraped_at is stored as ISO string in ScrapedItem; convert to datetime
                try:
                    scraped_dt = datetime.fromisoformat(item.scraped_at)
                except (ValueError, TypeError):
                    scraped_dt = datetime.utcnow()

                db_item = ResearchItem(
                    source_id=source.id,
                    category=_normalise_category(item.category),
                    product=item.product if item.product in VALID_PRODUCTS else "M600",
                    title=item.title,
                    content=item.content,
                    content_hash=item.content_hash,
                    scraped_at=scraped_dt,
                    metadata_=item.metadata,
                )
                session.add(db_item)
                saved += 1

            session.commit()
        return saved

    def add_tag(self, item_id: int, tag_name: str):
        with Session(self.engine) as session:
            tag = session.query(Tag).filter_by(name=tag_name).first()
            if tag is None:
                tag = Tag(name=tag_name)
                session.add(tag)
                session.flush()
            link = session.query(ItemTag).filter_by(item_id=item_id, tag_id=tag.id).first()
            if not link:
                session.add(ItemTag(item_id=item_id, tag_id=tag.id))
            session.commit()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def query_items(
        self,
        product: Optional[str] = None,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Flexible query returning a list of dicts for easy display."""
        with Session(self.engine) as session:
            q = session.query(ResearchItem).join(Source)

            if product and product != "all":
                q = q.filter(
                    (ResearchItem.product == product) | (ResearchItem.product == "both")
                )
            if category:
                q = q.filter(ResearchItem.category == _normalise_category(category))
            if keyword:
                kw = f"%{keyword.lower()}%"
                q = q.filter(
                    ResearchItem.title.ilike(kw) | ResearchItem.content.ilike(kw)
                )

            rows = q.order_by(ResearchItem.scraped_at.desc()).limit(limit).all()

            results = []
            for row in rows:
                results.append(
                    {
                        "id": row.id,
                        "title": row.title,
                        "category": row.category,
                        "product": row.product,
                        "content_preview": row.content[:300] + "..."
                        if len(row.content) > 300
                        else row.content,
                        "content": row.content,
                        "source_name": row.source_rel.source_name,
                        "source_url": row.source_rel.url,
                        "authors": row.source_rel.authors,
                        "year": row.source_rel.year,
                        "doi": row.source_rel.doi,
                        "scraped_at": str(row.scraped_at),
                        "metadata": row.metadata_,
                    }
                )
        return results

    def get_all_sources(self) -> list[dict]:
        with Session(self.engine) as session:
            sources = session.query(Source).order_by(Source.source_name).all()
            return [
                {
                    "id": s.id,
                    "url": s.url,
                    "source_name": s.source_name,
                    "title": s.title,
                    "authors": s.authors,
                    "year": s.year,
                    "venue": s.venue,
                    "doi": s.doi,
                    "arxiv_id": s.arxiv_id,
                    "first_scraped": str(s.first_scraped),
                }
                for s in sources
            ]

    def get_stats(self) -> dict:
        with Session(self.engine) as session:
            total = session.query(ResearchItem).count()
            by_cat = {}
            for cat in VALID_CATEGORIES:
                by_cat[cat] = (
                    session.query(ResearchItem).filter_by(category=cat).count()
                )
            by_product = {}
            for prod in VALID_PRODUCTS:
                by_product[prod] = (
                    session.query(ResearchItem).filter_by(product=prod).count()
                )
            sources = session.query(Source).count()
        return {
            "total_items": total,
            "by_category": by_cat,
            "by_product": by_product,
            "total_sources": sources,
        }

    def print_summary(self):
        stats = self.get_stats()
        logger.info("--- Database Summary ---")
        logger.info("Total items: %d", stats["total_items"])
        logger.info("Sources: %d", stats["total_sources"])
        for cat, count in stats["by_category"].items():
            logger.info("  %-12s %d", cat, count)

    def export_json(self, output_path: Path, **filters):
        items = self.query_items(**filters, limit=10000)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(items, indent=2, default=str))
        logger.info("Exported %d items to %s", len(items), output_path)
