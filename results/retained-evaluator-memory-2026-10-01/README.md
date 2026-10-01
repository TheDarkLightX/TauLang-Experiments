# Retained VM memory extension

[Build instructions, results and patch details](memory-replay/README.md) ·
[Download the reproduction ZIP](memory-reproduction.zip)

The fresh Linux arm64 comparison reduces sampled RSS after 311 evaluations from
493.96 to 163.25 MiB with all six memory options enabled. Parser cleanup plus
allocator trim alone reaches 166.24 MiB. This is a post-loading footprint result;
RSS immediately after loading remains about 476 MiB. The fresh macOS saving is
about 3%, where glibc trimming is unavailable.

The three full macOS Release suites each report 2,639 passes and the same three
stock printing failures out of 2,642 configured tests. Focused reduced-pack and
Linux checks pass. The package includes complete and incremental Tau patches,
the required parser patch, source identities, raw results and reproduction tools.
Per-evaluation figures are medians of the five per-process step medians.

ZIP SHA-256: `670cecab1f856c14a0874de9d5d310beeb4dae06ecf687362f71d1c14c447481`

The extracted ZIP passed every manifest check, independent replay of both saved
4,665-output measurement sets, and a fresh live example on the tested executable.
See [the extraction check](extracted-package-check.json). Platform, configuration,
shared-host timing limits and the full distinction between broad and focused
tests are documented in the package.
