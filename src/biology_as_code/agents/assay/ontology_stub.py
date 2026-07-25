"""
Local entity lexicon — surface form → canonical + ontology ids.

Illustrative accessions (SCHEMA.md): resolve via OLS before publishing IRIs
as gold. Enough to normalize the golden set + common viral subjects.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EntityHit:
    surface: str
    canonical: str
    ontology_id: str | None
    kind: str  # food | compound | outcome | site
    form_default: str | None = None


# surface aliases (lower) → entity
_SUBJECTS: dict[str, EntityHit] = {}


def _reg(*aliases: str, hit: EntityHit) -> None:
    for a in aliases:
        _SUBJECTS[a.lower()] = hit


_reg(
    "spirulina",
    "arthrospira",
    "arthrospira platensis",
    hit=EntityHit(
        "spirulina",
        "Spirulina (Arthrospira platensis)",
        "NCBITaxon:1156 · FOODON:illustrative",
        "food",
        "whole food / powder (often unstated)",
    ),
)
_reg(
    "creatine",
    "creatine monohydrate",
    hit=EntityHit(
        "creatine",
        "Creatine monohydrate",
        "CHEBI:illustrative · PubChem:586",
        "compound",
        "supplement",
    ),
)
_reg(
    "flavonoids",
    "flavonoid",
    "dietary flavonoids",
    hit=EntityHit(
        "flavonoids",
        "Dietary flavonoids (polyphenol class)",
        "CHEBI:47916",
        "compound",
        None,
    ),
)
_reg(
    "apple cider vinegar",
    "acv",
    "apple-cider vinegar",
    hit=EntityHit(
        "apple cider vinegar",
        "Apple cider vinegar",
        "FOODON:illustrative",
        "food",
        "liquid vinegar",
    ),
)
_reg(
    "chlorella",
    hit=EntityHit("chlorella", "Chlorella (green algae)", "NCBITaxon:illustrative", "food"),
)
_reg(
    "vitamin d",
    "vitamin d3",
    "cholecalciferol",
    hit=EntityHit("vitamin d", "Vitamin D", "CHEBI:27300", "compound", "supplement"),
)
_reg(
    "mediterranean diet",
    "med diet",
    "mediterranean-style diet",
    hit=EntityHit(
        "mediterranean diet",
        "Mediterranean dietary pattern",
        "pattern:mediterranean",
        "food",
        "dietary pattern",
    ),
)
_reg(
    "trans fat",
    "trans fats",
    "industrial trans fat",
    hit=EntityHit(
        "trans fat",
        "Industrial trans fatty acids",
        "CHEBI:illustrative",
        "compound",
    ),
)
_reg(
    "folic acid",
    "folate",
    hit=EntityHit("folic acid", "Folic acid / folate", "CHEBI:27470", "compound"),
)
_reg(
    "ultra-processed food",
    "ultra processed food",
    "upf",
    "ultra-processed foods",
    hit=EntityHit(
        "ultra-processed food",
        "Ultra-processed food (NOVA 4 pattern)",
        "pattern:upf-nova4",
        "food",
        "industrial formulation",
    ),
)

_OUTCOMES: dict[str, EntityHit] = {
    "heavy metals": EntityHit(
        "heavy metals", "Heavy metal body burden", "CHEBI:5631", "outcome"
    ),
    "brain metals": EntityHit(
        "metals from neural tissue",
        "Heavy metals in neural tissue",
        "CHEBI:5631",
        "outcome",
    ),
    "bbb": EntityHit(
        "blood-brain barrier crossing",
        "Blood–brain barrier permeability",
        "UBERON:0002620",
        "site",
    ),
    "strength": EntityHit(
        "strength / performance",
        "Muscular strength / high-intensity performance",
        "EFO:illustrative",
        "outcome",
    ),
    "cvd": EntityHit(
        "cardiovascular disease",
        "Cardiovascular disease risk",
        "MONDO:0004995",
        "outcome",
    ),
    "belly fat": EntityHit(
        "belly fat", "Visceral / abdominal adiposity", "EFO:illustrative", "outcome"
    ),
    "weight loss": EntityHit(
        "weight loss", "Body weight reduction", "EFO:illustrative", "outcome"
    ),
    "type 2 diabetes": EntityHit(
        "type 2 diabetes", "Type 2 diabetes mellitus", "MONDO:0005148", "outcome"
    ),
    "neural tube defects": EntityHit(
        "neural tube defects", "Neural tube defects", "MONDO:0019300", "outcome"
    ),
}


def resolve_subject(text: str) -> EntityHit | None:
    t = text.lower()
    # longest alias first
    for alias in sorted(_SUBJECTS.keys(), key=len, reverse=True):
        if alias in t:
            return _SUBJECTS[alias]
    return None


def resolve_outcome(key: str) -> EntityHit:
    k = key.lower()
    if k in _OUTCOMES:
        return _OUTCOMES[k]
    return EntityHit(key, key, None, "outcome")


def list_known_subjects() -> list[str]:
    return sorted({h.surface for h in _SUBJECTS.values()})
