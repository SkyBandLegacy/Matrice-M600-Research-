"""
Citation Manager.

Generates APA 7th edition citations from source records in the database.
Supports:
  - Webpages / online documentation
  - Academic papers (journal, conference, preprint)
  - Technical manuals / reports
  - Forum posts
  - arXiv preprints

Export formats:
  - APA text (plain)
  - BibTeX
  - Word-ready bibliography (via python-docx)
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# Data model
# -----------------------------------------------------------------------

@dataclass
class Citation:
    """All fields needed to produce a complete APA citation."""

    # Core identification
    source_id: int
    url: str
    source_name: str

    # Bibliographic
    authors: list[str] = field(default_factory=list)
    year: Optional[str] = None
    title: Optional[str] = None
    venue: Optional[str] = None        # journal / conference / website name
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    publisher: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    access_date: Optional[str] = None  # for webpages

    # Internal
    source_type: str = "webpage"       # webpage|journal|conference|manual|forum|arxiv

    def __post_init__(self):
        if not self.access_date:
            self.access_date = datetime.utcnow().strftime("%Y, %B %d")
        if not self.year:
            self.year = datetime.utcnow().strftime("%Y")


# -----------------------------------------------------------------------
# APA formatter
# -----------------------------------------------------------------------

def _fmt_authors_apa(authors: list[str]) -> str:
    """Format author list in APA style (Last, F. M., & Last, F. M.).

    Handles two input conventions:
      - "Last, First M."  (already Last-First — returned as-is)
      - "First M. Last"   (natural order — converted to Last, F. M.)
    """
    if not authors:
        return ""

    formatted = []
    for name in authors[:20]:  # APA caps at 20 before et al.
        name = name.strip()
        if not name:
            continue
        if "," in name:
            # Already in "Last, First" APA format — use as-is
            formatted.append(name)
        else:
            parts = name.split()
            if len(parts) >= 2:
                last = parts[-1]
                initials = ". ".join(p[0].upper() for p in parts[:-1]) + "."
                formatted.append(f"{last}, {initials}")
            else:
                formatted.append(name)

    if len(authors) > 20:
        formatted = formatted[:19] + ["...", _fmt_authors_apa([authors[-1]])]
        return ", ".join(formatted)

    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]}, & {formatted[1]}"
    else:
        return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"


def _italicise_bibtex(text: str) -> str:
    return text


def _clean(text: Optional[str]) -> str:
    return (text or "").strip()


class APAFormatter:
    """Produces APA 7th edition citation strings."""

    def format(self, c: Citation) -> str:
        dispatch = {
            "journal": self._journal,
            "conference": self._conference,
            "arxiv": self._arxiv,
            "manual": self._manual,
            "forum": self._forum,
            "webpage": self._webpage,
        }
        fn = dispatch.get(c.source_type, self._webpage)
        return fn(c)

    def _journal(self, c: Citation) -> str:
        author_str = _fmt_authors_apa(c.authors)
        title = _clean(c.title)
        venue = _clean(c.venue)
        year = _clean(c.year)
        vol_iss = ""
        if c.volume:
            vol_iss = f", *{c.volume}*"
            if c.issue:
                vol_iss += f"({c.issue})"
        pages = f", {c.pages}" if c.pages else ""
        doi = f" https://doi.org/{c.doi}" if c.doi else (f" {c.url}" if c.url else "")

        parts = [f"{author_str} ({year}). {title}. *{venue}*{vol_iss}{pages}.{doi}"]
        return "".join(parts)

    def _conference(self, c: Citation) -> str:
        author_str = _fmt_authors_apa(c.authors)
        title = _clean(c.title)
        venue = _clean(c.venue)
        year = _clean(c.year)
        doi = f" https://doi.org/{c.doi}" if c.doi else (f" {c.url}" if c.url else "")
        return f"{author_str} ({year}). {title}. In *{venue}*.{doi}"

    def _arxiv(self, c: Citation) -> str:
        author_str = _fmt_authors_apa(c.authors)
        title = _clean(c.title)
        year = _clean(c.year)
        arxiv_id = _clean(c.arxiv_id)
        url = c.url or f"https://arxiv.org/abs/{arxiv_id}"
        return f"{author_str} ({year}). *{title}*. arXiv. {url}"

    def _manual(self, c: Citation) -> str:
        author_str = _fmt_authors_apa(c.authors) or "DJI"
        title = _clean(c.title)
        year = _clean(c.year)
        publisher = _clean(c.publisher) or "DJI"
        url = f" {c.url}" if c.url else ""
        return f"{author_str} ({year}). *{title}*. {publisher}.{url}"

    def _forum(self, c: Citation) -> str:
        author_str = _fmt_authors_apa(c.authors) or "Anonymous"
        title = _clean(c.title)
        year = _clean(c.year)
        venue = _clean(c.venue) or c.source_name
        url = c.url or ""
        return (
            f"{author_str} ({year}). {title} [Forum post]. *{venue}*. {url}"
        )

    def _webpage(self, c: Citation) -> str:
        author_str = _fmt_authors_apa(c.authors) or "DJI"
        title = _clean(c.title)
        year = _clean(c.year)
        venue = _clean(c.venue) or c.source_name
        url = c.url or ""
        access = c.access_date or ""
        return (
            f"{author_str} ({year}). *{title}*. {venue}. Retrieved {access}, from {url}"
        )


# -----------------------------------------------------------------------
# BibTeX formatter
# -----------------------------------------------------------------------

def _bibtex_key(c: Citation) -> str:
    if c.authors:
        first_author = c.authors[0].strip()
        # "Last, First" format → extract before the comma
        last = first_author.split(",")[0].split()[-1] if "," in first_author else first_author.split()[-1]
    else:
        last = "Unknown"
    year = c.year or "0000"
    title_word = re.sub(r"[^\w]", "", (c.title or "").split()[0]).lower() if c.title else "untitled"
    return f"{last.lower()}{year}{title_word}"


class BibTeXFormatter:
    def format(self, c: Citation) -> str:
        key = _bibtex_key(c)
        author_str = " and ".join(c.authors) if c.authors else "Unknown"
        fields: list[tuple[str, str]] = [
            ("author", author_str),
            ("title", _clean(c.title)),
            ("year", _clean(c.year)),
        ]
        if c.source_type == "journal":
            entry_type = "article"
            fields += [("journal", _clean(c.venue))]
            if c.volume:
                fields.append(("volume", c.volume))
            if c.issue:
                fields.append(("number", c.issue))
            if c.pages:
                fields.append(("pages", c.pages))
        elif c.source_type == "conference":
            entry_type = "inproceedings"
            fields += [("booktitle", _clean(c.venue))]
        elif c.source_type == "arxiv":
            entry_type = "misc"
            fields += [("eprint", _clean(c.arxiv_id)), ("archivePrefix", "arXiv")]
        elif c.source_type == "manual":
            entry_type = "manual"
            fields += [("organization", _clean(c.publisher) or "DJI")]
        else:
            entry_type = "misc"
            fields += [("howpublished", f"\\url{{{c.url}}}")]

        if c.doi:
            fields.append(("doi", c.doi))
        if c.url and c.source_type not in ("journal",):
            fields.append(("url", c.url))
        if c.access_date:
            fields.append(("note", f"Accessed: {c.access_date}"))

        field_str = "\n".join(
            f"  {k:<16} = {{{v}}},"
            for k, v in fields
            if v.strip()
        )
        return f"@{entry_type}{{{key},\n{field_str}\n}}"


# -----------------------------------------------------------------------
# Citation Manager
# -----------------------------------------------------------------------

class CitationManager:
    def __init__(self, db_sources: list[dict]):
        """
        db_sources: list of source dicts from ResearchDatabase.get_all_sources()
        """
        self.citations: list[Citation] = []
        self.apa = APAFormatter()
        self.bibtex = BibTeXFormatter()
        self._load_sources(db_sources)

    def _detect_source_type(self, source: dict) -> str:
        name = source.get("source_name", "").lower()
        url = source.get("url", "").lower()
        if "arxiv" in url or "arxiv" in name:
            return "arxiv"
        if "scholar" in name or source.get("doi"):
            return "journal"
        if "forum" in name or "forum" in url:
            return "forum"
        if ".pdf" in url or "manual" in (source.get("title") or "").lower():
            return "manual"
        if "semantic" in name:
            return "journal"
        return "webpage"

    def _load_sources(self, sources: list[dict]):
        for s in sources:
            c = Citation(
                source_id=s.get("id", 0),
                url=s.get("url", ""),
                source_name=s.get("source_name", ""),
                authors=s.get("authors") or [],
                year=s.get("year"),
                title=s.get("title"),
                venue=s.get("venue") or s.get("source_name"),
                doi=s.get("doi"),
                arxiv_id=s.get("arxiv_id"),
                source_type=self._detect_source_type(s),
            )
            self.citations.append(c)

    def get_apa_bibliography(self) -> list[str]:
        """Return sorted list of APA citation strings."""
        refs = [self.apa.format(c) for c in self.citations]
        return sorted(refs, key=lambda r: r.lstrip("*").lower())

    def get_bibtex(self) -> str:
        entries = [self.bibtex.format(c) for c in self.citations]
        return "\n\n".join(entries)

    def export_apa_txt(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = self.get_apa_bibliography()
        path.write_text("\n\n".join(lines), encoding="utf-8")
        logger.info("APA bibliography written to %s (%d refs)", path, len(lines))

    def export_bibtex(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.get_bibtex(), encoding="utf-8")
        logger.info("BibTeX file written to %s", path)

    def export_apa_docx(self, path: Path):
        """Write an APA-formatted bibliography to a Word document."""
        try:
            from docx import Document
            from docx.shared import Pt, Inches
            from docx.enum.text import WD_ALIGN_PARAGRAPH
        except ImportError:
            logger.error("python-docx not installed. Run: pip install python-docx")
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        doc = Document()

        # Heading
        heading = doc.add_heading("References", level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

        refs = self.get_apa_bibliography()
        for ref in refs:
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.LEFT

            # Hanging indent (APA style)
            fmt = para.paragraph_format
            fmt.left_indent = Inches(0.5)
            fmt.first_line_indent = Inches(-0.5)

            # Handle *italics* markdown
            parts = re.split(r"(\*[^*]+\*)", ref)
            for part in parts:
                if part.startswith("*") and part.endswith("*"):
                    run = para.add_run(part[1:-1])
                    run.italic = True
                else:
                    para.add_run(part)

            para.add_run("")  # Ensure paragraph ends cleanly
            # Add spacing between entries
            fmt.space_after = Pt(12)

        doc.save(str(path))
        logger.info("APA bibliography Word doc written to %s", path)

    def print_bibliography(self):
        refs = self.get_apa_bibliography()
        print("\n" + "=" * 70)
        print("REFERENCES")
        print("=" * 70)
        for i, ref in enumerate(refs, 1):
            clean = re.sub(r"\*([^*]+)\*", r"\1", ref)
            print(f"\n[{i}] {clean}")
        print("\n" + "=" * 70)
        print(f"Total references: {len(refs)}")
