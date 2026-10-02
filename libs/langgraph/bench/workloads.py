"""Shared existing pyperf and CodSpeed workload catalog."""

import random

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from bench.fanout_to_subgraph import fanout_to_subgraph, fanout_to_subgraph_sync
from bench.pydantic_state import pydantic_state
from bench.react_agent import react_agent
from bench.sequential import create_sequential
from bench.wide_dict import wide_dict
from bench.wide_state import wide_state

benchmarks = (
    (
        "fanout_to_subgraph_10x",
        fanout_to_subgraph().compile(checkpointer=None),
        fanout_to_subgraph_sync().compile(checkpointer=None),
        {
            "subjects": [
                random.choices("abcdefghijklmnopqrstuvwxyz", k=1000) for _ in range(10)
            ]
        },
    ),
    (
        "fanout_to_subgraph_10x_checkpoint",
        fanout_to_subgraph().compile(checkpointer=InMemorySaver()),
        fanout_to_subgraph_sync().compile(checkpointer=InMemorySaver()),
        {
            "subjects": [
                random.choices("abcdefghijklmnopqrstuvwxyz", k=1000) for _ in range(10)
            ]
        },
    ),
    (
        "fanout_to_subgraph_100x",
        fanout_to_subgraph().compile(checkpointer=None),
        fanout_to_subgraph_sync().compile(checkpointer=None),
        {
            "subjects": [
                random.choices("abcdefghijklmnopqrstuvwxyz", k=1000) for _ in range(100)
            ]
        },
    ),
    (
        "fanout_to_subgraph_100x_checkpoint",
        fanout_to_subgraph().compile(checkpointer=InMemorySaver()),
        fanout_to_subgraph_sync().compile(checkpointer=InMemorySaver()),
        {
            "subjects": [
                random.choices("abcdefghijklmnopqrstuvwxyz", k=1000) for _ in range(100)
            ]
        },
    ),
    (
        "react_agent_10x",
        react_agent(10, checkpointer=None),
        react_agent(10, checkpointer=None),
        {"messages": [HumanMessage("hi?")]},
    ),
    (
        "react_agent_10x_checkpoint",
        react_agent(10, checkpointer=InMemorySaver()),
        react_agent(10, checkpointer=InMemorySaver()),
        {"messages": [HumanMessage("hi?")]},
    ),
    (
        "react_agent_100x",
        react_agent(100, checkpointer=None),
        react_agent(100, checkpointer=None),
        {"messages": [HumanMessage("hi?")]},
    ),
    (
        "react_agent_100x_checkpoint",
        react_agent(100, checkpointer=InMemorySaver()),
        react_agent(100, checkpointer=InMemorySaver()),
        {"messages": [HumanMessage("hi?")]},
    ),
    (
        "wide_state_25x300",
        wide_state(300).compile(checkpointer=None),
        wide_state(300).compile(checkpointer=None),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(5)
                    }
                    for i in range(5)
                }
            ]
        },
    ),
    (
        "wide_state_25x300_checkpoint",
        wide_state(300).compile(checkpointer=InMemorySaver()),
        wide_state(300).compile(checkpointer=InMemorySaver()),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(5)
                    }
                    for i in range(5)
                }
            ]
        },
    ),
    (
        "wide_state_15x600",
        wide_state(600).compile(checkpointer=None),
        wide_state(600).compile(checkpointer=None),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(5)
                    }
                    for i in range(3)
                }
            ]
        },
    ),
    (
        "wide_state_15x600_checkpoint",
        wide_state(600).compile(checkpointer=InMemorySaver()),
        wide_state(600).compile(checkpointer=InMemorySaver()),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(5)
                    }
                    for i in range(3)
                }
            ]
        },
    ),
    (
        "wide_state_9x1200",
        wide_state(1200).compile(checkpointer=None),
        wide_state(1200).compile(checkpointer=None),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(3)
                    }
                    for i in range(3)
                }
            ]
        },
    ),
    (
        "wide_state_9x1200_checkpoint",
        wide_state(1200).compile(checkpointer=InMemorySaver()),
        wide_state(1200).compile(checkpointer=InMemorySaver()),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(3)
                    }
                    for i in range(3)
                }
            ]
        },
    ),
    (
        "wide_dict_25x300",
        wide_dict(300).compile(checkpointer=None),
        wide_dict(300).compile(checkpointer=None),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(5)
                    }
                    for i in range(5)
                }
            ]
        },
    ),
    (
        "wide_dict_25x300_checkpoint",
        wide_dict(300).compile(checkpointer=InMemorySaver()),
        wide_dict(300).compile(checkpointer=InMemorySaver()),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(5)
                    }
                    for i in range(5)
                }
            ]
        },
    ),
    (
        "wide_dict_15x600",
        wide_dict(600).compile(checkpointer=None),
        wide_dict(600).compile(checkpointer=None),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(5)
                    }
                    for i in range(3)
                }
            ]
        },
    ),
    (
        "wide_dict_15x600_checkpoint",
        wide_dict(600).compile(checkpointer=InMemorySaver()),
        wide_dict(600).compile(checkpointer=InMemorySaver()),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(5)
                    }
                    for i in range(3)
                }
            ]
        },
    ),
    (
        "wide_dict_9x1200",
        wide_dict(1200).compile(checkpointer=None),
        wide_dict(1200).compile(checkpointer=None),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(3)
                    }
                    for i in range(3)
                }
            ]
        },
    ),
    (
        "wide_dict_9x1200_checkpoint",
        wide_dict(1200).compile(checkpointer=InMemorySaver()),
        wide_dict(1200).compile(checkpointer=InMemorySaver()),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(3)
                    }
                    for i in range(3)
                }
            ]
        },
    ),
    (
        "sequential_10",
        create_sequential(10).compile(),
        create_sequential(10).compile(),
        {"messages": []},  # Empty list of messages
    ),
    (
        "sequential_1000",
        create_sequential(1000).compile(),
        create_sequential(1000).compile(),
        {"messages": []},  # Empty list of messages
    ),
    (
        "pydantic_state_25x300",
        pydantic_state(300).compile(checkpointer=None),
        pydantic_state(300).compile(checkpointer=None),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(5)
                    }
                    for i in range(5)
                }
            ]
        },
    ),
    (
        "pydantic_state_25x300_checkpoint",
        pydantic_state(300).compile(checkpointer=InMemorySaver()),
        pydantic_state(300).compile(checkpointer=InMemorySaver()),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(5)
                    }
                    for i in range(5)
                }
            ]
        },
    ),
    (
        "pydantic_state_15x600",
        pydantic_state(600).compile(checkpointer=None),
        pydantic_state(600).compile(checkpointer=None),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(5)
                    }
                    for i in range(3)
                }
            ]
        },
    ),
    (
        "pydantic_state_15x600_checkpoint",
        pydantic_state(600).compile(checkpointer=InMemorySaver()),
        pydantic_state(600).compile(checkpointer=InMemorySaver()),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(5)
                    }
                    for i in range(3)
                }
            ]
        },
    ),
    (
        "pydantic_state_9x1200",
        pydantic_state(1200).compile(checkpointer=None),
        pydantic_state(1200).compile(checkpointer=None),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(3)
                    }
                    for i in range(3)
                }
            ]
        },
    ),
    (
        "pydantic_state_9x1200_checkpoint",
        pydantic_state(1200).compile(checkpointer=InMemorySaver()),
        pydantic_state(1200).compile(checkpointer=InMemorySaver()),
        {
            "messages": [
                {
                    str(i) * 10: {
                        str(j) * 10: ["hi?" * 10, True, 1, 6327816386138, None] * 5
                        for j in range(3)
                    }
                    for i in range(3)
                }
            ]
        },
    ),
)

compilation_benchmarks = (
    (
        "sequential_1000",
        create_sequential(1_000),
    ),
    (
        "pydantic_state_25x300",
        pydantic_state(300),
    ),
    (
        "wide_state_15x600",
        wide_state(600),
    ),
)
