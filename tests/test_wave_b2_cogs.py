"""Wave B2: PepT1, bile/micelle ids, gut incretin graph, Met synthase, haem iron."""

from __future__ import annotations


def test_pept1_on_protein_digestion():
    from biology_as_code import get_pathway

    p = get_pathway("protein_digestion_absorption")
    assert any(e.mechanism_id == "pept1" for e in p.edges)
    edge = next(e for e in p.edges if e.mechanism_id == "pept1")
    assert edge.from_node == "oligopeptides"
    assert edge.to_node == "amino_acids_enterocyte"


def test_bile_micelle_mechanism_ids_on_lipid_digestion():
    from biology_as_code import get_pathway
    from biology_as_code.pathways.metabolic_mechanisms import get_metabolic_mechanism_registry

    p = get_pathway("lipid_digestion_absorption")
    mids = {e.mechanism_id for e in p.edges if e.mechanism_id}
    assert "bile_salt_emulsification" in mids
    assert "bile_salt_micelle" in mids
    assert "pancreatic_lipase" in mids
    reg = get_metabolic_mechanism_registry()
    assert reg.get("bile_salt_micelle") is not None
    assert reg.get("bile_salt_emulsification") is not None


def test_gut_incretin_network_discoverable():
    from biology_as_code import get_pathway, list_pathways

    assert "gut_incretin_network" in {n.lower() for n in list_pathways()}
    p = get_pathway("gut_incretin_network")
    assert p is not None
    for nid in ("cck", "glp1", "gip", "pyy", "satiety", "insulin_secretion"):
        assert nid in p.nodes
    # CCK activates bile release; GLP-1 activates insulin
    effects = {(e.from_node, e.to_node, e.effect) for e in p.edges}
    assert ("cck", "gallbladder_bile_release", "activates") in effects
    assert ("glp1", "insulin_secretion", "activates") in effects
    assert ("glp1", "gastric_emptying", "inhibits") in effects


def test_methionine_synthase_on_one_carbon():
    from biology_as_code import get_pathway
    from biology_as_code.pathways.metabolic_mechanisms import get_metabolic_mechanism_registry

    p = get_pathway("methionine_one_carbon")
    mids = [e.mechanism_id for e in p.edges if e.mechanism_id]
    assert mids.count("methionine_synthase") >= 2  # Hcy→Met and methyl-THF→Met
    assert get_metabolic_mechanism_registry().get("methionine_synthase") is not None
    # remethylation edge
    assert any(
        e.from_node == "homocysteine" and e.to_node == "methionine" and e.mechanism_id == "methionine_synthase"
        for e in p.edges
    )


def test_heme_iron_branch_expanded():
    from biology_as_code import get_pathway
    from biology_as_code.pathways.metabolic_mechanisms import get_metabolic_mechanism_registry

    p = get_pathway("iron_absorption")
    assert "heme_enterocyte" in p.nodes
    assert "dietary_heme" in p.nodes
    mids = {e.mechanism_id for e in p.edges if e.mechanism_id}
    assert "hcp1_heme_uptake" in mids
    assert "heme_oxygenase_1" in mids
    # haem path: dietary_heme → heme_enterocyte → fe2_enterocyte → plasma
    assert any(e.from_node == "dietary_heme" and e.to_node == "heme_enterocyte" for e in p.edges)
    assert any(e.from_node == "heme_enterocyte" and e.to_node == "fe2_enterocyte" for e in p.edges)
    reg = get_metabolic_mechanism_registry()
    assert reg.get("hcp1_heme_uptake") is not None
    assert reg.get("heme_oxygenase_1") is not None


def test_wave_b2_mechanism_ids_resolve():
    from biology_as_code import get_pathway
    from biology_as_code.pathways.metabolic_mechanisms import get_metabolic_mechanism_registry

    known = {m.id for m in get_metabolic_mechanism_registry().list_all()}
    required = {
        "pept1",
        "bile_salt_micelle",
        "bile_salt_emulsification",
        "methionine_synthase",
        "hcp1_heme_uptake",
        "heme_oxygenase_1",
    }
    assert required <= known
    for name in (
        "protein_digestion_absorption",
        "lipid_digestion_absorption",
        "methionine_one_carbon",
        "iron_absorption",
    ):
        p = get_pathway(name)
        for e in p.edges:
            if e.mechanism_id:
                assert e.mechanism_id in known, f"{name}: {e.mechanism_id}"


def test_gut_incretin_regulation_fed_higher():
    from biology_as_code import fed, overnight_fast, pathway_activities

    a = pathway_activities(fed())
    b = pathway_activities(overnight_fast())
    assert "gut_incretin_network" in a
    assert a["gut_incretin_network"] > b["gut_incretin_network"]
