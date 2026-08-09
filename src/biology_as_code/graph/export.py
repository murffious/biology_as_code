"""
Export the graph to formats other engines read.

SQLite is the canonical store because it runs anywhere with no install. These
exporters exist so the same graph can be loaded into Neo4j or Kùzu for real
traversal work, into an RDF store alongside the repo's existing ``aca.ttl`` and
``claim-shape.ttl``, or into a viewer via GraphML.

    from biology_as_code.graph import build, to_cypher
    print(to_cypher(build()))
"""

from __future__ import annotations

import json
from typing import Any
from xml.sax.saxutils import escape

BAC = "https://github.com/murffious/biology_as_code/ns#"


def to_cypher(graph: Any, *, batch: int = 500) -> str:
    """
    Cypher CREATE statements for Neo4j or Kùzu.

    Emitted as parameterless literals rather than a parameterised load, so the
    output is a self-contained script that can be diffed and reviewed.
    """
    lines = [
        "// Biology as Code — generated graph export",
        "// Constraints first, so a malformed load fails at the boundary.",
    ]
    labels = sorted({n.label for n in graph.nodes()})
    for label in labels:
        lines.append(
            f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS "
            f"FOR (n:{label}) REQUIRE n.id IS UNIQUE;"
        )
    lines.append("")

    count = 0
    for node in graph.nodes():
        props = {"id": node.id, "name": node.name, **node.props}
        lines.append(f"CREATE (:{node.label} {_cypher_map(props)});")
        count += 1
        if count % batch == 0:
            lines.append("")

    lines.append("")
    for edge in graph.edges():
        props: dict[str, Any] = dict(edge.props)
        if edge.asserts_magnitude:
            props["asserts_magnitude"] = True
        if edge.evidence:
            props["evidence"] = edge.evidence
        if edge.strength is not None:
            props["strength"] = edge.strength
        tail = f" {_cypher_map(props)}" if props else ""
        lines.append(
            f"MATCH (a {{id: {_cypher_str(edge.src)}}}), (b {{id: {_cypher_str(edge.dst)}}}) "
            f"CREATE (a)-[:{edge.rel}{tail}]->(b);"
        )
    return "\n".join(lines) + "\n"


def to_turtle(graph: Any) -> str:
    """
    RDF Turtle, so the graph sits alongside the repo's existing shapes.

    Node labels become ``rdf:type``; relations become predicates in the project
    namespace. Provenance is expressed with ``prov:wasDerivedFrom`` where an
    edge names its evidence, which is the join point with PROV-O.
    """
    out = [
        f"@prefix bac:  <{BAC}> .",
        "@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix prov: <http://www.w3.org/ns/prov#> .",
        "",
    ]
    for node in graph.nodes():
        subj = f"bac:{_iri(node.id)}"
        out.append(f"{subj} rdf:type bac:{node.label} ;")
        out.append(f'    rdfs:label {json.dumps(node.name)} ;')
        for key, val in sorted(node.props.items()):
            if val is None or val == "" or isinstance(val, (list, dict)):
                continue
            out.append(f"    bac:{_iri(str(key))} {_ttl_lit(val)} ;")
        out[-1] = out[-1].rstrip(" ;") + " ."
        out.append("")

    for edge in graph.edges():
        out.append(f"bac:{_iri(edge.src)} bac:{edge.rel} bac:{_iri(edge.dst)} .")
        if edge.evidence:
            out.append(
                f"bac:{_iri(edge.src)} prov:wasDerivedFrom bac:{_iri(edge.evidence)} ."
            )
    return "\n".join(out) + "\n"


def to_graphml(graph: Any) -> str:
    """GraphML for yEd, Gephi or Cytoscape."""
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '  <key id="label" for="node" attr.name="label" attr.type="string"/>',
        '  <key id="name"  for="node" attr.name="name"  attr.type="string"/>',
        '  <key id="rel"   for="edge" attr.name="rel"   attr.type="string"/>',
        '  <graph id="bac" edgedefault="directed">',
    ]
    for node in graph.nodes():
        out.append(f'    <node id="{escape(node.id)}">')
        out.append(f'      <data key="label">{escape(node.label)}</data>')
        out.append(f'      <data key="name">{escape(node.name)}</data>')
        out.append("    </node>")
    for i, edge in enumerate(graph.edges()):
        out.append(
            f'    <edge id="e{i}" source="{escape(edge.src)}" target="{escape(edge.dst)}">'
        )
        out.append(f'      <data key="rel">{escape(edge.rel)}</data>')
        out.append("    </edge>")
    out += ["  </graph>", "</graphml>"]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- helpers

def _cypher_str(val: str) -> str:
    return json.dumps(str(val))


def _cypher_map(props: dict[str, Any]) -> str:
    parts = []
    for key, val in sorted(props.items()):
        if val is None:
            continue
        safe = key if key.isidentifier() else f"`{key}`"
        if isinstance(val, bool):
            parts.append(f"{safe}: {str(val).lower()}")
        elif isinstance(val, (int, float)):
            parts.append(f"{safe}: {val}")
        elif isinstance(val, (list, dict)):
            parts.append(f"{safe}: {json.dumps(json.dumps(val))}")
        else:
            parts.append(f"{safe}: {json.dumps(str(val))}")
    return "{" + ", ".join(parts) + "}"


def _iri(text: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9_.-]", "_", text)


def _ttl_lit(val: Any) -> str:
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    return json.dumps(str(val))


__all__ = ["to_cypher", "to_turtle", "to_graphml", "BAC"]
