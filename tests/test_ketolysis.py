"""Ketolysis pathway (TODO 6b) — discovery + biochemistry invariants."""

from __future__ import annotations


def test_ketolysis_is_discoverable():
    from biology_as_code import get_pathway, list_pathways

    assert "ketolysis" in [n.lower() for n in list_pathways()]
    p = get_pathway("ketolysis")
    assert p is not None
    assert len(p.nodes) == 4
    assert len(p.edges) == 3


def test_ketolysis_enzymes_present():
    from biology_as_code import get_pathway

    enzymes = " ".join(e.enzyme for e in get_pathway("ketolysis").edges)
    for marker in ("BDH1", "SCOT", "OXCT1", "ACAT1"):
        assert marker in enzymes, f"missing key enzyme marker {marker}"


def test_ketolysis_starts_at_ketone_ends_at_acetyl_coa():
    from biology_as_code import get_pathway

    p = get_pathway("ketolysis")
    node_ids = set(p.nodes)
    assert "beta_hydroxybutyrate" in node_ids
    assert "acetyl_coa" in node_ids
    # the chain is linear BHB -> acetoacetate -> acetoacetyl_coa -> acetyl_coa
    froms = {e.from_node for e in p.edges}
    tos = {e.to_node for e in p.edges}
    assert "beta_hydroxybutyrate" in froms  # substrate is consumed
    assert "acetyl_coa" in tos               # product is produced
    assert p.summary()["acetyl_coa_per_ketone"] == 2


def test_ketolysis_liver_cannot_run_it():
    """The defining teaching point: liver lacks SCOT (no futile cycle)."""
    from biology_as_code import get_pathway

    p = get_pathway("ketolysis")
    blob = (p.description + " " + p.summary()["location"]).lower()
    assert "liver" in blob and "scot" in blob
