# Zero-argument definitions and qlt point-constant checks

This package records 14 small CLI checks on Tau
`8c1f5ecd0e1391e8264d9d006a74e0586592f47f` and parser
`5b14b6fde86f16dc52c4c0a953a8a1e53c88f95a`.

The reference build has only the macOS enum-name correction from
[Tau #193](https://github.com/IDNI/tau-lang/issues/193). The exact patch is
included. Five results disagree with the expected answers; nine controls
agree. Every command completed with exit code zero. This is a report of
language-correctness examples, not qualification of a proposed logic fix.

## Replay

Python 3 is sufficient to inspect the saved records:

```sh
python3 verify_saved.py
```

To run the 14 inputs against a Tau binary:

```sh
python3 replay.py /path/to/tau --output replay-results.json
```

Each input runs in a fresh process with `--charvar false -c false -S error`
and a 15-second timeout. The output file must not already exist. The script
returns 1 when answers differ from the expected results, as they do in the
recorded build; it returns 0 only when all 14 expected answers are produced
without an error diagnostic. An error or missing verdict is also a failure.

`cases.json` contains all inputs and expected answers. `observations.json`
contains the complete captured stdout and stderr, with ANSI color escapes
removed. Timing diagnostics are retained but are not performance evidence.

## Why these answers are expected

For the definition checks, `k() := {7}:bv[8]` names the constant 7. Its equality
to 7 is satisfiable, and its inequality to 7 is not valid. The observed answers
are F and T, respectively, after an unresolved-call diagnostic. A definition
with one unused argument and the literal constant itself both give T and F.
The additional assignment case has the witness `x = 7`; the arithmetic
control evaluates `6 + 1` at width 8.

The qlt documentation describes variables as rational points. The grammar
represents a constant such as `{3}:qlt` as the singleton interval `[3,3]`.
Writing `p` for that singleton gives an exhaustive explanation:

| Value of y | p intersect y | p intersect the complement of y | Both nonempty? |
| --- | --- | --- | --- |
| y = 3 | p | empty | No |
| y differs from 3 | empty | p | No |

Thus no y satisfies both nonempty-intersection conditions, and for every y
at least one intersection is empty. The recorded quantified answers reverse
both conclusions. The ground cases y = 3 and y = 5 return F as expected.
Replacing p by `[0,1]` gives a positive control: y = 0 leaves the point 0 in
one intersection and `(0,1]` in the other.

## Build

Recorded environment: macOS 26.6.2 arm64, Homebrew Clang 22.1.2,
Boost 1.89.0 and cvc5 1.3.1. Install Tau's documented dependencies and use the
recorded compiler version. Fetch the source and its parser:

```sh
git clone https://github.com/IDNI/tau-lang.git
git -C tau-lang checkout 8c1f5ecd0e1391e8264d9d006a74e0586592f47f
git -C tau-lang submodule update --init --recursive
```

On macOS, apply `macos-enum-names.patch` from this package with
`git -C tau-lang apply /path/to/macos-enum-names.patch`. It renames only the
two enum members and their uses; it does not change definition resolution or
qlt rules. Configure the source with the following settings:

```sh
cmake --fresh -S tau-lang -B tau-lang/build/release -G 'Unix Makefiles' \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang \
  -DCMAKE_CXX_COMPILER=clang++ -DTAU_BUILD_EXECUTABLE=ON \
  -DTAU_BUILD_TESTS=OFF -DTAU_DONT_USE_FTXUI=ON \
  -DTAU_ARTIFACT_PREINST=OFF -DTAU_LTO=OFF \
  -DTAU_BAS=sbf,tau,qint,qlt,bv
cmake --build tau-lang/build/release --target tau -j2
```

Put the recorded Clang tools on PATH or supply their absolute paths to CMake.
Supply `CVC5_DIR` if the installed cvc5 CMake package is not found. The recorded
Homebrew build also used `-DCMAKE_EXE_LINKER_FLAGS=-L/opt/homebrew/opt/icu4c/lib`.
Configure and compiler records confirm `TAU_CACHE` and parser measurements
are enabled. Local source and dependency prefixes in the saved build logs
are replaced with placeholders. `build-info.json` identifies the binary and
source change, and `MANIFEST.sha256` covers the package files.
