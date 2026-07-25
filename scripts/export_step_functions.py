"""
Compile the biology_as_code digestion machine registry to Amazon States Language.

**Offline and dependency-free.** This proves the machines are Step-Functions-shaped
and emits deployable ASL JSON — it does NOT call AWS or deploy anything. The local
runtime is still ``biology_as_code.machines.trace``.

    python scripts/export_step_functions.py                       # write dist/asl/*.json
    python scripts/export_step_functions.py --out build/asl
    python scripts/export_step_functions.py --food ex.spinach_salad.zero_fat
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from biology_as_code.digestion.asl import food_to_input, registry_to_asl  # noqa: E402


def _write_asl(out_dir: Path) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    registry = registry_to_asl()
    written: list[str] = []
    for machine_id, asl in registry.items():
        path = out_dir / f"{machine_id}.json"
        path.write_text(json.dumps(asl, indent=2), encoding="utf-8")
        written.append(str(path))
    (out_dir / "registry.asl.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="export_step_functions",
        description="Compile the digestion machines to Amazon States Language (offline).",
    )
    parser.add_argument("--out", default="dist/asl", help="output directory for ASL JSON")
    parser.add_argument("--food", default=None, help="print a food's nested execution input and exit")
    args = parser.parse_args(argv)

    if args.food:
        print(json.dumps(food_to_input(args.food), indent=2))
        return 0

    written = _write_asl(Path(args.out))
    print(f"wrote {len(written)} machine(s) + registry.asl.json to {args.out}/")
    for path in written:
        print(f"  {path}")
    print("\nNote: nested-stage ARNs are placeholders — fill at deploy. No AWS was called.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
