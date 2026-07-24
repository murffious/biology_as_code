"""
Teaching pathway graphs.

Module **filenames kept** from the simulator (no forced rename to atp.py / lipid.py).
Use :func:`list_pathways` / :func:`get_pathway` for discovery.
"""

from biology_as_code.pathways.registry import get_pathway, list_pathways, pathway_loaders

__all__ = ["get_pathway", "list_pathways", "pathway_loaders"]
