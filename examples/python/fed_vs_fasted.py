#!/usr/bin/env python3
"""Fed vs overnight fast — pathway regulation, nutrient sensing, and ketolysis (open FLOW).

Shows three views of the same fed→fasted switch:
  1. scalar pathway activities (the engine's regulation snapshot)
  2. the AMPK / mTORC1 / SREBP graphs *run on state* (multi-node, with cross-talk)
  3. the ketolysis graph as mermaid — the fasting fuel peripheral tissues burn
"""

from biology_as_code import fed, get_pathway, overnight_fast, pathway_activities
from biology_as_code.pathways.pathway_regulation import nutrient_sensing_snapshot
from biology_as_code.visualization.graphs import pathway_to_mermaid

if __name__ == "__main__":
    fed_state = fed()
    fast_state = overnight_fast()

    print("=== 1. Pathway activities (FLOW regulation snapshot) ===")
    print("Fed:           ", pathway_activities(fed_state))
    print("Overnight fast:", pathway_activities(fast_state))

    print("\n=== 2. Nutrient sensing (AMPK / mTORC1 / SREBP graphs, executed on state) ===")
    print("Fed:           ", nutrient_sensing_snapshot(fed_state)["regulators"])
    print("Overnight fast:", nutrient_sensing_snapshot(fast_state)["regulators"])
    print("   fasting flips the switch: AMPK ↑ → mTORC1 ↓ → SREBP-1c ↓ (lipogenesis off)")

    print("\n=== 3. Ketolysis — the fuel fasting makes (liver can't burn its own ketones) ===")
    print("Peripheral tissues (brain, heart, muscle) run this graph; the liver lacks SCOT.\n")
    print(pathway_to_mermaid(get_pathway("ketolysis")))
