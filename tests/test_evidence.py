"""Open evidence / provenance surface (feature #3)."""

from __future__ import annotations


def test_pubmed_url_and_normalize():
    from biology_as_code import pubmed_url
    from biology_as_code.evidence import normalize_pmid

    assert pubmed_url(25686106) == "https://pubmed.ncbi.nlm.nih.gov/25686106/"
    assert pubmed_url("PMID: 25686106") == "https://pubmed.ncbi.nlm.nih.gov/25686106/"
    assert pubmed_url("") is None
    assert normalize_pmid(None) is None


def test_pathway_references_aggregates_sources():
    from biology_as_code.evidence import pathway_references

    refs = pathway_references()
    assert refs  # ketolysis + nutrient-sensing declared sources
    joined = " ".join(refs)
    assert "PMC" in joined  # at least one PubMed Central citation surfaced


def test_law_evidence_loads_bundled_candidates():
    from biology_as_code import law_evidence

    ev = law_evidence()
    assert ev, "bundled LAW-026 evidence should load"
    r = ev[0]
    assert r.pmid.isdigit()
    assert r.url.startswith("https://pubmed.ncbi.nlm.nih.gov/")
    assert r.source_type == "pubmed"


def test_all_sources_shape():
    from biology_as_code import all_sources

    s = all_sources()
    assert set(s) == {"pathway_references", "law_evidence", "pmids", "counts"}
    assert s["counts"]["law_evidence"] == len(s["law_evidence"])
    assert all(p.isdigit() for p in s["pmids"])


def test_fetch_pubmed_is_fail_closed_offline():
    """No network by default: returns a stub, never fabricated metadata."""
    from biology_as_code.evidence import fetch_pubmed

    r = fetch_pubmed(25686106)  # no fetcher, not enabled
    assert r.pmid == "25686106"
    assert r.title == ""  # nothing invented
    assert "not fetched" in r.note

    # opt-in with a caller-supplied fetcher works and never crashes provenance
    r2 = fetch_pubmed(123, enabled=True, fetcher=lambda p: {"title": "X", "year": 2020})
    assert r2.title == "X" and r2.year == 2020
    r3 = fetch_pubmed(123, enabled=True, fetcher=lambda p: (_ for _ in ()).throw(RuntimeError("boom")))
    assert "fetch error" in r3.note
