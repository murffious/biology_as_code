"""CLI: python -m biology_as_code.systems demo|lint|trials|edges"""

from __future__ import annotations

import json
import sys

from biology_as_code.systems.coverage import cover_meal, render_table
from biology_as_code.systems.edges import default_ledger
from biology_as_code.systems.linter import lint_claim
from biology_as_code.systems.trials import trial_coverage

DEMO_MEALS = {
    "hall_upf_arm": {
        "meal_id": "hall_2019_upf_pattern",
        "label": "Hall 2019 UPF arm (pattern, not one plate)",
        "nova_group": 4,
        "matrix": "disrupted",
        "eating_rate_kcal_min": 48,
        "energy_kcal": 500,
        "sodium_mg": 1800,
        "fiber_g": 8,
        "hpf_fat_sodium": True,
        "emulsifiers_declared": True,
    },
    "plain_yogurt": {
        "meal_id": "plain_yogurt_full_fat",
        "label": "Plain full-fat yogurt",
        "nova_group": 1,
        "matrix": "intact",
        "available_carb_g": 12,
        "protein_g": 9,
        "fat_g": 5,
        "gi": 36,
        "lipid_vehicle_g": 5,
        "fat_soluble_cargo": False,
    },
    "frosted_cereal": {
        "meal_id": "frosted_cereal_skim",
        "label": "Frosted cereal + skim milk",
        "nova_group": 4,
        "matrix": "disrupted",
        "available_carb_g": 45,
        "added_sugar_g": 18,
        "gi": 80,
        "sodium_mg": 220,
        "hpf_carb_sodium": True,
        "emulsifiers_declared": False,
        "lipid_vehicle_g": 1,
        "fat_soluble_cargo": False,
    },
    "spinach_zero_fat": {
        "meal_id": "spinach_zero_fat",
        "label": "Fat-free spinach salad",
        "matrix": "intact",
        "lipid_vehicle_g": 0,
        "fat_soluble_cargo": True,
        "fiber_g": 4,
        "nonhaem_iron_mg": 3.2,
    },
}


def _cmd_demo() -> int:
    for meal in DEMO_MEALS.values():
        table = cover_meal(meal)
        print(render_table(table))
        print()
    return 0


def _cmd_lint(words: list[str]) -> int:
    samples = words or [
        "Ultra-processed food causes depression.",
        "UPF raises energy intake via faster eating rate.",
        "This superfood detox boosts immunity.",
        "Emulsifiers erode mucus and can inflame the barrier in mice.",
    ]
    for text in samples:
        r = lint_claim(text)
        print(f"[{r.state.value}] malformed={r.malformed}")
        print(f"  {text}")
        print(f"  {r.reason}")
        if r.required_l3_prompt:
            print(f"  next: {r.required_l3_prompt}")
        print()
    return 0


def _cmd_trials() -> int:
    for trial in trial_coverage():
        print(f"== {trial.trial_id} ==")
        print(trial.title)
        print("cites:", ", ".join(trial.citations))
        for n in trial.notes:
            print(f"  {n.system_id:<16} {n.state.value:<14} {n.reason}")
        print()
    return 0


def _cmd_edges() -> int:
    ledger = default_ledger()
    print(json.dumps([e.to_dict() for e in ledger.edges], indent=2))
    print("\nNext studies:")
    for line in ledger.next_studies():
        print("-", line)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = args[0] if args else "demo"
    rest = args[1:]
    if cmd == "demo":
        return _cmd_demo()
    if cmd == "lint":
        return _cmd_lint([" ".join(rest)] if rest else [])
    if cmd == "trials":
        return _cmd_trials()
    if cmd == "edges":
        return _cmd_edges()
    print("usage: python -m biology_as_code.systems [demo|lint|trials|edges]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
