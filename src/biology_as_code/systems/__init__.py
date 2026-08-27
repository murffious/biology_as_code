"""Body-system coverage layer (L4 filing cabinets on top of L1–L3 walks).

Constitution rules reused, not replaced:

- empty beats fake
- gate ≠ bound
- L1→L5 without L3 is malformed
- Confirmed is never emitted by a mechanism walk

Public surface is small. Adapters for integumentary, skeletal, muscular,
respiratory, urinary, reproductive are registered as PARKED so a coverage
table can still print 11 rows of honest grey.
"""

from biology_as_code.systems.anatomy import BODY_SYSTEMS, SystemSpec, parked_systems, shipped_systems
from biology_as_code.systems.coverage import (
    SystemCoverageRow,
    SystemCoverageTable,
    cover_meal,
    render_table,
)
from biology_as_code.systems.edges import Edge, EdgeLedger, default_ledger, next_studies
from biology_as_code.systems.linter import LintResult, lint_claim, lint_many
from biology_as_code.systems.states import EvalState, WalkResult
from biology_as_code.systems.trials import TrialCoverage, trial_coverage, list_trials

__all__ = [
    "BODY_SYSTEMS",
    "Edge",
    "EdgeLedger",
    "EvalState",
    "LintResult",
    "SystemCoverageRow",
    "SystemCoverageTable",
    "SystemSpec",
    "TrialCoverage",
    "WalkResult",
    "cover_meal",
    "default_ledger",
    "lint_claim",
    "lint_many",
    "list_trials",
    "next_studies",
    "parked_systems",
    "render_table",
    "shipped_systems",
    "trial_coverage",
]
