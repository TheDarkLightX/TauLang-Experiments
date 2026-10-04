# Support-cell oracle proof obligations (draft, before implementation)

Base repository revision: `65ef69bdc5e6f1e479236d9dfb4d9b6d2e5302d1`.
Initial status at contract creation: proposed; no theorem was checked then.
Current status: SC-1/SC-2/SC-3 completed for the explicit set-algebra amendment
below; executable correspondence bounded and tested, not implementation proved.

Scope amendment, approved by study lead before the formula proof: the checked
carrier is an arbitrary Boolean subalgebra of sets with genuine atomless
splitting. General abstract Boolean-algebra transfer by a representation theorem
is not formalized. The original broader statements below remain the record of
the proposed target and must not be reported as achieved in that broader scope.
`compare_exact` and all-nonempty-support realizability were also proved. See
README and receipts for the exact completed claims.
Target toolchain: repository-precedent Lean `leanprover/lean4:v4.29.1`.
No external theorem-library dependency is planned.

## Semantic boundary

Only Boolean-algebra terms with variables, 0, 1, complement, meet, join,
and formulas constructed from term equality, propositional connectives, and
quantifiers over the same Boolean-algebra carrier are eligible. Named or
interpreted constants, temporal formulas, Tau `sbf`, mixed sorts, recursion,
and operational Tau checker behavior are outside this packet. The exact
experiment AST, evaluator bytes, and binding order must be fixed before
claiming implementation correspondence.

Let an assignment of n parameters determine its 2^n Boolean minterm cells.
A support records precisely which cells are nonzero. A new quantified
Boolean-algebra element refines each occupied cell into low-only, high-only,
or both occupied child cells; an unoccupied cell has no occupied children.
The atomless splitting property is needed to realize the `both` case.

## SC-1: quantifier-free support abstraction

For every carrier, Boolean-algebra structure, n, parameter assignment, and
well-scoped quantifier-free formula in the language above, interpreting the
formula in that algebra equals interpreting it by the exact support of the
assignment. There is no fixed finite carrier bound. Pure term truth tables
are used pointwise inside occupied minterms; an equation means equality in
all occupied cells, rather than merely equality at one Boolean valuation.

Acceptance: checked Lean theorem from explicit definitions; no assumed
checker-soundness premise. Propositional/set-carrier specialization is
acceptable only if clearly labeled, with general Boolean-algebra refinement
left open. Controls: 0=1 under nonempty support; x=0 or x=1 valid over the
2-element algebra but false under support occupying both parameter cells.

## SC-2: atomless one-variable refinement realizability

For every nontrivial atomless Boolean algebra, every finite parameter
assignment, and every support-child labeling that has at least one occupied
child exactly for occupied parent cells, there exists one Boolean-algebra
element whose extended assignment has exactly that child support.

The nontrivial/atomless premises must be explicit. Atomlessness means every
nonzero element has a proper nonzero subelement; it must not be replaced by
the desired finite refinement conclusion. Prove using finite disjoint-cell
splitting and finite gluing. If this theorem is not completed, mark it open;
do not silently put the refinement conclusion into a structure field and
call that an atomless proof.

## SC-3: quantified support-evaluator exactness

For every nontrivial atomless Boolean algebra, every finite parameter
assignment, and every well-scoped first-order formula in the restricted
language, algebraic truth agrees with recursive evaluation of zero/equality
on support and enumeration of precisely the legal support refinements at
quantifiers. Universal quantification must be justified too, either directly
or by classical duality. SC-1 and SC-2 are dependencies.

Executable correspondence is separate: the Lean evaluator and the Python
oracle must agree over a versioned exhaustive/bounded fixture set. This is
regression evidence, not a proof that Python implements the Lean evaluator.

## Secondary contracts, only after the oracle boundary is clear

- Equality/congruence closure: an inductively defined closure of sound,
  fixed-interpretation equations preserves semantics. This theorem alone
  does not certify rewrite rules, checker answers, extraction, or caches.
- Protected extraction: selecting a replacement only when its actual emitted
  cost is no greater than original, with fallback to original, ensures the
  measured nonregression postcondition. Does not ensure optimality or speed.
- Context-safe substitution: equality of complete, well-scoped, sort-matched
  terms under the same ordered variables/constants/assumptions preserves
  enclosing formula semantics. No statement that a string cache key enforces
  those bindings without implementation evidence.

## Falsifiers and acceptance

Controls include finite-two-element versus atomless formula semantics,
one-way implication incorrectly used as equality, variable-order/context or
sort mismatch, and a `both` refinement disallowed by finite atomic carriers.
Each checked claim must have exact source hashes, checker version, replay
argv, exit code, and dependency audit using Lean's declaration inspection.
No admitted theorem, custom unproved declaration, unsafe proof escape, or
opaque native evaluation oracle is allowed. Standard Lean foundational
assumptions, if present, must be individually reported, not hidden.
No parser/C++/Tau/code-refinement claim follows from an abstract theorem.
Known Boolean-algebra minterm and quantifier-elimination facts are background;
newness, if any, lies in the experiment/refinement artifacts, not these facts.
