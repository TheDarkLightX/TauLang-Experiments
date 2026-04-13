# Current Infinite Tables Proof Status

This file is the current status snapshot for the infinite-table proof lane. Older index files may lag behind this document.

## Scope Discipline

The claim here is scoped to the Lean artifacts currently mirrored under `proofs/lean/infinite_tables/`. It does not claim that unrestricted TABA tables, full Nullary Second-Order logic, full Guarded Successor, or Tau runtime lowering are complete.

## Mechanically Checked Pieces

| Packet | Status | Meaning |
| --- | --- | --- |
| `clopen_boolref_embedding` | checked | Finite clopens embed into the completed Boolean reference semantics and preserve Boolean operations. |
| `kleene_stabilization` | checked | If an update is monotone and omega-continuous, the Kleene supremum is a least fixed point; if the finite iterates stabilize, the completed fixed point is already finite. |
| `unsafe_recurrence_boundary` | checked | Same-stratum complement is anti-monotone and not omega-continuous, so it is unsafe inside the positive recursive kernel. |
| `safe_table_syntax` | checked | A safe table-expression syntax with lower-stratum guards, positive current references, lower-prime, lower-guarded CBF conditionals, and explicit defaults denotes a monotone omega-continuous simultaneous update with a fixed-point receipt. |

## What This Means

The safe table syntax lane is now more than a carrier theorem. It includes a table-expression grammar, a denotational semantics, monotonicity, omega-continuity, and a fixed-point theorem.

The core recurrence shape is:

```latex
s_0 := \bot
```

```latex
s_{n+1} := U_T(s_n)
```

```latex
\mu U_T := \bigvee_{n < \omega} s_n
```

```latex
U_T\!\left(\bigvee_{n < \omega} s_n\right) = \bigvee_{n < \omega} U_T(s_n)
```

Standard reading: the sequence starts from bottom, repeatedly applies the table update `U_T`, defines the least recursive table value as the supremum of all finite approximants, and requires the update to commute with that countable increasing supremum.

Plain English: the safe table language can run recurrence by taking better and better finite approximations, and the theorem says the limit is stable under one more table update.

## What Is Still Open

The following are not solved by the safe syntax packet:

- unrestricted same-stratum prime inside recurrence
- current-state-dependent row guards
- current-state-dependent CBF guards
- arbitrary `select` inside recurrence
- unrestricted `common` inside recurrence
- full official NSO syntax
- full official Guarded Successor syntax
- Tau runtime lowering
- BDD or Tau-engine optimization receipts

## Current Answer

Finite tables are solved as an executable tutorial kernel. Safe infinite-recursive table syntax is now mechanically represented and proved for a meaningful fragment. Full unrestricted TABA tables are not solved yet.