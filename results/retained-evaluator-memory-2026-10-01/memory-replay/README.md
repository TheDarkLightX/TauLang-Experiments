# Release parser working memory after retained VM admission

This package tests an extension of the retained evaluator proposed in
[Tau #199](https://github.com/IDNI/tau-lang/issues/199). A direct `evalspec`
request does not invoke the parser again. The parser can therefore keep the
large temporary tables left by loading the VM, even though later evaluations
do not use those tables.

The parser addition provides an explicit idle cleanup operation. The standalone
Tau executable calls it after successful admission, after the local specification
has been destroyed, when the interpreter has no running or pending work. The
operation preserves the grammar, declared type names, owned parse results and
logical roots. It refuses calls during parsing. It discards inspection of the
last parse's temporary tables and must not run concurrently with parsing.

A separate optional call to `malloc_trim(0)` asks glibc to return freed pages to
the operating system. It does nothing on macOS. The patch does not collect the
global tree store.

## Fresh results and qualification

Test date: 2026-10-01. Five alternating fresh processes per configuration, with
diagnostic counters disabled. The Linux arm64 medians are:

| Median measurement | Memory options off | Parser cleanup + trim | All six options |
| --- | ---: | ---: | ---: |
| RSS after 311 evaluations | 493.96 MiB | 166.24 MiB | 163.25 MiB |
| Setup | 1.697 s | 1.744 s | 1.767 s |
| Per-evaluation time | 1.442 ms | 1.442 ms | 1.355 ms |
| Setup + 311 evaluations | 2.207 s | 2.240 s | 2.216 s |

Parser cleanup plus trim cuts sampled RSS by **66.3%**; all six options cut it by **67.0%**. The smaller change captures **99.1% of the measured saving**. Setup increased by 2.8% and 4.1%, respectively; setup plus 311 evaluations increased by 1.5% and 0.4%. Times are descriptive medians on a shared host, with other activity present. No build or regression suite ran during measurement.

This is a reduction after loading and evaluation, not a peak-memory result: median RSS immediately after loading remained about **476 MiB**. On macOS, the corresponding medians were **525.91, 509.67 and 510.47 MiB**; glibc trimming is unavailable there. The Linux percentage should not be applied to the earlier Mac table.

The corresponding macOS medians are:

| Median measurement | Memory options off | Parser cleanup + trim | All six options |
| --- | ---: | ---: | ---: |
| RSS after 311 evaluations | 525.91 MiB | 509.67 MiB | 510.47 MiB |
| Setup | 2.013 s | 2.067 s | 2.070 s |
| Per-evaluation time | 1.120 ms | 1.141 ms | 1.063 ms |
| Setup + 311 evaluations | 2.383 s | 2.436 s | 2.419 s |

The full default-pack macOS Release suite completed in ordinary mode, retained
evaluation mode, and retained evaluation with all six memory options enabled.
Each run passed 2,639 of 2,642 configured tests. The other three require a
particular printed order; a separate stock build prints exactly the same
formulas. See `recorded/failure-comparison.json`. Stock was checked for those
three tests only, not rerun through the entire suite. Upstream's default 19
excluded C++ suites and 12 internally skipped cases remain.

Both reduced configurations passed their focused checks with memory options off
and on: 18/18 for `sbf,tau,bv`, and 7/7 for `sbf,tau,qint`. Linux passed 18/18
focused checks in each setting. The complete Linux suite was not run. The
parser/evaluator API suite passed 13 cases and 19,300 assertions in every build
where it is included. All 64 memory-option combinations passed four arithmetic
witnesses on each platform.

Each platform passed 5,598 VM output comparisons: 4,665 from the repeated
measurements and 933 from the separate counter run. These include repeated
inputs, not 5,598 distinct cases. The saved-data checker independently evaluates
the original-source Python model and rejects changed outputs, missing runs and
changed timing totals. All patches match the compiled source; complete and
incremental installation routes produce the same source tree.

In the Linux counter run, the selected configuration retained 33 Tau constants
and zero outer normalization-cache entries throughout 311 evaluations, with no
heap allocation for its temporary output buffer. With options off, the final
counts were 4,338 constants, 4,768 cache entries and 311 temporary-output heap
allocations. These counters cover those stores, not every allocation inside Tau
or cvc5. Parser cleanup and trim each ran once when enabled.

## Contents and pinned source

- Tau: `a739b90259729590dee7b424df05ba65bfdeacf2`.
- Parser: `5b14b6fde86f16dc52c4c0a953a8a1e53c88f95a`.
- `memory-evaluator.patch`: complete retained evaluator plus memory extension,
  applied to the pinned upstream Tau revision.
- `memory-addon.patch`: only the memory extension, applied after the earlier
  evaluator. `base-evaluator-rebased.patch` supplies that earlier evaluator for
  this revision. Applying the complete patch and applying these two patches
  are alternative routes to the same source.
- `parser-scratch.patch`: the required parser-library addition.
- `macos-build.patch`: two separate macOS compilation corrections, including
  the enum-name correction discussed in [#193](https://github.com/IDNI/tau-lang/issues/193).
- `replay_memory.py`: fresh processes, original-source Python model, and saved
  full output records. `verify_memory.py` independently recalculates saved
  outputs and timing summaries without executing Tau.
- `catalog/`: the unchanged earlier compact-VM reproduction package, including
  original and transformed VM specifications, the model, inputs, adapters,
  license and historical evidence. Its READMEs and executable hashes describe
  the earlier experiment. **Use this top-level README for the new build.**

## Options

All options remain disabled by default. Enable the retained evaluator itself
with `TAU_CONCRETE_EVAL=1`.

| Environment variable, enabled by `1` | Purpose |
| --- | --- |
| `TAU_EVAL_RELEASE_PARSE_SCRATCH` | Release unused parser tables after standalone admission. |
| `TAU_EVAL_TRIM` | Ask glibc to return free allocator pages after admission. |
| `TAU_EVAL_DECIMAL_ONLY` | Return decimal values to `evalspec` without also allocating unused Tau output constants. The C++ API still returns constants by default. |
| `TAU_EVAL_TRANSIENT_NORMALIZE` | Simplify each concrete value without adding it to the outer normalization cache. |
| `TAU_EVAL_ARENA_OUTPUTS` | Store temporary output slots in a small local buffer, with heap fallback if required. |
| `TAU_EVAL_FLAT_LEAVES` | Store output expressions in one contiguous array. |
| `TAU_MEMORY_TELEMETRY` | Print storage counters; disabled for timing confirmation. |

The replay compares one executable in three configurations: all six memory
options disabled; parser cleanup and trim enabled; and all six enabled. The
reference is the retained evaluator with memory options disabled, not stock Tau.

## Build and test

Install Tau's documented C++23 build dependencies, cvc5, Boost and Spot. Confirm
that `ltlsynt --version` works. The recorded macOS build uses Clang 22.1.2,
cvc5 1.3.1, Boost 1.89.0, Spot 2.15.1, Release optimization, LTO off and the
full default algebra pack. Release enables Tau's cache in the build logic even
when the initial CMake cache entry says `OFF`.

On a system where CMake already locates those dependencies:

```sh
./build.sh -DTAU_BUILD_JOBS=8
./test-modes.sh
```

For the recorded Homebrew layout, the additional configuration arguments are:

```sh
./build.sh -DTAU_BUILD_JOBS=12 \
  -DCMAKE_C_COMPILER="$(brew --prefix llvm)/bin/clang" \
  -DCMAKE_CXX_COMPILER="$(brew --prefix llvm)/bin/clang++" \
  -DCMAKE_OSX_SYSROOT="$(xcrun --show-sdk-path)" \
  -DCVC5_DIR="$HOME/.tau/cvc5/dist/lib/cmake/cvc5" \
  -DCMAKE_EXE_LINKER_FLAGS="-L$(brew --prefix icu4c)/lib"
```

Generated-code tests need a working `g++` command and the ICU library search
path. The recorded run uses GNU g++ 15 for those generated programs and
`LDFLAGS=-L/opt/homebrew/opt/icu4c/lib`. These are test-environment settings,
not additional Tau source changes. Keep upstream's default test exclusions
when comparing these results.

## Focused Linux build

The allocator-specific checks use Linux arm64, GCC 14.2.0, Boost 1.83.0,
cvc5 1.3.1, glibc 2.41, the `sbf,tau,bv` pack and the legacy terminal interface.
The Linux check set covers the evaluator, algebra interface and direct REPL
commands. It is separate from the full default-pack macOS suites.

With GCC, CMake, Git, Python, curl, unzip, Boost log and ICU development packages
installed, obtain the pinned upstream cvc5 distribution:

```sh
curl -fL https://github.com/cvc5/cvc5/releases/download/cvc5-1.3.1/cvc5-Linux-arm64-shared.zip -o cvc5.zip
printf '%s  %s\n' 3f53790fcc4e9596c5e340c6f58cdf38a6fc481a179d5e1f9c724d06fba25360 cvc5.zip | sha256sum -c -
unzip -q cvc5.zip
export LD_LIBRARY_PATH="$PWD/cvc5-Linux-arm64-shared/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
./build.sh --target tau -DTAU_BUILD_JOBS=4 \
  -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ \
  -DTAU_BAS=sbf,tau,bv -DTAU_ARTIFACT_PREINST=OFF -DTAU_DONT_USE_FTXUI=ON \
  -DCVC5_DIR="$PWD/cvc5-Linux-arm64-shared/lib/cmake/cvc5"
cmake --build tau-source/build/release -j 4 --target \
  test_api-concrete_eval test_ba_descriptor_pack test_ba_conformance
ctest --test-dir tau-source/build/release --output-on-failure \
  -R '^(test_api-concrete_eval|test_ba_descriptor_pack|test_ba_conformance|test_repl-evalspec-.*)$'
```

This shorter build does not create every test executable. Use the focused
`ctest` selection above, not `test-modes.sh`, with that build. The replay below
explicitly controls the memory options for each process.

## Replay the VM

From this directory, after the build and tests finish:

```sh
python3 -B replay_memory.py tau-source/build/release/tau \
  --catalog catalog --output new-counters --repeats 1 --telemetry
python3 -B replay_memory.py tau-source/build/release/tau \
  --catalog catalog --output new-measurements --repeats 5
python3 -B verify_memory.py new-measurements/results.json \
  --catalog catalog --negative-checks
```

Output directories must be new. The replay uses five alternating process orders
and checks every output against the Python model of the original VM. Every
process performs three smoke transitions, 17 payroll transitions, 35 conformance
inputs and 256 distinct saved inputs: 311 comparisons. Five processes per
configuration make 4,665 comparisons. The separate one-repeat counter run adds
933 comparisons.

Setup includes loading and admission. Per-evaluation time includes the adapter,
pipe exchange and decoding; model evaluation occurs outside the timer. Total
is setup plus the sum of the 311 measured evaluations, excluding model checks
and memory observations. Sampled RSS after the workload is not lifetime peak
memory. Run measurements without competing work where possible.

## Option-combination witnesses

`check_options.py` starts a fresh process for each of the 64 combinations of
six memory switches. For an eight-bit input below 128, the first output is the
input plus one and the second is the first output plus seven. Otherwise the
outputs subtract one and seven respectively. Arithmetic is modulo 256.

| Input | Expected first output | Expected second output |
| ---: | ---: | ---: |
| 0 | 1 | 8 |
| 127 | 128 | 135 |
| 128 | 127 | 120 |
| 255 | 254 | 247 |

The check also verifies that repeated admission returns the same interface,
that cleanup occurs exactly once when enabled, and that the trim counter
matches platform support. These are finite witnesses, not exhaustive coverage
of all Tau inputs.

```sh
python3 -B check_options.py tau-source/build/release/tau --output new-options
```

## VM source and related work

The compact source uses shared lookup definitions and Tau's existing whole-record
equality. These source transformations are documented with their original
measurements in `catalog/README.md` and `catalog/LOOKUP-README.md`; they are
identical in all three configurations of this experiment.

Thank you @castrod for the existing record-equality expansion in
[adb27feb5](https://github.com/IDNI/tau-lang/commit/adb27feb5). Thank you
@taumorrow for the related functional-step work in
[#178](https://github.com/IDNI/tau-lang/issues/178) and
[PR #179](https://github.com/IDNI/tau-lang/pull/179). That PR was not applied or
benchmarked here. Connecting retained expressions to the interpreter remains
separate work.

This is an opt-in prototype. Finite output comparisons and regression tests do
not prove equivalence for arbitrary Tau programs. The full macOS suites and focused Linux tests have different coverage;
keep their results separate. Each memory measurement applies to its recorded
executable and platform.
