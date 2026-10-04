# Reproduction commands and boundaries

These commands provide a self-contained supplement to the study replay plan. A test-split run requires explicit `--freeze` and `--expect-freeze-sha256` arguments, included below. This supplement does not alter the frozen source, protocol, corpus, or analysis.

The fresh native-execution commands below are recipes, not claims of another completed native campaign. The completed offline clean-checkout replay is recorded separately below. Run from the repository root unless stated otherwise. Obtain Tau separately from the official IDNI repository, review its license, and supply the intended binary path. The publication packet does not redistribute it.

## Identities

- Destination base revision: `65ef69bdc5e6f1e479236d9dfb4d9b6d2e5302d1`.
- Original local scientific source/evidence revision used for the clean replay: `4d5e97f18bb79aebebb3d386e9c09670e1d3b757`, binding 163 regular Git blobs.
- Remote [scientific storage revision `3ee5ee545486b910e24e5efe034ad762a1abad36`](https://github.com/TheDarkLightX/TauLang-Experiments/commit/3ee5ee545486b910e24e5efe034ad762a1abad36) contains 169 scientific files: 162 unchanged original blobs and seven lossless archive-storage files. [RELEASE_BINDING.json](../RELEASE_BINDING.json) records this packaging relationship; it does not relabel the historical replay as a run of a later commit.
- Tau source: `7625580db1a54e0b55beaf753566c137df42fe66`.
- Required primary Linux binary SHA256: `874511bf414d0bfbaca224d6fde1cc2514419ad15c912d24dd334f6792909726`.
- Main freeze SHA256: `f98ef54d269d43e79561010bfa3faff327d97981159a0aa1c5224128d14f67f2`.
- Online reuse freeze SHA256: `080f547d64b7b7387fad4162140f8e07981fe0ec926d304d92a0c32755229456`.
- Python 3.12.14, SymPy 1.14.0, and Lean 4.29.1 identify the recorded environment; all remaining build information is in `../results/build/environment.json` and `../results/build/build-receipt.json` relative to this file.

The remote scientific storage commit has tree `2705912415f2bb37e52826d07d81feee96852623`, exactly equal to independently audited local packaging revision `12a00314bbef5f74b5ab0c7f8e624918384a332d`. [PUBLICATION_PROVENANCE.json](../PUBLICATION_PROVENANCE.json) records the identity mapping and separates the final manuscript release from the scientific storage commit. A compatible rebuild is not automatically byte-identical to the recorded binary. A different binary changes the provenance scope and does not reproduce the exact primary profile merely by accepting the same syntax.

## Completed clean-checkout replay

The [clean-checkout summary](../results/clean-checkout-replay/SUMMARY.json) records a separate local Git clone of original scientific revision `4d5e97f18bb79aebebb3d386e9c09670e1d3b757`, with no copied untracked source files and evidence archives extracted after hash verification. It passed 81 unit tests, full validation of 336 heldout cases, verification of all 30 reuse runs, `lake build`, and the 1,073-fixture Lean correspondence replay (11,979 observations; 19 refinement cases and 273 children). This replay launched zero native Tau processes. It used the same Linux host and existing Python, SymPy, and Lean installation, so it establishes committed-checkout reproducibility rather than a fresh dependency installation, native rebuild, or native campaign. The summary links and hashes the actual replay receipts.

## Reconstruct archived evidence before offline replay

The reuse archive is stored as four exact byte parts to fit publication transport limits. The [storage instructions](../evidence/ARCHIVE_PARTS.md) and part manifest define their order, byte counts, and hashes. No archive member is changed, removed, or recompressed. From the repository root, run the hash-checking helper before extracting reuse evidence:

```sh
python3 experiments/semantic_saturation/evidence/reconstruct_reuse.py
tar -xzf experiments/semantic_saturation/evidence/reuse-001.tar.gz \
  -C experiments/semantic_saturation
```

The reconstructed compressed archive is 25,305,939 bytes with SHA256 `ede9201dbbc4aa3d37c175c360a5514bdfe9d17c5f424d7465ae282799f8f581`, identical to the original audited archive. The helper verifies every part and the complete concatenation before creating the file, and refuses to replace different content or a symlink. The helper does not extract members; perform the shown extraction only into a clean checkout without an existing raw reuse result tree. Quality and development archives remain whole files. The flattened reuse summaries used by the paper figures need no archive reconstruction.

## Python tests and frozen identities

```sh
export PYTHONPATH=experiments/semantic_saturation/src
python3 -B -m unittest discover -s experiments/semantic_saturation/tests -v
sha256sum experiments/semantic_saturation/FREEZE.json
sha256sum experiments/semantic_saturation/corpora/reuse-frozen-v1.json
sha256sum "$TAU_BIN"
```

Set `TAU_BIN` to the separately obtained binary's absolute path before invoking it. The freeze-aware runner verifies every file named by the manifest. Do not regenerate the freeze to make a mismatch disappear. Do not use Python optimization options that disable assertions: optimized execution is outside the frozen profile.

## Fresh quality execution

`results/reproduction-quality-001` below must not already exist. To rerun again, use another explicitly named fresh directory.

```sh
python3 experiments/semantic_saturation/src/run_study.py \
  --corpus experiments/semantic_saturation/corpora/test.json \
  --binary "$TAU_BIN" \
  --freeze experiments/semantic_saturation/FREEZE.json \
  --expect-freeze-sha256 f98ef54d269d43e79561010bfa3faff327d97981159a0aa1c5224128d14f67f2 \
  --out experiments/semantic_saturation/results/reproduction-quality-001

python3 experiments/semantic_saturation/src/validate_run.py \
  experiments/semantic_saturation/results/reproduction-quality-001 \
  --out experiments/semantic_saturation/results/reproduction-quality-001-validation.json

python3 experiments/semantic_saturation/src/analyze_results.py \
  experiments/semantic_saturation/results/reproduction-quality-001 \
  --out experiments/semantic_saturation/results/reproduction-quality-001-analysis.json
```

The validator launches no native process. It validates persisted evidence and recomputes support/parsing/accounting. The first command is the fresh native execution. Keep these evidence levels distinct. Retain incomplete, failed, or invalidated directories with their status; do not reuse their names as though nothing failed.

## Fresh online reuse execution

The following campaign is separate from the common-transcript quality run and retains three fixed repetitions. The destination must be fresh.

```sh
python3 experiments/semantic_saturation/src/run_reuse.py \
  --freeze experiments/semantic_saturation/corpora/reuse-frozen-v1.json \
  --expect-freeze-sha256 080f547d64b7b7387fad4162140f8e07981fe0ec926d304d92a0c32755229456 \
  --binary "$TAU_BIN" \
  --out experiments/semantic_saturation/results/reproduction-reuse-001

python3 experiments/semantic_saturation/src/run_reuse.py \
  --verify-out experiments/semantic_saturation/results/reproduction-reuse-001 \
  --expect-freeze-sha256 080f547d64b7b7387fad4162140f8e07981fe0ec926d304d92a0c32755229456
```

The offline verifier's console result should be retained as a separately named receipt. No mocked-native mode is used for these commands. Unit-test mock receipts establish control-flow tests only.

## Resource screens

The support runner can replay its matrix in a fresh destination without a native binary. The search screen additionally needs the exact validated development result directory used to supply checked pairs. That directory identity must be recorded in the final release inventory rather than guessed from an arbitrary development run.

```sh
python3 experiments/semantic_saturation/src/run_resources.py \
  --out experiments/semantic_saturation/results/reproduction-resources-001 \
  --development-results "$VALIDATED_DEVELOPMENT_RESULTS"
```

Set `VALIDATED_DEVELOPMENT_RESULTS` to the released development result directory after checking its identity and validation receipt. Compare the generated resource matrix to the frozen `corpora/resource-protocol/matrix.json`. This is a descriptive resource screen: it launches zero native processes and does not certify the extracted search outputs for deployment.

## Lean reference and implementation correspondence

Install the official toolchain specified by `proofs/lean/support_cells_v001/lean-toolchain` and place its binaries on PATH. From that directory:

```sh
lean --version
lake build
python3 replay.py
```

`replay.py` checks the theorem and dependency audit, deterministic bridge generation, fixtures, parser correspondence, and mutation controls. It writes fresh replay receipts in that proof directory, so use a disposable clean checkout or preserve prior receipts before reproduction. The versioned fixtures are inputs. `prepare_fixtures.py` is optional historical construction provenance, is not a replay prerequisite, and must not be required to access private historical material.

A successful Lean replay proves the set-model theorem and establishes the recorded differential fixture agreement. It does not prove the Python adapter, native Tau implementation, e-graph, emitted-byte optimality, or performance.

## Rebuild paper displays and PDF

The raw quality records are packaged as `evidence/heldout-001.tar.gz`; reuse records become `evidence/reuse-001.tar.gz` after the lossless reconstruction above. Their archive members begin with `results/heldout-001/` and `results/reuse-001/`, respectively. Verify the released evidence manifest before extraction. If raw quality records are absent, extract the quality archive into the study directory, then rebuild the paper-only displays:

```sh
tar -xzf experiments/semantic_saturation/evidence/heldout-001.tar.gz \
  -C experiments/semantic_saturation
python3 experiments/semantic_saturation/paper/build_parser_sensitivity.py --check
python3 experiments/semantic_saturation/paper/build_quality_figures.py
python3 experiments/semantic_saturation/paper/build_reuse_figures.py
python3 experiments/semantic_saturation/paper/build_pdf.py
```

The reuse figure builder reads flattened public summary/analysis/verification files and does not require extracting the raw reuse archive. These commands perform no new native Tau measurement. The quality figure builder requires Matplotlib (recorded 3.10.8). PDF layout uses Pandoc for Markdown parsing, ReportLab (4.4.9), Pillow (12.3.0), and the locally installed DejaVu Serif family at the font paths stated in `build_pdf.py`. It does not require a working TeX installation. Poppler `pdftoppm` renders the final PDF for visual review. Dependency availability and font paths must be checked on a different host.
