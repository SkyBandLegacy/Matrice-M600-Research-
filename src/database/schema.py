"""
SQLAlchemy ORM models for the research database.

Tables:
  - research_items   : all scraped content
  - sources          : deduplicated source/citation records
  - tags             : freeform keyword tags per item
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship


class Base(DeclarativeBase):
    pass


class Source(Base):
    """Represents a unique source (URL + source name)."""

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(Text, nullable=False)
    source_name = Column(String(100), nullable=False)
    first_scraped = Column(DateTime, default=datetime.utcnow)

    # Citation fields (may be populated later by citation manager)
    authors = Column(JSON, nullable=True)         # list of author strings
    year = Column(String(10), nullable=True)
    title = Column(Text, nullable=True)
    venue = Column(Text, nullable=True)           # journal / conference / website
    doi = Column(String(200), nullable=True)
    arxiv_id = Column(String(50), nullable=True)

    items = relationship("ResearchItem", back_populates="source_rel")

    __table_args__ = (UniqueConstraint("url", "source_name", name="uq_source"),)

    def __repr__(self):
        return f"<Source id={self.id} name={self.source_name!r} url={self.url[:50]!r}>"


class ResearchItem(Base):
    """A single extracted knowledge unit."""

    __tablename__ = "research_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)

    # Classification
    category = Column(
        String(30), nullable=False, index=True
    )  # hardware|software|protocol|spec|use_case
    product = Column(String(20), nullable=False, index=True)  # M600|GS Pro|both
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(32), unique=True, nullable=False)

    # Provenance
    scraped_at = Column(DateTime, default=datetime.utcnow)
    metadata_ = Column("metadata", JSON, nullable=True)

    source_rel = relationship("Source", back_populates="items")
    tags = relationship("Tag", secondary="item_tags", back_populates="items")

    def __repr__(self):
        return (
            f"<ResearchItem id={self.id} cat={self.category!r} "
            f"product={self.product!r} title={self.title[:40]!r}>"
        )


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(80), unique=True, nullable=False)

    items = relationship("ResearchItem", secondary="item_tags", back_populates="tags")


class ItemTag(Base):
    __tablename__ = "item_tags"

    item_id = Column(Integer, ForeignKey("research_items.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)


def init_db(db_url: str = "sqlite:///data/research.db"):
    """Create all tables and return the engine."""
    engine = create_engine(db_url, echo=False, future=True)

    # Enable WAL mode for SQLite to allow concurrent reads
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return engine
