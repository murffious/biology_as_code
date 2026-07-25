"""Content-addressed claim IDs + immutable version helpers."""

from __future__ import annotations

import hashlib
import re
from typing import Any


def _norm_token(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s\-:./]", "", s)
    return s


def compute_claim_id(
    subject: str,
    predicate: str,
    outcome_norm: str,
    *,
    site: str | None = None,
) -> str:
    """
    Stable 16-hex content hash of the core triple (+ optional site).
    Same normalized inputs → same id (grade-once / dedupe key).
    """
    payload = "|".join(
        [
            _norm_token(subject),
            _norm_token(predicate),
            _norm_token(outcome_norm),
            _norm_token(site or ""),
        ]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    # Canonical: bare 16-hex (parity with services/assay TS product path).
    # Historical `assay:claim/` prefix is stripped on read for feed merge.
    return digest


def compute_bundle_claim_id(raw_text: str, subject_canonical: str) -> str:
    """
    Bundle-level id when a viral post contains multiple atoms.
    Uses subject + normalized raw text so paraphrases of *different* posts
    stay distinct until a semantic embedder (P3) collapses them.
    Arg order: (raw_text, subject) for call-site history; payload is subject|raw.
    """
    payload = f"{_norm_token(subject_canonical)}|{_norm_token(raw_text)}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return digest


def normalize_claim_id(claim_id: str) -> str:
    """Strip optional historical prefix so dual-engine ids resolve the same."""
    s = (claim_id or "").strip()
    if s.startswith("assay:claim/"):
        return s.split("/", 1)[-1]
    return s


def supersede(prev: dict[str, Any], *, rubric_version: str | None = None) -> dict[str, Any]:
    """
    Return a new claim version that SUPERSEDES `prev`. Never mutates in place.
    """
    nxt = dict(prev)
    old_v = int(prev.get("version") or 1)
    nxt["version"] = old_v + 1
    nxt["supersedes"] = prev.get("claim_id")
    if rubric_version is not None:
        verdict = dict(nxt.get("verdict") or {})
        verdict["rubric_version"] = rubric_version
        nxt["verdict"] = verdict
    return nxt
