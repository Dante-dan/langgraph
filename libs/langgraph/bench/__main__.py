from uuid import uuid4

from pyperf._runner import Runner
from uvloop import new_event_loop

from bench.serde_allowlist import collect_allowlist_large, collect_allowlist_small
from bench.workloads import benchmarks, compilation_benchmarks
from langgraph.graph import StateGraph
from langgraph.pregel import Pregel


async def arun(graph: Pregel, input: dict):
    len(
        [
            c
            async for c in graph.astream(
                input,
                {
                    "configurable": {"thread_id": str(uuid4())},
                    "recursion_limit": 1000000000,
                },
                durability="exit",
            )
        ]
    )


async def arun_first_event_latency(graph: Pregel, input: dict) -> None:
    """Latency for the first event.

    Run the graph until the first event is processed and then stop.
    """
    stream = graph.astream(
        input,
        {
            "configurable": {"thread_id": str(uuid4())},
            "recursion_limit": 1000000000,
        },
        durability="exit",
    )

    try:
        async for _ in stream:
            break
    finally:
        await stream.aclose()


def run(graph: Pregel, input: dict):
    len(
        [
            c
            for c in graph.stream(
                input,
                {
                    "configurable": {"thread_id": str(uuid4())},
                    "recursion_limit": 1000000000,
                },
                durability="exit",
            )
        ]
    )


def run_first_event_latency(graph: Pregel, input: dict) -> None:
    """Latency for the first event.

    Run the graph until the first event is processed and then stop.
    """
    stream = graph.stream(
        input,
        {
            "configurable": {"thread_id": str(uuid4())},
            "recursion_limit": 1000000000,
        },
        durability="exit",
    )

    try:
        for _ in stream:
            break
    finally:
        stream.close()


def compile_graph(graph: StateGraph) -> None:
    """Compile the graph."""
    graph.compile()


r = Runner()

# Full graph run time
for name, agraph, graph, input in benchmarks:
    r.bench_async_func(name, arun, agraph, input, loop_factory=new_event_loop)
    if graph is not None:
        r.bench_func(name + "_sync", run, graph, input)


# Pick a handful of graphs to measure the first event latency.
# At the moment, limiting just due to the size of the annotation on github.
GRAPHS_FOR_1st_EVENT_LATENCY = (
    "sequential_1000",
    "pydantic_state_25x300",
)

# First event latency
for name, agraph, graph, input in benchmarks:
    if graph not in GRAPHS_FOR_1st_EVENT_LATENCY:
        continue
    r.bench_async_func(
        name + "_first_event_latency",
        arun_first_event_latency,
        agraph,
        input,
        loop_factory=new_event_loop,
    )
    if graph is not None:
        r.bench_func(
            name + "_first_event_latency_sync", run_first_event_latency, graph, input
        )

# Graph compilation times

for name, graph in compilation_benchmarks:
    r.bench_func(name + "_compilation", compile_graph, graph)

# Serde allowlist collection
r.bench_func("serde_allowlist_small", collect_allowlist_small)
r.bench_func("serde_allowlist_large", collect_allowlist_large)
