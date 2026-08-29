# Patent Non-Assertion Covenant

Morf Engineering Inc. holds pending patent claims covering the KIBO product meal
score and the Kibo-vars weighted product composite. Those claims are **not
asserted** against any implementation of the open evaluation layer published in
this repository, specifically:

- the FLOW / `dig` evaluation and bioavailability-gating layer,
- the LAW-SPEC law identifiers and law cards,
- the `MASTER_CROSSWALK.tsv` and the ID spine it encodes (see the scope note
  below -- this covenant concerns patents only and grants no rights in the
  third-party data that table carries), and
- the **FDP-1 provenance declaration format** and its reference validator.

This covenant runs with the specification and survives any change of ownership,
merger, or acquisition. Any successor in interest to the pending claims takes
them subject to this covenant.

The Apache License, Version 2.0 (see `LICENSE`) governs the copyright in this
repository. Its Section 3 grants patent rights only for the contributions
licensed here; it does not, and this covenant does not, grant any license to the
KIBO product meal score, the Kibo-vars composite, their weights, or their tier
badges, none of which are included in this repository. See `PROPRIETARY_IP.md`.

_This is a covenant, not legal advice. For the authoritative terms of use, read
`LICENSE`._

## Scope note -- this covenant is about patents, not about data rights

A non-assertion covenant is a promise not to sue on the pending claims. It is not
a statement of ownership and it conveys no copyright, database right, or licence
in anything listed above.

`MASTER_CROSSWALK.tsv` is specifically affected. Eight of its twelve columns derive
from a Virtual Metabolic Human / Recon3D export whose operative licence this
project has not confirmed and whose own notes record as CC BY-NC 2.0. Listing the
table here means only that the KIBO claims are not asserted against implementations
that use it. It does not mean the table is ours to relicense, and it does not
place the VMH-derived rows under Apache-2.0.

See `NOTICE`, `THIRD-PARTY-DATA.json`, and `MASTER_CROSSWALK.NOTICE.md`.

