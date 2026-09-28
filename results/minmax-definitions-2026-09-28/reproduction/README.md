# Min/max in definition bodies and fallback values

The two-line grammar correction keeps a bare two-argument `min` or `max`
call as a built-in operation when it is the entire right-hand side of a
definition or an explicit fixed-point fallback value. These positions are
separate from the operand-list correction in
[#185](https://github.com/IDNI/tau-lang/issues/185).

Tau source: `8b5a61ca98a72f0a2cbece9b1338c7295482bbd3`.
Parser source: `5b14b6fde86f16dc52c4c0a953a8a1e53c88f95a`.
Test date: 2026-09-28.

## Changes and scope

- `minmax-definition-followup.patch`: the two grammar exclusions and two
  API tests checking the parsed expression, with 260 assertions. Definition
  heads, other argument counts, offsets, typed references, and longer names
  remain available. Both character-variable modes are covered.
- `minmax-operands.patch`: the earlier operand-list correction and its ten
  registered command tests. It is included unchanged.
- `additional-printer-check.patch`: four typed min/max conjunction round trips,
  including underscores and both operand orders, with 12 assertions. This
  is a separate check of the correction proposed in
  [#190](https://github.com/IDNI/tau-lang/issues/190).
- `printing-documentation-and-build.patch`: the shared conjunction-printing,
  help-text, and macOS enum-name corrections described in
  [#190](https://github.com/IDNI/tau-lang/issues/190),
  [#191](https://github.com/IDNI/tau-lang/issues/191), and
  [#193](https://github.com/IDNI/tau-lang/issues/193).
- `complete-combination.patch`: exactly that complete source combination,
  including the newly added command-test file. Apply either the complete
  patch or the four component patches in the order listed under replay below.

The comparison named `operand-reference` includes the earlier operand-list
correction and all shared changes. Only the two new definition/fallback
exclusions are absent; the same new API tests are present. This isolates the
new grammar change from the earlier operand correction. Its focused checks
pass 10/10, but the new grammar test has 16 failed assertions out of 260.
The corrected build passes all 272 assertions, including the additional
printing check. No separate full-suite run is claimed for `operand-reference`.

## Results and remaining failures

The corrected build passes the ten earlier focused checks and all 2,352
small-width checks of casts and complements (1,176 expected true answers and
1,176 expected false answers). Expected values are computed in Python.
The corpus is finite and does not establish correctness for all widths or
all formulas.

The new definition/fallback checker has 128 checks. **72 pass strictly**:
56 definition `normalize` checks at widths 1–3 and 16 explicit fallback checks
at width 2. The other **56 fail strictly** because `sat` and `valid` print a
definition-call type diagnostic, even with explicitly typed parameters.
They print the mathematically expected Boolean answer, but are not counted
as passes. Parenthesizing the built-in call in the definition reproduces the
same complete stdout and stderr on both the pre-operand reference and the
corrected build. That supports the intended parsing interpretation while
leaving the type diagnostic unresolved.

The configured Release suite passes 2,542/2,543 tests. Its sole failure is
`test_repl-run_cmd-values_stay_within_constant_size_budget`, also observed
before the min/max changes. Earlier reference and corrected builds both
produce values for steps 0–8 and report the constant-size limit before the
expected step 9. Those observations are included as
`prior-constant-budget-comparison.json`. They are explicitly prior results;
the current full-suite failure is recorded separately in `release-tests.json`
and `release-failure.txt`. The suite is not all-passing.

The full-suite result applies to the complete combination described above,
in the default type pack. No no-bit-vector configuration or performance
claim is made. The change alters grammar selection, not bit-vector arithmetic.

## Check the stored evidence

With Python 3.9 or later, from this directory:

```sh
python3 verify_results.py
```

This checks file hashes, regenerates the 2,352 expected cases, recomputes
acceptance from full process outputs, checks all 128 new cases and the 112
parenthesized observations, and checks the per-test Release results. It does
not run Tau or reinterpret diagnostics as passes. Raw output and binary
hashes are retained. Timing text in test logs is incidental, not a benchmark.

## Build and replay

Install the dependencies from the
[pinned upstream build instructions](https://github.com/IDNI/tau-lang/blob/8b5a61ca98a72f0a2cbece9b1338c7295482bbd3/README.md#compiling-the-source-code).
Keep this package as `minmax-definitions-reproduction` beside the source copies:

```sh
git clone https://github.com/IDNI/tau-lang.git tau-corrected
git -C tau-corrected checkout 8b5a61ca98a72f0a2cbece9b1338c7295482bbd3
git -C tau-corrected submodule update --init --recursive
git -C tau-corrected apply ../minmax-definitions-reproduction/complete-combination.patch

git clone https://github.com/IDNI/tau-lang.git tau-operand-reference
git -C tau-operand-reference checkout 8b5a61ca98a72f0a2cbece9b1338c7295482bbd3
git -C tau-operand-reference submodule update --init --recursive
git -C tau-operand-reference apply ../minmax-definitions-reproduction/complete-combination.patch
python3 minmax-definitions-reproduction/prepare_reference.py tau-operand-reference
```

Alternatively, apply the component patches to a clean pinned checkout in
this order: `printing-documentation-and-build.patch`, `minmax-operands.patch`,
`minmax-definition-followup.patch`, `additional-printer-check.patch`.
Their result is checked against the complete patch by source-file hashes.
Do not also apply the complete patch to that checkout.

In each source directory:

```sh
./dev preset release-tests -DTAU_BUILD_JOBS=4 -DTAU_LTO=OFF \
  -DTAU_ARTIFACT_PREINST=OFF -DTAU_DONT_USE_FTXUI=ON \
  -DTAU_PARSER_DONT_USE_FTXUI=ON --target tau test_api-tref_api
./build/release/test_api-tref_api --test-suite='Min/max definition and fallback grammar'
```

The recorded setup uses macOS 26.6.2 arm64, Homebrew Clang 22.1.2, cvc5
1.3.1, Boost 1.89.0, Release `-O3 -DNDEBUG`, caching and parser measurement
on. Set `CMAKE_C_COMPILER`, `CMAKE_CXX_COMPILER`, `CVC5_DIR` and
`CMAKE_EXE_LINKER_FLAGS` to the corresponding installed locations if needed.
The macOS enum-name correction permits this pinned source to compile and is
included identically in both variants.

From the common parent directory:

```sh
python3 minmax-definitions-reproduction/check_definitions.py --tau tau-corrected/build/release/tau --output definitions-corrected-replay.json
python3 minmax-definitions-reproduction/check_definitions.py --tau tau-operand-reference/build/release/tau --output definitions-reference-replay.json
python3 minmax-definitions-reproduction/check.py --tau tau-corrected/build/release/tau --output focused-replay.json
python3 minmax-definitions-reproduction/run_exact.py --tau tau-corrected/build/release/tau --output exact-replay.json
python3 minmax-definitions-reproduction/check_controls.py --tau tau-corrected/build/release/tau --output controls-replay.json
```

Both definition-check commands exit 1 on the recorded source: the corrected
build has 72 strict passes; the operand-only reference has zero. The focused
and exact corrected checks should exit 0. The control command records the 56
parenthesized diagnostic-bearing cases and exits 1; it deliberately does not
call them successful evaluations. Output files are never overwritten. Each
new definition/control call runs in a fresh process with a 12-second timeout.

For the configured suite, from `tau-corrected`:

```sh
python3 ../minmax-definitions-reproduction/enable_printer_test.py
cmake --build build/release --parallel 4
ctest --preset release-tests --parallel 4 --timeout 180 --output-on-failure
```

The extra printer suite is enabled and other default exclusions retained.
`build-info.json` lists the effective configuration. Tests that compile
produced C++ need working child compilers: the recorded run used GCC 15.2.0
for `g++`, Clang 22.1.2 through `TAU_CXX`, and the installed ICU directory in
`LDFLAGS`. The known budget-test failure remains a failure.
