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
