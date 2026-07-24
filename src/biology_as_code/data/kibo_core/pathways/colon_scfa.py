"""
Colon SCFA recovery pathway — UNITS skeleton for LAW-025 / LAW-026.

Mirrors nonhaem_iron walk shape. Magnitudes are provisional
(magnitude_locked low). FLOW colonic medium is the demo layer;
this graph is the formal spine only.
"""

from __future__ import annotations

from biology_as_code.data.kibo_core.laws.models import Modifier, PathwayNode


def build_colon_scfa_pathway() -> dict[str, PathwayNode]:
    nodes: dict[str, PathwayNode] = {}

    nodes["colon.residue_arrival"] = PathwayNode(
        id="colon.residue_arrival",
        label="Ileal residue / colonic medium envelope arrives",
        system="Assimilation",
        organ="ileocecal → proximal colon",
        subsystem="Colon.ResidueArrival",
        mechanism="si_escape_of_fermentable_cargo",
        cargo=("fermentable_fiber", "rs", "residual_macros"),
        next_pathways=("colon.fermentation",),
        law_ids=("LAW-025", "LAW-017", "LAW-023"),
        priors={"human_evidence": 0.85, "magnitude_locked": 0.35},
        note="Join to engine colonic_medium; not all fiber_g is fermentable.",
        enhancers=(
            Modifier(
                id="mod.high_rs_or_soluble_fiber",
                nutrient="resistant_starch_soluble_fiber",
                relation="EXPANDS_BOUND",
                law_id="LAW-025",
                magnitude=1.15,
                prior=0.55,
                requires_context="high_fermentable_fraction",
                note="Higher fermentable fraction increases substrate available",
            ),
        ),
        inhibitors=(
            Modifier(
                id="mod.low_fermentable_packet",
                nutrient="refined_low_fiber",
                relation="NARROWS_BOUND",
                law_id="LAW-017",
                magnitude=0.7,
                prior=0.55,
                requires_context="low_fermentable_fraction",
                note="Low fermentable packet narrows colon substrate",
            ),
        ),
    )

    nodes["colon.fermentation"] = PathwayNode(
        id="colon.fermentation",
        label="Microbiome fermentation → SCFA pool",
        system="Biotransformation",
        organ="colon lumen (microbiota)",
        subsystem="Colon.MicrobiomeFermentation",
        mechanism="microbial_fermentation_to_scfa",
        cargo=("acetate", "propionate", "butyrate"),
        next_pathways=("colon.scfa_absorption",),
        law_ids=("LAW-026", "LAW-017"),
        priors={"human_evidence": 0.8, "magnitude_locked": 0.25},
        note="SCFA mix host- and substrate-dependent; no locked stoichiometry.",
        enhancers=(
            Modifier(
                id="mod.microbiome_diversity",
                nutrient="microbiome_diversity",
                relation="EXPANDS_BOUND",
                law_id="LAW-026",
                magnitude=1.2,
                prior=0.5,
                requires_context="high_microbiome_diversity",
                note="Diversity proxy; provisional",
            ),
        ),
        inhibitors=(
            Modifier(
                id="mod.dysbiosis",
                nutrient="dysbiosis",
                relation="NARROWS_BOUND",
                law_id="LAW-026",
                magnitude=0.75,
                prior=0.45,
                requires_context="dysbiosis",
                note="Low diversity / dysbiosis narrows SCFA yield",
            ),
        ),
    )

    nodes["colon.scfa_absorption"] = PathwayNode(
        id="colon.scfa_absorption",
        label="SCFA uptake (colonocyte / portal)",
        system="Transport",
        organ="colon epithelium",
        subsystem="Colon.SCFAUptake",
        mechanism="scfa_import_to_host",
        cargo=("scfa_host",),
        next_pathways=("colon.host_energy_recovery",),
        law_ids=("LAW-026",),
        priors={"human_evidence": 0.75, "magnitude_locked": 0.3},
        note="Butyrate preferential colonocyte fuel; acetate/propionate more systemic.",
    )

    nodes["colon.host_energy_recovery"] = PathwayNode(
        id="colon.host_energy_recovery",
        label="Host energy salvage + signals (not disease claims)",
        system="Energy",
        organ="colonocyte + portal / systemic",
        subsystem="Colon.HostEnergyRecovery",
        mechanism="scfa_oxidation_and_signaling",
        cargo=("atp_proxy", "anti_inflam_signal_proxy"),
        next_pathways=(),
        law_ids=("LAW-026",),
        priors={"human_evidence": 0.7, "magnitude_locked": 0.2},
        note="EXPANDS_BOUND energy recovery; do not auto-claim disease prevention.",
    )

    return nodes


COLON_SCFA_PATHWAY = build_colon_scfa_pathway()


def colon_scfa_context_from_engine(
    *,
    fermentable_fraction: float = 0.55,
    microbiome_diversity: float = 0.8,
) -> dict[str, bool]:
    """Map engine/FLOW fields into walk context flags (boolean gates only)."""
    return {
        "high_fermentable_fraction": fermentable_fraction >= 0.65,
        "low_fermentable_fraction": fermentable_fraction < 0.4,
        "high_microbiome_diversity": microbiome_diversity >= 0.75,
        "dysbiosis": microbiome_diversity < 0.45,
    }
