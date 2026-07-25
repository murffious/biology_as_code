"""
Teaching pathway graphs + co-located mermaid packs.

Code: this package (`*.py`).
Diagrams: ``pathways/packs/<id>/pathway.mermaid`` (do not name a folder the same
as a ``.py`` module — that would shadow the import).

Coverage map: ``pathways/packs/COVERAGE.md``.
Use :func:`list_pathways` / :func:`get_pathway` for discovery.
"""

from biology_as_code.pathways.registry import get_pathway, list_pathways, pathway_loaders

__all__ = ["get_pathway", "list_pathways", "pathway_loaders"]
