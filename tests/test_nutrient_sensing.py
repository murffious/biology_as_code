"""Multi-node AMPK/mTORC1/SREBP regulatory graphs (feature #2)."""

from __future__ import annotations

import pytest

NETWORKS = ["ampk_network", "mtorc1_network", "srebp_network"]


@pytest.mark.parametrize("name", NETWORKS)
def test_networks_discoverable_and_multinode(name):
    from biology_as_code import get_pathway, list_pathways

    assert name in [n.lower() for n in list_pathways()]
    p = get_pathway(name)
    assert p is not None
    assert len(p.nodes) >= 8, "should be a genuine multi-node graph, not a scalar proxy"
    assert len(p.edges) >= 8


@pytest.mark.parametrize("name", NETWORKS)
def test_edges_are_signed_and_valid(name):
    from biology_as_code import get_pathway

    p = get_pathway(name)
    for e in p.edges:
        assert e.effect in ("activates", "inhibits"), e
        assert e.from_node in p.nodes
        assert e.to_node in p.nodes
    s = p.summary()
    assert s["activating_edges"] + s["inhibiting_edges"] == len(p.edges)


def test_key_crosstalk_edges_present():
    """The physiology that matters: AMPK ⊣ mTORC1, mTORC1 → SREBP, the ULK1 switch."""
    from biology_as_code import get_pathway

    def has(net, frm, to, eff):
        return any(e.from_node == frm and e.to_node == to and e.effect == eff
                   for e in get_pathway(net).edges)

    assert has("ampk_network", "ampk", "mtorc1", "inhibits")
    assert has("ampk_network", "ampk", "ulk1", "activates")
    assert has("mtorc1_network", "mtorc1", "ulk1", "inhibits")
    assert has("mtorc1_network", "mtorc1", "srebp", "activates")
    assert has("srebp_network", "ampk", "srebp1c", "inhibits")


def test_networks_track_sources():
    from biology_as_code import get_pathway

    for name in NETWORKS:
        refs = get_pathway(name).references
        assert refs and any("PMC" in r or "http" in r for r in refs)
