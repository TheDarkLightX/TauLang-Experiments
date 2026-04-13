# Operation Safety Boundary

This note records the next boundary after the safe table syntax capstone.

## Safe Forms

Fixed-guard selection:

```latex
\mathrm{select}_G(x) := G \wedge x
```

Standard reading: the selected value is the meet of the fixed guard `G` and the recursive input `x`.

Plain English: keep the part of `x` that lies under the fixed guard, and discard the rest.

Fixed-guard revision:

```latex
\mathrm{revise}_{G,a}(x) := (G \wedge a) \vee (G' \wedge x)
```

Standard reading: under guard `G`, use the replacement value `a`; outside `G`, keep the old recursive value `x`.

Plain English: overwrite the guarded region and leave the rest unchanged.

The Lean packet proves both operations are monotone and omega-continuous when `G` and `a` are fixed lower-stratum data.

## Unsafe Forms

The same packet proves checked counterexamples for:

- current-value-dependent guards
- arbitrary value-predicate selection
- equality-style `common` treated as value-predicate selection

This matters for recurrence. A recursive kernel can use Kleene iteration safely only when the update is monotone and continuous enough for the chosen completion semantics. These counterexamples explain why arbitrary `select` and unrestricted `common` cannot simply be admitted into the recursive layer.

## Scope

This is a classifier theorem, not a full implementation of official TABA tables. It says which operation shapes are safe enough for the current fixed-point lane and which shapes require stratification or a separate proof.