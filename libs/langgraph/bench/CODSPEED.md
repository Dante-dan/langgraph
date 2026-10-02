# CodSpeed migration reference

The pytest suite shares the existing pyperf workload catalog in `workloads.py`:
fanout to subgraphs (10x/100x), ReAct agents (10x/100x), wide-state, wide-dict,
and Pydantic state (25x300/15x600/9x1200), including checkpointed variants;
sequential graphs (10/1000 nodes); graph compilation; and both serializer
allowlist workloads. Each execution workload is measured synchronously and
asynchronously. First-event latency covers sequential_1000 and
pydantic_state_25x300 in both modes.

Run the suite with `make benchmark-codspeed`. Graph construction, existing input
construction, and uvloop construction happen outside execution measurements.
Async measurements include `run_until_complete`, matching the existing explicit
loop approach; first-event measurements include closing the stream. Each
invocation uses a fresh checkpoint thread ID and the existing
`durability="exit"` configuration. Workload shapes and sizes remain those of the
existing pyperf suite, rather than new benchmark samples.

CodSpeed simulation results are not wall-clock timings. Local execution checks
the benchmark functions and instrumentation; upstream profiling and comparisons
require a CodSpeed CI runner and repository integration. The existing pyperf
entry point, baseline cache, and PR annotations remain until a CodSpeed main
baseline and PR comparison are established. The two suites share workload
objects and compilation builders; they run as separate processes.

The `codspeed.yml` workflow runs simulation measurements on main and pull
requests, and can be dispatched manually. It uses an official setup-python
build and the CodSpeed action, which publishes comparisons and profiles to the
CodSpeed dashboard. The public repository must be connected to CodSpeed for
those uploads and dashboard results. No main baseline, PR comparison, or
flamegraph has been produced by this local reference validation yet.

Integration follows the [official Python guide](https://codspeed.io/docs/benchmarks/python)
and [pytest plugin reference](https://codspeed.io/docs/reference/pytest-codspeed).
