"""Core contracts — thin adapters over existing dig/pathway code (not a second ODE engine)."""

from biology_as_code.core.base import (
    GraphPathwayLike,
    MealSimulatorLike,
    PathwaySummary,
    StructuralEdge,
    StructuralNode,
)
from biology_as_code.core.exceptions import BiologyAsCodeError, PathwayError, SimulationError

__all__ = [
    "BiologyAsCodeError",
    "GraphPathwayLike",
    "MealSimulatorLike",
    "PathwayError",
    "PathwaySummary",
    "SimulationError",
    "StructuralEdge",
    "StructuralNode",
]
