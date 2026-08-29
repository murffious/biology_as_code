"""
SatietyResponse — declared, not executable.

A satiety response is not a single curve. The literature reports at least three
things under the name, and they do not reduce to one another:

1. **Subjective appetite ratings** — VAS scores over time, integrated as an
   AUC much like a glycemic response. Cheap, and only weakly predictive of
   what anyone actually eats.
2. **Ad libitum intake at a subsequent meal** — the behavioural endpoint, in
   kcal. This is what the Hall and Forde designs measure, and it is the one
   that matters for the conformance suite.
3. **Satiety hormone excursions** — CCK, GLP-1, PYY, ghrelin suppression. A
   mechanism, not an outcome.

Writing a protocol before choosing which of those it computes would fix the
wrong thing behind a version number. The stub raises so a caller finds out at
the call site rather than downstream of a zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from biology_as_code.responses.base import ResponseNotExecutable, ResponseResult, Sample

__all__ = ["SatietyResponse"]


@dataclass(frozen=True)
class SatietyResponse:
    """Placeholder for a satiety protocol that has not been fixed yet."""

    protocol_id: str = "SatietyResponse/0.0-draft"
    unit: str = "kcal"

    #: The endpoints a version 1.0 would have to choose between.
    candidate_endpoints: tuple[str, ...] = (
        "vas_appetite_auc",
        "ad_libitum_intake_kcal",
        "satiety_hormone_excursion",
    )

    def compute(self, samples: Sequence[Sample]) -> ResponseResult:
        raise ResponseNotExecutable(
            "SatietyResponse is declared but not executable. Three distinct "
            f"endpoints are reported under this name ({', '.join(self.candidate_endpoints)}) "
            "and version 1.0 must pick one before a number means anything. "
            "For the ward-conformance work the endpoint is ad libitum intake in kcal; "
            "see tests/conformance/."
        )
