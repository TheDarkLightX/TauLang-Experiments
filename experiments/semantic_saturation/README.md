# Checked semantic saturation for a restricted Tau fragment

This research packet combines a Lean-checked finite-support reference semantics with a frozen synthetic Tau optimization study and an online cache experiment. It is a scoped technical-report draft, not a new general equality-saturation/QE algorithm or a production compiler pass.

## Main findings

- The rewrite-disabled semantic egraph and a strong scoped recursive-congruence control tie emitted-byte quality on all 336 held-out cases. The egraph representation adds no measured quality advantage under those matched alternatives.
- The full hybrid adds rewrite search. Across 333 native-parser-supported cases it emits 24.10% fewer typed bytes than guarded native normalization and 17.12% fewer than native+SymPy. The portfolio beats the hybrid on 10 cases. Those 333-case comparisons are a post-hoc attribution sensitivity; the frozen 336-case result is preserved.
- Three unsupported native output forms caused 746 bytes of the primary apparent gain. They are parser-adaptation limits, not Tau solver failures. Among 105 supported quantified cases, the hybrid saves only 45 bytes against native and ties the simpler semantic controls.
- Every cached online arm uses the same native-call count. Semantic decision caching provides no savings beyond ordinary exact memoization. Fixed-bank signature indexing explains the candidate-search benefit; no special semantic-cache speedup is established.
- Lean proves exact executable support comparison for nonempty atomless Boolean subalgebras of sets. The Python adapter/parser, native Tau and optimizer are tested rather than formally verified. Abstract-BA representation transfer is not formalized.

## Read the paper and results

- [Manuscript source](paper/MANUSCRIPT.md)
- [Paper and figure guide](paper/README.md)
- [Validated held-out analysis](results/heldout-001-analysis.json)
- [Parser attribution sensitivity](paper/native-parser-sensitivity.json)
- [Online reuse results](results/reuse-001-ANALYSIS.md)
- [Timing-overlap disclosure](results/reuse-001-TIMING_NOTE.md)
- [Formal proof packet](../../proofs/lean/support_cells_v001/README.md)
- [Separate executable audits](audit/README.md)

## Reproduce

The prospectively frozen protocol, inputs and source hashes are in FREEZE.json; its SHA256 is f98ef54d269d43e79561010bfa3faff327d97981159a0aa1c5224128d14f67f2. No held-out optimization outputs were measured before this freeze. The protocol was recorded privately before execution; it is not a public preregistration claim.

Start with [paper reproduction instructions](paper/REPRODUCTION.md) and [complete raw evidence](evidence/README.md). Offline validation, unit tests and Lean replay do not require a native Tau binary. Fresh native measurements require the pinned official source/build profile; binaries are intentionally not redistributed. A different binary creates a new replication profile, not the same execution identity.

[License boundary](../../docs/license-and-use.md): this packet contains original harnesses, examples, proofs and research artifacts. Obtain Tau from the official IDNI repository under its own license. Private source archives, build dependencies, executable binaries, credentials and internal tracking records are excluded.
