# Safe Table Syntax Capstone

This note records the current infinite-table proof capstone. It is intentionally scoped.

## Claim

The checked Lean packet `proofs/lean/infinite_tables/safe_table_syntax/` proves a safe table-expression fragment over a complete Boolean algebra.

A table update has the shape:

```latex
U_T : (I \to \alpha) \to (I \to \alpha)
```

Standard reading: `U_T` is a function from current table states to next table states, where each key in `I` receives a Boolean-algebra value in `\alpha`.

Plain English: one update pass computes the next value of every table entry.

## Safe Syntax

The fragment includes:

- row guards that read only lower-stratum data
- values that may read current recursive entries positively
- lower-stratum prime, because it is constant relative to the current recurrence
- lower-guarded conditional Boolean-function style conditionals
- explicit defaults

The fragment excludes:

- same-stratum prime in recursive positions
- row guards that inspect the current recursive state
- condition guards that inspect the current recursive state
- unrestricted `select`
- unrestricted `common`

## Main Equations

The recurrence starts at bottom:

```latex
s_0 := \bot
```

It advances by applying the table update:

```latex
s_{n+1} := U_T(s_n)
```

The candidate recursive meaning is the supremum of all finite stages:

```latex
\mu U_T := \bigvee_{n < \omega} s_n
```

The key continuity theorem is:

```latex
U_T\!\left(\bigvee_{n < \omega} s_n\right) = \bigvee_{n < \omega} U_T(s_n)
```

Standard reading: applying the table update after taking the supremum of the finite approximants gives the same result as taking the supremum after updating each finite approximant.

Plain English: the table update does not introduce a hidden discontinuity at the infinite limit.

The fixed-point proof artifact is:

```latex
U_T(\mu U_T) = \mu U_T
```

Standard reading: the recursively defined table value is unchanged by one more application of the update.

Plain English: the limit really is a stable table meaning, not just an informal approximation.

## Why This Matters

The earlier obstruction showed that finite clopens alone cannot contain arbitrary countable recurrence limits. The capstone does not deny that obstruction. It moves the recurrence proof to a complete Boolean-algebra reference layer and restricts the table syntax so the induced update is monotone and omega-continuous.

That is the safe semantic core. The remaining work is to classify more official TABA operators, lower the safe fragment into Tau runtime artifacts, and prove which implementation carriers preserve this reference meaning.

## Demo Evidence

Project boundary: this demo is a community research prototype.
It is not an official IDNI or Tau Language table implementation and should not
be read as a claim about what IDNI intends to ship.

The runnable demo is:

```bash
./scripts/run_table_demos.sh --accept-tau-license
```

It checks these public-facing facts:

- the safe symbolic table update is idempotent on the checked formula,
- the finite four-cell carrier update matches the expected low-bit result,
- finite-carrier pointwise revision matches the expected low-bit result,
- Tau-native table syntax agrees with its raw guarded-choice expansion,
- pointwise revision preserves old values outside the guard,
- pointwise revision uses replacement values inside the guard,
- pointwise revision is idempotent for the same guard and replacement,
- the same table syntax is rejected when `TAU_ENABLE_SAFE_TABLES` is absent.

The central demo equation is:

```latex
\operatorname{priority\_quarantine\_update}
=
\operatorname{priority\_quarantine\_raw}.
```

Standard reading: the parsed `table { when ... else ... }` term denotes the same
Boolean-algebra value as the hand-expanded guarded-choice formula.

Plain English: the demo shows that the new table syntax is not magic. It lowers
to the exact guarded-choice expression specified by the checked lowering
artifact.

Boundary: this is still safe guarded choice. It is not unrestricted recurrence,
same-stratum prime, full NSO, or Guarded Successor.
