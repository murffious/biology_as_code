"""
biology_as_code — open dig + teaching pathways (Biology as Code companion).

Unrelated to *Code Biology* (Barbieri), which studies organic codes in living
systems; the claim here is methodological, not semiotic. See docs/naming.md.

Public surface is intentionally small. Deep modules keep their original names
under pathways/, dig/, simulation/, data/.

External product scoring: not included (see product_score/).
"""

from biology_as_code.data.version_manifest import package_version

__version__ = package_version()

# Fail-closed claim auditor (returns UNEVALUABLE rather than guessing)
from biology_as_code.audit import Claim, ClaimAudit, audit_claim

# Unified carrier — one DigestRun object (host + packet + ingestion) that the app
# and the engine both consume, validated against the same shared schemas.
from biology_as_code.carrier import (
    DigestRun,
    conditions_from_digest_run,
    load_digest_run,
    run_digest_run,
    to_machine_context,
    validate_digest_run,
)

# High-level meal dig
# Dig helpers
from biology_as_code.dig import Bolus, DigestiveFlowSimulator, build_absorption_plan

# Digestion engine — how the body handles a standardized food under conditions
# (the auditor's sibling: (packet, conditions) -> trace, same gate/bound physiology)
from biology_as_code.digestion import Conditions, DigestionTrace, digest

# Evidence / provenance (offline, no fabricated citations)
from biology_as_code.evidence import all_sources, law_evidence, pubmed_url

# LAW-SPEC law cards (inspect the constitution as data)
from biology_as_code.laws import get_law, law_card, list_laws

# Open declarative digestion machines (teaching layer)
from biology_as_code.machines import get_machine, list_machines, run_digestion, trace

# Typed food packets (repo examples/foods/ — the auditor's input side)
from biology_as_code.packets import FoodPacket, get_packet, list_packets, validate_packet

# Pathways discovery (original module names preserved under .pathways)
from biology_as_code.pathways.registry import get_pathway, list_pathways

# Optional product score hook (usually unavailable)
from biology_as_code.scoring import external_scorer_available, run_external_score_analysis
from biology_as_code.simulation.meal_engine import (
    FoodPayload,
    LifecycleStage,
    LifestyleFactors,
    MealEngine,
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

# System coverage table, claim linter, and trial-gap ledger
from biology_as_code.systems import cover_meal, lint_claim, next_studies, trial_coverage

__all__ = [
    "cover_meal",
    "lint_claim",
    "next_studies",
    "trial_coverage",
    "Bolus",
    "Claim",
    "ClaimAudit",
    "Conditions",
    "DigestRun",
    "DigestionTrace",
    "DigestiveFlowSimulator",
    "FoodPayload",
    "MealEngine",
    "LifecycleStage",
    "LifestyleFactors",
    "MealRunResult",
    "__version__",
    "all_sources",
    "audit_claim",
    "build_absorption_plan",
    "conditions_from_digest_run",
    "digest",
    "exercise",
    "load_digest_run",
    "run_digest_run",
    "to_machine_context",
    "validate_digest_run",
    "FoodPacket",
    "fed",
    "get_law",
    "get_machine",
    "get_packet",
    "get_pathway",
    "law_card",
    "law_evidence",
    "list_laws",
    "list_machines",
    "list_packets",
    "list_pathways",
    "overnight_fast",
    "pathway_activities",
    "external_scorer_available",
    "prolonged_fast",
    "pubmed_url",
    "run_digestion",
    "run_external_score_analysis",
    "simulate_meal",
    "trace",
    "validate_packet",
]
