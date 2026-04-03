"""
Interactive search CLI.

Run:
    python -m src.search.cli

Or with a direct query:
    python -m src.search.cli "M600 communication protocols"
    python -m src.search.cli --category hardware --product M600
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from src.database.store import ResearchDatabase
from src.search.engine import SearchEngine

console = Console()
DB_PATH = Path("data/research.db")


# -----------------------------------------------------------------------
# Formatting helpers
# -----------------------------------------------------------------------

CATEGORY_COLORS = {
    "hardware": "cyan",
    "software": "green",
    "protocol": "magenta",
    "spec": "yellow",
    "use_case": "blue",
}

PRODUCT_COLORS = {
    "M600": "red",
    "GS Pro": "bright_blue",
    "both": "white",
}


def fmt_category(cat: str) -> str:
    color = CATEGORY_COLORS.get(cat, "white")
    return f"[{color}]{cat}[/{color}]"


def fmt_product(prod: str) -> str:
    color = PRODUCT_COLORS.get(prod, "white")
    return f"[{color}]{prod}[/{color}]"


def print_results(items: list[dict], query: str = ""):
    if not items:
        console.print("[yellow]No results found.[/yellow]")
        return

    console.print(
        f"\n[bold]Found [green]{len(items)}[/green] results"
        + (f" for [italic]{query!r}[/italic]" if query else "")
        + "[/bold]\n"
    )

    table = Table(
        box=box.ROUNDED,
        show_lines=True,
        expand=True,
        title_style="bold",
    )
    table.add_column("#", style="dim", width=4, no_wrap=True)
    table.add_column("Product", width=8, no_wrap=True)
    table.add_column("Category", width=10, no_wrap=True)
    table.add_column("Title", style="bold", min_width=30)
    table.add_column("Source", width=16)
    table.add_column("Preview", min_width=40)

    for idx, item in enumerate(items, start=1):
        preview = item["content_preview"].replace("\n", " ")[:150]
        table.add_row(
            str(idx),
            fmt_product(item["product"]),
            fmt_category(item["category"]),
            item["title"][:70],
            item["source_name"],
            preview,
        )

    console.print(table)


def print_detail(item: dict):
    title = f"[bold]{item['title']}[/bold]"
    meta_lines = [
        f"Product  : {fmt_product(item['product'])}",
        f"Category : {fmt_category(item['category'])}",
        f"Source   : {item['source_name']}",
        f"URL      : [link={item['source_url']}]{item['source_url'][:80]}[/link]",
    ]
    if item.get("authors"):
        meta_lines.append(f"Authors  : {', '.join(item['authors'][:3])}")
    if item.get("year"):
        meta_lines.append(f"Year     : {item['year']}")
    if item.get("doi"):
        meta_lines.append(f"DOI      : {item['doi']}")

    console.print(Panel(title, border_style="bold blue"))
    for line in meta_lines:
        console.print(" " + line)
    console.print()
    console.print(Panel(item["content"][:2000], title="Content", border_style="dim"))


def print_stats(db: ResearchDatabase):
    stats = db.get_stats()
    console.print(Panel("[bold]Database Statistics[/bold]", border_style="blue"))
    console.print(f"  Total items  : [green]{stats['total_items']}[/green]")
    console.print(f"  Total sources: [green]{stats['total_sources']}[/green]")
    console.print()
    console.print("  [bold]By Category:[/bold]")
    for cat, count in stats["by_category"].items():
        bar = "█" * min(count, 40)
        console.print(f"    {fmt_category(cat):<22}  {bar} {count}")
    console.print()
    console.print("  [bold]By Product:[/bold]")
    for prod, count in stats["by_product"].items():
        console.print(f"    {fmt_product(prod):<22}  {count}")


# -----------------------------------------------------------------------
# Interactive REPL
# -----------------------------------------------------------------------

HELP_TEXT = """
[bold]Search Commands:[/bold]
  <query>                   Free-text search (auto-detects product/category)
  /protocols [M600|GS Pro]  Show all communication protocols
  /hardware  [M600|GS Pro]  Show hardware components
  /specs     [M600|GS Pro]  Show technical specifications
  /missions               Show GS Pro mission planning info
  /software               Show software & SDK items
  /stats                  Database statistics
  /detail <N>             Show full content of result #N
  /export <file.json>     Export current results to JSON
  /help                   Show this help
  /quit                   Exit
"""


def interactive_loop(engine: SearchEngine, db: ResearchDatabase):
    console.print(Panel("[bold cyan]DJI M600 / GS Pro Research Search[/bold cyan]\nType /help for commands", border_style="cyan"))
    last_results: list[dict] = []

    while True:
        try:
            raw = console.input("\n[bold cyan]>[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Bye![/dim]")
            break

        if not raw:
            continue

        # Commands
        if raw.lower() in ("/quit", "/exit", "q"):
            break

        elif raw.lower() == "/help":
            console.print(HELP_TEXT)

        elif raw.lower() == "/stats":
            print_stats(db)

        elif raw.lower().startswith("/protocols"):
            prod = raw.split()[-1] if len(raw.split()) > 1 else "M600"
            last_results = engine.show_protocols(prod)
            print_results(last_results, f"protocols ({prod})")

        elif raw.lower().startswith("/hardware"):
            prod = raw.split()[-1] if len(raw.split()) > 1 else "M600"
            last_results = engine.show_hardware(prod)
            print_results(last_results, f"hardware ({prod})")

        elif raw.lower().startswith("/specs"):
            prod = raw.split()[-1] if len(raw.split()) > 1 else "M600"
            last_results = engine.show_specs(prod)
            print_results(last_results, f"specs ({prod})")

        elif raw.lower() == "/missions":
            last_results = engine.show_mission_planning()
            print_results(last_results, "GS Pro mission planning")

        elif raw.lower() == "/software":
            last_results = engine.show_software()
            print_results(last_results, "software & SDK")

        elif raw.lower().startswith("/detail"):
            parts = raw.split()
            if len(parts) < 2 or not parts[1].isdigit():
                console.print("[red]Usage: /detail <N>[/red]")
            else:
                n = int(parts[1]) - 1
                if 0 <= n < len(last_results):
                    print_detail(last_results[n])
                else:
                    console.print(f"[red]Result #{n+1} not in current list[/red]")

        elif raw.lower().startswith("/export"):
            parts = raw.split(maxsplit=1)
            out = Path(parts[1].strip()) if len(parts) > 1 else Path("data/exports/results.json")
            db.export_json(out, limit=10000)
            console.print(f"[green]Exported to {out}[/green]")

        else:
            # Free-text search
            last_results = engine.search(raw)
            print_results(last_results, raw)


# -----------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Search the DJI M600 research database")
    parser.add_argument("query", nargs="?", help="Run a single query and exit")
    parser.add_argument("--product", choices=["M600", "GS Pro", "both"], help="Filter by product")
    parser.add_argument("--category", choices=["hardware", "software", "protocol", "spec", "use_case"], help="Filter by category")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--db", default="data/research.db", help="Database path")
    args = parser.parse_args()

    db = ResearchDatabase(Path(args.db))
    engine = SearchEngine(db)

    if args.query:
        results = engine.search(args.query, product=args.product, category=args.category, limit=args.limit)
        print_results(results, args.query)
    else:
        interactive_loop(engine, db)


if __name__ == "__main__":
    main()
