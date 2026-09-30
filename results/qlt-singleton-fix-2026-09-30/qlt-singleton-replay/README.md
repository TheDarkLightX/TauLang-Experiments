# Exact singleton cases for qlt quantifiers

This patch addresses [Tau Lang #197](https://github.com/IDNI/tau-lang/issues/197).
It targets Tau commit `577b635af244d8a1b6e71ef7b2b92ed756187c7e`, with parser
`5b14b6fde86f16dc52c4c0a953a8a1e53c88f95a`.

The reported condition asks whether a singleton can have a nonempty intersection
with both a value and its complement. That is impossible. The generic rules
for sets that can always be divided cannot be used for a singleton.

The patch adds a qlt implementation of the existing `case_split_quantifiers`
capability. When every use of a bound variable is restricted to membership in
the same exact singleton, it checks the two possible cases directly. It uses
actual rational points for both cases; it does not treat an interval as a point.

For the singleton `C = {3}`:

| Observed case | Representative | `C & x` | `C & x'` | Both nonempty? |
| --- | --- | --- | --- | --- |
| Contains 3 | `x = {3}` | `{3}` | empty | No |
| Does not contain 3 | `x = {0}` | empty | `{3}` | No |

These cases are exhaustive even if values are interpreted as sets. A formula
that observes `x` only through this singleton cannot distinguish two values
that agree on whether they contain 3. Existential quantification is therefore
the OR of the two substituted formulas; universal quantification is their AND.
When the singleton is `{0}`, the outside representative is `{1}`.

The source check follows shared subtrees without revisiting the same node and
restriction. The point-factor lookup is cached and uses an explicit stack. Only
intersection, union, XOR and complement propagate the
restriction. It declines an uncovered variable use, multiple different point
restrictions, non-point intervals, named endpoints, approximate constants and
a nested binding that would be captured by substitution. These checks use
the constant representation and approximation flag retained by the existing
qlt tree; this patch does not change approximation metadata. Other qlt routes
continue to handle those formulas. This is a focused correction, not a complete
solver for every combination of qlt order and set expressions.

The interval-output controls record compatibility with this revision; they
do not decide whether qlt variables should generally represent whole intervals.

The change is confined to qlt's descriptor, its quantifier code, its tests and
the capability documentation. Existing comparison hooks and generic
quantifier algorithms are unchanged.

## Reproduce

Place this directory beside a clean Tau checkout under the name `qlt-singleton-replay`.
Install Tau's documented build dependencies, then run:

```sh
git clone https://github.com/IDNI/tau-lang.git
git -C tau-lang checkout 577b635af244d8a1b6e71ef7b2b92ed756187c7e
git -C tau-lang submodule update --init --recursive
cd tau-lang
git apply --check ../qlt-singleton-replay/fix-qlt-singleton-quantifiers.patch
git apply ../qlt-singleton-replay/fix-qlt-singleton-quantifiers.patch
./dev preset release-tests -DTAU_BUILD_EXECUTABLE=ON -DTAU_LTO=OFF -DTAU_ARTIFACT_PREINST=ON -DTAU_DONT_USE_FTXUI=ON
ctest --preset release-tests --output-on-failure
python3 ../qlt-singleton-replay/check_reported.py build/release/tau replay-reported
python3 ../qlt-singleton-replay/singleton_model_check.py build/release/tau replay-model
python3 ../qlt-singleton-replay/check_compatibility.py build/release/tau replay-compatibility.json
```

The six report commands must give `F, T, F, F, T, T`. The model checker evaluates
128 formulas independently using Boolean membership in one point, including
both quantifier orders and both existential and universal binders. All three
checkers save outputs and JSON results, and fail on a mismatch.

On macOS, the pinned upstream revision also needs the separate
`macos-build-compatibility.patch` before building. It addresses the enum-name
collision in [#193](https://github.com/IDNI/tau-lang/issues/193) and qualifies the
same macOS name collision in an upstream test. These build corrections are
separate from the qlt patch. Compiler and dependency paths may require the
usual local CMake options.

To run just the qlt solver and added regression tests:

```sh
ctest --preset release-tests -R '^test_integration-solver-qlt$' --output-on-failure
```

## Validation

The focused Release suite passes **57 cases and 7,236 assertions**, including
6,000 comparisons against independent point-membership calculations. All six
reported checks pass. The independent quantified model passes **128/128** with
the patch, compared with **126/128** on stock. The two reported decision checks,
four zero-point boundary checks and four temporal controls also pass; stock
fails the two reported decision checks.

The full default Release run passes **2,622 of 2,626 configured CTest entries**.
The four failures were replayed on a stock build with the same configuration;
all four fail there too. Three checks expect a particular printed operand order,
and the fourth marks a passing test as an unexpected success. The exact names
and comparison are in `evidence/stock-failure-comparison.json`. This comparison
reran those four stock tests, not the whole stock suite.

The reduced `sbf,tau,bv` and `sbf,tau,qint` configurations pass four and three
focused CTest entries respectively. Only the default configuration received a
full run. Upstream's default test exclusions and conditional skips were retained.
No performance gain is claimed.

The patch applies cleanly to the tested base and reproduces its modified source
files exactly. It also applies cleanly to `b5445d315071d2eb6d0c20728feab3f09d94fe57`,
which landed during validation and leaves the four patched files unchanged.
Runtime testing in this package is on `577b635af244d8a1b6e71ef7b2b92ed756187c7e`;
the newer commit received an application check only.

`validation.json` records the build, executable hash, results and limits.
`MANIFEST.sha256` lists the packaged file checksums.

Thank you @castrod for the earlier [pinned-point correction for #148](https://github.com/IDNI/tau-lang/commit/e47e43c0dfb63a2ee936a2d623f72e60780fe2c4),
which is already present in the tested source. The new pass handles singleton
intersections before generic quantifier elimination; it preserves that existing
ordering and pinned-point work.

The recorded macOS run used Homebrew Clang 22.1.2, cvc5 1.3.1 and Boost 1.89.0.
Tests that compile generated C++ used Homebrew `g++-15`; the system `g++` on
this machine could not find its standard headers. The test process also had
ICU's library directory in `LDFLAGS`. With those dependencies installed, an
example test environment is:

```sh
mkdir -p test-toolchain
ln -s "$(command -v g++-15)" test-toolchain/g++
PATH="$PWD/test-toolchain:$PATH" LDFLAGS="-L$(brew --prefix icu4c)/lib" \
  ctest --preset release-tests --output-on-failure
```

These are host build requirements, not changes to qlt's logic.

The complete recorded macOS configuration was (apply the separate build patch
once, before configuring):

```sh
git apply ../qlt-singleton-replay/macos-build-compatibility.patch
./dev preset release-tests --keep-cache \
  -DTAU_BUILD_EXECUTABLE=ON -DTAU_BAS=tau,qint,qlt,nlang,bv,sbf,hsb \
  -DCMAKE_C_COMPILER=/opt/homebrew/opt/llvm/bin/clang \
  -DCMAKE_CXX_COMPILER=/opt/homebrew/opt/llvm/bin/clang++ \
  -DCMAKE_EXE_LINKER_FLAGS=-L/opt/homebrew/opt/icu4c/lib \
  -DCVC5_DIR="$HOME/.tau/cvc5/dist/lib/cmake/cvc5" \
  -DTAU_LTO=OFF -DTAU_ARTIFACT_PREINST=ON -DTAU_DONT_USE_FTXUI=ON
```
