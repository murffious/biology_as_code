"""
How the body handles a standardized food, under conditions.

    from biology_as_code.digestion import digest, Conditions

    digest("ex.spinach_salad.zero_fat").summary
    # 'beta_carotene: transport gate CLOSED — path shut (LAW-020, LAW-045) | …'

    # same food, different conditions -> different handling
    digest("ex.lentils.with_ascorbate", Conditions(partners={"tea_tannins": True})).summary

The auditor answers *is a claim true*; :func:`digest` answers *what does the body
do*. Both walk the same gate/bound physiology. The Amazon States Language export of
the same machine lives in :mod:`biology_as_code.digestion.asl`.
"""

from __future__ import annotations

from biology_as_code.digestion.conditions import Conditions, fasted, fed
from biology_as_code.digestion.engine import (
    BoundFinding,
    DigestionTrace,
    NutrientHandling,
    digest,
    packet_to_context,
)

__all__ = [
    "BoundFinding",
    "Conditions",
    "DigestionTrace",
    "NutrientHandling",
    "digest",
    "fasted",
    "fed",
    "packet_to_context",
]
