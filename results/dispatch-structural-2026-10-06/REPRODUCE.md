# Build and replay

Use Python 3.9 or later, a C++23 compiler, CMake and [Tau's dependencies](https://github.com/IDNI/tau-lang/tree/92b760179ac6412270e54369a2d225dd226fdf18). These instructions describe the measured macOS configuration. Other operating systems and algebra selections have not been qualified here.

## Three comparable builds

From this package directory:

```sh
bundle="$(pwd)"
for tree in tau-growth-only tau-one-step tau-combined; do
    git clone https://github.com/IDNI/tau-lang.git "$tree"
    git -C "$tree" checkout --detach 92b760179ac6412270e54369a2d225dd226fdf18
    git -C "$tree" submodule update --init --recursive
    git -C "$tree/external/parser" rev-parse HEAD
done
git -C tau-growth-only apply "$bundle/patches/case-split-growth.patch"
git -C tau-one-step apply "$bundle/patches/case-split-growth.patch"
git -C tau-one-step apply "$bundle/patches/one-step-decision.patch"
git -C tau-combined apply "$bundle/patches/combined-candidate.patch"
```

Each parser should be `7d24705ac11863fa48261208134abc68e6c9cc1d`. The combined patch already contains the growth guard and one-step decision. Do not apply them twice. `structural-runtime.patch` is provided for focused review: applying it after the growth and one-step patches produces the same seven changed runtime files as the combined patch. The combined patch also contains the regression tests and option documentation.

On the measured Mac, the supplied compiler wrappers explicitly select the SDK. Check their compiler and SDK locations against your installation. Apply the same build corrections to all three trees:

```sh
for tree in tau-growth-only tau-one-step tau-combined; do
    git -C "$tree" apply "$bundle/patches/common-macos.patch"
    git -C "$tree/external/parser" apply "$bundle/patches/parser-darwin-build.patch"
done
export PATH="$bundle/tools:$PATH"
export SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk
export TAU_TEST_CXX="$bundle/tools/clang++"
export TAU_STORE_REMOTE=
export TAU_STORE_PUBLISH=OFF
for tree in tau-growth-only tau-one-step tau-combined; do
    (
        cd "$tree"
        ./dev preset release-tests -DTAU_BUILD_JOBS=4 -DTAU_STORE_KEEP=0 \
          -G 'Unix Makefiles' \
          -DCMAKE_C_COMPILER="$bundle/tools/clang" \
          -DCMAKE_CXX_COMPILER="$bundle/tools/clang++" \
          -DTAU_HOST_C_COMPILER="$bundle/tools/clang" \
          -DTAU_HOST_CXX_COMPILER="$bundle/tools/clang++" --target tau
    ) || exit
done
```

Release enables `TAU_CACHE` through a normal CMake variable even when the stored cache entry says `OFF`. Confirm the effective compiler definitions contain `-DTAU_CACHE`. Keep the compiler environment for tests that compile generated C++. The signing correction requires a fresh dependency build; do not change dependency bytes already covered by stored hashes.

## Correctness before performance

Run the public decision checks in fresh processes for each bit width:

```sh
for name in growth-only one-step combined; do
    python3 -B repro/check_single_step_semantics.py \
      --binary "tau-$name/build/release/tau" --route api \
      --out "fresh-decisions-$name" || exit
done
python3 -B repro/check_outputs.py \
  --unmodified tau-growth-only/build/release/tau \
  --patched tau-combined/build/release/tau --out fresh-outputs
python3 -B repro/check_reparse.py --repro repro \
  --growth-only tau-growth-only/build/release/tau \
  --candidate tau-combined/build/release/tau --out fresh-reparse
python3 -B repro/check_wide.py \
  --unmodified tau-growth-only/build/release/tau \
  --patched tau-combined/build/release/tau --out fresh-wide
python3 -B repro/discover_rule_guards.py fresh-rule-search
python3 -B repro/check_finite_semantics.py \
  --binary tau-combined/build/release/tau --out fresh-rule-replay \
  --cases-json fresh-rule-search/bank.json
```

The historical helper option `--unmodified` selects the growth-only reference here. Its `split_off` variant means that reference with case splitting disabled. It does not mean the combined candidate with case splitting disabled.

Build all native targets, then run the native and command-line tests:

```sh
cmake --build tau-combined/build/release --parallel 4
ctest --test-dir tau-combined/build/release -E '^test_repl-' \
  --output-on-failure --output-junit fresh-native.xml -j4
ctest --test-dir tau-combined/build/release -R '^test_repl-' \
  --output-on-failure --timeout 120 -j4
```

The additional direct check calls the helper and native decision functions with independently enumerated expected answers. The compile helper uses the existing Unix Makefiles commands, so build the reference target in each tree first:

```sh
python3 -B repro/generate_native_bank.py fresh-direct-finite-bank.cpp
cmp fresh-direct-finite-bank.cpp repro/direct-finite-bank.cpp
for name in growth-only combined; do
    cmake --build "tau-$name/build/release" \
      --target test_integration-satisfiability6 --parallel 4 || exit
done
python3 -B repro/build-direct-memoryless.py --tree tau-growth-only \
  --source direct-finite-bank.cpp --tag baseline
python3 -B repro/build-direct-memoryless.py --tree tau-combined \
  --source direct-finite-bank.cpp --tag candidate --single-step
repro/direct-baseline
repro/direct-candidate
```

## Isolate the contributions

Stop competing builds and test jobs first. This runner checks every output, alternates variant order, and runs three repetitions of seven bounded examples:

```sh
python3 -B repro/compare_components.py --repro repro \
  --growth-only tau-growth-only/build/release/tau \
  --one-step tau-one-step/build/release/tau \
  --candidate tau-combined/build/release/tau --out fresh-components
```

The 63 attempts each have a 30-second and 1,536-MiB stop condition. Any missing or wrong answer, diagnostic error, nonzero exit or resource stop fails the comparison. Runners refuse to overwrite existing output directories. Preserve failed attempts alongside later corrections.

CPU and memory describe complete processes, including startup, loading and the stated number of steps. They do not isolate warm-step cost. The `structural` result label means the complete candidate; the other labels are defined in the result file. RSS is sampled, so it can miss a brief peak.

To check the supplied records without building Tau:

```sh
unzip evidence.zip
python3 -B repro/verify_followup_records.py .
python3 -B repro/verify_earlier_records.py
```

That command regenerates expected inputs and finite answers, compares retained outputs, recomputes medians, checks completeness and verifies file hashes. It does not rerun Tau or turn finite tests into a proof for all inputs.
