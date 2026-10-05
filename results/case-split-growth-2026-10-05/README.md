# Tau issue 203: Mac validation of the case-split growth budget

This is an exploratory implementation offered as a direction for discussion,
not an official Tau patch or a complete fix for [issue 203](https://github.com/IDNI/tau-lang/issues/203).
It addresses case-split growth in the report's two generated rule shapes on
the pinned `devel` version. Larger live revisions and the reparse path still
need investigation.

The refined patch passes the full default Release suites: 2,718 baseline
and 2,724 candidate CTest entries, with no failures. The independent integer
checks pass all 1,551 input evaluations. At 14 flat terms, median process CPU
falls from 3.389 s to 0.201 s and median peak RSS from 205.25 to 37.875 MiB.
The remaining revision cost is not solved. A separate 384-bit declaration
check passed all 54 input evaluations on both loading paths, using the report
generator's small numeric IDs/keys. These are completion checks, not repeated
timing estimates.

- [Patch](case-split-growth.patch)
- [Results, witness table and limits](RESULTS.md)
- [Proposed follow-up](FOLLOW-UP.md)
- [Complete reproduction package](tau-203-case-split.zip)
- [Archive checksum](SHA256SUMS)
- [Machine-readable summary](summary.json)

Unzip the package and start with its README.md. It offers a quick executable-only
build and a small comparison, followed by the optional complete test run.
Paths named in RESULTS.md refer to the extracted package. The archive includes
all raw timing attempts and independent-reference runs, every input and output,
test results, the separate Mac build corrections and a SHA-256 file manifest.
No binaries are needed to inspect the evidence.

The replay records medians and every attempt, rejects outputs followed by
a failed exit or input error,
uses explicit step counts, restores test options automatically, and tests both
a known-true formula and its false negation after forced rollback. The budget
is documented as a heuristic, not a memory or linear-time guarantee. Both
compared builds use the same Mac build corrections and dependency package.

Tau: 92b760179ac6412270e54369a2d225dd226fdf18.
Parser: 7d24705ac11863fa48261208134abc68e6c9cc1d.
See the report for the exact compiler, platform, test selection and exclusions.
