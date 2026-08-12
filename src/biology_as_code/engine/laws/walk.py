"""Walk a pathway graph applying enhancers / inhibitors / gates."""

from __future__ import annotations

from collections.abc import Mapping

from .models import Modifier, PathwayNode, WalkResult, WalkState


def _active(mod: Modifier, ctx: Mapping[str, object]) -> bool:
    if mod.requires_context is None:
        return False
    return bool(ctx.get(mod.requires_context))


def _apply_modifiers(
    node: PathwayNode,
    state: WalkState,
    prior_product: float,
    fired: list[str],
) -> float:
    """Return updated prior_product."""
    for mod in node.inhibitors:
        if not _active(mod, state.context):
            continue
        mag = mod.magnitude if mod.magnitude is not None else 0.7
        state.yield_factor *= mag
        prior_product *= mod.prior
        fired.append(mod.id)
        state.log.append(
            f"{node.id}: inhibitor {mod.nutrient} ({mod.law_id}) "
            f"×{mag:.3f} prior={mod.prior:.2f} → yield={state.yield_factor:.4f}"
        )
    for mod in node.enhancers:
        if not _active(mod, state.context):
            continue
        mag = mod.magnitude if mod.magnitude is not None else 1.3
        state.yield_factor *= mag
        prior_product *= mod.prior
        fired.append(mod.id)
        state.log.append(
            f"{node.id}: enhancer {mod.nutrient} ({mod.law_id}) "
            f"×{mag:.3f} prior={mod.prior:.2f} → yield={state.yield_factor:.4f}"
        )
    return prior_product


def walk_pathway(
    nodes: Mapping[str, PathwayNode],
    start: str,
    *,
    context: Mapping[str, object] | None = None,
    cargo: str = "cargo",
    max_steps: int = 32,
    follow: str = "first",
) -> WalkResult:
    """
    Walk from start following next_pathways.

    follow:
      - "first": take next_pathways[0] each time (deterministic spine)
      - "all_product": not implemented as multi-path merge; use first for now

    Gate: if node.is_gate and gate closed → block (yield 0).
    """
    if start not in nodes:
        raise KeyError(f"unknown start node {start}")

    state = WalkState(cargo=cargo, context=dict(context or {}))
    prior_product = 1.0
    fired: list[str] = []
    cur: str | None = start
    steps = 0
    end: str | None = None

    while cur is not None and steps < max_steps:
        steps += 1
        node = nodes[cur]
        state.path.append(cur)
        state.log.append(f"enter {cur} ({node.label})")

        if node.is_gate:
            key = node.gate_context_key
            if key is None:
                open_ = node.gate_default_open
            elif key in state.context:
                open_ = bool(state.context[key])
            else:
                open_ = node.gate_default_open
            if not open_:
                state.blocked = True
                state.block_reason = f"gate closed at {cur} (key={key})"
                state.yield_factor = 0.0
                state.log.append(state.block_reason)
                end = cur
                break

        prior_product = _apply_modifiers(node, state, prior_product, fired)

        # optional node prior for human evidence
        if "human_evidence" in node.priors:
            prior_product *= float(node.priors["human_evidence"])

        if not node.next_pathways:
            end = cur
            state.log.append(f"terminus {cur}")
            break

        nxt = node.next_pathways[0] if follow in ("first", "all_product") else node.next_pathways[0]
        if nxt not in nodes:
            state.blocked = True
            state.block_reason = f"dangling next_pathway {nxt} from {cur}"
            state.log.append(state.block_reason)
            end = cur
            break
        cur = nxt

    if end is None and state.path:
        end = state.path[-1]

    return WalkResult(
        start=start,
        end=end,
        yield_factor=state.yield_factor,
        path=list(state.path),
        log=list(state.log),
        blocked=state.blocked,
        block_reason=state.block_reason,
        prior_product=prior_product,
        modifiers_fired=fired,
    )


def collect_reachable(nodes: Mapping[str, PathwayNode], start: str) -> set[str]:
    seen: set[str] = set()
    stack = [start]
    while stack:
        n = stack.pop()
        if n in seen or n not in nodes:
            continue
        seen.add(n)
        stack.extend(nodes[n].next_pathways)
    return seen
