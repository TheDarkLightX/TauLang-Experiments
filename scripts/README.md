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
