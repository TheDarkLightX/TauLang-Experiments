# Greatest witnesses for closed bit-vector mask implications

This is an original reference implementation and evidence for a proposed Tau decision shortcut. Given concrete masks of the same width, a single existentially bound x, and a conjunction of the following shape, the solver returns the bit-inclusion greatest value of x satisfying every constraint except the final nonzero test.

```text
x & y = 0
for each i:  (x & u_i = 0) OR (x & v_i != 0)
require x != 0
```

Start with the width-limited complement of y. When the current bound has no bit in common with v_i, every remaining witness must avoid u_i. Clear those bits and discharge the clause. Once the bound satisfies every remaining positive arm, the bound itself is a witness for the constraints. Existence of a nonzero solution is equivalent to this final bound being nonzero. The straightforward C++ implementation has at most as many discharges as clauses. Repeated scans of the clause vector can take quadratic time.

## Run the C++ check

From this directory, with a C++17 compiler:

```sh
c++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror replay.cpp -o replay
./replay
```

The oracle checks all 17,472 two-bit formulas with one through three ordered clauses and all 69,888 witness assignments. It also checks a 64-bit input, a forced cascade, and unsupported polarities and widths. The reference accepts typed concrete masks of widths 1 through 64. Binding and syntactic recognition belong to the caller. [C++ implementation](guarded_bv.hpp) · [Oracle and controls](replay.cpp)

## Proof and native evidence

A Lean proof derives the greatest witness and the existential elimination rule for an arbitrary Boolean algebra with decidable equality. It also covers any additional upward-closed predicate on x. The source uses no project-specific axioms or proof placeholders. [Lean source](GuardedWitness.lean)

The replay archive contains the C++ and Lean projects, native inputs, an exact-source Tau wheel identifier, JSON verdicts, Python frontend and all paired raw timing samples. The stock Tau source and binaries are distributed by IDNI. The original code in this directory is supplied under the repository's MIT license. [Download the replay archive](replay.zip)

```sh
unzip replay.zip
cd guarded-bv
sha256sum -c SHA256SUMS
```

The native comparison measures the public Python string interface on Tau devel `ab7a13ed610ff6cfb8364dd2e509df74c9bdac6c`. On matching inputs the external prototype recognizes the input text, computes the bound and sends a short ground formula to the same native decision call. In the fallback both arms submit identical input text. See `native/README.md` for exact parameters, artifact provenance, native build instructions and timing scope. The C++ implementation above was checked for correctness separately. No native solver patch is benchmarked here.

Additional controls are in `native/extended-controls.md`. On the release CLI, the first decision command on the stored 16-bit cascade took 3.02 ms on the original expression and 1.20 ms on the reduced expression. Preparing, displaying and storing the expressions took 70.44 and 2.66 ms. A typed upstream prototype would still need to measure the cost of recognizing the original tree.
