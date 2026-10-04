# Complete raw evidence

The three gzip-compressed tar archives preserve every retained raw result from the expanded experiment and development runs. ARCHIVES.json pins exact bytes. Archives contain only original research inputs/outputs and receipts; no upstream Tau source, dependency source or executable binary is included.

From the study directory, expand them using Python3.12 or later:

    python3 -c "import tarfile; from pathlib import Path; [tarfile.open(p).extractall('.', filter='data') for p in sorted(Path('evidence').glob('*.tar.gz'))]"

Extraction restores the gitignored results/heldout-001, results/reuse-001 and development directories. It does not alter the frozen source, protocol or corpus files. Use a fresh checkout to avoid overwriting an existing local replay under those directory names.

- heldout-001.tar.gz: all 336 quality cases and their raw native receipts, exact emitted expressions, registry proposals, gate records and start/final manifests.
- reuse-001.tar.gz: all 30 online stream/repetition runs, 7,680 arm requests, every raw native receipt, complete cumulative curves, source/freeze identities, independent verification and timing-overlap note.
- development-evidence.tar.gz: five exploratory/integration runs, including superseded accounting versions and the final current-source smoke. These are development evidence, not confirmatory outcomes. Consult DEVELOPMENT_HISTORY.md before interpreting older timing fields.

Readable final summaries and analyses are also kept as ordinary files under results/ and paper/. Compressing the raw receipts avoids storing over a gigabyte of repeated JSON directly in Git. scripts/package_evidence.py deterministically rebuilds each archive from its restored files into a fresh destination.
