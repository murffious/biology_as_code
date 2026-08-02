"""
Fractional-absorption bounds — the seed that parameterises the gut absorption edges.

``data/bounds-absorption.seed.yaml`` holds one entry per nutrient for the fraction
of an ingested dose that crosses the enterocyte. Every value comes from a
secondary source (Kohlmeier 2003), so every value enters the lattice at ``prior``:
a usable quantitative prior, explicitly *not* a Bound. Promotion needs the primary
read with a population and a dose stated.

Why this exists as data rather than as floats in a registry
-----------------------------------------------------------
``dig/mineral_interactions.py`` already carried a ``typical_bioavailability``
float per mineral. Those floats have no source, no dose, and no cohort — and for
seven of the thirteen overlapping minerals they disagree with this seed. Most of
those disagreements are not errors on either side; they are the *same nutrient
measured under different conditions*, which is precisely what a bare float cannot
say. Zinc is the clean example: 0.70 is real at a 3 mg dose with no competing meal
constituents, and 0.30 is real across a mixed diet. Neither number is wrong. A
model that stores one of them without the condition is.

So this module does not overwrite the registry. It loads the scoped priors
alongside it and gives :func:`reconcile_with_registry` to surface the gaps.

Fraction shapes
---------------
The seed writes fractions the way the source states them, which is not always a
number: ``0.70``, ``"<0.02"``, ``">0.90"``, ``{min, max}``, or a cohort split like
``{young_adult, older}``. :class:`FractionSpec` keeps that shape rather than
flattening it. In particular there is no ``midpoint()`` for a one-sided bound —
averaging ``">0.90"`` into ``0.95`` invents a ceiling the source never gave.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"
SEED_PATH = DATA_DIR / "bounds-absorption.seed.yaml"

#: Seed nutrient ids are namespaced (``nut.zn``, ``vit.c``). Mineral registry ids
#: are bare (``zn``). Only the ``nut.`` namespace maps; ``vit.`` entries belong to
#: the vitamin module and are deliberately not forced into the mineral registry.
_MINERAL_NAMESPACE = "nut."


class SeedUnavailable(RuntimeError):
    """Raised when the seed file cannot be read or parsed."""


def _require_yaml() -> Any:
    try:
        import yaml
    except ModuleNotFoundError as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "parsing the absorption seed needs PyYAML, which is not a runtime "
            "dependency of biology-as-code. Install with: pip install pyyaml"
        ) from exc
    return yaml


@dataclass(frozen=True)
class FractionSpec:
    """A fraction as the source stated it, not as a model would prefer it."""

    raw: Any
    point: float | None = None
    low: float | None = None
    high: float | None = None
    #: ``point`` | ``range`` | ``lower`` | ``upper`` | ``cohort`` | ``unstated``
    kind: str = "unstated"
    #: Populated only for ``kind == "cohort"``: cohort label -> fraction.
    by_cohort: tuple[tuple[str, float], ...] = ()

    @property
    def is_scalar(self) -> bool:
        return self.kind == "point"

    def contains(self, value: float) -> bool:
        """Whether ``value`` is consistent with what the source stated.

        A one-sided bound is satisfied by anything on the stated side; a cohort
        split is satisfied by any of its cohort values. ``unstated`` contains
        nothing — an absent fraction is not a permissive one.
        """
        if self.kind == "unstated":
            return False
        if self.kind == "cohort":
            return any(abs(value - v) < 1e-9 for _label, v in self.by_cohort)
        if self.kind == "point":
            return self.point is not None and abs(value - self.point) < 1e-9
        if self.kind == "lower":
            return self.low is not None and value >= self.low
        if self.kind == "upper":
            return self.high is not None and value <= self.high
        if self.kind == "range":
            return (
                self.low is not None
                and self.high is not None
                and self.low <= value <= self.high
            )
        return False

    def describe(self) -> str:
        if self.kind == "point" and self.point is not None:
            return f"{self.point:g}"
        if self.kind == "lower" and self.low is not None:
            return f">{self.low:g}"
        if self.kind == "upper" and self.high is not None:
            return f"<{self.high:g}"
        if self.kind == "range":
            return f"{self.low:g}-{self.high:g}"
        if self.kind == "cohort":
            return ", ".join(f"{label} {value:g}" for label, value in self.by_cohort)
        return "unstated"


_ONE_SIDED = re.compile(r"^\s*([<>])\s*([0-9]*\.?[0-9]+)\s*$")
_RANGE = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*[-–]\s*([0-9]*\.?[0-9]+)\s*$")


def parse_fraction(raw: Any) -> FractionSpec:
    """Parse a seed ``fraction`` value into a :class:`FractionSpec`.

    Never guesses. An unrecognised shape comes back as ``kind="unstated"`` with
    the original preserved in ``raw``, so a caller can see what it could not read
    instead of receiving a plausible number.
    """
    if raw is None:
        return FractionSpec(raw=raw, kind="unstated")

    if isinstance(raw, bool):
        return FractionSpec(raw=raw, kind="unstated")

    if isinstance(raw, (int, float)):
        return FractionSpec(raw=raw, point=float(raw), kind="point")

    if isinstance(raw, str):
        one_sided = _ONE_SIDED.match(raw)
        if one_sided:
            operator, number = one_sided.groups()
            value = float(number)
            if operator == ">":
                return FractionSpec(raw=raw, low=value, kind="lower")
            return FractionSpec(raw=raw, high=value, kind="upper")
        spread = _RANGE.match(raw)
        if spread:
            low, high = (float(g) for g in spread.groups())
            return FractionSpec(raw=raw, low=low, high=high, kind="range")
        return FractionSpec(raw=raw, kind="unstated")

    if isinstance(raw, dict):
        if "min" in raw and "max" in raw:
            return FractionSpec(
                raw=raw, low=float(raw["min"]), high=float(raw["max"]), kind="range"
            )
        numeric = {
            key: float(value)
            for key, value in raw.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        if numeric:
            return FractionSpec(
                raw=raw,
                kind="cohort",
                by_cohort=tuple(sorted(numeric.items())),
                low=min(numeric.values()),
                high=max(numeric.values()),
            )

    return FractionSpec(raw=raw, kind="unstated")


@dataclass(frozen=True)
class AbsorptionBound:
    """One seed entry: a scoped fractional-absorption prior for one nutrient."""

    id: str
    nutrient: str
    label: str
    edge: str
    fraction: FractionSpec
    gate: str = "prior"
    status: str = "usable"
    site: str | None = None
    dose_ref_mg: float | None = None
    dose_response: Any = None
    form: str | None = None
    basis: str | None = None
    parent_cite: str | None = None
    parent_doi: str | None = None
    parent_provenance: str | None = None
    flag: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None

    @property
    def mineral_id(self) -> str | None:
        """Registry id for ``nut.*`` entries, else None (vitamins, fat, etc.)."""
        if self.nutrient.startswith(_MINERAL_NAMESPACE):
            return self.nutrient[len(_MINERAL_NAMESPACE) :]
        return None

    @property
    def needs_reanchor(self) -> bool:
        """The seed flags this value as superseded; do not admit it as a bound."""
        return self.status.upper() == "REANCHOR"

    @property
    def has_resolved_parent(self) -> bool:
        """A named parent whose DOI was resolved and corroborated, not guessed."""
        return bool(self.parent_doi) and self.parent_provenance == "resolved"


def _to_bound(entry: dict[str, Any]) -> AbsorptionBound:
    parent = entry.get("parent") or {}
    return AbsorptionBound(
        id=str(entry["id"]),
        nutrient=str(entry["nutrient"]),
        label=str(entry.get("label", entry["id"])),
        edge=str(entry.get("edge", "")),
        fraction=parse_fraction(entry.get("fraction")),
        gate=str(entry.get("gate", "prior")),
        status=str(entry.get("status", "usable")),
        site=entry.get("site"),
        dose_ref_mg=entry.get("dose_ref_mg"),
        dose_response=entry.get("dose_response"),
        form=entry.get("form"),
        basis=entry.get("basis"),
        parent_cite=parent.get("cite"),
        parent_doi=parent.get("doi"),
        parent_provenance=parent.get("provenance"),
        flag=entry.get("flag"),
        raw=entry,
    )


@lru_cache(maxsize=1)
def _seed() -> dict[str, Any]:
    if not SEED_PATH.is_file():
        raise SeedUnavailable(f"absorption seed not found at {SEED_PATH}")
    data = _require_yaml().safe_load(SEED_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "bounds" not in data:
        raise SeedUnavailable(f"{SEED_PATH.name}: expected a mapping with a 'bounds' list")
    return data


def seed_meta() -> dict[str, Any]:
    """The seed's own header: source, units, gate default, promotion requirements."""
    return dict(_seed().get("meta") or {})


@lru_cache(maxsize=1)
def absorption_bounds() -> tuple[AbsorptionBound, ...]:
    """Every entry in the seed, in file order."""
    return tuple(_to_bound(entry) for entry in _seed()["bounds"])


def bounds_by_mineral() -> dict[str, AbsorptionBound]:
    """Seed entries keyed by mineral-registry id (``nut.zn`` -> ``zn``)."""
    return {
        bound.mineral_id: bound
        for bound in absorption_bounds()
        if bound.mineral_id is not None
    }


@dataclass(frozen=True)
class Reconciliation:
    """How one registry float relates to the seed's scoped prior for the same nutrient."""

    mineral_id: str
    label: str
    registry_value: float | None
    seed: FractionSpec
    #: ``consistent`` | ``conflict`` | ``reanchor`` | ``dose_dependent`` |
    #: ``seed_only`` | ``registry_only``
    verdict: str
    note: str = ""

    @property
    def is_conflict(self) -> bool:
        return self.verdict == "conflict"


def reconcile_with_registry(
    registry: dict[str, Any] | None = None,
) -> tuple[Reconciliation, ...]:
    """Compare the seed's priors against ``MINERAL_REGISTRY``'s bare floats.

    Reports; does not resolve. A ``conflict`` verdict means the registry's number
    falls outside what the source stated *under the seed's condition* — which is
    usually a scope difference (dose, cohort, meal matrix) rather than one side
    being wrong. Resolving it means deciding which condition the registry float is
    supposed to represent, and that is a modelling decision, not a data cleanup.
    """
    if registry is None:
        from biology_as_code.dig.mineral_interactions import MINERAL_REGISTRY

        registry = MINERAL_REGISTRY

    seeded = bounds_by_mineral()
    out: list[Reconciliation] = []

    for mineral_id in sorted(set(seeded) | set(registry)):
        bound = seeded.get(mineral_id)
        spec = registry.get(mineral_id)
        registry_value = getattr(spec, "typical_bioavailability", None) if spec else None

        if bound is None:
            out.append(
                Reconciliation(
                    mineral_id=mineral_id,
                    label=getattr(spec, "name", mineral_id),
                    registry_value=registry_value,
                    seed=FractionSpec(raw=None, kind="unstated"),
                    verdict="registry_only",
                    note="no seed entry; the registry float has no source at all",
                )
            )
            continue

        if spec is None:
            out.append(
                Reconciliation(
                    mineral_id=mineral_id,
                    label=bound.label,
                    registry_value=None,
                    seed=bound.fraction,
                    verdict="seed_only",
                    note="sourced prior with no MINERAL_REGISTRY entry",
                )
            )
            continue

        if bound.needs_reanchor:
            flag = bound.flag or {}
            out.append(
                Reconciliation(
                    mineral_id=mineral_id,
                    label=bound.label,
                    registry_value=registry_value,
                    seed=bound.fraction,
                    verdict="reanchor",
                    note=str(flag.get("action", "seed flags this value as superseded")),
                )
            )
            continue

        if bound.fraction.kind == "unstated" and bound.dose_response is not None:
            out.append(
                Reconciliation(
                    mineral_id=mineral_id,
                    label=bound.label,
                    registry_value=registry_value,
                    seed=bound.fraction,
                    verdict="dose_dependent",
                    note=(
                        "the source gives a curve, not a fraction; a single float "
                        "cannot represent it"
                    ),
                )
            )
            continue

        if registry_value is None or bound.fraction.kind == "unstated":
            out.append(
                Reconciliation(
                    mineral_id=mineral_id,
                    label=bound.label,
                    registry_value=registry_value,
                    seed=bound.fraction,
                    verdict="seed_only" if registry_value is None else "registry_only",
                    note="neither side states a comparable scalar fraction",
                )
            )
            continue

        consistent = bound.fraction.contains(registry_value)
        condition = []
        if bound.dose_ref_mg is not None:
            condition.append(f"seed dose {bound.dose_ref_mg:g} mg")
        if bound.form:
            condition.append(f"form {bound.form}")
        out.append(
            Reconciliation(
                mineral_id=mineral_id,
                label=bound.label,
                registry_value=registry_value,
                seed=bound.fraction,
                verdict="consistent" if consistent else "conflict",
                note="; ".join(condition),
            )
        )

    return tuple(out)


__all__ = [
    "AbsorptionBound",
    "FractionSpec",
    "Reconciliation",
    "SEED_PATH",
    "SeedUnavailable",
    "absorption_bounds",
    "bounds_by_mineral",
    "parse_fraction",
    "reconcile_with_registry",
    "seed_meta",
]
