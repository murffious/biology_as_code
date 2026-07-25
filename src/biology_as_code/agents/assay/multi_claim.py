"""
Multi-claim chart expander — Pinterest / TikTok "organ healing drinks" pattern.

One image ⇒ N atomic organ→drink claims + one superlative frame claim.
Each atom is scored separately; systems map lets UI group by body system.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .ids import compute_bundle_claim_id
from .organ_systems import OrganSystem, resolve_organ
from .pipeline import assay_claim
from .schema import (
    AssertionStrength,
    AtomicClaim,
    CanonicalClaim,
    ClaimType,
    Intervention,
    Outcome,
    Source,
    Subject,
)
from .score import RUBRIC_VERSION, EvidenceSet, apply_atom_grades, score

# Default rows from docs/image.png — ORGAN HEALING DRINKS
DEFAULT_ORGAN_DRINK_ROWS: list[tuple[str, str]] = [
    ("eyes", "Carrot Juice"),
    ("brain", "Beetroot Juice"),
    ("lungs", "Ginger Tea"),
    ("liver", "Lemon Water"),
    ("kidneys", "Coconut Water"),
    ("heart", "Pomegranate Juice"),
]

# Per-row evidence priors for the viral chart (honest, not invented RCTs).
# mechanism_only=True → "healing" sold as clinical organ repair.
_ROW_EVIDENCE: dict[str, dict[str, Any]] = {
    "eyes": {
        "human_studies": 20,
        "human_directly_supports": False,  # juice does not "heal" eyes
        "animal_or_in_vitro_only": False,
        "dose_form_match": False,  # β-carotene literature ≠ carrot juice heals eyeball
        "mechanism_only": True,
        "effect_size_meaningful": False,
        "confounding_concern": False,
        "has_superlative_atom": True,
        "superlative_false": True,
        "replication_count": 0,
        "rebuttals": 0,
        "confidence_prior": 0.35,
        "notes": {
            "human_evidence": (
                "Carotenoids (β-carotene, lutein/zeaxanthin from diet) appear in eye-health "
                "literature; no trial shows carrot juice 'heals' eyes or repairs tissue."
            ),
            "mechanism_vs_outcome": (
                "Vitamin A / carotenoid *nutrient* story is sold as organ *healing* outcome."
            ),
            "dose_form": "Studied nutrients ≠ unspecified kitchen juice as organ therapy.",
            "superlative": "'Healing drink' for eyes is marketing, not a clinical indication.",
        },
        "kernel": (
            "Carrot juice is a source of provitamin A carotenoids relevant to visual nutrition "
            "research — not an eyeball-repair drink."
        ),
    },
    "brain": {
        "human_studies": 15,
        "human_directly_supports": False,
        "animal_or_in_vitro_only": False,
        "dose_form_match": False,
        "mechanism_only": True,
        "effect_size_meaningful": False,
        "confounding_concern": False,
        "has_superlative_atom": True,
        "superlative_false": True,
        "replication_count": 1,
        "rebuttals": 0,
        "confidence_prior": 0.4,
        "notes": {
            "human_evidence": (
                "Dietary nitrate / beetroot has human data on blood pressure and some "
                "perfusion/cognition surrogates — not 'heals the brain' or structural repair."
            ),
            "mechanism_vs_outcome": "NO / perfusion mechanism ≠ organ healing claim.",
            "superlative": "Brain-healing juice is overclaim beyond nitrate literature.",
        },
        "kernel": (
            "Beetroot juice is studied for nitrate → NO pathways and BP; that is not the same "
            "as healing brain tissue."
        ),
    },
    "lungs": {
        "human_studies": 5,
        "human_directly_supports": False,
        "animal_or_in_vitro_only": False,
        "dose_form_match": False,
        "mechanism_only": True,
        "effect_size_meaningful": False,
        "confounding_concern": False,
        "has_superlative_atom": True,
        "superlative_false": True,
        "replication_count": 0,
        "rebuttals": 0,
        "confidence_prior": 0.3,
        "notes": {
            "human_evidence": (
                "Ginger has some human data for nausea and limited respiratory symptom work; "
                "no evidence ginger tea cleans or heals lungs."
            ),
            "mechanism_vs_outcome": "Warm fluid + ginger bioactives ≠ pulmonary healing.",
        },
        "kernel": (
            "Ginger tea may be soothing; it is not a lung-cleaning or lung-healing therapy."
        ),
    },
    "liver": {
        "human_studies": 3,
        "human_directly_supports": False,
        "animal_or_in_vitro_only": True,
        "dose_form_match": False,
        "mechanism_only": True,
        "effect_size_meaningful": False,
        "confounding_concern": False,
        "has_superlative_atom": True,
        "superlative_false": True,
        "replication_count": 0,
        "rebuttals": 0,
        "confidence_prior": 0.25,
        "notes": {
            "human_evidence": (
                "Lemon water is hydration + vitamin C; 'liver cleanse/heal' has no rigorous "
                "human support as organ therapy."
            ),
            "mechanism_vs_outcome": "Detox/cleanse marketing for liver is classic overclaim.",
        },
        "kernel": (
            "Lemon water is fine hydration; the liver does not need a lemon 'cleanse' to heal."
        ),
    },
    "kidneys": {
        "human_studies": 8,
        "human_directly_supports": False,
        "animal_or_in_vitro_only": False,
        "dose_form_match": False,
        "mechanism_only": True,
        "effect_size_meaningful": False,
        "confounding_concern": False,
        "has_superlative_atom": True,
        "superlative_false": True,
        "replication_count": 0,
        "rebuttals": 0,
        "confidence_prior": 0.35,
        "notes": {
            "human_evidence": (
                "Coconut water is an electrolyte fluid; hydration matters for kidney function "
                "in general — no evidence it heals kidneys as a therapy."
            ),
            "mechanism_vs_outcome": "Hydration ≠ organ healing claim.",
        },
        "kernel": (
            "Coconut water can contribute to fluid/electrolyte intake; it is not a kidney-healing drink."
        ),
    },
    "heart": {
        "human_studies": 25,
        "human_directly_supports": False,
        "animal_or_in_vitro_only": False,
        "dose_form_match": False,
        "mechanism_only": True,
        "effect_size_meaningful": False,
        "confounding_concern": False,
        "has_superlative_atom": True,
        "superlative_false": True,
        "replication_count": 2,
        "rebuttals": 0,
        "confidence_prior": 0.45,
        "notes": {
            "human_evidence": (
                "Pomegranate polyphenols have vascular/BP-adjacent literature; juice is not "
                "proven to 'heal' the heart organ."
            ),
            "mechanism_vs_outcome": "Vascular markers ≠ heart healing.",
        },
        "kernel": (
            "Pomegranate juice appears in cardiometabolic research for polyphenols — not as a heart-healing drink."
        ),
    },
}


@dataclass
class ChartRow:
    organ: str
    drink: str
    system: OrganSystem
    claim_sentence: str


@dataclass
class MultiClaimBundle:
    """Full chart assay: frame + per-organ atoms scored."""

    title: str
    frame_claim: str
    frame_result: dict[str, Any]
    rows: list[dict[str, Any]] = field(default_factory=list)
    systems_summary: list[dict[str, Any]] = field(default_factory=list)
    scoped_restatement: str = ""
    red_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "multi_claim_chart",
            "title": self.title,
            "frame_claim": self.frame_claim,
            "frame": self.frame_result,
            "rows": self.rows,
            "systems_summary": self.systems_summary,
            "scoped_restatement": self.scoped_restatement,
            "red_flags": self.red_flags,
            "pattern": "organ_healing_drinks",
        }


def parse_organ_drink_text(text: str) -> list[tuple[str, str]] | None:
    """
    Parse OCR/pasted chart text into (organ, drink) rows.
    Accepts lines like 'EYES: Carrot Juice' or 'EYES - Carrot Juice'.
    """
    t = text or ""
    if not re.search(r"organ\s+heal|healing\s+drink|cleanse|detox\s+drink", t, re.I):
        # Still try if multiple organ labels present
        if not re.search(r"\b(eyes?|brain|lungs?|liver|kidneys?|heart)\b", t, re.I):
            return None

    rows: list[tuple[str, str]] = []
    # Pattern: ORGAN optional separator drink
    for m in re.finditer(
        r"\b(eyes?|brain|lungs?|liver|kidneys?|heart)\b\s*[:\-–—]?\s*([A-Za-z][A-Za-z \-]{2,40})",
        t,
        re.I,
    ):
        organ = m.group(1).lower()
        drink = m.group(2).strip()
        # stop at next organ word inside drink capture
        drink = re.split(
            r"\b(eyes?|brain|lungs?|liver|kidneys?|heart)\b",
            drink,
            maxsplit=1,
            flags=re.I,
        )[0].strip(" :-–—")
        if resolve_organ(organ) and len(drink) > 2:
            rows.append((organ, drink.title() if drink.islower() else drink))

    if len(rows) >= 3:
        # dedupe by organ
        seen: set[str] = set()
        out: list[tuple[str, str]] = []
        for o, d in rows:
            key = resolve_organ(o).organ_key if resolve_organ(o) else o
            if key in seen:
                continue
            seen.add(key)
            out.append((o, d))
        return out
    return None


def is_organ_healing_chart(text: str) -> bool:
    if re.search(r"organ\s+healing\s+drinks?", text, re.I):
        return True
    parsed = parse_organ_drink_text(text)
    return bool(parsed and len(parsed) >= 4)


def organ_healing_chart_text() -> str:
    """Canonical OCR of docs/image.png for demos without vision."""
    lines = ["ORGAN HEALING DRINKS"]
    for organ, drink in DEFAULT_ORGAN_DRINK_ROWS:
        lines.append(f"{organ.upper()}: {drink}")
    return "\n".join(lines)


def _score_row(organ_key: str, drink: str, system: OrganSystem) -> dict[str, Any]:
    sentence = (
        f"{drink} is an organ-healing drink for the {system.organ} "
        f"({system.system_label})."
    )
    subject = Subject(
        surface=drink.lower(),
        canonical=drink,
        ontology_id=None,
        form="beverage",
    )
    atom = AtomicClaim(
        atom_id="a1",
        predicate="heals / cleanses",
        outcome=Outcome(
            surface=f"{system.organ} healing",
            canonical=f"{system.system_label} — organ healing claim",
            ontology_id=None,
        ),
        site=system.site,
        assertion_strength=AssertionStrength.ABSOLUTE.value,
        claim_type=ClaimType.CAUSAL.value,
    )
    # secondary: maps to system capacity
    atom2 = AtomicClaim(
        atom_id="a2",
        predicate="supports",
        outcome=Outcome(
            surface=system.capacity_frame,
            canonical=system.capacity_frame,
            ontology_id=None,
        ),
        site=system.site,
        assertion_strength=AssertionStrength.HEDGED.value,
        claim_type=ClaimType.ASSOCIATIONAL.value,
    )
    atoms = [atom, atom2]
    ev_raw = dict(_ROW_EVIDENCE.get(organ_key, _ROW_EVIDENCE["liver"]))
    kernel = ev_raw.pop("kernel", sentence)
    evidence = EvidenceSet.from_dict(ev_raw)
    verdict, attacks, conf = score(evidence, atoms)
    atoms = apply_atom_grades(atoms, attacks, verdict.label)
    for a in atoms:
        if a.atom_id == "a1":
            a.evidence_basis = ev_raw.get("notes", {}).get(
                "human_evidence", "Organ-healing claim fails human-evidence bar."
            )
        else:
            a.evidence_basis = kernel

    claim = CanonicalClaim(
        claim_id=compute_bundle_claim_id(sentence, drink),
        source=Source(
            platform="pinterest-style",
            raw_text=sentence,
            author="organ-healing-drinks chart",
        ),
        subject=subject,
        intervention=Intervention(specified=False),
        atomic_claims=atoms,
        red_flags=[
            "Organ-healing / cleanse marketing vocabulary",
            "No dose, form, or duration",
            f"Organ named ({system.organ}) — evaluate as system: {system.system_label}",
            "Mechanism or nutrient story sold as organ repair",
        ],
        scoped_restatement=kernel,
        verdict=verdict,
        version=1,
        status="assessed",
        net_grade="False" if verdict.label == "BUSTED" else "Low",
        attacks=attacks,
        provenance={
            "pipeline": "assay-multi",
            "pipeline_version": "0.1.0",
            "rubric_version": RUBRIC_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "organ": system.organ,
            "system_id": system.system_id,
            "system_label": system.system_label,
            "drink": drink,
            "pattern": "organ_healing_drinks",
        },
    )
    return {
        "organ": system.organ,
        "organ_key": organ_key,
        "system_id": system.system_id,
        "system_label": system.system_label,
        "capacity_frame": system.capacity_frame,
        "drink": drink,
        "claim_sentence": sentence,
        "verdict": verdict.to_dict(),
        "confidence": conf,
        "attacks": [a.to_dict() for a in attacks],
        "atomic_claims": [a.to_dict() for a in atoms],
        "scoped_restatement": kernel,
        "claim_id": claim.claim_id,
        "claim": claim.to_dict(),
        "red_flags": claim.red_flags,
    }


def assay_organ_healing_chart(
    text: str | None = None,
    *,
    platform: str = "pinterest-style",
) -> MultiClaimBundle:
    """
    Expand ORGAN HEALING DRINKS chart → frame + N organ→system claims.
    """
    raw = (text or "").strip() or organ_healing_chart_text()
    parsed = parse_organ_drink_text(raw) or DEFAULT_ORGAN_DRINK_ROWS

    frame = (
        "These drinks heal organs: "
        + "; ".join(f"{d} → {o}" for o, d in parsed)
        + ". (ORGAN HEALING DRINKS chart)"
    )
    # Frame as superlative absolute multi-claim
    frame_res = assay_claim(
        "ORGAN HEALING DRINKS: special drinks heal your eyes, brain, lungs, liver, kidneys, and heart.",
        platform=platform,
        author="viral-chart",
    )
    # Force frame evidence as multi-organ superlative bust
    frame_pub = {
        "claim": frame_res.claim.to_dict(),
        "confidence": frame_res.confidence,
        "matched_fixture": frame_res.matched_fixture,
        "verdict": frame_res.claim.verdict.to_dict(),
        "scoped_restatement": (
            "No beverage is an 'organ healing drink' suite. Individual ingredients may appear in "
            "nutrition research for related *systems* (vision, vascular, hydration) — that is not "
            "the same as healing eyes, brain, lungs, liver, kidneys, or heart."
        ),
    }

    rows_out: list[dict[str, Any]] = []
    by_system: dict[str, list[str]] = {}
    for organ, drink in parsed:
        sys = resolve_organ(organ)
        if not sys:
            continue
        row = _score_row(sys.organ_key, drink, sys)
        rows_out.append(row)
        by_system.setdefault(sys.system_id, []).append(
            f"{sys.system_label}: {drink} → {row['verdict']['label']}"
        )

    systems_summary = []
    for sid, lines in by_system.items():
        # pick first matching system label
        label = next(
            (r["system_label"] for r in rows_out if r["system_id"] == sid),
            sid,
        )
        systems_summary.append(
            {
                "system_id": sid,
                "system_label": label,
                "claims": lines,
                "net": "BUSTED"
                if any(
                    r["verdict"]["label"] == "BUSTED"
                    for r in rows_out
                    if r["system_id"] == sid
                )
                else "MIXED",
            }
        )

    restatement = (
        "This chart packages six organ-level *healing* claims under one superlative frame. "
        "Assay splits them and re-maps each organ to a body **system** for evaluation:\n"
        + "\n".join(f"• {r['scoped_restatement']}" for r in rows_out)
        + "\n\nGeneralization: prefer system/capacity language (visual nutrition, vascular function, "
        "hydration) over 'heals organ X' — none of the absolute healing claims survive the gauntlet."
    )

    return MultiClaimBundle(
        title="ORGAN HEALING DRINKS",
        frame_claim=frame,
        frame_result=frame_pub,
        rows=rows_out,
        systems_summary=systems_summary,
        scoped_restatement=restatement,
        red_flags=[
            "Multi-claim infographic — must atomize per organ×drink",
            "Organ list should generalize to body systems for cataloguing",
            "Healing / cleanse frame is superlative marketing",
            "Pinterest/TikTok visual rhetoric (workers scrubbing organs)",
            "No doses, durations, or clinical contexts",
        ],
    )
