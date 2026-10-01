# Validation records

The macOS logs contain the full default-pack runs and focused reduced-pack
checks. The Linux logs contain only the focused bit-vector-pack checks. The
three full-suite failures are compared with a separate stock build in
`failure-comparison.json`; stock was checked only for those three tests.

Detailed full-suite output is compressed in the three `full-*-last.log.gz`
files. The smaller `full-*.log` files list every configured test and outcome.

Local directory prefixes and terminal colors have been removed from log copies.
Test names, commands, returned formulas, pass/fail outcomes and recorded durations
are retained. Runtime performance comes from the separate VM replay records,
not from regression-test durations. RSS is a sample, not a lifetime peak.

Every benchmark configuration uses the same executable on its platform and the
same compact VM source. The three arms are `baseline` (six memory options off),
`parser_trim` (parser cleanup and trim on), and `selected` (all six on). These
names are defined in `replay_memory.py`. Linux measurements are native arm64 in
a container; the full regression suite was run on macOS.
