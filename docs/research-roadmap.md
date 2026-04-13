# Research Roadmap

## 1. Finite Tables

Goal: make finite tables an executable semantic kernel.

Core artifacts:

- table `set`, `select`, and `common` semantics
- pointwise Boolean operations
- finite-clopen or BDD-backed carriers
- deterministic examples and traces
- correctness statements in Lean

## 2. Infinite Table Reference Semantics

Goal: separate executable finite approximants from completed reference semantics.

Core artifacts:

- finite clopen embedding into completed stream-predicate semantics
- countable union support for reference semantics
- Kleene least-fixed-point semantics for safe recurrence
- finite-stabilization theorem connecting finite execution to completed semantics
- negative boundary theorems for unsafe same-stratum complement

## 3. Quantifier-Elimination Dispatch

Goal: choose the QE backend based on fragment shape.

Candidate lanes:

- current Tau antiprenex pipeline
- BDD existential abstraction
- finite-mask QE
- splitter-based QE
- Skolem split-witness QE
- syntax-directed simplification before semantic compilation

Working principle:

```text
qelim algorithm choice should be fragment-sensitive, because the fastest method depends on where the structure lives: in syntax, or in the compiled carrier.
```

## 4. Proof-Carrying Optimization

Goal: every optimization should emit a semantic receipt.

Receipt classes:

- same denotation
- same satisfying assignments
- same finite approximants
- same least fixed point under monotonicity and omega-continuity assumptions
- counterexample witness when a rewrite is invalid

## 5. Tau Runtime Bridge

Goal: keep runtime experiments behind feature flags and patches.

The repo should demonstrate behavior without redistributing Tau itself.
