"""System coverage of the two UPF feeding trials.

Coded from published reports, not from re-analysis of individual data.
HOLDS = the trial measured a field that seats this system's gate.
OPEN  = the mechanism is named in the literature but was not locked by the trial.
UNEVALUABLE = system parked or trial silent.
REFUSE = walk the companion review already declined (diet→brain MNP).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from biology_as_code.systems.anatomy import BODY_SYSTEMS
from biology_as_code.systems.states import EvalState


@dataclass(frozen=True)
class TrialNote:
    system_id: str
    state: EvalState
    measured: tuple[str, ...]
    missing: tuple[str, ...]
    reason: str
    citations: tuple[str, ...]


@dataclass(frozen=True)
class TrialCoverage:
    trial_id: str
    title: str
    citations: tuple[str, ...]
    notes: tuple[TrialNote, ...]

    def to_dicts(self) -> list[dict[str, Any]]:
        return [
            {
                "trial": self.trial_id,
                "system_id": n.system_id,
                "state": n.state.value,
                "measured": list(n.measured),
                "missing": list(n.missing),
                "reason": n.reason,
            }
            for n in self.notes
        ]


def _note(system_id: str, state: EvalState, reason: str, measured=(), missing=(), cites=()) -> TrialNote:
    return TrialNote(system_id, state, tuple(measured), tuple(missing), reason, tuple(cites))


HALL_2019 = TrialCoverage(
    trial_id="hall_2019",
    title="Ultra-processed diets cause excess calorie intake and weight gain (inpatient crossover)",
    citations=("PMID:31105044", "DOI:10.1016/j.cmet.2019.05.008"),
    notes=(
        _note(
            "digestive",
            EvalState.HOLDS,
            "Eating rate measured (demo contrast used in fixture: ≈48 vs 31 kcal/min; trial text reports kcal/min and g/min but these fixture values are not verbatim extracted cells). Oro-sensory/matrix path is in scope.",
            measured=("energy_intake_kcal_d", "eating_rate_kcal_min", "eating_rate_g_min"),
        ),
        _note(
            "endocrine",
            EvalState.OPEN,
            "Appetite ratings and some fasting gut hormones were comparable across arms; meal-stimulated GLP-1/PYY explaining the +508 kcal/d was not locked.",
            measured=("appetite_ratings", "fasting_gut_hormones"),
            missing=("meal_stimulated_GLP1", "meal_stimulated_PYY"),
        ),
        _note(
            "cardiovascular",
            EvalState.OPEN,
            "Weight +0.9 kg in two weeks on the UPF arm is an energy-surplus signal. BP/ApoB walks were not the design target.",
            measured=("body_weight_kg", "energy_intake_kcal_d"),
            missing=("sbp_delta", "apob"),
        ),
        _note(
            "immune",
            EvalState.UNEVALUABLE,
            "No mucus, calprotectin, or emulsifier-resolved readout. Diets were additive-rich by construction of NOVA-4 but not assayed at L3.",
            missing=("calprotectin", "mucus_thickness", "emulsifier_dose"),
        ),
        _note(
            "nervous",
            EvalState.OPEN,
            "Faster eating is compatible with a reward/oro-sensory gate. No YFAS, fMRI, or HPF-pair coding was reported as a primary mechanism test.",
            measured=("eating_rate_kcal_min",),
            missing=("YFAS", "fMRI_reward"),
        ),
        _note(
            "integumentary",
            EvalState.UNEVALUABLE,
            "Adapter parked; trial silent.",
        ),
        _note("skeletal", EvalState.UNEVALUABLE, "Adapter parked; trial silent."),
        _note("muscular", EvalState.UNEVALUABLE, "Adapter parked; trial silent."),
        _note("respiratory", EvalState.UNEVALUABLE, "Adapter parked; trial silent."),
        _note("urinary", EvalState.UNEVALUABLE, "Adapter parked; trial silent."),
        _note("reproductive", EvalState.UNEVALUABLE, "Adapter parked; trial silent."),
    ),
)


DICKEN_2025 = TrialCoverage(
    trial_id="dicken_2025_update",
    title="UPDATE free-living UPF vs minimally processed diet trial (Nature Medicine 2025)",
    citations=("Dicken et al. 2025 Nature Medicine UPDATE trial — confirm DOI/PMID before deposit",),
    notes=(
        _note(
            "digestive",
            EvalState.OPEN,
            "Weight and intake differences in free living imply eating-rate/energy-density paths but do not measure oro-sensory rate the way Hall did.",
            measured=("body_weight", "ad_lib_intake_or_proxy"),
            missing=("eating_rate_kcal_min",),
        ),
        _note(
            "endocrine",
            EvalState.OPEN,
            "Cardiometabolic labs may be present depending on the published panel; meal-stimulated incretin still not the locked L3.",
            missing=("meal_stimulated_GLP1",),
        ),
        _note(
            "cardiovascular",
            EvalState.OPEN,
            "Weight change is the published headline (~1 kg class difference in the companion review). Hard CVD endpoints were not the  design.",
            measured=("body_weight",),
            missing=("events", "apob"),
        ),
        _note(
            "immune",
            EvalState.UNEVALUABLE,
            "No public system-resolved microbiome/mucus close in the summaries used here.",
            missing=("calprotectin", "16S_or_metagenome_primary"),
        ),
        _note(
            "nervous",
            EvalState.UNEVALUABLE,
            "Free-living adherence and palatability are not a coded HPF or reward assay.",
            missing=("YFAS", "HPF_coding"),
        ),
        _note("integumentary", EvalState.UNEVALUABLE, "Adapter parked."),
        _note("skeletal", EvalState.UNEVALUABLE, "Adapter parked."),
        _note("muscular", EvalState.UNEVALUABLE, "Adapter parked."),
        _note("respiratory", EvalState.UNEVALUABLE, "Adapter parked."),
        _note("urinary", EvalState.UNEVALUABLE, "Adapter parked."),
        _note("reproductive", EvalState.UNEVALUABLE, "Adapter parked."),
    ),
)


TRIALS = {HALL_2019.trial_id: HALL_2019, DICKEN_2025.trial_id: DICKEN_2025}


def list_trials() -> tuple[str, ...]:
    return tuple(TRIALS)


def trial_coverage(trial_id: str | None = None) -> tuple[TrialCoverage, ...]:
    if trial_id is None:
        return tuple(TRIALS.values())
    if trial_id not in TRIALS:
        raise KeyError(trial_id)
    return (TRIALS[trial_id],)


def assert_eleven_rows(trial: TrialCoverage) -> None:
    ids = {n.system_id for n in trial.notes}
    expected = {s.id for s in BODY_SYSTEMS}
    if ids != expected:
        raise AssertionError(f"{trial.trial_id} missing {expected - ids}")
