"""
Rosetta — surface language to typed relation.

The first stage of claim adjudication: take a claim as written and decide what
kind of assertion it is. This is deterministic and lexical on purpose. It is the
stage most likely to be wrong, so it must be the stage easiest to inspect and
correct — every decision returns the token that produced it.

    >>> parse("Iron supports energy and boosts vitality").verb_class
    'soft'
    >>> parse("Vitamin C increases non-heme iron absorption").relation
    'EXPANDS_BOUND'
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: Surface verb -> claim_verb_class, from schemas/relation_enums.subset.json.
#: Ordered most-specific first; the first hit wins.
LEXICON: list[tuple[str, str]] = [
    # disease claims — regulated language, the strongest thing a label can say
    (r"\b(prevents?|prevention of|cures?|treats?|reverses?|protects? against)\b", "disease_claim"),
    (r"\b(reduces? (?:the )?risk of|lowers? (?:the )?risk of)\b", "disease_claim"),

    # explicit gates — presence/absence, requirement, blocking
    (r"\b(requires?|is required for|only .* if|without .* cannot|must be present)\b", "gate"),
    (r"\b(blocks?|prevents? (?:the )?absorption|inhibits?|chelates?|binds?)\b", "gate"),
    (r"\b(enables?|unlocks?|allows? absorption|makes? .* available)\b", "gate"),

    # bounds — directional magnitude change
    (r"\b(increases?|raises?|improves?|enhances?|amplifies?|boosts? (?:the )?absorption)\b",
     "bound_increase"),
    (r"\b(decreases?|lowers?|reduces?|blunts?|suppresses?|slows?)\b", "bound_decrease"),

    # hedges — the field's own uncertainty language
    (r"\b(may|might|could|is associated with|is linked to|suggests?|appears? to)\b", "hedge"),

    # soft / marketing — no mechanism, no endpoint, no magnitude
    (r"\b(supports?|promotes?|helps?|aids?|maintains?|nourishes?)\b", "soft"),
    (r"\b(boosts?|detox\w*|superfood|cleanses?|energizes?|optimi[sz]es?|supercharges?)\b",
     "marketing"),
]

#: verb class -> the typed relation it licenses. Soft and marketing language
#: licenses nothing: it resolves to MALFORMED_MECHANISM by construction.
CLASS_TO_RELATION = {
    "gate": None,               # direction decided by polarity, below
    "bound_increase": "EXPANDS_BOUND",
    "bound_decrease": "NARROWS_BOUND",
    "disease_claim": None,      # decided downstream; often malformed
    "hedge": "NEEDS_RESOLUTION",
    "soft": "MALFORMED_MECHANISM",
    "marketing": "MALFORMED_MECHANISM",
}

_CLOSING = re.compile(
    r"\b(blocks?|inhibits?|chelates?|binds?|prevents? (?:the )?absorption|without)\b", re.I
)
_OPENING = re.compile(
    r"\b(enables?|unlocks?|requires?|is required for|allows?|makes? .* available|with)\b", re.I
)

#: Claims about an endpoint the body reaches, versus a step in the pipeline.
_ENDPOINT = re.compile(
    r"\b(cancer|diabetes|heart disease|mortality|deficiency|obesity|stroke|"
    r"blood pressure|cholesterol|inflammation)\b", re.I
)

#: Claim separators. "/" is deliberately absent: in this domain it separates
#: aliases for one entity ("vitamin A / carotenoids"), not two assertions.
_ATOM_SPLIT = re.compile(r"\s*(?:,| and | plus |;)\s*")


@dataclass(frozen=True)
class RosettaParse:
    """What Rosetta could determine, and what it could not."""

    surface: str
    verb_class: str | None
    surface_verb: str | None
    relation: str | None
    atomized: list[str] = field(default_factory=list)
    reaches_endpoint: bool = False
    hedged: bool = False

    @property
    def typed(self) -> bool:
        """True when the claim carries a mechanism the constitution can check."""
        return self.relation not in (None, "MALFORMED_MECHANISM")


def parse(surface: str) -> RosettaParse:
    """Classify a claim's surface language. Never raises; returns nulls instead."""
    text = (surface or "").strip()
    if not text:
        return RosettaParse(surface="", verb_class=None, surface_verb=None, relation=None)

    verb_class: str | None = None
    surface_verb: str | None = None
    for pattern, cls in LEXICON:
        if m := re.search(pattern, text, re.I):
            verb_class, surface_verb = cls, m.group(0).lower()
            break

    # Hedging is a modifier, not a class: "may increase" is still a bound
    # claim, made tentatively. The class records what is asserted; this records
    # how strongly. The Court caps hedged claims at Plausible.
    hedged = any(
        re.search(pat, text, re.I) for pat, cls in LEXICON if cls == "hedge"
    )
    relation = _resolve_relation(verb_class, text)

    return RosettaParse(
        surface=text,
        verb_class=verb_class,
        surface_verb=surface_verb,
        relation=relation,
        atomized=atomize(text),
        reaches_endpoint=bool(_ENDPOINT.search(text)),
        hedged=hedged,
    )


def _resolve_relation(verb_class: str | None, text: str) -> str | None:
    if verb_class is None:
        # No recognised verb at all. That is not "no relation" — it is a claim
        # the parser could not type, which the Court must treat as unevaluable.
        return None
    if verb_class == "gate":
        if _CLOSING.search(text):
            return "CLOSES_GATE"
        if _OPENING.search(text):
            return "OPENS_GATE"
        return "NEEDS_RESOLUTION"
    if verb_class == "disease_claim":
        # A disease claim is only well-formed if it also names a mechanism.
        # On its own it is a jump from food to endpoint with no pipeline.
        return "MALFORMED_MECHANISM"
    return CLASS_TO_RELATION.get(verb_class)


def atomize(surface: str) -> list[str]:
    """
    Split a compound claim into separately checkable assertions.

    "Iron supports energy and boosts vitality" is two claims wearing one
    sentence, and the weaker one sets the verdict.
    """
    text = (surface or "").strip().rstrip(".")
    if not text:
        return []
    parts = [p.strip() for p in _ATOM_SPLIT.split(text) if p.strip()]
    return parts if len(parts) > 1 else [text]


__all__ = ["parse", "atomize", "RosettaParse", "LEXICON", "CLASS_TO_RELATION"]
