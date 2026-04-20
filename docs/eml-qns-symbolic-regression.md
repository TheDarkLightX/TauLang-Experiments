# EML/qNS Symbolic Regression Demo

This demo connects bounded EML symbolic-regression artifacts to Tau's finite
`qns8` Boolean-algebra carrier.

Project boundary: this is a community research prototype. It is not an official
IDNI or Tau Language feature, not an endorsement claim, and not a claim about
what IDNI intends to ship.

## Run

```bash
./scripts/run_eml_qns_demo.sh --accept-tau-license
```

The script downloads official Tau Language if needed, applies the local qNS
experiment patch, builds Tau, runs the certificate gate, and writes:

```text
results/local/eml-qns-demo-gallery.json
results/local/eml-qns-demo-gallery-manifest.json
results/local/eml-qns-demo-gallery-failclosed.json
```

## What It Shows

The demo has three lanes:

- slow lane: checked bounded EML regression fixture artifacts,
- fast lane: Tau `qns8` gating over finite certificate evidence masks,
- negative lane: tampered certificate rejection.

The pieces have different jobs:

```text
LLM or bounded enumerator:
  proposes candidate formulas

EML:
  gives analytic candidates a tiny symbolic syntax

host checker:
  checks grammar, domain, sample fit, holdout fit, and residual evidence

qNS:
  records checker results as finite Boolean-algebra masks

Tau qns8:
  performs exact finite mask operations

table memory:
  stores accepted evidence masks and preserves old memory on rejection
```

The LLM is not the trusted part. It is only a proposer. The useful property of
qNS as a Boolean algebra is that evidence state can be joined, intersected,
complemented relative to the evidence universe, and stored in table entries.

The current expected receipt is:

```text
slow_source_count = 2
fast_promoted_count = 7
tampered_count = 28
tampered_rejected_count = 28
tau_rejected_count = 21
hash_rejected_count = 7
```

## Certificate Mask

The v1 evidence mask is:

```text
bit 0: grammar_bounded
bit 1: fit_passed
bit 2: holdout_passed
bit 3: minimality_scoped
bit 4: proof_receipt
bit 5: symbolic_identity
bit 6: residual_certificate
bit 7: review_required
```

The required mask is `0x7F`. The promotion rule is:

```text
promote iff
  source_hash_is_current
  and (accepted_mask & 0x7F) = 0x7F
  and review_mask = 0
```

Standard reading: a row promotes exactly when it points to the current source
artifact, all required evidence bits are present, and no review bit is set.

Plain English: the formula is not accepted because it looks good. It is accepted
only when every declared evidence gate is present and Tau agrees on the finite
mask check.

## Local LLM Memory Smoke Demo

The default memory smoke demo is model-free. It uses a fixture proposal file so
every runner can reproduce the qNS and table-memory path:

```bash
./scripts/run_eml_qns_llm_memory_demo.sh --skip-setup-patch
```

To use an installed local model through `ollama`, opt in explicitly:

```bash
./scripts/run_eml_qns_llm_memory_demo.sh --skip-setup-patch --live-ollama --model llama3.2:3b
```

The live-Ollama path uses `num_gpu = 0` by default to avoid small-GPU memory
failures. A stronger local model can be selected with:

```bash
./scripts/run_eml_qns_llm_memory_demo.sh --skip-setup-patch --live-ollama --model bonsai-8b
```

if that model is installed in the local Ollama runtime.

For guided setup:

```bash
./scripts/setup_local_llm_proposer.sh --profile installed --run-smoke
```

To pull a small public fallback model explicitly:

```bash
./scripts/setup_local_llm_proposer.sh --profile compact --pull --run-smoke
```

The script never downloads a model unless `--pull` is supplied. The result is
written to:

```text
results/local/eml-qns-llm-memory-demo.json
results/local/eml-qns-llm-memory-demo.md
```

Current model-free receipt:

```text
candidate_count = 5
parse_ok_count = 3
promoted_count = 3
review_count = 2
memory_updated_count = 3
rejected_count = 2
rejected_preserved_count = 2
qns_table_regression_ok = true
symbolic_tau_table_check_ok = true
```

The receipt can be checked without rerunning Tau:

```bash
python3 scripts/verify_eml_qns_memory_receipt.py
```

The demo runner invokes that verifier automatically after each run. The
verifier also has a mutation self-test, so it checks that a deliberately broken
rejected-row memory update is caught.

The model-free path and live-model path share the same lane:

```text
fixture or local LLM proposal
  -> EML parser and checker
  -> Tau qns8 promotion check using examples/tau/eml_qns_evidence_memory_v1.tau
  -> named Tau qns8 table memory revision
  -> Tau table-syntax equivalence check using examples/tau/eml_symbolic_memory_table_v1.tau
```

Boundary: this is not proof by model output. It is evidence that a small local
model can produce proposal rows and that the qNS/Tau layer can accept or reject
those rows without trusting the model. The memory update itself is a named
Tau definition whose body uses direct `qns8` table syntax:

```text
memory_revise_qns8(old, guard, replacement) :=
  table { when guard => replacement; else => old }
```

The JSON artifact records the exact named call and the equivalent direct table
expression for every candidate. It also includes `qns8` table regressions for
top guard, bottom guard, and partial guard cases. Each regression checks both
the direct expression and the named Tau definition. The companion table check
proves that the symbolic memory revision shape agrees with the raw
guarded-choice expansion over Tau's `tau` carrier.

The optional live-model smoke test with `llama3.2:3b` currently reports:

```text
candidate_count = 5
parse_ok_count = 5
promoted_count = 3
review_count = 2
memory_updated_count = 3
rejected_count = 2
rejected_preserved_count = 2
qns_table_regression_ok = true
symbolic_tau_table_check_ok = true
```

## Depth Boundary

The checked public fixture is depth-3:

```text
depth_3_corpus_size = 1446
```

Depth-4 is possible, but it is not the default public run:

```text
depth_4_corpus_size = 2090918
```

Depth-4 can find formulas with deeper nested analytic structure. It can also
test whether a depth-3 winner remains stable when the search space expands, or
whether a more complex expression overfits noisy data.

The practical implementation boundary is evaluation cost. The depth-4 corpus is
more than one thousand times larger than the depth-3 corpus. A useful depth-4
lane should be streaming, pruned, or batched before it becomes a default public
demo.

The current non-default probe is:

```bash
python3 scripts/run_eml_depth4_probe.py \
  --limit 250000 \
  --out results/local/eml-depth4-probe.json
```

It scans a prefix of the depth-4 corpus and records where shallow known targets
are rediscovered. It is a scaling probe, not a proof that depth-4 search is
complete.

Current local receipt:

```text
scanned = 250000
eval_elapsed_s = 20.096624638012145
valid_evals = 441372
evals_per_second = 21962.49409789734
```

Known targets are rediscovered early in the prefix:

```text
x              first_fit_at = 1
exp(x)         first_fit_at = 4
ln(x)          first_fit_at = 48
exp(exp(x))    first_fit_at = 22
```

Interpretation: depth-4 is not blocked by mathematics, but the naive CPU path is
already expensive enough that the next serious lane should be batched,
streaming, and preferably GPU-shaped.

The parallel CPU probe is:

```bash
python3 scripts/run_eml_depth4_parallel_probe.py \
  --limit 250000 \
  --workers 4 \
  --out results/local/eml-depth4-parallel-probe.json
```

Current local receipt:

```text
scanned = 250000
elapsed_s = 5.5803029160015285
valid_evals = 440764
evals_per_second = 78985.67633956007
```

Interpretation: CPU multiprocessing already gives about a `3.6x` improvement
over the single-process prefix probe. In Python this should use worker
processes, not ordinary threads, because recursive Python evaluation is
CPU-bound and constrained by the GIL. A native C++ evaluator, NumPy batch
kernel, or GPU backend can use lower-level parallelism more directly.

## GPU Direction

The GPU-shaped version is:

```text
candidate trees x sample points -> score matrix
```

The CPU should generate and canonicalize EML tree shapes. The GPU should
evaluate candidate values and residuals in batches. Tau should keep doing the
small symbolic part: qNS evidence-mask gating and fail-closed certificate
checks.

This is not implemented in the public v1 demo. It is the next scaling lane.

The local GPU-readiness check found an NVIDIA GTX 1060 with 3 GB VRAM, but the
active Python environment does not currently have `torch`, `cupy`, `jax`, or
`numba` installed. The safe next implementation step is therefore a backend
abstraction with a NumPy CPU path first and an optional CuPy or PyTorch path
when a GPU stack is explicitly installed.

## Depth-5 Probe

Depth-5 is far larger than depth-4:

```text
exact_depth_5_count = 4371935991808
total_depth_5_count = 4371938082726
```

The non-default shard probe is:

```bash
python3 scripts/run_eml_depth5_probe.py \
  --limit 100000 \
  --depth4-seed-limit 1000 \
  --out results/local/eml-depth5-probe.json
```

Current local receipt:

```text
scanned = 100000
depth4_seed_count = 1000
lower3_count = 1446
eval_elapsed_s = 3.836631323036272
valid_evals = 70394
evals_per_second = 18347.866675990874
```

No known shallow target was exactly rediscovered in that shard. The best
`exp(exp(x))` shard error was about `0.02031416145632381`.

Interpretation: depth-5 is not a default brute-force search space. It needs
several controls at once:

- canonicalization to remove equivalent or redundant trees,
- pruning from domain and interval checks before numerical scoring,
- batched CPU or GPU scoring for the candidates that survive,
- qNS certificate gating after a candidate is selected.

## Hardware Tiers

The demo should eventually expose three execution tiers:

```text
standard laptop:
  depth-3 checked fixtures
  always run quickly

modern multi-core CPU:
  depth-4 process-parallel probe
  enabled only by an explicit deep flag

accelerated workstation:
  depth-4 or depth-5 batched search
  requires a GPU backend or large unified-memory machine
```

A MacBook-class machine with large unified memory can make depth-4 routine and
can make depth-5 shard experiments realistic. It still does not make exhaustive
depth-5 brute force the right default, because depth-5 has trillions of
candidates. The value of that hardware is that it can run larger batches, keep
more candidate state in memory, and run a neural proposer beside the symbolic
gate.

The intended accelerated workflow is:

```text
LLM or proposer suggests regions of the search space
  -> canonicalizer removes duplicate shapes
  -> interval/domain pruner rejects impossible candidates
  -> GPU batch evaluator scores survivors
  -> qNS/Tau gate checks evidence masks
  -> proof/residual certificate decides promotion
```

This is the practical reason higher depth matters. Depth-4 and depth-5 are not
only bigger brute-force spaces. They are where the neuro-symbolic loop becomes
useful: the model proposes where to search, while the symbolic system decides
what survives.

## What This Does Not Claim

- It is not full symbolic regression.
- It is not neural proposal generation.
- It is not native Tau analytic EML semantics.
- It is not cryptographic attestation.
- Source hashes are local artifact-integrity checks, not protection against a
  compromised generator or verifier.
