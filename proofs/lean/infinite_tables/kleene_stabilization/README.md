# Kleene Stabilization Packet

This proof packet closes the recurrence bridge needed by the infinite-table reference semantics.

## Main Theorems

```lean
theorem kleeneMu_fixed
theorem kleeneMu_least_fixed
theorem kleeneMu_eq_stable_iter
```

## Standard Reading

`kleeneMu oc F` is the countable supremum of the finite iteration sequence starting at bottom:

```text
bot, F(bot), F(F(bot)), ...
```

If `F` is monotone and omega-continuous, that supremum is a fixed point of `F`. If `Y` is any fixed point of `F`, then `kleeneMu oc F` is below `Y`. If the finite iteration sequence stabilizes at step `N`, then the completed supremum equals the finite iterate at `N`.

## Why It Matters

This is the exact bridge between finite executable approximants and completed infinite reference semantics:

```text
finite approximants stabilize
  -> completed Kleene supremum equals finite stabilized value
```

## Non-Claims

This packet does not prove:

```text
full TABA syntax
NSO
Guarded Successor
Tau lowering
same-stratum complement safety
executable BDD canonicalization
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
