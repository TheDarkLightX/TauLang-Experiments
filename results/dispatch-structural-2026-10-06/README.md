# Lower revision cost for bounded dispatch rules

This is an exploratory extension to the [case-split growth proposal for Tau issue #203](https://github.com/IDNI/tau-lang/issues/203#issuecomment-6005107958). It addresses the report's flat amount/key conditions and exclusive dispatch branches, including revision through `u[t] = i0[t]`. It is a suggested implementation direction, not an official Tau patch or a complete resolution of the issue.

The 12-term revision example fell from **8.100 s to 0.243 s of total CPU, a 33.3-times improvement over the growth guard alone**. Separating the components shows that most of this gain comes from deciding eligible memoryless formulas in one step. Structural elimination adds about 1.15 times beyond that. Repeated-step totals changed little.

- [Concept map, rejected paths, witness argument and notation legend](CONCEPT-MAP.md)
- [Build and replay instructions](REPRODUCE.md)
- [Complete candidate patch](patches/combined-candidate.patch)
- [One-step decision addition](patches/one-step-decision.patch)
- [Structural runtime addition](patches/structural-runtime.patch)
- [Recorded evidence archive](evidence.zip)

## What changes

1. **Keep the growth guard.** Case splitting can multiply a small formula. The guard abandons an expanding transformation and returns its original input to the remaining solver pipeline. Its default is an empirical heuristic, not a memory or runtime guarantee.
2. **Use a single-step decision for eligible memoryless formulas.** For `always body`, where all streams refer to the current step and the supported body contains no temporal dependency, close the relation over inputs and outputs once. Realizability asks whether every input has an allowed output. Trace validity asks whether every input/output combination satisfies the relation. The helper returns to the existing path for unsupported shapes or an undecided result.
3. **Eliminate output quantifiers while useful structure remains.** Recognize complete guarded definitions, check their coverage with the bitvector solver, and permit larger conditional trees while retaining a bound on clause expansion. A separate identity removes an existential variable used only in positive comparisons against closed forbidden values when a spare value exists. It is tried independently of a previously failed definition search. Scope checks and the domain-size condition are required. This group also asks the solver first for closed formulas whose quantifiers are all of one kind. Its components were measured together, so the additional gain is not attributed to the disequality identity alone.

The complete patch also includes regression tests and option documentation. The growth guard's accounting charges cumulative substituted-body node instances, not exact added nodes or total memory. It can discard useful partial work on rollback. The structural clause ceiling changes from 16 to 256, with a tighter per-conjunct limit based on atom count. Neither number establishes an optimal default.

## Measured contributions

Median total process CPU, three repetitions per cell:

| Input and route | Growth guard | Guard + one-step decision | Combined candidate |
| --- | ---: | ---: | ---: |
| 12 flat terms, fresh load and 3 steps | 0.180897 s | 0.183198 s | 0.174877 s |
| 16 exclusive branches, fresh load and 6 steps | 0.711934 s | 0.741216 s | 0.671325 s |
| 10 flat terms, revision and 3 checked steps | 1.674587 s | 0.274917 s | 0.225777 s |
| 12 flat terms, revision and 3 checked steps | 8.099730 s | 0.281225 s | 0.243497 s |
| 16 exclusive branches, revision and 6 checked steps | 1.019557 s | 0.969635 s | 0.836496 s |
| 12 flat terms, fresh load and 60 steps | 0.424572 s | 0.422216 s | 0.419505 s |
| 16 exclusive branches, fresh load and 120 steps | 2.137410 s | 2.142574 s | 2.086050 s |

For the 12-term revision, median sampled peak RSS was **129.44 / 45.05 / 40.70 MiB**, in the same column order. The combined result is about 68.6% below the growth-only reference. Sampling can miss brief peaks.

All 63 attempts passed, including 1,809 expected outputs. Variant order alternates across repetitions. CPU includes startup, loading or revision, and the stated steps; these are not isolated load times or warm-step measurements. Small differences in the load and repeated-step rows should not be treated as established improvements.

Tau is pinned to `92b760179ac6412270e54369a2d225dd226fdf18`, parser to `7d24705ac11863fa48261208134abc68e6c9cc1d`. Hardware: Apple M3 Max, 128 GiB RAM; macOS 26.6.2; Clang 22.1.2; Spot 2.15.1; Release with LTO, effective `TAU_CACHE=ON` and the default seven algebras. Identical Mac build corrections apply to each variant. This is not a comparison against the report's older `main` revision or current `devel`.

## Concrete revision witness

For the measured 12-term rule, set the selected ID to 1 and the amount to 12,001, above all twelve thresholds. The generated keys are distinct nonzero values.

| Step after installing the rule | Supplied keys | Expected and observed `o5` |
| --- | --- | ---: |
| 2 | Every key input is 0 | 0 |
| 3 | Every key matches its required value | 1 |
| 4 | All keys match except the last, which is 0 | 0 |

The recorded inputs also check that `o1` preserves the amount in the broader output and reparse checks. A fast completion without the expected output sequence does not count as a pass.

## Correctness evidence and rejected assumptions

- The independent command bank enumerates **66,318 assignments for 414 formulas**, at bit widths 1, 2 and 3. Each of the three variants returned all **828 expected satisfiability/validity answers**. Each width uses a fresh process and every answer is matched to its echoed command.
- Direct native checks compare all 414 rows with the earlier implementation and independently check satisfiability and trace validity. The new helper accepts **718 decisions** with the expected answers and declines **110**. Seven additional unsupported categories also decline: lookback, initial-time references, eventual formulas, nested eventual formulas, time constraints, embedded Tau constants and QLT values.
- All **172 native tests** passed across the initial run and a targeted retry. Initially, 131 passed; the build-setup step timed out after 1,500 seconds while rebuilding after a Git display-metadata change, leaving 41 tests unstarted. Those 41 and the interpreter executable whose bytes changed passed on retry using already-built binaries. Both changed command tests also passed. The timeout is retained, not counted as a successful setup run.
- Earlier checks retained here include **4,480 finite answers**, **1,551 output cases**, printed-rule reparse checks, full-pattern 384-bit inputs, and **2,566 command tests**. Seven of the initial command tests failed because their child compiler could not find the C++ standard library; all seven passed with the documented compiler/SDK environment. The earlier patch's runtime bytes match the combined binary used for the new measurements; later source changes restored and clarified tests.
- A bounded search over **128 condition variants of one supplied identity** refuted 125. Three survived the finite bank, representing two observed behaviors. This is counterexample-guided refinement of rule conditions, not discovery of a new identity, a trained model, or proof of a globally optimal rule set.
- Unlimited splitting slowed one earlier Tau-valued control from about 0.149 s to 1.274 s in a single-pass screen. That supports retaining the guard; it does not establish that unlimited splitting is always slower.
- A separate constant-top experiment produced identical answers in the growth-only and combined builds. Its 78 differences from an assumed trace-validity oracle are **not established optimizer regressions**: the assumed entry-point equivalence was not justified. Direct checks and the source's input-handling contracts were examined, but the constant-top interpretation remains unresolved.

The mathematical justification and finite counterexamples are in the [concept map](CONCEPT-MAP.md). Other algebra selections, broader applications and composition with the upstream functional path still need testing. A finite bank and agreement with an earlier implementation do not prove every internal semantic contract.

## Relationship to upstream work

The first branch of the map follows @taumorrow’s approach: recognize output definitions before normalization obscures their structure ([#175](https://github.com/IDNI/tau-lang/pull/175)), then evaluate those definitions directly ([#179](https://github.com/IDNI/tau-lang/pull/179)). Thank you for helping clarify where we can avoid solver work altogether. Those PRs were not applied in these measurements; testing them together with this candidate remains a separate step.

## Reading the records

Extract `evidence.zip`, then run both supplied record checks:

```sh
unzip evidence.zip
python3 -B repro/verify_followup_records.py .
python3 -B repro/verify_earlier_records.py
```

The first checks the new component comparison, independent decision bank and native-test accounting. The second checks the earlier search, timings, output and command-test records. `MANIFEST.sha256` covers both the archive and the extracted files. Absolute local paths were shortened in public logs and command records, and one upstream diagnostic label and punctuation were restyled; published hashes cover those copies. Source pins, binary hashes, outcomes, timing values and failed attempts are preserved. Compiler-derived timing lines in correctness-test logs were collected during other work and are not performance evidence.
