"""Tests for the citation manager."""

import pytest
from src.citations.manager import (
    Citation,
    APAFormatter,
    BibTeXFormatter,
    CitationManager,
)


@pytest.fixture
def apa():
    return APAFormatter()


@pytest.fixture
def bibtex():
    return BibTeXFormatter()


def test_apa_journal(apa):
    c = Citation(
        source_id=1,
        url="https://doi.org/10.1234/test",
        source_name="Test Journal",
        authors=["Smith, John A.", "Doe, Jane B."],
        year="2023",
        title="UAV Architecture Study",
        venue="Journal of Robotics",
        doi="10.1234/test",
        source_type="journal",
    )
    result = apa.format(c)
    assert "Smith," in result
    assert "Doe," in result
    assert "(2023)" in result
    assert "UAV Architecture Study" in result
    assert "10.1234/test" in result


def test_apa_webpage(apa):
    c = Citation(
        source_id=2,
        url="https://www.dji.com/matrice600-pro",
        source_name="DJI Official",
        title="Matrice 600 Pro",
        year="2023",
        source_type="webpage",
    )
    result = apa.format(c)
    assert "dji.com" in result
    assert "Retrieved" in result


def test_apa_arxiv(apa):
    c = Citation(
        source_id=3,
        url="https://arxiv.org/abs/2301.00001",
        source_name="arXiv",
        authors=["Zhang, Wei"],
        title="Drone Autonomy",
        year="2023",
        arxiv_id="2301.00001",
        source_type="arxiv",
    )
    result = apa.format(c)
    assert "arXiv" in result
    assert "arxiv.org" in result


def test_bibtex_key_format(bibtex):
    c = Citation(
        source_id=4,
        url="https://example.com",
        source_name="Test",
        authors=["Johnson, Alice"],
        year="2022",
        title="Flight Control Systems",
        source_type="journal",
        venue="IEEE Transactions",
    )
    result = bibtex.format(c)
    assert "@article{johnson2022flight" in result
    assert "author" in result
    assert "title" in result


def test_citation_manager_from_sources():
    sources = [
        {
            "id": 1,
            "url": "https://www.dji.com/matrice600-pro",
            "source_name": "DJI Official",
            "title": "Matrice 600 Pro",
            "authors": None,
            "year": "2023",
            "venue": None,
            "doi": None,
            "arxiv_id": None,
            "first_scraped": "2024-01-01",
        },
        {
            "id": 2,
            "url": "https://arxiv.org/abs/2301.00001",
            "source_name": "arXiv",
            "title": "UAV Research",
            "authors": ["Wang, Li"],
            "year": "2023",
            "venue": None,
            "doi": None,
            "arxiv_id": "2301.00001",
            "first_scraped": "2024-01-01",
        },
    ]
    cm = CitationManager(sources)
    assert len(cm.citations) == 2

    bib = cm.get_apa_bibliography()
    assert len(bib) == 2
    assert any("arXiv" in r for r in bib)


def test_bibliography_is_sorted():
    sources = [
        {"id": 1, "url": "https://z.com", "source_name": "Z Source", "title": "Zebra Study",
         "authors": ["Zimmerman, A."], "year": "2020", "venue": None, "doi": None, "arxiv_id": None, "first_scraped": ""},
        {"id": 2, "url": "https://a.com", "source_name": "A Source", "title": "Apple Study",
         "authors": ["Adams, B."], "year": "2021", "venue": None, "doi": None, "arxiv_id": None, "first_scraped": ""},
    ]
    cm = CitationManager(sources)
    bib = cm.get_apa_bibliography()
    # Adams should come before Zimmerman
    adams_idx = next(i for i, r in enumerate(bib) if "Adams" in r)
    zimm_idx = next(i for i, r in enumerate(bib) if "Zimmerman" in r)
    assert adams_idx < zimm_idx
