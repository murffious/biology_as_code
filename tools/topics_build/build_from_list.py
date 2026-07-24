#!/usr/bin/env python3
"""Dev-only: rebuild topics_ontology.json. Not installed with the pip package."""
from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def main() -> int:
    if "site-packages" in str(Path(__file__).resolve()) and os.environ.get(
        "BIOLOGY_AS_CODE_FORCE_TOPICS_BUILD"
    ) != "1":
        print(
            "Refusing to run topics build from an installed package path. "
            "Use the repo tools/topics_build/ checkout, or set "
            "BIOLOGY_AS_CODE_FORCE_TOPICS_BUILD=1.",
            file=sys.stderr,
        )
        return 2
    impl = Path(__file__).with_name("_classify_topics_impl.py")
    if not impl.is_file():
        print(f"Missing {impl}", file=sys.stderr)
        return 1
    ns = runpy.run_path(str(impl))
    return int(ns["main"]())


if __name__ == "__main__":
    raise SystemExit(main())
