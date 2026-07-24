"""
Load encyclopedia topic vocabulary as typed sim nodes.

Source JSON built from frozen list.topics.md (reference only).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from biology_as_code.data.kibo_core.paths import data_file

_DEFAULT = data_file("topics_ontology.json")


@dataclass(frozen=True)
class TopicNode:
    id: str
    label: str
    kind: str
    sim_role: str
    systems: tuple[str, ...]
    chain_layer: str | None
    law_links: tuple[str, ...]
    sim_repr: dict[str, Any]
    status: str
    categories: tuple[str, ...] = ()
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def field_hint(self) -> str:
        return str((self.sim_repr or {}).get("field_hint") or self.id)

    @property
    def sim_ready(self) -> bool:
        return self.sim_role not in ("lexicon", "measurement", "endpoint") or bool(
            self.law_links
        )


class TopicRegistry:
    def __init__(self, topics: list[TopicNode], meta: dict[str, Any] | None = None):
        self._by_id = {t.id: t for t in topics}
        self._by_label = {t.label.casefold(): t for t in topics}
        self.meta = meta or {}

    def __len__(self) -> int:
        return len(self._by_id)

    def get(self, topic_id: str) -> TopicNode:
        return self._by_id[topic_id]

    def find(self, label: str) -> TopicNode | None:
        return self._by_label.get(label.casefold())

    def all(self) -> list[TopicNode]:
        return [self._by_id[k] for k in sorted(self._by_id)]

    def by_role(self, role: str) -> list[TopicNode]:
        return [t for t in self.all() if t.sim_role == role]

    def by_system(self, system: str) -> list[TopicNode]:
        return [t for t in self.all() if system in t.systems]

    def by_status(self, status: str) -> list[TopicNode]:
        return [t for t in self.all() if t.status == status]

    def linked_to_law(self, law_id: str) -> list[TopicNode]:
        return [t for t in self.all() if law_id in t.law_links]

    def sim_ready(self) -> list[TopicNode]:
        return [
            t
            for t in self.all()
            if t.sim_role
            in (
                "cargo",
                "modifier",
                "signal",
                "mechanism",
                "process",
                "compartment",
                "payload_food",
                "host_context",
            )
        ]

    def summary(self) -> dict[str, Any]:
        roles: dict[str, int] = {}
        for t in self.all():
            roles[t.sim_role] = roles.get(t.sim_role, 0) + 1
        return {
            "n": len(self),
            "by_role": roles,
            "mapped": len(self.by_status("mapped")),
            "sim_stub": len(self.by_status("sim_stub")),
            "lexicon": len(self.by_status("lexicon")),
        }


def load_topics(path: Path | str | None = None) -> TopicRegistry:
    p = Path(path) if path else _DEFAULT
    data = json.loads(p.read_text(encoding="utf-8"))
    nodes: list[TopicNode] = []
    for raw in data.get("topics") or []:
        nodes.append(
            TopicNode(
                id=raw["id"],
                label=raw["label"],
                kind=raw.get("kind") or "other",
                sim_role=raw.get("sim_role") or "lexicon",
                systems=tuple(raw.get("systems") or []),
                chain_layer=raw.get("chain_layer"),
                law_links=tuple(raw.get("law_links") or []),
                sim_repr=dict(raw.get("sim_repr") or {}),
                status=raw.get("status") or "lexicon",
                categories=tuple(raw.get("categories") or []),
                raw=raw,
            )
        )
    return TopicRegistry(
        nodes,
        meta={
            "source": data.get("source"),
            "count": data.get("count"),
            "honesty": data.get("honesty"),
        },
    )
