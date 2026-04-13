# Safe Table Select and Revision

The latest checked table grammar admits two more official-looking operations, but only in their safe form.

## Selection

```latex
\mathrm{select}_G(x) := G \wedge x
```

Standard reading: the selected value is the meet of the fixed guard `G` and the value `x`.

Plain English: selection keeps the part of `x` inside the fixed guard and removes the rest.

Trap: this is not arbitrary selection by any predicate over values. Arbitrary predicates are not monotone in general, and the proof lane contains a checked counterexample.

## Revision

```latex
\mathrm{revise}_{G,a}(x) := (G \wedge a) \vee (G' \wedge x)
```

Standard reading: inside `G`, use replacement `a`; outside `G`, keep the old value `x`.

Plain English: revision overwrites the guarded region and preserves everything outside it.

Trap: the guard must be fixed relative to the recursive state. If the guard reads the current recursive value, the operation can become anti-monotone, and Kleene iteration can lose its semantic guarantee.

## Why This Is Progress

The earlier safe grammar excluded `select` and revision. The v554 proof packet brings their safe forms into the grammar and proves that the whole simultaneous table update remains monotone, omega-continuous, and fixed-point stable.

This does not solve unrestricted full TABA tables. It expands the safe recursive kernel with checked boundaries.