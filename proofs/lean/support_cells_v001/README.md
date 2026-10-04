# Checked finite-support semantics for an atomless set algebra

## Result and exact scope

`Proofs.lean` proves `compare_exact`: for **every nonempty base set X**, every
Boolean subalgebra A of predicates on X satisfying genuine atomless splitting,
any number n of parameters, and any two well-scoped formulas f and g, the
executable finite-support comparator returns true **if and only if** f and g
have the same truth value for **every A-valued parameter assignment**.

The typed language contains 0, 1, variable, complement, meet, join, term
equality, formula negation, conjunction, disjunction, existential and universal
quantification. Quantifiers range over **all members of A**, not a finite
powerset or Boolean assignment sample. The Lean reference evaluator exhaustively
enumerates child supports and filters the exact legal refinement relation.
There are no resource caps in the mathematical theorem. Runtime enumeration
is doubly exponential and is not proposed as a fast implementation.

The central construction is not a checker-soundness assumption:

1. `term_eq_support` reduces equality of sets to equality at occupied cells.
2. `cell_member` proves every parameter cell is an algebra member.
3. `realize_refinement` constructs a prescribed finite child support by genuine
   nonempty proper splitting of each occupied cell and finite disjoint gluing.
4. `formula_support_exact` proves quantified formula exactness by induction.
5. `executable_support_exact` proves the finite Boolean evaluator implements
   the mathematical support interpretation.
6. `all_nonempty_supports_realizable` proves that every nonempty support is
   realizable in every nontrivial atomless set algebra.
7. `compare_exact` proves the complete equivalence decision statement above.

`proper_element_exists`, `endpoint_full_support_false`, `proper_closed_true`,
`endpoint_not_equivalent_true`, `one_way_not_equivalence`,
and `finite_two_element_boundary` capture the boundary between a two-element
Boolean algebra and atomlessness. `term_signature_transfer` proves transfer of
pure 0/1 term identities to this set interpretation without atomlessness.

## Assumptions and dependency audit

`AtomlessField` is a family of predicates closed under empty/full sets, finite
union, finite intersection, and complement. Its only atomless assumption is:
every nonempty member p contains a nonempty member q whose complement in p is
also nonempty. Finite support refinement is **proved from** that property.
`compare_exact` additionally requires `Nonempty X`; degenerate empty-support
cases are admitted only in the more general intermediate semantics.

Imports: the `Std` library bundled with Lean 4.29.1. No mathlib, remote proof
service, or additional library dependencies. The audit prints each important
declaration's dependencies. The only foundational dependencies are
`propext`, `Classical.choice`, and `Quot.sound`; some controls use fewer or none.
There are no custom unproved declarations, admissions, native-decide proofs,
or unsafe proof escapes. `replay.py` checks both source tokens and the complete
audit output. See `receipts/lean-build.txt`.

## Python and parser correspondence

`fixtures.json` contains 1,073 deterministic development fixtures, including
complete depth-one term predicates with 0-2 free variables, shallow formula
pairs, quantified proper-split predicates, nested/alternating quantifiers,
shadowed variable names, ordered-interface controls, pilot originals and
registry entries. Total simultaneous slots are at most three. They are not the
expanded experiment's holdout set.

`Bridge.lean` is generated deterministically by `replay.py`:

- Python uses ordered named slots, appending the newest binder at the most
  significant bit; Lean uses a head/de Bruijn slot at Fin 0.
- The adapter reverses the initial variable order and prepends each binder.
  Variable resolution selects the first matching name in that newest-first
  environment. `pythonCell` explicitly converts back to the Python bit index.
- Python XOR is desugared into `(a & !b) | (!a & b)`.
- eq0/ne0 become term equality/inequality to zero; T/F become fixed true/false
  equalities. Formula tags preserve their sorts.

The replay checks 11,979 formula/support observations against the canonical
`experiments/semantic_saturation/src/support_oracle.py`. It also compares all
legal one-binder child supports for every nonempty parent support with 0-2
slots: 19 parent cases and 273 children. The two implementations use different
enumeration algorithms. Two actually executed Lean translation mutants (wrong initial variable order,
and resolving a shadowed name to the old binder slot) must produce different
observations and their correct counterparts must match Python. An executed
Python refinement mutant that forbids both children must reject the closed
proper-element formula that the real atomless evaluator accepts. Two negative
Lean compile tests must also reject a formula in a term position and a
variable index without a valid in-scope bound.

The 24 native parser receipts contain exact historical normalizer stdout,
parsed candidate ASTs, native binary hash, and full source-receipt hashes. Their
stdout is reparsed by the canonical `normalized_parser.py` and the resulting
ASTs are included in the Lean comparison. They are inherited Mac pilot-003
executions, **not fresh Linux native-Tau observations**.

## Replay

Install the official toolchain named by `lean-toolchain` and place its `bin`
directory on PATH. From this directory:

```sh
lean --version
lake build
python3 replay.py
```

`replay.py` rebuilds `Proofs.lean`, verifies all printed dependencies, verifies
that `Bridge.lean` equals deterministic generation, runs the Lean evaluator,
executes the canonical Python oracle/parser, and writes receipts. Build products
stay in ignored `.build`/`.lake` directories. No downloads or private checkpoint
files are required for replay.

`prepare_fixtures.py` records the original fixture construction process. It is
**optional, not part of replay**, and requires the original private pilot
checkpoint at its documented path. The versioned `fixtures.json` is the replay
input. Do not run fixture regeneration as a clean-clone prerequisite.

Official archive used in the cloud run:
`https://github.com/leanprover/lean4/releases/download/v4.29.1/lean-4.29.1-linux.tar.zst`.
SHA256: `bf062d29556d655685fb287563c249ad6a8fde34352c18b5e32568a595c1aec1`.
Compiler commit: `f72c35b3f637c8c6571d353742168ab66cc22c00`.
The earlier 4.19.0 HEAD-only request was a connectivity diagnostic; no 4.19.0
binary or proof result is used.

## What this does not prove

- No representation theorem transferring arbitrary abstract Boolean algebras
  into this set model is formalized. The theorem must be described as a result
  about atomless Boolean **subalgebras of sets**, not all abstract ABA structures.
- The named-AST adapter, parser, Python integer masks, caches, resource limits,
  status handling, and Python evaluator are **tested**, not formally verified.
- No theorem links these bytes to arbitrary Tau syntax, Tau/sbf interpretations,
  temporal recurrence, named/interpreted constants, mixed sorts, or C++ checker
  implementation. Native parser receipts do not close those gaps.
- No theorem here certifies the e-graph, cache/context keys, extracted costs,
  runtime improvement, native checker acceptance, or publication readiness.
- Minterm decomposition and atomless quantifier elimination are established
  mathematics. The potential contribution is the explicit checked artifact,
  executable reduction and bounded implementation evidence, not discovery of
  those underlying results.

The initial contracts and the explicit set-model scope amendment are in
`OBLIGATIONS.md`. Exact current source identities and results are in
`receipts/correspondence.json`; the leader must bind these regular files to a
revision before claiming revision-bound completed evidence.
