"""
Deterministic scoring gauntlet — PLAN.md §5.

LLM never decides a grade. Same evidence set + atoms + rubric_version → same verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schema import (
    AtomicClaim,
    AttackName,
    AttackResult,
    Verdict,
    VerdictLabel,
)

RUBRIC_VERSION = "1.0.0"

# Evidence set keys used by fixtures / mock grounder
# {
#   "human_studies": int,
#   "human_directly_supports": bool,
#   "animal_or_in_vitro_only": bool,
#   "dose_form_match": bool,          # studied form matches claimed use
#   "mechanism_only": bool,           # mechanism sold as clinical outcome
#   "effect_size_meaningful": bool,
#   "confounding_concern": bool,
#   "has_superlative_atom": bool,
#   "superlative_false": bool,
#   "replication_count": int,         # independent replications of the core claim
#   "rebuttals": int,
#   "confidence_prior": float,        # 0..1 optional
# }


@dataclass
class EvidenceSet:
    human_studies: int = 0
    human_directly_supports: bool = False
    animal_or_in_vitro_only: bool = False
    dose_form_match: bool = True
    mechanism_only: bool = False
    effect_size_meaningful: bool = False
    confounding_concern: bool = False
    has_superlative_atom: bool = False
    superlative_false: bool = False
    replication_count: int = 0
    rebuttals: int = 0
    confidence_prior: float = 0.5
    notes: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> "EvidenceSet":
        if not d:
            return cls()
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in d.items() if k in known and k != "notes"}, notes=d.get("notes") or {})


def _run_attacks(
    atoms: list[AtomicClaim],
    evidence: EvidenceSet,
) -> list[AttackResult]:
    has_super = evidence.has_superlative_atom or any(
        a.assertion_strength == "superlative" or a.claim_type == "superlative" for a in atoms
    )
    multi = len(atoms) > 1
    # Parity with TS score.ts: absHeavy over ALL atoms; fail if multi && ≥2
    abs_heavy = [
        a
        for a in atoms
        if a.assertion_strength in ("absolute", "superlative") or a.claim_type == "superlative"
    ]
    atomization_pass = not (multi and len(abs_heavy) >= 2)

    attacks: list[AttackResult] = [
        AttackResult(
            name=AttackName.ATOMIZATION.value,
            pass_=atomization_pass,
            finding=(
                evidence.notes.get(
                    "atomization",
                    f"Bundle splits into {len(atoms)} atom(s). "
                    + (
                        "Weaker absolute/superlative atoms ride behind any kernel."
                        if multi and not atomization_pass
                        else (
                            "Multiple atoms but atomization clean."
                            if multi
                            else "Single atom — atomization clean."
                        )
                    ),
                )
            ),
            core=False,
        ),
        AttackResult(
            name=AttackName.HUMAN_EVIDENCE.value,
            pass_=evidence.human_directly_supports and evidence.human_studies > 0,
            finding=evidence.notes.get(
                "human_evidence",
                (
                    f"{evidence.human_studies} human study signal(s); directly supports claim."
                    if evidence.human_directly_supports
                    else (
                        f"Only animal/in-vitro or off-target human data remain "
                        f"(human_studies={evidence.human_studies})."
                        if evidence.animal_or_in_vitro_only or evidence.human_studies == 0
                        else "Human literature exists but does not directly support this wording."
                    )
                ),
            ),
            core=True,
        ),
        AttackResult(
            name=AttackName.DOSE_FORM.value,
            pass_=evidence.dose_form_match,
            finding=evidence.notes.get(
                "dose_form",
                "Studied form matches claimed use."
                if evidence.dose_form_match
                else "Studied dose/form does not match what the claim implies (extract vs food, clinical vs kitchen).",
            ),
            core=True,
        ),
        AttackResult(
            name=AttackName.MECHANISM_VS_OUTCOME.value,
            pass_=not evidence.mechanism_only,
            finding=evidence.notes.get(
                "mechanism_vs_outcome",
                "Mechanism sold as a demonstrated clinical outcome."
                if evidence.mechanism_only
                else "Outcome-level evidence present (or not purely mechanism storytelling).",
            ),
            core=True,
        ),
        AttackResult(
            name=AttackName.EFFECT_SIZE.value,
            pass_=evidence.effect_size_meaningful,
            finding=evidence.notes.get(
                "effect_size",
                "Effect size is clinically meaningful where claimed."
                if evidence.effect_size_meaningful
                else "Even if a signal exists, effect size is trivial, surrogate-only, or unshown in the claimed population.",
            ),
            core=False,
        ),
        AttackResult(
            name=AttackName.CONFOUNDING.value,
            pass_=not evidence.confounding_concern,
            finding=evidence.notes.get(
                "confounding",
                "Material confounding / funding concern."
                if evidence.confounding_concern
                else "Not the weak point — confounding attack does not land.",
            ),
            core=False,
        ),
        AttackResult(
            name=AttackName.SUPERLATIVE.value,
            pass_=(not has_super) or (not evidence.superlative_false),
            finding=evidence.notes.get(
                "superlative",
                (
                    "No superlative atom."
                    if not has_super
                    else (
                        "Superlative fails — counterexamples exist."
                        if evidence.superlative_false
                        else "Superlative language present but not falsified in this evidence set."
                    )
                ),
            ),
            core=True,
        ),
        AttackResult(
            name=AttackName.REPLICATION.value,
            pass_=evidence.replication_count >= 2
            or (evidence.human_directly_supports and evidence.replication_count >= 1 and evidence.human_studies >= 3),
            finding=evidence.notes.get(
                "replication",
                f"Independent replication count ≈ {evidence.replication_count}; "
                f"human_studies={evidence.human_studies}.",
            ),
            core=True,
        ),
    ]

    return attacks


def _confidence(evidence: EvidenceSet, attacks: list[AttackResult]) -> float:
    """Monotone confidence: rebuttals and failed core attacks only lower score."""
    c = max(0.0, min(1.0, evidence.confidence_prior))
    failed_core = sum(1 for a in attacks if a.core and not a.pass_)
    failed_soft = sum(1 for a in attacks if not a.core and not a.pass_)
    c *= 0.55**failed_core
    c *= 0.85**failed_soft
    c *= 0.9 ** max(0, evidence.rebuttals)
    return round(c, 4)


def score(
    evidence: EvidenceSet | dict[str, Any] | None,
    atoms: list[AtomicClaim],
    rubric_version: str = RUBRIC_VERSION,
) -> tuple[Verdict, list[AttackResult], float]:
    """
    Pure function. Returns (verdict, attacks, confidence).
    Verdict map (PLAN.md §5):
      - dies on a core attack → BUSTED
      - core holds but soft attacks fail (size/scope) → PLAUSIBLE
      - survives all → CONFIRMED
    """
    ev = evidence if isinstance(evidence, EvidenceSet) else EvidenceSet.from_dict(evidence)
    attacks = _run_attacks(atoms, ev)

    survived_names = [a.name for a in attacks if a.pass_]
    failed_names = [a.name for a in attacks if not a.pass_]
    core_failed = [a.name for a in attacks if a.core and not a.pass_]
    soft_failed = [a.name for a in attacks if not a.core and not a.pass_]

    if core_failed:
        label = VerdictLabel.BUSTED.value
        rule = f"dies on core attack(s): {', '.join(core_failed)}"
    elif soft_failed or ev.rebuttals > 0:
        label = VerdictLabel.PLAUSIBLE.value
        rule = "core holds but overstated on size/scope/confounding"
    else:
        label = VerdictLabel.CONFIRMED.value
        rule = "survives all attacks in the gauntlet"

    verdict = Verdict(
        label=label,
        survived=len(survived_names),
        total=len(attacks),
        rubric_version=rubric_version,
        failed_attacks=failed_names,
        survived_attacks=survived_names,
        rule=rule,
    )
    conf = _confidence(ev, attacks)
    return verdict, attacks, conf


def apply_atom_grades(
    atoms: list[AtomicClaim],
    attacks: list[AttackResult],
    verdict_label: str,
) -> list[AtomicClaim]:
    """Stamp per-atom grade labels for UI (intake card style)."""
    fail_set = {a.name for a in attacks if not a.pass_}
    out: list[AtomicClaim] = []
    for a in atoms:
        grade = "Moderate"
        if a.claim_type == "superlative" or a.assertion_strength == "superlative":
            grade = "False" if AttackName.SUPERLATIVE.value in fail_set else "Low"
        elif a.claim_type == "mechanistic" and AttackName.MECHANISM_VS_OUTCOME.value in fail_set:
            grade = "Very low"
        elif AttackName.HUMAN_EVIDENCE.value in fail_set:
            grade = "Very low" if a.site == "brain" else "Low"
        elif verdict_label == VerdictLabel.CONFIRMED.value:
            grade = "High"
        elif verdict_label == VerdictLabel.PLAUSIBLE.value:
            grade = "Moderate"
        else:
            grade = "Low"
        stamped = AtomicClaim(
            atom_id=a.atom_id,
            predicate=a.predicate,
            outcome=a.outcome,
            site=a.site,
            assertion_strength=a.assertion_strength,
            claim_type=a.claim_type,
            grade=grade,
            survived=[x for x in (a.survived or [])],
            failed=[x for x in (a.failed or [])],
            evidence_basis=a.evidence_basis,
            graph_ref=a.graph_ref,
        )
        out.append(stamped)
    return out
