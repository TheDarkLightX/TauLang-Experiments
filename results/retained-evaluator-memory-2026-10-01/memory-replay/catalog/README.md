# Lower VM loading memory with whole-record equality

In the VM's 22 branches that leave memory unchanged, replace the repeated
16-field equality with Tau's existing record equality:

```text
o1[t].memory = i3[t].memory
```

Both sides have the same `Words` type. Tau expands this into the same 16
field comparisons, preserving the input and output time indices. The VM
source shrinks from 29,839 to 17,233 bytes after the earlier lookup sharing.
The memory-write branch remains unchanged.

The complete original, lookup-sharing and compact sources are in `vm/spec/`.
`vm-compact-memory.patch` applies to `vm/spec/vm-shared-lookups.tau` and makes
only this source change. `compact_memory.py` generates the compact source
from the pinned original, checks the expected 22 replacements and verifies
that expanding the record comparisons restores the lookup-sharing source
byte for byte. Its initial lookup-sharing step rejects other source hashes.

## Measured results

Fresh measurements on the same Apple M3 Max, using the identical evaluator
executable and five alternating runs per source:

| Measurement | Shared lookups | Shared lookups plus record equality |
| --- | ---: | ---: |
| Median setup | 3.451 s | 1.962 s |
| Median sampled RSS after 55 transitions | 1,074.8 MiB | 554.8 MiB |
| Median of five per-run step medians | 1.002 ms | 0.959 ms |
| 256 distinct inputs, setup plus measured steps | 3.793 s | 2.258 s |

This is **48.4% less sampled memory** and **43.1% less setup time** relative
to the earlier shared-lookup source. The 256-input total is **1.68 times
faster**, including setup. Those totals are one run per source; setup and
RSS are medians of five runs. RSS samples are not lifetime peaks. No competing
Tau builds or benchmark jobs ran during these measurements.

The original retained-source result was about 2,567 MiB in an earlier run.
That historical measurement is preserved in `EVALUATOR-README.md`; it is not
a third arm of this fresh comparison. The ordinary adapter still used less
memory in the earlier comparison, so memory optimization remains useful.

## Correctness evidence

- All **531 output checks per source** match the separate Python model of
  the original VM: five 55-transition runs and another 256 distinct inputs.
- Tau prints **exactly the same 28,546-byte loaded formula** for both sources,
  with SHA-256 `ffcda6fea6ee1f62533eeb653f22be24388609de4ce54c10214ce3491c4941b3`.
  The comparison excludes the echoed input command and prompt.
- Both admit the same 102 inputs, 21 outputs, 22 decisions, 17 leaves,
  60,940 expression occurrences and 455 retained terms.
- The saved-results checker rejects a changed memory output and a missing
  repeat. The source transformation rejects a changed original-source hash.

The relevant existing implementation is
[`adt_flatten_rewrite_equality`](https://github.com/IDNI/tau-lang/blob/15d091723f2b17175bc41f9a9ab6fb5a7760751f/src/adt/adt_flatten.tmpl.h#L648).
Thank you @castrod for the
[record-equality expansion](https://github.com/IDNI/tau-lang/commit/adb27feb5)
already present upstream. Thank you @taumorrow for the related functional-step
work in [#178](https://github.com/IDNI/tau-lang/issues/178) and
[PR #179](https://github.com/IDNI/tau-lang/pull/179); this comparison does not
apply or benchmark that PR.

## Replay

Follow `EVALUATOR-README.md` to build Tau revision
`15d091723f2b17175bc41f9a9ab6fb5a7760751f` with the included
`retained-evaluator.patch`. The included `macos-enum-names.patch` is also
needed for the recorded macOS build. This memory reduction requires no
additional Tau patch or parser patch. The separate SAT recognizer is excluded.

From this directory:

```sh
python3 compact_memory.py --output generated-compact
python3 replay_compact.py tau-source/build/release/tau --output new-compact-results
python3 check_loaded_formula.py tau-source/build/release/tau --output new-formula-check
python3 verify_compact.py
```

The first command writes the compact source. The second runs Tau and checks
all outputs against the original-source Python model. The third compares
Tau's loaded formulas in fresh processes. The fourth checks the bundled saved
measurements without Tau. To check a new five-repeat run:

```sh
python3 verify_compact.py --results new-compact-results/results.json
```

Use fresh output directories. For a separately built executable, calculate its
SHA-256 and pass it using `--expected-binary-sha256 YOUR_EXECUTABLE_SHA256`.
The default requires the recorded executable hash. This explicit override
keeps the output, source and completeness checks enabled.

`recorded/build.json` and `EVALUATOR-README.md` give compiler, dependencies,
configuration and previous regression results. The executable used here has
SHA-256 `6539b872083f3258bad4e72bf8a6214479d7ec5ccf82cc0b895a943ec9c61973`.
Full Tau regression suites were not rerun for this VM-source change; the
executable is unchanged. These comparisons support the exact bundled rewrite,
not arbitrary programs or production readiness.

## Other experiment

Sharing the 50 index-mask expressions through one more definition shortened
the source further, but a one-run screen used 556.7 MiB versus 553.5 MiB for
record equality alone. It offered no useful memory saving and is excluded
from the candidate. This screen does not establish a statistically significant
regression.

Earlier sources, patches and results are retained. See `LOOKUP-README.md`
for lookup sharing and `EVALUATOR-README.md` for the evaluator proposal.
