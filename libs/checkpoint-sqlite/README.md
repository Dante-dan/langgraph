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

## Deleting threads and maintaining the database

`SqliteSaver.delete_thread(thread_id)` and
`await AsyncSqliteSaver.adelete_thread(thread_id)` delete the thread's checkpoint
and pending-write rows across all checkpoint namespaces. They perform logical
row deletion; they do not guarantee erasure of the serialized contents from the
database file, its write-ahead log (WAL), or external copies such as backups.

SQLite can retain deleted contents in free pages and in its WAL. Applications
that need to remove these remnants should plan an explicit maintenance window.
Stop all users of the database, close their connections, and ensure no readers,
writers, or background jobs can reopen it until maintenance finishes. The saver
lock protects only that saver instance; it does not provide this exclusion.

The following examples operate on an **existing, initialized, on-disk checkpoint
database**. They enable SQLite's `secure_delete=ON` on the maintenance connection
before deleting the thread, truncate the WAL, run `VACUUM` to rebuild the database
and remove contents left by earlier deletions, then truncate the WAL again because
`VACUUM` can itself write to the WAL. These operations can be expensive, need
additional disk space, and affect the entire database. Schedule them explicitly
rather than running them automatically after each deletion.

### Synchronous maintenance

```python
from langgraph.checkpoint.sqlite import SqliteSaver


def delete_thread_and_maintain(database: str, thread_id: str) -> None:
    # All other database users must remain stopped throughout this function.
    with SqliteSaver.from_conn_string(database) as saver:
        saver.conn.execute("PRAGMA secure_delete=ON").close()
        saver.delete_thread(thread_id)
        for operation in (
            "PRAGMA wal_checkpoint(TRUNCATE)",
            "VACUUM",
            "PRAGMA wal_checkpoint(TRUNCATE)",
        ):
            cursor = saver.conn.execute(operation)
            result = cursor.fetchone()
            cursor.close()
            if operation.startswith("PRAGMA") and result != (0, 0, 0):
                raise RuntimeError(f"WAL truncation did not complete: {result}")
```

### Asynchronous maintenance

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


async def adelete_thread_and_maintain(database: str, thread_id: str) -> None:
    # All other database users must remain stopped throughout this function.
    async with AsyncSqliteSaver.from_conn_string(database) as saver:
        async with saver.conn.execute("PRAGMA secure_delete=ON"):
            pass
        await saver.adelete_thread(thread_id)
        for operation in (
            "PRAGMA wal_checkpoint(TRUNCATE)",
            "VACUUM",
            "PRAGMA wal_checkpoint(TRUNCATE)",
        ):
            async with saver.conn.execute(operation) as cursor:
                result = await cursor.fetchone()
            if operation.startswith("PRAGMA") and result != (0, 0, 0):
                raise RuntimeError(f"WAL truncation did not complete: {result}")
```

A busy checkpoint may return a result instead of raising an exception. Both
examples check the result and raise if truncation did not complete. If any step
fails, deletion may already have committed: keep database users stopped, resolve
the error, and retry maintenance. Do not report physical cleanup as complete just
because the deletion method returned.

This maintenance concerns SQLite's current database and WAL files. It is not a
secure-erasure guarantee for storage media, filesystem snapshots, backups,
replicas, exported checkpoints, or other copies. Those require their own retention
and deletion policies. It does not manage `SqliteStore` data or vector tables.

See SQLite's documentation for [`secure_delete`](https://www.sqlite.org/pragma.html#pragma_secure_delete),
[`wal_checkpoint`](https://www.sqlite.org/pragma.html#pragma_wal_checkpoint), and
[`VACUUM`](https://www.sqlite.org/lang_vacuum.html).

## 📕 Releases & Versioning

See our [Releases](https://docs.langchain.com/oss/python/release-policy) and [Versioning](https://docs.langchain.com/oss/python/versioning) policies.

## 💁 Contributing

As an open-source project in a rapidly developing field, we are extremely open to contributions, whether it be in the form of a new feature, improved infrastructure, or better documentation.

For detailed information on how to contribute, see the [Contributing Guide](https://docs.langchain.com/oss/python/contributing/overview).
