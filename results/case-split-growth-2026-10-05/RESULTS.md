# Results and limits

This is an exploratory implementation and a suggestion for discussion. It is
not an official Tau patch or a complete fix for [issue 203](https://github.com/IDNI/tau-lang/issues/203).

## Match to the reported use case

The report describes ID dispatch through mutually exclusive branches and a
flat condition of independent amount/key checks, loaded either as a fresh
specification or a live revision through `u[t] = i0[t]`. Both generated rule
shapes and both loading paths are tested here. These are comparisons on the
`devel` pin in README.md, not a retest of the report's `main` commit `3badb21a`.
The patch reduces case-split growth during fresh loading. Revision still has
substantial separate cost; the report's larger revision cases and reparse
path were not repeated. Linear scaling is not established.

Baseline means that pinned source with the three shared Mac build corrections.
Candidate means the same source and corrections plus the growth-budget patch.

## Change and correctness argument

The proposed option, `--bv-case-split-max-growth`, gives one case-split call
a cumulative expansion budget. The default is 8 times the input formula's
distinct node count. CLI/REPL value 0 selects unlimited expansion.

For each case analysis, count the distinct nodes in the substituted bodies
together, subtract the replaced body's size, and charge any positive excess
against the remaining allowance. Shared nodes count once within that group.
Boolean-algebra constants are opaque to the count. If the allowance is
exceeded, return the whole original input formula to the remaining pipeline.
Within the allowance, use the existing case-split result.

This changes an optional transformation decision. It does not approximate an
answer or treat an abandoned transformation as a proved verdict. The direct
C++ tests check exact tree identity after rollback, a total function known to
be true, and its negation known to be false. The output checks use independent
integer arithmetic, so baseline agreement is not their only correctness test.

The budget is a heuristic. Substitution occurs before counting; joining nodes
are not charged; later simplification does not refund earlier charges. This
does not bound peak memory, total work or final formula size. The default 8
has not been proved optimal. A formula that needs a useful split but shares
its call with a costly split can still lose that optimization on rollback.

## Measured results

All figures below are medians of three successful fresh processes on the
environment in `README.md`. CPU means user plus system CPU for the whole
process, including loading and checked steps. Memory means the median of
the three per-process peak resident-memory measurements. These are not
isolated solver-stage times or end-of-run memory samples.

| Freshly loaded rule | Baseline CPU | Patched CPU | Case split disabled CPU | Baseline peak MiB | Patched peak MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8 flat terms | 0.157 s | 0.158 s | 0.156 s | 30.25 | 30.38 |
| 9 flat terms | 0.191 s | 0.155 s | 0.149 s | 38.19 | 34.31 |
| 12 flat terms | 0.714 s | 0.180 s | 0.174 s | 76.06 | 36.45 |
| 14 flat terms | 3.389 s | 0.201 s | 0.196 s | 205.25 | 37.88 |
| 20 flat terms | not run | 0.258 s | 0.246 s | not run | 42.61 |
| 64 flat terms | not run | 0.772 s | 0.658 s | not run | 82.00 |
| 12 branches | 0.757 s | 0.522 s | 0.507 s | 84.77 | 64.09 |
| 16 branches | 2.392 s | 0.719 s | 0.679 s | 169.00 | 77.11 |
| 64 branches | not run | 3.375 s | 2.920 s | not run | 243.27 |

At 14 terms, this is 16.8 times faster and 81.5% lower peak memory. The
case-split-disabled control is the baseline executable with
`--bv-case-split false`. It is slightly cheaper on these examples, but disabling
the pass globally also removes useful transformations on other inputs.
The patch keeps the pass available when its charge fits the allowance.

Larger baseline points were omitted after an earlier baseline build failed
on a 24-branch input. That earlier executable and dependency build differ
from the final rebuilt pair, so the failure is not assigned to the final
binary here. No speedup ratio is claimed for omitted comparisons.
The full 17-point results, including every repeat, are in
`evidence/rule-measurements/`. Amounts and numeric outputs are 24-bit.
Identifiers and keys are 8-bit except for the 64-branch input, which uses
16-bit values to hold its last key. The 384-bit variant has a separate bounded completion check below; it is
not part of these repeated timings.

| Additional example | Baseline CPU | Default budget CPU | Baseline peak MiB | Default budget peak MiB |
| --- | ---: | ---: | ---: | ---: |
| Existing #107 controller | 0.200 s | 0.202 s | 34.88 | 34.83 |
| Controller plus 9-key rule | 0.411 s | 0.320 s | 52.94 | 45.80 |
| Controller plus 12-key rule | 1.484 s | 0.355 s | 120.17 | 47.91 |
| 10-key rule with Tau-valued output | 1.282 s | 0.156 s | 54.95 | 34.73 |

The controller's CPU difference is less than 1%, with three observations per
configuration. This is evidence from the selected examples, not a general
no-regression guarantee. Budgets 1, 2, 8 and unlimited all produced the checked
outputs. Unlimited restores approximately the baseline costs in the growing
examples. The raw controller runs are retained separately from the rule runs.

## Answer checks

There are 190 input combinations for a 12-term rule and 327 for a 12-branch
chain. Each runs on baseline, candidate and case-split-disabled baseline:
1,551 input evaluations in total. All pass. Expected output is computed by
unsigned integer comparisons, and the echoed amount and step numbers are
also checked. The tested values cover threshold minus one, the threshold,
threshold plus one, zero and the largest 24-bit amount, matching and missing
keys, alternating keys and fallback identifiers.

Selected witnesses for the flat 12-term rule, with thresholds 1,000 through
12,000 and expected key `j + 1` for term `j`:

| Amount | Identifier | Keys | Expected `o5` | Reason |
| ---: | ---: | --- | ---: | --- |
| 1,000 | 1 | none | 1 | The first threshold is not exceeded. |
| 1,001 | 1 | none | 0 | The first threshold is exceeded and its key is missing. |
| 1,001 | 1 | alternating, starting with the first key | 1 | The only active threshold has its key. |
| 12,001 | 1 | all | 1 | Every exceeded threshold has its key. |
| 12,001 | 1 | all except the last | 0 | The last required key is missing. |
| 16,777,215 | 0 | none | 1 | The fallback identifier selects output one. |

All three configurations agree with these independently computed values.
The additional controller checks also require a zero exit status and the
known output values. A correct output followed by an error is a failure.

## Wider declarations

All 54 input evaluations passed across 12 additional processes using 384-bit
ID/key declarations: 12 flat terms and 12 branches on fresh loading, 10 flat
terms and 12 branches on revision, each on baseline, candidate and baseline
with splitting disabled. These retain the report generator's small numeric
IDs/keys in wider declarations; arbitrary high-bit values were not tested.
Amounts and outputs remain 24-bit. Both output values and step numbers pass,
and executable hashes match the final measured pair before and after replay.
These single runs establish completion and checked answers, not repeated
timing estimates. See `evidence/wide-checks/` and `repro/check_wide.py`.

## Upstream tests

The complete default `release-tests` runs passed: **2,718 of 2,718 baseline
CTest entries and 2,724 of 2,724 candidate entries**, with zero failures.
Every common entry passed in both builds; all six additional candidate
entries passed. The default-suite comparison and complete CTest console
logs are in `evidence/tests/`. These counts are CTest entries, some of which
contain multiple C++ test cases.

Completed additional checks:

| Configuration | Scope | Result |
| --- | --- | --- |
| `sbf,tau,bv` | Case-split, API-limit and pack C++ suites, option commands, new CLI and 20-term run checks | 188 CTest entries passed |
| `sbf,tau,qint` | API-limit and pack C++ suites plus applicable option commands | 158 CTest entries passed |
| Default pack | Six newly added REPL/CLI entries, run separately | 6 passed |

The reduced configurations received these focused checks, not complete suite
runs. The case-split C++ suite includes forced rollback, unlimited mode,
useful simplification under a small allowance, and independently known true
and false formulas. The build corrections are identical in baseline and
candidate, including the qualified name needed by one existing Mac test.

## Remaining revision cost

Updating a running specification is still substantially more expensive for
some rules. At 10 flat terms, total process CPU is 2.095 s for baseline,
1.607 s for the patch and 1.850 s with case splitting disabled. The freshly
loaded patched rule takes 0.160 s. These process totals have different
startup/update sequences, so they are not an isolated revision-stage ratio.
This patch does not claim to solve the remaining update cost.

Related simplification work is discussed in [#155](https://github.com/IDNI/tau-lang/issues/155)
and [PR #156](https://github.com/IDNI/tau-lang/pull/156). Thanks to @taumorrow
for that contribution. PR #156 was not applied or benchmarked here.

## Evidence quality

All 135 rule timing attempts, 60 controller timing attempts and 1,551
independent-reference input evaluations passed. Competing builds were paused
for timing runs; correctness-only runs were allowed to overlap compilation.
Binary hashes match before and after each campaign. Raw input/output hashes
were independently checked after preparing this package. The runner was
checked against wrong output, wrong step numbering, nonzero exit status and
timeout outcomes. It preserves failed attempts and stops on failure.
