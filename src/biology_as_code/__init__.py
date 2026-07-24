"""
biology_as_code — open dig + teaching pathways (Biology as Code companion).

Public surface is intentionally small. Deep modules keep their original names
under pathways/, dig/, simulation/, data/.

Product meal score / Kibo-vars product scorer: not included (see product_score/).
"""

from biology_as_code.data.version_manifest import package_version

__version__ = package_version()

# High-level meal dig
# Dig helpers
from biology_as_code.dig import Bolus, DigestiveFlowSimulator, build_absorption_plan

# Pathways discovery (original module names preserved under .pathways)
from biology_as_code.pathways.registry import get_pathway, list_pathways

# Optional product score hook (usually unavailable)
from biology_as_code.product_score import product_score_available, run_product_score_analysis
from biology_as_code.simulation.kibo_engine import (
    FoodPayload,
    KIBOEngine,
    LifecycleStage,
    LifestyleFactors,
)
from biology_as_code.simulation.runner import MealRunResult, simulate_meal

# Scenarios
from biology_as_code.simulation.scenarios import (
    exercise,
    fed,
    overnight_fast,
    pathway_activities,
    prolonged_fast,
)

__all__ = [
    "Bolus",
    "DigestiveFlowSimulator",
    "FoodPayload",
    "KIBOEngine",
    "LifecycleStage",
    "LifestyleFactors",
    "MealRunResult",
    "__version__",
    "build_absorption_plan",
    "exercise",
    "fed",
    "get_pathway",
    "list_pathways",
    "overnight_fast",
    "pathway_activities",
    "product_score_available",
    "prolonged_fast",
    "run_product_score_analysis",
    "simulate_meal",
]
