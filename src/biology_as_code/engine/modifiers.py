"""
ModifierBinding — a modifier bound to a place in the engine.

The pathway-graph :class:`~biology_as_code.engine.laws.models.Modifier` says a
nutrient enhances or inhibits a node. That is enough for a walk, and not enough
for host state. A host variable that modifies digestion has to say four further
things before it can be trusted:

``effect_direction``
    Which way it pushes. Separated from magnitude because direction is often
    well established while size is not — an MTHFR variant reduces enzyme
    activity, and how much depends on the variant and the folate status.

``effect_magnitude``
    Size of the push, as a fold change, or ``None`` for *direction only*. A
    binding with a direction and no magnitude is a legitimate, publishable
    state. Inventing a number to fill the field is how a model becomes
    confidently wrong.

``evidence_state``
    ``verified`` | ``supported`` | ``contested`` | ``candidate``. Distinct from
    ``prior``: prior is a weight the walk multiplies, evidence state is a claim
    about the literature that a human curates.

``binding_site``
    A dotted path to the engine process parameter this actually moves. Without
    it a modifier is a note in a database; with it, ``tools/resolve_bindings.py``
    can prove the thing it claims to modify exists.

Genome enters the model here and nowhere else. There is no genotype field on
host state: a variant that has no binding site has no modelled effect, and
saying so explicitly is better than carrying a genotype the engine silently
ignores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Literal

from biology_as_code.engine.clocks import Clock
from biology_as_code.engine.laws.models import RelationType

__all__ = [
    "EffectDirection",
    "EvidenceState",
    "ModifierBinding",
    "BindingRegistry",
    "EVIDENCE_STATES",
]

#: Which way a modifier pushes its binding site.
EffectDirection = Literal["increase", "decrease", "none", "unknown"]

#: Curated claim about the literature behind a binding.
EvidenceState = Literal["verified", "supported", "contested", "candidate"]

EVIDENCE_STATES: tuple[str, ...] = ("verified", "supported", "contested", "candidate")

#: Evidence states that may carry a magnitude into a computation. A contested or
#: candidate binding may still be *declared* with a magnitude, but the engine
#: treats it as direction-only unless a caller opts in explicitly.
_MAGNITUDE_TRUSTED: frozenset[str] = frozenset({"verified", "supported"})


@dataclass(frozen=True)
class ModifierBinding:
    """A modifier bound to a concrete engine parameter."""

    id: str
    """What is doing the modifying: a nutrient, a variant id, a host condition."""
    modifier: str
    """Dotted path to the engine process parameter moved, e.g.
    ``processes.nonhaem_iron.lumen_speciation.reduction_factor``."""
    binding_site: str
    effect_direction: EffectDirection
    relation: RelationType
    evidence_state: EvidenceState
    """Fold change when active; ``None`` means direction is known, size is not."""
    effect_magnitude: float | None = None
    law_ids: tuple[str, ...] = ()
    """Clock on which the modifier's own state changes (a genotype is FIXED, an
    induced enzyme is ADAPTATION)."""
    clock: Clock = Clock.FIXED
    """Context key that must be truthy for this binding to fire."""
    requires_context: str | None = None
    citations: tuple[str, ...] = ()
    note: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.evidence_state not in EVIDENCE_STATES:
            raise ValueError(
                f"{self.id}: evidence_state must be one of {EVIDENCE_STATES}, "
                f"got {self.evidence_state!r}"
            )
        if self.effect_magnitude is not None and self.effect_magnitude <= 0:
            raise ValueError(
                f"{self.id}: effect_magnitude is a fold change and must be positive, "
                f"got {self.effect_magnitude}"
            )
        if not self.binding_site.strip():
            raise ValueError(f"{self.id}: binding_site is required — an unbound modifier is a note")
        if self.effect_direction == "none" and self.effect_magnitude not in (None, 1.0):
            raise ValueError(
                f"{self.id}: effect_direction 'none' contradicts magnitude {self.effect_magnitude}"
            )
        # Direction and magnitude must agree. A magnitude below 1 with direction
        # 'increase' is the kind of sign error that silently inverts a result.
        if self.effect_magnitude is not None:
            if self.effect_direction == "increase" and self.effect_magnitude < 1.0:
                raise ValueError(
                    f"{self.id}: direction 'increase' with magnitude {self.effect_magnitude} < 1"
                )
            if self.effect_direction == "decrease" and self.effect_magnitude > 1.0:
                raise ValueError(
                    f"{self.id}: direction 'decrease' with magnitude {self.effect_magnitude} > 1"
                )

    @property
    def is_direction_only(self) -> bool:
        """True when the binding asserts a direction but no trustworthy size."""
        return self.effect_magnitude is None

    def effective_magnitude(self, *, allow_untrusted: bool = False) -> float | None:
        """
        The fold change the engine should apply, or ``None`` for direction-only.

        Contested and candidate bindings return ``None`` unless
        ``allow_untrusted`` is set, so an unreviewed number cannot reach a
        computation just by being present in the registry.
        """
        if self.effect_magnitude is None:
            return None
        if self.evidence_state in _MAGNITUDE_TRUSTED or allow_untrusted:
            return self.effect_magnitude
        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "modifier": self.modifier,
            "binding_site": self.binding_site,
            "effect_direction": self.effect_direction,
            "effect_magnitude": self.effect_magnitude,
            "relation": self.relation,
            "evidence_state": self.evidence_state,
            "law_ids": list(self.law_ids),
            "clock": self.clock.value,
            "requires_context": self.requires_context,
            "citations": list(self.citations),
            "note": self.note,
        }


class BindingRegistry:
    """A set of bindings, queryable by site and by evidence state."""

    def __init__(self, bindings: Iterable[ModifierBinding] = ()):
        self._by_id: dict[str, ModifierBinding] = {}
        for b in bindings:
            self.add(b)

    def __len__(self) -> int:
        return len(self._by_id)

    def __iter__(self):
        return iter(self._by_id[k] for k in sorted(self._by_id))

    def __contains__(self, binding_id: str) -> bool:
        return binding_id in self._by_id

    def add(self, binding: ModifierBinding) -> None:
        if binding.id in self._by_id:
            raise ValueError(f"duplicate binding id {binding.id!r}")
        self._by_id[binding.id] = binding

    def get(self, binding_id: str) -> ModifierBinding:
        return self._by_id[binding_id]

    def all(self) -> list[ModifierBinding]:
        return [self._by_id[k] for k in sorted(self._by_id)]

    def sites(self) -> list[str]:
        """Every distinct binding site referenced, in order."""
        return sorted({b.binding_site for b in self.all()})

    def by_site(self, site: str) -> list[ModifierBinding]:
        return [b for b in self.all() if b.binding_site == site]

    def by_evidence(self, *states: str) -> list[ModifierBinding]:
        wanted = set(states)
        return [b for b in self.all() if b.evidence_state in wanted]

    def direction_only(self) -> list[ModifierBinding]:
        """Bindings asserting a direction with no usable magnitude."""
        return [b for b in self.all() if b.effective_magnitude() is None]

    def summary(self) -> dict[str, Any]:
        counts: dict[str, int] = {s: 0 for s in EVIDENCE_STATES}
        for b in self.all():
            counts[b.evidence_state] += 1
        return {
            "n": len(self),
            "by_evidence_state": counts,
            "n_direction_only": len(self.direction_only()),
            "n_sites": len(self.sites()),
        }
