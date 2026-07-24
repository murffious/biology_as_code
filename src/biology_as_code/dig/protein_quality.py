
"""
protein_quality.py
Protein quality scoring based on DIAAS / PDCAAS concepts
and limiting amino acid principles from nutrition textbooks.
"""

from dataclasses import dataclass

# Reference amino acid pattern (mg/g protein) – simplified adult pattern
# Based on FAO/WHO reference patterns used in DIAAS
REFERENCE_AA = {
    "histidine": 16,
    "isoleucine": 30,
    "leucine": 61,
    "lysine": 48,
    "saa": 23,          # sulfur amino acids (Met + Cys)
    "aaa": 41,          # aromatic (Phe + Tyr)
    "threonine": 25,
    "tryptophan": 6.6,
    "valine": 40
}

@dataclass
class ProteinSource:
    name: str
    protein_g_per_100g: float
    amino_acids_mg_per_g_protein: dict[str, float]  # key = aa name
    digestibility: float = 0.95                     # true ileal digestibility 0–1
    source_type: str = "mixed"                      # animal, plant, mixed

    def limiting_amino_acid(self) -> tuple:
        """Return (aa_name, score) of the most limiting indispensable AA.

        With no amino-acid data at all, returns ("unknown", 0.0) rather than
        reporting a spurious limiting AA derived from missing values.
        """
        if not self.amino_acids_mg_per_g_protein:
            return "unknown", 0.0
        scores = {}
        for aa, ref in REFERENCE_AA.items():
            content = self.amino_acids_mg_per_g_protein.get(aa, 0)
            scores[aa] = content / ref if ref > 0 else 0
        limiting = min(scores, key=scores.get)
        return limiting, scores[limiting]

    def pdcaas(self) -> float:
        """Protein Digestibility Corrected Amino Acid Score (capped at 1.0)."""
        _, score = self.limiting_amino_acid()
        return min(1.0, score * self.digestibility)

    def diaas(self) -> float:
        """Digestible Indispensable Amino Acid Score (can be >1.0)."""
        _, score = self.limiting_amino_acid()
        return score * self.digestibility

    def quality_category(self) -> str:
        d = self.diaas()
        if d >= 1.0:
            return "Excellent"
        elif d >= 0.75:
            return "Good"
        elif d >= 0.50:
            return "Low"
        else:
            return "Poor"


# Common food protein profiles (approximate textbook values)
COMMON_PROTEINS = {
    "egg": ProteinSource(
        name="Whole Egg",
        protein_g_per_100g=12.6,
        amino_acids_mg_per_g_protein={
            "histidine": 24, "isoleucine": 54, "leucine": 86, "lysine": 70,
            "saa": 56, "aaa": 93, "threonine": 47, "tryptophan": 16, "valine": 66
        },
        digestibility=0.97,
        source_type="animal"
    ),
    "whey": ProteinSource(
        name="Whey Protein",
        protein_g_per_100g=80,
        amino_acids_mg_per_g_protein={
            "histidine": 18, "isoleucine": 60, "leucine": 110, "lysine": 95,
            "saa": 45, "aaa": 65, "threonine": 65, "tryptophan": 18, "valine": 55
        },
        digestibility=0.99,
        source_type="animal"
    ),
    "casein": ProteinSource(
        name="Casein",
        protein_g_per_100g=80,
        amino_acids_mg_per_g_protein={
            "histidine": 28, "isoleucine": 52, "leucine": 92, "lysine": 78,
            "saa": 33, "aaa": 105, "threonine": 42, "tryptophan": 12, "valine": 65
        },
        digestibility=0.97,
        source_type="animal"
    ),
    "soy": ProteinSource(
        name="Soy Protein Isolate",
        protein_g_per_100g=90,
        amino_acids_mg_per_g_protein={
            "histidine": 26, "isoleucine": 49, "leucine": 82, "lysine": 63,
            "saa": 26, "aaa": 90, "threonine": 38, "tryptophan": 13, "valine": 50
        },
        digestibility=0.95,
        source_type="plant"
    ),
    "pea": ProteinSource(
        name="Pea Protein",
        protein_g_per_100g=80,
        amino_acids_mg_per_g_protein={
            "histidine": 25, "isoleucine": 45, "leucine": 84, "lysine": 72,
            "saa": 20, "aaa": 88, "threonine": 36, "tryptophan": 9, "valine": 50
        },
        digestibility=0.89,
        source_type="plant"
    ),
    "wheat": ProteinSource(
        name="Wheat Gluten",
        protein_g_per_100g=75,
        amino_acids_mg_per_g_protein={
            "histidine": 22, "isoleucine": 38, "leucine": 68, "lysine": 18,
            "saa": 35, "aaa": 80, "threonine": 26, "tryptophan": 10, "valine": 42
        },
        digestibility=0.91,
        source_type="plant"
    ),
    "beef": ProteinSource(
        name="Beef",
        protein_g_per_100g=26,
        amino_acids_mg_per_g_protein={
            "histidine": 34, "isoleucine": 48, "leucine": 81, "lysine": 89,
            "saa": 40, "aaa": 80, "threonine": 46, "tryptophan": 12, "valine": 50
        },
        digestibility=0.95,
        source_type="animal"
    ),
    "rice": ProteinSource(
        name="Rice Protein",
        protein_g_per_100g=80,
        amino_acids_mg_per_g_protein={
            "histidine": 23, "isoleucine": 42, "leucine": 82, "lysine": 31,
            "saa": 48, "aaa": 95, "threonine": 35, "tryptophan": 12, "valine": 58
        },
        digestibility=0.88,
        source_type="plant"
    )
}


@dataclass
class ProteinQualityResult:
    pdcaas: float
    diaas: float
    limiting_amino_acid: str
    notes: str
    quality_category: str = ""
    name: str = ""


class ProteinSourceCategory:
    """Lightweight namespace for engine imports."""
    ANIMAL = "animal"
    PLANT = "plant"
    MIXED = "mixed"


def score_protein(source_name: str) -> dict:
    """Return quality metrics for a named protein source."""
    if source_name not in COMMON_PROTEINS:
        return {"error": f"Unknown source: {source_name}"}
    p = COMMON_PROTEINS[source_name]
    limiting_aa, score = p.limiting_amino_acid()
    return {
        "name": p.name,
        "source_type": p.source_type,
        "pdcaas": round(p.pdcaas(), 3),
        "diaas": round(p.diaas(), 3),
        "quality_category": p.quality_category(),
        "limiting_aa": limiting_aa,
        "limiting_score": round(score, 3),
        "digestibility": p.digestibility
    }


def calculate_protein_quality(source_name: str) -> ProteinQualityResult:
    """Engine-facing protein quality API."""
    raw = score_protein(source_name.lower())
    if "error" in raw:
        return ProteinQualityResult(
            pdcaas=0.0, diaas=0.0, limiting_amino_acid="unknown",
            notes=raw["error"], quality_category="Unknown", name=source_name,
        )
    return ProteinQualityResult(
        pdcaas=raw["pdcaas"],
        diaas=raw["diaas"],
        limiting_amino_acid=raw["limiting_aa"],
        notes=f"{raw['name']} ({raw['source_type']}) – {raw['quality_category']}",
        quality_category=raw["quality_category"],
        name=raw["name"],
    )


def complementary_score(source1: str, source2: str) -> dict:
    """Alias used by engine imports."""
    return complement_proteins(source1, source2)


def complement_proteins(source1: str, source2: str) -> dict:
    """Simple complementary protein evaluation."""
    if source1 not in COMMON_PROTEINS or source2 not in COMMON_PROTEINS:
        return {"error": "Unknown source"}
    p1 = COMMON_PROTEINS[source1]
    p2 = COMMON_PROTEINS[source2]
    
    # Average the AA profiles (equal weight for simplicity)
    combined_aa = {}
    for aa in REFERENCE_AA:
        v1 = p1.amino_acids_mg_per_g_protein.get(aa, 0)
        v2 = p2.amino_acids_mg_per_g_protein.get(aa, 0)
        combined_aa[aa] = (v1 + v2) / 2
    
    combined = ProteinSource(
        name=f"{p1.name} + {p2.name}",
        protein_g_per_100g=(p1.protein_g_per_100g + p2.protein_g_per_100g) / 2,
        amino_acids_mg_per_g_protein=combined_aa,
        digestibility=(p1.digestibility + p2.digestibility) / 2
    )
    
    return {
        "combination": combined.name,
        "diaas": round(combined.diaas(), 3),
        "pdcaas": round(combined.pdcaas(), 3),
        "quality_category": combined.quality_category(),
        "limiting_aa": combined.limiting_amino_acid()[0]
    }
