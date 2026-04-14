# Infinite Table Proof Status

## Status

The current checked result is a scoped semantic foundation, not unrestricted full TABA tables.

## What Is Mechanically Checked

Three proof packets are now included under `proofs/lean/infinite_tables/`.

### 1. Finite clopens embed into completed reference semantics

The finite executable carrier embeds into a completed stream-predicate carrier. The embedding preserves bottom, top, meet, join, and prime/complement.

The same packet proves the boundary witness:

```text
EventuallyOne(s) := exists n, s n = true
```

`EventuallyOne` is expressible as a countable union in the completed carrier, but no finite-support clopen represents it.

### 2. Kleene recurrence and finite stabilization

For a monotone omega-continuous update `F`, the countable supremum of finite iterates from bottom is a least fixed point.

If the finite iteration sequence stabilizes at step `N`, then the completed least fixed point equals the finite iterate at `N`.

### 3. Same-stratum complement is unsafe

Complement is not monotone over the completed reference carrier. It also fails omega-continuity on a concrete increasing chain.

This is the formal reason unrestricted current-state prime/complement must be excluded, stratified, or separately proved safe.

## What This Gives Us

The current proof stack justifies the following design:

```text
finite executable lane
  embeds into
completed reference semantics
  supports
safe monotone recurrence
  with
explicit negative boundaries for unsafe recurrence
```

## What Remains Before Claiming Full TABA Tables

Still open:

```text
official table syntax formalization
syntax-to-semantics adequacy theorem
full select/common/revision recurrence safety classification
full CBF fragment integration
NSO syntax and binding layer
Guarded Successor integration
Tau runtime lowering and tests
BDD-backed executable optimization evidence
```

## Practical Next Step

The next proof target should be the official table syntax adequacy layer:

```text
TableExpr syntax
  -> denotational semantics
  -> safe recurrence predicate
  -> theorem: SafeTableExpr denotes a monotone omega-continuous update
```

Only after that layer is checked should the repo claim more than a semantic foundation.
