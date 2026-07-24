"""
vitamin_absorption.py
Richer vitamin absorption kinetics + nutrient interaction system
Based on Advanced Nutrition and Human Metabolism Chapter 9 + Handbook tables.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AbsorptionResult:
    vitamin_id: str
    absorbed_fraction: float
    absorbed_amount: float
    limiting_factors: list[str] = field(default_factory=list)
    enhanced_by: list[str] = field(default_factory=list)

class VitaminAbsorptionSystem:
    """
    Models dose-dependent absorption, transporters, and nutrient interactions.
    """
    
    def __init__(self, vitamins_json_path: str | None = None):
        if vitamins_json_path is None:
            # Teaching registry lives under package fixtures/
            vitamins_json_path = (
                Path(__file__).resolve().parents[1] / "data" / "fixtures" / "vitamins.json"
            )
        with open(vitamins_json_path) as f:
            self.vitamins = {v["id"]: v for v in json.load(f)}
    
    # Common aliases from ontology / meal payloads
    ALIASES = {
        "folate": "b9",
        "folic_acid": "b9",
        "thiamin": "b1",
        "thiamine": "b1",
        "riboflavin": "b2",
        "niacin": "b3",
        "cobalamin": "b12",
        "ascorbate": "c",
        "ascorbic_acid": "c",
        "retinol": "a",
        "calciferol": "d",
        "tocopherol": "e",
        "phylloquinone": "k",
        # minerals sometimes passed into vitamin map — skip gracefully
        "iron": None,
        "zinc": None,
        "calcium": None,
    }

    def calculate_absorption(self, vitamin_id: str, intake_mg: float, 
                             context: dict[str, Any] | None = None) -> AbsorptionResult:
        """
        Calculate absorbed amount considering dose saturation, solubility, 
        and interactions present in the meal context.
        """
        if context is None:
            context = {}

        raw_id = vitamin_id.lower()
        if raw_id in self.ALIASES:
            mapped = self.ALIASES[raw_id]
            if mapped is None:
                return AbsorptionResult(vitamin_id, 0.0, 0.0, ["not_a_vitamin_use_mineral_module"])
            vitamin_id = mapped
            
        v = self.vitamins.get(vitamin_id)
        if not v:
            return AbsorptionResult(vitamin_id, 0.0, 0.0, ["unknown_vitamin"])
        
        abs_info = v.get("absorption", {})
        bio_range = abs_info.get("bioavailability_range", [0.5, 0.8])
        base_fraction = sum(bio_range) / 2
        
        limiting = []
        enhanced = []
        
        # Dose-dependent saturation (especially important for Vitamin C and some B vitamins)
        if abs_info.get("dose_dependent_saturation"):
            max_eff_dose = abs_info.get("max_efficiency_dose_mg", 200)
            if intake_mg > max_eff_dose:
                # Efficiency declines after saturation point
                excess = intake_mg - max_eff_dose
                base_fraction *= max(0.3, 1.0 - (excess / (max_eff_dose * 3)))
                limiting.append("dose_saturation")
        
        # Fat-soluble vitamins need dietary fat and bile
        if v.get("solubility") == "fat":
            dietary_fat = context.get("dietary_fat_g", 10)
            if dietary_fat < 5:
                base_fraction *= 0.4
                limiting.append("insufficient_dietary_fat")
            if not context.get("bile_present", True):
                base_fraction *= 0.2
                limiting.append("low_bile")
        
        # Specific interactions
        interactions = v.get("interactions", {})
        
        # Enhancers
        for enhancer in interactions.get("enhances", []) + interactions.get("enhanced_by", []) + interactions.get("synergizes_with", []):
            if context.get(enhancer) or context.get(f"has_{enhancer}"):
                base_fraction = min(0.98, base_fraction * 1.25)
                enhanced.append(enhancer)
        
        # Inhibitors / antagonists
        for inhibitor in interactions.get("inhibited_by", []) + interactions.get("antagonized_by", []):
            if context.get(inhibitor) or context.get(f"has_{inhibitor}"):
                base_fraction *= 0.6
                limiting.append(inhibitor)
        
        # Fiber viscosity effect (high viscosity can slow absorption of some nutrients)
        viscosity = context.get("fiber_viscosity", 0.0)
        if viscosity > 0.6 and v.get("solubility") == "water":
            base_fraction *= (1.0 - viscosity * 0.25)
            limiting.append("high_fiber_viscosity")
        
        # Special cases
        if vitamin_id == "b12":
            if not context.get("intrinsic_factor", True):
                base_fraction *= 0.05
                limiting.append("missing_intrinsic_factor")
            if not context.get("stomach_acid", True):
                base_fraction *= 0.4
                limiting.append("low_stomach_acid")
        
        if vitamin_id == "c" and context.get("non_heme_iron"):
            # Vitamin C enhances iron absorption (documented interaction)
            enhanced.append("non_heme_iron_boost")
        
        absorbed_fraction = max(0.05, min(0.98, base_fraction))
        absorbed_amount = intake_mg * absorbed_fraction
        
        return AbsorptionResult(
            vitamin_id=vitamin_id,
            absorbed_fraction=absorbed_fraction,
            absorbed_amount=absorbed_amount,
            limiting_factors=limiting,
            enhanced_by=enhanced
        )
    
    def process_meal_vitamins(self, vitamin_intakes: dict[str, float], 
                              meal_context: dict[str, Any] | None = None) -> dict[str, AbsorptionResult]:
        """Process an entire meal's vitamin content."""
        results = {}
        for vid, amount in vitamin_intakes.items():
            results[vid] = self.calculate_absorption(vid, amount, meal_context)
        return results


class VitaminAbsorptionEngine(VitaminAbsorptionSystem):
    """
    Engine-facing API expected by kibo_engine.
    Wraps dose/interaction logic into a single absorb() call.
    """

    def absorb(
        self,
        intake_mg: dict[str, float],
        food_matrix_quality: float = 0.7,
        fiber_viscosity: float = 0.3,
        current_pool: dict[str, float] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ctx = {
            "dietary_fat_g": 12,
            "bile_present": True,
            "intrinsic_factor": True,
            "stomach_acid": True,
            "fiber_viscosity": fiber_viscosity,
            "food_matrix_quality": food_matrix_quality,
        }
        if context:
            ctx.update(context)
        if intake_mg.get("c", 0) > 20:
            ctx["non_heme_iron"] = True

        results = self.process_meal_vitamins(intake_mg, ctx)
        updated = dict(current_pool or {})
        interactions = []
        absorbed = {}
        for vid, res in results.items():
            absorbed[vid] = {
                "fraction": res.absorbed_fraction,
                "amount": res.absorbed_amount,
                "limiting": res.limiting_factors,
                "enhanced": res.enhanced_by,
            }
            # adequacy nudge: absorbed dose vs rough target
            prev = updated.get(vid, 0.7)
            bump = min(0.25, res.absorbed_amount / 100.0) * food_matrix_quality
            updated[vid] = max(0.0, min(1.0, prev * 0.95 + bump + res.absorbed_fraction * 0.05))
            interactions.extend(res.limiting_factors)
            interactions.extend(res.enhanced_by)

        return {
            "absorbed": absorbed,
            "updated_adequacy": updated,
            "interactions_triggered": sorted(set(interactions)),
            "food_matrix_quality": food_matrix_quality,
        }


if __name__ == "__main__":
    system = VitaminAbsorptionEngine()
    
    # Example: high Vitamin C meal with iron and some fiber
    context = {
        "dietary_fat_g": 15,
        "bile_present": True,
        "non_heme_iron": True,
        "fiber_viscosity": 0.4,
        "intrinsic_factor": True,
        "stomach_acid": True
    }
    
    intakes = {"c": 250, "b1": 1.5, "b9": 0.4, "d": 20, "b12": 0.005}
    
    results = system.process_meal_vitamins(intakes, context)
    
    print("=== Vitamin Absorption Results ===")
    for vid, res in results.items():
        print(f"{vid.upper()}: absorbed {res.absorbed_amount:.3f} mg "
              f"({res.absorbed_fraction*100:.1f}%)")
        if res.limiting_factors:
            print(f"   Limited by: {res.limiting_factors}")
        if res.enhanced_by:
            print(f"   Enhanced by: {res.enhanced_by}")
