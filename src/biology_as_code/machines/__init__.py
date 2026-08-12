"""
Open declarative digestion machines — a teaching layer for ``biology_as_code``.

Each GI stage is a versioned, inspectable JSON state graph (states, transitions,
edge cases, teaching time windows) instead of hard-coded procedure — "biology as
code." Open FLOW tier only: these carry **no** product-score / vendor-scoring hooks.

    from biology_as_code.machines import list_machines, get_machine, validate_all

    list_machines()                 # 8 stages: oral, stomach, duodenum, jejunum,
                                    # portal, systemic, cell, colon (+ process.full-digest)
    m = get_machine('stage.stomach')
    m['states']['emptyingControl']  # inspect the branch logic
    validate_all()['ok']            # True
"""

from biology_as_code.machines.digestion import (
    digestion_stage_ids,
    meal_to_context,
    run_digestion,
)
from biology_as_code.machines.executor import match, trace
from biology_as_code.machines.loader import (
    get_machine,
    list_machines,
    load_registry,
    machine_path,
)
from biology_as_code.machines.validate import content_hash, validate_all, validate_machine

__all__ = [
    "content_hash",
    "digestion_stage_ids",
    "get_machine",
    "list_machines",
    "load_registry",
    "machine_path",
    "match",
    "meal_to_context",
    "run_digestion",
    "trace",
    "validate_all",
    "validate_machine",
]
