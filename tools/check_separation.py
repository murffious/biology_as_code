#!/usr/bin/env python3
"""No product identifier ships from this repository.

WHY IT REPLACES THE INLINE grep IN ci.yml
-----------------------------------------
The old gate was `grep -rniE "kibo|mealcoach|morf" src/ tests/`. It had four holes,
and three of them were found the hard way.

1. **An allowlist of directories.** `ontology-sdk/` was neither `src/` nor `tests/`,
   so it accumulated ten product-name references — four of which also leaked private
   repository paths — and CI stayed green the whole time. A gate that names the places
   it looks cannot see the place nobody thought to name. This one scans EVERY TRACKED
   FILE and excludes a short, justified list instead.

2. **Contents only, never paths.** A directory called `kibo_core/` is invisible to a
   content grep. Nothing tracked is affected today, but the shape of the check did not
   match the shape of the risk.

3. **Product and author conflated.** `morf` is the AUTHOR: `Paul Murff`,
   `Morf Engineering`, `paulmorf@morfengineering.tech`. It belongs in `CITATION.cff`,
   `pyproject.toml`, `paper/paper.md` and `.zenodo.json` — that is attribution, not
   leakage. Treating it as a product identifier meant the only way to keep the gate
   green was to exclude the files where the real product names would also hide.
   Product names and author names are now separate patterns with separate rules.

4a. **The gate failed on its own allowlist, in CI, after passing locally.** A reason
   in `separation.allow` says *"Records renames such as KIBO_PRODUCT_SCORE_MODULE ->
   BAC_SCORER_MODULE"*, and the scan read it as a leak. Two lessons. The small one:
   the local mutation test ran while `separation.allow` was still UNTRACKED, so
   `git ls-files` never handed it to the scanner — a gate keyed on tracked files must
   be tested after `git add`, not before. The real one: this is mention-vs-use inside
   the gate itself, the same error `check_no_human_rows.py` exists to avoid. The fix
   is not to exempt the file — that would make it the one place a leak could hide.
   In `separation.allow` alone, the PATH column is scanned and the reason text after
   `#` is not, because a reason that cannot name what it excepts is not a reason.

4. **`--exclude-dir="*.egg-info"` hid a real hit.** `src/biology_as_code.egg-info/PKG-INFO`
   carries `Keywords: ...,kibo,...` from an older `pyproject.toml`. It is untracked, so
   it never shipped from git — but the exclusion is why nobody noticed the stale
   artifact. Untracked files are out of scope here by construction, not by exception.

    python3 tools/check_separation.py            # scan every tracked file
    python3 tools/check_separation.py --staged   # only what is about to be committed
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
ALLOW = ROOT / "tools" / "separation.allow"

# Product identifiers. These must not appear in shipped code, data or docs.
PRODUCT = re.compile(r"(?i)\b(kibo|mealcoach)\b|kibo[_-]?\w+")
# The author and the organisation. Legitimate in authorship metadata; a smell in code.
AUTHOR = re.compile(r"(?i)\bmorf\b|morfengineering")
# Where authorship legitimately belongs. Author hits elsewhere are reported, not failed.
AUTHOR_OK = {"CITATION.cff", ".zenodo.json", "ZENODO.md", "pyproject.toml",
             "paper/paper.md", "NOTICE", "LICENSE", "PATENTS.md",
             "docs/VMH-LICENCE-ENQUIRY.md", "CHANGELOG.md"}
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".xlsx", ".xls", ".zip",
          ".whl", ".gz", ".so", ".ttl"}


def tracked(staged: bool) -> list[str]:
    cmd = (["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"] if staged
           else ["git", "ls-files"])
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True).stdout.split()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--staged", action="store_true")
    a = ap.parse_args()

    allowed, bad_allow = {}, []
    if ALLOW.exists():
        for raw in ALLOW.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            path, _, why = line.partition("#")
            (allowed.__setitem__(path.strip(), why.strip()) if why.strip()
             else bad_allow.append(path.strip()))
    if bad_allow:
        print(f"FAIL — {len(bad_allow)} allowlist entr(ies) with no stated reason:")
        for x in bad_allow:
            print(f"  {x}")
        return 1

    prod, auth, scanned = [], [], 0
    for rel in tracked(a.staged):
        p = ROOT / rel
        if not p.is_file() or rel in allowed:
            continue
        # 2. paths, not just contents
        if PRODUCT.search(rel):
            prod.append((rel, "PATH NAME carries a product identifier"))
        if p.suffix.lower() in BINARY:
            continue
        try:
            text = p.read_text(errors="replace")
        except Exception:                                        # noqa: BLE001
            continue
        if p == ALLOW:
            # Mention vs use. The allowlist's PATH column is real content and stays
            # under the gate; its reason text is prose ABOUT the product names and
            # must be free to say them. Blanking the comments rather than skipping
            # the file keeps a product-named path from ever being smuggled in here.
            text = "\n".join(ln.partition("#")[0] for ln in text.splitlines())
        scanned += 1
        for m in PRODUCT.finditer(text):
            ln = text[:m.start()].count("\n") + 1
            prod.append((rel, f"line {ln}: …{text[max(0,m.start()-45):m.end()+45].strip()[:100]}…"))
            break
        if rel not in AUTHOR_OK and AUTHOR.search(text):
            m = AUTHOR.search(text)
            auth.append((rel, f"line {text[:m.start()].count(chr(10))+1}"))

    print(f"separation: {scanned} tracked file(s) scanned"
          + (f", {len(allowed)} allowlisted" if allowed else ""))
    for rel, why in sorted(allowed.items()):
        print(f"  allowed  {rel}\n      {why}")

    if auth:
        print(f"\n  note: author/org name outside authorship metadata in {len(auth)} file(s) "
              f"— reported, not failed:")
        for rel, w in auth[:8]:
            print(f"    {rel}  {w}")

    if prod:
        print(f"\nFAIL — {len(prod)} product identifier(s) in tracked content:\n")
        for rel, w in prod:
            print(f"  {rel}\n      {w}")
        print("\nSee PROPRIETARY_IP.md. Root IP documents that RESERVE the claims belong "
              "in tools/separation.allow with a reason.")
        return 1
    print("OK — no product identifiers in tracked content or path names.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
