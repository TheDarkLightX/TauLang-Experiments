# Tau Derivative and Finite Equivalence Demo

This experiment is the executable companion to the c120 through c122 proof
lane. It is a standalone Tau-like kernel check, not a Tau parser feature and
not a runtime delta engine.

## Kernel

The expression language is intentionally small:

```text
const table
common
pointJoin
pointCompl
```

The carrier is the four-cell Boolean algebra encoded as 4-bit masks. A
constant leaf is a finite table from four keys to carrier values.

## Derivative Law

For a key `k`, replacement value `v`, and expression `e`, the demo checks:

```text
eval(derivative(k,v,e)) = update(eval(e), k, evalConst(e,v)).
```

Standard reading:

- Evaluating the derivative of `e` gives the original denotation of `e`, updated
  at key `k` by evaluating the expression shape with every constant leaf replaced
  by `v`.

Plain English:

- The derivative describes the semantic effect of a single-key perturbation.

The demo also checks the two local consequences:

```text
eval(derivative(k,v,e))(k) = evalConst(e,v)
```

and, for `k' != k`:

```text
eval(derivative(k,v,e))(k') = eval(e)(k').
```

## Finite Equivalence Law

The c121/c122 lesson is that the extended relation is algebraically complete for
the checked expression kernel, but executable equivalence still needs a
decidable semantic equality test.

On the finite carrier used here, that test is just:

```text
eval(e1) == eval(e2)
```

Standard reading:

- Two expressions are equivalent exactly when their finite denotation tables are
  equal.

Plain English:

- In the finite demo, complete equivalence checking is possible because the
  whole table can be compared.

Boundary:

- This finite decision rule does not make arbitrary infinite-carrier equivalence
  decidable.

## Run

```bash
python3 scripts/run_tau_derivative_equivalence_demo.py \
  --out results/local/tau-derivative-equivalence-demo.json
```

The benchmark wrapper also runs it:

```bash
./scripts/run_benchmarks.sh
```

## Current Receipt

With the default deterministic corpus:

```text
cases:                         80
derivative sound cases:        80
size-preserved cases:          80
away-from-key cases:           80
at-key cases:                  80
equivalence classifications:   80
equivalent cases:              61
non-equivalent cases:          19
result:                        passed
```

## Boundary

This demo does not prove:

- Tau parser integration,
- runtime cache correctness for real Tau nodes,
- whole-language delta evaluation,
- infinite-carrier equivalence decidability.

It does show that the c120/c121/c122 proof lane has an executable shape: local
derivatives for one-key changes and complete equivalence by table comparison on
a finite carrier.
