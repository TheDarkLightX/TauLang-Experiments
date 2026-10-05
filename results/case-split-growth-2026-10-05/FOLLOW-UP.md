# Exploratory case-split growth budget for Tau issue 203

Thank you @andrei-idni for the report and reproduction generator. David, I am sharing this as an **exploratory patch suggesting a direction for discussion, not an official Tau patch or a complete fix for [#203](https://github.com/IDNI/tau-lang/issues/203)**.

The use case I tested is the one in the report: dispatch by ID through mutually exclusive `?:` branches, and a flat `||` condition with independent amount/key checks. Both fresh loading and live revision through `u[t] = i0[t]` matter. The results support reducing a case-split contribution to fresh-load cost. **The remaining revision cost is not solved.**

Baseline here means `devel` at `92b760179ac6412270e54369a2d225dd226fdf18`, with three shared Mac build corrections. The candidate adds only the growth-budget patch. These are new comparisons on that pin, not a retest of the report's `main` commit `3badb21a`.

| Freshly loaded rule | Baseline CPU | Candidate CPU | Baseline peak memory | Candidate peak memory |
| --- | ---: | ---: | ---: | ---: |
| 14 flat terms | 3.389 s | 0.201 s | 205.25 MiB | 37.88 MiB |
| 16 branches | 2.392 s | 0.719 s | 169.00 MiB | 77.11 MiB |
| 64 flat terms | not run | 0.772 s | not run | 82.00 MiB |
| 64 branches | not run | 3.375 s | not run | 243.27 MiB |

At 14 terms, that is **16.8 times faster with 81.5% lower peak memory**. Larger baseline points were omitted, so no speedup ratio is claimed for them.

These are medians of three fresh processes per configuration on an M3 Max, macOS 26.6.2, Clang 22.1.2, Release with LTO and the default seven algebras. Parser is `7d24705ac11863fa48261208134abc68e6c9cc1d`; Spot is 2.15.1. CPU includes startup, loading and checked steps. It is not directly comparable to the report's isolated load times.

The costly case arises when loading closes a rule as `all inputs ex output`. Splitting each keyed input can copy the existential output scope again. Applying those splits in succession can multiply the formula even though the original rule is small.

The suggested option, `--bv-case-split-max-growth`, defaults to **8**, with **0 meaning unlimited**. It charges cumulative expansion of substituted bodies against 8 times the original formula's distinct node count. On excess, it returns the entire original formula for the remaining solver pipeline. It does not turn an abandoned transformation into a verdict.

This is a heuristic, not a memory or runtime bound: bodies exist before counting, joining nodes are not charged, and later simplification does not refund earlier charges. A useful split can also be lost when the same call exceeds its allowance. The default remains an empirical choice.

Globally disabling case splitting is slightly cheaper on the growing examples, but removes useful transformations too. As a control, the existing [#107](https://github.com/IDNI/tau-lang/issues/107) controller took 0.200 s on baseline and 0.202 s with the budget. Budgets 1, 2, 8 and unlimited produced the expected outputs on the selected controller examples. This does not establish unchanged performance for every formula.

For correctness, **517 input combinations across three configurations passed all 1,551 evaluations** against independent unsigned-integer comparisons: baseline, candidate and baseline with `--bv-case-split false`. Outputs and step numbers are checked. Selected witnesses for the 12-term rule, with thresholds 1,000 through 12,000:

| Amount | Identifier | Keys supplied | Expected output |
| ---: | ---: | --- | ---: |
| 1,000 | 1 | none | 1 |
| 1,001 | 1 | none | 0 |
| 12,001 | 1 | all | 1 |
| 12,001 | 1 | all except the last | 0 |
| 16,777,215 | 0 | none | 1 |

The complete default Release suites passed: **2,718/2,718 baseline and 2,724/2,724 candidate CTest entries**, including all six added entries. Focused reduced-configuration checks passed **188** entries with `sbf,tau,bv` and **158** with `sbf,tau,qint`. The standard preset's test selection applies. Added checks cover exact rollback, independently known true/false formulas, useful simplification under a small allowance, a 20-term execution, and option handling.

The report's **384-bit declarations** also passed 54 input evaluations: fresh loading at 12 terms and 12 branches, revision at 10 terms and 12 branches, each in all three configurations. These use the generator's small numeric IDs/keys in wider declarations, not arbitrary high-bit values, and are completion checks rather than repeated benchmarks.

For the narrower 10-term revision, median process CPU remains 1.607 s with the patch, versus 2.095 s for baseline and 1.850 s with splitting disabled. The report's larger revision cases and reparse path were not repeated. These results do not establish linear scaling or resolve the whole reported use case.

Thanks to @taumorrow for the related simplification work in [#155](https://github.com/IDNI/tau-lang/issues/155) and [PR #156](https://github.com/IDNI/tau-lang/pull/156). That PR was not applied or benchmarked here.

The [patch](case-split-growth.patch), [results and limitations](RESULTS.md), and [reproduction ZIP](tau-203-case-split.zip) are available with [build and replay instructions](README.md) and [checksums](SHA256SUMS). The package includes all 195 timing attempts, input/output checks and test logs. The runner stops on wrong answers, wrong step numbers, nonzero exits or timeouts and retains every attempt.
