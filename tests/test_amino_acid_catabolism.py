"""Amino-acid catabolism teaching graphs — discovery + biochemistry invariants."""

from __future__ import annotations

AA_PATHWAYS = (
    "aa_nitrogen_disposal",
    "bcaa_catabolism",
    "phenylalanine_tyrosine_catabolism",
    "methionine_one_carbon",
    "glucogenic_ketogenic_aa",
)


def test_all_aa_pathways_discoverable():
    from biology_as_code import get_pathway, list_pathways

    names = {n.lower() for n in list_pathways()}
    for name in AA_PATHWAYS:
        assert name in names, f"missing from list_pathways: {name}"
        p = get_pathway(name)
        assert p is not None
        assert len(p.nodes) >= 4
        assert len(p.edges) >= 3


def test_nitrogen_disposal_links_urea_and_glutamate():
    from biology_as_code import get_pathway

    p = get_pathway("aa_nitrogen_disposal")
    assert "glutamate" in p.nodes
    assert "nh4" in p.nodes
    assert "urea_cycle_entry" in p.nodes
    s = p.summary()
    assert s["links_to"] == "urea_cycle"
    assert s["central_collector"] == "glutamate"
    mids = {e.mechanism_id for e in p.edges if e.mechanism_id}
    assert "aminotransferase" in mids
    assert "glutamate_dehydrogenase" in mids


def test_bcaa_has_trunk_and_divergent_fates():
    from biology_as_code import get_pathway

    p = get_pathway("bcaa_catabolism")
    for aa in ("leucine", "isoleucine", "valine"):
        assert aa in p.nodes
    assert "bcka" in p.nodes
    assert "acetyl_coa" in p.nodes
    assert "succinyl_coa" in p.nodes
    enzymes = " ".join(e.enzyme for e in p.edges)
    assert "BCKDH" in enzymes or "BCKDH" in p.summary().get("committed_enzyme", "")
    assert p.summary()["clinical_hook"] == "MSUD"
    assert p.summary()["leu_fate"] == "ketogenic"
    assert p.summary()["val_fate"] == "glucogenic"
    assert any(e.mechanism_id == "bckdh" for e in p.edges)


def test_phe_tyr_pku_and_mixed_products():
    from biology_as_code import get_pathway

    p = get_pathway("phenylalanine_tyrosine_catabolism")
    assert "phenylalanine" in p.nodes
    assert "tyrosine" in p.nodes
    assert "fumarate" in p.nodes
    assert "acetoacetate" in p.nodes
    # Phe → Tyr is the PKU step
    pah_edges = [e for e in p.edges if e.from_node == "phenylalanine" and e.to_node == "tyrosine"]
    assert len(pah_edges) == 1
    assert pah_edges[0].mechanism_id == "phenylalanine_hydroxylase"
    assert "PKU" in p.summary()["clinical_hook"]
    # FAH split to both products
    tos = {e.to_node for e in p.edges if e.from_node == "fumarylacetoacetate"}
    assert "fumarate" in tos and "acetoacetate" in tos


def test_methionine_sam_and_homocysteine_branch():
    from biology_as_code import get_pathway

    p = get_pathway("methionine_one_carbon")
    for nid in ("methionine", "sam", "sah", "homocysteine", "cysteine"):
        assert nid in p.nodes
    assert p.summary()["universal_methyl_donor"] == "SAM"
    assert p.summary()["branch_point"] == "homocysteine"
    assert any(e.mechanism_id == "methionine_adenosyltransferase" for e in p.edges)
    # Hcy has both remethylation and transsulfuration
    hcy_tos = {e.to_node for e in p.edges if e.from_node == "homocysteine"}
    assert "methionine" in hcy_tos
    assert "cysteine" in hcy_tos


def test_glucogenic_ketogenic_classification_map():
    from biology_as_code import get_pathway

    p = get_pathway("glucogenic_ketogenic_aa")
    assert p.summary()["graph_kind"] == "classification_map"
    assert "Leu" in p.summary()["purely_ketogenic"]
    # Leu/Lys only go ketogenic
    leu_tos = {e.to_node for e in p.edges if e.from_node == "leu_lys"}
    assert leu_tos == {"acetyl_coa_fate"}
    # Structural integrity
    for e in p.edges:
        assert e.from_node in p.nodes
        assert e.to_node in p.nodes


def test_aa_mechanism_ids_resolve():
    from biology_as_code import get_pathway
    from biology_as_code.pathways.metabolic_mechanisms import get_metabolic_mechanism_registry

    known = {m.id for m in get_metabolic_mechanism_registry().list_all()}
    required = {
        "aminotransferase",
        "glutamate_dehydrogenase",
        "bckdh",
        "phenylalanine_hydroxylase",
        "methionine_adenosyltransferase",
    }
    assert required <= known
    for name in AA_PATHWAYS:
        p = get_pathway(name)
        for e in p.edges:
            if e.mechanism_id:
                assert e.mechanism_id in known, f"{name}: unknown mechanism {e.mechanism_id}"
