"""
Integrity checks on VERSION_MANIFEST.json.

The manifest is the package's self-description: version, component tiers, and
which module or data file backs each component. Nothing verified it, so it could
drift from reality while still reading as authoritative. A manifest that names a
module which no longer exists is worse than no manifest.

These tests found two live inconsistencies when first written: the manifest
claimed Python >=3.10 while pyproject required >=3.11, and the ``evidence_pubmed``
component pointed at ``evidence_pubmed.py``, which had been renamed to
``evidence.py``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from biology_as_code import __version__
from biology_as_code.data.version_manifest import package_version

REPO_ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = REPO_ROOT / "src" / "biology_as_code"
MANIFEST_PATH = PKG_ROOT / "data" / "VERSION_MANIFEST.json"

KNOWN_TIERS = {
    "FLOW",
    "FLOW_open",
    "UNITS",
    "UNITS_skeleton",
    "EVIDENCE",
    "POLICY",
    "LAW",
}


def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def pyproject() -> str:
    return (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")


def citation_cff() -> str:
    return (REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8")


# --- version agreement across every place it is written ------------------------


def test_one_version_everywhere():
    """pyproject, the manifest, CITATION.cff and the runtime must agree.

    Four files record the version. A release where they disagree produces a wheel,
    a Zenodo record and a citation that describe different software.
    """
    declared = re.search(r'^version = "([^"]+)"', pyproject(), re.M).group(1)
    cff = re.search(r'^version: "([^"]+)"', citation_cff(), re.M).group(1)
    assert manifest()["package_version"] == declared
    assert cff == declared
    assert package_version() == declared
    assert __version__ == declared


def test_semver_block_matches_the_version_string():
    data = manifest()
    semver = data["semver"]
    rebuilt = f"{semver['major']}.{semver['minor']}.{semver['patch']}"
    if semver.get("pre"):
        rebuilt += f"-{semver['pre']}"
    assert rebuilt == data["package_version"]


def test_manifest_python_floor_matches_pyproject():
    """The manifest must not advertise a Python the package rejects at install."""
    required = re.search(r'requires-python = "([^"]+)"', pyproject()).group(1)
    assert manifest()["compatibility"]["python"] == required


def test_cff_doi_matches_zenodo_identifier():
    text = citation_cff()
    top = re.search(r'^doi: "([^"]+)"', text, re.M).group(1)
    identifiers = re.findall(r'value: "(10\.5281/zenodo\.[0-9]+)"', text)
    assert identifiers, "CITATION.cff has no Zenodo identifier block"
    assert all(value == top for value in identifiers)


# --- every path the manifest names must exist ---------------------------------


def _component_modules() -> list[tuple[str, str]]:
    pairs = []
    for name, component in manifest()["components"].items():
        modules = component.get("modules") or (
            [component["module"]] if "module" in component else []
        )
        pairs.extend((name, module) for module in modules)
    return pairs


@pytest.mark.parametrize(("name", "module"), _component_modules(), ids=lambda v: str(v))
def test_component_module_resolves(name: str, module: str):
    """Each component names a module or directory that is actually in the package."""
    target = Path(module)
    matches = list(PKG_ROOT.rglob(target.name))
    assert matches, f"component {name!r} points at missing path {module!r}"


@pytest.mark.parametrize(
    ("name", "relative"),
    [(n, a["path"]) for n, a in manifest()["data_artifacts"].items()],
    ids=lambda v: str(v),
)
def test_data_artifact_resolves(name: str, relative: str):
    assert (PKG_ROOT / "data" / relative).exists(), f"artifact {name!r} missing: {relative}"


# --- tier vocabulary ----------------------------------------------------------


def test_declared_tiers_are_from_the_known_vocabulary():
    """An unrecognised tier silently defeats the point of tiering."""
    data = manifest()
    unknown = set()
    for component in data["components"].values():
        if "tier" in component and component["tier"] not in KNOWN_TIERS:
            unknown.add(component["tier"])
    for artifact in data["data_artifacts"].values():
        if "tier" in artifact and artifact["tier"] not in KNOWN_TIERS:
            unknown.add(artifact["tier"])
    assert not unknown, f"unknown tiers: {sorted(unknown)}"


def test_unlocked_magnitudes_are_declared_not_implied():
    """Any artifact carrying a magnitude must say whether it is locked."""
    for name, artifact in manifest()["data_artifacts"].items():
        if artifact.get("tier", "").startswith("UNITS_skeleton"):
            assert "magnitude_locked" in artifact, (
                f"{name}: skeleton artifact must declare magnitude_locked"
            )
            assert artifact["magnitude_locked"] is False
