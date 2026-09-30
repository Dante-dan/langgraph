# LangGraph SQLite Checkpoint

[![PyPI - Version](https://img.shields.io/pypi/v/langgraph-checkpoint-sqlite?label=%20)](https://pypi.org/project/langgraph-checkpoint-sqlite/#history)
[![PyPI - License](https://img.shields.io/pypi/l/langgraph-checkpoint-sqlite)](https://opensource.org/licenses/MIT)
[![PyPI - Downloads](https://img.shields.io/pepy/dt/langgraph-checkpoint-sqlite)](https://pypistats.org/packages/langgraph-checkpoint-sqlite)
[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/langchain_oss.svg?style=social&label=Follow%20%40LangChain)](https://x.com/langchain_oss)

To help you ship LangGraph apps to production faster, check out [LangSmith](https://www.langchain.com/langsmith).
[LangSmith](https://www.langchain.com/langsmith) is a unified developer platform for building, testing, and monitoring LLM applications.

## Quick Install

```bash
uv add langgraph-checkpoint-sqlite
```

## 🤔 What is this?

This library provides a SQLite implementation of LangGraph's checkpoint saver, with both sync and async support via `aiosqlite`. Use it when you want LangGraph state persistence backed by SQLite for local development, testing, or lightweight deployments.

## 📖 Documentation

For full documentation, see the [API reference](https://reference.langchain.com/python/langgraph.checkpoint.sqlite). For conceptual guides on persistence and memory, see the [LangGraph Docs](https://docs.langchain.com/oss/python/langgraph/overview).

## Security

> [!IMPORTANT]
> Set `LANGGRAPH_STRICT_MSGPACK=true` or pass an explicit `allowed_msgpack_modules` list when creating your checkpointer. This restricts checkpoint deserialization to known-safe types, preventing code execution if the database is compromised. See the [langgraph-checkpoint README](https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint#serde) for details.

### Detecting a removed head checkpoint

`get_tuple()` and `aget_tuple()` accept an optional `expected_checkpoint_id` in the
`configurable` map. On a protected resume, load the latest checkpoint ID for that
`(thread_id, checkpoint_ns)` from a separately protected, durable anchor and pass it
as the expectation:

```python
config = {
    "configurable": {
        "thread_id": thread_id,
        "checkpoint_ns": checkpoint_ns,
        "expected_checkpoint_id": trusted_head_id,
    }
}
checkpoint_tuple = checkpointer.get_tuple(config)
```

If the SQLite head is missing or differs, the read raises
`CheckpointHeadMismatchError` instead of returning an older checkpoint. The same
check applies when `checkpoint_id` requests a historical checkpoint. A missing or
empty expectation is not a protected resume: omitted expectations preserve the
existing behavior, while an explicitly empty value is rejected.

The anchor must be outside the SQLite file and protected against rollback by the
attacker who can edit checkpoints. After each checkpoint write, persist its returned
ID in that anchor before treating the state as committed. If a crash occurs between
the checkpoint write and anchor update, the next protected read rejects the newer
SQLite head; recovery must reconcile the two stores through a trusted procedure.
For an intentional reset or fork, establish a new trusted anchor for the new
thread/namespace before protected reads. This read check does not make checkpoint
and anchor writes atomic or fence concurrent writers; applications must coordinate
those operations themselves.

The check covers `get_tuple()` / `aget_tuple()` (and their `get()` / `aget()`
wrappers), including explicit historical reads. It does not cover `list()` /
`alist()` or graph history enumeration through `get_state_history()` /
`aget_state_history()`: those APIs still enumerate the remaining checkpoints
without checking `expected_checkpoint_id`, even after a head deletion. Use a
protected point read to validate the head before consuming history; that separate
read does not make subsequent enumeration atomic with it.

An expected head ID detects a missing or different head, not changes to the
contents of a row that retains that ID. The proposed checkpoint-identity authenticated-data
work in [#9027](https://github.com/langchain-ai/langgraph/pull/9027) addresses the
complementary case of replaying an older authentic encrypted checkpoint under a
newer ID. This reference alone does not provide that payload authentication, and
payload authentication alone does not detect deletion of the latest checkpoint.

## Usage

```python
from langgraph.checkpoint.sqlite import SqliteSaver

write_config = {"configurable": {"thread_id": "1", "checkpoint_ns": ""}}
read_config = {"configurable": {"thread_id": "1"}}

with SqliteSaver.from_conn_string(":memory:") as checkpointer:
    checkpoint = {
        "v": 4,
        "ts": "2024-07-31T20:14:19.804150+00:00",
        "id": "1ef4f797-8335-6428-8001-8a1503f9b875",
        "channel_values": {"my_key": "meow", "node": "node"},
        "channel_versions": {"__start__": 2, "my_key": 3, "start:node": 3, "node": 3},
        "versions_seen": {
            "__input__": {},
            "__start__": {"__start__": 1},
            "node": {"start:node": 2},
        },
    }

    # store checkpoint
    checkpointer.put(write_config, checkpoint, {}, {})

    # load checkpoint
    checkpointer.get(read_config)

    # list checkpoints
    list(checkpointer.list(read_config))
```

### Async

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
    checkpoint = {
        "v": 4,
        "ts": "2024-07-31T20:14:19.804150+00:00",
        "id": "1ef4f797-8335-6428-8001-8a1503f9b875",
        "channel_values": {"my_key": "meow", "node": "node"},
        "channel_versions": {"__start__": 2, "my_key": 3, "start:node": 3, "node": 3},
        "versions_seen": {
            "__input__": {},
            "__start__": {"__start__": 1},
            "node": {"start:node": 2},
        },
    }

    # store checkpoint
    await checkpointer.aput(write_config, checkpoint, {}, {})

    # load checkpoint
    await checkpointer.aget(read_config)

    # list checkpoints
    [c async for c in checkpointer.alist(read_config)]
```

## 📕 Releases & Versioning

See our [Releases](https://docs.langchain.com/oss/python/release-policy) and [Versioning](https://docs.langchain.com/oss/python/versioning) policies.

## 💁 Contributing

As an open-source project in a rapidly developing field, we are extremely open to contributions, whether it be in the form of a new feature, improved infrastructure, or better documentation.

For detailed information on how to contribute, see the [Contributing Guide](https://docs.langchain.com/oss/python/contributing/overview).
