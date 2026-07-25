"""
Atomizer — raw claim text → AtomicClaim[] + red flags.

Deterministic heuristics for the vertical slice (P1). A future LLM extractor
must return the same shape; scoring never runs inside the LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .ontology_stub import EntityHit, resolve_outcome, resolve_subject
from .schema import (
    AssertionStrength,
    AtomicClaim,
    ClaimType,
    Intervention,
    Outcome,
    Subject,
)

SUPERLATIVE_RE = re.compile(
    r"\b(only|best|never|always|cure[sd]?|miracle|guaranteed|fastest|#1|number one)\b",
    re.I,
)
ABSOLUTE_RE = re.compile(
    r"\b(pulls?|removes?|eliminates?|destroys?|detox(?:es|ify)?|will|must)\b",
    re.I,
)
DOSE_RE = re.compile(
    r"\b(\d+\s*(?:mg|g|mcg|µg|iu|ml)\b|\d+\s*times?\s*(?:a|per)\s*day|daily|twice daily)",
    re.I,
)


@dataclass
class AtomizeResult:
    subject: Subject
    intervention: Intervention
    atoms: list[AtomicClaim]
    red_flags: list[str]
    matched_fixture: str | None = None


def _strength(text: str, *, superlative: bool = False) -> str:
    if superlative or SUPERLATIVE_RE.search(text):
        return AssertionStrength.SUPERLATIVE.value
    if text.isupper() or ABSOLUTE_RE.search(text):
        return AssertionStrength.ABSOLUTE.value
    if re.search(r"\b(may|might|could|associated|linked|suggests?)\b", text, re.I):
        return AssertionStrength.HEDGED.value
    return AssertionStrength.STRONG.value


def _flags(text: str, intervention: Intervention) -> list[str]:
    flags: list[str] = []
    if text.isupper() or (len(text) > 40 and sum(1 for c in text if c.isupper()) / max(len(text), 1) > 0.45):
        flags.append("Absolute / all-caps framing")
    if not intervention.specified:
        flags.append("No dose, form, or duration specified")
    if SUPERLATIVE_RE.search(text):
        flags.append("Superlative language (only / best / always / cure)")
    if re.search(r"\b(brain|bbb|blood[- ]brain)\b", text, re.I) and re.search(
        r"\b(detox|metal|pull|chelat)", text, re.I
    ):
        flags.append("Mechanism splice risk — site + outcome may be smuggled together")
    if re.search(r"\b(detox|toxin flush|cleanse)\b", text, re.I):
        flags.append("Detox marketing vocabulary — high overclaim rate")
    return flags


def _atom(
    i: int,
    predicate: str,
    outcome_key: str,
    *,
    site: str | None,
    strength: str,
    claim_type: str,
    text: str,
) -> AtomicClaim:
    out = resolve_outcome(outcome_key)
    return AtomicClaim(
        atom_id=f"a{i}",
        predicate=predicate,
        outcome=Outcome(surface=out.surface, canonical=out.canonical, ontology_id=out.ontology_id),
        site=site,
        assertion_strength=strength,
        claim_type=claim_type,
    )


def atomize_spirulina(text: str, subject: EntityHit) -> AtomizeResult:
    """Golden-path atomizer matching claim-intake-card.jsx."""
    atoms = [
        _atom(
            1,
            "chelates / removes",
            "heavy metals",
            site="organs / body",
            strength=AssertionStrength.ABSOLUTE.value,
            claim_type=ClaimType.CAUSAL.value,
            text=text,
        ),
        _atom(
            2,
            "removes",
            "brain metals",
            site="brain",
            strength=AssertionStrength.ABSOLUTE.value,
            claim_type=ClaimType.CAUSAL.value,
            text=text,
        ),
        _atom(
            3,
            "crosses",
            "bbb",
            site=None,
            strength=AssertionStrength.ABSOLUTE.value,
            claim_type=ClaimType.MECHANISTIC.value,
            text=text,
        ),
        _atom(
            4,
            "is the only",
            "food that detoxes brain via BBB",
            site=None,
            strength=AssertionStrength.SUPERLATIVE.value,
            claim_type=ClaimType.SUPERLATIVE.value,
            text=text,
        ),
    ]
    intervention = Intervention(specified=False)
    return AtomizeResult(
        subject=Subject(
            surface=subject.surface,
            canonical=subject.canonical,
            ontology_id=subject.ontology_id,
            form=None,
        ),
        intervention=intervention,
        atoms=atoms,
        red_flags=_flags(text, intervention)
        + [
            "Unsupported superlative — 'only food'",
            "Mechanism splice — 'crosses BBB' ≠ 'chelates metal out'",
        ],
        matched_fixture="spirulina-brain-metals",
    )


def atomize_generic(text: str, subject: EntityHit | None) -> AtomizeResult:
    """
    Single-atom fallback for unknown claims.
    Keeps structure valid so the gauntlet can still run (mostly fails core attacks
    when evidence is unspecified — honest underclaim vs overclaim).
    """
    dose_m = DOSE_RE.search(text)
    intervention = Intervention(
        dose=dose_m.group(0) if dose_m else None,
        specified=bool(dose_m),
    )
    sub = (
        Subject(
            surface=subject.surface,
            canonical=subject.canonical,
            ontology_id=subject.ontology_id,
            form=subject.form_default,
        )
        if subject
        else Subject(surface="unknown", canonical="Unknown subject", ontology_id=None)
    )

    # crude outcome guess
    outcome_key = "cvd"
    for key in (
        "neural tube defects",
        "type 2 diabetes",
        "belly fat",
        "weight loss",
        "strength",
        "cvd",
        "heavy metals",
    ):
        if key.replace(" ", "") in text.lower().replace(" ", "") or key in text.lower():
            outcome_key = key
            break
    else:
        # last clause after "reduces/prevents/causes/cures"
        m = re.search(
            r"\b(?:reduces?|prevents?|causes?|cures?|treats?|boosts?|improves?|lowers?)\s+(.+?)(?:\.|$)",
            text,
            re.I,
        )
        if m:
            outcome_key = m.group(1).strip()[:80]

    superlative = bool(SUPERLATIVE_RE.search(text))
    pred = "affects"
    if re.search(r"\bprevents?\b", text, re.I):
        pred = "prevents"
    elif re.search(r"\bcauses?\b", text, re.I):
        pred = "causes"
    elif re.search(r"\breduces?|lowers?\b", text, re.I):
        pred = "reduces"
    elif re.search(r"\bcures?\b", text, re.I):
        pred = "cures"
    elif superlative:
        pred = "is the only / best"

    ctype = (
        ClaimType.SUPERLATIVE.value
        if superlative
        else ClaimType.CAUSAL.value
        if pred in ("prevents", "causes", "cures", "reduces")
        else ClaimType.ASSOCIATIONAL.value
    )

    atoms = [
        _atom(
            1,
            pred,
            outcome_key,
            site=None,
            strength=_strength(text, superlative=superlative),
            claim_type=ctype,
            text=text,
        )
    ]
    return AtomizeResult(
        subject=sub,
        intervention=intervention,
        atoms=atoms,
        red_flags=_flags(text, intervention),
        matched_fixture=None,
    )


def atomize(text: str) -> AtomizeResult:
    text = (text or "").strip()
    if not text:
        raise ValueError("empty claim text")

    subject = resolve_subject(text)
    low = text.lower()

    # Multi-organ healing-drinks chart (Pinterest) — expand via multi_claim module;
    # here we still return a frame atomization for single-pipeline callers.
    if re.search(r"organ\s+healing\s+drinks?", low) or (
        re.search(r"\b(carrot juice|beetroot|ginger tea|lemon water|coconut water|pomegranate)\b", low)
        and re.search(r"\b(eyes?|brain|lungs?|liver|kidneys?|heart)\b", low)
    ):
        from .organ_systems import resolve_organ

        intervention = Intervention(specified=False)
        atoms = [
            _atom(
                1,
                "heals (frame)",
                "organs via special drinks",
                site="multi-organ",
                strength=AssertionStrength.SUPERLATIVE.value,
                claim_type=ClaimType.SUPERLATIVE.value,
                text=text,
            )
        ]
        # One atom per organ if listed
        i = 2
        for organ_name in ("eyes", "brain", "lungs", "liver", "kidneys", "heart"):
            if re.search(rf"\b{organ_name}\b", low):
                sys = resolve_organ(organ_name)
                atoms.append(
                    _atom(
                        i,
                        "heals",
                        organ_name,
                        site=sys.site if sys else organ_name,
                        strength=AssertionStrength.ABSOLUTE.value,
                        claim_type=ClaimType.CAUSAL.value,
                        text=text,
                    )
                )
                i += 1
        return AtomizeResult(
            subject=Subject(
                surface="organ healing drinks",
                canonical="Multi-organ 'healing drinks' chart",
                ontology_id=None,
                form="infographic",
            ),
            intervention=intervention,
            atoms=atoms,
            red_flags=_flags(text, intervention)
            + [
                "Multi-claim chart — use assay multi-claim expander for per-system grading",
                "Organ list should map to body systems (CV, hepatic, renal, …)",
            ],
            matched_fixture="organ-healing-drinks",
        )

    # Golden fixtures by subject + keywords
    if subject and subject.surface == "spirulina" and re.search(
        r"metal|brain|bbb|blood[- ]brain|detox|chelat", low
    ):
        return atomize_spirulina(text, subject)

    if subject and subject.surface == "creatine" and re.search(
        r"strength|muscle|performance|power", low
    ):
        r = atomize_generic(text, subject)
        r.matched_fixture = "creatine-strength"
        r.atoms = [
            _atom(
                1,
                "increases",
                "strength",
                site="skeletal muscle",
                strength=AssertionStrength.STRONG.value,
                claim_type=ClaimType.CAUSAL.value,
                text=text,
            )
        ]
        r.red_flags = [f for f in r.red_flags if "dose" not in f.lower()]
        r.intervention = Intervention(dose="3–5 g/day (typical studied)", specified=True)
        return r

    if subject and subject.surface == "flavonoids" and re.search(
        r"heart|cardio|cvd|cardiovascular", low
    ):
        r = atomize_generic(text, subject)
        r.matched_fixture = "flavonoids-cvd"
        r.atoms = [
            _atom(
                1,
                "associated with lower risk of",
                "cvd",
                site=None,
                strength=AssertionStrength.HEDGED.value,
                claim_type=ClaimType.ASSOCIATIONAL.value,
                text=text,
            )
        ]
        return r

    if subject and subject.surface == "apple cider vinegar" and re.search(
        r"belly|fat|weight|melt", low
    ):
        r = atomize_generic(text, subject)
        r.matched_fixture = "acv-belly-fat"
        r.atoms = [
            _atom(
                1,
                "melts / removes",
                "belly fat",
                site="abdomen",
                strength=AssertionStrength.ABSOLUTE.value,
                claim_type=ClaimType.CAUSAL.value,
                text=text,
            )
        ]
        r.red_flags = _flags(text, r.intervention) + [
            "Cosmetic fat-loss absolute claim",
        ]
        return r

    return atomize_generic(text, subject)
