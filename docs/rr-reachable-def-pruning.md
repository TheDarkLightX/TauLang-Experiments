# Reachable recurrence-definition pruning

This note records an experimental recurrence-rewrite optimization. The pass is
off by default.

## Optimization

Before recurrence relations are transformed and applied, collect the relation
names referenced by the current main formula. Keep only definitions whose head
relation is reachable from those names, then close the set by following
references in the kept definition bodies.

The feature flag is:

```bash
TAU_RR_REACHABLE_DEFS=1
```

The pruning audit flag is:

```bash
TAU_RR_REACHABLE_DEFS_AUDIT=1
```

The audit computes the optimized result and the unpruned result, then requires
structural equality.

## Post-transform variant

The pre-transform pass can reduce transform cost in one-shot checks, but it can
also defeat the transformed-definition cache in batched workloads because each
main formula may produce a different pruned definition list.

The post-transform variant keeps the transformed-definition cache first, then
prunes the transformed rule list:

```bash
TAU_RR_REACHABLE_DEFS=1
TAU_RR_REACHABLE_DEFS_POST_TRANSFORM=1
```

An additional cache exists for the reachability result:

```bash
TAU_RR_REACHABLE_DEFS_CACHE=1
```

On the current table-check corpus, the cache did not hit because the reachable
sets were distinct.

## Evidence

One-shot table demo solver telemetry, three repetitions, with value-inference
skip, transformed-definition cache, and active-rule filtering already enabled:

```text
baseline transform_ms: 27.615619
reachable transform_ms: 11.521693
baseline solve_total_ms: 43.863820
reachable solve_total_ms: 25.756450
reachable definitions: 330 before, 51 after
output parity: passed
```

Batched table checks, three repetitions, same baseline flags:

```text
baseline solve_total_ms: 99.787529
reachable solve_total_ms: 107.447080
baseline transform_ms: 17.950046
reachable transform_ms: 37.377849
reachable definitions: 2250 before, 183 after
output parity: passed
```

Post-transform pruning, one batched repetition:

```text
baseline solve_total_ms: 35.534020
reachable solve_total_ms: 32.557691
baseline transform_ms: 6.656013
reachable transform_ms: 10.832494
reachable definitions: 750 before, 61 after
output parity: passed
```

Post-transform pruning with audit, one batched repetition:

```text
reachable audit rows: 15
reachable audit structurally equal rows: 15
active-rule audit rows: 15
active-rule audit structurally equal rows: 15
```

## Conclusion

This is not a default optimization candidate yet.

The useful result is diagnostic: recurrence-rewrite optimization is
fragment-sensitive even inside the same safe-table workload. Pre-transform
definition pruning helps one-shot checks, but it can harm batched checks by
destroying cache locality. Post-transform pruning preserves cache locality and
can reduce solver time, but the current evidence is small and mixed.

Keep this as an auditable experimental flag. Do not present it as a general Tau
Language speedup until a broader corpus shows stable wins.
