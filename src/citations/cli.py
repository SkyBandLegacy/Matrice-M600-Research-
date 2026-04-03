"""
Citation CLI.

Usage:
    python -m src.citations.cli --format apa
    python -m src.citations.cli --format bibtex --out refs.bib
    python -m src.citations.cli --format docx --out references.docx
"""

import argparse
from pathlib import Path

from src.database.store import ResearchDatabase
from src.citations.manager import CitationManager


def main():
    parser = argparse.ArgumentParser(description="Export citations from the research database")
    parser.add_argument("--format", choices=["apa", "bibtex", "docx"], default="apa")
    parser.add_argument("--out", help="Output file path")
    parser.add_argument("--db", default="data/research.db")
    args = parser.parse_args()

    db = ResearchDatabase(Path(args.db))
    sources = db.get_all_sources()
    manager = CitationManager(sources)

    if args.format == "apa":
        if args.out:
            manager.export_apa_txt(Path(args.out))
        else:
            manager.print_bibliography()

    elif args.format == "bibtex":
        out = Path(args.out) if args.out else Path("data/exports/references.bib")
        manager.export_bibtex(out)
        print(f"BibTeX written to {out}")

    elif args.format == "docx":
        out = Path(args.out) if args.out else Path("data/exports/references.docx")
        manager.export_apa_docx(out)
        print(f"Word document written to {out}")


if __name__ == "__main__":
    main()
