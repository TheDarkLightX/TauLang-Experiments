# TauFold application execution and proof-checker experiments

This tests the retained evaluator proposed in [Tau #199](https://github.com/IDNI/tau-lang/issues/199)
on three actual TauFold V1 applications. Native Tau computes every transition.
A checker generated from the original Tau specification checks the resulting
trace inside RISC Zero 3.0.6. Real succinct receipts are then verified in a
separate process. All inputs here are public synthetic examples.

TauFold is pinned to `d3671f46ec316b1adcc21a2bfdb8c68afda004cc`.
The original VM specification is byte-identical to the earlier evaluator
benchmark: SHA-256 `6bd3f28e938038a363182d01c1371f2f4cfdd487677de2d474e3dc0a4496f4eb`.
This is the 32-bit V1 VM, not the separate V2 account-policy implementation.

## Native Tau results

Mac M3 Max, 128 GiB, macOS 26.6.2; three fresh processes per application and
variant. The order is forward, reverse, forward, not a fully balanced design.
The desktop was not isolated from all other activity. Builds and other heavy
experiments did not overlap these timed runs. See `environment.json` for pins.

Times are medians of **setup plus the sum of adapter step calls**. They exclude
the independent Python checks, state assembly between calls, and proving. They
are not measurements of the complete application or UI workflow.

| Application and public result | Steps | Ordinary Tau | Retained evaluator | Program fixed before load | Program and input fixed before load |
| --- | ---: | ---: | ---: | ---: | ---: |
| Auction: second-highest bid 58,000; winner index 1, counting from zero | 73 | 18.867 s | 2.052 s | 1.824 s | 1.795 s |
| Payroll: within-budget result 1 | 56 | 14.908 s | 2.075 s | 1.782 s | 1.774 s |
| Clipped linear classifier: decision 1 | 32 | 9.999 s | 2.017 s | 1.871 s | 1.836 s |

The ordinary adapter already keeps one Tau process alive. The retained variant
uses the published evaluator and memory patches, with all six memory options
enabled, plus the previously published shared lookups and record-equality source
rewrite. Thus the 4.96–9.20× comparison is the combined execution route, not the
isolated contribution of any one memory option.

The two preparation variants replace fixed scalar fields with exact 32-bit Tau
constants before loading. Program-only preparation leaves 37 unbound fields;
preparing the whole run leaves 20, down from 102. All 21 outputs, including the
fault flag, remain. This is an adapter/source experiment, not a new C++ patch.
It rejects changes to bound values. Private values belong to that one execution;
the prototype does not place prepared private inputs in a shared cache.

Preparing the whole run reduces these native totals a further 9.0–14.5%
(1.10–1.17×). Program-only preparation captures much of that benefit.
Setup remains around 1.74–2.02 s for the retained variants, versus 0.48–0.50 s
for ordinary Tau. Sampled RSS at the end is approximately 182–193 MiB for
ordinary Tau, 504–507 MiB for retained evaluation, and 461–462 MiB for whole-run
preparation. These are samples, not peak-memory measurements. The earlier Linux
allocator result must not be applied to this Mac comparison.

## Proof-checker experiments

The first experiment shares repeated expressions and replaces masked `u128`
arithmetic with wrapping `u32` arithmetic, only after confirming that the parsed
specification contains Boolean and 32-bit nodes. On these applications this
reduces guest cycles by about 4.3%, but leaves proof segment sizes unchanged.
The one-run proof times did not improve. Smaller generated text alone did not
solve the proving bottleneck. Separate width-only and sharing-only controls are
included in `saved/`.

The prepared checker also retains 32-bit words across the generated function
boundary, prepares the 82 fixed program/input fields once, and compares the
20 resulting state words directly. This avoids repeated widening, fixed-field
packing, program validation and a temporary memory-vector allocation on every
transition. The original public relation still rejects out-of-range inputs.

| Application | Original guest cycles | Prepared checker cycles | Reduction | Original / prepared segment cycles |
| --- | ---: | ---: | ---: | ---: |
| Auction | 852,601 | 292,180 | 65.7% | 1,048,576 / 524,288 |
| Payroll | 652,816 | 229,868 | 64.8% | 1,048,576 / 524,288 |
| Classifier | 413,508 | 164,272 | 60.3% | 524,288 / 262,144 |

Segment cycles include padding and other proving work; guest cycles alone do
not determine proving time. The complete proof timing observations are in
`saved/proof-results.json` and `saved/prepared-proof-results.json`. Each is one
real proof per application and checker, not a repeated timing estimate:

| Application | Original proof process | Sharing + 32-bit arithmetic | Prepared checker |
| --- | ---: | ---: | ---: |
| Auction | 86.050 s | 102.604 s | 54.886 s |
| Payroll | 93.401 s | 120.793 s | 51.529 s |
| Classifier | 50.186 s | 52.391 s | 30.210 s |

The prepared observations are 36.2–44.8% lower than the original. Their different
positions in the run order and desktop activity prevent a precise timing claim.
All nine real receipts passed separate-process verification. Each application's
public claim is byte-identical across the three checker versions, using the same
native trace and random salt. Proof sizes remain 224,034 bytes for auction and
224,026 bytes for payroll and classification.

The prepared route preserves the initial-state, trace-length, input-cursor,
after-halt, fault, full next-state, termination, program-hash, input-commitment
and source-hash checks. Program and input are immutable for the trace and are
validated before preparation. Changing-state checks remain inside the loop.
All values on the internal route have Rust's `u32` type; this optimization is
not a license to narrow arbitrary Tau bit-vector widths.

This is a **separate TauFold checker patch**. The native Tau optimization can
use the original guest unchanged. Changing the checker creates a new guest
image and requires an explicit verifier pin update. The old image rejects
receipts from the prepared image, as expected. Saved guest identities are from
these fresh Mac builds; they are not claimed to match historical Linux releases.

## Correctness evidence and limits

- 1,932 native transition comparisons across the 36 measured processes match
  the Python expression model of the original specification, including all
  21 output words. Every arm produces the same complete trace.
- Fixed-input preparation also passes all seven example programs: 402
  transitions, 420 boundary-state checks, seven changed unbound-input checks,
  and 42 rejections of changed fixed values.
- Four generated Rust variants match 1,992 original-source vectors each:
  7,968 comparisons, including every opcode, boundary words and all seven
  example traces. The prepared executable is checked separately against the
  same 1,992 vectors and rejects three out-of-range public inputs.
- Each initial checker build passes all 12 core/host test cases, including
  direct guest checks. The prepared checker passes 13, including 6,357
  comparisons with the original trace-checking route for valid and changed
  states. Test logs are included.
- Receipts, public claims, hashes, identities and separate-process verification
  results are included. Private witness files are not included. The saved-data
  checker recomputes expected native outputs and rejects a changed output,
  missing repeat and altered timing total. It checks recorded proof evidence;
  it does not itself perform cryptographic verification.

These are finite tests and a scoped prototype, not proof of equivalence for all
Tau programs. The Tau executable and patches were unchanged during this work;
the [prior full qualification](https://github.com/TheDarkLightX/TauLang-Experiments/tree/03874744432cb7f4643a851ba4f8d0af2e6dfa54/results/retained-evaluator-memory-2026-10-01)
still applies, with its three stock-reproduced printed-order failures and
platform limits. The full Tau suite was not rerun for these adapter and Rust
changes. No UI, throughput-under-load, or full end-to-end speedup is claimed.

## Short saved-evidence check

Python 3.12, no Tau or proving installation required:

```sh
python3 -B verify_results.py
```

## Fresh native execution

Download the earlier complete Tau patch/build package and check its checksum:

```sh
curl -fL https://raw.githubusercontent.com/TheDarkLightX/TauLang-Experiments/03874744432cb7f4643a851ba4f8d0af2e6dfa54/results/retained-evaluator-memory-2026-10-01/memory-reproduction.zip -o memory-reproduction.zip
python3 -c "import hashlib; assert hashlib.sha256(open('memory-reproduction.zip','rb').read()).hexdigest() == '670cecab1f856c14a0874de9d5d310beeb4dae06ecf687362f71d1c14c447481'"
unzip -q memory-reproduction.zip
```

Follow `memory-replay/README.md` for Tau dependencies, its license and building
the candidate. Build a separate stock control at the same Tau/parser pins with
the same Release options; apply only `macos-build.patch` on Mac. The current
comparison uses Tau `a739b90259729590dee7b424df05ba65bfdeacf2` and parser
`5b14b6fde86f16dc52c4c0a953a8a1e53c88f95a`, not TauFold's older Tau build pin.
Keep both executables unchanged throughout a run.

Obtain the application source in a fresh directory:

```sh
git clone --filter=blob:none --sparse https://github.com/TheDarkLightX/TauFoldzkVM.git source
git -C source checkout --detach d3671f46ec316b1adcc21a2bfdb8c68afda004cc
git -C source sparse-checkout set zkvm
git -C source apply ../host-profile.patch
python3 -B native_experiments.py --catalog memory-replay/catalog \
  --source source/zkvm --candidate /path/to/candidate/tau \
  --stock /path/to/stock/tau --output native-measured --repeats 3
python3 -B check_binding.py --catalog memory-replay/catalog \
  --source source/zkvm --candidate /path/to/candidate/tau --output binding-check
```

The native script also writes synthetic witness files with mode 0600. The proof
runner replaces the fixed comparison salt with fresh random bytes. Keep witness
files separate from public receipts, and do not use real private inputs for this
reproduction.

## Fresh proof and checker tests

Install host Rust 1.97.1 and the RISC Zero Rust 1.94.1 toolchain using the
[official instructions](https://dev.risczero.com/api/zkvm/install). Select it as
the `risc0` Rust toolchain. Place or symlink the official **3.0.6** `r0vm` at
`tools/risc0-3.0.6/r0vm`; confirm its version. The recorded Mac archive checksum
is in `environment.json`. Allow several GB of RAM and build space. All proofs
use the local prover and explicitly disable development mode.

Run from this directory, sequentially:

```sh
python3 -B checker_codegen.py --root source/zkvm --output checker-candidates
python3 -B check_checker.py --catalog memory-replay/catalog \
  --source source/zkvm --output checker-check
python3 -B build_checkers.py
python3 -B prove_examples.py
python3 -B build_prepared.py
python3 -B check_prepared_relation.py prepared-checker/taufold-proof \
  checker-check/vectors.json --output prepared-relation.json
python3 -B prove_prepared.py
```

The builders temporarily modify only this fresh `source/zkvm` checkout and
restore the original compiler, generated source and core afterwards. They leave
the profiling host patch and helper files. The measured executables are copied
to separate folders before another variant is built. Output directories must
not already exist. Do not run competing builds or tests during proof timings.

To verify one new receipt without running Tau or the prover:

```sh
RISC0_DEV_MODE=0 TAUFOLD_R0VM=/nonexistent/r0vm TAU_BINARY=/nonexistent/tau \
  prepared-checker/taufold-proof verify source/zkvm/examples/auction.json \
  prepared-proofs/auction/receipt.bin prepared-proofs/auction/claim.json
```

The same command can check bundled files under `saved/prepared-proofs/` if the
rebuilt guest image equals the recorded identity. Never take a verifier's
expected image from an untrusted receipt; compare against the independently
selected build identity.

## Applying the experimental TauFold patch

On a fresh checkout of the pinned TauFold revision, copy `checker_codegen.py`
and `word_checker_codegen.py` into `zkvm/tools/`, apply
`saved/prepared32/prepared-trace.patch`, then regenerate:

```sh
python3 zkvm/tools/compile_tau.py
python3 zkvm/tools/compile_tau.py --check
```

The generated file must match `saved/prepared32/generated.rs`. Build and run the
core/host tests, including the normally ignored guest test, with the pinned
`r0vm` available. `host-profile.patch` is separate instrumentation; it is not
required for the prepared checker itself. Review the new guest identity before
updating any verifier configuration. This package proposes no automatic rollout.

Thank you @castrod for Tau's existing record-equality expansion and @taumorrow
for the related functional-step work in [#178](https://github.com/IDNI/tau-lang/issues/178)
and [PR #179](https://github.com/IDNI/tau-lang/pull/179). That PR was not applied
or benchmarked here. TauFold source retains its MIT license in `reference/LICENSE`;
Tau itself retains its separate upstream license.
