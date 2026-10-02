"""End-to-end tests for `TracePolicy` input processing on node trace runs."""

from typing import Any

import pytest
from langsmith._internal._serde import dumps_json
from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send, TracePolicy
from tests.fake_tracer import FakeTracer, Run


class State(TypedDict):
    value: int


def _node_run(tracer: FakeTracer, name: str) -> Run:
    return next(r for r in tracer.flattened_runs() if r.name == name)


def _incr(state: State) -> State:
    return {"value": state["value"] + 1}


def test_trace_policy_transforms_recorded_inputs() -> None:
    seen: dict[str, Any] = {}

    def process_inputs(inp: Any) -> Any:
        seen["inputs"] = inp
        return {"scrubbed_in": True}

    graph = (
        StateGraph(State)
        .add_node("n", _incr, trace_policy=TracePolicy(process_inputs=process_inputs))
        .add_edge(START, "n")
        .add_edge("n", END)
        .compile()
    )

    tracer = FakeTracer()
    # the real graph output is unaffected by the trace policy
    assert graph.invoke({"value": 1}, {"callbacks": [tracer]}) == {"value": 2}

    run = _node_run(tracer, "n")
    # the recorded input is transformed; the output is recorded as-is
    assert run.inputs == {"scrubbed_in": True}
    assert run.outputs == {"value": 2}
    # process_inputs observed the real, untransformed input
    assert seen["inputs"] == {"value": 1}


def test_trace_policy_transforms_recorded_outputs() -> None:
    seen: dict[str, Any] = {}

    def process_outputs(out: Any) -> Any:
        seen["outputs"] = out
        return {"scrubbed_out": True}

    graph = (
        StateGraph(State)
        .add_node("n", _incr, trace_policy=TracePolicy(process_outputs=process_outputs))
        .add_edge(START, "n")
        .add_edge("n", END)
        .compile()
    )

    tracer = FakeTracer()
    # the real graph output is unaffected by the trace policy
    assert graph.invoke({"value": 1}, {"callbacks": [tracer]}) == {"value": 2}

    run = _node_run(tracer, "n")
    # the recorded output is transformed; the input is recorded as-is
    assert run.inputs == {"value": 1}
    assert run.outputs == {"scrubbed_out": True}
    # process_outputs observed the real, untransformed output
    assert seen["outputs"] == {"value": 2}


def test_trace_policy_none_records_real_payloads() -> None:
    graph = (
        StateGraph(State)
        .add_node("n", _incr)
        .add_edge(START, "n")
        .add_edge("n", END)
        .compile()
    )

    tracer = FakeTracer()
    assert graph.invoke({"value": 1}, {"callbacks": [tracer]}) == {"value": 2}

    run = _node_run(tracer, "n")
    assert run.inputs == {"value": 1}
    assert run.outputs == {"value": 2}


def test_trace_policy_processor_error_safe_without_callbacks() -> None:
    def boom(_inp: Any) -> Any:
        raise RuntimeError("processor failed")

    graph = (
        StateGraph(State)
        .add_node("n", _incr, trace_policy=TracePolicy(process_inputs=boom))
        .add_edge(START, "n")
        .add_edge("n", END)
        .compile()
    )

    # no callbacks: the processor still runs but is fail-open, so execution is unaffected
    assert graph.invoke({"value": 1}) == {"value": 2}


def test_trace_policy_processor_error_does_not_break_execution() -> None:
    def boom(_inp: Any) -> Any:
        raise RuntimeError("processor failed")

    graph = (
        StateGraph(State)
        .add_node("n", _incr, trace_policy=TracePolicy(process_inputs=boom))
        .add_edge(START, "n")
        .add_edge("n", END)
        .compile()
    )

    tracer = FakeTracer()
    # a raising processor must not abort the node; the untransformed input is recorded
    assert graph.invoke({"value": 1}, {"callbacks": [tracer]}) == {"value": 2}
    assert _node_run(tracer, "n").inputs == {"value": 1}


@pytest.mark.anyio
async def test_trace_policy_transforms_recorded_inputs_async() -> None:
    graph = (
        StateGraph(State)
        .add_node(
            "n",
            _incr,
            trace_policy=TracePolicy(process_inputs=lambda _: {"scrubbed_in": True}),
        )
        .add_edge(START, "n")
        .add_edge("n", END)
        .compile()
    )

    tracer = FakeTracer()
    assert await graph.ainvoke({"value": 5}, {"callbacks": [tracer]}) == {"value": 6}

    run = _node_run(tracer, "n")
    assert run.inputs == {"scrubbed_in": True}
    assert run.outputs == {"value": 6}


@pytest.mark.parametrize("as_list", [False, True])
def test_conditional_send_trace_omits_arguments(as_list: bool) -> None:
    class Sensitive:
        def __repr__(self) -> str:
            raise AssertionError("Send argument must not be rendered for edge tracing")

    payload = {"value": 7, "sensitive": Sensitive()}
    received: list[Any] = []

    def route(state: State) -> Any:
        send = Send("worker", payload)
        return [send, Send("worker2", payload)] if as_list else send

    def worker(arg: Any) -> State:
        received.append(arg)
        return {"value": arg["value"]}

    graph = (
        StateGraph(State)
        .add_node("worker", worker)
        .add_node("worker2", lambda arg: {})
        .add_conditional_edges(START, route, ["worker", "worker2"])
        .add_edge("worker", END)
        .compile()
    )
    tracer = FakeTracer()
    assert graph.invoke({"value": 1}, {"callbacks": [tracer]}) == {"value": 7}
    assert received == [payload]
    assert received[0] is payload
    output = _node_run(tracer, "route").outputs
    serialized = dumps_json(output)
    assert b"sensitive" not in serialized
    assert b"arg" not in serialized
    expected = {
        "type": "Send",
        "node": "worker",
    }
    assert output == (
        expected
        if not as_list
        else {"output": [expected, {"type": "Send", "node": "worker2"}]}
    )


@pytest.mark.anyio
async def test_async_conditional_send_trace_preserves_routing() -> None:
    payload = {"value": 8, "history": "sensitive" * 1000}
    received: list[Any] = []

    async def route(state: State) -> list[Send]:
        return [Send("worker", payload, timeout=10)]

    async def worker(arg: Any) -> State:
        received.append(arg)
        return {"value": arg["value"]}

    graph = (
        StateGraph(State)
        .add_node("worker", worker)
        .add_conditional_edges(START, route, ["worker"])
        .add_edge("worker", END)
        .compile()
    )
    tracer = FakeTracer()
    assert await graph.ainvoke({"value": 1}, {"callbacks": [tracer]}) == {"value": 8}
    assert received[0] is payload
    output = _node_run(tracer, "route").outputs
    assert output == {
        "output": [
            {
                "type": "Send",
                "node": "worker",
                "timeout": {
                    "run_timeout": 10.0,
                    "idle_timeout": None,
                    "refresh_on": "auto",
                },
            }
        ]
    }
    before = dumps_json(output)
    payload["history"] *= 10
    tracer = FakeTracer()
    await graph.ainvoke({"value": 1}, {"callbacks": [tracer]})
    assert dumps_json(_node_run(tracer, "route").outputs) == before


@pytest.mark.parametrize("as_tuple", [False, True])
def test_conditional_string_trace_unchanged(as_tuple: bool) -> None:
    def route(state: State) -> Any:
        return ("worker",) if as_tuple else "worker"

    graph = (
        StateGraph(State)
        .add_node("worker", _incr)
        .add_conditional_edges(START, route)
        .add_edge("worker", END)
        .compile()
    )
    tracer = FakeTracer()
    assert graph.invoke({"value": 1}, {"callbacks": [tracer]}) == {"value": 2}
    assert _node_run(tracer, "route").outputs == {
        "output": ("worker",) if as_tuple else "worker"
    }
