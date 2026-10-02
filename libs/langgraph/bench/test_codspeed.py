"""Initial CodSpeed coverage for existing sequential and serializer workloads."""

from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from uvloop import new_event_loop

from bench.sequential import create_sequential
from bench.serde_allowlist import collect_allowlist_large, collect_allowlist_small


@pytest.mark.parametrize("nodes", [10, 1000], ids=["10", "1000"])
@pytest.mark.parametrize("checkpoint", [False, True], ids=["plain", "checkpoint"])
@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("first_event", [False, True], ids=["full", "first_event"])
def test_sequential(benchmark, nodes, checkpoint, asynchronous, first_event):
    graph = create_sequential(nodes).compile(
        checkpointer=InMemorySaver() if checkpoint else None
    )

    def config():
        return {
            "configurable": {"thread_id": str(uuid4())},
            "recursion_limit": 1000000000,
        }

    def run():
        stream = graph.stream({"messages": []}, config(), durability="exit")
        try:
            if first_event:
                return int(next(stream, None) is not None)
            return sum(1 for _ in stream)
        finally:
            stream.close()

    async def arun():
        stream = graph.astream({"messages": []}, config(), durability="exit")
        count = 0
        try:
            async for _ in stream:
                count += 1
                if first_event:
                    break
            return count
        finally:
            await stream.aclose()

    if asynchronous:
        # Keep loop construction outside the measured invocation, as in pyperf.
        loop = new_event_loop()
        try:
            assert benchmark(lambda: loop.run_until_complete(arun())) > 0
        finally:
            loop.close()
    else:
        assert benchmark(run) > 0


@pytest.mark.parametrize("nodes", [10, 1000], ids=["10", "1000"])
def test_sequential_compilation(benchmark, nodes):
    builder = create_sequential(nodes)
    assert benchmark(builder.compile) is not None


@pytest.mark.parametrize(
    "collect", [collect_allowlist_small, collect_allowlist_large], ids=["small", "large"]
)
def test_serde_allowlist(benchmark, collect):
    benchmark(collect)
