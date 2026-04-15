# Equality-Aware Path Simplification

Tau's README lists this known issue:

```text
Path simplification algorithm does not take equalities between variables
into account leading to later blow ups.
```

This note records the first proof-shaped experiment for that issue.

## Core Law

If a path entails that variables equal their representatives, then replacing
each variable by its representative preserves evaluation on that path.

```text
env(rep(x)) = env(x) for every x
implies
eval(env, subst(rep, e)) = eval(env, e)
```

Standard reading: if the current environment gives every variable the same
value as its representative, then evaluating the representative-substituted
expression gives the same Boolean value as evaluating the original expression.

Implementation reading: equality-aware path simplification is safe only inside
the path scope where those equalities are known. The representative map must not
escape into unrelated branches.

## Proof Receipt

The Lean packet is:

```text
tau_equality_path_simplification_2026_04_15
```

It proves:

- representative substitution preserves evaluation under the `Respects`
  premise,
- a single equality `x = y` is enough to justify replacing `y` by `x`,
- representative substitution is unsound without the equality premise.

Boundary: this is a small Boolean-expression kernel. It is not yet a theorem
about Tau's full C++ normalizer.

## Executable Demo

Run:

```bash
python3 scripts/run_equality_path_simplification_demo.py \
  --out results/local/equality-path-simplification-demo.json
```

Current local receipt:

```text
cases:                 3
original nodes:        29
optimized nodes:       10
node reduction:     65.517%
semantic checks:       passed
```

The demo also records counterexamples outside the equality assumptions. This is
important. Replacing aliases by representatives is not globally valid; it is
valid only on paths where the required equality facts hold.

## Related Tau Recombination Probe

The standalone model checks representative substitution under path equalities.
The current Tau binary already handles simple branch-local equality reductions,
for example:

```text
normalize (x = y:sbf && ((x & y') = 0))
```

returns:

```text
x = y
```

The remaining Tau-facing probe is therefore more specific. It asks whether Tau
can recombine branches after an equality split has created a longer residual
normal form.

The recombination law itself is not equality-specific:

```text
(A and B) or ((not A) and B) iff B
```

The equality split matters because equality-path simplification can create
exactly this shape in Tau's normalizer.

Run:

```bash
python3 scripts/run_equality_split_tau_probe.py \
  --out results/local/equality-split-tau-probe.json
```

The probe uses Tau itself for the equivalence check:

```text
solve --tau !(original <-> target)
```

The expected answer is:

```text
no solution
```

Current local receipt:

```text
cases:                         4
useful reduction cases:        4
matched target cases:          0
Tau-normalized characters:   152
target-normalized characters: 36
character reduction:      76.316%
equivalence checks:       passed
```

Example:

```text
original Tau normal form:
x = y || y'x = 0

target normal form:
y'x = 0
```

Tau proves the original formula and target formula equivalent by returning
`no solution` for the negated equivalence query. The current normalizer still
prints the longer form.

Boundary: this is evidence of a branch-recombination opportunity after
equality-path simplification. It is not evidence that Tau lacks all
branch-local equality substitution, and it is not yet a Tau patch that performs
the recombination automatically.

## Feature-Gated Tau Patch Attempt

The experiment patch now includes a first feature-gated C++ recombination pass:

```bash
TAU_EQUALITY_SPLIT_RECOMBINE=1 python3 scripts/run_equality_split_tau_probe.py \
  --out results/local/equality-split-tau-probe-enabled.json
```

Current enabled receipt:

```text
cases:                         4
matched target cases:          3
target-sized cases:            4
Tau-normalized characters:    36
target-normalized characters: 36
```

Interpretation: the pass now closes the measured reduction opportunity on this
small corpus. Three cases match the target normal form textually. The
three-alias case reaches the same normalized size, but Tau prints an equivalent
term ordering, so it is not counted as a textual target match.

Extended alias-order smoke test:

```bash
TAU_EQUALITY_SPLIT_RECOMBINE=1 python3 scripts/run_equality_split_tau_probe.py \
  --extended \
  --out results/local/equality-split-tau-probe-extended-enabled.json
```

Current extended receipt:

```text
cases:                         8
matched target cases:          3
target-sized cases:            8
Tau-normalized characters:   108
target-normalized characters: 108
```

The extra cases permute the three-alias equality path. They check that the pass
handles direct and transitive alias representatives, not only the first
hand-written equality order.

## Tau Implementation Shape

A conservative Tau implementation should be feature-gated and path-scoped:

```text
TAU_EQUALITY_PATH_SIMPLIFY=1
```

Safe implementation outline:

```text
for each conjunction path:
  collect variable equalities
  build a representative map for that path
  substitute representatives only in that path body
  run existing Boolean simplification
  fall back to old path if extraction is incomplete
```

The promotion gate should require:

- output parity on existing normalization and solver corpora,
- explicit counters for collected equality classes and substituted variables,
- no representative substitution outside the branch where the equalities hold,
- a wider Tau-native benchmark before default enablement.

This is a stronger next target than raw variable-name caching because it is
named directly by Tau's known-issues list and has a precise semantic premise.
