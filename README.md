# DJI M600 + GS Pro Research Automation System

An end-to-end academic research pipeline that scrapes, organises, searches, and
cites technical data about the **DJI Matrice 600 Pro** and **DJI GS Pro** — then
auto-generates a paper template ready for editing.

---

## Project Structure

```
Matrice-M600-Research-/
├── main.py                    ← Unified entry point
├── requirements.txt
├── src/
│   ├── scraper/
│   │   ├── base.py            ← Rate-limited HTTP client, cache, retry
│   │   ├── dji_official.py    ← DJI product pages & developer docs
│   │   ├── pdf_parser.py      ← DJI manual PDF downloader & section extractor
│   │   ├── forums.py          ← DJI Forum + Phantom Pilots scrapers
│   │   ├── academic.py        ← Semantic Scholar, arXiv, Google Scholar
│   │   └── runner.py          ← Orchestrates all scrapers
│   ├── database/
│   │   ├── schema.py          ← SQLAlchemy ORM (research_items, sources, tags)
│   │   └── store.py           ← High-level DB read/write API
│   ├── search/
│   │   ├── engine.py          ← Relevance-scored search + NL query parsing
│   │   └── cli.py             ← Interactive Rich terminal REPL
│   ├── citations/
│   │   ├── manager.py         ← APA 7th + BibTeX formatters
│   │   └── cli.py             ← Citation export CLI
│   └── paper/
│       ├── generator.py       ← Word document paper template builder
│       └── cli.py             ← Paper generation CLI
├── data/
│   ├── raw/                   ← Cached HTML pages (auto-created)
│   ├── pdfs/                  ← Downloaded / local PDF manuals
│   ├── processed/             ← JSON exports
│   └── exports/               ← Generated papers, bibliographies
└── tests/
    ├── test_database.py
    ├── test_citations.py
    └── test_search.py
```

---

## Quick Start

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run all scrapers

```bash
python main.py scrape
```

This scrapes:
- DJI official product pages (M600, GS Pro specs)
- DJI Developer documentation (SDK, protocols)
- DJI Matrice 600 Pro PDF manuals (auto-downloaded)
- DJI Forum & Phantom Pilots (M600/GS Pro threads)
- Semantic Scholar (free academic API — no key needed)
- arXiv (UAV research papers)
- Google Scholar (conservative rate-limited HTML scrape)

Scraped data is cached in `data/raw/` and stored in `data/research.db`.

### 3. Search the database

**Interactive mode:**
```bash
python main.py search
```

**Single query:**
```bash
python main.py search "M600 communication protocols"
python main.py search "GS Pro mission planning"
python main.py search --category hardware --product M600
```

**Search REPL commands:**
```
/protocols M600       → All M600 communication protocols
/hardware M600        → All M600 hardware components
/specs M600           → Technical specifications
/missions             → GS Pro mission planning
/software             → SDK and software items
/stats                → Database statistics
/detail <N>           → Full content of result #N
/export results.json  → Save results to JSON
/help                 → Full command reference
```

### 4. Generate citations

```bash
# Print APA bibliography to terminal
python main.py cite --format apa

# Export APA-formatted Word document
python main.py cite --format docx --out data/exports/references.docx

# Export BibTeX for LaTeX papers
python main.py cite --format bibtex --out data/exports/references.bib
```

### 5. Generate paper template

```bash
# Word document (recommended)
python main.py paper --format docx --out data/exports/paper_template.docx

# Text outline (quick preview)
python main.py paper --format txt

# Custom title
python main.py paper --format docx --title "My M600 Research Paper"
```

The generated Word document includes:
- APA-formatted title page
- All 8 sections pre-populated from the database
- Auto-inserted source notes for every paragraph
- Placeholder guidance text (blue italic) for empty sections
- Complete references list at the end

---

## Running Individual Scrapers

```bash
python main.py scrape --sources dji       # DJI official only
python main.py scrape --sources pdf       # PDF manuals only
python main.py scrape --sources academic  # Semantic Scholar + arXiv only
python main.py scrape --sources forums    # DJI Forum + Phantom Pilots only
```

## Adding Your Own PDFs

Drop any PDF into `data/pdfs/` before running the scraper. The PDF parser
will extract all text sections and add them to the database automatically.

---

## Database Categories

| Category   | Description                                      |
|------------|--------------------------------------------------|
| `hardware` | Physical components (motors, battery, frame, FC) |
| `software` | Apps, SDKs, firmware, APIs                       |
| `protocol` | Communication protocols (Lightbridge, OSDK, CAN) |
| `spec`     | Technical specifications (weight, range, speed)  |
| `use_case` | Applications, missions, deployment scenarios     |

## Products

| Value    | Description                       |
|----------|-----------------------------------|
| `M600`   | DJI Matrice 600 / 600 Pro         |
| `GS Pro` | DJI Ground Station Pro            |
| `both`   | Applies to both platforms         |

---

## Run Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Tips for Academic Use

1. **Run scrapers first** (`python main.py scrape`) — give it 5–10 minutes
2. **Add PDFs** you already have into `data/pdfs/` before scraping
3. **Search iteratively** to verify content before writing
4. **Generate the Word template** — it pulls live DB content into each section
5. **Export BibTeX** if writing in LaTeX
6. All raw HTML is cached in `data/raw/` — re-runs are fast (no re-download)

---

## Architecture Notes

- **Rate limiting**: 2 s between requests by default (5 s for Google Scholar)
- **Deduplication**: Content is SHA-256 hashed; exact duplicates are skipped
- **Caching**: HTML pages cached by URL hash — safe to interrupt and resume
- **Retry logic**: Transient network errors retried 3× with exponential backoff
- **Database**: SQLite via SQLAlchemy ORM — zero server setup required
