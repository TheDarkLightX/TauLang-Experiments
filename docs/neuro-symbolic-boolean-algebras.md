# Neuro-Symbolic Boolean Algebras

This note documents the first community experiment for a neuro-symbolic Boolean
algebra carrier in Tau. The implementation is intentionally small: `qns8` is a
finite powerset Boolean algebra over eight audited atoms, and `qns64` is the
same carrier shape over sixty-four audited atoms.

## Core Split

The design follows this split:

```text
q_NS(y | x) = q_N(y | x) * chi_S(y, x) / sum_z q_N(z | x) * chi_S(z, x)
```

Standard reading. The neuro-symbolic distribution at candidate `y`, given
input `x`, is the neural distribution at `y`, given `x`, multiplied by the
symbolic characteristic function at `(y, x)`, then divided by the total
surviving neural mass over the finite candidate universe.

Plain English. The model proposes candidates with scores. Tau removes
candidates that fail exact symbolic checks. The host renormalizes the remaining
scores.

Boundary. Tau is not trusted to compute the neural score. Tau is only used for
the exact Boolean filtering step.

## Implemented Carrier

Carrier:

```text
B_x = P(U_x)
```

Operations:

```text
A meet B = A intersection B
A join B = A union B
A prime = U_x without A
```

The native Tau carriers are `qns8` and `qns64`. Each value is a bit mask. Meet
is bitwise `&`, join is bitwise `|`, and prime is represented in the demo as
XOR with the top element, for example `{ #xFF }:qns8` or
`{ #xFFFFFFFFFFFFFFFF }:qns64`.

## Tested Lanes

The demo uses the same carrier family for three interpretations:

- Candidate filtering, where each atom is a proposed action.
- Controlled-vocabulary concept filtering, where each atom is an audited
  concept such as `registry_verified` or `sanction_risk`.
- Bounded trace-class filtering, where each atom is a protocol trace class such
  as `trade_without_login` or `admit_before_patch`.

The trace-class lane is not a full regular-language Boolean algebra. It is a
finite quotient that demonstrates the same exact set operations on audited
trace labels.

## Reproduction

Run:

```bash
./scripts/run_qns_semantic_ba_demo.sh --accept-tau-license
```

The script downloads the official Tau Language repository, applies the local
experiment patches, builds Tau, and runs Tau normalization checks over `qns8`
and `qns64` expressions.

The main Tau example is:

```text
examples/tau/qns_candidate_filter_v1.tau
```

The result is written to:

```text
results/local/qns-semantic-ba-demo.json
```

## Proof Artifact

The matching Lean packet is:

```text
proofs/lean/qns_semantic_ba_v001
```

It proves the formula-level finite powerset laws used by the demo:

```text
unsafeLeak u n allowed review hardReject = bottom
```

Standard reading. The meet of the auto-accepted region and the hard-rejected
region is the empty region.

```text
partition u n allowed review hardReject = proposed u n
```

Standard reading. The join of the auto-accept, human-review, and symbolic-reject
regions is exactly the proposed region.

Boundary. The Lean packet proves the Boolean formula semantics. It does not
prove the C++ parser, bit-mask implementation, neural scoring, or correctness
of an LLM atom extractor.

## Why `qns64` matters

`qns8` is small enough for teaching. `qns64` is large enough to hold a useful
audited candidate menu: actions, concept atoms, protocol trace classes,
tool-call labels, or proof-obligation categories. The semantics are still the
ordinary finite powerset Boolean algebra.

## Boundary

This is not upstream Tau `nlang`. It is not probabilistic Tau. It is not proof
that an LLM extracted the correct atoms. It is a finite, exact symbolic carrier
for the part of the neuro-symbolic loop that Tau can check deterministically.
