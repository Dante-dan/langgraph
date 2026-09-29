from langgraph.cache.sqlite import SqliteCache


def test_get_preserves_requested_namespace_segments(tmp_path) -> None:
    cache = SqliteCache(path=str(tmp_path / "cache.db"))
    keys = [
        (("__pregel_ns_writes", "example.node", "foo,bar"), "hash1"),
        ((), "hash2"),
    ]
    cache.set({keys[0]: ("comma", None), keys[1]: ("empty", None)})

    assert cache.get(keys) == {keys[0]: "comma", keys[1]: "empty"}


async def test_aget_preserves_requested_namespace_segments(tmp_path) -> None:
    cache = SqliteCache(path=str(tmp_path / "cache.db"))
    key = (("__pregel_ns_writes", "example.node", "foo,bar"), "hash1")
    await cache.aset({key: ("value", None)})

    assert await cache.aget([key]) == {key: "value"}
