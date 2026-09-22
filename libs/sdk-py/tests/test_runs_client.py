from __future__ import annotations

import json

import httpx
import pytest

from langgraph_sdk._async.http import HttpClient
from langgraph_sdk._async.runs import RunsClient
from langgraph_sdk._sync.http import SyncHttpClient
from langgraph_sdk._sync.runs import SyncRunsClient


@pytest.mark.asyncio
async def test_async_insert_input() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/threads/thread_123/runs/run_456/input"
        assert json.loads(request.content) == {"input": {"messages": ["follow up"]}}
        return httpx.Response(202, json={"input_id": "input_789"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        transport=transport, base_url="https://example.com"
    ) as client:
        result = await RunsClient(HttpClient(client)).insert_input(
            "thread_123", "run_456", {"messages": ["follow up"]}
        )

    assert result == {"input_id": "input_789"}


def test_sync_insert_input() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/threads/thread_123/runs/run_456/input"
        assert json.loads(request.content) == {"input": {"messages": ["follow up"]}}
        return httpx.Response(202, json={"input_id": "input_789"})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="https://example.com") as client:
        result = SyncRunsClient(SyncHttpClient(client)).insert_input(
            "thread_123", "run_456", {"messages": ["follow up"]}
        )

    assert result == {"input_id": "input_789"}
