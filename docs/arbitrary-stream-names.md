# Arbitrary Stream Names, Semantic Kernel

Tau's future-work list includes arbitrary stream names. The implementation work
is parser and runtime engineering, but there is a small semantic law that should
hold behind the feature.

## Law

Let `rename_f(e)` replace every stream key `k` in expression `e` with `f(k)`.

```text
env'(f(k)) = env(k) for every key k
implies
eval(env', rename_f(e)) = eval(env, e)
```

Standard reading:

- If the renamed environment gives every renamed key the same value that the
  original environment gave the original key, then the renamed expression has
  the same denotation as the original expression.

Plain English:

- Changing stream names should not change meaning by itself.

## Checked Artifact

The local Lean packet `tau_stream_rename_semantics_2026_04_15` proves this law
for a small Tau-like Boolean-expression kernel.

## Boundary

This does not implement arbitrary stream names in Tau. It only states the
semantic invariant that an implementation should preserve.
