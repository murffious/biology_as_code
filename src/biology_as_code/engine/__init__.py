"""
engine — cohesive Biology-as-Code / Nutritional Engineering Python package.

Layers:
  systems      7 functional systems
  geography    kingdoms K1–K7 + organ bounds
  laws         registry, pathway graph models, walks
  pathways     iron, food quality, cascade risk
  sim          compartmental FLOW (MetabolicState + phases)
  data/        JSON laws + rules + atomic paths

Honesty: FLOW coefficients are open-tier unless magnitude_locked.
"""

from biology_as_code.engine.clocks import CLOCK_ORDER, Clock
from biology_as_code.engine.compartments import (
    Admission,
    Compartment,
    CompartmentResult,
    ExoticCompartment,
    SimpleCompartment,
    compartment_registry,
)
from biology_as_code.engine.fluxes import Flux, FluxSet
from biology_as_code.engine.geography import KINGDOMS, ORGAN_BOUNDS
from biology_as_code.engine.laws import (
    LawRegistry,
    PathwayNode,
    WalkState,
    load_system_bound_registry,
    walk_pathway,
)
from biology_as_code.engine.modifiers import (
    EVIDENCE_STATES,
    BindingRegistry,
    ModifierBinding,
)
from biology_as_code.engine.pathways import NONHAEM_IRON_PATHWAY, propagate_cascades
from biology_as_code.engine.processes import (
    Context,
    PacketState,
    Process,
    ProcessResult,
    process_from_pathway,
)
from biology_as_code.engine.signals import (
    SIGNALS,
    ExogenousSignal,
    Signal,
    get_signal,
    list_signals,
)
from biology_as_code.engine.sim import MetabolicSimulator, MetabolicState
from biology_as_code.engine.systems import SEVEN_SYSTEMS, SYSTEM_ROLES
from biology_as_code.engine.topics import build_sim_context_template, load_topics

__version__ = "0.2.0"

__all__ = [
    "CLOCK_ORDER",
    "EVIDENCE_STATES",
    "KINGDOMS",
    "SIGNALS",
    "Admission",
    "BindingRegistry",
    "Clock",
    "Compartment",
    "CompartmentResult",
    "Context",
    "ExogenousSignal",
    "ExoticCompartment",
    "Flux",
    "FluxSet",
    "ModifierBinding",
    "PacketState",
    "Process",
    "ProcessResult",
    "Signal",
    "SimpleCompartment",
    "compartment_registry",
    "get_signal",
    "list_signals",
    "process_from_pathway",
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
