# Applying the guarded bit-vector patch to Tau

This patch adds a decision rule for a closed existential over one bit-vector of width 1–64 with concrete masks. Tau runs it on the translated quantifier-free matrix, before bounded BDD construction, when quantifier-free decision is enabled. The rule observes the configured maximum bit-blast width (default 16) and requires a nonzero quantifier-free BDD node limit. Raising the width limit allows inputs through 64 bits. A recognized formula is decided by clearing impossible bits from a candidate witness. An unsupported operator, free coefficient, or unsupported binder shape continues along the existing backend path. The rule honors the decision budget and uses the existing result cache.

## Apply and run the scoped upstream tests

Download `tau-guarded-bv.patch` to the directory where you will clone Tau, or run these commands from the extracted `guarded-bv` replay directory. Tau's normal source build requires its documented build dependencies.

```sh
git clone --branch devel https://github.com/IDNI/tau-lang.git
cd tau-lang
git checkout --detach ab7a13ed610ff6cfb8364dd2e509df74c9bdac6c
git apply --check ../tau-guarded-bv.patch
git apply ../tau-guarded-bv.patch
git submodule update --init external/parser
cmake --preset release-tests-bvonly
cmake --build --preset release-tests-bvonly --target test_integration-bv_quantifier_free_decision
ctest --test-dir build/release-bvonly -R '^test_integration-bv_quantifier_free_decision$' --output-on-failure
```

The same patch passes `git apply --check` on `42a6e977cf1dd9d452ad30384e69e37714f68f9e`, the later `devel` revision checked for this handoff. Applying it there produced the same three source and test files, byte for byte. The patch SHA-256 is `39ebe302b3f7ddc8298a3e6dba58243db1ae85774b6e855d5911644a7e1cf128`.

## Native checks

The focused build uses the pinned Tau source and parser, Clang 19.1.7, and Tau's published Linux v0.8.5 SDK for libraries and generated pack headers. Full-project CI on a clean build remains open.

On the pinned source, 81 fresh processes parsed Tau formulas and called the patched native BV decision function. All 81 verdicts matched the expected answers. The rule fired on the 64 mixed-mask cases and six SAT/UNSAT cascades at widths 3, 8 and 16. The other eleven used the fallback, including eight cases wider than the default cap and queries with a universal binder, a complemented variable or a free coefficient. The input, expected verdict, observed verdict and route are included in the replay. The C++ reference separately checked 17,472 formulas by exhaustive enumeration. Rechecking the Lean source reproduced all five declarations' recorded axiom reports.

## What the proof covers

The kernel-checked Lean theorem proves that one guarded mask elimination procedure computes a greatest feasible witness and that every upward-closed terminal condition can be checked on that witness. Zero-mask restrictions give the initial upper bound. Conjunctions of positive mask-hit requirements are upward closed. The native code rescans the guards until no bits change. Every clear preserves the upper bound on all feasible witnesses, and at a fixed point that bound satisfies the guards. With at most 64 bits, at most 64 passes can strictly change the bound. The Lean project checks the abstract elimination rule. The integration tests exercise the C++ recognizer, dispatch and iteration order.

## Timing scope

The 79.26 ms and 1.97 ms medians in the proposal measure the stock string API and an external frontend on a 16-bit cascade. Both include input processing. The archived raw measurements identify their executable and interface.

A separate C++ comparison timed the patched rule on already-built cvc5 expressions against Tau's bounded BDD decision. The candidate arm calls the BDD on a declined input, so each row includes the cost of finding a match or rejecting the expression. Both arms saw the same terms, checked against exhaustive enumeration. Twelve paired blocks per corpus alternated execution order. The ratio is the median of paired ratios. The time columns give each arm's median separately.

| Corpus | BDD, µs/query | Guard then BDD, µs/query | BDD / candidate |
|---|---:|---:|---:|
| One guard | 13.63 | 3.36 | 3.99× |
| Four mixed guards | 33.64 | 8.30 | 4.02× |
| Fourteen mixed guards | 81.08 | 26.24 | 3.23× |
| Eight-bit cascade | 48.34 | 13.66 | 3.48× |
| Unsupported expression encountered early | 79.49 | 80.71 | 0.99× |
| Unsupported expression encountered late | 78.07 | 103.30 | 0.76× |

The late rejection cost about 32% more time. These workloads do not establish how frequently Tau encounters these shapes or the net effect on a representative application. The extracted replay includes `typed-comparison/README.md`, the source, all 144 observations and the script that computed this table.
