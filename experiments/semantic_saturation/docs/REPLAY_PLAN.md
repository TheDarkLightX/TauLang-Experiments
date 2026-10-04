# Replay and publication plan

This directory contains original research code, inputs, proof integration and measurement evidence. Tau source, binaries, third-party source archives, and compiler logs containing upstream source excerpts are excluded.

## Native dependency boundary

Obtain Tau from the official IDNI repository and review its license. Source revision `7625580db1a54e0b55beaf753566c137df42fe66` and parser revision `cdcc0f7e9bba21cce518405693ca55e75f292e3e` identify the clean source. The measured Linux binary is identified by `results/build/environment.json`, not redistributed. Build flags and raw-log hashes are in `results/build/build-receipt.json`.

The source build was made with GCC14.2, CMake3.31.6, Boost1.86, the `release-tau` preset, the `sbf,tau` pack, FTXUI disabled, LTO disabled, artifact preinstantiation disabled, and one build job. The official `dev` helper defaults to Clang in this preset; specify C and C++ compiler overrides when using GCC. Keep dependencies in an ignored external directory outside this packet.

## Commands

Set `TAU_BIN` to the absolute path of a compatible native binary. From the repository root, set `PYTHONPATH=experiments/semantic_saturation/src`. Then:

- Run Python unit tests with `python3 -B -m unittest discover -s experiments/semantic_saturation/tests -v`.
- Regenerate each corpus with `python3 experiments/semantic_saturation/src/generate_corpus.py --split test --out <fresh-corpus-path>` and compare its SHA256 against the freeze manifest.
- Run the frozen corpus with `python3 experiments/semantic_saturation/src/run_study.py --corpus experiments/semantic_saturation/corpora/test.json --binary "$TAU_BIN" --out <fresh-run-directory> --freeze experiments/semantic_saturation/FREEZE.json --expect-freeze-sha256 f98ef54d269d43e79561010bfa3faff327d97981159a0aa1c5224128d14f67f2`.
- Validate it with `python3 experiments/semantic_saturation/src/validate_run.py <fresh-run-directory> --out <validation.json>`.
- Analyze it with `python3 experiments/semantic_saturation/src/analyze_results.py <fresh-run-directory> --out <analysis.json>`.
- In `proofs/lean/support_cells_v001`, install the pinned Lean4.29.1 toolchain, run `lake build`, then `python3 replay.py`. The Python/Lean correspondence fixtures are development data, not the experiment holdout.

Output directories must be fresh; old receipts are never overwritten by a study run. Native and source identity changes create a new provenance scope. Changes to candidate policy, budgets, extraction, emitter, corpus or endpoints after test results require a separately labeled development cycle and new holdout, not a retroactive overwrite.

## Validation boundaries

The validation script launches no native processes: it recomputes support semantics, parses emitted bytes, checks metrics, checks exact native truth receipts against stored raw processes, and rejects source/binary-profile mismatches. A fresh native rerun is a separate command. The Lean replay proves its set-algebra semantics and tests the Python adapter, but does not prove the native Tau implementation, Python parser or optimizer.

The historical Mac pilot is exploratory and retained by hash and scoped comparison. Its binary is absent; no artifact should imply that its binary bytes were rechecked in the Linux environment. Build-to-build differences are reported, not tuned away.

The frozen reuse input is corpora/reuse-frozen-v1.json, SHA256080f547d64b7b7387fad4162140f8e07981fe0ec926d304d92a0c32755229456. Its runner requires that exact hash and native binary profile; see REUSE_PROTOCOL.md. A replacement native build is a new provenance study and cannot be mislabeled as this pinned online campaign.

Frozen-file hashes are checked before held-out execution. If moving this package to a clean checkout, retain repository-relative layout and use the provided corpora. Raw process clocks and stdout are recorded execution evidence, not cryptographic attestations.
