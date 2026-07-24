"""
digestion_capacity_routing.py
=============================
Drive GI segment absorption fractions from enzyme capacity + dig→abs pathway edges.

Replaces pure hard-coded fractions in DigestiveFlowSimulator when an absorption
plan is supplied. Tier: FLOW open teaching (not LAW-SPEC magnitudes).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from biology_as_code.dig.digestive_enzymes import DigestiveEnzymeSystem, GISite, SubstrateClass
from biology_as_code.pathways.digestion_absorption_pathways import (
    DigestionAbsorptionRegistry,
    get_digestion_absorption_registry,
)

# Textbook-ish relative allocation of *absorbed* mass across segments.
# Scaled by enzyme capacity so EPI / low bile / lactase flags move residual.
_CARB_SEG_WEIGHTS: list[tuple[str, float]] = [
    ("Mouth", 0.06),
    ("Duodenum", 0.28),
    ("Jejunum", 0.58),
    ("Ileum", 0.08),
]
_PROTEIN_SEG_WEIGHTS: list[tuple[str, float]] = [
    ("Stomach", 0.12),
    ("Duodenum", 0.28),
    ("Jejunum", 0.50),
    ("Ileum", 0.10),
]
_FAT_SEG_WEIGHTS: list[tuple[str, float]] = [
    ("Stomach", 0.08),
    ("Duodenum", 0.42),
    ("Jejunum", 0.33),
    ("Ileum", 0.17),
]

# Map dig-pathway edge locations → GI segment labels used by flow sim
_LOC_TO_SEG = {
    "mouth": "Mouth",
    "stomach": "Stomach",
    "duodenum": "Duodenum",
    "jejunum": "Jejunum",
    "ileum": "Ileum",
    "brush border": "Jejunum",
    "apical membrane": "Jejunum",
    "basolateral membrane": "Jejunum",
    "enterocyte": "Jejunum",
    "si lumen": "Jejunum",
    "terminal ileum": "Ileum",
    "oil-water interface of micelles": "Duodenum",
    "duodenal lumen": "Duodenum",
    "mouth → duodenum": "Duodenum",
    "duodenum / jejunum": "Duodenum",
    "stomach → duodenum": "Duodenum",
}


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _normalize_weights(
    weights: list[tuple[str, float]], total_frac: float
) -> dict[str, float]:
    """Scale segment weights so they sum to total_frac (absorption of intake)."""
    s = sum(w for _, w in weights) or 1.0
    return {seg: round(total_frac * (w / s), 4) for seg, w in weights}


@dataclass
class MacroAbsorptionPlan:
    """Per-macro, per-segment *fraction of current bolus* absorbed at that segment.

    Flow simulator applies these as sequential fractions of remaining bolus,
    so we convert cumulative targets into sequential fractions via
    ``to_sequential_fractions``.
    """

    # target cumulative absorption of *intake* by end of each segment name
    carbs_by_segment: dict[str, float] = field(default_factory=dict)
    protein_by_segment: dict[str, float] = field(default_factory=dict)
    fats_by_segment: dict[str, float] = field(default_factory=dict)
    # total SI absorbable of intake (0–1)
    total_carbs: float = 0.85
    total_protein: float = 0.85
    total_fats: float = 0.90
    edge_trace: list[dict[str, Any]] = field(default_factory=list)
    capacity_summary: dict[str, Any] = field(default_factory=dict)
    tier: str = "FLOW_open"
    notes: str = (
        "Segment fractions from enzyme capacity × dig-pathway edge weights; "
        "not UNITS/LAW-SPEC."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier,
            "totals": {
                "carbs": self.total_carbs,
                "protein": self.total_protein,
                "fats": self.total_fats,
            },
            "carbs_by_segment": dict(self.carbs_by_segment),
            "protein_by_segment": dict(self.protein_by_segment),
            "fats_by_segment": dict(self.fats_by_segment),
            "capacity_summary": self.capacity_summary,
            "edge_trace": self.edge_trace,
            "notes": self.notes,
        }

    def sequential_for(self, macro: str, segment_label: str) -> float | None:
        """
        Sequential absorption fraction of *remaining* bolus at segment.
        Built once via ``_sequential_cache`` on first use.
        """
        cache = getattr(self, "_seq", None)
        if cache is None:
            self._seq = {
                "carbs": self._to_sequential(self.carbs_by_segment),
                "protein": self._to_sequential(self.protein_by_segment),
                "fats": self._to_sequential(self.fats_by_segment),
            }
            cache = self._seq
        return cache.get(macro, {}).get(segment_label)

    @staticmethod
    def _to_sequential(by_seg_of_intake: dict[str, float]) -> dict[str, float]:
        """
        Convert absolute fractions of *intake* per segment into sequential
        fractions of *remaining* so product of (1-f) leaves residual = 1 - sum.
        Order follows standard GI order.
        """
        order = [
            "Mouth",
            "Esophagus",
            "Stomach",
            "Duodenum",
            "Jejunum",
            "Ileum",
            "Colon",
            "Rectum",
        ]
        remaining = 1.0
        out: dict[str, float] = {}
        for seg in order:
            abs_of_intake = float(by_seg_of_intake.get(seg, 0.0))
            if abs_of_intake <= 0 or remaining <= 1e-9:
                continue
            # absorb min(wanted, remaining) of original → sequential frac of current
            take = min(abs_of_intake, remaining)
            seq = take / remaining
            out[seg] = round(_clamp(seq, 0.0, 0.98), 4)
            remaining -= take
        return out


def _edge_trace(
    reg: DigestionAbsorptionRegistry, enzymes: DigestiveEnzymeSystem, ctx: dict[str, Any]
) -> list[dict[str, Any]]:
    """Annotate dig-pathway edges with enzyme activity when mechanism_id matches."""
    rows: list[dict[str, Any]] = []
    for pathway in reg.list_all():
        for edge in pathway.edges:
            mid = edge.mechanism_id or ""
            act = None
            if mid and mid in enzymes.catalog:
                # pick first active site for activity estimate
                enz = enzymes.catalog[mid]
                site = enz.active_sites[0] if enz.active_sites else GISite.DUODENUM
                act = enzymes.activity(mid, site, ctx).relative_activity
            loc = (edge.location or "").lower()
            seg_guess = None
            for key, seg in _LOC_TO_SEG.items():
                if key in loc:
                    seg_guess = seg
                    break
            rows.append(
                {
                    "pathway": pathway.name,
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "process": edge.process,
                    "location": edge.location,
                    "segment_guess": seg_guess,
                    "mechanism_id": mid or None,
                    "enzyme_activity": act,
                }
            )
    return rows


def _total_absorbable(
    enzymes: DigestiveEnzymeSystem,
    substrate: SubstrateClass,
    load_g: float,
    sites: list[GISite],
    ctx: dict[str, Any],
    *,
    floor: float,
    ceiling: float,
    quality_score: float,
) -> float:
    """Combine multi-site digestion_fraction into a single absorbable fraction of intake."""
    if load_g <= 0:
        return 0.0
    parts = [
        enzymes.digestion_fraction(substrate, site, load_g, ctx) for site in sites
    ]
    # diminishing stack: 1 - product(1 - f_i)
    residual = 1.0
    for f in parts:
        residual *= 1.0 - _clamp(f, 0.0, 0.95)
    stacked = 1.0 - residual
    # quality soft gate (matrix / processing)
    stacked *= 0.85 + 0.15 * _clamp(quality_score)
    return round(_clamp(stacked, floor, ceiling), 4)


def build_absorption_plan(
    enzymes: DigestiveEnzymeSystem | None = None,
    *,
    macros_g: dict[str, float] | None = None,
    enzyme_context: dict[str, Any] | None = None,
    quality_score: float = 0.7,
    dig_registry: DigestionAbsorptionRegistry | None = None,
) -> MacroAbsorptionPlan:
    """
    Build a meal absorption plan from enzyme capacity + dig pathway structure.

    Parameters
    ----------
    macros_g : carb/protein/fats grams (for MM load)
    enzyme_context : bile_salts, pancreatic_capacity, colipase, lactase_persistent, …
    """
    enzymes = enzymes or DigestiveEnzymeSystem()
    dig_registry = dig_registry or get_digestion_absorption_registry()
    macros_g = macros_g or {}
    ctx = dict(enzyme_context or {})
    carbs = float(macros_g.get("carbs") or macros_g.get("carb") or 0.0)
    protein = float(macros_g.get("protein") or 0.0)
    fats = float(macros_g.get("fats") or macros_g.get("fat") or 0.0)

    # Site capacities for report
    cap_duo = enzymes.site_digestive_capacity(GISite.DUODENUM, ctx)
    cap_jej = enzymes.site_digestive_capacity(GISite.JEJUNUM, ctx)
    cap_sto = enzymes.site_digestive_capacity(GISite.STOMACH, ctx)

    # Totals from enzyme MM fractions
    total_c = _total_absorbable(
        enzymes,
        SubstrateClass.STARCH,
        max(carbs, 1.0),
        [GISite.MOUTH, GISite.DUODENUM, GISite.JEJUNUM],
        ctx,
        floor=0.35 if carbs > 0 else 0.0,
        ceiling=0.94,
        quality_score=quality_score,
    )
    # blend starch + disaccharidase (brush border)
    bb = enzymes.digestion_fraction(
        SubstrateClass.DISACCHARIDE, GISite.JEJUNUM, max(carbs, 1.0), ctx
    )
    if carbs > 0:
        total_c = round(_clamp(0.65 * total_c + 0.35 * bb, 0.40, 0.95), 4)

    total_p = _total_absorbable(
        enzymes,
        SubstrateClass.PROTEIN,
        max(protein, 1.0),
        [GISite.STOMACH, GISite.DUODENUM, GISite.JEJUNUM],
        ctx,
        floor=0.40 if protein > 0 else 0.0,
        ceiling=0.94,
        quality_score=quality_score,
    )
    pep = enzymes.digestion_fraction(
        SubstrateClass.PEPTIDE, GISite.JEJUNUM, max(protein, 1.0), ctx
    )
    if protein > 0:
        total_p = round(_clamp(0.6 * total_p + 0.4 * pep, 0.45, 0.95), 4)

    total_f = _total_absorbable(
        enzymes,
        SubstrateClass.TRIGLYCERIDE,
        max(fats, 1.0),
        [GISite.STOMACH, GISite.DUODENUM, GISite.JEJUNUM],
        ctx,
        floor=0.30 if fats > 0 else 0.0,
        ceiling=0.96,
        quality_score=quality_score,
    )
    # Micelle / bile gate (L-FAT-1 style teaching)
    bile = float(ctx.get("bile_salts", 0.85 if fats > 5 else 0.5))
    if fats <= 0:
        total_f = 0.0
    else:
        # low bile or no colipase collapses fat absorption hard
        if not ctx.get("colipase", True):
            total_f = round(total_f * 0.2, 4)
        total_f = round(total_f * _clamp(0.25 + 0.75 * bile), 4)

    plan = MacroAbsorptionPlan(
        carbs_by_segment=_normalize_weights(_CARB_SEG_WEIGHTS, total_c) if carbs > 0 else {},
        protein_by_segment=_normalize_weights(_PROTEIN_SEG_WEIGHTS, total_p)
        if protein > 0
        else {},
        fats_by_segment=_normalize_weights(_FAT_SEG_WEIGHTS, total_f) if fats > 0 else {},
        total_carbs=total_c if carbs > 0 else 0.0,
        total_protein=total_p if protein > 0 else 0.0,
        total_fats=total_f if fats > 0 else 0.0,
        edge_trace=_edge_trace(dig_registry, enzymes, ctx),
        capacity_summary={
            "stomach": cap_sto.get("capacity_by_substrate", {}),
            "duodenum": cap_duo.get("capacity_by_substrate", {}),
            "jejunum": cap_jej.get("capacity_by_substrate", {}),
            "enzyme_context": {
                k: ctx[k]
                for k in (
                    "bile_salts",
                    "colipase",
                    "trypsin_active",
                    "pancreatic_capacity",
                    "zn_adequate",
                    "lactase_persistent",
                    "ppi",
                )
                if k in ctx
            },
            "loads_g": {"carbs": carbs, "protein": protein, "fats": fats},
        },
    )
    return plan


def expected_residual_macros(
    macros_g: dict[str, float], plan: MacroAbsorptionPlan
) -> dict[str, float]:
    """Macros remaining after SI given plan totals (ignores colon fiber path)."""
    return {
        "carbs": round(float(macros_g.get("carbs") or 0) * (1.0 - plan.total_carbs), 3),
        "protein": round(
            float(macros_g.get("protein") or 0) * (1.0 - plan.total_protein), 3
        ),
        "fats": round(float(macros_g.get("fats") or 0) * (1.0 - plan.total_fats), 3),
    }


if __name__ == "__main__":
    enz = DigestiveEnzymeSystem()
    healthy = build_absorption_plan(
        enz,
        macros_g={"carbs": 60, "protein": 30, "fats": 20},
        enzyme_context={
            "bile_salts": 0.9,
            "colipase": True,
            "trypsin_active": True,
            "pancreatic_capacity": 1.0,
        },
        quality_score=0.9,
    )
    epi = build_absorption_plan(
        enz,
        macros_g={"carbs": 60, "protein": 30, "fats": 20},
        enzyme_context={
            "bile_salts": 0.3,
            "colipase": True,
            "trypsin_active": True,
            "pancreatic_capacity": 0.25,
        },
        quality_score=0.9,
    )
    print("healthy totals", healthy.total_carbs, healthy.total_protein, healthy.total_fats)
    print("EPI totals   ", epi.total_carbs, epi.total_protein, epi.total_fats)
    print("healthy residual", expected_residual_macros({"carbs": 60, "protein": 30, "fats": 20}, healthy))
    print("EPI residual   ", expected_residual_macros({"carbs": 60, "protein": 30, "fats": 20}, epi))
