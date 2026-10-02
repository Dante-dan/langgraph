"""CodSpeed measurements of the shared existing pyperf workloads."""

from uuid import uuid4

import pytest
from uvloop import new_event_loop

from bench.serde_allowlist import collect_allowlist_large, collect_allowlist_small
from bench.workloads import benchmarks, compilation_benchmarks


@pytest.mark.parametrize(
    "name,agraph,graph,input", benchmarks, ids=[case[0] for case in benchmarks]
)
@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_execution(benchmark, name, agraph, graph, input, asynchronous):
    _measure(benchmark, agraph if asynchronous else graph, input, asynchronous, False)


@pytest.mark.parametrize(
    "name,agraph,graph,input",
    [
        case
        for case in benchmarks
        if case[0] in ("sequential_1000", "pydantic_state_25x300")
    ],
    ids=["sequential_1000", "pydantic_state_25x300"],
)
@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_first_event_latency(benchmark, name, agraph, graph, input, asynchronous):
    _measure(benchmark, agraph if asynchronous else graph, input, asynchronous, True)


def _measure(benchmark, graph, input, asynchronous, first_event):
    def config():
        return {
            "configurable": {"thread_id": str(uuid4())},
            "recursion_limit": 1000000000,
        }

    def run():
        stream = graph.stream(input, config(), durability="exit")
        try:
            if first_event:
                return int(next(stream, None) is not None)
            return sum(1 for _ in stream)
        finally:
            stream.close()

    async def arun():
        stream = graph.astream(input, config(), durability="exit")
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
        loop = new_event_loop()
        try:
            assert benchmark(lambda: loop.run_until_complete(arun())) > 0
        finally:
            loop.close()
    else:
        assert benchmark(run) > 0


@pytest.mark.parametrize(
    "name,graph",
    compilation_benchmarks,
    ids=[case[0] for case in compilation_benchmarks],
)
def test_compilation(benchmark, name, graph):
    assert benchmark(graph.compile) is not None


@pytest.mark.parametrize(
    "collect",
    [collect_allowlist_small, collect_allowlist_large],
    ids=["small", "large"],
)
def test_serde_allowlist(benchmark, collect):
    benchmark(collect)
