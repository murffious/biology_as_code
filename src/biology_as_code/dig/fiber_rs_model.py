"""
fiber_rs_model.py
Detailed Resistant Starch (RS1–RS5) and Fiber Property Model
Grounded in Advanced Nutrition and Human Metabolism Chapter 4 + Handbook data.
"""

from dataclasses import dataclass, field
from enum import Enum


class FiberType(Enum):
    SOLUBLE = "soluble"
    INSOLUBLE = "insoluble"
    RESISTANT_STARCH = "resistant_starch"
    MIXED = "mixed"


class RSType(Enum):
    RS1 = "RS1"  # Physically inaccessible (whole grains, seeds)
    RS2 = "RS2"  # Native granular starch (green banana, raw potato, high-amylose maize)
    RS3 = "RS3"  # Retrograded starch (cooked & cooled potatoes, rice, pasta)
    RS4 = "RS4"  # Chemically modified starches
    RS5 = "RS5"  # Amylose-lipid complexes


@dataclass
class FiberProperties:
    """Physical and physiological properties of a fiber source."""
    viscosity: float = 0.0          # 0–1 (gel-forming capacity)
    fermentability: float = 0.5     # 0–1 (how completely fermented)
    water_holding_capacity: float = 0.5
    gel_forming: float = 0.0
    solubility: float = 0.5         # 0 = fully insoluble, 1 = fully soluble
    particle_size: float = 0.5      # relative


@dataclass
class SCFAProfile:
    """Expected SCFA production ratios (must sum ~1.0)."""
    acetate: float = 0.60
    propionate: float = 0.25
    butyrate: float = 0.15

    def scale(self, total_scfa_kcal: float) -> dict[str, float]:
        return {
            "acetate": self.acetate * total_scfa_kcal,
            "propionate": self.propionate * total_scfa_kcal,
            "butyrate": self.butyrate * total_scfa_kcal
        }


@dataclass
class ColonicMedium:
    """
    Part 3 projection of a Part 2 packet: colonic import envelope.

    FLOW / open-tier only — not MICOM medium, not LAW-SPEC.
    Named so SI residual → fermentable substrate is explicit before SCFA.
    """

    fiber_g: float
    fermentable_fraction: float
    fermentable_fiber_g: float
    residual_macros_g: dict[str, float] = field(default_factory=dict)
    viscosity: float = 0.3
    rs_profile: dict[str, float] = field(default_factory=dict)
    notes: str = "FLOW open-tier colonic medium envelope; not UNITS/LAW-SPEC"

    def as_dict(self) -> dict:
        return {
            "fiber_g": round(self.fiber_g, 3),
            "fermentable_fraction": round(self.fermentable_fraction, 3),
            "fermentable_fiber_g": round(self.fermentable_fiber_g, 3),
            "residual_macros_g": {
                k: round(float(v), 3) for k, v in self.residual_macros_g.items()
            },
            "viscosity": round(self.viscosity, 3),
            "rs_profile": dict(self.rs_profile),
            "notes": self.notes,
        }


@dataclass
class ResistantStarch:
    """Detailed model for one RS subtype."""
    rs_type: RSType
    description: str
    typical_sources: list[str]
    fermentability: float           # 0–1
    butyrate_preference: float      # multiplier for butyrate production (RS2/RS3 high)
    glycemic_impact: float          # 0–1 (lower = better for blood glucose)
    properties: FiberProperties = field(default_factory=FiberProperties)
    scfa_profile: SCFAProfile = field(default_factory=SCFAProfile)


# Canonical RS definitions based on textbook Chapter 4
RS_REGISTRY: dict[RSType, ResistantStarch] = {
    RSType.RS1: ResistantStarch(
        rs_type=RSType.RS1,
        description="Physically inaccessible starch trapped within intact plant cell walls",
        typical_sources=["whole grains", "seeds", "legumes", "coarsely ground cereals"],
        fermentability=0.55,
        butyrate_preference=1.1,
        glycemic_impact=0.4,
        properties=FiberProperties(viscosity=0.2, fermentability=0.55, solubility=0.1, water_holding_capacity=0.6),
        scfa_profile=SCFAProfile(acetate=0.58, propionate=0.24, butyrate=0.18)
    ),
    RSType.RS2: ResistantStarch(
        rs_type=RSType.RS2,
        description="Native granular starch with B- or C-type crystallinity; resistant until gelatinized",
        typical_sources=["green banana", "raw potato", "high-amylose maize starch", "high-amylose wheat"],
        fermentability=0.85,
        butyrate_preference=1.45,   # strong butyrate producer
        glycemic_impact=0.25,
        properties=FiberProperties(viscosity=0.3, fermentability=0.85, solubility=0.15, water_holding_capacity=0.5),
        scfa_profile=SCFAProfile(acetate=0.50, propionate=0.22, butyrate=0.28)
    ),
    RSType.RS3: ResistantStarch(
        rs_type=RSType.RS3,
        description="Retrograded starch formed after gelatinization and cooling (amylose re-crystallization)",
        typical_sources=["cooked & cooled potato", "cooled rice", "cooled pasta", "stale bread", "cornflakes"],
        fermentability=0.80,
        butyrate_preference=1.40,
        glycemic_impact=0.30,
        properties=FiberProperties(viscosity=0.25, fermentability=0.80, solubility=0.1, water_holding_capacity=0.55),
        scfa_profile=SCFAProfile(acetate=0.52, propionate=0.23, butyrate=0.25)
    ),
    RSType.RS4: ResistantStarch(
        rs_type=RSType.RS4,
        description="Chemically modified starches (cross-linked, esterified, etc.)",
        typical_sources=["chemically modified food starches", "some resistant maltodextrins"],
        fermentability=0.60,
        butyrate_preference=1.15,
        glycemic_impact=0.35,
        properties=FiberProperties(viscosity=0.4, fermentability=0.60, solubility=0.3, water_holding_capacity=0.7),
        scfa_profile=SCFAProfile(acetate=0.55, propionate=0.25, butyrate=0.20)
    ),
    RSType.RS5: ResistantStarch(
        rs_type=RSType.RS5,
        description="Amylose-lipid complexes; formed when amylose interacts with fatty acids or monoglycerides",
        typical_sources=["foods with amylose + lipid (some baked goods, stews)", "specialized RS5 ingredients"],
        fermentability=0.70,
        butyrate_preference=1.25,
        glycemic_impact=0.28,
        properties=FiberProperties(viscosity=0.35, fermentability=0.70, solubility=0.2, water_holding_capacity=0.6),
        scfa_profile=SCFAProfile(acetate=0.53, propionate=0.24, butyrate=0.23)
    ),
}


class FiberRSModel:
    """
    Main interface for fiber and resistant starch calculations.
    Used by DigestionFlowSimulator (colon stage) and MetabolicState.
    """

    def __init__(self):
        self.rs_registry = RS_REGISTRY

    def get_rs(self, rs_type: RSType) -> ResistantStarch:
        return self.rs_registry[rs_type]

    def resolve_fermentable_fraction(
        self,
        fermentable_fraction: float | None = None,
        fiber_properties: FiberProperties | None = None,
        rs_profile: dict[str, float] | None = None,
    ) -> float:
        """
        Part 2 field priority:
          explicit fermentable_fraction → FiberProperties.fermentability →
          blend from rs_profile → default 0.55
        """
        if fermentable_fraction is not None:
            return max(0.0, min(1.0, float(fermentable_fraction)))
        if fiber_properties is not None and fiber_properties.fermentability is not None:
            return max(0.0, min(1.0, float(fiber_properties.fermentability)))
        if rs_profile:
            total = sum(float(v) for v in rs_profile.values()) or 1.0
            acc = 0.0
            for k, v in rs_profile.items():
                ku = k.upper() if str(k).lower().startswith("rs") else str(k)
                w = float(v) / total
                if ku in ("RS1", "RS2", "RS3", "RS4", "RS5"):
                    acc += self.rs_registry[RSType[ku]].fermentability * w
                else:
                    acc += 0.55 * w
            return max(0.0, min(1.0, acc))
        return 0.55

    def project_colonic_medium(
        self,
        total_fiber_g: float,
        *,
        fermentable_fraction: float | None = None,
        fiber_properties: FiberProperties | None = None,
        rs_profile: dict[str, float] | None = None,
        residual_macros_g: dict[str, float] | None = None,
        viscosity: float | None = None,
    ) -> ColonicMedium:
        """
        Explicit SI residual → colon substrate (colonic import envelope).

        Fiber is mostly not absorbed in SI; residual macros come from transit
        leftover after ileum. Fermentable mass is what SCFA arithmetic should use.
        """
        rs_profile = dict(rs_profile or {"rs2": 0.3, "rs3": 0.2})
        f_frac = self.resolve_fermentable_fraction(
            fermentable_fraction, fiber_properties, rs_profile
        )
        if viscosity is None:
            viscosity = (
                fiber_properties.viscosity if fiber_properties is not None else 0.3
            )
        fiber_g = max(0.0, float(total_fiber_g))
        return ColonicMedium(
            fiber_g=fiber_g,
            fermentable_fraction=f_frac,
            fermentable_fiber_g=fiber_g * f_frac,
            residual_macros_g=dict(residual_macros_g or {}),
            viscosity=float(viscosity),
            rs_profile=rs_profile,
        )

    def estimate_scfa_production(self, 
                                  total_fiber_g: float,
                                  rs_breakdown: dict[str, float] | None = None,
                                  viscosity: float = 0.3) -> tuple[float, SCFAProfile, dict[str, float]]:
        """
        Estimate total SCFA energy (kcal) and profile from a fiber load.
        
        rs_breakdown example: {"RS2": 0.4, "RS3": 0.3, "other": 0.3}
        Returns: (total_scfa_kcal, blended_profile, component_kcal)
        """
        if rs_breakdown is None:
            rs_breakdown = {"RS2": 0.3, "RS3": 0.2, "other": 0.5}

        # Base fermentation yield ~1.5–2.5 kcal/g fermented fiber
        base_yield = 2.0

        total_weight = sum(rs_breakdown.values()) or 1.0
        blended = SCFAProfile(acetate=0.0, propionate=0.0, butyrate=0.0)
        butyrate_boost = 1.0
        fermentability = 0.0

        for key, frac in rs_breakdown.items():
            weight = frac / total_weight
            if key in ["RS1", "RS2", "RS3", "RS4", "RS5"]:
                rs = self.rs_registry[RSType[key]]
                fermentability += rs.fermentability * weight
                butyrate_boost += (rs.butyrate_preference - 1.0) * weight
                blended.acetate += rs.scfa_profile.acetate * weight
                blended.propionate += rs.scfa_profile.propionate * weight
                blended.butyrate += rs.scfa_profile.butyrate * weight
            else:
                # Generic fiber
                fermentability += 0.55 * weight
                blended.acetate += 0.60 * weight
                blended.propionate += 0.25 * weight
                blended.butyrate += 0.15 * weight

        # Normalize profile
        total_ratio = blended.acetate + blended.propionate + blended.butyrate
        if total_ratio > 0:
            blended.acetate /= total_ratio
            blended.propionate /= total_ratio
            blended.butyrate /= total_ratio

        # Viscosity slightly reduces overall fermentation rate but can increase butyrate in some cases
        effective_fermentability = fermentability * (1.0 - viscosity * 0.15)
        total_scfa_kcal = total_fiber_g * base_yield * effective_fermentability * butyrate_boost

        component_kcal = blended.scale(total_scfa_kcal)
        return total_scfa_kcal, blended, component_kcal

    def glycemic_impact(self, rs_breakdown: dict[str, float]) -> float:
        """Return average glycemic impact (0 = very low, 1 = high)."""
        if not rs_breakdown:
            return 0.7
        total = sum(rs_breakdown.values()) or 1.0
        impact = 0.0
        for key, frac in rs_breakdown.items():
            key_u = key.upper() if key.lower().startswith("rs") else key
            if key_u in ["RS1", "RS2", "RS3", "RS4", "RS5"]:
                impact += self.rs_registry[RSType[key_u]].glycemic_impact * (frac / total)
            else:
                impact += 0.65 * (frac / total)
        return impact

    def simulate_fermentation(
        self,
        total_fiber_g: float,
        rs_profile: dict[str, float] | None = None,
        microbiome_diversity: float = 0.8,
        viscosity: float = 0.3,
    ) -> dict:
        """
        Engine-facing fermentation report.
        rs_profile keys may be rs2/RS2 style.
        """
        rs_profile = rs_profile or {"rs2": 0.3, "rs3": 0.2}
        # normalize keys to RS1..RS5
        breakdown: dict[str, float] = {}
        for k, v in rs_profile.items():
            ku = k.upper() if k.lower().startswith("rs") else k
            breakdown[ku] = breakdown.get(ku, 0.0) + float(v)
        if sum(breakdown.values()) < 0.99:
            breakdown["other"] = breakdown.get("other", 0.0) + max(0.0, 1.0 - sum(breakdown.values()))

        total_kcal, profile, components = self.estimate_scfa_production(
            total_fiber_g, breakdown, viscosity=viscosity
        )
        # Microbiome diversity modulates yield
        diversity_factor = 0.55 + 0.45 * max(0.0, min(1.0, microbiome_diversity))
        total_kcal *= diversity_factor
        components = {k: v * diversity_factor for k, v in components.items()}
        butyrate_frac = profile.butyrate

        return {
            "total_scfa_kcal": round(total_kcal, 2),
            "butyrate_fraction": round(butyrate_frac, 3),
            "scfa_profile": {
                "acetate": round(profile.acetate, 3),
                "propionate": round(profile.propionate, 3),
                "butyrate": round(profile.butyrate, 3),
            },
            "component_kcal": {k: round(v, 2) for k, v in components.items()},
            "glycemic_impact": round(self.glycemic_impact(breakdown), 3),
            "microbiome_diversity": microbiome_diversity,
            "rs_breakdown": breakdown,
            "substrate_fiber_g": round(float(total_fiber_g), 3),
            "tier": "FLOW_open",
        }

    def food_rs_content(self, food_key: str, portion_g: float = 100.0) -> dict:
        """Look up approximate RS grams and subtype mix for a food."""
        food = FOOD_RS_TABLE.get(food_key.lower())
        if not food:
            return {"error": f"unknown food: {food_key}", "known": sorted(FOOD_RS_TABLE.keys())}
        scale = portion_g / 100.0
        rs_g = food["rs_g_per_100g"] * scale
        return {
            "food": food["name"],
            "portion_g": portion_g,
            "rs_g": round(rs_g, 2),
            "dominant_types": food["types"],
            "notes": food.get("notes", ""),
            "fiber_g_est": round(food.get("fiber_g_per_100g", food["rs_g_per_100g"]) * scale, 2),
        }

    def meal_rs_from_foods(self, foods: dict[str, float]) -> dict:
        """
        Aggregate RS from {food_key: grams}.
        Returns total RS g and blended type profile for simulate_fermentation.
        """
        total_rs = 0.0
        type_weights = {f"RS{i}": 0.0 for i in range(1, 6)}
        items = []
        for key, grams in foods.items():
            info = self.food_rs_content(key, grams)
            if "error" in info:
                continue
            total_rs += info["rs_g"]
            items.append(info)
            for t in info["dominant_types"]:
                type_weights[t] += info["rs_g"] / max(len(info["dominant_types"]), 1)
        tw_sum = sum(type_weights.values()) or 1.0
        profile = {k: v / tw_sum for k, v in type_weights.items() if v > 0}
        return {"total_rs_g": round(total_rs, 2), "rs_profile": profile, "items": items}


# Food-specific RS content (approx g RS / 100 g edible portion; textbook/handbook ranges)
FOOD_RS_TABLE: dict[str, dict] = {
    "green_banana": {
        "name": "Green banana",
        "rs_g_per_100g": 8.5,
        "fiber_g_per_100g": 2.6,
        "types": ["RS2"],
        "notes": "High granular RS2; falls when fully ripe",
    },
    "raw_potato_starch": {
        "name": "Raw potato starch",
        "rs_g_per_100g": 65.0,
        "fiber_g_per_100g": 0.0,
        "types": ["RS2"],
        "notes": "Very high RS2 ingredient; heat gelatinizes → loses RS2",
    },
    "cooled_potato": {
        "name": "Cooked & cooled potato",
        "rs_g_per_100g": 3.5,
        "fiber_g_per_100g": 2.2,
        "types": ["RS3"],
        "notes": "Retrogradation forms RS3; reheating partially reduces",
    },
    "cooled_rice": {
        "name": "Cooked & cooled rice",
        "rs_g_per_100g": 2.0,
        "fiber_g_per_100g": 0.4,
        "types": ["RS3"],
        "notes": "Cooling overnight increases RS3",
    },
    "cooled_pasta": {
        "name": "Cooked & cooled pasta",
        "rs_g_per_100g": 1.8,
        "fiber_g_per_100g": 1.8,
        "types": ["RS3"],
        "notes": "Retrograded amylose",
    },
    "oats_uncooked": {
        "name": "Uncooked oats / oat bran",
        "rs_g_per_100g": 2.5,
        "fiber_g_per_100g": 10.0,
        "types": ["RS1", "RS2"],
        "notes": "Intact structures + native starch",
    },
    "legumes_cooked": {
        "name": "Cooked legumes (beans, lentils)",
        "rs_g_per_100g": 3.0,
        "fiber_g_per_100g": 7.5,
        "types": ["RS1", "RS3"],
        "notes": "Cell walls (RS1) + retrogradation on cooling",
    },
    "whole_grain_bread": {
        "name": "Whole-grain dense bread",
        "rs_g_per_100g": 1.2,
        "fiber_g_per_100g": 6.0,
        "types": ["RS1"],
        "notes": "Physically inaccessible starch in intact grains",
    },
    "high_amylose_maize": {
        "name": "High-amylose maize starch",
        "rs_g_per_100g": 40.0,
        "fiber_g_per_100g": 0.0,
        "types": ["RS2"],
        "notes": "Commercial RS2 ingredient; more heat-stable than potato starch",
    },
    "cornflakes": {
        "name": "Cornflakes",
        "rs_g_per_100g": 2.5,
        "fiber_g_per_100g": 3.0,
        "types": ["RS3"],
        "notes": "Processing + cooling can create RS3",
    },
    "green_banana_flour": {
        "name": "Green banana flour",
        "rs_g_per_100g": 35.0,
        "fiber_g_per_100g": 8.0,
        "types": ["RS2"],
        "notes": "Concentrated RS2 food ingredient",
    },
    "seeds_whole": {
        "name": "Intact seeds",
        "rs_g_per_100g": 2.0,
        "fiber_g_per_100g": 10.0,
        "types": ["RS1"],
        "notes": "RS1 – physically inaccessible until milled",
    },
}


if __name__ == "__main__":
    model = FiberRSModel()

    # High RS2/RS3 meal (e.g. cooled potato + green banana flour)
    rs_mix = {"RS2": 0.45, "RS3": 0.35, "other": 0.20}
    total_kcal, profile, components = model.estimate_scfa_production(30, rs_mix, viscosity=0.35)

    print("=== Fiber / RS SCFA Estimate ===")
    print(f"Total SCFA energy: {total_kcal:.1f} kcal")
    print(f"Profile → Acetate {profile.acetate:.2f}, Propionate {profile.propionate:.2f}, Butyrate {profile.butyrate:.2f}")
    print(f"Component kcal: {components}")
    print(f"Glycemic impact: {model.glycemic_impact(rs_mix):.2f}")
    print("\n=== simulate_fermentation ===")
    print(model.simulate_fermentation(35, {"rs2": 0.45, "rs3": 0.35}, microbiome_diversity=0.9))
    print("\n=== Food RS table sample ===")
    print(model.meal_rs_from_foods({"cooled_potato": 200, "green_banana": 100, "legumes_cooked": 150}))
