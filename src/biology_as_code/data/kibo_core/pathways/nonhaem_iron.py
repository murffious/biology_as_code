"""
Non-haem iron delivery pathway — flagship graph for LAW-004 family.

Spine:
  meal_payload → lumen_speciation → dmt1_apical → enterocyte → ferroportin_export → blood_transferrin

Modifiers (same-meal / host context keys):
  ascorbate_same_meal, tannin, phytate, meat_fish_factor, copper_redox, hepcidin_block
"""

from __future__ import annotations

from biology_as_code.data.kibo_core.laws.models import Modifier, PathwayNode


def build_nonhaem_iron_pathway() -> dict[str, PathwayNode]:
    nodes: dict[str, PathwayNode] = {}

    nodes["fe.meal_payload"] = PathwayNode(
        id="fe.meal_payload",
        label="Non-haem iron on the plate (label amount)",
        system="Assimilation",
        organ="meal / oral payload",
        subsystem="Payload.NonHaemIron",
        mechanism="label_input",
        cargo=("nonhaem_Fe",),
        next_pathways=("fe.lumen_speciation",),
        law_ids=("LAW-020",),  # label ≠ dose family
        priors={"human_evidence": 0.95, "magnitude_locked": 0.9},
        note="Starting yield_factor multiplies this abstract unit payload.",
    )

    nodes["fe.lumen_speciation"] = PathwayNode(
        id="fe.lumen_speciation",
        label="Lumen redox / chelation (free Fe²⁺ pool)",
        system="Assimilation",
        organ="duodenal–jejunal lumen",
        subsystem="MineralSpeciation.IronRedox",
        mechanism="ascorbate_reduces_ferric; phytate/tannin chelate",
        cargo=("Fe2+", "Fe3+"),
        next_pathways=("fe.dmt1_apical",),
        law_ids=("LAW-002", "LAW-004", "LAW-006", "LAW-041"),
        priors={"human_evidence": 0.9, "magnitude_locked": 0.65},
        inhibitors=(
            Modifier(
                id="mod.tannin",
                nutrient="tannin_polyphenol",
                relation="NARROWS_BOUND",
                law_id="LAW-006",
                # Derman: 3.8% → 2.1% ≈ ×0.55 relative to tea-free baseline in that arm;
                # use conservative meal-level narrow when tea co-present.
                magnitude=0.55,
                conditions=("same_meal_beverage",),
                prior=0.85,
                requires_context="tannin",
                note="Tea tannin narrows non-haem Fe absorption",
            ),
            Modifier(
                id="mod.phytate",
                nutrient="phytate",
                relation="NARROWS_BOUND",
                law_id="LAW-002",
                magnitude=0.6,
                conditions=("whole_grain_legume_matrix",),
                prior=0.8,
                requires_context="phytate",
                note="Phytate chelation; magnitude provisional fold",
            ),
        ),
        enhancers=(
            Modifier(
                id="mod.ascorbate",
                nutrient="ascorbate",
                relation="EXPANDS_BOUND",
                law_id="LAW-004",
                # ~2× orange juice (Rossander); up to ~10× in Derman tea-rescue conditions.
                # Default walk uses moderate 2.0; tea+C scenario can still net above tea-alone.
                magnitude=2.0,
                conditions=("same_meal", "nonhaem_only"),
                prior=0.9,
                requires_context="ascorbate_same_meal",
                note="Vitamin C same meal; can override tannin in cited conditions",
            ),
            Modifier(
                id="mod.ascorbate_strong",
                nutrient="ascorbate_high",
                relation="EXPANDS_BOUND",
                law_id="LAW-004",
                magnitude=5.0,
                conditions=("same_meal", "high_C_dose_or_tea_rescue_context"),
                prior=0.75,
                requires_context="ascorbate_strong",
                note="Optional strong arm toward 10× literature upper",
            ),
            Modifier(
                id="mod.meat_factor",
                nutrient="meat_fish_factor",
                relation="EXPANDS_BOUND",
                law_id="LAW-005",
                magnitude=2.0,
                conditions=("same_meal_animal_tissue",),
                prior=0.85,
                requires_context="meat_fish_factor",
            ),
            Modifier(
                id="mod.copper",
                nutrient="copper_cuprous",
                relation="EXPANDS_BOUND",
                law_id="LAW-041",
                magnitude=1.15,
                conditions=("copper_status_adequate",),
                prior=0.7,
                requires_context="copper_redox",
                note="Keeps Fe²⁺; magnitude soft",
            ),
        ),
    )

    nodes["fe.dmt1_apical"] = PathwayNode(
        id="fe.dmt1_apical",
        label="DMT1 apical uptake (Fe²⁺)",
        system="Assimilation",
        organ="duodenum enterocyte apical membrane",
        subsystem="NonHaemFeUptake.DMT1",
        mechanism="mech.dmt1_iron / tx.dmt1",
        cargo=("Fe2+",),
        next_pathways=("fe.enterocyte",),
        law_ids=("LAW-041", "LAW-004"),
        priors={"human_evidence": 0.92, "magnitude_locked": 0.7},
        is_gate=True,
        gate_context_key="fe2_available",
        gate_default_open=True,
        note="If context sets fe2_available=False, gate closes (severe ferric lock).",
        inhibitors=(
            Modifier(
                id="mod.mineral_competition",
                nutrient="competing_divalent_metals",
                relation="NARROWS_BOUND",
                law_id="LAW-042",
                magnitude=0.85,
                prior=0.65,
                requires_context="high_competing_minerals",
            ),
        ),
    )

    nodes["fe.enterocyte"] = PathwayNode(
        id="fe.enterocyte",
        label="Enterocyte handling / local store",
        system="Assimilation",
        organ="duodenal enterocyte",
        subsystem="Enterocyte.IronHandling",
        mechanism="cytosolic_iron_pool",
        cargo=("Fe2+",),
        next_pathways=("fe.ferroportin_export",),
        law_ids=(),
        priors={"human_evidence": 0.8, "magnitude_locked": 0.4},
        note="Under-specified in extraction corpus — room to grow",
    )

    nodes["fe.ferroportin_export"] = PathwayNode(
        id="fe.ferroportin_export",
        label="Ferroportin basolateral export",
        system="Assimilation",
        organ="duodenum basolateral",
        subsystem="IronExport.Ferroportin",
        mechanism="tx.ferroportin; hepcidin degrades",
        cargo=("Fe2+",),
        next_pathways=("fe.blood_transferrin",),
        law_ids=("LAW-014",),
        priors={"human_evidence": 0.9, "magnitude_locked": 0.6},
        # Not a hard gate: hepcidin throttles (NARROWS) rather than absolute close.
        is_gate=False,
        note="hepcidin_block context activates export throttle modifier.",
        inhibitors=(
            Modifier(
                id="mod.hepcidin",
                nutrient="hepcidin",
                relation="NARROWS_BOUND",
                law_id="LAW-014",
                magnitude=0.2,
                prior=0.85,
                requires_context="hepcidin_block",
                note="Inflammation / replete iron — export throttled",
            ),
        ),
    )

    nodes["fe.blood_transferrin"] = PathwayNode(
        id="fe.blood_transferrin",
        label="Transferrin-bound iron in plasma",
        system="Transport",
        organ="blood plasma",
        subsystem="IronTransport.Transferrin",
        mechanism="TF-bound_Fe",
        cargo=("TF-Fe",),
        next_pathways=(),
        law_ids=("LAW-011",),
        priors={"human_evidence": 0.95, "magnitude_locked": 0.7},
        note="Terminus for Absorption volume; tissue use is downstream Defense/Energy",
    )

    return nodes


# Module-level singleton for tests
NONHAEM_IRON_PATHWAY: dict[str, PathwayNode] = build_nonhaem_iron_pathway()
