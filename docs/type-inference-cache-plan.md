# Type-Inference Cache Plan

This note records the next implementation target after the `var_name` fast-path
experiment and the scoped cache-key proof.

## What Failed

The feature flag:

```bash
TAU_INFER_FAST_VAR_NAME=1
```

skips leave-phase default reconstruction for raw `var_name` leaf nodes. It
preserved the checked table-demo solver outputs, but the latest direct wrapper
did not show a stable speedup.

That is not surprising. A raw name leaf is too low-level. The semantic object
that needs caching is not just:

```text
name
```

It is closer to:

```text
scope + canonized variable + resolver state
```

## Proven Cache-Key Lesson

The small Lean model proves:

```text
cache(scope,name) = some type
implies
resolve(scope,name) = type
```

and therefore:

```text
annotateCached(resolve,cache,e) = annotate(resolve,e).
```

The same model gives a counterexample to name-only caching when shadowing is
possible.

## Tau Source Implication

The relevant Tau source area is:

```text
src/ba_types_inference.tmpl.h
src/type_scoped_resolver.h
src/type_scoped_resolver.tmpl.h
```

The resolver exposes scope-sensitive operations, including:

```text
type_scoped_resolver::scope_of
type_scoped_resolver::type_id_of
type_scoped_resolver::assign
type_scoped_resolver::merge
```

A real cache should live near the update path for typed variables, not at raw
`var_name` leaves.

## Candidate Cache Key

A conservative first key is:

```text
scope_id
canonized_variable_id
resolver_epoch
```

The `resolver_epoch` is the safety valve. It should change whenever an operation
can change the answer to a variable type query in the current scope:

```text
open scope
close scope
assign type
merge variables
```

With that key, a cache hit claims:

```text
same scope, same variable, same resolver epoch
```

so the cached type is allowed to stand in for the resolver query.

## Conservative Runtime Rule

```text
if cache key is complete and present:
  reuse cached typed variable
else:
  ask resolver and store result
```

Fallback is always full resolver behavior. A missing cache entry must never
change meaning.

## What To Measure

The next patch should record:

```text
variable_update_queries
variable_update_cache_hits
variable_update_cache_misses
resolver_epoch_bumps
output_parity
solve_total_ms
```

Promotion requires output parity first. Speedup is secondary.

## First Tau-Side Attempt

The first implementation used:

```bash
TAU_INFER_VARIABLE_UPDATE_CACHE=1
```

and cached variable updates only inside one `update(...)` call, where
`resolver.current_types()` is fixed.

Current result:

```text
output parity: passed
cache queries: 2635
cache hits:     432
hit rate:      16.3947%
solve delta:   -5.599%
```

This is useful negative evidence. The cache was semantically conservative, but
too narrow to improve the current safe-table solver corpus.

The next attempt should not promote this cache. It should either cache a larger
resolver product, cache across repeated inference calls with a real epoch, or
move to a different hotspot.

## Boundary

This plan is still narrower than a whole Tau type-inference proof. It is the
next implementation-shaped experiment suggested by the proof and telemetry.
