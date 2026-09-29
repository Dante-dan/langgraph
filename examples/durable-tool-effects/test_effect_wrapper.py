"""Offline regression cases for the opt-in ToolNode effect wrapper example."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from effect_wrapper import (
    DurableEffectWrapper,
    Receipt,
    Reconciliation,
    SqliteClaimStore,
    UnresolvedEffect,
)
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool

from langgraph.prebuilt import ToolNode


def invoke(node, call):
    runtime = Mock()
    runtime.store = None
    runtime.context = None
    runtime.stream_writer = lambda _: None
    return node.invoke(
        {"messages": [AIMessage("", tool_calls=[call])]},
        config={"configurable": {"__pregel_runtime": runtime}},
    )


def test_lost_response_reconciles_without_second_write(tmp_path):
    effects = {}
    calls = []
    allowed = True

    @tool
    def charge(order_id: str) -> str:
        """Make a fake externally idempotent charge."""
        calls.append(order_id)
        effects.setdefault(order_id, f"charged {order_id}")
        if len(calls) == 1:
            raise TimeoutError("provider committed, response lost")
        return effects[order_id]

    store_path = tmp_path / "effects.sqlite"

    def make_node():
        wrapper = DurableEffectWrapper(
            SqliteClaimStore(store_path),
            tool_name="charge",
            effect_key=lambda request: request.tool_call["args"]["order_id"],
            reconcile=lambda key, _request: (
                Reconciliation("settled", Receipt(effects[key]))
                if key in effects
                else Reconciliation("not_executed")
            ),
            authorize=lambda _request: allowed,
        )
        return ToolNode([charge], wrap_tool_call=wrapper)

    first = {
        "name": "charge",
        "args": {"order_id": "o988"},
        "id": "call-1",
        "type": "tool_call",
    }
    with pytest.raises(TimeoutError):
        invoke(make_node(), first)

    # A restarted process and a model re-plan both use a new call ID.
    second = {**first, "id": "call-2"}
    output = invoke(make_node(), second)
    assert output["messages"][0].content == "charged o988"
    assert output["messages"][0].tool_call_id == "call-2"
    assert calls == ["o988"]

    allowed = False
    assert invoke(make_node(), second)["messages"][0].content == "charged o988"
    assert calls == ["o988"]


def test_unknown_outcome_fails_closed_and_revoked_authority_blocks_retry(tmp_path):
    calls = []
    result = Reconciliation("unknown")
    allowed = True

    @tool
    def charge(order_id: str) -> str:
        """Make a fake charge."""
        calls.append(order_id)
        if len(calls) == 1:
            raise TimeoutError("outcome unknown")
        return "charged"

    wrapper = DurableEffectWrapper(
        SqliteClaimStore(tmp_path / "effects.sqlite"),
        tool_name="charge",
        effect_key=lambda request: request.tool_call["args"]["order_id"],
        reconcile=lambda _key, _request: result,
        authorize=lambda _request: allowed,
    )
    node = ToolNode([charge], wrap_tool_call=wrapper)
    call = {
        "name": "charge",
        "args": {"order_id": "o988"},
        "id": "call-1",
        "type": "tool_call",
    }
    with pytest.raises(TimeoutError):
        invoke(node, call)
    with pytest.raises(UnresolvedEffect):
        invoke(node, {**call, "id": "call-2"})
    assert calls == ["o988"]

    result = Reconciliation("not_executed")
    allowed = False
    with pytest.raises(PermissionError):
        invoke(node, {**call, "id": "call-3"})
    assert calls == ["o988"]


def test_distinct_keys_execute_and_settle_independently(tmp_path):
    calls = []

    @tool
    def charge(order_id: str) -> str:
        """Make a fake charge."""
        calls.append(order_id)
        return f"charged {order_id}"

    wrapper = DurableEffectWrapper(
        SqliteClaimStore(tmp_path / "effects.sqlite"),
        tool_name="charge",
        effect_key=lambda request: request.tool_call["args"]["order_id"],
        reconcile=lambda _key, _request: Reconciliation("unknown"),
        authorize=lambda _request: True,
    )
    node = ToolNode([charge], wrap_tool_call=wrapper)
    for order in ("o1", "o2", "o1"):
        call = {
            "name": "charge",
            "args": {"order_id": order},
            "id": f"call-{len(calls)}",
            "type": "tool_call",
        }
        assert isinstance(invoke(node, call)["messages"][0], ToolMessage)
    assert calls == ["o1", "o2"]
