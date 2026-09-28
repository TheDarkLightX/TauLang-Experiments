# Tau correctness reproduction packages — 27 September 2026

These packages contain pinned build instructions, small command-line reproductions, independent expected answers and recorded outputs for Tau `fd536d56e00f12187cbed123c67a735a6964c660` with parser `5b14b6fde86f16dc52c4c0a953a8a1e53c88f95a`.

- [Built-in min/max parsing](minmax-parser-reproduction.zip): optional grammar correction, ten regression tests, exact small-value checks, original/corrected outputs and registered Release test results. After extraction, `python3 verify_results.py` checks the stored evidence without building Tau. All 2,352 exact candidate checks pass; the configured Release suite initially passed 2,370 of 2,378 entries, with the remaining eight passing after correcting child compiler selection. Excluded and optional suites remain outside that result.
- [Rational interval and order checks](tau-correctness-reproduction.zip): 27 selected checks across seven report topics, including the original min/max examples. On the recorded unmodified build, 17 fail and 10 controls pass. The archive has no proposed correction. After extraction, `python3 check_expected.py` checks the independent expectations; `python3 check.py --tau /path/to/tau --output replay.json` runs the full set. That live command is expected to exit 1 on the affected revision. A failed check must be inspected; it does not by itself establish a new bug.

Each archive has its own README and manifest. Scripts require Python 3.9 or later and use its standard library. Live checks require a separately built Tau executable. The packages reject diagnostics, incomplete output, invalid models, nonzero exits and timeouts rather than counting them as successful checks. These results do not establish complete language correctness, cross-platform coverage or a performance improvement.

The min/max correction was developed after the unmodified-build check set. The general archive's statement that it contains no tested correction describes that archive; the separate min/max archive supplies the later correction and its results.

Archive checksums are in [SHA256SUMS](SHA256SUMS). On macOS run `shasum -a 256 -c SHA256SUMS`; on systems with GNU coreutils use `sha256sum -c SHA256SUMS`.
