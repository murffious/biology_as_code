"""
kibo_core — cohesive Biology-as-Code / Nutritional Engineering Python package.

Layers:
  systems      7 functional systems
  geography    kingdoms K1–K7 + organ bounds
  laws         registry, pathway graph models, walks
  pathways     iron, food quality, cascade risk
  sim          compartmental FLOW (MetabolicState + phases)
  data/        JSON laws + rules + atomic paths

Honesty: FLOW coefficients are open-tier unless magnitude_locked.
"""

from biology_as_code.data.kibo_core.geography import KINGDOMS, ORGAN_BOUNDS
from biology_as_code.data.kibo_core.laws import (
    LawRegistry,
    PathwayNode,
    WalkState,
    load_system_bound_registry,
    walk_pathway,
)
from biology_as_code.data.kibo_core.pathways import NONHAEM_IRON_PATHWAY, propagate_cascades
from biology_as_code.data.kibo_core.sim import MetabolicSimulator, MetabolicState
from biology_as_code.data.kibo_core.systems import SEVEN_SYSTEMS, SYSTEM_ROLES
from biology_as_code.data.kibo_core.topics import build_sim_context_template, load_topics

__version__ = "0.2.0"

__all__ = [
    "KINGDOMS",
    "NONHAEM_IRON_PATHWAY",
    "ORGAN_BOUNDS",
    "SEVEN_SYSTEMS",
    "SYSTEM_ROLES",
    "LawRegistry",
    "MetabolicSimulator",
    "MetabolicState",
    "PathwayNode",
    "WalkState",
    "__version__",
    "build_sim_context_template",
    "load_system_bound_registry",
    "load_topics",
    "propagate_cascades",
    "walk_pathway",
]
