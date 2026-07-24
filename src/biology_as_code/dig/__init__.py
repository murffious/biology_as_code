"""GI digestion / absorption stack (capacity routing, enzymes, minerals, fiber).

The declarative machine registry (``biology_as_code.machines``) is the single
source of truth for the digestion *stage sequence*; ``run_digestion`` walks it
end-to-end, while the numeric models below compute gram-level absorption.
"""

from biology_as_code.dig.digestion_capacity_routing import build_absorption_plan
from biology_as_code.dig.digestion_flow_simulator import Bolus, DigestiveFlowSimulator

# SSOT bridge: digestion structure/flow comes from the machine registry.
from biology_as_code.machines.digestion import digestion_stage_ids, run_digestion

__all__ = [
    "Bolus",
    "DigestiveFlowSimulator",
    "build_absorption_plan",
    "digestion_stage_ids",
    "run_digestion",
]
