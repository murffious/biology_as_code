"""
The auditor's constitution: declared gate and bound rules.

Gate ≠ Bound is the load-bearing distinction in this package, so the two rule
kinds are separate types rather than one table with a flag:

* :class:`GateRule` — **categorical**. A required co-factor is absent, so the
  transport path is not available at all. Absence makes the claim false, not
  merely smaller.
* :class:`BoundRule` — **magnitude**. The path is open either way; a partner or
  matrix state moves the ceiling. No numbers are asserted here, only a signed
  direction, because magnitudes belong to evidence rather than to law.

The register already draws this line itself. LAW-047 states that calcium's effect
on non-haem iron is "a magnitude effect, not a categorical gate like fat for
micelles", and LAW-020 types the lipid requirement as ``dietary_lipid
OPENS_GATE micellar_bioavailability (carotenoids)``. Every rule below carries
``law_refs`` into that register, and ``tests/test_claim_audit.py`` asserts the
structural invariant: a :class:`GateRule` may only cite laws whose card has
``gate.present == True``, and a :class:`BoundRule` only laws where it is False.
The table cannot drift from the constitution without turning CI red.

The table is deliberately small — it covers the mechanisms the repository's
filled packets exercise. An unlisted nutrient yields ``UNEVALUABLE``, never a
default pass. Adding a rule is a source-backed decision, not a convenience.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Predicate = Literal["positive", "true", "false"]
Direction = Literal["EXPANDS_BOUND", "NARROWS_BOUND"]


def _satisfied(predicate: Predicate, value: Any) -> bool:
    if predicate == "positive":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0
    if predicate == "true":
        return value is True
    return value is False


@dataclass(frozen=True)
class GateRule:
    """A categorical requirement. Fails closed when no required field is declared.

    ``requires`` holds one or more ``(field, predicate)`` alternatives. The gate is
    satisfied if **any** declared alternative passes, unknown if **none** are
    declared, and failed if at least one is declared and every declared one fails.

    Alternatives exist so a gate can be opened by a structural fact rather than a
    magnitude. ``dietary_lipid_g`` needs a number, and a packet author who does not
    have a sourced number should not have to invent one to record that a meal
    obviously contains a lipid phase — olive oil does, by construction. Declaring
    ``lipid_phase_present: true`` opens the gate while leaving the magnitude
    unlocked, which is the same discipline the LAW-026 energy band follows.
    """

    nutrient: str
    requires: tuple[tuple[str, Predicate], ...]
    kingdom: str
    gate_note: str
    law_refs: tuple[str, ...] = ()

    @property
    def fields(self) -> tuple[str, ...]:
        return tuple(field for field, _ in self.requires)

    def predicate_for(self, field: str) -> Predicate | None:
        for name, predicate in self.requires:
            if name == field:
                return predicate
        return None

    def satisfied_by(self, field: str, value: Any) -> bool:
        predicate = self.predicate_for(field)
        return False if predicate is None else _satisfied(predicate, value)


@dataclass(frozen=True)
class BoundRule:
    """A signed magnitude modifier. Never asserts a number."""

    nutrient: str
    triggered_by: str
    predicate: Predicate
    direction: Direction
    note: str
    law_refs: tuple[str, ...] = ()
    source: Literal["partner", "matrix"] = "partner"

    def satisfied_by(self, value: Any) -> bool:
        return _satisfied(self.predicate, value)


# --- Gates -------------------------------------------------------------------
# Hydrophobic cargo needs a lipid phase for micellar presentation (LAW-020), and
# absorbed cargo leaves the enterocyte by chylomicron/lymph (LAW-045). With no
# lipid phase declared in the meal, the path is shut rather than narrowed.

_FAT_VEHICLE_NOTE = (
    "dietary lipid co-present required for micellar presentation of hydrophobic cargo"
)

_FAT_VEHICLE_CARGO = (
    "beta_carotene",
    "carotenoids",
    "lutein",
    "lycopene",
    "phylloquinone",
    "retinol",
    "vitamin_a",
    "vitamin_d",
    "vitamin_e",
    "vitamin_k",
)

_IF_NOTE = "gastric intrinsic factor plus an intact ileal receptor path required"

# Either a declared lipid magnitude or a declared lipid phase opens the gate.
# The structural boolean lets a packet be filled in without inventing grams.
_FAT_VEHICLE_REQUIRES: tuple[tuple[str, Predicate], ...] = (
    ("dietary_lipid_g", "positive"),
    ("lipid_phase_present", "true"),
)

GATE_RULES: tuple[GateRule, ...] = tuple(
    GateRule(
        nutrient=nutrient,
        requires=_FAT_VEHICLE_REQUIRES,
        kingdom="lumen",
        gate_note=_FAT_VEHICLE_NOTE,
        law_refs=("LAW-020", "LAW-045"),
    )
    for nutrient in _FAT_VEHICLE_CARGO
) + (
    GateRule(
        nutrient="cobalamin",
        requires=(("intrinsic_factor", "true"),),
        kingdom="lumen",
        gate_note=_IF_NOTE,
        law_refs=("LAW-043",),
    ),
    GateRule(
        nutrient="vitamin_b12",
        requires=(("intrinsic_factor", "true"),),
        kingdom="lumen",
        gate_note=_IF_NOTE,
        law_refs=("LAW-043",),
    ),
)


# --- Bounds ------------------------------------------------------------------
# Non-haem iron is the canonical bound story: the path stays open, partners move
# the ceiling. Modelling this as a gate is the classic error LAW-047 warns about.

BOUND_RULES: tuple[BoundRule, ...] = (
    BoundRule(
        nutrient="nonhaem_iron",
        triggered_by="ascorbate_same_meal",
        predicate="true",
        direction="EXPANDS_BOUND",
        note="ascorbate reduces and chelates Fe, and can override tannin inhibition",
        law_refs=("LAW-004",),
    ),
    BoundRule(
        nutrient="nonhaem_iron",
        triggered_by="tea_tannins",
        predicate="true",
        direction="NARROWS_BOUND",
        note="tea/coffee tannins bind Fe and reduce non-haem absorption",
        law_refs=("LAW-006",),
    ),
    BoundRule(
        nutrient="nonhaem_iron",
        triggered_by="calcium_same_meal",
        predicate="true",
        direction="NARROWS_BOUND",
        note="competitive luminal interaction; magnitude effect, not a categorical gate",
        law_refs=("LAW-047",),
    ),
    BoundRule(
        nutrient="*",
        triggered_by="destroyed",
        predicate="true",
        direction="EXPANDS_BOUND",
        note="matrix disruption raises accessible surface area and free substrate vs intact form",
        law_refs=("LAW-024",),
        source="matrix",
    ),
    BoundRule(
        nutrient="*",
        triggered_by="intact",
        predicate="true",
        direction="NARROWS_BOUND",
        note="intact food form slows emptying and lowers the accessible fraction",
        law_refs=("LAW-024",),
        source="matrix",
    ),
)


# --- Verb classification -----------------------------------------------------
# Verb classes come from schemas/relation_enums.subset.json. Soft and marketing
# verbs carry no typed mechanism or endpoint, so they are refused before any
# packet is touched — there is nothing to evaluate against.

UNAUDITABLE_VERB_CLASSES: frozenset[str] = frozenset({"soft", "marketing", "hedge"})
MECHANISM_VERB_CLASSES: frozenset[str] = frozenset({"gate", "bound_increase", "bound_decrease"})
ENDPOINT_VERB_CLASSES: frozenset[str] = frozenset({"disease_claim"})


def gates_for(nutrient: str) -> tuple[GateRule, ...]:
    """Gate rules that apply to a nutrient. Empty tuple means no categorical gate."""
    return tuple(rule for rule in GATE_RULES if rule.nutrient == nutrient)


def bounds_for(nutrient: str) -> tuple[BoundRule, ...]:
    """Bound rules for a nutrient, including wildcard matrix rules."""
    return tuple(rule for rule in BOUND_RULES if rule.nutrient in (nutrient, "*"))


def known_nutrients() -> tuple[str, ...]:
    """Every nutrient this table can say anything about."""
    named = {rule.nutrient for rule in GATE_RULES}
    named |= {rule.nutrient for rule in BOUND_RULES if rule.nutrient != "*"}
    return tuple(sorted(named))


def all_law_refs() -> tuple[str, ...]:
    """Every law id cited by the table, de-duplicated and sorted."""
    refs: set[str] = set()
    for rule in GATE_RULES:
        refs |= set(rule.law_refs)
    for rule in BOUND_RULES:
        refs |= set(rule.law_refs)
    return tuple(sorted(refs))
