# Clopen to BoolRef Embedding Packet

This proof packet connects the finite executable lane to the completed reference lane.

## Main Theorems

```lean
theorem embed_equiv_iff
theorem embed_bot
theorem embed_top
theorem embed_inf
theorem embed_sup
theorem embed_compl
theorem eventuallyOne_eq_iUnion_cylinders
theorem no_clopen_represents_eventuallyOne
theorem eventuallyOne_not_in_embedClopen_range
```

## Standard Reading

A finite-support clopen is represented by a Boolean-valued function on infinite Boolean streams whose output depends only on finitely many coordinates.

`embedClopen` maps such a finite object into the completed reference carrier:

```text
embedClopen(c) = { streams s where c.fn(s) = true }
```

The embedding preserves bottom, top, meet, join, and prime/complement.

The packet also proves that `EventuallyOne`, the set of streams containing at least one true bit, is a countable union of cylinders in the completed carrier, but is not represented by any finite-support clopen.

## Why It Matters

This proves the finite executable lane is semantically compatible with the completed reference lane, while preserving the obstruction that finite clopens alone cannot express arbitrary countable recurrence behavior.

## Non-Claims

This packet does not prove:

```text
BoolRef is atomless
finite clopens are countably complete
table recurrence
NSO
Guarded Successor
Tau lowering
```

## Local Check

The source packet was checked locally with:

```bash
lake build
```

and scanned for proof escapes:

```text
sorry
admit
axiom
unsafe
sorryAx
```
