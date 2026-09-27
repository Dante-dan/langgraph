"""Private payload channel for LangGraph's message stream callback."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

NO_RAW_PAYLOAD = object()
raw_node_payload_value: ContextVar[Any] = ContextVar(
    "langgraph_raw_node_payload", default=NO_RAW_PAYLOAD
)


@contextmanager
def raw_node_payload(value: Any) -> Iterator[None]:
    """Expose an untransformed node payload only during callback dispatch."""
    token = raw_node_payload_value.set(value)
    try:
        yield
    finally:
        raw_node_payload_value.reset(token)
