"""Reference ToolNode wrapper for an externally idempotent write tool.

This is an opt-in example, not a general exactly-once guarantee. The external
provider MUST enforce the supplied effect key on every write attempt. A durable
claim alone cannot close the write-before-receipt failure window.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from langchain_core.messages import ToolMessage

from langgraph.prebuilt.tool_node import ToolCallRequest


class UnresolvedEffect(RuntimeError):
    """The external outcome is unknown; callers must not retry blindly."""


@dataclass(frozen=True)
class Receipt:
    """Provider-verified effect and the response to show to the model."""

    content: str


@dataclass(frozen=True)
class Reconciliation:
    outcome: Literal["settled", "not_executed", "unknown"]
    receipt: Receipt | None = None


class SqliteClaimStore:
    """Minimal durable claim/receipt store; each operation opens a connection."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS effects ("
                "effect_key TEXT PRIMARY KEY, tool_name TEXT NOT NULL, "
                "arguments TEXT NOT NULL, "
                "state TEXT NOT NULL CHECK (state IN ('claimed', 'settled')), "
                "receipt TEXT)"
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=30)
        try:
            with db:
                yield db
        finally:
            db.close()

    def claim(
        self, effect_key: str, tool_name: str, arguments: str
    ) -> tuple[str, str | None]:
        """Atomically create a claim, or return the existing state and receipt."""
        with self._connect() as db:
            created = db.execute(
                "INSERT OR IGNORE INTO effects VALUES (?, ?, ?, 'claimed', NULL)",
                (effect_key, tool_name, arguments),
            ).rowcount
            row = db.execute(
                "SELECT tool_name, arguments, state, receipt FROM effects WHERE effect_key=?",
                (effect_key,),
            ).fetchone()
            if created:
                return "new", None
            if row[0] != tool_name:
                raise ValueError("effect key already belongs to a different tool")
            if row[1] != arguments:
                raise ValueError("effect key already belongs to different arguments")
            return row[2], row[3]

    def settle(self, effect_key: str, receipt: Receipt) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT state, receipt FROM effects WHERE effect_key=?", (effect_key,)
            ).fetchone()
            if row is None:
                raise ValueError("effect key was never claimed")
            if row[0] == "settled" and row[1] != receipt.content:
                raise ValueError("conflicting settlement receipt")
            db.execute(
                "UPDATE effects SET state='settled', receipt=? WHERE effect_key=?",
                (receipt.content, effect_key),
            )


class DurableEffectWrapper:
    """Build a `ToolNode.wrap_tool_call` handler for one write tool.

    `effect_key` must be a caller-owned business identity, independent of the
    model's tool-call ID. The tool itself must pass that same key to a provider
    with atomic idempotency. `reconcile` must perform an authoritative external
    read; it may return `not_executed` only when that is proven. `authorize`
    checks current authority immediately before every actual attempt.
    """

    def __init__(
        self,
        store: SqliteClaimStore,
        *,
        tool_name: str,
        effect_key: Callable[[ToolCallRequest], str],
        reconcile: Callable[[str, ToolCallRequest], Reconciliation],
        authorize: Callable[[ToolCallRequest], bool],
    ) -> None:
        self.store = store
        self.tool_name = tool_name
        self.effect_key = effect_key
        self.reconcile = reconcile
        self.authorize = authorize

    def __call__(
        self,
        request: ToolCallRequest,
        execute: Callable[[ToolCallRequest], ToolMessage],
    ) -> ToolMessage:
        if request.tool_call["name"] != self.tool_name:
            return execute(request)
        key = self.effect_key(request)
        if not key:
            raise ValueError("write tool requires a stable effect key")
        arguments = json.dumps(
            request.tool_call["args"], sort_keys=True, separators=(",", ":")
        )
        state, saved = self.store.claim(key, self.tool_name, arguments)
        if state == "settled":
            return ToolMessage(
                content=saved or "", tool_call_id=request.tool_call["id"]
            )
        if state == "claimed":
            outcome = self.reconcile(key, request)
            if outcome.outcome == "settled":
                if outcome.receipt is None:
                    raise ValueError("settled reconciliation requires a receipt")
                self.store.settle(key, outcome.receipt)
                return ToolMessage(
                    content=outcome.receipt.content,
                    tool_call_id=request.tool_call["id"],
                )
            if outcome.outcome != "not_executed":
                raise UnresolvedEffect(f"effect {key!r} has an unknown outcome")
        if not self.authorize(request):
            raise PermissionError("write is no longer authorized")
        # An exception here deliberately leaves a claim. Recovery must read the
        # provider, including when the exception appears to be a timeout.
        result = execute(request)
        if not isinstance(result, ToolMessage) or result.status == "error":
            raise UnresolvedEffect(f"effect {key!r} did not return a success receipt")
        self.store.settle(key, Receipt(str(result.content)))
        return result
