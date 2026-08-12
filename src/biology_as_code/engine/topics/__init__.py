"""Topic vocabulary → simulation representation."""

from .registry import TopicNode, TopicRegistry, load_topics
from .sim_map import (
    SIM_ROLE_TYPES,
    build_sim_context_template,
    topics_for_system,
    topics_linked_to_law,
)

__all__ = [
    "SIM_ROLE_TYPES",
    "TopicNode",
    "TopicRegistry",
    "build_sim_context_template",
    "load_topics",
    "topics_for_system",
    "topics_linked_to_law",
]
