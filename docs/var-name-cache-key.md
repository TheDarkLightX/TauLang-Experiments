# Scoped Var-Name Cache Key

This experiment follows the `TAU_INFER_FAST_VAR_NAME=1` telemetry result. The
fast path was measurable but did not show a stable speedup. The next safer
question is whether a real cache key can be stated precisely.

## Law

For a resolver:

```text
resolve(scope,name) = type
```

a scoped cache is sound when every cache hit agrees with the resolver:

```text
cache(scope,name) = some type
implies
resolve(scope,name) = type.
```

Under that condition, cached annotation and uncached annotation agree:

```text
annotateCached(resolve,cache,e) = annotate(resolve,e).
```

Standard reading: if each cached `(scope,name)` entry stores the same type that
the resolver would compute, then using the cache does not change the annotated
expression.

Plain English: caching is safe only when the cache key contains enough context
to distinguish scoped names.

## Counterexample

A cache keyed only by name is not sound under shadowing:

```text
resolve(global,x) = tau
resolve(local,x)  = sbf
```

If the cache stores only:

```text
x -> tau
```

then the local occurrence of `x` is incorrectly typed as `tau` instead of
`sbf`.

## Lean Artifact

The local Lean packet is:

```text
experiments/aristotle_tasks/tau_var_name_cache_key_2026_04_15
```

It proves the scoped-cache soundness theorem and a name-only shadowing
counterexample in a small Tau-like model.

## Runnable Demo

Run:

```bash
python3 scripts/run_var_name_cache_key_demo.py \
  --out results/local/var-name-cache-key-demo.json
```

Current local receipt:

```text
case_count: 3
scoped cache: matches all cases
name-only cache: has counterexamples under shadowing
```

## Boundary

This is not a theorem about Tau's full scoped union-find resolver. It is a proof
and executable model for the cache-key shape that a Tau implementation would
need to preserve.
