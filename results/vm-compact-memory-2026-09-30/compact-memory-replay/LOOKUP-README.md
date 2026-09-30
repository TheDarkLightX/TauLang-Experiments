# Reduce VM loading cost by sharing repeated lookups

This extends the [retained-evaluator proposal in Tau #199](https://github.com/IDNI/tau-lang/issues/199) with a change to the VM's Tau source. It uses the same evaluator patch and measured executable. Three ordinary Tau definitions replace repeated lookup text before loading. The original VM source and all historical measurements remain in this package.

## What changes

The original 77,942-byte VM repeatedly spells out the same long lookup calls. The alternative is 29,839 bytes:

| Shared expression | Repeated uses |
| --- | ---: |
| 32-way opcode lookup at the current program counter | 20 |
| 32-way operand lookup at the current program counter | 45 |
| 16-way memory lookup at the selected operand | 7 |

For example, the repeated opcode lookup becomes `vmsharedlookup0({0}:bv[32])`, with its unchanged expression defined once. The helper takes an unused argument; the lookup still reads the original current inputs. The helpers are acyclic and change no operators, constants, branch conditions or output assignments. Expanding them in reverse order restores the original main formula byte for byte.

`share_lookups.py` accepts only the exact bundled VM source hash. It is a bounded source transformation for this example, not a general Tau optimizer. The replay's Python model always reads the original VM source. Tau receives the alternative source, expands its ordinary definitions, and performs every branch choice and output computation. Python does not calculate the Tau outputs.

## Reproduce

Follow [EVALUATOR-README.md](EVALUATOR-README.md) to build the pinned Tau revision with `retained-evaluator.patch`. macOS additionally needs the included `macos-enum-names.patch`. No new Tau patch, parser patch or SAT recognizer is added here.

Generate and check the alternative source:

```sh
python3 share_lookups.py --output generated-source
```

The supplied copy is [vm/spec/vm-shared-lookups.tau](vm/spec/vm-shared-lookups.tau). Both specifications retain the license in [vm/LICENSE](vm/LICENSE).

Run the comparison with no compilation or other heavy work alongside it:

```sh
python3 replay_shared.py tau-source/build/release/tau --output new-shared-results
```

The output directory must be new. The driver performs five alternating repeats of the same 55-transition workload for each retained variant, then one 256-input run for each retained variant and the ordinary adapter. Every output is checked against the original-source Python model. Setup includes source transformation, model parsing, process startup, source loading and admission. Step intervals include Python, pipe communication and decoding; model checking is outside those intervals.

Check all saved outputs and timing arithmetic without running Tau:

```sh
python3 verify_shared.py
```

That also checks the original package's recorded tests and replay. Complete output tuples and unrounded timings are in [recorded/shared-lookup-results.json](recorded/shared-lookup-results.json).

## Measurements and limits

The comparison uses the same Apple M3 Max and environment as the original package. The executable SHA-256 is `6539b872083f3258bad4e72bf8a6214479d7ec5ccf82cc0b895a943ec9c61973`. There was no compilation or competing experiment during timing.

| Measurement | Original source, retained evaluator | Shared lookups, retained evaluator |
| --- | ---: | ---: |
| Median setup | 8.045 s | 3.324 s |
| Median loading | 7.576 s | 2.866 s |
| Median admission | 0.234 s | 0.222 s |
| Median of five per-run step medians | 0.970 ms | 0.939 ms |
| 256 distinct inputs, setup plus measured steps | 8.718 s | 3.692 s |
| Median sampled RSS after 55 transitions | 2,566.1 MiB | 1,073.8 MiB |

Setup is **58.7% lower** and sampled RSS **58.2% lower**. The 256-input run including setup is **2.36× faster** than the original retained path. The fresh ordinary-adapter run took 65.214 s including setup, giving **17.67×** for the shared-lookup retained path on that workload. Step times remain around 0.94 ms; this experiment is aimed at loading cost.

Setup and RSS use five runs per retained variant. The setup-inclusive 256-input comparison uses one run per path, so it is not a median of repeated whole runs. The old table in #199 remains the observation for the original source in its earlier run.

Both retained variants admit 102 inputs, 21 outputs, 22 decisions, 17 leaves, 60,940 expression occurrences and 455 retained top-level terms. Each has 531 checked transitions: five repeats of 55 plus 256 additional inputs. The ordinary reference has a fresh 256-input comparison here. The additional vectors are separate inputs rather than one feedback trace; 56 have expected VM fault outputs. The original package describes the three-step arithmetic program, 17-step synthetic payroll program and 35 conformance inputs.

The earlier full regression results still describe this unchanged executable: 2,395 of 2,398 configured entries pass in each switch mode, and the three printing failures also occur in stock with the same macOS correction. Those suites were not rerun for this source rewrite. This evidence does not prove equivalence for arbitrary programs or qualify integration into Tau's normal temporal interpreter.

The source change reduces parsing work; it does not establish a faster repeated-step algorithm. Sampled resident memory is not lifetime peak memory and remains substantially above the ordinary adapter. Parsing and loading still deserve further work. A three-second diagnostic sample of the original load stayed inside the parser, consistent with the large loading share; that sampled run was separate from the timing comparison.

Thank you @taumorrow for the functional-step work in [Tau #178](https://github.com/IDNI/tau-lang/issues/178) and [PR #179](https://github.com/IDNI/tau-lang/pull/179). Neither that PR nor the related [parser prediction memoization PR #21](https://github.com/IDNI/parser/pull/21) was applied or benchmarked in this comparison.
