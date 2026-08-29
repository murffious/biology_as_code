"""
Signal catalog — typed once, referenced everywhere.

Before this module, hormones appeared as ad-hoc strings scattered through
pathway packs, catalogs and reports. A signal named ``"GLP1"`` in one place and
``"glp-1"`` in another is two signals as far as the code is concerned, and no
test can tell you which one a law meant. The catalog fixes an identifier, a
class, a source tissue and a direction of action for each endogenous signal, so
a law that cites one is citing something checkable.

Medications do not get added to this catalog. A GLP-1 receptor agonist is not
GLP-1: it shares a receptor, not a clock, a source, or a degradation route.
Exogenous inputs enter as :class:`ExogenousSignal` built from the existing
``MedicationProfile`` schema, and carry the endogenous signal they act on in
``acts_on`` rather than impersonating it.

Nothing here has a magnitude. The catalog says *what a signal is*, not what it
does to a given host — that lives in laws and modifiers, which reference these
ids.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

from biology_as_code.engine.clocks import Clock

__all__ = [
    "SignalClass",
    "SignalDirection",
    "Signal",
    "ExogenousSignal",
    "SIGNALS",
    "get_signal",
    "list_signals",
    "signals_from_medication_profile",
]


class SignalClass(str, Enum):
    """What kind of messenger this is."""

    PEPTIDE_HORMONE = "peptide_hormone"
    INCRETIN = "incretin"
    ADIPOKINE = "adipokine"
    METABOLITE = "metabolite"
    NEURAL = "neural"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


#: What the signal does to intake / substrate availability at the whole-host
#: level. Deliberately coarse — three values, not a number.
SignalDirection = Literal["orexigenic", "anorexigenic", "anabolic", "catabolic", "mixed"]


@dataclass(frozen=True)
class Signal:
    """One endogenous signal."""

    id: str
    label: str
    signal_class: SignalClass
    source: str
    """Coarse whole-host direction of action."""
    direction: SignalDirection
    """Clock the signal's own concentration runs on."""
    clock: Clock
    """Free-form aliases seen in the literature; the catalog id is canonical."""
    aliases: tuple[str, ...] = ()
    """Engine parameters this signal is allowed to move. Empty = not yet bound."""
    binding_sites: tuple[str, ...] = ()
    note: str = ""

    @property
    def is_incretin(self) -> bool:
        return self.signal_class is SignalClass.INCRETIN


@dataclass(frozen=True)
class ExogenousSignal:
    """
    A medication or supplement entering the model as a signal.

    ``acts_on`` names the endogenous :class:`Signal` whose pathway this agent
    engages. It is explicitly *not* the same object: an agonist has its own
    onset, duration and clock, and modelling it as the native hormone throws
    away exactly the differences that matter.
    """

    id: str
    label: str
    """Catalog id of the endogenous signal engaged, when there is one."""
    acts_on: str | None
    """agonist | antagonist | substrate | inhibitor | unknown."""
    mode: str = "unknown"
    route: str = "unknown"
    clock: Clock = Clock.EVENT
    """Source record this was built from, for provenance."""
    source_record: dict[str, Any] = field(default_factory=dict)
    note: str = ""

    def resolved_target(self) -> Signal | None:
        """The endogenous signal engaged, if the catalog knows it."""
        return SIGNALS.get(self.acts_on) if self.acts_on else None


def _s(*args: Any, **kwargs: Any) -> tuple[str, Signal]:
    sig = Signal(*args, **kwargs)
    return sig.id, sig


#: The catalog. Keyed by canonical id.
SIGNALS: dict[str, Signal] = dict(
    (
        _s(
            id="ghrelin",
            label="Ghrelin",
            signal_class=SignalClass.PEPTIDE_HORMONE,
            source="gastric oxyntic mucosa (X/A-like cells)",
            direction="orexigenic",
            clock=Clock.MEAL,
            aliases=("lenomorelin",),
            note="Rises pre-prandially, falls after eating. The one clearly orexigenic gut peptide.",
        ),
        _s(
            id="cck",
            label="Cholecystokinin",
            signal_class=SignalClass.PEPTIDE_HORMONE,
            source="duodenal/jejunal I cells",
            direction="anorexigenic",
            clock=Clock.MEAL,
            aliases=("CCK", "cholecystokinin"),
            note="Released to lipid and protein digestion products; drives gallbladder "
            "contraction and pancreatic enzyme secretion as well as satiation.",
        ),
        _s(
            id="glp1",
            label="Glucagon-like peptide-1",
            signal_class=SignalClass.INCRETIN,
            source="ileal/colonic L cells",
            direction="anorexigenic",
            clock=Clock.MEAL,
            aliases=("GLP-1", "GLP1", "glp-1"),
            note="Incretin: potentiates glucose-dependent insulin release and slows "
            "gastric emptying. Short native half-life (DPP-4 cleavage).",
        ),
        _s(
            id="gip",
            label="Glucose-dependent insulinotropic polypeptide",
            signal_class=SignalClass.INCRETIN,
            source="duodenal/jejunal K cells",
            direction="anabolic",
            clock=Clock.MEAL,
            aliases=("GIP", "gastric inhibitory polypeptide"),
            note="The other incretin; more proximal release than GLP-1 and not "
            "anorexigenic on its own.",
        ),
        _s(
            id="pyy",
            label="Peptide YY",
            signal_class=SignalClass.PEPTIDE_HORMONE,
            source="ileal/colonic L cells",
            direction="anorexigenic",
            clock=Clock.MEAL,
            aliases=("PYY", "PYY3-36", "peptide tyrosine tyrosine"),
            note="Co-secreted with GLP-1; part of the ileal brake.",
        ),
        _s(
            id="insulin",
            label="Insulin",
            signal_class=SignalClass.PEPTIDE_HORMONE,
            source="pancreatic beta cells",
            direction="anabolic",
            clock=Clock.MEAL,
            aliases=("INS",),
            note="Substrate disposal and storage. Baseline sensitivity itself runs on "
            "an adaptation clock even though the excursion is per-meal.",
        ),
        _s(
            id="glucagon",
            label="Glucagon",
            signal_class=SignalClass.PEPTIDE_HORMONE,
            source="pancreatic alpha cells",
            direction="catabolic",
            clock=Clock.MEAL,
            aliases=("GCG",),
            note="Counter-regulatory to insulin; hepatic glucose output.",
        ),
        _s(
            id="leptin",
            label="Leptin",
            signal_class=SignalClass.ADIPOKINE,
            source="white adipose tissue",
            direction="anorexigenic",
            clock=Clock.ADAPTATION,
            aliases=("LEP", "OB protein"),
            note="Adiposity signal, not a meal signal. Diurnal modulation rides on an "
            "adaptation-clock level — the only catalog entry not on the meal clock.",
        ),
    )
)

_ALIAS_INDEX: dict[str, str] = {}
for _sig in SIGNALS.values():
    _ALIAS_INDEX[_sig.id.lower()] = _sig.id
    _ALIAS_INDEX[_sig.label.lower()] = _sig.id
    for _alias in _sig.aliases:
        _ALIAS_INDEX[_alias.lower()] = _sig.id


def get_signal(name: str) -> Signal:
    """
    Resolve a signal by id, label or any known alias.

    Raises ``KeyError`` on an unknown name rather than returning None — a law
    that cites a signal the catalog has never heard of is a defect, not a
    missing optional.
    """
    key = str(name).strip().lower()
    if key in _ALIAS_INDEX:
        return SIGNALS[_ALIAS_INDEX[key]]
    raise KeyError(
        f"unknown signal {name!r}; catalog has {sorted(SIGNALS)}. "
        "Medications are not signals — build an ExogenousSignal instead."
    )


def list_signals() -> list[Signal]:
    """Every endogenous signal, in id order."""
    return [SIGNALS[k] for k in sorted(SIGNALS)]


def signals_from_medication_profile(profile: dict[str, Any]) -> list[ExogenousSignal]:
    """
    Build :class:`ExogenousSignal` objects from a ``MedicationProfile`` document.

    Reads the existing schema rather than introducing a parallel one. Entries
    whose target cannot be resolved against the catalog still produce a signal,
    with ``acts_on=None`` — an unrecognised drug is a modelling gap worth
    carrying explicitly, not a reason to drop the medication on the floor.
    """
    out: list[ExogenousSignal] = []
    entries = profile.get("medications") or profile.get("entries") or []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        raw_target = (
            entry.get("acts_on")
            or entry.get("target_signal")
            or (entry.get("engine_hooks") or {}).get("signal")
            or entry.get("mechanism_target")
        )
        target: str | None = None
        if raw_target:
            try:
                target = get_signal(str(raw_target)).id
            except KeyError:
                target = None
        ident = str(entry.get("id") or entry.get("name") or f"exogenous_{len(out)}")
        out.append(
            ExogenousSignal(
                id=ident,
                label=str(entry.get("label") or entry.get("name") or ident),
                acts_on=target,
                mode=str(entry.get("mode") or entry.get("action") or "unknown"),
                route=str(entry.get("route") or "unknown"),
                clock=Clock.EVENT,
                source_record=dict(entry),
                note="" if target or not raw_target else f"unresolved target {raw_target!r}",
            )
        )
    return out
