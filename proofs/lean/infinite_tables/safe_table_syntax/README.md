# Safe TABA Table Syntax Capstone

This packet proves the safe table syntax layer.

## Main Theorem

```lean
theorem v552_safe_table_syntax_receipt
```

## Standard Reading

`TableExpr` is a syntax for safe table bodies. It has rows and an explicit default. Each row has a guard and a value.

The denotation maps a table expression into a Boolean-algebra-valued update:

```text
denoteTable lower state table
```

A simultaneous recursive table body is interpreted as:

```text
updateTables lower body : State I alpha -> State I alpha
```

The main theorem proves:

```text
updateTables is monotone
updateTables is omega-continuous
the omega-supremum of finite approximants is a fixed point
```

## Included Fragment

```text
lower-stratum row guards
positive current-state value references
lower-stratum prime
lower-guarded CBF-style conditionals
explicit defaults
```

## Excluded Fragment

```text
same-stratum prime
current-state-dependent row guards
current-state-dependent CBF guards
arbitrary select inside recurrence
unrestricted common inside recurrence
NSO syntax
Guarded Successor syntax
Tau runtime lowering
```

## Why It Matters

This is stronger than just a semantic foundation. It gives a syntax-to-semantics theorem for the safe table fragment.

It still does not prove unrestricted full TABA tables.

## Local Check

```bash
lake build
```

and scan for proof escapes:

```text
sorry
admit
axiom
unsafe
sorryAx
```
