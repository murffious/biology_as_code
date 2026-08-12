"""
Optional external scorer plugin surface.

Nothing in the open tree scores products. This package defines only the
*contract* an out-of-tree scorer must satisfy, plus a fail-closed loader that
returns an "unavailable" stub when no plugin is installed. Digestion,
simulation, FLOW evaluation and claim adjudication all run without it.

See ``README.md`` in this package for the plugin protocol.
"""

from .interface import ScoreRequest, ScoreResult, ScorerPlugin
from .loader import (
    external_scorer_available,
    get_external_scorer,
    run_external_score_analysis,
    unavailable_result,
)

__all__ = [
    "ScoreRequest",
    "ScoreResult",
    "ScorerPlugin",
    "external_scorer_available",
    "get_external_scorer",
    "run_external_score_analysis",
    "unavailable_result",
]
