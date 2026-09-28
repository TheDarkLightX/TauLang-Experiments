# Typed definition arguments: reproduction and correction

This package addresses a false argument-type diagnostic in `sat`, `valid` and
`unsat` on Tau devel `8b5a61ca98a72f0a2cbece9b1338c7295482bbd3`, parser
`5b14b6fde86f16dc52c4c0a953a8a1e53c88f95a`.

The smallest example is:

```tau
g(x:bv[2]) := x:bv[2]. sat g({1}:bv[2]) = {1}:bv[2].
```

The reference prints `T` together with a message saying the call's argument type
cannot match its definition. The corrected executable prints `T` without that
message. The direct API also accepts the correctly typed specification when
`keep_as_written()` is selected.

## Build

Install the dependencies listed in Tau's README, then create two checkouts:

```sh
git clone https://github.com/IDNI/tau-lang.git tau-reference
git -C tau-reference checkout 8b5a61ca98a72f0a2cbece9b1338c7295482bbd3
git -C tau-reference submodule update --init --recursive
git clone https://github.com/IDNI/tau-lang.git tau-corrected
git -C tau-corrected checkout 8b5a61ca98a72f0a2cbece9b1338c7295482bbd3
git -C tau-corrected submodule update --init --recursive
```

Apply `macos-enum-names.patch` to both checkouts. This identifier-only change is
needed on the tested macOS SDK (upstream issue #193); it is kept separate from
the type correction. Apply `typed-arguments.patch` to `tau-corrected` only.
Use `git apply /absolute/path/to/the/patch` from each appropriate checkout.

In each checkout, build with `./dev preset release-tests --target tau` and the
compiler/dependency settings for your system. The recorded build uses macOS
26.6.2 arm64, Clang 22.1.2, cvc5 1.3.1, Boost 1.89.0, Release, and these options:

```text
-DTAU_LTO=OFF
-DTAU_ARTIFACT_PREINST=OFF
-DTAU_DONT_USE_FTXUI=ON
-DTAU_PARSER_DONT_USE_FTXUI=ON
```

On Homebrew, specify its LLVM compiler through `CMAKE_C_COMPILER` and
`CMAKE_CXX_COMPILER`, its ICU library directory through `CMAKE_EXE_LINKER_FLAGS`,
and `CVC5_DIR` when discovery needs help. Effective `TAU_CACHE` was enabled.
No prebuilt executable or private repository is required.

## Quick check

Run this from the package directory, once with `tau-reference` and once with
`tau-corrected`, and compare both stdout and stderr:

```sh
./tau-corrected/build/release/tau --charvar=false --color=false \
  --highlighting=false --benchmarks=false --status=false -S error \
  -e 'g(x:bv[2]) := x:bv[2]. sat g({1}:bv[2]) = {1}:bv[2].'
```

In the corrected checkout, the added direct API test checks typed constants,
variables, compound expressions, casts, nested calls, indexed calls, and genuine
type mismatches in both folded and as-written specifications:

```sh
cmake --build build/release --target test_ref_arg_types --parallel 4
ctest --test-dir build/release -R '^test_ref_arg_types$' --output-on-failure
```

## Extended command checks

From this package directory, with both executable paths adjusted to your layout:

```sh
python3 check_calls.py --tau tau-reference/build/release/tau --output reference.json
python3 check_calls.py --tau tau-corrected/build/release/tau --output corrected.json
python3 verify_records.py
```

The checker starts a fresh process for each input and requires both the expected
answer and a clean diagnostic stream on valid calls. Eight deliberately
incompatible calls must still be rejected. Expected answers follow directly
from the identity definitions and the distinct zero/one values; they do not rely
on agreement with the reference.

The extended list retains eight explicit `sbf` cast cases that neither build
fully decides. Consequently, the full checker still exits with status 1 on the
corrected executable. These are retained limitations, not passing tests. The
saved results distinguish the 128 strict passes from those eight incomplete
cases. The original reference has 38/136 strict passes; 96 valid calls emit the
false argument-type message. The correction removes that message from all 96,
but six of those still encounter the separate cast limitation. There are no new
failed cases among the previously passing calls.

For a build without bit vectors, add `--without-bv`; this retains the `sbf`
checks and the incompatible-algebra controls. `verify_records.py` recomputes
counts and pass/fail classifications from every saved command output.

## Patch scope

The change is in `collect_immediate_ref_arg_types`. A `ref_arg` wrapper is untyped
when construction hooks are disabled, while the immediate `bf` expression has
its inferred type. Read that expression for a non-variable argument. The
existing variable handling and mismatch checks remain in place. Nested calls
must contribute one argument each; their own parameter lists must not inflate
the outer call's argument count.

The small `sbf` cast cases are a recorded limitation of normalization. No claim
is made here that the patch supplies missing cast evaluation, proves general
solver correctness, or improves performance.

## Recorded validation

| Configuration | Command checks | Upstream checks |
|---|---|---|
| Reference, default pack | 38/136 strict passes | See the separately reported #194 test failure |
| Corrected, default pack | 128/136 strict passes | 2,532/2,533 Release entries pass; only the unchanged #194 test fails |
| Corrected, `sbf,tau,bv` | 128/136 strict passes | 22/22 focused entries pass |
| Corrected, `sbf,tau,qint` | 28/36 strict passes | 22/22 focused entries pass |
| Corrected plus min/max grammar changes | 128/136 identity checks; 128/128 min/max checks | No new full-suite run for this combination |

All eight remaining identity cases use an explicit `sbf` cast. The reduced
configuration omits bit-vector inputs, so its total differs. Default test
exclusions were retained. The full inventory, outcomes and durations are in
`recorded/ctest-results.json`; command records retain each input, stdout, stderr,
exit status and measured executable hash.

After that full run, the separate test-only correction for #194 was applied.
The three budget checks and the new API test passed (4/4). This is a targeted
confirmation, not another full-suite pass. Declaring the new API test's `sbf,tau`
requirements changes only registration; reconfiguration and the API test passed
in all three builds. No Linux coverage or performance improvement is claimed.

## Optional check with the min/max grammar corrections

`minmax-grammar.patch` contains only the grammar changes already described in
issue #185. Apply it after the type correction, rebuild `tau`, then run:

```sh
python3 check_definitions.py --tau tau-corrected/build/release/tau --output minmax.json
```

This checks ordinary unsigned min/max directly in Python, plus explicit
fixed-point fallback values. All 128 cases return their expected answer without
diagnostics. It resolves the 56 diagnostic-bearing cases retained in the earlier
#185 follow-up. The combined check does not include unrelated printing changes.
Its source components and executable hash are listed in `build-info.json`.

To verify file integrity on macOS, run `shasum -a 256 -c SHA256SUMS` from this
directory (`sha256sum -c SHA256SUMS` on Linux).
