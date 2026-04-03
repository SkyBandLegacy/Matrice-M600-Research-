"""
PDF parser for DJI technical manuals and academic papers.

Supports both local PDFs (dropped into data/pdfs/) and remote PDF URLs.
Extracts:
  - Full text by section
  - Tables (specs)
  - Figures captions
  - References list
"""

import logging
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from .base import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)

# Known DJI manual PDF URLs (public download links)
DJI_MANUAL_URLS = [
    {
        "url": "https://dl.djicdn.com/downloads/matrice600/20160831/Matrice_600_User_Manual_v1.2.pdf",
        "product": "M600",
        "title": "Matrice 600 User Manual v1.2",
        "category": "hardware",
    },
    {
        "url": "https://dl.djicdn.com/downloads/matrice600pro/Matrice_600_Pro_User_Manual_v1.0_EN.pdf",
        "product": "M600",
        "title": "Matrice 600 Pro User Manual v1.0",
        "category": "hardware",
    },
    {
        "url": "https://dl.djicdn.com/downloads/matrice600/20161010/Matrice_600_Advanced_User_Guide_v1.0.pdf",
        "product": "M600",
        "title": "Matrice 600 Advanced User Guide v1.0",
        "category": "hardware",
    },
]

# Patterns to detect section headings
SECTION_RE = re.compile(
    r"^(\d+[\.\d]*\s+|[A-Z][A-Z\s]{4,}$)",
    re.MULTILINE,
)

REFERENCE_RE = re.compile(
    r"^\[?\d+\]?\s+[A-Z].{20,}",
    re.MULTILINE,
)


def _try_import_fitz():
    try:
        import fitz  # PyMuPDF
        return fitz
    except ImportError:
        return None


def _try_import_pdfplumber():
    try:
        import pdfplumber
        return pdfplumber
    except ImportError:
        return None


class PDFParser(BaseScraper):
    name = "PDF Parser"

    def __init__(self, pdf_dir: Optional[Path] = None, **kwargs):
        super().__init__(**kwargs)
        self.pdf_dir = pdf_dir or Path("data/pdfs")
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Download helpers
    # ------------------------------------------------------------------

    def download_pdf(self, url: str, dest: Path) -> Path:
        if dest.exists():
            logger.debug("PDF already downloaded: %s", dest.name)
            return dest
        logger.info("Downloading PDF: %s", url)
        resp = self.get(url)
        dest.write_bytes(resp.content)
        return dest

    # ------------------------------------------------------------------
    # Text extraction
    # ------------------------------------------------------------------

    def extract_text_fitz(self, pdf_path: Path) -> list[dict]:
        """Extract pages with PyMuPDF (preferred — handles complex layouts)."""
        fitz = _try_import_fitz()
        if fitz is None:
            return []
        pages = []
        doc = fitz.open(str(pdf_path))
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            pages.append({"page": page_num, "text": text})
        doc.close()
        return pages

    def extract_text_pdfplumber(self, pdf_path: Path) -> list[dict]:
        """Fallback extractor using pdfplumber."""
        pdfplumber = _try_import_pdfplumber()
        if pdfplumber is None:
            return []
        pages = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append({"page": page_num, "text": text})
        return pages

    def extract_tables_pdfplumber(self, pdf_path: Path) -> list[dict]:
        """Extract tables from PDF pages."""
        pdfplumber = _try_import_pdfplumber()
        if pdfplumber is None:
            return []
        tables = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                for tbl in page.extract_tables():
                    if tbl:
                        tables.append({"page": page_num, "table": tbl})
        return tables

    def extract_pages(self, pdf_path: Path) -> list[dict]:
        pages = self.extract_text_fitz(pdf_path)
        if not pages:
            pages = self.extract_text_pdfplumber(pdf_path)
        return pages

    # ------------------------------------------------------------------
    # Section splitting
    # ------------------------------------------------------------------

    def split_sections(self, full_text: str) -> list[dict]:
        """Split full document text into named sections."""
        sections = []
        current_title = "Introduction"
        current_lines: list[str] = []

        for line in full_text.splitlines():
            stripped = line.strip()
            if SECTION_RE.match(stripped) and len(stripped) < 120:
                if current_lines:
                    sections.append(
                        {
                            "title": current_title,
                            "text": "\n".join(current_lines).strip(),
                        }
                    )
                current_title = stripped
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            sections.append(
                {"title": current_title, "text": "\n".join(current_lines).strip()}
            )
        return sections

    def extract_references(self, full_text: str) -> list[str]:
        return REFERENCE_RE.findall(full_text)

    # ------------------------------------------------------------------
    # Main scrape
    # ------------------------------------------------------------------

    def parse_pdf(self, pdf_path: Path, meta: dict) -> list[ScrapedItem]:
        """Parse a single PDF into ScrapedItems (one per meaningful section)."""
        items: list[ScrapedItem] = []
        pages = self.extract_pages(pdf_path)
        if not pages:
            logger.warning("Could not extract text from %s", pdf_path)
            return items

        full_text = "\n".join(p["text"] for p in pages)
        sections = self.split_sections(full_text)
        references = self.extract_references(full_text)

        tables = self.extract_tables_pdfplumber(pdf_path)

        for sec in sections:
            if len(sec["text"]) < 100:
                continue
            item = ScrapedItem(
                source_url=meta.get("url", str(pdf_path)),
                source_name=f"PDF: {meta.get('title', pdf_path.stem)}",
                category=meta.get("category", "hardware"),
                title=f"{meta.get('title', pdf_path.stem)} — {sec['title']}",
                content=sec["text"],
                product=meta.get("product", "M600"),
                metadata={
                    "pdf_file": str(pdf_path),
                    "section": sec["title"],
                    "total_pages": len(pages),
                    "tables_found": len(tables),
                    "references": references[:10],
                },
            )
            items.append(item)

        return items

    def scrape(self) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []

        # 1. Download and parse known DJI manuals
        for manual in DJI_MANUAL_URLS:
            filename = urlparse(manual["url"]).path.split("/")[-1]
            dest = self.pdf_dir / filename
            try:
                self.download_pdf(manual["url"], dest)
                logger.info("[PDF] Parsing %s", dest.name)
                items.extend(self.parse_pdf(dest, manual))
            except Exception as exc:
                logger.error("Failed to process %s: %s", manual["url"], exc)

        # 2. Parse any PDFs already in data/pdfs/
        for pdf_file in self.pdf_dir.glob("*.pdf"):
            already_done = {
                urlparse(m["url"]).path.split("/")[-1] for m in DJI_MANUAL_URLS
            }
            if pdf_file.name in already_done:
                continue
            logger.info("[PDF] Parsing local file: %s", pdf_file.name)
            meta = {
                "title": pdf_file.stem.replace("_", " "),
                "product": "M600" if "600" in pdf_file.name else "GS Pro",
                "category": "hardware",
            }
            try:
                items.extend(self.parse_pdf(pdf_file, meta))
            except Exception as exc:
                logger.error("Failed to parse %s: %s", pdf_file, exc)

        return items
