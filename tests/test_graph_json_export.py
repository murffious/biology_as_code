"""
The JSON graph export must be usable by a renderer that knows no Python.

`scripts/export_graph_json.py` exists so an HTML cascade diagram stops
hand-copying facts the pathway modules already test. That only holds if the
export is complete (a cofactor dropped here is a cofactor the diagram silently
stops showing) and if it stays out of the layout's business (a coordinate
emitted here is a hand-tuned layout a generator will overwrite).

These tests check the export against the registry, not against itself, in the
spirit of `test_pathway_export_lossless.py`.

    pytest tests/test_graph_json_export.py -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT / "scripts"))

from export_graph_json import (  # noqa: E402
    FORBIDDEN_KEYS,
    GRAPH_SCHEMA,
    INDEX_SCHEMA,
    build_all,
    dumps,
    index_to_json,
)

from biology_as_code.nodes import CERTIFICATION_ORDER  # noqa: E402

PACKS = SRC / "biology_as_code" / "pathways" / "packs"
INDEX_FILE = PACKS / "graph-index.json"

#: Carnitine synthesis is the worked case for `requires_nutrient`: five distinct
#: dependencies on one linear chain, so a shortfall at any single step blocks
#: endogenous synthesis. The exported strings are finer-grained than the families
#: (folate and B12 appear because they regenerate methionine for SAM), so assert
#: the families are each represented rather than pinning a flat count.
CARNITINE_FAMILIES = {
    "methyl donation (SAM)": {"methionine (SAM)", "folate", "vitamin B12"},
    "iron": {"iron"},
    "vitamin C": {"vitamin C"},
    "vitamin B6": {"vitamin B6 (PLP)"},
    "niacin (NAD)": {"niacin (NAD)"},
}

#: The four PLP-dependent steps of tryptophan → niacin. `OHKYN -> OHANTH` is the
#: bottleneck (the only route to niacin) and `OHKYN -> XANTH` is the spillway
#: that fills when it stalls; losing either in export loses the B6 argument.
TRYPTOPHAN_B6_STEPS = {
    ("KYN", "KYNA"),
    ("KYN", "ANTH"),
    ("OHKYN", "XANTH"),
    ("OHKYN", "OHANTH"),
}


def _documents() -> dict[str, dict[str, Any]]:
    """Freshly built documents, keyed by pathway id."""
    return {doc["id"]: doc for doc in build_all()}


def _walk(value: Any, path: str = "$") -> Iterator[tuple[str, str]]:
    """Yield (json path, key) for every mapping key in a document."""
    if isinstance(value, dict):
        for key, sub in value.items():
            yield f"{path}.{key}", str(key)
            yield from _walk(sub, f"{path}.{key}")
    elif isinstance(value, list):
        for i, sub in enumerate(value):
            yield from _walk(sub, f"{path}[{i}]")


def test_exporter_runs_and_writes_every_pack():
    """The script itself must run green, not just its importable pieces."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "export_graph_json.py")],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    ids = sorted(_documents())
    assert ids, "no pathways collected"
    for pack_id in ids:
        assert (PACKS / pack_id / "graph.json").is_file(), f"{pack_id}: no graph.json"
    assert INDEX_FILE.is_file(), "no graph-index.json"
    print(f"✓ Exporter wrote graph.json for {len(ids)} packs + index")


def test_written_json_parses_and_declares_its_schema():
    for pack_id in _documents():
        path = PACKS / pack_id / "graph.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert doc["schema"] == GRAPH_SCHEMA, f"{pack_id}: unexpected schema tag"
        assert doc["id"] == pack_id
        assert doc["nodes"], f"{pack_id}: no nodes"
        assert doc["edges"], f"{pack_id}: no edges"
    index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    assert index["schema"] == INDEX_SCHEMA
    assert index["count"] == len(index["pathways"]) == len(_documents())
    print(f"✓ Valid JSON for {index['count']} graphs + index")


def test_every_edge_endpoint_resolves_to_a_declared_node():
    """A dangling endpoint renders as a missing box, or as nothing at all."""
    dangling = []
    for pack_id, doc in _documents().items():
        declared = {n["id"] for n in doc["nodes"]}
        assert "" not in declared, f"{pack_id}: empty node id"
        for edge in doc["edges"]:
            for end in ("from", "to"):
                if edge[end] not in declared:
                    dangling.append(f"{pack_id}: {edge[end]!r} ({end})")
    assert not dangling, f"edges point at undeclared nodes: {dangling[:10]}"
    print("✓ Every edge endpoint resolves")


def test_carnitine_synthesis_keeps_its_five_nutrient_families():
    doc = _documents()["carnitine_synthesis"]
    exported = {c for edge in doc["edges"] for c in edge["cofactors"]}
    assert exported, "carnitine synthesis exported with no cofactors at all"
    for family, members in CARNITINE_FAMILIES.items():
        assert exported & members, f"lost the {family} dependency: have {sorted(exported)}"
    assert exported <= set().union(*CARNITINE_FAMILIES.values()), (
        f"unexpected cofactor strings: {sorted(exported - set().union(*CARNITINE_FAMILIES.values()))}"
    )
    # The same facts must also survive into the derived per-nutrient view.
    assert set(doc["nutrient_dependencies"]) == exported
    print(f"✓ Carnitine synthesis: {len(CARNITINE_FAMILIES)} families, {len(exported)} nutrients")


def test_tryptophan_niacin_keeps_its_b6_steps():
    doc = _documents()["tryptophan_niacin"]
    b6_steps = {
        (edge["from"], edge["to"])
        for edge in doc["edges"]
        if any("B6" in c for c in edge["cofactors"])
    }
    assert b6_steps == TRYPTOPHAN_B6_STEPS, f"B6 steps drifted: {sorted(b6_steps)}"
    iron_steps = {
        (edge["from"], edge["to"]) for edge in doc["edges"] if "iron" in edge["cofactors"]
    }
    assert ("OHANTH", "ACMS") in iron_steps, "lost the non-heme iron dioxygenase step"
    print(f"✓ Tryptophan → niacin: {len(b6_steps)} PLP steps + iron dioxygenase")


def test_yields_are_sign_normalised_to_positive_means_produced():
    """GAPDH-style edges store `nadh_cost = -1` for NADH *produced*; a client
    reading the raw field would print the opposite of the biology."""
    doc = _documents()["carnitine_synthesis"]
    made_nadh = [
        edge
        for edge in doc["edges"]
        if any(y["species"] == "NADH" and y["delta"] > 0 for y in edge["yields"])
    ]
    assert made_nadh, "γ-butyrobetaine aldehyde dehydrogenase should export NADH +1"
    assert doc["net_yields"].get("NADH") == 1
    print("✓ Yields normalised (positive = produced)")


def test_no_layout_leaks_into_the_export():
    """Layout stays hand-authored in a separate file keyed by node id.

    If coordinates ever ship from the generator, the next export silently
    overwrites hand-tuned positions — the failure this whole split exists to
    prevent.
    """
    leaks = []
    for pack_id, doc in _documents().items():
        for json_path, key in _walk(doc):
            if key.lower() in FORBIDDEN_KEYS:
                leaks.append(f"{pack_id}: {json_path}")
    assert not leaks, f"layout keys leaked into the export: {leaks[:10]}"
    print(f"✓ No layout keys ({sorted(FORBIDDEN_KEYS)}) in any graph.json")


def test_provenance_block_carries_references_and_an_honest_tier():
    for pack_id, doc in _documents().items():
        prov = doc["provenance"]
        assert prov["module"].startswith("biology_as_code.pathways."), pack_id
        assert isinstance(prov["references"], list), pack_id
        assert prov["certification"] in CERTIFICATION_ORDER, pack_id
        # Teaching topology from a secondary source is never a Bound.
        assert prov["certification"] != "bound", f"{pack_id}: claims a tier nobody earned"
        expected = "prior" if prov["references"] else "candidate"
        assert prov["certification"] == expected, pack_id
    cited = [d for d in _documents().values() if d["provenance"]["references"]]
    assert cited, "no pathway carries references — provenance block is dead weight"
    print(f"✓ Provenance on every graph ({len(cited)} cited)")


def test_index_agrees_with_the_per_pathway_files():
    index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    docs = _documents()
    for row in index["pathways"]:
        doc = docs[row["id"]]
        assert row["nodes"] == len(doc["nodes"])
        assert row["edges"] == len(doc["edges"])
        assert row["graph"] == f"{row['id']}/graph.json"
        assert (PACKS / row["graph"]).is_file()
    # Vitamin B6 lands in two pathways; that cross-pathway roll-up is the index's
    # reason to exist.
    b6 = [k for k in index["nutrient_index"] if "B6" in k]
    assert b6, "no B6 entry in the cross-pathway nutrient index"
    owners = {entry.split("::")[0] for key in b6 for entry in index["nutrient_index"][key]}
    assert {"tryptophan_niacin", "carnitine_synthesis"} <= owners, owners
    print(f"✓ Index agrees with {len(index['pathways'])} graphs")


def test_graph_json_not_stale():
    """Committed JSON must match a fresh export — same guard as the mermaid packs.

    Fix with: PYTHONPATH=src python3 scripts/export_graph_json.py
    """
    docs = _documents()
    stale = [
        f"{pack_id}/graph.json"
        for pack_id, doc in docs.items()
        if (PACKS / pack_id / "graph.json").read_text(encoding="utf-8") != dumps(doc)
    ]
    if INDEX_FILE.read_text(encoding="utf-8") != dumps(index_to_json(list(docs.values()))):
        stale.append("graph-index.json")
    assert not stale, "stale JSON — re-run scripts/export_graph_json.py: " + ", ".join(stale)
    print(f"✓ JSON in sync with generator ({len(docs)} graphs)")
