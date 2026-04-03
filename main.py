#!/usr/bin/env python3
"""
DJI M600 / GS Pro Research Automation System — Main Entry Point.

Unified CLI combining all sub-tools:

    python main.py scrape                     # Run all scrapers
    python main.py scrape --sources dji       # Only DJI official site
    python main.py scrape --sources academic  # Only academic databases
    python main.py search                     # Interactive search REPL
    python main.py search "M600 protocols"    # Single query
    python main.py cite --format apa          # Print APA bibliography
    python main.py cite --format bibtex       # Export .bib file
    python main.py paper --format docx        # Generate Word paper template
    python main.py stats                      # Database statistics
"""

import argparse
import sys
from pathlib import Path


def cmd_scrape(args):
    from src.scraper.runner import run_all
    run_all(args.sources)


def cmd_search(args):
    from src.database.store import ResearchDatabase
    from src.search.engine import SearchEngine
    from src.search.cli import interactive_loop, print_results

    db = ResearchDatabase(Path(args.db))
    engine = SearchEngine(db)

    if args.query:
        results = engine.search(
            args.query,
            product=args.product,
            category=args.category,
            limit=args.limit,
        )
        print_results(results, args.query)
    else:
        interactive_loop(engine, db)


def cmd_cite(args):
    from src.database.store import ResearchDatabase
    from src.citations.manager import CitationManager

    db = ResearchDatabase(Path(args.db))
    cm = CitationManager(db.get_all_sources())

    if args.format == "apa":
        if args.out:
            cm.export_apa_txt(Path(args.out))
        else:
            cm.print_bibliography()
    elif args.format == "bibtex":
        out = Path(args.out) if args.out else Path("data/exports/references.bib")
        cm.export_bibtex(out)
        print(f"BibTeX → {out}")
    elif args.format == "docx":
        out = Path(args.out) if args.out else Path("data/exports/references.docx")
        cm.export_apa_docx(out)
        print(f"Word bibliography → {out}")


def cmd_paper(args):
    from src.database.store import ResearchDatabase
    from src.citations.manager import CitationManager
    from src.paper.generator import PaperGenerator

    db = ResearchDatabase(Path(args.db))
    cm = CitationManager(db.get_all_sources())
    gen = PaperGenerator(db, cm)

    title = args.title or (
        "DJI Matrice 600 Pro and GS Pro: System Architecture, "
        "Communication Protocols, and Research Applications"
    )

    if args.format == "docx":
        out = Path(args.out) if args.out else Path("data/exports/paper_template.docx")
        gen.generate_docx(out, title=title)
        print(f"Paper template → {out}")
    elif args.format == "txt":
        out = Path(args.out) if args.out else Path("data/exports/paper_outline.txt")
        gen.generate_txt_outline(out)
        print(f"Text outline → {out}")


def cmd_stats(args):
    from src.database.store import ResearchDatabase
    from src.search.cli import print_stats

    db = ResearchDatabase(Path(args.db))
    print_stats(db)


# -----------------------------------------------------------------------
# Argument parser
# -----------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="m600-research",
        description="DJI M600 / GS Pro Research Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--db", default="data/research.db", help="Database path")
    sub = parser.add_subparsers(dest="command", required=True)

    # scrape
    p_scrape = sub.add_parser("scrape", help="Run web scrapers")
    p_scrape.add_argument(
        "--sources",
        choices=["all", "dji", "pdf", "forums", "academic"],
        default="all",
    )

    # search
    p_search = sub.add_parser("search", help="Search the research database")
    p_search.add_argument("query", nargs="?", help="Query string (omit for interactive mode)")
    p_search.add_argument("--product", choices=["M600", "GS Pro", "both"])
    p_search.add_argument("--category", choices=["hardware", "software", "protocol", "spec", "use_case"])
    p_search.add_argument("--limit", type=int, default=20)

    # cite
    p_cite = sub.add_parser("cite", help="Generate citations / bibliography")
    p_cite.add_argument("--format", choices=["apa", "bibtex", "docx"], default="apa")
    p_cite.add_argument("--out", help="Output file path")

    # paper
    p_paper = sub.add_parser("paper", help="Generate paper template")
    p_paper.add_argument("--format", choices=["docx", "txt"], default="docx")
    p_paper.add_argument("--out", help="Output file path")
    p_paper.add_argument("--title", help="Paper title")

    # stats
    sub.add_parser("stats", help="Show database statistics")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "scrape": cmd_scrape,
        "search": cmd_search,
        "cite": cmd_cite,
        "paper": cmd_paper,
        "stats": cmd_stats,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
