# Restricted Tau Rewrite Normalizer

This note documents the executable companion to the c111 Lean proof.

The proof-backed claim is scoped:

```text
Inside the restricted seven-rule rewrite theory, normalization terminates,
preserves denotation, is confluent, and has unique normal forms.
```

It is not a proof of complete Boolean-algebra equivalence for all Tau
expressions.

## Rule Set

The executable normalizer implements these oriented rules:

```text
common(a, a)                         -> a
pointJoin(a, a)                      -> a
common(a, pointJoin(a, b))           -> a
pointJoin(a, common(a, b))           -> a
pointCompl(pointCompl(a))            -> a
pointCompl(common(a, b))             -> pointJoin(pointCompl(a), pointCompl(b))
pointCompl(pointJoin(a, b))          -> common(pointCompl(a), pointCompl(b))
```

The rules for commutativity, associativity, and distributivity are deliberately
absent. As oriented rewrite rules, they can cause loops or uncontrolled growth.

## Measure

The termination measure is:

```text
M(const) := 1
M(common(a,b)) := M(a)+M(b)+1
M(pointJoin(a,b)) := M(a)+M(b)+1
M(pointCompl(a)) := 3*M(a)+1
```

The factor `3` on `pointCompl` is the important engineering move. It gives
enough budget for De Morgan rewrites to decrease the measure even when the
surface expression becomes wider.

## Demo

Run:

```bash
python3 scripts/tau_kb_normalizer.py normalize \
  'pointCompl(common(a, pointJoin(a, b)))' \
  --json
```

Expected shape:

```text
input:       pointCompl(common(a, pointJoin(a, b)))
normal form: pointCompl(a)
```

The script also checks Boolean semantic parity between the input and the normal
form on all valuations when the variable set is small.

## Benchmark

Run:

```bash
./scripts/run_benchmarks.sh
```

The benchmark writes:

```text
results/local/kb-normalizer-benchmark.json
```

The current benchmark is a deterministic corpus benchmark for the normalizer
itself. It is not a Tau Language runtime benchmark and should not be cited as a
Tau speedup unless the normalizer is later wired into a Tau execution path and
measured there.

## Tau Qelim Probe

The patch also exposes an opt-in qelim experiment flag:

```bash
TAU_QELIM_BACKEND=bdd \
TAU_QELIM_BDD_KB_REWRITE=1 \
TAU_QELIM_BDD_STATS=1 \
external/tau-lang/build-Release/tau --charvar false \
  -e 'qelim ex x !((x = 0) && ((x = 0) || (a = 0)))'
```

The reproducible probe is:

```bash
python3 scripts/run_qelim_kb_probe.py
```

The current probe checks formulas designed to expose absorption, De Morgan, and
double-complement opportunities. It requires the patched Tau binary. It compares
the BDD qelim backend with and without `TAU_QELIM_BDD_KB_REWRITE=1` and fails if
the outputs differ.

Current local receipt:

```text
5 qelim probes
5 matching outputs
0 output mismatches
```

The pass reduced compiled expression nodes on the targeted absorption probes,
for example `6 -> 2` and `5 -> 1`.

Boundary: timings on this tiny corpus are mixed and noisy. The result supports
"this pass can simplify the compiled qelim expression without changing output,"
not "this is a promoted Tau speedup."

## Generated Matrix Result

The larger generated matrix is opt-in:

```bash
RUN_QELIM_KB_MATRIX=1 ./scripts/run_benchmarks.sh
```

It compares:

```text
bdd
bdd+kb
bdd+ac
bdd+ac+kb
```

Current research conclusion:

- `bdd+kb` preserved output parity on the generated matrix.
- `bdd+kb` consistently reduced compiled expression nodes on the targeted
  absorption-heavy formulas.
- The profit guard discarded rewrites whose normal form would have increased
  node count.
- Timing remained mixed. A wider generated corpus showed a small internal
  improvement, while the smaller repeated corpus did not.

So the promotion decision is:

```text
keep TAU_QELIM_BDD_KB_REWRITE opt-in
do not make it default yet
```

The next useful optimization target is a selector that predicts when the KB pass
is worth running, rather than always running it after compilation.

## How This Helps Tau Optimization

The useful compiler pattern is:

```text
source expression
  -> restricted rewrite normalization
  -> AC canonicalization, if separately proved
  -> fragment-sensitive qelim dispatch
  -> solver or runtime path
```

The c111 result supports only the first arrow. It is still valuable because it
turns a fragile list of simplification rules into a checked normalizer with a
termination and confluence story.
