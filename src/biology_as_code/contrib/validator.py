"""
Fail-closed contribution auditor — the claim auditor pointed at submissions.

A contribution is a typed proposal to strengthen the register (evidence, a packet
fill, a claim for the corpus, or a gate/bound rule). It walks the same kind of
gate a claim does and returns one of three honest verdicts:

``ACCEPTED``
    Schema-valid, the target resolves against the live register, and a primary
    source backs it. Provisionally scored ``3`` on the validation-ledger scale;
    review raises it as corroboration accrues.

``NEEDS_SOURCE``
    Well-formed and on-target, but unsourced. Recorded ``OPEN`` (strength ``0``),
    never promoted. **Empty beats fake.**

``REFUSE``
    Malformed, the target does not exist, or a magnitude is asserted with no
    primary evidence — the exact collapse the constitution exists to prevent.

No network, no runtime dependency — the same discipline as :mod:`evidence`. The
structural shape is checked by ``schemas/contribution.schema.json`` through the
repo's zero-dependency validator; the policy above is enforced here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from biology_as_code.audit.gates import known_nutrients
from biology_as_code.evidence import normalize_pmid, pubmed_url
from biology_as_code.laws import get_law
from biology_as_code.packets.loader import PacketNotFound, PacketsUnavailable, get_packet
from biology_as_code.packets.validate import load_schema, validate_against

Verdict = str  # "ACCEPTED" | "NEEDS_SOURCE" | "REFUSE"

# Ledger scale (docs/VALIDATION_LEDGER.md): 0 Unsourced … 5 Locked.
_STRENGTH_LABEL: dict[int, str] = {
    0: "Unsourced",
    1: "Asserted / flagged",
    2: "Structural inference",
    3: "Established mechanism",
    4: "Strong",
    5: "Locked",
}
_ACCEPTED_STRENGTH = 3  # single crowd-supplied primary source; review may raise to 4-5


def _walk_up_for(relative: str) -> Path | None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / relative
        if candidate.exists():
            return candidate
    return None


@lru_cache(maxsize=1)
def _schema() -> dict[str, Any]:
    found = _walk_up_for("schemas/contribution.schema.json")
    if found is None:
        raise FileNotFoundError(
            "schemas/contribution.schema.json not found; expected a repository checkout"
        )
    return load_schema(found)


@dataclass(frozen=True)
class ContributionResult:
    """Outcome of auditing one contribution. Truthy only when ``ACCEPTED``."""

    verdict: Verdict
    contribution_id: str
    reasons: tuple[str, ...] = ()
    target: str = ""
    strength: int = 0
    provenance: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.verdict == "ACCEPTED"

    @property
    def strength_label(self) -> str:
        return _STRENGTH_LABEL.get(self.strength, "unknown")

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "contribution_id": self.contribution_id,
            "reasons": list(self.reasons),
            "target": self.target,
            "strength": self.strength,
            "strength_label": self.strength_label,
            "provenance": dict(self.provenance),
        }


def _target_exists(kind: str, ref: str) -> tuple[bool, str]:
    """Resolve a contribution target against the live register.

    ``law``, ``packet``, ``mechanism`` and ``pathway_step`` are closed sets
    (a miss is a hard ``REFUSE``). ``nutrient`` and ``claim`` are open
    vocabularies (a new nutrient or corpus claim is legitimate), so any
    non-empty ref resolves.
    """
    note = f"{kind} {ref}"
    if not ref:
        return False, note
    if kind == "law":
        return get_law(ref) is not None, note
    if kind == "packet":
        try:
            get_packet(ref)
            return True, note
        except PacketNotFound:
            return False, note
        except PacketsUnavailable:
            # Packets not on disk (installed wheel): cannot disprove, so do not
            # hard-fail on an environment limitation.
            return True, f"{note} (unverified — packets not reachable here)"
    if kind == "nutrient":
        if ref in known_nutrients():
            return True, note
        return True, f"{note} (new nutrient — not yet in the gate/bound table)"
    if kind == "claim":
        return True, f"{note} (new corpus claim)"
    if kind == "mechanism":
        from biology_as_code.pathways.metabolic_mechanisms import (
            get_metabolic_mechanism_registry,
        )
        return get_metabolic_mechanism_registry().get(ref) is not None, note
    if kind == "pathway_step":
        # ref shape: "pathway_name::from_node->to_node"
        from biology_as_code.pathways.registry import get_pathway
        pname, sep, step = ref.partition("::")
        if not sep or "->" not in step:
            return False, f"{note} (expected 'pathway::from->to')"
        p = get_pathway(pname)
        if p is None:
            return False, f"{note} (unknown pathway {pname})"
        keys = {
            f"{getattr(e, 'from_node', '')}->{getattr(e, 'to_node', '')}"
            for e in getattr(p, "edges", []) or []
        }
        return (step in keys), note
    return False, note


def _tier_from_signoffs(base: int, contribution: Any) -> tuple[int, tuple[str, ...]]:
    """Raise strength by distinct peer sign-offs. Locking a magnitude (tier 5)
    requires >=2 independent reviewers; disputed sign-offs never promote."""
    signoffs = contribution.get("signoffs") or []
    reviewers = {
        s.get("reviewer")
        for s in signoffs
        if isinstance(s, dict) and s.get("reviewer") and s.get("verdict") != "disputed"
    }
    disputed = [
        s.get("reviewer")
        for s in signoffs
        if isinstance(s, dict) and s.get("verdict") == "disputed"
    ]
    n = len(reviewers)
    strength = min(base + n, 5)
    if n < 2:
        strength = min(strength, 4)  # tier 5 (lock a magnitude) needs >=2 independent sign-offs
    notes: list[str] = []
    if n:
        notes.append(f"{n} independent sign-off(s)")
    if disputed:
        notes.append(f"{len(disputed)} disputed — not promoted")
    return strength, tuple(notes)


def _source_ok(source: dict[str, Any]) -> tuple[bool, str]:
    """Whether a source is present and well-formed. Never fabricates metadata."""
    if not source:
        return False, "no source attached"
    kind = source.get("kind")
    if kind == "pubmed":
        pmid = normalize_pmid(source.get("pmid"))
        return (bool(pmid), f"PMID {pmid}" if pmid else "pubmed source with no valid PMID")
    if kind == "doi":
        doi = str(source.get("doi") or "").strip()
        return (bool(doi), f"DOI {doi}" if doi else "doi source with no doi")
    if kind in {"guideline", "textbook"}:
        cite = str(source.get("citation") or "").strip()
        return (bool(cite), cite if cite else f"{kind} source with no citation")
    return False, f"unknown source kind {kind!r}"


def validate_contribution(contribution: Any) -> ContributionResult:
    """Audit ``contribution`` fail-closed. Never raises on malformed input."""
    cid = str(contribution.get("id") or "") if isinstance(contribution, dict) else ""

    # 1. Structural shape.
    schema_result = validate_against(contribution, _schema())
    if not schema_result:
        return ContributionResult(
            "REFUSE", cid, reasons=("schema: " + "; ".join(schema_result.errors),)
        )

    # 2. Target must resolve against the live register.
    target = contribution["target"]
    resolved, tnote = _target_exists(str(target.get("kind")), str(target.get("ref") or ""))
    if not resolved:
        return ContributionResult(
            "REFUSE", cid, reasons=(f"target does not exist: {tnote}",), target=tnote
        )

    source = contribution.get("source") or {}
    src_ok, src_note = _source_ok(source)
    asserts_magnitude = bool(contribution.get("asserts_magnitude"))

    # 3. Fail-closed: a magnitude cannot be promoted without primary evidence.
    if asserts_magnitude and not src_ok:
        return ContributionResult(
            "REFUSE",
            cid,
            reasons=(f"asserts a magnitude with no primary evidence ({src_note}) — empty beats fake",),
            target=tnote,
        )

    # 4. Sourced, on-target, schema-clean -> ACCEPTED. Peer sign-offs raise the tier.
    if src_ok:
        provenance: dict[str, Any] = {"source": dict(source), "note": src_note}
        if source.get("kind") == "pubmed":
            provenance["url"] = pubmed_url(source.get("pmid"))
        strength, signoff_notes = _tier_from_signoffs(_ACCEPTED_STRENGTH, contribution)
        if signoff_notes:
            provenance["signoffs"] = list(signoff_notes)
        return ContributionResult(
            "ACCEPTED",
            cid,
            reasons=(f"accepted on {src_note}",) + signoff_notes,
            target=tnote,
            strength=strength,
            provenance=provenance,
        )

    # 5. Well-formed and on-target but unsourced -> recorded OPEN, not promoted.
    return ContributionResult(
        "NEEDS_SOURCE",
        cid,
        reasons=("well-formed but unsourced — recorded OPEN (strength 0), not promoted",),
        target=tnote,
        strength=0,
    )
