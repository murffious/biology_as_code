"""GI digestion / absorption stack (capacity routing, enzymes, minerals, fiber)."""

from biology_as_code.dig.digestion_capacity_routing import build_absorption_plan
from biology_as_code.dig.digestion_flow_simulator import Bolus, DigestiveFlowSimulator

__all__ = [
    "Bolus",
    "DigestiveFlowSimulator",
    "build_absorption_plan",
]
