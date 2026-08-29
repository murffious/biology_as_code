#!/usr/bin/env python3
"""Fixtures for the one primitive the whole SDK rests on."""
import sys
from declared import Declared, weakest_link, Refused, OPEN, NONE, UNGRADED

f = []
def check(cond, msg):
    if not cond:
        f.append(msg)

# the distinction Optional[T] cannot make
o, n = Declared.open(), Declared.none()
check(o != n, "OPEN and NONE must not compare equal — that is the whole point")
check(o.is_open and not o.is_none, "OPEN misclassified")
check(n.is_none and not n.is_open, "NONE misclassified")
check(not o.known and not n.known, "neither OPEN nor NONE is known")

# a missing value must never arrive silently
for d, label in ((o, "OPEN"), (n, "NONE")):
    try:
        d.value(); f.append(f"{label}.value() returned instead of refusing")
    except Refused:
        pass
check(Declared.of(2.1, "B").value() == 2.1, "a known value must come back")

# null is not a state
try:
    Declared.of(None); f.append("null accepted as a state")
except ValueError:
    pass

# opting out has to be explicit
check(o.or_refuse(0.0) == 0.0, "or_refuse should hand back the caller's default")

# weakest link — the iron-two-hosts case: three good values, one OPEN, ungraded
vals = [Declared.of(2.1, "B"), Declared.of(0.0, "B"), Declared.of(620, "A"), Declared.open()]
check(weakest_link(vals) == UNGRADED,
      f"one OPEN input must cap the score at '—', got {weakest_link(vals)!r}")
check(weakest_link(vals[:3]) == "B", "worst of A,B,B is B")
# and averaging must not sneak back in
check(weakest_link([Declared.of(1, "A"), Declared.of(2, "D")]) == "D",
      "weakest link, not mean — D must win over A")

for m in f:
    print("FAIL", m)
print(f"\n{len(f)} failures")
sys.exit(1 if f else 0)
