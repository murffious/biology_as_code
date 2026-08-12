"""
LAW-004 in Abstract Physiological Operation form.

The registry statement — "co-ingested ascorbic acid increases non-haem Fe
absorption and can overcome inhibitors such as tea tannin" — is true and
under-specified. It does not fix the order the effects apply in, what to do when
the ascorbate dose is unknown, or what "can overcome" means when both modifiers
fire. This module is the same law with those gaps closed, written in the
notation of ``docs/notational-conventions.md``.

Five numbered steps, executed in order. The step numbers are stable and are
cited by ``tests/test_ao_law_004.py``; a step that turns out to be wrong is
marked withdrawn and kept, never renumbered.

The three decisions the prose left open, and how they are resolved:

**Domain boundary is asserted, not assumed** (AO-004.1). Haem iron uses ``!``,
not ``?``: applying an ascorbate fold to haem iron is not a wide answer, it is a
wrong one, so the step refuses instead of widening.

**Concurrency is established before the fold** (AO-004.2 before AO-004.3).
Ascorbate two hours after the meal is not a smaller effect, it is no effect.
Applying the fold and discounting it afterwards gets the wrong shape.

**"Can overcome" is arithmetic, not precedence** (AO-004.4). Both modifiers
apply multiplicatively. Under Derman's conditions ascorbate's ~10× against
tannin's ~0.55× nets above the tea-free baseline; encoding ascorbate as *winning*
would give the wrong answer at every dose where it does not.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from biology_as_code.engine.clocks import Clock
from biology_as_code.engine.fluxes import Flux

__all__ = [
    "AOStep",
    "UncertaintyCompletion",
    "LAW_004_AO",
    "LAW_004_ASCORBATE_FOLD_BOUNDS",
    "LAW_004_DOSE_BOUNDS_MG",
    "apply_law_004",
    "OutOfKingdom",
]

LAW_ID = "LAW-004"

#: The literature's own spread, not a modelling choice. ~2x for orange-juice
#: doses (Rossander 1979), up to ~10x in the tea-rescue conditions (Derman
#: 1977). A single point value would be presenting one paper's condition as the
#: law.
LAW_004_ASCORBATE_FOLD_BOUNDS: tuple[float, float] = (1.5, 10.0)

#: Normative bounds on the host-defined ascorbate dose. A host supplying a value
#: outside this range is non-conforming, and a validator can say so without
#: knowing anything about that host's model.
LAW_004_DOSE_BOUNDS_MG: tuple[float, float] = (0.0, 2000.0)

#: Tannin narrowing from LAW-006, carried here because AO-004.4 resolves the two
#: together. 3.8% -> 2.1% in the Derman tea arm.
_TANNIN_FOLD = 0.55

CompletionState = Literal["normal", "out_of_kingdom", "contested"]


class OutOfKingdom(ValueError):
    """
    The input falls outside the law's modelled domain.

    Not an error in the input — an error in applying *this law* to it. The law
    simply does not speak to the case, and saying so is more useful than
    returning a number.
    """


@dataclass(frozen=True)
class UncertaintyCompletion:
    """
    A value with its uncertainty state, per the ``?`` / ``!`` conventions.

    ``bounds`` is mandatory whenever ``value`` is present. The whole point of
    the record is to stop a number travelling without its uncertainty, so a
    point value with no interval is rejected at construction.
    """

    state: CompletionState
    value: float | None = None
    bounds: tuple[float, float] | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if self.value is not None and self.bounds is None:
            raise ValueError(
                "a completion carrying a value must carry bounds; a number without "
                "its uncertainty is exactly what this record exists to prevent"
            )
        if self.bounds is not None:
            lo, hi = self.bounds
            if lo > hi:
                raise ValueError(f"bounds are inverted: {self.bounds}")

    @property
    def is_known(self) -> bool:
        return self.state == "normal"

    def widen(self, to: tuple[float, float], note: str = "") -> UncertaintyCompletion:
        """
        The ``?`` operator: propagate, widening bounds.

        Widening is monotone. An implementation whose ``?`` narrows an interval
        is non-conforming, so a narrowing request raises rather than being
        silently honoured.
        """
        lo, hi = to
        if self.bounds is not None:
            cur_lo, cur_hi = self.bounds
            if lo > cur_lo or hi < cur_hi:
                raise ValueError(
                    f"? may only widen: {self.bounds} -> {to} narrows the interval"
                )
        return UncertaintyCompletion(
            state="contested" if self.state != "out_of_kingdom" else self.state,
            value=self.value,
            bounds=(lo, hi),
            note=note or self.note,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "value": self.value,
            "bounds": list(self.bounds) if self.bounds else None,
            "note": self.note,
        }


@dataclass(frozen=True)
class AOStep:
    """One numbered Abstract Physiological Operation."""

    number: str
    name: str
    reads: tuple[str, ...]
    writes: tuple[str, ...]
    precondition: str
    effect: str
    uncertainty: str
    withdrawn: str = ""

    @property
    def is_withdrawn(self) -> bool:
        return bool(self.withdrawn)

    @property
    def law_id(self) -> str:
        return self.number.split(".")[0].replace("AO-", "LAW-")


#: The law, as an ordered list. Order is normative: an implementation applying
#: these in a different order is non-conforming even where the arithmetic
#: commutes.
LAW_004_AO: tuple[AOStep, ...] = (
    AOStep(
        number="AO-004.1",
        name="Admit non-haem iron",
        reads=("packet.cargo[nonhaem_Fe]", "packet.identity"),
        writes=("[[lumen_fe]]",),
        precondition="require !nonhaem_species",
        effect="[[lumen_fe]] <- packet.cargo[nonhaem_Fe]",
        uncertainty="haem iron => out_of_kingdom; the law does not speak to it",
    ),
    AOStep(
        number="AO-004.2",
        name="Establish same-meal concurrency",
        reads=("context_stream.ascorbate_same_meal", "context_stream.co_ingested"),
        writes=("[[concurrent]]",),
        precondition="none",
        effect="[[concurrent]] <- ascorbate present in the SAME eating occasion",
        uncertainty="unknown timing => contested, [[concurrent]] = false",
    ),
    AOStep(
        number="AO-004.3",
        name="Apply the ascorbate fold",
        reads=("[[concurrent]]", "<ascorbate_dose_mg>"),
        writes=("[[yield]]",),
        precondition="[[concurrent]] is true, else step does not run",
        effect="[[yield]] <- [[yield]] x ?ascorbate_fold",
        uncertainty=f"dose unknown => contested over {LAW_004_ASCORBATE_FOLD_BOUNDS}",
    ),
    AOStep(
        number="AO-004.4",
        name="Resolve against tannin inhibition (LAW-006)",
        reads=("[[yield]]", "context_stream.tannin_same_meal"),
        writes=("[[yield]]",),
        precondition="none",
        effect="both modifiers apply multiplicatively, in registry order",
        uncertainty="neither modifier is skipped when the other fires",
    ),
    AOStep(
        number="AO-004.5",
        name="Emit",
        reads=("[[yield]]",),
        writes=("packet.cargo[nonhaem_Fe]", "fluxes"),
        precondition="none",
        effect="Flux(nonhaem_Fe, %Duodenum% -> portal) at the resolved yield",
        uncertainty="a contested [[yield]] emits a contested flux; carried, not dropped",
    ),
)


@dataclass
class LawResult:
    """Outcome of executing the law, with the step trace."""

    yield_completion: UncertaintyCompletion
    delivered_fe: float | None
    flux: Flux | None
    steps_run: list[str] = field(default_factory=list)
    log: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "law": LAW_ID,
            "yield": self.yield_completion.as_dict(),
            "delivered_fe": self.delivered_fe,
            "flux": self.flux.as_dict() if self.flux else None,
            "steps_run": list(self.steps_run),
            "log": list(self.log),
        }


def _dose_to_fold(dose_mg: float) -> float:
    """
    Map a host-supplied ascorbate dose onto a fold within the law's bounds.

    Linear in log dose between the two cited anchors: ~2x at an orange-juice
    dose (~75 mg, Rossander) and ~10x at the tea-rescue dose (~1000 mg,
    Derman). Interpolation between two published points, clamped to the law's
    bounds — not a fitted curve, and it does not pretend to be one.
    """
    import math

    lo_fold, hi_fold = LAW_004_ASCORBATE_FOLD_BOUNDS
    if dose_mg <= 0:
        return 1.0
    lo_dose, hi_dose = 75.0, 1000.0
    if dose_mg <= lo_dose:
        return min(2.0, hi_fold)
    if dose_mg >= hi_dose:
        return hi_fold
    span = math.log(hi_dose / lo_dose)
    frac = math.log(dose_mg / lo_dose) / span
    return max(lo_fold, min(hi_fold, 2.0 + frac * (hi_fold - 2.0)))


def apply_law_004(
    *,
    lumen_fe: float,
    species: str = "nonhaem",
    ascorbate_same_meal: bool | None = None,
    ascorbate_dose_mg: float | None = None,
    tannin_same_meal: bool = False,
    dt_seconds: float = 3600.0,
) -> LawResult:
    """
    Execute LAW-004 in AO order.

    ``ascorbate_same_meal=None`` means the timing is unknown, which is not the
    same as absent: AO-004.2 marks it contested and proceeds with concurrency
    false. ``ascorbate_dose_mg=None`` with concurrency true means present but
    unquantified, which AO-004.3 handles with ``?`` — the fold widens to the
    law's full bound rather than defaulting to a plausible number.
    """
    steps: list[str] = []
    log: list[str] = []

    # --- AO-004.1 Admit non-haem iron ------------------------------------
    steps.append("AO-004.1")
    if species != "nonhaem":
        raise OutOfKingdom(
            f"{LAW_ID} AO-004.1: species {species!r} is outside the law's domain. "
            "The ascorbate fold characterises non-haem iron only; applying it to "
            "haem iron would be wrong rather than merely uncertain."
        )
    working = float(lumen_fe)
    log.append(f"AO-004.1: admitted {working} non-haem Fe")

    # --- AO-004.2 Establish same-meal concurrency ------------------------
    steps.append("AO-004.2")
    timing_unknown = ascorbate_same_meal is None
    concurrent = bool(ascorbate_same_meal)
    if timing_unknown:
        log.append("AO-004.2: ascorbate timing unknown => contested, concurrency false")
    else:
        log.append(f"AO-004.2: concurrency = {concurrent}")

    # --- AO-004.3 Apply the ascorbate fold -------------------------------
    completion = UncertaintyCompletion(
        state="contested" if timing_unknown else "normal",
        value=1.0,
        bounds=(1.0, 1.0),
        note="no ascorbate effect applied",
    )
    if concurrent:
        steps.append("AO-004.3")
        if ascorbate_dose_mg is None:
            # `?` — propagate and widen to the law's stated range.
            #
            # Widened from an *unknown*, not from the no-effect prior. The
            # no-effect interval is the degenerate (1.0, 1.0), and the law's
            # bound (1.5, 10.0) does not contain it — correctly, because
            # ascorbate is present, so "no effect" is excluded. Widening from
            # (1.0, 1.0) would trip the monotonicity check for the right
            # reason: it is not a widening, it is a different claim.
            completion = UncertaintyCompletion(state="contested").widen(
                LAW_004_ASCORBATE_FOLD_BOUNDS,
                note="ascorbate present, dose unquantified: ?ascorbate_fold widened "
                "to the law's bound rather than defaulted",
            )
            fold_point = None
            log.append(
                f"AO-004.3: ?ascorbate_fold contested over {LAW_004_ASCORBATE_FOLD_BOUNDS}"
            )
        else:
            lo_mg, hi_mg = LAW_004_DOSE_BOUNDS_MG
            if not (lo_mg <= ascorbate_dose_mg <= hi_mg):
                raise ValueError(
                    f"{LAW_ID} AO-004.3: <ascorbate_dose_mg> = {ascorbate_dose_mg} is "
                    f"outside the normative host-defined bounds {LAW_004_DOSE_BOUNDS_MG}"
                )
            fold_point = _dose_to_fold(ascorbate_dose_mg)
            completion = UncertaintyCompletion(
                state="normal",
                value=fold_point,
                bounds=LAW_004_ASCORBATE_FOLD_BOUNDS,
                note=f"fold from host-defined dose {ascorbate_dose_mg} mg",
            )
            log.append(f"AO-004.3: ascorbate fold x{fold_point:.2f}")
        if completion.value is not None and fold_point is not None:
            working *= fold_point
    else:
        log.append("AO-004.3: skipped, precondition [[concurrent]] false")

    # --- AO-004.4 Resolve against tannin (LAW-006) -----------------------
    steps.append("AO-004.4")
    if tannin_same_meal:
        working *= _TANNIN_FOLD
        lo, hi = completion.bounds or (1.0, 1.0)
        completion = UncertaintyCompletion(
            state=completion.state,
            value=completion.value,
            bounds=(lo * _TANNIN_FOLD, hi * _TANNIN_FOLD),
            note=(completion.note + "; tannin narrowing applied multiplicatively").strip("; "),
        )
        log.append(
            f"AO-004.4: tannin x{_TANNIN_FOLD} applied multiplicatively "
            "('can overcome' is arithmetic, not precedence)"
        )
    else:
        log.append("AO-004.4: no tannin in the occasion")

    # --- AO-004.5 Emit ----------------------------------------------------
    steps.append("AO-004.5")
    flux: Flux | None = None
    if working > 0 and dt_seconds > 0:
        flux = Flux(
            substance="nonhaem_Fe",
            source="small_intestine",
            sink="portal",
            rate=working / (dt_seconds / 3600.0),
            substance_unit="rel",
            time_unit="per_h",
            clock=Clock.MEAL,
            law_ids=(LAW_ID, "LAW-006") if tannin_same_meal else (LAW_ID,),
            prior=0.9,
            note=f"AO-004.5 emit; completion state {completion.state}",
        )
    log.append(f"AO-004.5: emitted {working:.4f} at state {completion.state}")

    return LawResult(
        yield_completion=completion,
        delivered_fe=working,
        flux=flux,
        steps_run=steps,
        log=log,
    )
