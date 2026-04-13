# Unsafe Recurrence Boundary Packet

This proof packet gives the negative boundary for safe infinite-table recurrence.

## Main Theorems

```lean
theorem complement_not_monotone
theorem complement_not_omegaContinuous
```

## Standard Reading

Complement reverses order. Therefore, from `X <= Y`, it does not follow that `X' <= Y'`. In the completed reference carrier used here, same-stratum complement is not monotone.

The packet also gives a concrete increasing chain where complement fails to preserve the countable supremum.

## Why It Matters

The safe recursive kernel cannot include unrestricted same-stratum complement. Negation must be stratified, fixed from a lower layer, or separately proved safe for a narrower fragment.

## Non-Claims

This packet does not say all negation is forbidden. It only rejects unrestricted current-state complement inside a monotone omega-continuous recurrence theorem.

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
