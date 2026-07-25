"""
Vertical slice: text → atomize → (fixture|heuristic) ground → score → CanonicalClaim.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .atomize import atomize
from .fixtures.golden import GOLDEN
from .ids import compute_bundle_claim_id
from .schema import (
    CanonicalClaim,
    Intervention,
    Source,
    to_jsonld,
    validate_claim,
)
from .score import RUBRIC_VERSION, EvidenceSet, apply_atom_grades, score


@dataclass
class AssayResult:
    claim: CanonicalClaim
    confidence: float
    matched_fixture: str | None
    jsonld: dict[str, Any]
    validation_errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim.to_dict(),
            "confidence": self.confidence,
            "matched_fixture": self.matched_fixture,
            "jsonld": self.jsonld,
            "validation_errors": self.validation_errors,
            "rubric_version": RUBRIC_VERSION,
        }


def _default_evidence_for_unknown(atomize_res) -> EvidenceSet:
    """
    Honest unknown: without grounding, core human-evidence & replication fail.
    Superlative fails if present. Does not invent support.
    """
    has_super = any(
        a.assertion_strength == "superlative" or a.claim_type == "superlative"
        for a in atomize_res.atoms
    )
    return EvidenceSet(
        human_studies=0,
        human_directly_supports=False,
        animal_or_in_vitro_only=True,
        dose_form_match=atomize_res.intervention.specified,
        mechanism_only=False,
        effect_size_meaningful=False,
        confounding_concern=False,
        has_superlative_atom=has_super,
        superlative_false=has_super,
        replication_count=0,
        rebuttals=0,
        confidence_prior=0.2,
        notes={
            "human_evidence": (
                "No grounded human evidence attached yet — run PubMed grounding (P2) "
                "or match a golden fixture. Default is fail-closed on human evidence."
            ),
            "replication": "Ungrounded claim: replication unknown → fail-closed.",
            "dose_form": (
                "Dose/form specified in text."
                if atomize_res.intervention.specified
                else "Dose/form not specified in the claim text."
            ),
        },
    )


def _ground(matched_fixture: str | None, atomize_res) -> tuple[EvidenceSet, str | None, str | None]:
    """Return evidence set, scoped restatement override, atom basis map."""
    if matched_fixture and matched_fixture in GOLDEN:
        g = GOLDEN[matched_fixture]
        return (
            EvidenceSet.from_dict(g["evidence"]),
            g.get("scoped_restatement"),
            g.get("atom_bases"),
        )
    return _default_evidence_for_unknown(atomize_res), None, None


def _restatement(
    override: str | None,
    *,
    subject: str,
    verdict_label: str,
    raw: str,
) -> str:
    if override:
        return override
    if verdict_label == "BUSTED":
        return (
            f"As stated, this claim about {subject} does not survive the Assay gauntlet. "
            f"Keep the kernel only if human evidence later grounds it; do not coach the "
            f"absolute wording: “{raw[:160]}{'…' if len(raw) > 160 else ''}”."
        )
    if verdict_label == "PLAUSIBLE":
        return (
            f"There may be a real signal for {subject}, but scope/size/causality are overstated "
            "relative to a fail-closed read of the evidence set. Hedge in coaching."
        )
    return (
        f"This claim about {subject} survives the current gauntlet under rubric {RUBRIC_VERSION}. "
        "Still cite the scoped human evidence when coaching."
    )


def assay_claim(
    raw_text: str,
    *,
    platform: str = "paste",
    author: str | None = None,
    url: str | None = None,
    reach: str | None = None,
    posted_at: str | None = None,
) -> AssayResult:
    raw_text = (raw_text or "").strip()
    ar = atomize(raw_text)
    evidence, restatement_override, atom_bases = _ground(ar.matched_fixture, ar)
    verdict, attacks, confidence = score(evidence, ar.atoms, RUBRIC_VERSION)
    atoms = apply_atom_grades(ar.atoms, attacks, verdict.label)

    if atom_bases:
        for a in atoms:
            if a.atom_id in atom_bases:
                a.evidence_basis = atom_bases[a.atom_id]
    else:
        for a in atoms:
            a.evidence_basis = (
                f"Heuristic grade under fail-closed grounding; predicate={a.predicate}."
            )

    claim_id = compute_bundle_claim_id(raw_text, ar.subject.canonical)
    source = Source(
        platform=platform,
        url=url,
        author=author,
        posted_at=posted_at,
        reach=reach,
        raw_text=raw_text,
    )
    restatement = _restatement(
        restatement_override,
        subject=ar.subject.canonical,
        verdict_label=verdict.label,
        raw=raw_text,
    )

    # net grade for intake-card UI
    net = {
        "BUSTED": "False",
        "PLAUSIBLE": "Moderate",
        "CONFIRMED": "High",
    }.get(verdict.label, "Low")

    claim = CanonicalClaim(
        claim_id=claim_id,
        source=source,
        subject=ar.subject,
        intervention=ar.intervention or Intervention(),
        atomic_claims=atoms,
        red_flags=ar.red_flags,
        scoped_restatement=restatement,
        verdict=verdict,
        version=1,
        status="assessed" if ar.matched_fixture else "draft",
        net_grade=net,
        attacks=attacks,
        provenance={
            "pipeline": "assay",
            "pipeline_version": "0.1.0",
            "rubric_version": RUBRIC_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "matched_fixture": ar.matched_fixture,
            "grounding": "fixture" if ar.matched_fixture else "fail_closed_heuristic",
        },
    )

    payload = claim.to_dict()
    errs = validate_claim(payload)
    return AssayResult(
        claim=claim,
        confidence=confidence,
        matched_fixture=ar.matched_fixture,
        jsonld=to_jsonld(claim),
        validation_errors=errs,
    )


def assay_to_public_dict(result: AssayResult) -> dict[str, Any]:
    """API-friendly shape for Claims Lab UI."""
    c = result.claim
    return {
        "claim_id": c.claim_id,
        "version": c.version,
        "status": c.status,
        "net_grade": c.net_grade,
        "confidence": result.confidence,
        "matched_fixture": result.matched_fixture,
        "source": c.source.to_dict(),
        "subject": c.subject.to_dict(),
        "intervention": c.intervention.to_dict(),
        "atomic_claims": [a.to_dict() for a in c.atomic_claims],
        "red_flags": c.red_flags,
        "scoped_restatement": c.scoped_restatement,
        "verdict": c.verdict.to_dict(),
        "attacks": [a.to_dict() for a in c.attacks],
        "jsonld": result.jsonld,
        "validation_errors": result.validation_errors,
        "rubric_version": RUBRIC_VERSION,
        "examples": [
            GOLDEN[k]["raw_text"]
            for k in (
                "spirulina-brain-metals",
                "creatine-strength",
                "flavonoids-cvd",
                "acv-belly-fat",
            )
        ],
    }
