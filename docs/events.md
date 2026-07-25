# Events & feedback

The ordered digestion flow is a state machine. The parts of physiology that are *not*
a line — hormonal signaling, feedback loops, cross-system reactions — are naturally
**event-driven**. This layer fans the [digestion engine](digestion.md)'s events out to
subscribers that react in a cascade.

```python
from biology_as_code.events import simulate

trace, reactions = simulate("ex.spinach_salad.with_oil")
[r.type for r in reactions]
# ['chylomicron-export', 'insulin', 'ampk-suppressed']
```

- **`EventBus`** — subscribe handlers to event types, publish events, record the
  cascade. A handler may publish further events; a hard cap keeps a feedback loop from
  running forever.
- **Subscribers** (defaults) — the non-linear systems wired as reactors:
  `portal-glucose → insulin → ampk-suppressed` (a 2nd-order cascade),
  `scfa → ampk-activation` (LAW-026), `mps-signal → mtor-activation`,
  `fat-soluble-vehicle → chylomicron-export` (LAW-045).
- **Fail-closed** — a subscriber fires only on its trigger. No trigger, no reaction —
  never a fabricated signal.

The ordered flow stays `biology_as_code.digest`; the bus is the non-linear layer on
top. In the AWS model the machines already borrow: **Step Functions → EventBridge →
subscribers**. Wiring the fuller signaling systems
(`simulation/signaling_pathways.py`, `simulation/hormonal_energy.py`) as subscribers
is the next step from here.
