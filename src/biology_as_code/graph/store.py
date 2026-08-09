"""
GraphStore — the property graph over the Biology as Code constitution.

SQLite rather than a graph server, deliberately: the store must run in CI with
no install, produce byte-identical databases from the same inputs, and let the
closed ENUMs be enforced as constraints instead of conventions. Traversal depth
here is small (a claim resolves through a handful of hops), so the engine is not
the interesting part. The model is.

Export to Cypher, Turtle or GraphML when a real graph engine is wanted —
see :mod:`biology_as_code.graph.export`.

    from biology_as_code.graph import GraphStore

    g = GraphStore.open(":memory:")
    g.add_node("LAW-020", "Law", "Delivery = multi-stage fractional yields", system="Assimilation")
    g.neighbors("LAW-020", rel="HAS_GATE")
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

#: Relations that assert biology. Everything else is structural bookkeeping.
BIOLOGICAL_RELATIONS = frozenset({
    "OPENS_GATE",
    "CLOSES_GATE",
    "EXPANDS_BOUND",
    "NARROWS_BOUND",
    "COMPETES_WITH",
    "PART_OF",
    "NEEDS_RESOLUTION",
    "MALFORMED_MECHANISM",
})


class GraphError(RuntimeError):
    """A write that the constitution refuses."""


@dataclass(frozen=True)
class Node:
    id: str
    label: str
    name: str
    props: dict[str, Any]


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    rel: str
    asserts_magnitude: bool
    evidence: str | None
    strength: int | None
    props: dict[str, Any]


class GraphStore:
    """A typed property graph with fail-closed write semantics."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.row_factory = sqlite3.Row

    # ------------------------------------------------------------ lifecycle

    @classmethod
    def open(cls, path: str | Path = ":memory:") -> GraphStore:
        conn = sqlite3.connect(str(path))
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        return cls(conn)

    def close(self) -> None:
        self._conn.commit()
        self._conn.close()

    def __enter__(self) -> GraphStore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def commit(self) -> None:
        self._conn.commit()

    # ------------------------------------------------------------ writes

    def add_node(self, node_id: str, label: str, name: str, **props: Any) -> str:
        """
        Insert a node, or update it in place if it already exists.

        Upsert rather than INSERT OR REPLACE: replace deletes the row first,
        and the edge foreign keys cascade on delete, so re-adding a node that
        other nodes already point at would silently destroy its edges.
        """
        try:
            self._conn.execute(
                "INSERT INTO node (id, label, name, props) VALUES (?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "  label = excluded.label, "
                "  name  = excluded.name, "
                "  props = excluded.props",
                (node_id, label, name, json.dumps(props, sort_keys=True)),
            )
        except sqlite3.IntegrityError as exc:
            raise GraphError(f"node {node_id!r} ({label}): {exc}") from exc
        return node_id

    def add_edge(
        self,
        src: str,
        rel: str,
        dst: str,
        *,
        asserts_magnitude: bool = False,
        evidence: str | None = None,
        strength: int | None = None,
        **props: Any,
    ) -> None:
        """
        Connect two nodes.

        A magnitude-asserting edge without ``evidence`` is refused by the
        database, not by this function — the rule survives direct SQL.
        """
        try:
            # ON CONFLICT DO NOTHING, never INSERT OR IGNORE: OR IGNORE
            # suppresses CHECK and foreign-key failures too, which would make
            # the closed relation ENUM silently unenforced. This form ignores
            # only the duplicate-edge UNIQUE conflict.
            self._conn.execute(
                "INSERT INTO edge "
                "(src, dst, rel, asserts_magnitude, evidence, strength, props) "
                "VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT (src, dst, rel) DO NOTHING",
                (
                    src,
                    dst,
                    rel,
                    int(asserts_magnitude),
                    evidence,
                    strength,
                    json.dumps(props, sort_keys=True),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise GraphError(f"edge {src} -{rel}-> {dst}: {exc}") from exc

    # ------------------------------------------------------------ reads

    def get_node(self, node_id: str) -> Node | None:
        row = self._conn.execute(
            "SELECT id, label, name, props FROM node WHERE id = ?", (node_id,)
        ).fetchone()
        return _to_node(row) if row else None

    def nodes(self, label: str | None = None) -> Iterator[Node]:
        sql = "SELECT id, label, name, props FROM node"
        args: tuple[Any, ...] = ()
        if label:
            sql += " WHERE label = ?"
            args = (label,)
        for row in self._conn.execute(sql + " ORDER BY id", args):
            yield _to_node(row)

    def edges(self, rel: str | None = None) -> Iterator[Edge]:
        sql = ("SELECT src, dst, rel, asserts_magnitude, evidence, strength, props "
               "FROM edge")
        args: tuple[Any, ...] = ()
        if rel:
            sql += " WHERE rel = ?"
            args = (rel,)
        for row in self._conn.execute(sql + " ORDER BY id", args):
            yield _to_edge(row)

    def neighbors(
        self, node_id: str, rel: str | None = None, *, incoming: bool = False
    ) -> list[Node]:
        """Nodes one hop away, optionally filtered by relation."""
        col, other = ("dst", "src") if incoming else ("src", "dst")
        sql = (
            f"SELECT n.id, n.label, n.name, n.props FROM edge e "
            f"JOIN node n ON n.id = e.{other} WHERE e.{col} = ?"
        )
        args: list[Any] = [node_id]
        if rel:
            sql += " AND e.rel = ?"
            args.append(rel)
        return [_to_node(r) for r in self._conn.execute(sql + " ORDER BY n.id", args)]

    def paths(self, src: str, dst: str, max_depth: int = 4) -> list[list[str]]:
        """
        All simple paths from src to dst up to ``max_depth`` hops.

        Breadth-first in Python rather than a recursive CTE, because we need the
        edge relation names in the result and the graphs here are small.
        """
        found: list[list[str]] = []
        queue: list[list[str]] = [[src]]
        while queue:
            path = queue.pop(0)
            if len(path) > max_depth + 1:
                continue
            tail = path[-1]
            for nb in self.neighbors(tail):
                if nb.id in path:
                    continue
                new = [*path, nb.id]
                if nb.id == dst:
                    found.append(new)
                else:
                    queue.append(new)
        return found

    def query(self, sql: str, args: Iterable[Any] = ()) -> list[sqlite3.Row]:
        """Escape hatch for the views in schema.sql."""
        return list(self._conn.execute(sql, tuple(args)))

    # ------------------------------------------------------------ audit

    def integrity_report(self) -> dict[str, Any]:
        """
        What the graph knows it cannot support.

        This is the graph's version of the manuscript's verification appendix:
        every place a magnitude is asserted without evidence, every law with no
        contribution, every dangling relation.
        """
        unsourced = self.query("SELECT law_id, bound_text FROM v_unsourced_bounds")
        coverage = self.query("SELECT law_id, contributions, best_strength FROM v_law_evidence")
        gateless = self.query(
            "SELECT law_id FROM v_law_card WHERE gate_present IN (0, 'false') OR gate_present IS NULL"
        )
        return {
            "laws": sum(1 for _ in self.nodes("Law")),
            "laws_without_evidence": sum(1 for r in coverage if r["contributions"] == 0),
            "laws_with_unsourced_bound": len(unsourced),
            "laws_without_categorical_gate": len(gateless),
            "unsourced_bound_ids": [r["law_id"] for r in unsourced],
            "biological_edges": sum(
                1 for e in self.edges() if e.rel in BIOLOGICAL_RELATIONS
            ),
            "magnitude_edges": sum(1 for e in self.edges() if e.asserts_magnitude),
        }

    def counts(self) -> dict[str, int]:
        rows = self.query("SELECT label, COUNT(*) c FROM node GROUP BY label ORDER BY label")
        out = {r["label"]: r["c"] for r in rows}
        rows = self.query("SELECT rel, COUNT(*) c FROM edge GROUP BY rel ORDER BY rel")
        out.update({f"->{r['rel']}": r["c"] for r in rows})
        return out


def _to_node(row: sqlite3.Row) -> Node:
    return Node(row["id"], row["label"], row["name"], json.loads(row["props"]))


def _to_edge(row: sqlite3.Row) -> Edge:
    return Edge(
        row["src"],
        row["dst"],
        row["rel"],
        bool(row["asserts_magnitude"]),
        row["evidence"],
        row["strength"],
        json.loads(row["props"]),
    )


__all__ = ["GraphStore", "GraphError", "Node", "Edge", "BIOLOGICAL_RELATIONS"]
