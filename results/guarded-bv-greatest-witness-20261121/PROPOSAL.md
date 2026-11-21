# Decide closed bit-vector mask implications by propagating a greatest witness

A closed existential bit-vector formula can be decided by clearing bits from one candidate when its clauses have the shape below. On a 16-bit cascade, an external recognizer reduced the median `tau.sat` string call from **79.26 to 1.97 ms**. A separate stored-expression control puts most of the saving in input processing. I’m sharing the C++ implementation and proof so the team can evaluate where this belongs.

### Recognized formula

For concrete, same-width masks `y`, `u[i]` and `v[i]`, find a nonzero `x` with `(x & y) = 0` and one clause per pair:

```text
((x & u[i]) = 0) || ((x & v[i]) != 0)
```

Start at the width-limited complement of `y`. If `(bound & v[i]) == 0`, every remaining witness must satisfy the left arm. Clear `u[i]` from the bound and discharge that clause. Once every remaining positive arm holds, the bound itself satisfies all the clauses and contains every feasible value. A nonzero solution exists exactly when the bound is nonzero. Each clause can be discharged once. The simple rescanning implementation is quadratic in the clause count in the worst case.

This two-bit query returns `F`. The bound falls from 3 to 1 to 0. Removing the last clause makes the query satisfiable.

```text
sat ex b:bv[2] (b != 0 && (b & {0}:bv[2]) = 0
  && (((b & {1}:bv[2]) = 0) || ((b & {2}:bv[2]) != 0))
  && (((b & {2}:bv[2]) = 0) || ((b & {0}:bv[2]) != 0))).
```

The polarity check matters. In two-bit mask notation, `((x & 1) == 0) || (((~x) & 2) != 0)` accepts 1 and 2 but rejects their join, 3. The recognizer declines this form.

### What was measured

Both arms received identical source text on `devel` at `ab7a13ed`, with the default bounded BDD and quantifier-free decision settings. The external frontend recognized the full expression, propagated the bound, and submitted a short ground formula to the same native API. On a mismatch it passed the original text through. Six fresh-process pairs per case alternated arm order on one logical CPU of a shared AMD EPYC 9V74.

| Input | Stock → guarded call, median ms | Whole process, median ms |
|---|---:|---:|
| 14 guards, SAT | 86.94 → 2.32 | 192.56 → 110.81 |
| 14 guards, UNSAT | 71.29 → 1.99 | 165.24 → 88.93 |
| 16-bit cascade, UNSAT | 79.26 → 1.97 | 166.81 → 85.92 |
| 32-bit independent masks, SAT | 93.19 → 2.40 | 190.69 → 88.54 |
| Unrecognized 14-guard input | 72.96 → 69.84 | 164.21 → 158.16 |

All 60 verdicts matched. Another four-guard fallback sample was slower, 22.91 → 24.64 ms. On the stock 0.8.5 CLI (`a584081`), `whatis FORMULA` on the 16-bit cascade took 70.44 → 2.66 ms for inspection, printing and storage. The first `sat %1` then took **3.02 → 1.20 ms**, including dispatch and printing. A C++ change downstream of parsing cannot claim the string-API gain.

### Code and reproduction

The C++17 implementation checks against exhaustive enumeration on 17,472 two-bit formulas (69,888 witness assignments). The packet also includes a Lean proof, 202 expected native decisions, exact inputs, paired observations and commands. [C++ reference](https://github.com/TheDarkLightX/TauLang-Experiments/blob/ac5f476f983706219514afc31a7a8719a38318ac/results/guarded-bv-greatest-witness-20261121/guarded_bv.hpp) · [Lean proof](https://github.com/TheDarkLightX/TauLang-Experiments/blob/ac5f476f983706219514afc31a7a8719a38318ac/results/guarded-bv-greatest-witness-20261121/GuardedWitness.lean) · [Reproduction packet](https://github.com/TheDarkLightX/TauLang-Experiments/blob/ac5f476f983706219514afc31a7a8719a38318ac/results/guarded-bv-greatest-witness-20261121/README.md)

This extends the single-witness observation in #152 to mixed guards that require repeated reductions. It complements the clause pruning in #151 and bounded BDD decision in #184. Would an early typed recognizer be useful here? The alternative placement after the existing BV cache and budget checks can be assessed by timing recognition on the original typed tree. [Pinned BV decision path](https://github.com/IDNI/tau-lang/blob/ab7a13ed610ff6cfb8364dd2e509df74c9bdac6c/src/boolean_algebras/bv/bv_ba_solver.tmpl.h#L769-L815)

OpenAI ChatGPT assisted with the reference implementation, proof and measurements.
