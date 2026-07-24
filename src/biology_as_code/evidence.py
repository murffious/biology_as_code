"""
Open evidence / provenance surface.

Honest and offline by design: this module never fabricates citations and never
touches the network on its own. It (a) aggregates every source string already
declared on the package's pathways, (b) loads the PubMed candidate evidence
bundled for LAW-026 (colon SCFA energy), and (c) builds/validates PubMed URLs.
A live PubMed lookup is available but **fail-closed** — you must opt in and pass
your own fetcher (mirrors the product-score plugin gate).

    from biology_as_code import all_sources, pubmed_url, law_evidence

    pubmed_url(25686106)          # 'https://pubmed.ncbi.nlm.nih.gov/25686106/'
    len(law_evidence())          # bundled LAW-026 PubMed candidates
    all_sources()["counts"]      # {'pathway_references': N, 'law_evidence': M, 'pmids': K}
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

_PUBMED_URL = "https://pubmed.ncbi.nlm.nih.gov/{}/"
_LAW026 = Path(__file__).resolve().parent / "data" / "kibo_core" / "data" / "evidence_candidates_LAW026.json"


@dataclass(frozen=True)
class EvidenceRecord:
    pmid: str = ""
    title: str = ""
    year: int | None = None
    source_type: str = "pubmed"  # pubmed | textbook | url | guideline
    url: str = ""
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "pmid": self.pmid,
            "title": self.title,
            "year": self.year,
            "source_type": self.source_type,
            "url": self.url,
            "note": self.note,
        }


def normalize_pmid(pmid: str | int | None) -> str | None:
    """Digits-only PMID, or None if there are no digits."""
    if pmid is None:
        return None
    digits = re.sub(r"\D", "", str(pmid))
    return digits or None


def pubmed_url(pmid: str | int | None) -> str | None:
    """Canonical PubMed URL for a PMID, or None if the PMID is unusable."""
    p = normalize_pmid(pmid)
    return _PUBMED_URL.format(p) if p else None


@lru_cache(maxsize=1)
def pathway_references() -> tuple[str, ...]:
    """Every ``references`` string declared on a registered pathway (deduped)."""
    from biology_as_code.pathways.registry import pathway_loaders

    seen: list[str] = []
    for _label, factory in pathway_loaders():
        reg = factory()
        paths = reg.list_all() if hasattr(reg, "list_all") else list(reg.pathways.values())
        for p in paths:
            for ref in getattr(p, "references", None) or []:
                if ref not in seen:
                    seen.append(ref)
    return tuple(sorted(seen))


@lru_cache(maxsize=1)
def law_evidence() -> tuple[EvidenceRecord, ...]:
    """Bundled PubMed candidate evidence for LAW-026 (empty tuple if absent)."""
    if not _LAW026.is_file():
        return ()
    data = json.loads(_LAW026.read_text(encoding="utf-8"))
    out: list[EvidenceRecord] = []
    for c in data.get("candidates") or []:
        pmid = normalize_pmid(c.get("pmid")) or ""
        out.append(
            EvidenceRecord(
                pmid=pmid,
                title=c.get("title") or "",
                year=c.get("year"),
                source_type="pubmed",
                url=c.get("url") or (pubmed_url(pmid) or ""),
                note=c.get("journal") or "",
            )
        )
    return tuple(out)


def pmids_cited() -> list[str]:
    """All distinct PMIDs referenced anywhere (law evidence + pathway ref strings)."""
    pmids = {r.pmid for r in law_evidence() if r.pmid}
    for ref in pathway_references():
        for m in re.finditer(r"PMID[:\s]*(\d{5,9})", ref):
            pmids.add(m.group(1))
    return sorted(pmids)


def all_sources() -> dict[str, Any]:
    """Unified provenance view across the whole package."""
    refs = list(pathway_references())
    laws = [r.as_dict() for r in law_evidence()]
    pmids = pmids_cited()
    return {
        "pathway_references": refs,
        "law_evidence": laws,
        "pmids": pmids,
        "counts": {
            "pathway_references": len(refs),
            "law_evidence": len(laws),
            "pmids": len(pmids),
        },
    }


def fetch_pubmed(
    pmid: str | int,
    *,
    enabled: bool = False,
    fetcher: Callable[[str], dict[str, Any]] | None = None,
) -> EvidenceRecord:
    """Optional live PubMed lookup — **fail-closed**.

    The open package makes no network calls. To fetch, pass ``enabled=True`` and
    your own ``fetcher(pmid) -> dict`` (e.g. an E-utilities client). Without both,
    this returns a stub record with the canonical URL and a note — never fabricated
    metadata.
    """
    p = normalize_pmid(pmid)
    if not p:
        return EvidenceRecord(note="invalid pmid")
    url = pubmed_url(p) or ""
    if not enabled or fetcher is None:
        return EvidenceRecord(
            pmid=p, url=url, source_type="pubmed",
            note="not fetched (offline) — pass enabled=True and a fetcher(pmid) to look up",
        )
    try:
        meta = fetcher(p) or {}
        return EvidenceRecord(
            pmid=p,
            title=str(meta.get("title") or ""),
            year=meta.get("year"),
            source_type="pubmed",
            url=url,
            note="fetched",
        )
    except Exception as exc:  # never let a user fetcher crash provenance
        return EvidenceRecord(pmid=p, url=url, note=f"fetch error: {exc}")


__all__ = [
    "EvidenceRecord",
    "all_sources",
    "fetch_pubmed",
    "law_evidence",
    "normalize_pmid",
    "pathway_references",
    "pmids_cited",
    "pubmed_url",
]
