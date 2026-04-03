"""
Paper generator CLI.

Usage:
    python -m src.paper.cli --format docx --out paper.docx
    python -m src.paper.cli --format txt
    python -m src.paper.cli --title "My Custom Paper Title"
"""

import argparse
from pathlib import Path

from src.database.store import ResearchDatabase
from src.citations.manager import CitationManager
from src.paper.generator import PaperGenerator

DEFAULT_TITLE = (
    "DJI Matrice 600 Pro and GS Pro: System Architecture, "
    "Communication Protocols, and Research Applications"
)


def main():
    parser = argparse.ArgumentParser(description="Generate research paper template from the database")
    parser.add_argument("--format", choices=["docx", "txt"], default="docx")
    parser.add_argument("--out", help="Output file path")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="Paper title")
    parser.add_argument("--db", default="data/research.db")
    args = parser.parse_args()

    db = ResearchDatabase(Path(args.db))
    sources = db.get_all_sources()
    cm = CitationManager(sources)
    gen = PaperGenerator(db, cm)

    if args.format == "docx":
        out = Path(args.out) if args.out else Path("data/exports/paper_template.docx")
        gen.generate_docx(out, title=args.title)
        print(f"Paper template written to: {out}")

    elif args.format == "txt":
        out = Path(args.out) if args.out else Path("data/exports/paper_outline.txt")
        gen.generate_txt_outline(out)
        print(f"Text outline written to: {out}")


if __name__ == "__main__":
    main()
