"""
digestive_enzymes.py
Handbook-style digestive enzyme catalog: location, substrates, cofactors,
pH optima, and simplified kinetics for the GI flow simulator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GISite(Enum):
    MOUTH = "mouth"
    STOMACH = "stomach"
    DUODENUM = "duodenum"
    JEJUNUM = "jejunum"
    ILEUM = "ileum"
    COLON = "colon"
    PANCREAS = "pancreas"      # secretion origin
    LIVER_GB = "liver_gallbladder"


class SubstrateClass(Enum):
    STARCH = "starch"
    DISACCHARIDE = "disaccharide"
    PROTEIN = "protein"
    PEPTIDE = "peptide"
    TRIGLYCERIDE = "triglyceride"
    PHOSPHOLIPID = "phospholipid"
    NUCLEIC_ACID = "nucleic_acid"
    BILE = "bile_acid"
    FIBER = "fiber_microbial"


@dataclass
class EnzymeSpec:
    id: str
    name: str
    ec_hint: str
    origin: str
    active_sites: list[GISite]
    substrates: list[SubstrateClass]
    products: list[str]
    ph_optima: tuple  # (low, high)
    cofactors: list[str] = field(default_factory=list)
    activators: list[str] = field(default_factory=list)
    inhibitors: list[str] = field(default_factory=list)
    km_relative: float = 1.0       # relative substrate affinity (lower = higher affinity)
    vmax_relative: float = 1.0     # relative capacity
    requires_colipase: bool = False
    zymogen: str | None = None
    notes: str = ""


@dataclass
class EnzymeActivityResult:
    enzyme_id: str
    relative_activity: float
    limiting_factors: list[str]
    note: str = ""


# ---------------------------------------------------------------------------
# Canonical enzyme table
# ---------------------------------------------------------------------------

ENZYME_CATALOG: dict[str, EnzymeSpec] = {
    "salivary_amylase": EnzymeSpec(
        id="salivary_amylase", name="Salivary α-amylase (ptyalin)", ec_hint="EC 3.2.1.1",
        origin="salivary glands", active_sites=[GISite.MOUTH, GISite.STOMACH],
        substrates=[SubstrateClass.STARCH],
        products=["maltose", "maltotriose", "limit dextrins"],
        ph_optima=(6.5, 7.0), cofactors=["Cl-"],
        inhibitors=["low_pH"],
        vmax_relative=0.4, notes="Inactivated as gastric pH falls below ~4",
    ),
    "lingual_lipase": EnzymeSpec(
        id="lingual_lipase", name="Lingual lipase", ec_hint="EC 3.1.1.3-like",
        origin="von Ebner glands", active_sites=[GISite.MOUTH, GISite.STOMACH],
        substrates=[SubstrateClass.TRIGLYCERIDE],
        products=["DAG", "FA"],
        ph_optima=(3.5, 6.0), vmax_relative=0.15,
        notes="Important in neonates; acid-stable",
    ),
    "pepsin": EnzymeSpec(
        id="pepsin", name="Pepsin", ec_hint="EC 3.4.23.1",
        origin="chief cells (pepsinogen)", active_sites=[GISite.STOMACH],
        substrates=[SubstrateClass.PROTEIN],
        products=["peptides"],
        ph_optima=(1.5, 2.5),
        activators=["HCl", "autoactivation"],
        inhibitors=["high_pH", "PPI_effect"],
        zymogen="pepsinogen",
        vmax_relative=0.7,
        notes="Endopeptidase; denatured proteins preferred",
    ),
    "gastric_lipase": EnzymeSpec(
        id="gastric_lipase", name="Gastric lipase", ec_hint="EC 3.1.1.3",
        origin="chief cells", active_sites=[GISite.STOMACH],
        substrates=[SubstrateClass.TRIGLYCERIDE],
        products=["DAG", "FA"],
        ph_optima=(3.0, 6.0), vmax_relative=0.25,
        notes="~10–30% of TAG digestion; critical if pancreatic lipase low",
    ),
    "pancreatic_amylase": EnzymeSpec(
        id="pancreatic_amylase", name="Pancreatic α-amylase", ec_hint="EC 3.2.1.1",
        origin="pancreatic acinar cells", active_sites=[GISite.DUODENUM, GISite.JEJUNUM],
        substrates=[SubstrateClass.STARCH],
        products=["maltose", "maltotriose", "α-limit dextrins"],
        ph_optima=(6.7, 7.2), cofactors=["Cl-", "Ca2+"],
        vmax_relative=1.0,
    ),
    "trypsin": EnzymeSpec(
        id="trypsin", name="Trypsin", ec_hint="EC 3.4.21.4",
        origin="pancreas (trypsinogen)", active_sites=[GISite.DUODENUM, GISite.JEJUNUM],
        substrates=[SubstrateClass.PROTEIN, SubstrateClass.PEPTIDE],
        products=["peptides"],
        ph_optima=(7.5, 8.5),
        activators=["enteropeptidase", "trypsin"],
        zymogen="trypsinogen",
        vmax_relative=1.0,
        notes="Master activator of other pancreatic zymogens",
    ),
    "chymotrypsin": EnzymeSpec(
        id="chymotrypsin", name="Chymotrypsin", ec_hint="EC 3.4.21.1",
        origin="pancreas", active_sites=[GISite.DUODENUM, GISite.JEJUNUM],
        substrates=[SubstrateClass.PROTEIN, SubstrateClass.PEPTIDE],
        products=["peptides"],
        ph_optima=(7.5, 8.5), activators=["trypsin"], zymogen="chymotrypsinogen",
        vmax_relative=0.9,
    ),
    "elastase": EnzymeSpec(
        id="elastase", name="Pancreatic elastase", ec_hint="EC 3.4.21.36",
        origin="pancreas", active_sites=[GISite.DUODENUM, GISite.JEJUNUM],
        substrates=[SubstrateClass.PROTEIN],
        products=["peptides"],
        ph_optima=(7.5, 8.5), activators=["trypsin"], zymogen="proelastase",
        vmax_relative=0.6,
    ),
    "carboxypeptidase_a": EnzymeSpec(
        id="carboxypeptidase_a", name="Carboxypeptidase A", ec_hint="EC 3.4.17.1",
        origin="pancreas", active_sites=[GISite.DUODENUM, GISite.JEJUNUM],
        substrates=[SubstrateClass.PEPTIDE],
        products=["amino acids", "shorter peptides"],
        ph_optima=(7.0, 8.0), cofactors=["Zn2+"], activators=["trypsin"],
        zymogen="procarboxypeptidase_A", vmax_relative=0.7,
    ),
    "carboxypeptidase_b": EnzymeSpec(
        id="carboxypeptidase_b", name="Carboxypeptidase B", ec_hint="EC 3.4.17.2",
        origin="pancreas", active_sites=[GISite.DUODENUM, GISite.JEJUNUM],
        substrates=[SubstrateClass.PEPTIDE],
        products=["Lys", "Arg", "peptides"],
        ph_optima=(7.0, 8.0), cofactors=["Zn2+"], activators=["trypsin"],
        zymogen="procarboxypeptidase_B", vmax_relative=0.6,
    ),
    "pancreatic_lipase": EnzymeSpec(
        id="pancreatic_lipase", name="Pancreatic lipase", ec_hint="EC 3.1.1.3",
        origin="pancreas", active_sites=[GISite.DUODENUM, GISite.JEJUNUM],
        substrates=[SubstrateClass.TRIGLYCERIDE],
        products=["2-MAG", "FA"],
        ph_optima=(7.0, 8.5),
        cofactors=["colipase", "bile_salts", "Ca2+"],
        requires_colipase=True,
        inhibitors=["bile_salt_excess_without_colipase"],
        vmax_relative=1.0,
        notes="Colipase anchors lipase to oil-water interface in bile salt micelles",
    ),
    "colipase": EnzymeSpec(
        id="colipase", name="Colipase", ec_hint="cofactor",
        origin="pancreas (procolipase)", active_sites=[GISite.DUODENUM],
        substrates=[SubstrateClass.TRIGLYCERIDE],
        products=[],
        ph_optima=(6.0, 9.0), activators=["trypsin"],
        zymogen="procolipase", vmax_relative=1.0,
        notes="Not a catalyst; required cofactor for pancreatic lipase",
    ),
    "phospholipase_a2": EnzymeSpec(
        id="phospholipase_a2", name="Phospholipase A2", ec_hint="EC 3.1.1.4",
        origin="pancreas", active_sites=[GISite.DUODENUM],
        substrates=[SubstrateClass.PHOSPHOLIPID],
        products=["lyso-PL", "FA"],
        ph_optima=(7.0, 8.5), cofactors=["Ca2+", "bile_salts"],
        activators=["trypsin"], zymogen="prophospholipase_A2", vmax_relative=0.5,
    ),
    "cholesterol_esterase": EnzymeSpec(
        id="cholesterol_esterase", name="Carboxyl ester lipase / cholesterol esterase",
        ec_hint="EC 3.1.1.13",
        origin="pancreas", active_sites=[GISite.DUODENUM],
        substrates=[SubstrateClass.TRIGLYCERIDE],
        products=["cholesterol", "FA"],
        ph_optima=(6.5, 8.0), cofactors=["bile_salts"], vmax_relative=0.4,
    ),
    "maltase": EnzymeSpec(
        id="maltase", name="Maltase (α-glucosidase)", ec_hint="EC 3.2.1.20",
        origin="enterocyte brush border", active_sites=[GISite.JEJUNUM],
        substrates=[SubstrateClass.DISACCHARIDE],
        products=["glucose"],
        ph_optima=(5.8, 6.2), vmax_relative=0.8,
    ),
    "sucrase": EnzymeSpec(
        id="sucrase", name="Sucrase (sucrase-isomaltase complex)", ec_hint="EC 3.2.1.48",
        origin="brush border", active_sites=[GISite.JEJUNUM],
        substrates=[SubstrateClass.DISACCHARIDE],
        products=["glucose", "fructose"],
        ph_optima=(5.8, 6.2), vmax_relative=0.7,
    ),
    "lactase": EnzymeSpec(
        id="lactase", name="Lactase (lactase-phlorizin hydrolase)", ec_hint="EC 3.2.1.108",
        origin="brush border", active_sites=[GISite.JEJUNUM],
        substrates=[SubstrateClass.DISACCHARIDE],
        products=["glucose", "galactose"],
        ph_optima=(5.5, 6.0), vmax_relative=0.5,
        inhibitors=["lactase_nonpersistence"],
        notes="Declines after weaning in most populations",
    ),
    "isomaltase": EnzymeSpec(
        id="isomaltase", name="Isomaltase / α-dextrinase", ec_hint="EC 3.2.1.10",
        origin="brush border", active_sites=[GISite.JEJUNUM],
        substrates=[SubstrateClass.STARCH, SubstrateClass.DISACCHARIDE],
        products=["glucose"],
        ph_optima=(5.8, 6.2), vmax_relative=0.6,
    ),
    "aminopeptidase_n": EnzymeSpec(
        id="aminopeptidase_n", name="Aminopeptidase N", ec_hint="EC 3.4.11.2",
        origin="brush border", active_sites=[GISite.JEJUNUM, GISite.ILEUM],
        substrates=[SubstrateClass.PEPTIDE],
        products=["amino acids"],
        ph_optima=(7.0, 8.0), cofactors=["Zn2+"], vmax_relative=0.7,
    ),
    "dipeptidase": EnzymeSpec(
        id="dipeptidase", name="Cytosolic / membrane dipeptidases", ec_hint="various",
        origin="enterocyte", active_sites=[GISite.JEJUNUM],
        substrates=[SubstrateClass.PEPTIDE],
        products=["amino acids"],
        ph_optima=(7.0, 8.0), vmax_relative=0.8,
    ),
    "enteropeptidase": EnzymeSpec(
        id="enteropeptidase", name="Enteropeptidase (enterokinase)", ec_hint="EC 3.4.21.9",
        origin="duodenal brush border", active_sites=[GISite.DUODENUM],
        substrates=[SubstrateClass.PROTEIN],
        products=["trypsin (from trypsinogen)"],
        ph_optima=(6.0, 9.0), vmax_relative=0.3,
        notes="Initiates pancreatic protease cascade",
    ),
    "bile_salt_facilitated": EnzymeSpec(
        id="bile_salt_facilitated", name="Bile salt micellar solubilization",
        ec_hint="physicochemical",
        origin="liver / gallbladder", active_sites=[GISite.DUODENUM, GISite.JEJUNUM],
        substrates=[SubstrateClass.TRIGLYCERIDE, SubstrateClass.BILE],
        products=["mixed micelles"],
        ph_optima=(6.0, 8.0), cofactors=["bile_salts", "phospholipids"],
        vmax_relative=1.0,
        notes="Not an enzyme; required for efficient fat & fat-soluble vitamin absorption",
    ),
}


# Site → default luminal pH for activity calc
SITE_PH = {
    GISite.MOUTH: 6.8,
    GISite.STOMACH: 2.0,
    GISite.DUODENUM: 6.5,
    GISite.JEJUNUM: 6.8,
    GISite.ILEUM: 7.2,
    GISite.COLON: 6.5,
}


class DigestiveEnzymeSystem:
    """Query enzymes by site and estimate relative activity under conditions."""

    def __init__(self):
        self.catalog = ENZYME_CATALOG

    def enzymes_at(self, site: GISite) -> list[EnzymeSpec]:
        return [e for e in self.catalog.values() if site in e.active_sites]

    def enzymes_for_substrate(self, substrate: SubstrateClass) -> list[EnzymeSpec]:
        return [e for e in self.catalog.values() if substrate in e.substrates]

    def activity(
        self,
        enzyme_id: str,
        site: GISite,
        context: dict[str, Any] | None = None,
    ) -> EnzymeActivityResult:
        """
        context may include:
          ph, bile_salts (0–1), colipase (bool), trypsin_active (bool),
          zn_adequate (bool), cl_present (bool), lactase_persistent (bool),
          pancreatic_capacity (0–1), ppi (bool)
        """
        context = context or {}
        enz = self.catalog.get(enzyme_id)
        if not enz:
            return EnzymeActivityResult(enzyme_id, 0.0, ["unknown_enzyme"])

        limiting: list[str] = []
        ph = float(context.get("ph", SITE_PH.get(site, 7.0)))
        lo, hi = enz.ph_optima
        # Gaussian-ish pH penalty
        if ph < lo:
            ph_factor = max(0.05, 1.0 - (lo - ph) * 0.35)
        elif ph > hi:
            ph_factor = max(0.05, 1.0 - (ph - hi) * 0.35)
        else:
            ph_factor = 1.0
        if ph_factor < 0.5:
            limiting.append(f"suboptimal_pH_{ph}")

        act = enz.vmax_relative * ph_factor

        # Cofactors
        if "Cl-" in enz.cofactors and not context.get("cl_present", True):
            act *= 0.4
            limiting.append("low_chloride")
        if "Zn2+" in enz.cofactors and not context.get("zn_adequate", True):
            act *= 0.5
            limiting.append("zinc_cofactor_low")
        if "Ca2+" in enz.cofactors and not context.get("ca_present", True):
            act *= 0.7
            limiting.append("low_calcium")
        if "bile_salts" in enz.cofactors:
            bile = float(context.get("bile_salts", 0.8))
            act *= max(0.1, min(1.0, bile))
            if bile < 0.4:
                limiting.append("low_bile_salts")

        if enz.requires_colipase and not context.get("colipase", True):
            act *= 0.15
            limiting.append("missing_colipase")

        if enz.zymogen and enz.id != "pepsin":
            if not context.get("trypsin_active", True) and enz.id != "enteropeptidase":
                # zymogens need cascade
                if enz.id not in ("enteropeptidase", "salivary_amylase", "lingual_lipase",
                                  "pepsin", "gastric_lipase", "maltase", "sucrase",
                                  "lactase", "isomaltase", "aminopeptidase_n", "dipeptidase"):
                    if not context.get("trypsin_active", True):
                        act *= 0.2
                        limiting.append("zymogen_not_activated")

        if enz.id == "pepsin" and context.get("ppi", False):
            act *= 0.35
            limiting.append("ppi_raised_gastric_ph")

        if enz.id == "lactase" and not context.get("lactase_persistent", True):
            act *= 0.15
            limiting.append("lactase_nonpersistence")

        # Pancreatic reserve
        if "pancreas" in enz.origin.lower() or enz.origin.startswith("pancrea"):
            cap = float(context.get("pancreatic_capacity", 1.0))
            act *= max(0.05, min(1.0, cap))
            if cap < 0.5:
                limiting.append("exocrine_pancreatic_insufficiency")

        act = max(0.0, min(1.5, act))
        return EnzymeActivityResult(enzyme_id, round(act, 3), limiting)

    def site_digestive_capacity(
        self,
        site: GISite,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Aggregate relative capacity by substrate class at a GI site."""
        # Copy so we never mutate the caller's dict: the router reuses one
        # context across sites, and stamping pH in place would leak the
        # previous site's pH (e.g. duodenal 6.5 into the stomach's pepsin).
        context = dict(context or {})
        context["ph"] = context.get("ph", SITE_PH.get(site, 7.0))
        by_sub: dict[str, list[float]] = {}
        details = []
        for enz in self.enzymes_at(site):
            res = self.activity(enz.id, site, context)
            details.append({
                "enzyme": enz.name,
                "activity": res.relative_activity,
                "limiting": res.limiting_factors,
                "cofactors": enz.cofactors,
                "ph_optima": enz.ph_optima,
            })
            for s in enz.substrates:
                by_sub.setdefault(s.value, []).append(res.relative_activity)
        capacity = {k: round(sum(v) / len(v), 3) for k, v in by_sub.items()}
        return {"site": site.value, "capacity_by_substrate": capacity, "enzymes": details}

    def kinetics_table(self) -> list[dict[str, Any]]:
        rows = []
        for e in self.catalog.values():
            rows.append({
                "id": e.id,
                "name": e.name,
                "origin": e.origin,
                "sites": [s.value for s in e.active_sites],
                "substrates": [s.value for s in e.substrates],
                "ph_optima": e.ph_optima,
                "cofactors": e.cofactors,
                "activators": e.activators,
                "km_relative": e.km_relative,
                "vmax_relative": e.vmax_relative,
                "zymogen": e.zymogen,
            })
        return rows

    def digestion_fraction(
        self,
        substrate: SubstrateClass,
        site: GISite,
        substrate_load: float,
        context: dict[str, Any] | None = None,
    ) -> float:
        """
        Simple Michaelis-Menten-inspired fractional digestion at one site.
        fraction ≈ sum(vmax_i * S / (km_i + S)) clipped.
        """
        context = context or {}
        s = max(substrate_load, 0.01)
        total = 0.0
        for enz in self.enzymes_for_substrate(substrate):
            if site not in enz.active_sites:
                continue
            res = self.activity(enz.id, site, context)
            mm = res.relative_activity * (s / (enz.km_relative * 20 + s))
            total += mm
        return round(min(0.95, total), 3)


if __name__ == "__main__":
    sys = DigestiveEnzymeSystem()
    print("=== Duodenum capacity (healthy) ===")
    import json
    print(json.dumps(sys.site_digestive_capacity(GISite.DUODENUM), indent=2)[:1500])
    print("\n=== Duodenum EPI (pancreatic_capacity=0.25) ===")
    print(sys.site_digestive_capacity(GISite.DUODENUM, {"pancreatic_capacity": 0.25, "bile_salts": 0.3}))
    print("\nTAG digestion fraction jejunum:", sys.digestion_fraction(
        SubstrateClass.TRIGLYCERIDE, GISite.JEJUNUM, 30, {"bile_salts": 0.9, "colipase": True}
    ))
