# Safe Table Syntax with Select and Revision

This proof packet corresponds to local cycle `v554`.

It extends the safe table-expression grammar with first-class safe `select` and revision constructors.

## Added Forms

```latex
\mathrm{select}_G(x) := G \wedge x
```

```latex
\mathrm{revise}_{G,a}(x) := (G \wedge a) \vee (G' \wedge x)
```

The guard `G` must be fixed lower-stratum data. It cannot depend on the current recursive table state.

## Checked Claim

The extended grammar still denotes a monotone and omega-continuous simultaneous table update, and the omega-supremum of finite approximants is a fixed point.

## Boundary

This is not unrestricted full TABA tables. It excludes same-stratum prime, current-state-dependent guards, arbitrary value-predicate `select`, unrestricted recursive `common`, NSO syntax, Guarded Successor syntax, and Tau runtime lowering.
