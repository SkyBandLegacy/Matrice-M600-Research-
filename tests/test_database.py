"""Tests for the database store layer."""

import tempfile
from pathlib import Path

import pytest

from src.scraper.base import ScrapedItem
from src.database.store import ResearchDatabase


@pytest.fixture
def tmp_db(tmp_path):
    return ResearchDatabase(tmp_path / "test.db")


def make_item(**kwargs) -> ScrapedItem:
    defaults = dict(
        source_url="https://example.com/page",
        source_name="Test Source",
        category="hardware",
        title="Test Item",
        content="This is test content about M600 hardware components.",
        product="M600",
    )
    defaults.update(kwargs)
    return ScrapedItem(**defaults)


def test_save_and_retrieve(tmp_db):
    item = make_item(title="Motor specs")
    saved = tmp_db.save_items([item])
    assert saved == 1

    results = tmp_db.query_items(product="M600", category="hardware")
    assert len(results) == 1
    assert results[0]["title"] == "Motor specs"


def test_duplicate_skipped(tmp_db):
    item = make_item()
    tmp_db.save_items([item])
    saved2 = tmp_db.save_items([item])
    assert saved2 == 0  # duplicate skipped

    results = tmp_db.query_items()
    assert len(results) == 1


def test_keyword_search(tmp_db):
    item1 = make_item(title="Lightbridge protocol", content="Lightbridge 2 uses 2.4GHz and 5.8GHz frequencies.", category="protocol")
    item2 = make_item(title="Battery specs", content="TB48S 22000mAh capacity.", category="spec",
                      source_url="https://example.com/battery")
    tmp_db.save_items([item1, item2])

    results = tmp_db.query_items(keyword="Lightbridge")
    assert len(results) == 1
    assert "Lightbridge" in results[0]["title"]


def test_product_filter(tmp_db):
    m600 = make_item(product="M600", title="M600 arm", source_url="https://example.com/1")
    gspro = make_item(product="GS Pro", title="GS Pro waypoint", source_url="https://example.com/2",
                      category="use_case")
    tmp_db.save_items([m600, gspro])

    m_results = tmp_db.query_items(product="M600")
    assert all(r["product"] in ("M600", "both") for r in m_results)

    gs_results = tmp_db.query_items(product="GS Pro")
    assert all(r["product"] in ("GS Pro", "both") for r in gs_results)


def test_stats(tmp_db):
    items = [
        make_item(category="hardware", source_url="https://example.com/1",
                  content="M600 uses six E2000 Pro motors mounted on a hexacopter frame."),
        make_item(category="protocol", source_url="https://example.com/2",
                  content="Lightbridge 2 provides 2.4GHz and 5.8GHz video transmission links."),
        make_item(category="spec", source_url="https://example.com/3",
                  content="Max takeoff weight 15.5kg, payload capacity 6kg, flight time 38min."),
    ]
    tmp_db.save_items(items)
    stats = tmp_db.get_stats()
    assert stats["total_items"] == 3
    assert stats["by_category"]["hardware"] == 1
    assert stats["by_category"]["protocol"] == 1


def test_get_all_sources(tmp_db):
    item = make_item(metadata={"authors": ["Smith, J."], "year": "2023", "doi": "10.1234/test"})
    tmp_db.save_items([item])
    sources = tmp_db.get_all_sources()
    assert len(sources) == 1
    assert sources[0]["source_name"] == "Test Source"


def test_export_json(tmp_db, tmp_path):
    tmp_db.save_items([make_item()])
    out = tmp_path / "export.json"
    tmp_db.export_json(out)
    assert out.exists()
    import json
    data = json.loads(out.read_text())
    assert len(data) == 1
