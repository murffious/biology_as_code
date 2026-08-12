"""
LipemicResponse — declared, not executable.

Postprandial lipaemia is slower and messier than a glycemic response and the
protocol choices are correspondingly less settled:

- **Window.** A triglyceride excursion runs 6–8 hours, and truncating at 4
  hours systematically favours whichever meal peaks earlier. There is no
  defensible short default.
- **Analyte.** Plasma triglyceride, chylomicron-TG, apoB-48 and remnant
  cholesterol all get called "the lipemic response" and peak at different
  times.
- **Baseline.** Fasting duration before t = 0 changes the baseline enough to
  move the AUC, so a protocol has to specify the fast, not just the sample.
- **Incremental vs total.** Both are reported, and unlike the glycemic case
  neither convention dominates.

The cheese-versus-butter conformance test deliberately asserts **direction
only** for exactly this reason: the mechanism behind the divergence is
unresolved, and a protocol that fixed a window and an analyte now would encode
an answer the evidence does not support.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from biology_as_code.responses.base import ResponseNotExecutable, ResponseResult, Sample

__all__ = ["LipemicResponse"]


@dataclass(frozen=True)
class LipemicResponse:
    """Placeholder for a postprandial lipaemia protocol that has not been fixed yet."""

    protocol_id: str = "LipemicResponse/0.0-draft"
    unit: str = "mmol/L·min"

    #: Choices a version 1.0 would have to make explicit.
    open_choices: tuple[str, ...] = (
        "window_hours",
        "analyte",
        "prior_fast_hours",
        "incremental_or_total",
    )

    def compute(self, samples: Sequence[Sample]) -> ResponseResult:
        raise ResponseNotExecutable(
            "LipemicResponse is declared but not executable. Four protocol choices "
            f"are still open ({', '.join(self.open_choices)}) and fixing them now "
            "would encode an answer the evidence does not support. The cheese/butter "
            "conformance test asserts direction only for the same reason."
        )
