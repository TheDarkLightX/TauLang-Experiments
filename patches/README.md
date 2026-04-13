# Patches

This directory is for minimal patch files against official Tau Language checkouts.

Patch policy:

- Keep patches focused.
- Do not include generated build artifacts.
- Avoid large copied blocks of Tau source when possible.
- Prefer feature flags for experimental behavior.
- For substantial work, prefer an upstream pull request or explicit permission from IDNI.

Expected workflow:

```bash
./scripts/setup_tau.sh
./scripts/apply_patches.sh
```

The patches are applied to `external/tau-lang`, which is gitignored.
