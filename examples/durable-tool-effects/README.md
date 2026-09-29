# Durable write-tool effects: bounded reference

This example uses `ToolNode.wrap_tool_call` without changing LangGraph's default
tool execution. It addresses a narrow case: a write tool with a caller-supplied
business effect key and an external provider that atomically enforces that key
on every write attempt. The example's SQLite database stores claims and
settlement receipts across process restarts. It is **not** an exactly-once
guarantee for arbitrary tools.

The adapter must supply:

- `effect_key(request)`: a stable operation identity such as `charge:o988`.
  A model's tool-call ID changes when the model plans a new call; a hash of
  arguments is not a substitute for business identity. The store rejects the
  same key with a different tool name or different effective arguments.
- `reconcile(key, request)`: an authoritative provider read. Return `settled`
  with a receipt only when the effect is proven. Return `not_executed` only
  when absence is proven; otherwise return `unknown` and surface the
  `UnresolvedEffect` exception. Reconciliation never authorizes a write.
- `authorize(request)`: a fresh authority check before each actual execution.
  In production, the external provider must also enforce the authorization
  and idempotency key at the effect boundary. This callback is illustrative;
  it is not a durable one-shot permit or a substitute for provider policy.

On first use, the wrapper claims the key before executing. A successful tool
response is stored as a receipt. If a process dies or times out after the
external write and before local settlement, the next invocation reconciles
the provider. A proven existing effect is returned to the current tool-call
ID without a second write. An unknown outcome fails closed. If the provider
proves no effect, the wrapper checks current authority before attempting the
same externally idempotent operation again.

The reference handles synchronous `ToolMessage` results only. It does not
cover `Command` results, async tools, storage migrations, provider-specific
receipt serialization, or application-specific permits. These are decisions
for a maintainer-approved public API. The small fake-provider tests exercise
lost response/restart, a new tool-call ID, unknown outcome, revoked authority,
and independent keys:

```sh
cd libs/prebuilt
uv run pytest ../../examples/durable-tool-effects/test_effect_wrapper.py
```
