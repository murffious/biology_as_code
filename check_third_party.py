#!/usr/bin/env python3
"""Every sizeable data file this PUBLIC repo ships must be accounted for.

  python3 check_third_party.py            report
  python3 check_third_party.py --strict   exit 1 on any FAIL

`murffious/biology_as_code` is public and Zenodo-deposited. Whatever is tracked
here is redistributed to the world under Apache-2.0 unless something says
otherwise — and for eight of MASTER_CROSSWALK.tsv's twelve columns, something has
to. This gate exists because the analysis already existed (in
working_map_nutrition/VMH_REFERENCE.md, since July) and simply never reached the
published repository. A fact known in a private repo and absent from a public one
is, from the outside, a fact nobody knew.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "THIRD-PARTY-DATA.json"
MIN_BYTES = 20_000
DATA_EXT = {".tsv", ".csv", ".json", ".ttl", ".mat", ".xml", ".parquet", ".db"}
SKIP_DIRS = {".venv", "node_modules", "__pycache__", ".git", "site", "notebooks"}


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=HERE, capture_output=True, text=True)
    if out.returncode != 0:
        return []
    return [HERE / f for f in out.stdout.splitlines()]


def main(argv: list[str]) -> int:
    fails: list[str] = []

    if not MANIFEST.is_file():
        print("FAIL  THIRD-PARTY-DATA.json missing")
        return 1
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    covered = {e["file"].rstrip("/") for e in m["entries"]}
    covered |= {f["file"].rstrip("/") for f in m["first_party"]}

    # 1. Every tracked data file over the threshold is declared, one way or another.
    unaccounted = []
    for p in tracked_files():
        if not p.is_file() or p.suffix not in DATA_EXT:
            continue
        if set(p.relative_to(HERE).parts) & SKIP_DIRS:
            continue
        if p.stat().st_size < MIN_BYTES:
            continue
        rel = str(p.relative_to(HERE))
        if not any(rel == c or rel.startswith(c + "/") for c in covered):
            unaccounted.append(rel)
    if unaccounted:
        fails.append(f"{len(unaccounted)} tracked data file(s) in neither the "
                     f"third-party nor the first-party list: {sorted(unaccounted)[:8]}")

    # 2. Each third-party entry that restricts anything must ship its own notice.
    for e in m["entries"]:
        if not e.get("blocks"):
            continue
        notice = HERE / (Path(e["file"]).stem + ".NOTICE.md")
        if e["file"].endswith("/"):
            notice = HERE / e["file"] / "NOTICE.md"
        if not notice.is_file():
            fails.append(f"{e['id']} restricts {e['blocks']} but has no {notice.name}")

    # 3. NOTICE must carry the third-party section.
    n = (HERE / "NOTICE").read_text(encoding="utf-8") if (HERE / "NOTICE").is_file() else ""
    if "THIRD-PARTY DATA" not in n:
        fails.append("NOTICE has no THIRD-PARTY DATA section")
    for e in m["entries"]:
        if e.get("blocks") and e["source"].split(" /")[0].split(" (")[0] not in n:
            fails.append(f"NOTICE does not attribute {e['source']}")

    # 4. CITATION.cff must not reclaim what the manifest says is third-party.
    c = (HERE / "CITATION.cff").read_text(encoding="utf-8") if (HERE / "CITATION.cff").is_file() else ""
    if "MASTER_CROSSWALK" in c and "does NOT claim authorship" not in c:
        fails.append("CITATION.cff mentions MASTER_CROSSWALK without disclaiming authorship")

    print(f"third-party register — {len(m['entries'])} third-party, "
          f"{len(m['first_party'])} first-party declared")
    for e in m["entries"]:
        mark = "restricted" if e.get("blocks") else "clear     "
        print(f"  {mark}  {e['file']:24} {e['source'][:44]:44} "
              f"{e['declared_licence']} ({e['licence_confidence']})")
    if fails:
        print()
        for f in fails:
            print("FAIL  " + f)
        return 1 if "--strict" in argv else 0
    print("\nOK    everything shipped is accounted for")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
