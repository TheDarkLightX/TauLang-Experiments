# Var-Name Fast-Path Telemetry

This is a Tau-side optimization experiment for the table-demo `solve --tau`
path. It is not a default optimization.

## Feature Flag

```bash
TAU_INFER_FAST_VAR_NAME=1
```

When the flag is set, the patched Tau binary skips leave-phase default
reconstruction for `var_name` leaf nodes during Boolean-algebra type inference.

## Reproduction

```bash
python3 scripts/run_infer_fast_var_name_demo.py \
  --reps 1 \
  --out results/local/infer-fast-var-name-demo-reps1.json
```

The wrapper runs the representative safe-table solver checks twice: once in
baseline mode and once with `TAU_INFER_FAST_VAR_NAME=1`. It records output
parity, solve telemetry, end-to-end elapsed time, and the number of fast-path
hits.

## Current Local Receipt

```text
ok: true
baseline solve total: 72.999700 ms
fast solve total:     73.525500 ms
solve delta:          -0.720%
baseline elapsed:     34866.789 ms
fast elapsed:         35152.460 ms
elapsed delta:        -0.819%
fast-path hits:       577
```

Standard reading: the fast path preserved the checked solver results on this
corpus, but this latest smoke run did not improve solve time or elapsed time.

Plain English: the shortcut is safe enough to keep studying, but not good
enough to promote.

## Boundary

This experiment tests one narrow type-inference shortcut on five safe-table
solver checks. It is not evidence of a general Tau speedup.

The useful result is the measurement discipline:

```text
output parity first, speed second, default promotion last
```

Promotion would require a broader corpus, stable speedup, and a code-level
argument that `var_name` leaves have no leave-phase reconstruction obligation.
