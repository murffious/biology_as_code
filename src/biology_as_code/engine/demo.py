#!/usr/bin/env python3
"""One-shot demo of the cohesive engine package."""

from __future__ import annotations

import json

from biology_as_code.engine import (
    KINGDOMS,
    NONHAEM_IRON_PATHWAY,
    SEVEN_SYSTEMS,
    MetabolicSimulator,
    MetabolicState,
    load_system_bound_registry,
    propagate_cascades,
    walk_pathway,
)


def main() -> None:
    print("=== engine demo ===\n")
    print("7 systems:", ", ".join(SEVEN_SYSTEMS))
    print("Kingdoms:", ", ".join(k.id for k in KINGDOMS))

    reg = load_system_bound_registry()
    print(f"\nLaws loaded: {len(reg)}")
    print("Assimilation sample:", [L.id for L in reg.by_system("Assimilation")[:5]])

    walk = walk_pathway(
        NONHAEM_IRON_PATHWAY,
        "fe.meal_payload",
        context={"ascorbate_same_meal": True, "tannin": True},
    )
    print("\nIron walk (C + tannin): yield_factor=", round(walk.yield_factor, 3))

    sim = MetabolicSimulator()
    st = MetabolicState(
        fat_g=35,
        carb_g=40,
        protein_g=30,
        fiber_g=25,
        ascorbate_same_meal=True,
        iron_rel=1.0,
        zinc_rel=1.0,
    )
    out = sim.run(st)
    print("\nSim summary:")
    print(json.dumps(sim.summary(out), indent=2)[:800])

    cas = propagate_cascades({"nut.retinol": "low", "nut.magnesium": "low"})
    print("\nCascade systems:", cas["systems_touched"], "diagnosis=", cas["diagnosis"])
    print("\nOK")


if __name__ == "__main__":
    main()
