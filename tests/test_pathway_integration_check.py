"""Smoke tests for scripts/check_pathway_integration.py."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


def test_integration_check_all_pass():
    import check_pathway_integration as chk

    report = chk.run_checks(only=None)
    assert report["pass"], f"integration failures: {report['failed']}"
    assert report["registry_count"] >= 28
    assert not report["orphan_packs"]
    assert not report["missing_packs"]


def test_integration_check_known_pathway():
    import check_pathway_integration as chk

    report = chk.run_checks(only="glycolysis")
    assert report["pass"], report["failed"]
    assert "glycolysis" in report["ok"] or any("glycolysis" in n for n in report["ok"])


def test_integration_check_unknown_pathway_fails():
    import check_pathway_integration as chk

    report = chk.run_checks(only="not_a_real_pathway_xyz")
    assert not report["pass"]
