"""Application-level reference for LangGraph issue #6265.

Cache the result and its original token usage, then emit that saved usage from an
uncached presentation node on every invocation. This does not replay live progress
events or execute the expensive node again on a cache hit. Saved usage describes
the computation that produced the cached artifact, not newly billed tokens.

Run from libs/langgraph with: uv run python examples/cached_usage_stream.py
"""

from langgraph.cache.memory import InMemoryCache
from langgraph.checkpoint.memory import InMemorySaver
from typing_extensions import TypedDict

from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph
from langgraph.types import CachePolicy


class State(TypedDict, total=False):
    x: int
    result: int
    token_usage: dict[str, int]


def expensive_node(state: State) -> State:
    print("NOT CACHED")
    return {
        "result": state["x"] * 2,
        "token_usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        },
    }


def cache_key(state: State) -> str:
    return str(state["x"])


def present_usage(state: State) -> None:
    get_stream_writer()({"token_usage": state["token_usage"]})


graph = (
    StateGraph(State)
    .add_node(expensive_node, cache_policy=CachePolicy(key_func=cache_key))
    .add_node(present_usage)
    .set_entry_point("expensive_node")
    .add_edge("expensive_node", "present_usage")
    .set_finish_point("present_usage")
    .compile(cache=InMemoryCache(), checkpointer=InMemorySaver())
)


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "cached-usage-example"}}
    for _ in range(2):
        print(
            list(
                graph.stream({"x": 5}, config=config, stream_mode=["updates", "custom"])
            )
        )
