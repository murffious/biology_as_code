"""A number that carries the record that grounds it.

WHY
---
Before this module, every constant in `dig/` was a bare literal:

    SOD_O2_PER_H2O2 = 2
    PO_NADH = 2.5

Both are emitted in `to_dict()` payloads, so a consumer reads them as assertions
about mammalian biochemistry with nothing attached. Nothing in the tree recorded
where either came from, whether anyone had checked, or whether the engine was
allowed to multiply by it. `docs/metabolic-constants.md` answered all three in
prose, which no test can read.

A resolve pass on 2026-09-07 is the reason this is not a theoretical worry:
12 of 17 PMIDs shipped in this repository named a different paper, and four of
those were "corrections" that replaced one wrong id with another. Prose that
says a number is sourced is not the same as a number that is sourced.

WHAT
----
`grounded()` returns an `int` or `float` subclass, so every existing use keeps
working — arithmetic, equality against a literal, `json.dumps` — while the value
itself carries its tier and the PMID that grounds it.

    SOD_O2_PER_H2O2 = grounded(2, tier="identity", pmid="5389100",
                               supports="SOD dismutates 2 superoxide per H2O2")

`tools/check_constants.py` then refuses a bare literal at module level in `dig/`,
and refuses a PMID that has not resolved to the paper it claims.

THE TIERS ARE THE ONES IN docs/metabolic-constants.md
-----------------------------------------------------
`identity`  — stoichiometry, true by the chemistry. May be encoded and computed.
`teaching`  — an accepted physiological value with real spread. May be *named*,
              never multiplied by a meal field.
`population`— a host/microbiota statistic. Must stay OPEN, so it may not appear
              in code at all; `grounded()` rejects it rather than letting a
              tier-3 number acquire the look of provenance by being annotated.
"""

from __future__ import annotations

from typing import Literal

Tier = Literal["identity", "teaching"]
TIERS: frozenset[str] = frozenset({"identity", "teaching"})

#: Tier 3. Named here so the refusal is discoverable from code, not only prose.
REFUSED_TIER = "population"


class GroundedInt(int):
    """An `int` that knows its tier and its PubMed record.

    No `__slots__`: CPython forbids a non-empty one on an `int` subclass, which
    is variable-length. The three attributes live in the instance dict.
    """

    tier: str
    pmid: str
    supports: str

    def __new__(cls, value: int, *, tier: str, pmid: str, supports: str) -> GroundedInt:
        self = super().__new__(cls, value)
        self.tier, self.pmid, self.supports = tier, pmid, supports
        return self

    def __repr__(self) -> str:
        return f"{int(self)!r} <{self.tier} PMID {self.pmid}>"


class GroundedFloat(float):
    """A `float` that knows its tier and its PubMed record.

    Same reason as `GroundedInt` for carrying no `__slots__`.
    """

    tier: str
    pmid: str
    supports: str

    def __new__(cls, value: float, *, tier: str, pmid: str, supports: str) -> GroundedFloat:
        self = super().__new__(cls, value)
        self.tier, self.pmid, self.supports = tier, pmid, supports
        return self

    def __repr__(self) -> str:
        return f"{float(self)!r} <{self.tier} PMID {self.pmid}>"


Grounded = GroundedInt | GroundedFloat


def grounded(
    value: int | float,
    *,
    tier: str,
    pmid: str,
    supports: str,
) -> Grounded:
    """Attach a tier and a PubMed id to a constant.

    Raises on a tier-3 value: a population statistic does not become encodable by
    acquiring a citation, and annotating one would make it look as though it had.
    """
    if tier == REFUSED_TIER:
        raise ValueError(
            f"tier {REFUSED_TIER!r} may not be encoded — it must stay OPEN "
            "(see docs/metabolic-constants.md, tier 3)"
        )
    if tier not in TIERS:
        raise ValueError(f"unknown tier {tier!r}; expected one of {sorted(TIERS)}")
    if not pmid.isdigit():
        raise ValueError(f"pmid must be digits, got {pmid!r}")
    if not supports.strip():
        raise ValueError("a grounded constant must say what the source supports")
    if isinstance(value, bool):
        raise TypeError("a bool is not a measured constant")
    if isinstance(value, int):
        return GroundedInt(value, tier=tier, pmid=pmid, supports=supports)
    return GroundedFloat(float(value), tier=tier, pmid=pmid, supports=supports)


def sources_for(namespace: object) -> dict[str, dict[str, str]]:
    """Every grounded constant in a module, as {name: {tier, pmid, supports}}.

    The payload shape of `to_dict()` is deliberately unchanged — a consumer that
    wants the warrant asks for it here rather than having it interleaved with the
    numbers.
    """
    out: dict[str, dict[str, str]] = {}
    for name in dir(namespace):
        value = getattr(namespace, name, None)
        if isinstance(value, (GroundedInt, GroundedFloat)):
            out[name] = {
                "value": str(value),
                "tier": value.tier,
                "pmid": value.pmid,
                "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{value.pmid}/",
                "supports": value.supports,
            }
    return out
