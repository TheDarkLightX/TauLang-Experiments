# Lossless reuse-evidence storage

The reuse archive is stored as four ordered parts to fit bounded publication
transport payloads. This is a storage-only adaptation: no archive member was
removed, altered, recompressed, or selected. The part manifest records the
original compressed archive's SHA-256, exact byte count, and each part's order,
size, and SHA-256.

From the repository root, reconstruct and validate it with:

```sh
python3 experiments/semantic_saturation/evidence/reconstruct_reuse.py
```

The helper validates every part and the entire concatenation before creating
`experiments/semantic_saturation/evidence/reuse-001.tar.gz`. It refuses to
overwrite different existing content or a symlink; an identical existing file
is verified. It does not extract archive entries. Existing reproduction commands
can then use the reconstructed archive at their original path.

The reconstructed SHA-256 is
`ede9201dbbc4aa3d37c175c360a5514bdfe9d17c5f424d7465ae282799f8f581`.
The full compressed archive is 25,305,939 bytes. Its bytes are identical to the
archive at the original locally audited scientific revision
`4d5e97f18bb79aebebb3d386e9c09670e1d3b757`.
