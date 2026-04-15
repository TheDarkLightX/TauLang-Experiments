# Variable-Update Cache Telemetry

This is the first Tau-side implementation attempt after the scoped cache-key
proof.

## Feature Flag

```bash
TAU_INFER_VARIABLE_UPDATE_CACHE=1
```

The cache is local to one `update(...)` call in Tau's Boolean-algebra type
inference. That call has already snapshotted:

```text
resolver.current_types()
```

so the cache does not cross resolver-scope changes.

## Reproduction

```bash
python3 scripts/run_infer_variable_update_cache_demo.py \
  --reps 1 \
  --out results/local/infer-variable-update-cache-demo-reps1.json
```

The wrapper runs the representative safe-table solver corpus in baseline mode
and cached mode, checks output parity, and records `[infer_update]` telemetry.

## Current Local Receipt

```text
ok: true
baseline solve total: 83.376100 ms
cached solve total:   88.044200 ms
solve delta:          -5.599%
baseline elapsed:     35355.672 ms
cached elapsed:       35556.682 ms
elapsed delta:        -0.569%
cache queries:        2635
cache hits:            432
cache misses:         2203
hit rate:             16.3947%
```

Standard reading: the cache preserved the checked solver outputs, but the hit
rate was too low and the cached mode was slower on this run.

Plain English: this cache is probably too narrow to be useful.

## Per-Case Hit Rates

```text
tau native table:          22.4%
protocol firewall table:   12.4%
collateral reason table:   12.9%
incident memory table:     14.9%
pointwise revision table:  22.0%
```

## Boundary

This is negative optimization evidence, not a failed proof. The semantic shape
was safe enough for output parity, but the implementation shape did not buy
enough reuse.

The next cache attempt should either:

- cache a larger resolver product than individual variable updates,
- cache across repeated inference calls with a real resolver epoch, or
- move to a different hotspot with a higher measured repetition rate.
