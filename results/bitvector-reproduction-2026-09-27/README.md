# Bit-vector correctness and BDD reproduction packages

These two packages support separate proposals against Tau `fd536d56e00f12187cbed123c67a735a6964c660`, with parser `5b14b6fde86f16dc52c4c0a953a8a1e53c88f95a`.

- [Arithmetic elimination correction](bitvector-elimination-reproduction.zip): a one-file patch, two small wrong-answer examples, 1,158 retained examples, an independent finite evaluator, build instructions and recorded checks. The correction-only build passed 4,632 checks across two preprocessing settings and two block-splitting limits.
- [Bounded BDD decision](bdd-decision-reproduction.zip): the arithmetic correction and the separate optimization patch, source-build instructions, 270 check inputs, seven timing examples, independent expectation checks and recorded results. Both compared builds contain the arithmetic correction. The measurements include gains, regressions and timed-out reference runs; they do not establish a universal speedup.

Download and extract the relevant ZIP, then follow its README. Python 3.9 or later and Tau's platform build dependencies are required. Obtain Tau source from the official repository as directed by the package; no precompiled executable is supplied.

The archive manifests record hashes of their contents. SHA-256 checksums of the ZIP files are:

```text
0525ec17c60803c3fded9e12658bc1046602b15f89c251a9dd8a10357ac0ed15  bitvector-elimination-reproduction.zip
67d8c1836dfa25bd6621930e21665cdd58f7c86adf3a3f5ea4b4455b11feefb1  bdd-decision-reproduction.zip
```

The selected test inputs and timings have the limits documented in each package. These are research patches for review, not an official Tau release.
