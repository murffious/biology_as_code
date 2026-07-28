"""
Export must not silently drop what the registry holds.

The pathway modules each declared their own ReactionEdge, so the same concept
acquired three names (`enzyme` / `enzyme_or_complex` / `enzyme_or_process`) and
seven cofactor fields. The exporter only knew some of them, so `etc_oxphos`
rendered every edge as the placeholder "step" and the TCA pack lost FADH2, GTP
and CO2 — while every existing test stayed green, because they compare the
generator against itself rather than against its input.

These tests compare the export against the registry.

See docs/python/PATHWAY_TYPES_REFACTOR.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT / "scripts"))

from biology_as_code.pathways._types import edge_enzyme, edge_yields  # noqa: E402
from biology_as_code.pathways.registry import _all_pathways  # noqa: E402

PLACEHOLDER = "step"


def _labelled_edges():
    """(pathway_name, edge, rendered_label) for every edge in every registry graph."""
    from export_pathway_packs import _edge_label

    for name, pathway in _all_pathways():
        for edge in getattr(pathway, "edges", []) or []:
            yield name, edge, _edge_label(edge)


def test_edges_with_an_enzyme_are_not_rendered_as_placeholder():
    """If the registry knows what catalyses a step, the label must say so."""
    lost = [
        (name, f"{edge.from_node}->{edge.to_node}", edge_enzyme(edge))
        for name, edge, label in _labelled_edges()
        if edge_enzyme(edge) and label == PLACEHOLDER
    ]
    assert not lost, (
        f"{len(lost)} edges carry an enzyme/complex/process name in the registry but "
        f"export as \"{PLACEHOLDER}\". First few: {lost[:5]}"
    )


def test_cofactor_yields_survive_export():
    """Every non-zero cofactor delta must appear in the rendered label, *with its
    sign*. Checking only that the species name appears would let an inverted
    label through — which is exactly how the NADPH bug survived the first pass."""
    lost = []
    for name, edge, label in _labelled_edges():
        for species, delta in edge_yields(edge):
            if f"{species}{delta:+g}" not in label:
                lost.append((name, f"{edge.from_node}->{edge.to_node}", species, delta))
    assert not lost, (
        f"{len(lost)} cofactor yields are dropped or mis-signed on export. "
        f"First few: {lost[:5]}"
    )


# (module, from_node, to_node) -> expected signed token. Hand-checked against the
# biology, not against the current output — these are the cases where a sign flip
# would be silently wrong.
SIGNED_CASES = [
    ("glycolysis", "gap", "13bpg", "NADH+1"),        # GAPDH produces NADH
    ("glycolysis", "pyruvate", "lactate", "NADH-1"),  # LDH consumes it
    ("glycolysis", "glucose", "g6p", "ATP-1"),        # hexokinase spends
    ("glycolysis", "13bpg", "3pg", "ATP+1"),          # PGK makes
    ("tca_cycle", "succinate", "fumarate", "FADH2+1"),
    ("tca_cycle", "succinyl_coa", "succinate", "GTP+1"),
    ("beta_oxidation", None, None, "FADH2+1"),        # ACAD produces FADH2
    ("pentose_phosphate", "g6p", "6pgl", "NADPH+1"),  # G6PD PRODUCES NADPH
    ("cholesterol_biosynthesis", "hmg_coa", "mevalonate", "NADPH-2"),  # HMGCR CONSUMES
]


def test_known_cofactor_signs_are_right_way_round():
    """NADPH is produced by the pentose phosphate pathway and consumed by
    cholesterol synthesis. Both stored `nadph_cost=-N` at one point, so a single
    blanket sign rule rendered one of them backwards."""
    from export_pathway_packs import _edge_label

    graphs = dict(_all_pathways())
    for module, src, dst, expected in SIGNED_CASES:
        assert module in graphs, f"pathway {module} not registered"
        edges = graphs[module].edges
        if src is None:
            labels = [_edge_label(e) for e in edges]
            assert any(expected in lab for lab in labels), (
                f"{module}: no edge renders {expected}"
            )
            continue
        match = next(
            (e for e in edges if e.from_node == src and e.to_node == dst), None
        )
        assert match is not None, f"{module}: no edge {src}->{dst}"
        label = _edge_label(match)
        assert expected in label, f"{module} {src}->{dst}: expected {expected}, got {label!r}"


def test_reduced_carriers_are_labelled_as_produced_not_consumed():
    """The redox fields track the OXIDISED partner, so a raw `nadh_cost=-1` on a
    step that makes NADH would print "NADH-1" and read backwards. Normalisation
    must flip it."""
    from biology_as_code.pathways.metabolic_pathways import (
        get_metabolic_pathways_registry,
    )

    reg = get_metabolic_pathways_registry()
    graphs = reg.list_all() if hasattr(reg, "list_all") else list(reg.pathways.values())
    glycolysis = next(g for g in graphs if g.name == "glycolysis")

    # GAPDH produces NADH; LDH consumes it.
    gapdh = next(e for e in glycolysis.edges if e.from_node == "gap")
    ldh = next(e for e in glycolysis.edges if e.to_node == "lactate")

    assert ("NADH", 1) in edge_yields(gapdh), edge_yields(gapdh)
    assert ("NADH", -1) in edge_yields(ldh), edge_yields(ldh)

    # ATP keeps its natural sign: hexokinase spends, PGK makes.
    hexokinase = next(e for e in glycolysis.edges if e.to_node == "g6p")
    pgk = next(e for e in glycolysis.edges if e.from_node == "13bpg")
    assert ("ATP", -1) in edge_yields(hexokinase), edge_yields(hexokinase)
    assert ("ATP", 1) in edge_yields(pgk), edge_yields(pgk)
