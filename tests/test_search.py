"""Tests for the search engine."""

import pytest
from src.scraper.base import ScrapedItem
from src.database.store import ResearchDatabase
from src.search.engine import SearchEngine


@pytest.fixture
def populated_db(tmp_path):
    db = ResearchDatabase(tmp_path / "search_test.db")
    items = [
        ScrapedItem(
            source_url="https://dji.com/m600/protocol",
            source_name="DJI Official",
            category="protocol",
            title="Lightbridge 2 Communication Protocol",
            content="Lightbridge 2 provides a robust 2.4GHz and 5.8GHz video transmission link for the M600 platform.",
            product="M600",
        ),
        ScrapedItem(
            source_url="https://dji.com/m600/hardware",
            source_name="DJI Official",
            category="hardware",
            title="M600 Hardware Components",
            content="The M600 features six E2000 Pro motors, a DJI A3 flight controller, and TB47S batteries.",
            product="M600",
        ),
        ScrapedItem(
            source_url="https://dji.com/gspro/mission",
            source_name="DJI Official",
            category="use_case",
            title="GS Pro Waypoint Mission Planning",
            content="DJI GS Pro enables autonomous waypoint flight missions with precision GPS tracking.",
            product="GS Pro",
        ),
        ScrapedItem(
            source_url="https://dji.com/m600/spec",
            source_name="DJI Official",
            category="spec",
            title="Matrice 600 Pro Specifications",
            content="Max takeoff weight: 15.5kg. Payload capacity: 6kg. Max flight time: 38 minutes.",
            product="M600",
        ),
    ]
    db.save_items(items)
    return db


@pytest.fixture
def engine(populated_db):
    return SearchEngine(populated_db)


def test_keyword_search(engine):
    results = engine.search("Lightbridge")
    assert len(results) >= 1
    assert any("Lightbridge" in r["title"] for r in results)


def test_protocol_shortcut(engine):
    results = engine.show_protocols("M600")
    assert all(r["category"] == "protocol" for r in results)


def test_hardware_shortcut(engine):
    results = engine.show_hardware("M600")
    assert all(r["category"] == "hardware" for r in results)


def test_mission_planning(engine):
    results = engine.show_mission_planning()
    assert len(results) >= 1
    assert all(r["product"] in ("GS Pro", "both") for r in results)


def test_natural_language_m600_protocols(engine):
    results = engine.search("show me all M600 communication protocols")
    assert len(results) >= 1
    # Should auto-detect M600 + protocol
    for r in results:
        assert r["product"] in ("M600", "both")


def test_natural_language_hardware(engine):
    results = engine.search("list hardware components for Matrice 600")
    assert any(r["category"] == "hardware" for r in results)


def test_product_isolation(engine):
    gs_results = engine.search("waypoint mission", product="GS Pro")
    assert all(r["product"] in ("GS Pro", "both") for r in gs_results)


def test_specs_search(engine):
    results = engine.show_specs("M600")
    assert any(r["category"] == "spec" for r in results)
