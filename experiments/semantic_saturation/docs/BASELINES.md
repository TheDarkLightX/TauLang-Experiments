# Established Boolean simplifier baseline

Implementation status: implemented and unit-tested. Resource settings are provisional until the expanded protocol is frozen. No held-out outcomes informed this implementation.

## SymPy lane and semantic boundary

The baseline uses SymPy 1.14.0 `simplify_logic` with explicit CNF and DNF requests. Both emitted results compete with the unchanged input under the experiment's declared UTF-8 serializer. This is a constrained candidate comparison, not a claim of globally minimum expression size. SymPy's native normal-form objective is not this experiment's byte objective.

The adapter has two strictly separated modes:

- **Pure Boolean-algebra terms:** BA variables, 0/1, complement, meet, join, and XOR map pointwise to propositional logic. Propositional equivalence transfers to identities of Boolean-algebra terms; it does not establish validity of arbitrary BA formulas.
- **Formula skeletons:** each complete `eq0` or `ne0` atom is one opaque propositional symbol. An `exists` subformula is also one opaque symbol, including its binder and complete body. Only the surrounding logical connectives are simplified. Opaque subformulas are restored without inspecting, simplifying, substituting, or reinterpreting their BA variables. Distinct atoms need not be jointly realizable: equivalence for *all* assignments to the opaque symbols is a sound sufficient condition, but incompleteness is expected.

In particular, a quantified proper-split formula is not evaluated in the two-element algebra by this lane. A single such formula has a one-symbol skeleton and remains unchanged. Repeated occurrences can still be eliminated by propositional identities. Syntactically distinct equality and inequality atoms are not identified as complements by the adapter. Alpha-equivalent but differently named binders are not merged. Traversal stops at the whole quantified subformula, so inner bound-variable occurrences never become outer propositions.

Inputs must have a valid immutable tuple AST, declared sorts and free-variable interface, and the frozen non-temporal pure 0/1 Boolean-algebra context. Invalid shape, sort, context, interface, or input AST resource limits raise `ValueError`; they do not produce an apparently validated fallback.

## Public interface

Set `experiments/semantic_saturation/src` on `PYTHONPATH` and import:

```python
from baselines import run_sympy_baseline, measure_ast

result = run_sympy_baseline(
    ast, context,
    max_propositions=8,
    timeout_seconds=5.0,
    max_ast_nodes=10_000,
    max_ast_depth=100,
)
output_ast = result.output
json_safe_receipt = result.to_dict()
```

`result.status` is `ok` when both normal-form attempts completed and passed the local propositional check. It is `partial` when only one did, `capped` when the input proposition cap prevented both attempts, `timeout` when no attempt completed before the deadline, and `error` for other portfolio failure. Each candidate has its own status, including `invalid` for an explicit failed equivalence check. Successful local output still requires the harness's final gates.

The always-present original candidate has status `retained` and an identity receipt. CNF/DNF candidates record their exact output AST and costs even if they are larger and therefore lose selection. A failed local equivalence check is never eligible for selection. A resource- or error-limited portfolio keeps the original, or a previously completed eligible candidate.

## Determinism and size accounting

The authoritative expression is `native_oracle.typed_render(ast, context)`, preserving explicit variable type annotations. The primary metric is its exact UTF-8 byte count. A separate `file_bytes` metric includes the complete declared wrapper `expression + ".\n"`. This matches `study_core.metrics`; unit tests cross-check the independent metric implementation against it.

Selection minimizes `(emitted_utf8_bytes, tree_nodes, repr(output_ast))`, matching the main byte-first objective. If those are exactly tied, original precedes CNF, which precedes DNF. Retaining the original ensures the selected emitted expression cannot grow.

The following diagnostics are recorded independently by walking the tuple AST:

- `tree_nodes`: all expanded AST occurrences, counting every root and leaf as one node. Binder names are payload, not separate AST nodes.
- `dag_nodes`: the number of distinct immutable subtree tuples, including operator tags and binder names.
- `tree_depth`: maximum root-to-leaf node count, so a leaf has depth one.

`dag_nodes` is only a structural-sharing diagnostic. In particular, identical variable-name subtrees in different lexical scopes do not authorize sharing across those scopes. No DAG sharing or new definitions are introduced in emitted Tau. The primary emitted expression remains fully expanded. Raw native Tau output size is a separate metric owned by the native baseline.

Propositions are ordered by the UTF-8 bytes of their fully typed rendering, then by the complete AST representation. They receive names `p000000`, `p000001`, and so on. Each receipt records this whole input order and mapping, the exact context and its key, and the active SymPy symbol order after constructor simplification. The independent truth-table check uses input proposition `j` as bit `j` of each ascending integer assignment. SymPy's n-ary output is restored using its deterministic argument order and a left-associated binary AST. There is no uncharged tree-shape search.

## Resource and time accounting

SymPy is a separate method-native comparison on the original AST. Its proposals are not injected for free into matched-stream egraph controls. A best-of-native-and-SymPy portfolio, if reported, must charge both computations and all applicable final checks.

The baseline's explicit input proposition cap is provisionally eight. It is applied *before* SymPy constructor simplification; even a large expression that would immediately annihilate to zero can be capped. This avoids silently changing budget policy based on internal simplification. Both calls use `force=True` after the adapter's own cap, `deep=False`, and `dontcare=None`. No assumptions or don't-care assignments are invented.

One isolated POSIX `fork` worker attempts CNF, then DNF, under one shared five-second deadline, provisionally. The deadline begins at public-function entry, so preparation consumes budget too. Parent-side bounded validation/accounting is not asynchronously interrupted. The parent kills and reaps unfinished workers; process cleanup and final accounting can exceed the deadline and remain charged. An eligible CNF result survives a later DNF timeout. A form that never starts receives `deadline_exhausted`; an active form interrupted by the deadline receives `timeout`.

The full `wall_seconds` includes input validation and metrics, proposition mapping/order, process costs, dependency import, SymPy constructor auto-simplification, both simplifier calls, reverse mapping, local independent validation, output emission/metrics, selection, and cleanup. Phase diagnostics separately report preparation, import, initial mapping, each form's simplification/reverse mapping/check/emission, process-inclusive time, and cleanup. Phase totals should not be summed blindly: process-inclusive time contains the child's phases. `sympy_initially_loaded_in_worker` states whether fork inherited an already loaded SymPy; no unrecorded warm/cold equivalence is assumed. No reliable peak-memory metric is claimed here.

Each completed CNF/DNF candidate must pass an independent, SymPy-free truth-table evaluator. This evaluates the complete opaque-proposition assignment space, or the pure term's Boolean corners. The main harness separately owns and charges native Tau and independent BA final checks. A successful adapter receipt is not a claim that the final Tau/BA gate has accepted the output. The local exhaustive check is exponentially bounded and is not a scalable atomless-BA decision procedure.

The installed SymPy version is recorded in every result. Publication runs must pin 1.14.0 in their environment; this module reports other versions rather than silently pretending they are 1.14.0. The optional `dd` package was absent at design time and has not been installed. No BDD result is claimed. Adding a package or changing limits, ordering, or selection later requires a protocol amendment before dependent held-out measurements.

## Verification

Run the focused tests with the standard library:

```sh
python -m unittest discover -s experiments/semantic_saturation/tests -p test_baselines.py -v
```

The tests cover serializer/metric parity, UTF-8 accounting, CNF-versus-DNF selection, original fallback for compact XOR, constants, opaque atom and quantifier preservation, exact binder identity, deterministic order, explicit caps, invalid input, an inequivalence negative control, worker errors, kill-and-reap timeout behavior, partial-result retention, and sixteen seeded development terms checked independently against the pilot corner-signature evaluator. Those seeds and examples are unit/development data, not held-out results.

## Source

The official [SymPy 1.14 logic reference](https://docs.sympy.org/latest/modules/logic.html#sympy.logic.boolalg.simplify_logic) documents the CNF/DNF options, exponential simplification cost, and default eight-variable cutoff. The adapter enforces and reports its own cap instead of relying on a silent fallback. The referenced documentation identified itself as 1.14.0 when accessed on 2026-10-04; the installed implementation was also inspected at version 1.14.0 during development.
