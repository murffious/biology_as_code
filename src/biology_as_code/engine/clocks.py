"""
Clock typing — the sixth thing every piece of state needs to declare.

A host variable is not fully specified by its name, units and value. It also
has a *rate of change*, and mixing rates silently is one of the easier ways to
write a model that is wrong in a way nothing catches. Height and gastric pH are
both "host state"; sampling them on the same schedule is nonsense.

Every field in the v2 ``HostState`` carries an ``x-clock`` facet drawn from this
enum, and the resolver in ``tools/resolve_bindings.py`` checks it is present.

The six clocks, fastest last:

``FIXED``
    Does not change within the model's horizon. Sex at birth, adult height,
    a genome. Read once, cached forever.

``ADAPTATION``
    Weeks to months. Enzyme induction, microbiome community shift, iron store
    repletion, training status. Responds to sustained exposure, not to a meal.

``DIURNAL``
    ~24 h cycle. Cortisol, melatonin, core temperature, insulin sensitivity
    across the day. Phase matters more than level.

``MEAL``
    Minutes to hours, once per eating occasion. Gastric emptying, incretin
    excursion, postprandial glucose and lipaemia.

``BITE``
    Seconds. Oral processing, bolus formation, eating rate, chew count. The
    clock at which texture actually acts.

``EVENT``
    Aperiodic and externally triggered. A dose of medication, surgery, an
    illness. Has an onset, not a period.

The distinction between ``EVENT`` and the periodic clocks is why exogenous
signals are typed separately from endogenous ones — see
:mod:`biology_as_code.engine.signals`.
"""

from __future__ import annotations

from enum import Enum

__all__ = ["Clock", "CLOCK_ORDER", "typical_period_seconds", "is_faster_than"]


class Clock(str, Enum):
    """How fast a quantity changes. ``str`` so it serialises as its own name."""

    FIXED = "fixed"
    ADAPTATION = "adaptation"
    DIURNAL = "diurnal"
    MEAL = "meal"
    BITE = "bite"
    EVENT = "event"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


#: Periodic clocks slowest to fastest. ``EVENT`` is deliberately absent: it is
#: aperiodic, so it does not sit anywhere on this axis.
CLOCK_ORDER: tuple[Clock, ...] = (
    Clock.FIXED,
    Clock.ADAPTATION,
    Clock.DIURNAL,
    Clock.MEAL,
    Clock.BITE,
)

#: Order-of-magnitude period, for sanity checks and sampling defaults only.
#: These are teaching scales, not measured constants, and nothing derives a
#: reported number from them.
_TYPICAL_PERIOD_S: dict[Clock, float | None] = {
    Clock.FIXED: None,
    Clock.ADAPTATION: 30 * 24 * 3600.0,
    Clock.DIURNAL: 24 * 3600.0,
    Clock.MEAL: 4 * 3600.0,
    Clock.BITE: 3.0,
    Clock.EVENT: None,
}


def typical_period_seconds(clock: Clock) -> float | None:
    """Order-of-magnitude period, or ``None`` for ``FIXED`` and ``EVENT``."""
    return _TYPICAL_PERIOD_S[Clock(clock)]


def is_faster_than(a: Clock, b: Clock) -> bool:
    """
    Whether ``a`` runs on a faster clock than ``b``.

    Raises for ``EVENT`` on either side: an aperiodic clock cannot be ordered
    against a periodic one, and returning False would quietly assert that it
    can.
    """
    a, b = Clock(a), Clock(b)
    if Clock.EVENT in (a, b):
        raise ValueError("EVENT is aperiodic and cannot be ordered against a periodic clock")
    return CLOCK_ORDER.index(a) > CLOCK_ORDER.index(b)
