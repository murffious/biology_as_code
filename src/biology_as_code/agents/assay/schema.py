"""
CanonicalClaim schema (SCHEMA.md / PLAN.md §4.1) as typed dicts + validation.

No external Zod/Pydantic dependency required — pure stdlib so the package
runs from `python -m assay` without installing anything.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class VerdictLabel(str, Enum):
    BUSTED = "BUSTED"
    PLAUSIBLE = "PLAUSIBLE"
    CONFIRMED = "CONFIRMED"


class AssertionStrength(str, Enum):
    HEDGED = "hedged"
    STRONG = "strong"
    ABSOLUTE = "absolute"
    SUPERLATIVE = "superlative"


class ClaimType(str, Enum):
    CAUSAL = "causal"
    MECHANISTIC = "mechanistic"
    SUPERLATIVE = "superlative"
    SAFETY = "safety"
    ASSOCIATIONAL = "associational"


class AttackName(str, Enum):
    ATOMIZATION = "atomization"
    HUMAN_EVIDENCE = "human_evidence"
    DOSE_FORM = "dose_form"
    MECHANISM_VS_OUTCOME = "mechanism_vs_outcome"
    EFFECT_SIZE = "effect_size"
    CONFOUNDING = "confounding"
    SUPERLATIVE = "superlative"
    REPLICATION = "replication"


# Core attacks that fail → BUSTED (PLAN.md §5)
CORE_ATTACKS = frozenset(
    {
        AttackName.HUMAN_EVIDENCE,
        AttackName.MECHANISM_VS_OUTCOME,
        AttackName.SUPERLATIVE,
        AttackName.DOSE_FORM,
        AttackName.REPLICATION,
    }
)


@dataclass
class Source:
    platform: str = "unknown"
    url: str | None = None
    author: str | None = None
    posted_at: str | None = None
    reach: str | None = None
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Subject:
    surface: str
    canonical: str
    ontology_id: str | None = None
    form: str | None = None  # whole food | extract | supplement | unstated

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Intervention:
    dose: str | None = None
    frequency: str | None = None
    duration: str | None = None
    specified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Outcome:
    surface: str
    canonical: str
    ontology_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AtomicClaim:
    atom_id: str
    predicate: str
    outcome: Outcome
    site: str | None = None
    assertion_strength: str = AssertionStrength.STRONG.value
    claim_type: str = ClaimType.CAUSAL.value
    grade: str | None = None
    survived: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    evidence_basis: str | None = None
    graph_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class AttackResult:
    name: str
    pass_: bool
    finding: str
    core: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "pass": self.pass_,
            "finding": self.finding,
            "core": self.core,
        }


@dataclass
class Verdict:
    label: str
    survived: int
    total: int
    rubric_version: str
    failed_attacks: list[str] = field(default_factory=list)
    survived_attacks: list[str] = field(default_factory=list)
    rule: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CanonicalClaim:
    claim_id: str
    source: Source
    subject: Subject
    intervention: Intervention
    atomic_claims: list[AtomicClaim]
    red_flags: list[str]
    scoped_restatement: str
    verdict: Verdict
    version: int = 1
    supersedes: str | None = None
    status: str = "draft"  # draft | grounded | assessed | auto_published | needs_review | published
    net_grade: str | None = None
    attacks: list[AttackResult] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "version": self.version,
            "supersedes": self.supersedes,
            "source": self.source.to_dict(),
            "subject": self.subject.to_dict(),
            "intervention": self.intervention.to_dict(),
            "atomic_claims": [a.to_dict() for a in self.atomic_claims],
            "red_flags": list(self.red_flags),
            "scoped_restatement": self.scoped_restatement,
            "verdict": self.verdict.to_dict(),
            "status": self.status,
            "net_grade": self.net_grade,
            "attacks": [a.to_dict() for a in self.attacks],
            "provenance": dict(self.provenance),
        }


def validate_claim(obj: dict[str, Any]) -> list[str]:
    """Return a list of validation errors (empty = valid)."""
    errs: list[str] = []
    cid = obj.get("claim_id")
    if not cid or not isinstance(cid, str):
        errs.append("missing claim_id")
    else:
        # Accept bare 16-hex (canonical) or historical assay:claim/<hex>
        core = str(cid).split("/")[-1] if str(cid).startswith("assay:claim/") else str(cid)
        if len(core) < 16:
            errs.append("claim_id hash must be ≥16 hex chars")
        elif not re.fullmatch(r"[0-9a-fA-F]{16,}", core):
            errs.append("claim_id core must be hex")

    if "subject" not in obj or not isinstance(obj["subject"], dict):
        errs.append("missing subject")
    else:
        if not obj["subject"].get("surface") and not obj["subject"].get("canonical"):
            errs.append("subject needs surface or canonical")

    atoms = obj.get("atomic_claims")
    if not atoms or not isinstance(atoms, list):
        errs.append("atomic_claims must be a non-empty list")
    else:
        for i, a in enumerate(atoms):
            if not a.get("predicate"):
                errs.append(f"atomic_claims[{i}].predicate required")
            if not a.get("outcome"):
                errs.append(f"atomic_claims[{i}].outcome required")

    v = obj.get("verdict")
    if v is not None:
        label = (v.get("label") if isinstance(v, dict) else None) or ""
        if label and label not in {x.value for x in VerdictLabel}:
            errs.append(f"verdict.label must be one of BUSTED|PLAUSIBLE|CONFIRMED, got {label}")

    return errs


# JSON-LD @context from SCHEMA.md (compact)
CLAIM_JSONLD_CONTEXT: dict[str, str] = {
    "biolink": "https://w3id.org/biolink/vocab/",
    "FOODON": "http://purl.obolibrary.org/obo/FOODON_",
    "CHEBI": "http://purl.obolibrary.org/obo/CHEBI_",
    "MONDO": "http://purl.obolibrary.org/obo/MONDO_",
    "UBERON": "http://purl.obolibrary.org/obo/UBERON_",
    "NCBITaxon": "http://purl.obolibrary.org/obo/NCBITaxon_",
    "ECO": "http://purl.obolibrary.org/obo/ECO_",
    "OBI": "http://purl.obolibrary.org/obo/OBI_",
    "ACA": "https://w3id.org/assay/aca/",
    "schema": "https://schema.org/",
    "prov": "http://www.w3.org/ns/prov#",
    "pav": "http://purl.org/pav/",
}


def to_jsonld(claim: CanonicalClaim | dict[str, Any]) -> dict[str, Any]:
    """Emit nanopub-shaped JSON-LD envelope for interoperability."""
    d = claim.to_dict() if isinstance(claim, CanonicalClaim) else dict(claim)
    verdict = d.get("verdict") or {}
    label = verdict.get("label", "BUSTED")
    rating_map = {"BUSTED": 1, "PLAUSIBLE": 3, "CONFIRMED": 5}
    return {
        "@context": CLAIM_JSONLD_CONTEXT,
        "claim_id": d.get("claim_id"),
        "pav:version": d.get("version", 1),
        "np:hasAssertion": {
            "subject": d.get("subject"),
            "intervention": d.get("intervention"),
            "atomic_claims": d.get("atomic_claims"),
            "aca:verdict": {
                "label": f"ACA:{label.title()}" if label != "BUSTED" else "ACA:Busted",
                "aca:rubricVersion": verdict.get("rubric_version"),
                "aca:survivedAttack": verdict.get("survived_attacks"),
                "aca:failedAttack": verdict.get("failed_attacks"),
                "scoped_restatement": d.get("scoped_restatement"),
            },
            "red_flags": d.get("red_flags"),
        },
        "np:hasProvenance": {
            "prov:wasDerivedFrom": d.get("source"),
            "prov:wasGeneratedBy": d.get("provenance")
            or {"pipeline": "assay", "pav:version": "0.1.0"},
        },
        "schema:ClaimReview": {
            "@type": "ClaimReview",
            "claimReviewed": (d.get("source") or {}).get("raw_text"),
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": rating_map.get(label, 1),
                "bestRating": 5,
                "alternateName": label.title() if label != "BUSTED" else "Busted",
            },
            "author": {"@type": "Organization", "name": "Assay / NutriCollective"},
        },
    }
