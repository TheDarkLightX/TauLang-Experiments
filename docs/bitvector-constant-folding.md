# Bitvector Constant Folding

This experiment extends the fixed-width modular arithmetic lane from law
triage to an optimizer-shaped artifact.

## Checked Kernel

The Lean packet proves constant folding plus identity simplification for a small
bitvector expression language:

```text
eval_w(simplify_w(e)) = eval_w(e)
```

The checked simplifier folds:

```text
const x + const y
const x * const y
```

and proves the identity rewrites:

```text
0 + x -> x
x + 0 -> x
0 * x -> 0
x * 0 -> 0
1 * x -> x
x * 1 -> x
```

using modulo `2^w` semantics. The key invariant is that every evaluated
subexpression is already a bounded bitvector value:

```text
bv_w(eval_w(e)) = eval_w(e)
```

## Runnable Corpus

Run:

```bash
python3 scripts/run_bitvector_constant_folding_demo.py \
  --width 4 \
  --count 80 \
  --out results/local/bitvector-constant-folding-demo.json
```

## Current Local Receipt

With width 4 and 80 generated cases:

```text
original nodes:              1540
constant-folded nodes:       1366
identity-simplified nodes:    626
constant-fold reduction:   11.299%
identity reduction:        59.351%
all semantic checks:        passed
```

The identity simplifier is reported separately because it is much stronger than
pure constant folding and depends on the bounded-value invariant.

The identity-rewrite proof has now been closed and independently returned by
Aristotle project `dc1acd60-175d-45a3-be53-dd037b6d94f2`. The returned project
was built locally and the Lean file was scanned clean for `sorry`, `admit`,
`axiom`, and `unsafe`.

## Boundary

This is a prototype optimizer lane. It is not Tau parser support, CVC5
integration, or a complete bitvector normalizer.
