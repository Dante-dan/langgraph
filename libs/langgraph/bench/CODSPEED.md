# CodSpeed migration reference

This initial suite covers sequential graphs (10 and 1000 nodes), synchronous and
asynchronous execution, checkpointed variants, first-event latency, compilation,
and both serializer allowlist workloads. The existing pyperf entry point remains
available; the fanout, agent, wide-state, wide-dict, and Pydantic workloads still
need migration before this suite can replace it.

Run the suite with `make benchmark-codspeed`. Graph construction and uvloop
construction happen outside execution measurements. Async measurements include
`run_until_complete`, matching the existing explicit-loop approach; first-event
measurements include closing the stream. Each invocation uses a fresh checkpoint
thread ID and the existing `durability="exit"` configuration.

CodSpeed simulation results are not wall-clock timings. Local execution checks
the benchmark functions and instrumentation; upstream profiling and comparisons
require a CodSpeed CI runner and repository integration. The existing baseline
cache and PR annotations remain until the complete suite and CodSpeed baseline
are established.
