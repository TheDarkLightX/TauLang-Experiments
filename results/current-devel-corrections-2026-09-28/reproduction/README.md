# Printing and help checks on current devel

This package records checks on Tau
`8b5a61ca98a72f0a2cbece9b1338c7295482bbd3`, with parser
`5b14b6fde86f16dc52c4c0a953a8a1e53c88f95a`.

The reference build has one macOS compilation adjustment: rename the local
`TRUE` and `FALSE` enum constants in `for_each_static_path`. Those names
otherwise expand to macros from the macOS SDK. The unmodified build failed
before producing a binary; `unmodified-build-error.txt` preserves the relevant
diagnostic. The adjustment changes identifiers only.

The corrected build has the same adjustment, the conjunction-printing
correction, its API regression, and a help/comment correction. No other
evaluation changes are included. The printing correction preserves `&`
between operands when `charvar=false`. The documentation correction says a
search limit gives no verdict, instead of describing it as unsatisfiable.

## Check the stored evidence

From this extracted directory, with Python 3.9 or later:

```sh
python3 verify_results.py
```

The verifier checks package hashes and reconstructs all nine printing cases
and all 48 Boolean assignments per build from their complete process outputs.
Python computes expected truth values independently. It also checks the four
controls, unchanged default-mode spelling, before/after help, and the
per-test Release results. This command does not build or run Tau.

The reference passes four of nine printing examples; the corrected build
passes all nine. Both pass the four true/false controls. The examples include
underscores, numerical suffixes, complement, nested expressions, three
operands, and output from quantifier elimination. These finite checks do not
prove every possible printing case correct.

## Build and replay

Install the dependencies from the
[pinned upstream build instructions](https://github.com/IDNI/tau-lang/blob/8b5a61ca98a72f0a2cbece9b1338c7295482bbd3/README.md#compiling-the-source-code).
Keep this package as `current-devel-reproduction` alongside two source copies:

```sh
git clone https://github.com/IDNI/tau-lang.git tau-reference
git -C tau-reference checkout 8b5a61ca98a72f0a2cbece9b1338c7295482bbd3
git -C tau-reference submodule update --init --recursive
git clone https://github.com/IDNI/tau-lang.git tau-corrected
git -C tau-corrected checkout 8b5a61ca98a72f0a2cbece9b1338c7295482bbd3
git -C tau-corrected submodule update --init --recursive
git -C tau-reference apply ../current-devel-reproduction/macos-enum-portability.patch
git -C tau-corrected apply ../current-devel-reproduction/combined.patch
```

`combined.patch` contains exactly the three separate patches plus the printer
API test. Apply either the combined patch or the three separate patches, not
both. The enum rename is harmless on other platforms but has only been
built on the recorded macOS configuration here.

In each source directory, use the same compiler and dependencies:

```sh
./dev preset release-tests -DTAU_BUILD_JOBS=4 -DTAU_LTO=OFF \
  -DTAU_ARTIFACT_PREINST=OFF -DTAU_DONT_USE_FTXUI=ON \
  -DTAU_PARSER_DONT_USE_FTXUI=ON --target tau
```

The recorded setup uses macOS 26.6.2 arm64, Homebrew Clang 22.1.2, cvc5
1.3.1 and Boost 1.89.0. It supplies `CMAKE_C_COMPILER`, `CMAKE_CXX_COMPILER`,
`CVC5_DIR` and an ICU library search directory through
`CMAKE_EXE_LINKER_FLAGS`. Set those to the corresponding installed locations
on your machine when CMake does not find them automatically. It uses the
default type pack, Release `-O3 -DNDEBUG`, effective caching enabled, parser
measurement enabled, and disabled LTO and artifact preinstantiation.

From the common parent directory:

```sh
python3 current-devel-reproduction/check.py --tau tau-reference/build/release/tau --output reference-replay.json
python3 current-devel-reproduction/check.py --tau tau-corrected/build/release/tau --output corrected-replay.json
```

The reference should exit 1; the corrected run should exit 0. Each Tau call
uses a fresh process with a 12-second timeout. Diagnostics, extra output,
missing answers, nonzero exits and timeouts fail the check. Existing result
files are not overwritten.

To reproduce the configured test suite, from `tau-corrected`:

```sh
python3 ../current-devel-reproduction/enable_printer_test.py
cmake --build build/release --parallel 4
./build/release/test_api-tref_api --test-case=set_charvar
ctest --preset release-tests --parallel 4 --timeout 180 --output-on-failure
```

The extra printer test is enabled while the other preset exclusions are
preserved. `build-info.json` lists those exclusions and `release-tests.json`
lists every registered test's result. Some optional checks also depend on
environment variables. Tests that compile generated C++ require working
child compilers: the recorded run selected GCC 15.2.0 for `g++`, Clang 22.1.2
through `TAU_CXX`, and the installed ICU directory through `LDFLAGS`.

The configured Release run passes 2,532 of 2,533 tests. The remaining test,
`test_repl-run_cmd-values_stay_within_constant_size_budget`, expects an output
at step 9. Both the reference and corrected binaries print the same nine
values at steps 0–8, then report that the constant-size limit was reached.
`constant-budget-comparison.json` retains both complete observations. This
failure is present without the printing and documentation corrections; it
remains unresolved. The verification script checks that this is the only
failed registered test. The earlier 2,369-test all-passing result applies to
the earlier pinned revision, not to this newer run.

The full-suite result applies to the combined printing, documentation and
identifier-rename build described above. It is not a new validation of any
BDD or arithmetic-elimination proposal. No performance claim is made.

## File input observations

`input-stream-observations.json` and the `input-stream` directory preserve
two short examples checked with the reference binary. Run each command file
in a fresh Tau process from that directory. The output for `o1` is
`0,a,b,a'` when `o2` refers to its own previous value, and `0,b,a',b'` when
`o2` refers to the previous input. Full stdout and stderr are retained. Both
match the earlier recorded observations. This is evidence for a question
about the intended mapping of file lines to time steps, not proof that the
current request-driven behavior is incorrect.
