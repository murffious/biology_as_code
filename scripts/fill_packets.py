#!/usr/bin/env python3
"""
Fill food packets with **structural** declarations only.

    python scripts/fill_packets.py --dry-run   # show the diff
    python scripts/fill_packets.py             # write

What this script will declare
-----------------------------
Facts that follow from a food's identity and require no measurement:

* ``lipid_phase_present`` — olive oil has a lipid phase by construction; raw
  spinach eaten alone does not. This is a boolean about meal composition, not a
  quantity, so it opens or closes the fat-vehicle gate without asserting grams.
* ``matrix.integrity`` — ``intact`` for a whole nut or fruit, ``destroyed`` for a
  flour, juice or extracted oil, ``partial`` where milling leaves structure behind.
* ``tea_tannins`` — true for tea and coffee, by identity.
* ``cargo`` presence for nutrients whose occurrence in the food is not in dispute.

What this script will **not** declare
-------------------------------------
Any magnitude. Every ``cargo`` entry keeps ``label_amount: "open"``. No
``dietary_lipid_g`` value is ever written, because that would be an invented
number; the boolean carries the gate instead.

Foods whose relevant property is genuinely ambiguous are skipped and listed at the
end rather than guessed. Whole vs skim milk, plain vs nonfat yogurt, and the degree
of cell-wall survival in cooked grains are all real judgement calls, and a wrong
structural declaration is worse than a stub because it produces a confident verdict.

Provenance
----------
Every declaration carries ``derivation: "structural"`` plus a ``rationale`` string,
so a reader can tell an inference from identity apart from measured data.
``tests/test_packet_fills.py`` asserts that separation holds.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
FOODS = REPO_ROOT / "examples" / "foods"

# --- structural declarations, each with the reason it is safe to assert --------

LIPID_PHASE: dict[str, tuple[bool, str]] = {
    "olive_oil": (True, "an extracted oil is a lipid phase by construction"),
    "walnut_oil": (True, "an extracted oil is a lipid phase by construction"),
    "canola_oil_dressing": (True, "oil-based dressing; lipid phase is the vehicle"),
    "butter": (True, "butterfat is the majority component by definition of the product"),
    "avocado": (True, "intrinsic lipid is the defining macronutrient of the fruit"),
    "salmon_fillet": (True, "oily fish; intrinsic lipid present in all forms of the fillet"),
    "egg_whole": (True, "yolk lipid is present in any whole egg"),
    "cheddar_cheese": (True, "a full-fat hard cheese by product definition"),
    "walnut_whole": (True, "intrinsic nut lipid"),
    "spinach_raw": (False, "leafy green eaten alone; no lipid phase in the meal"),
    "kale_raw": (False, "leafy green eaten alone; no lipid phase in the meal"),
    "broccoli_steamed": (False, "steamed brassica alone; no fat added and none intrinsic"),
    "soda_cola": (False, "sugar-water formulation; contains no lipid"),
    "orange_juice": (False, "expressed juice; lipid absent"),
}

MATRIX: dict[str, tuple[str, str]] = {
    "walnut_whole": ("intact", "cell walls encapsulate intracellular lipid"),
    "orange_whole": ("intact", "segment and cell-wall structure present"),
    "banana": ("intact", "whole fruit; parenchyma intact"),
    "strawberry": ("intact", "whole fruit; parenchyma intact"),
    "avocado": ("intact", "whole fruit flesh; lipid still cell-bound"),
    "orange_juice": ("destroyed", "expressed juice; cell structure removed with the pulp"),
    "oat_flour_gruel": ("destroyed", "milled to flour then hydrated; no intact cell walls"),
    "white_bread_upf": ("destroyed", "refined flour; bran and germ structure removed"),
    "potato_chips_upf": ("destroyed", "sliced, fried and dehydrated; cell structure lost"),
    "protein_powder_whey": ("destroyed", "isolated protein fraction; no food matrix remains"),
    "soda_cola": ("destroyed", "formulated solution; no matrix"),
    "olive_oil": ("destroyed", "lipid extracted out of the fruit matrix"),
    "walnut_oil": ("destroyed", "lipid extracted out of the nut matrix"),
    "whole_wheat_bread": ("partial", "milled, but bran and germ fractions retained"),
    "oats_porridge_plain": ("partial", "rolled and hydrated; some cell structure survives"),
}

TANNINS: dict[str, str] = {
    "black_tea_cup": "tea polyphenols present by identity",
    "green_tea": "tea polyphenols present by identity",
    "coffee_black": "coffee polyphenols present by identity",
}

# Cargo presence only where occurrence in the food is not in dispute.
CARGO: dict[str, tuple[tuple[str, ...], str]] = {
    "spinach_raw": (("beta_carotene",), "carotenoid occurrence in spinach is undisputed"),
    "kale_raw": (("beta_carotene",), "carotenoid occurrence in kale is undisputed"),
    "broccoli_steamed": (("beta_carotene",), "carotenoid occurrence in broccoli is undisputed"),
    "olive_oil": (("lipid",), "the product is lipid"),
    "walnut_oil": (("lipid",), "the product is lipid"),
    "butter": (("lipid",), "the product is majority lipid"),
    "avocado": (("lipid",), "intrinsic lipid is the defining macronutrient"),
    "walnut_whole": (("lipid",), "intrinsic nut lipid"),
    "bean_black_cooked": (("nonhaem_iron",), "non-haem iron occurrence in pulses is undisputed"),
    "tofu_firm": (("nonhaem_iron",), "non-haem iron occurrence in soy curd is undisputed"),
}

# Deliberately not filled. Kept as a list so the reasoning is reviewable.
SKIPPED: dict[str, str] = {
    "milk_cow": "fat content depends on whether whole/semi/skim; packet does not say",
    "yogurt_plain": "plain does not imply full-fat; ambiguous",
    "rice_white_cooked": "degree of starch-granule survival after cooking is a judgement call",
    "rice_brown_cooked": "as above, plus bran layer effects; needs a sourced position",
    "quinoa_cooked": "as above",
    "potato_boiled": "cooked starch matrix state is contested; retrogradation depends on cooling",
    "chicken_breast": "no gate or bound rule in the table applies; nothing to declare",
    "beef_ground": "haem iron is out of scope of the current rule table",
    "multivitamin_tablet": "an isolated-dose form; needs a policy on supplement packets first",
    "vitamin_d_softgel": "softgel carries its own lipid vehicle; needs a supplement policy",
    "iv_ascorbate_clinical": "parenteral route bypasses the gut entirely; out of scope",
    "lemon_wedge": "ascorbate partner fields describe a meal, not a standalone item",
}


def _partner(field: str, value: Any, rationale: str) -> dict[str, Any]:
    return {
        "field": field,
        "value": value,
        "concurrency": "same_meal",
        "derivation": "structural",
        "rationale": rationale,
    }


def fill(data: dict[str, Any], stem: str) -> tuple[dict[str, Any], list[str]]:
    """Apply structural declarations to one packet. Returns the packet and a change log."""
    changes: list[str] = []
    partners: list[dict[str, Any]] = list(data.get("partners") or [])
    declared = {entry.get("field") for entry in partners}

    if stem in LIPID_PHASE and "lipid_phase_present" not in declared:
        value, rationale = LIPID_PHASE[stem]
        partners.append(_partner("lipid_phase_present", value, rationale))
        changes.append(f"lipid_phase_present={value}")

    if stem in TANNINS and "tea_tannins" not in declared:
        partners.append(_partner("tea_tannins", True, TANNINS[stem]))
        changes.append("tea_tannins=True")

    if partners:
        data["partners"] = partners

    if stem in MATRIX:
        integrity, rationale = MATRIX[stem]
        current = (data.get("matrix") or {}).get("integrity", "unknown")
        if current in (None, "unknown"):
            matrix = dict(data.get("matrix") or {})
            matrix["integrity"] = integrity
            matrix["derivation"] = "structural"
            matrix["rationale"] = rationale
            data["matrix"] = matrix
            changes.append(f"matrix.integrity={integrity}")

    if stem in CARGO:
        nutrients, rationale = CARGO[stem]
        cargo: list[dict[str, Any]] = list(data.get("cargo") or [])
        present = {entry.get("nutrient") for entry in cargo}
        for nutrient in nutrients:
            if nutrient not in present:
                # label_amount stays open: presence is structural, quantity is not.
                cargo.append(
                    {
                        "nutrient": nutrient,
                        "label_amount": "open",
                        "derivation": "structural",
                        "rationale": rationale,
                    }
                )
                changes.append(f"cargo+={nutrient}")
        if cargo:
            data["cargo"] = cargo

    if changes and data.get("status") == "stub":
        data["status"] = "filled"
        changes.append("status=filled")

    return data, changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print changes without writing")
    args = parser.parse_args()

    touched = 0
    for path in sorted(FOODS.glob("*.json")):
        if path.stem.startswith("_"):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        data, changes = fill(data, path.stem)
        if not changes:
            continue
        touched += 1
        print(f"{path.stem:26s} {', '.join(changes)}")
        if not args.dry_run:
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    print(f"\n{touched} packets {'would be' if args.dry_run else ''} updated")
    print(f"{len(SKIPPED)} deliberately skipped:")
    for stem, reason in sorted(SKIPPED.items()):
        print(f"  {stem:26s} {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
