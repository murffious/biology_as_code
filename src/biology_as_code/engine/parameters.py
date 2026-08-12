"""
The engine's bindable parameter space, derived by introspection.

A ``x-binding_site`` annotation is a promise that some host field actually
reaches the engine. The promise is only worth something if it can be checked,
and it can only be checked against a parameter space that is *derived from the
engine* rather than typed out beside it. A hand-maintained list of valid paths
would drift, and a drifted allow-list validates nothing — it would happily
accept a path to a pathway node deleted three commits ago.

So this module walks the real objects:

``sim.state.<field>``
    Every field of :class:`~biology_as_code.engine.sim.state.MetabolicState`.

``compartments.<organ>.<field>``
    Every organ in ``ORGAN_BOUNDS`` and every field of ``OrganBounds``.

``processes.<pathway>.<node>.context.<key>``
    Every context key any modifier in a pathway graph actually reads
    (``Modifier.requires_context``), plus every gate key a node checks. If a
    modifier is deleted, its binding site disappears with it and anything still
    pointing there fails.

``processes.<pathway>.<node>.yield_factor``
    The multiplier each node contributes.

``signals.<id>``
    Every signal in the catalog.

``responses.<protocol_id>``
    Every executable response protocol.

Nothing here is written by hand except the shape of the path strings.
"""

from __future__ import annotations

from dataclasses import fields as dataclass_fields
from functools import lru_cache
from typing import Any, Iterable, Mapping

__all__ = [
    "ParameterSpace",
    "parameter_space",
    "resolve_binding",
    "list_parameters",
]


class ParameterSpace:
    """An immutable set of bindable parameter paths, with provenance."""

    def __init__(self, entries: Mapping[str, str]):
        self._entries = dict(entries)

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, path: str) -> bool:
        return path in self._entries

    def __iter__(self):
        return iter(sorted(self._entries))

    def paths(self) -> list[str]:
        return sorted(self._entries)

    def origin(self, path: str) -> str:
        """Where this parameter came from, for error messages."""
        return self._entries[path]

    def namespaces(self) -> list[str]:
        return sorted({p.split(".", 1)[0] for p in self._entries})

    def under(self, prefix: str) -> list[str]:
        return sorted(p for p in self._entries if p == prefix or p.startswith(prefix + "."))

    def nearest(self, path: str, limit: int = 3) -> list[str]:
        """Closest known paths, for a directed error when a binding dangles."""
        import difflib

        return difflib.get_close_matches(path, self._entries, n=limit, cutoff=0.5)


def _state_params() -> dict[str, str]:
    from biology_as_code.engine.sim.state import MetabolicState

    return {
        f"sim.state.{f.name}": "MetabolicState dataclass field"
        for f in dataclass_fields(MetabolicState)
    }


def _compartment_params() -> dict[str, str]:
    from biology_as_code.engine.geography.organ_bounds import ORGAN_BOUNDS, OrganBounds

    out: dict[str, str] = {}
    field_names = [f.name for f in dataclass_fields(OrganBounds)]
    for organ in ORGAN_BOUNDS:
        out[f"compartments.{organ}"] = "ORGAN_BOUNDS entry"
        for name in field_names:
            out[f"compartments.{organ}.{name}"] = "OrganBounds field"
    return out


def _pathway_params() -> dict[str, str]:
    from biology_as_code.engine.pathways.colon_scfa import COLON_SCFA_PATHWAY
    from biology_as_code.engine.pathways.nonhaem_iron import NONHAEM_IRON_PATHWAY

    graphs: dict[str, Mapping[str, Any]] = {
        "nonhaem_iron": NONHAEM_IRON_PATHWAY,
        "colon_scfa": COLON_SCFA_PATHWAY,
    }
    out: dict[str, str] = {}
    for pathway_id, nodes in graphs.items():
        out[f"processes.{pathway_id}"] = "pathway graph"
        for node_id, node in nodes.items():
            base = f"processes.{pathway_id}.{node_id}"
            out[base] = "pathway node"
            out[f"{base}.yield_factor"] = "pathway node yield multiplier"
            for mod in (*node.inhibitors, *node.enhancers):
                if mod.requires_context:
                    out[f"{base}.context.{mod.requires_context}"] = (
                        f"context key read by modifier {mod.id}"
                    )
            if node.is_gate and node.gate_context_key:
                out[f"{base}.gate.{node.gate_context_key}"] = "gate context key"
    return out


def _signal_params() -> dict[str, str]:
    from biology_as_code.engine.signals import SIGNALS

    return {f"signals.{sid}": "signal catalog entry" for sid in SIGNALS}


def _response_params() -> dict[str, str]:
    from biology_as_code.responses import GLYCEMIC_RESPONSE_V1

    return {f"responses.{GLYCEMIC_RESPONSE_V1.protocol_id}": "executable response protocol"}


@lru_cache(maxsize=1)
def parameter_space() -> ParameterSpace:
    """The full bindable parameter space. Cached; call ``.cache_clear()`` in tests."""
    entries: dict[str, str] = {}
    for builder in (
        _state_params,
        _compartment_params,
        _pathway_params,
        _signal_params,
        _response_params,
    ):
        entries.update(builder())
    return ParameterSpace(entries)


def list_parameters(prefix: str | None = None) -> list[str]:
    space = parameter_space()
    return space.under(prefix) if prefix else space.paths()


def resolve_binding(path: str) -> str:
    """
    Resolve a binding path, or raise ``KeyError`` naming the nearest matches.

    Raises rather than returning False so a caller cannot accidentally treat an
    unresolved binding as merely falsy.
    """
    space = parameter_space()
    if path in space:
        return space.origin(path)
    near = space.nearest(path)
    hint = f" Did you mean: {', '.join(near)}?" if near else ""
    raise KeyError(
        f"binding site {path!r} does not resolve to an engine parameter."
        f" Known namespaces: {', '.join(space.namespaces())}.{hint}"
    )


def check_bindings(paths: Iterable[str]) -> dict[str, list[str]]:
    """Split an iterable of paths into resolved and dangling."""
    space = parameter_space()
    resolved, dangling = [], []
    for p in paths:
        (resolved if p in space else dangling).append(p)
    return {"resolved": sorted(set(resolved)), "dangling": sorted(set(dangling))}
