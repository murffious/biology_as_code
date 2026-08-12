"""
GlycemicResponse/1.0 — the first executable versioned response object.

The protocol
------------
Every choice below is part of the version. Change one and it is ``1.1``, not
``1.0``.

1. **Baseline.** The value of the sample at t = 0. If no sample sits exactly at
   t = 0, the protocol refuses rather than extrapolating: a baseline guessed
   from the first available sample silently changes every downstream number.

2. **Integration.** Trapezoidal rule over consecutive samples.

3. **Incremental, area below baseline discarded.** The "iAUC" convention of
   Wolever & Jenkins: for each trapezoid, area is counted only where the curve
   lies above baseline, and a segment that dips below contributes zero rather
   than a negative. Where a segment crosses the baseline, only the part of the
   triangle above baseline counts. This matters: net AUC (which subtracts the
   below-baseline area) and iAUC differ substantially in anyone with a reactive
   dip, and the two are routinely reported under the same name.

4. **Window.** 0–120 minutes by default. Samples outside the window are ignored
   and their exclusion is reported in ``warnings``, never dropped silently.

5. **Sampling adequacy.** At least four samples inside the window, including
   t = 0. Fewer is computable and not meaningful; the protocol warns rather
   than refusing, since a sparse series is still a legitimate thing to report
   as long as the sparsity travels with it.

6. **Classification bounds.** Ordinal only, on iAUC relative to a reference
   response measured under the same protocol. Absolute iAUC cut-points are not
   provided and will not be: they depend on the assay, the dose and the
   population, and any fixed number here would be wrong for most callers.

Units are carried through unchanged: iAUC comes out in *concentration units ×
minutes*, whatever concentration unit went in.

Reference: Wolever TMS, Jenkins DJA. The use of the glycemic index in
predicting the blood glucose response to mixed meals. Am J Clin Nutr.
1986;43(1):167-172. Brouns F et al. Glycaemic index methodology.
Nutr Res Rev. 2005;18(1):145-171.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from biology_as_code.responses.base import ResponseResult, Sample

__all__ = ["GlycemicResponse", "GLYCEMIC_RESPONSE_V1", "incremental_auc"]


def incremental_auc(samples: Sequence[Sample], baseline: float) -> float:
    """
    Incremental AUC by the trapezoidal rule, area below baseline discarded.

    Handles the baseline crossing explicitly. For a segment running from an
    above-baseline point to a below-baseline one (or the reverse), only the
    triangle above the baseline is counted, with its base the fraction of the
    interval spent above.
    """
    ordered = sorted(samples, key=lambda s: s.minutes)
    total = 0.0
    for left, right in zip(ordered, ordered[1:]):
        dt = right.minutes - left.minutes
        if dt <= 0:
            continue
        a = left.value - baseline
        b = right.value - baseline
        if a >= 0 and b >= 0:
            total += (a + b) / 2.0 * dt
        elif a > 0 > b:
            # Crossing down: above-baseline triangle occupies a/(a-b) of dt.
            total += a / 2.0 * (a / (a - b)) * dt
        elif a < 0 < b:
            # Crossing up: above-baseline triangle occupies b/(b-a) of dt.
            total += b / 2.0 * (b / (b - a)) * dt
        # both below baseline: contributes nothing
    return total


@dataclass(frozen=True)
class GlycemicResponse:
    """
    Versioned glycemic response protocol.

    Instantiating with non-default parameters does **not** change
    ``protocol_id`` on its own — a caller that widens the window is running a
    variant, and :meth:`compute` records the actual parameters in
    ``detail`` so the result stays self-describing.
    """

    protocol_id: str = "GlycemicResponse/1.0"
    window_minutes: float = 120.0
    unit: str = "mmol/L·min"
    min_samples: int = 4

    def compute(self, samples: Sequence[Sample]) -> ResponseResult:
        if not samples:
            raise ValueError("GlycemicResponse requires at least a baseline sample")

        ordered = sorted(samples, key=lambda s: s.minutes)
        baseline_samples = [s for s in ordered if s.minutes == 0]
        if not baseline_samples:
            raise ValueError(
                "GlycemicResponse/1.0 requires a sample at t=0 for the baseline. "
                "Extrapolating a baseline from the first available sample changes "
                "every downstream number, so the protocol refuses instead."
            )
        baseline = baseline_samples[0].value

        in_window = [s for s in ordered if s.minutes <= self.window_minutes]
        excluded = [s for s in ordered if s.minutes > self.window_minutes]

        warnings: list[str] = []
        if excluded:
            warnings.append(
                f"{len(excluded)} sample(s) beyond the {self.window_minutes:g}-minute "
                f"window were excluded (latest t={excluded[-1].minutes:g})"
            )
        if len(in_window) < self.min_samples:
            warnings.append(
                f"only {len(in_window)} sample(s) in window; protocol expects at least "
                f"{self.min_samples}. The value is computable but sparsely sampled."
            )

        value = incremental_auc(in_window, baseline)
        peak = max(in_window, key=lambda s: s.value)

        return ResponseResult(
            protocol=self.protocol_id,
            value=value,
            unit=self.unit,
            classification="",  # absolute classification needs a reference; see classify_against
            detail={
                "baseline": baseline,
                "window_minutes": self.window_minutes,
                "n_samples_in_window": len(in_window),
                "n_samples_excluded": len(excluded),
                "peak_value": peak.value,
                "peak_minutes": peak.minutes,
                "incremental_peak": peak.value - baseline,
                "integration": "trapezoidal",
                "below_baseline": "discarded (iAUC, not net AUC)",
            },
            warnings=warnings,
        )

    def classify_against(
        self, result: ResponseResult, reference: ResponseResult
    ) -> ResponseResult:
        """
        Attach an ordinal class by comparing to a reference response.

        Ordinal only — ``lower`` / ``comparable`` / ``higher`` — with a 10%
        band around the reference counted as comparable. The band exists
        because within-subject day-to-day variation in iAUC is of that order;
        calling a 3% difference a difference would be reporting noise.

        Refuses to compare across protocols. Two iAUCs computed under different
        windows are not the same quantity.
        """
        if reference.protocol != result.protocol:
            raise ValueError(
                f"cannot classify a {result.protocol} result against a "
                f"{reference.protocol} reference — different protocols are "
                "different quantities"
            )
        if reference.value <= 0:
            raise ValueError("reference iAUC must be positive to classify against")

        ratio = result.value / reference.value
        if ratio < 0.90:
            label = "lower"
        elif ratio > 1.10:
            label = "higher"
        else:
            label = "comparable"

        result.classification = label
        result.detail["reference_value"] = reference.value
        result.detail["ratio_to_reference"] = ratio
        result.detail["comparable_band"] = "±10% of reference"
        return result


#: The published instance. Use this rather than constructing one, so callers
#: share the same parameters by default.
GLYCEMIC_RESPONSE_V1 = GlycemicResponse()
