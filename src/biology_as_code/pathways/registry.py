"""
Pathway registry — discovers existing get_*_registry modules without renaming them.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from typing import Any


def pathway_loaders() -> list[tuple[str, Callable[[], Any]]]:
    """(module_label, registry_factory) pairs."""
    from biology_as_code.pathways.amino_acid_catabolism import (
        get_amino_acid_catabolism_registry,
    )
    from biology_as_code.pathways.beta_oxidation import get_beta_oxidation_registry
    from biology_as_code.pathways.cholesterol_pathway import get_cholesterol_pathway_registry
    from biology_as_code.pathways.digestion_absorption_pathways import (
        get_digestion_absorption_registry,
    )
    from biology_as_code.pathways.etc_oxphos import get_etc_oxphos_registry
    from biology_as_code.pathways.fatty_acid_synthesis import get_fatty_acid_synthesis_registry
    from biology_as_code.pathways.gluconeogenesis import get_gluconeogenesis_registry
    from biology_as_code.pathways.glycogen_metabolism import get_glycogen_metabolism_registry
    from biology_as_code.pathways.ketogenesis import get_ketogenesis_registry
    from biology_as_code.pathways.ketolysis import get_ketolysis_registry
    from biology_as_code.pathways.metabolic_pathways import get_metabolic_pathways_registry
    from biology_as_code.pathways.nutrient_sensing import get_nutrient_sensing_registry
    from biology_as_code.pathways.pentose_phosphate import get_pentose_phosphate_registry
    from biology_as_code.pathways.supporting_pathways import get_supporting_pathways_registry
    from biology_as_code.pathways.tca_cycle import get_tca_cycle_registry
    from biology_as_code.pathways.urea_cycle import get_urea_cycle_registry

    return [
        ("metabolic_pathways", get_metabolic_pathways_registry),
        ("tca_cycle", get_tca_cycle_registry),
        ("etc_oxphos", get_etc_oxphos_registry),
        ("beta_oxidation", get_beta_oxidation_registry),
        ("gluconeogenesis", get_gluconeogenesis_registry),
        ("urea_cycle", get_urea_cycle_registry),
        ("pentose_phosphate", get_pentose_phosphate_registry),
        ("glycogen_metabolism", get_glycogen_metabolism_registry),
        ("cholesterol_pathway", get_cholesterol_pathway_registry),
        ("fatty_acid_synthesis", get_fatty_acid_synthesis_registry),
        ("ketogenesis", get_ketogenesis_registry),
        ("ketolysis", get_ketolysis_registry),
        ("nutrient_sensing", get_nutrient_sensing_registry),
        ("digestion_absorption_pathways", get_digestion_absorption_registry),
        ("supporting_pathways", get_supporting_pathways_registry),
        ("amino_acid_catabolism", get_amino_acid_catabolism_registry),
    ]


@lru_cache(maxsize=1)
def _all_pathways() -> tuple[tuple[str, Any], ...]:
    """Build every pathway graph once (name, pathway) — cached across calls."""
    out: list[tuple[str, Any]] = []
    for _label, factory in pathway_loaders():
        reg = factory()
        paths = reg.list_all() if hasattr(reg, "list_all") else list(reg.pathways.values())
        for p in paths:
            out.append((getattr(p, "name", str(p)), p))
    return tuple(out)


def list_pathways() -> list[str]:
    """All pathway graph names registered in teaching modules."""
    return [name for name, _p in _all_pathways()]


def get_pathway(name: str) -> Any | None:
    """Fetch one pathway graph by name (case-insensitive). Returns None if not found."""
    if not name:
        return None
    key = name.strip().lower()
    for n, p in _all_pathways():
        if n == name or str(n).lower() == key:
            return p
    return None
