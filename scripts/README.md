# Scripts

If the scripts are not executable after checkout, run them through `bash`:

```bash
bash scripts/setup_tau.sh
bash scripts/apply_patches.sh
bash scripts/run_benchmarks.sh
```

or set executable bits locally:

```bash
chmod +x scripts/*.sh
```

The scripts clone Tau Language from the official IDNI repository into `external/tau-lang`. That directory is gitignored and should not be committed.
