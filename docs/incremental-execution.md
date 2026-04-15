# Incremental Tau Execution Prototype

This document records a future-work experiment for Tau normalization and
satisfiability performance. It is not an upstream Tau feature.

## Goal

The experiment tests a small executable version of this idea:

```text
static read analysis + partial evaluation + single-key update
```

If a Tau expression does not read the input key that changed, its old cached
value can be reused. If the expression does read that key, only the affected
ancestor sub-expressions need recomputation.

## Semantic Contract

For an expression `e`, write:

```text
Reads(e)
```

for the set of input keys that `e` depends on.

The core law is:

```text
k notin Reads(e)
and env and env' agree on Reads(e)
implies eval(env,e) = eval(env',e).
```

Standard reading:

- If key `k` is not in the read set of expression `e`, and the old and new
  environments agree on every key read by `e`, then evaluating `e` in the old
  environment gives the same value as evaluating `e` in the new environment.

Plain English:

- Do not recompute an expression when the changed input is irrelevant to it.

The partial-evaluation law is:

```text
eval(env, partialEval(K,e)) = eval(env,e)
```

provided `env` agrees with the compile-time known map `K`.

Standard reading:

- Replacing known variables by constants preserves the denotation of `e` in any
  environment compatible with those known values.

Plain English:

- If a configuration input is already known, compile it away.

## Lean Proof Artifact

The local proof packet `tau_incremental_execution_frontier_2026_04_15` closes the
small semantic kernel behind this optimization. The later mathlib packets
`c118`, `c119`, `c120`, and `c123` restate the same lane in a cleaner theorem
stack: reads analysis, incremental invariance, derivative-style perturbation,
and partial evaluation.

It proves:

- boolean read membership agrees with propositional read membership,
- evaluation depends only on read keys,
- changing an unread key cannot change the expression value,
- partial evaluation preserves denotation under compatible known values,
- incremental cache invalidation returns the same value as full reevaluation,
- unread-key changes reuse the cached node value.

The derivative packet adds this law:

```text
eval(derivative(k,v,e)) = update(eval(e), k, evalConst(e,v)).
```

Standard reading:

- A single-key derivative denotes the original expression table updated at the
  changed key.

Plain English:

- The derivative is a symbolic delta for one input-key change.

Boundary:

- This is a checked Tau-like expression-kernel law. It is not yet an
  implementation of delta evaluation in Tau's runtime.

Native Tau now has a separate measurement hook for the real interpreter:

```bash
TAU_RUN_STATS=1
```

That hook records per-step counters from the current `run` loop. It is useful
for locating the runtime integration surface, but it is not the delta cache.

The first opt-in native optimization on that surface is:

```bash
TAU_SKIP_UNCHANGED_IO_REBUILD=1
```

It skips rebuilding input or output stream objects after an accepted update when
the new specification has the same IO stream set as the current interpreter and
the active stream class explicitly declares that unchanged rebuilds are safe.
File streams do not make that declaration, because rebuilding them reopens the
file.

The standalone executable companion is:

```bash
python3 scripts/run_tau_derivative_equivalence_demo.py \
  --out results/local/tau-derivative-equivalence-demo.json
```

Current local receipt:

```text
cases:                         80
derivative sound cases:        80
size-preserved cases:          80
equivalence classifications:   80
result:                        passed
```

The checked command is:

```bash
lake build
```

The proof artifact is intentionally smaller than Tau itself. It proves the
semantic shape that a Tau runtime patch should preserve.

## Runnable Prototype

Run:

```bash
python3 scripts/run_incremental_execution_demo.py \
  --out results/local/incremental-execution-demo.json
```

The prototype uses a Tau-like expression language:

```text
const
var
common
pointJoin
pointCompl
choice
select
revise
update
```

The value carrier is the four-cell Boolean algebra encoded as a 4-bit mask.

## Current Local Receipt

The current generated report says:

```text
cases:                         6
full unique residual nodes:    193
incrementally recomputed:       31
runtime-delta recomputed:       31
aggregate recompute saving: 83.938%
runtime-delta saving:       83.938%
runtime dependency checks:   passed
runtime delta checks:        passed
all equality checks:         passed
```

The representative cases are:

- protocol priority update after one guard changes,
- incident-memory update after one revision region changes,
- sharded policy update after one shard guard changes,
- guarded pointwise update after the replacement value changes.
- protocol priority update after an irrelevant configuration key changes,
- incident-memory update after an irrelevant audit-only key changes.

Every case checks:

- partial evaluation preserves the original denotation before the change,
- partial evaluation preserves the original denotation after the change,
- incremental recomputation equals full reevaluation after the change.
- expected relevance is classified correctly,
- irrelevant changes reuse the cached value without recomputing any node.
- the stable-node-id dependency index selects exactly the recomputed nodes.
- the explicit runtime-delta cache update agrees with both recursive
  incremental evaluation and full reevaluation.

The irrelevant-change cases are negative controls. They do not make the runtime
claim broader; they check that the analysis can safely identify no-op input
changes.

## Why This Matters

This targets the official Tau future-work item about normalization and
satisfiability performance from a different angle than qelim dispatch.

The qelim work asks:

```text
Which backend should eliminate this quantifier?
```

The incremental-execution work asks:

```text
Which parts of this expression need to run again at all?
```

For stream-like Tau workloads, the second question can be more important. If a
single input key changes at each tick, most of a large expression may be
unchanged.

## Boundary

This is a prototype, not a Tau runtime patch.

It does not prove:

- whole-language Tau incremental execution,
- parser integration,
- safe caching in the presence of all Tau language features,
- asymptotic speedup for arbitrary programs,
- correctness of an upstream implementation.

The next implementation step would be a feature-gated Tau runtime experiment
that records read sets for typed IR nodes, caches evaluated sub-expressions,
invalidates nodes whose read sets contain the changed key, and falls back to
full reevaluation whenever the analysis is incomplete.

## Tau Runtime Patch Shape

A future Tau patch should keep the optimization opt-in:

```bash
TAU_INCREMENTAL_EVAL=1
```

The safe implementation shape is:

```text
typed IR node
  -> stable node id
  -> read set
  -> cached value
  -> dirty flag
```

The current prototype now emits this shape explicitly: each residual expression
gets deterministic child-before-parent node IDs, a dependency index from input
key to node IDs, and a check that the dependency index for the changed key has
the same size as the unique recomputation set.

It now also executes the cache shape directly. The runtime path builds a
child-before-parent value table, gets dirty node IDs from the dependency index,
recomputes only those node IDs in one forward pass, and checks the root value
against full reevaluation.

On each input update:

```text
if changed_key in read_set(node):
  recompute node from children
else:
  reuse cached value
```

The conservative fallback is:

```text
if read_set is unknown:
  recompute normally
```

The first runtime benchmark should report:

```text
full_eval_nodes
incremental_recomputed_nodes
incremental_reused_nodes
changed_key_in_reads
fallback_count
same_output_as_full_eval
```

Promotion requires output parity against full reevaluation on every test case.

## Native Tau Runtime Telemetry

Run:

```bash
python3 scripts/run_tau_runtime_stats_demo.py \
  --out results/local/tau-runtime-stats-demo.json
```

This wrapper runs Tau's native update-stream example with `TAU_RUN_STATS=1`.
It compares baseline execution against `TAU_SKIP_UNCHANGED_IO_REBUILD=1`.

Current local receipt:

```text
step count:              3
accepted update count:   3
total paths attempted:   6
total paths solved:      6
total outputs:           6
total revisions tried:   1
total added spec parts:  2
input rebuilds skipped:  3
output rebuilds skipped: 1
output parity:           passed
final memory size:       9
```

Standard reading:

- The first two accepted updates add new specification parts. The third accepted
  update overlaps an existing output stream, so pointwise revision attempts and
  changes one existing specification part. With the skip flag enabled, Tau
  avoids rebuilding unchanged IO streams without changing the printed run
  output.

Plain English:

- The native Tau run loop is now measurable at the step boundary where a future
  incremental runtime cache would have to attach, and one small native rebuild
  optimization now has output-parity evidence.

Boundary:

- The skip flag does not cache expression values or change the solver. It only
  avoids recreating IO stream objects when the IO stream set is unchanged.
- The current parity receipt is still a small corpus. It now covers the console
  smoke case plus vector-remap and file-remap regression checks, but it is not a
  whole-runtime proof.

The stream-class regression command is:

```bash
python3 scripts/run_tau_io_rebuild_regression.py \
  --out results/local/tau-io-rebuild-regression.json
```

Current local regression receipt:

```text
vector baseline accepted updates: 3
vector skip accepted updates:     3
vector input rebuilds skipped:    3
vector output rebuilds skipped:   1
file baseline accepted updates:   3
file skip accepted updates:       3
file input rebuilds skipped:      0
file output rebuilds skipped:     0
vector output parity:             passed
file output parity:               passed
```

Standard reading:

- On vector-remapped streams, the skip flag avoids unchanged rebuilds and
  preserves the observed stream outputs. On file-remapped streams, the same flag
  performs zero skips, because the file stream class does not certify rebuild
  skipping as safe.

Plain English:

- The optimization now has a guardrail. It can skip streams whose rebuild is a
  state-preserving wrapper operation, but it will not skip file streams where
  rebuilding intentionally changes the stream state.
