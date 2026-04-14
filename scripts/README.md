# Scripts

## Smooth table demo

```bash
./scripts/run_table_demos.sh --accept-tau-license
```

This is the recommended public reproduction path.
It clones the official Tau Language repository into `external/tau-lang`, checks
out the tested commit, applies the experiment patch, regenerates Tau's parser,
builds the Tau binary, and runs the table demos.

The script writes local proof reports under:

```text
results/local/
```

Do not commit machine-local proof reports unless they have been reviewed for
machine-specific paths.

## Separate steps

```bash
./scripts/setup_tau.sh --accept-tau-license
./scripts/apply_patches.sh
./scripts/run_table_demos.sh
```

`setup_tau.sh` requires explicit license acknowledgement because this repository
does not redistribute Tau Language source or binaries.

`apply_patches.sh` applies patch files under `patches/` to the official Tau
checkout. It skips patches that are already applied and regenerates the parser
when the grammar is patched.

`run_table_demos.sh` is intentionally scoped. It checks the feature-gated safe
table fragment, not full unrestricted TABA tables.

The current suite includes:

- finite-carrier helper checks,
- Tau-native table syntax lowering checks,
- protocol firewall priority checks,
- collateral admission reason-router checks,
- incident-memory state-transformer checks,
- pointwise revision locality and idempotence checks,
- feature-flag rejection checks.

If the scripts are not executable after checkout, run:

```bash
chmod +x scripts/*.sh
```

## Restricted Tau rewrite normalizer

The c111 proof lane has an executable companion:

```bash
python3 scripts/tau_kb_normalizer.py normalize \
  'pointCompl(common(a, pointJoin(a, b)))' \
  --json
```

The script implements the seven checked rewrite rules from the restricted
Knuth-Bendix-style Tau expression system. It is intentionally narrow:

- it checks semantic parity over Boolean valuations,
- it checks that the c111 measure decreases at every emitted step,
- it does not orient commutativity, associativity, or distributivity,
- it is not a complete Boolean-algebra equivalence checker.

The benchmark wrapper records a deterministic corpus receipt:

```bash
./scripts/run_benchmarks.sh
```

That writes `results/local/kb-normalizer-benchmark.json`.

If a patched Tau binary is available, the same wrapper also runs:

```bash
python3 scripts/run_qelim_kb_probe.py
```

That writes `results/local/qelim-kb-probe.json` and compares the BDD qelim
backend with and without the opt-in `TAU_QELIM_BDD_KB_REWRITE=1` pass. The
generated matrix also tests `TAU_QELIM_BDD_KB_REWRITE=guarded`, which runs the
rewrite pass only when a cheap scan detects an absorption opportunity.

For the larger generated matrix, run:

```bash
RUN_QELIM_KB_MATRIX=1 ./scripts/run_benchmarks.sh
```

or directly:

```bash
python3 scripts/run_qelim_kb_matrix.py \
  --tau-bin external/tau-lang/build-Release/tau \
  --out results/local/qelim-kb-matrix.json
```

The matrix compares `bdd`, `bdd+kb`, `bdd+kb_guarded`, `bdd+ac`,
`bdd+ac+kb`, and `bdd+ac+kb_guarded`.
It is intentionally opt-in because it runs many Tau subprocesses.

To test whether guarded KB helps the already-promoted `auto` qelim route, run:

```bash
python3 scripts/run_qelim_auto_kb_matrix.py \
  --tau-bin external/tau-lang/build-Release/tau \
  --out results/local/qelim-auto-kb-matrix.json
```

That matrix compares `default`, `auto`, `auto+kb_guarded`, and
`auto+kb_forced`. Exact output parity is checked against the unmodified `auto`
route. Exact default parity is recorded separately because default and `auto`
may print semantically equivalent residual formulas in different syntactic
forms.
