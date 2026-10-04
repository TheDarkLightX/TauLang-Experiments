# Online fixed-bank reuse protocol

Status: implementation prepared before execution. The immutable freeze file and
its SHA256 are the execution authority; this document alone does not authorize a
benchmark. This experiment is separate from optimization-quality holdouts.

## Question and attribution boundary

Does a semantic-registry candidate cache reduce cumulative online cost beyond
ordinary exact-syntax/exact-pair memoization when every new emitted pair still
requires the native Tau checker in both directions?

A fourth, strong fixed-bank-signature control isolates the obvious amortization
of computing bank signatures once. Any improvement over pairwise support scans
may be loop hoisting, batching, or indexing. It is not automatically evidence for
semantic-class reuse. With the fixed menu used here, the additional semantic
class-decision memo is mathematically redundant with the signature-indexed bank.
The experiment may therefore yield no additional native savings and no useful
break-even advantage. These are valid findings, not failures to be suppressed.

## Exact request and response semantics

A request consists of an immutable AST and full explicit context: ordered
variable declarations and descriptors, ordered free-variable interface V, theory,
constants, and temporal profile. Primary contexts use V=(a,b,c), descriptor tau,
nontrivial atomless Boolean algebra, constants 0/1, and no temporal operators.
Every mixture source syntactically mentions all three free variables. Pure terms
and quantifier-free formulas are separate streams. No claims extend to arbitrary
Tau syntax, temporal recurrence, non-0/1 constants, or unbounded formulas.

For source x and its context, take checked_registry.candidate_bank's fixed,
objective-sorted grammar. Among its complete-support-equivalent members and x,
choose the least (typed UTF-8 expression bytes, AST nodes, repr) objective. The
original provides the nonregressing fallback. All arms have exactly this same
menu; none inserts a previously observed source into the bank. No optimized
answer is supplied in the request.

The proposed output must independently parse back from actual typed emitted
text and pass the support/native check_emission gate. The native gate sends both
universally closed implications of the actual emitted source and target. Terms
use their XOR-zero formula versus T. Accepted exact certificates may serve later
identical ordered emitted pairs in the identical context and checker profile.
The selected pair for every new syntax is checked afresh. No transitive native
certificate, alpha-renaming certificate, or semantic-key certificate is assumed.
Identical source and target still receive two native calls on a cold final gate
and are labeled ACCEPTED_IDENTITY. An inconclusive gate retains the original and
is recorded UNKNOWN; it is never an equivalence certificate.

## Arms, starting from empty state

1. no_cache: reconstruct the grammar bank each request, perform ordered complete
   pairwise support comparisons until the first cheaper equivalent member,
   then run a fresh final gate. No request, pair, signature, or final certificate
   survives for reuse.
2. exact_syntax: construct each context/sort bank once; memoize complete exact
   pair support outcomes and complete exact-query selections. Cache only
   accepted final native certificates. Repeated queries still validate their
   input, parse emitted source and target, and check the exact certificate key.
   This is a strong ordinary syntax/result-memoization baseline.
3. fixed_bank_signature: the same exact-query and exact-final-certificate
   behavior, plus each fixed bank AST's signature once and each novel exact
   query AST's signature once. An index maps full signatures to the cheapest
   fixed-bank member. This control has no cross-query class-decision memo.
4. semantic_registry: the same indexed bank and exact caches as arm 3, plus a
   profile/context/sort/signature decision memo. It stores the cheapest bank
   member, or no-bank-match, BEFORE applying the current query's original guard.
   It never stores a prior original as an extra candidate. This extra memo is
   redundant with arm 3's indexed lookup and has no authority to reuse a native
   certificate across changed syntax.

Signatures are complete finite-support formula evaluations or pure-term Boolean
corner vectors, never Boolean-corner interpretations of formulas. UNKNOWN or
incomplete signatures, support comparisons, or native certificates are not
cached as conclusive results. A complete support-only selection may be cached
even when its later native gate is unknown; the native gate is still retried.

Every reusable key includes the checker profile and full context key; signature
class decisions also include the AST sort. The checker profile binds the native
binary digest, command flags, timeout, support budgets, and checker/renderer/
parser/runner source digests. Exact signature memo keys additionally include the
sort and AST. Frozen source manifests are verified before and after execution.

## Fixed stream matrix

The source-only generator namespace is tau-online-reuse-2026-10-04-v1. It never
calls a correctness oracle, native binary, or optimizer. Exact request bytes and
per-stream canonical-JSON SHA256 values are saved by --freeze-out before any
campaign execution. There are ten streams, each of 64 requests:

| Stream kind | Exact | New equivalent syntax | Fresh syntax | Sorts |
| --- | ---: | ---: | ---: | --- |
| 100/0/0 | 64 | 0 | 0 | term and formula separately |
| 50/50/0 | 32 | 32 | 0 | term and formula separately |
| 25/25/50 | 16 | 16 | 32 | term and formula separately |
| 0/0/100 | 0 | 0 | 64 | term and formula separately |
| Context safety | eight repetitions of each of eight context cases | | | term and formula separately |

"Exact" denotes the one repeated source family, including its compulsory first
cold seed; the 100% label does not imply a hit on request 1. Mixtures containing
exact requests place this seed first, then deterministically shuffle remaining
category labels. The cold miss is reported and charged, not hidden as a warmup.
Equivalent variants use an injective seven-wrapper neutral-law construction and
are syntactically distinct. The complete exact request sequences are frozen.

"Fresh" means previously unseen syntax, not necessarily a new semantic class.
The random source-only generator uses tree budgets 15, 23, and 31, keeps all three
free variables, and rejects exact AST duplicates. Post-freeze, before timing,
independent support signatures verify equivalent labels and count actual
context-qualified semantic novelty and exact syntax repetition. This validation
is recorded as separate experiment overhead; its data never enters arm caches.
No semantic-novelty rejection sampling, selective rerun, or label-based answer
selection is performed.

The separate context stream cycles through: base abc; the same AST with reversed
V; reversed declaration order with original V; consistently alpha-renamed def;
unsupported theory; unsupported constants; unsupported temporal profile; and
unsupported descriptor. The four supported contexts receive independent cold
certification and may only reuse their own exact certificates thereafter. The
four unsupported contexts must reject before proposal work or native calls.
No automatic alignment is implemented. Profile mutation isolation is tested at
unit level. These safety cases are reported separately from the mixture curves.

## Frozen execution and timing

The primary native executable is external to the repository. Its required
SHA256 is 874511bf414d0bfbaca224d6fde1cc2514419ad15c912d24dd334f6792909726.
The path is supplied to --binary; the runner and output do not copy the binary
or Tau source into the repository. The timeout is 5 seconds per native direction.
There are exactly three full repetitions, each with new empty arm state for each
stream. There are no excluded warmups. Request position determines a four-arm
rotation, offset by repetition and stream index; each arm occupies each order
position sixteen times per stream. All three repetitions remain visible.

Cumulative per-arm wall time begins with initialization (including checker and
binary identity preparation), then every request through response construction.
Cold grammar construction, all bank/query signatures, pairwise support work,
cache lookups, typed emission/roundtrip parsing, native process startup and wait,
native receipt persistence, final certification, and warm-query overhead are
charged. Native process counts and durations come from actual newly appended
receipts, never by recursively counting cached receipt references.

Component times are nested, not additive totals. final_gate_s includes its own
support check, parsing, native subprocess work, and cache lookups; native wall
is a subset. final_gate_non_native_s is only the residual, not an isolated support
measurement. Final support calls and observation counts are recorded separately
from proposal/signature support work to prevent invisible validation costs.
Per-request operations retain support details, signatures' hashes, bank hashes,
and exact native commands/stdout/stderr/exit codes/timeouts. Raw receipt files
are hashed and linked from compact run indexes.

Raw proposal-support dataclasses are expanded into JSON only after the request
clock stops, so repeated full-observation copying is not charged to one arm
as though it were selection work. Gate receipt construction remains part of
the shared final-gate implementation.

Outer orchestration/JSON serialization and post-freeze stream validation are
outside the per-arm clock and disclosed separately; the total campaign wall
clock is also retained. The validation does not constitute free bank building
or supply any answer to an arm. Runs are process-inclusive observations on this
machine, not independent statistical samples or a production workload estimate.

The summary retains every per-request cumulative curve and each repetition's
component totals, native process counts, cache hits, statuses, output-byte sums,
and output/status mismatches. Pairwise semantic-versus-baseline differences
include first observed advantage and first point remaining faster through request
64. A missing point is explicitly no observed sustained break-even within this
64-request window; no long-run extrapolation is made. A small noisy lookup-time
advantage over the identical signature-bank menu is not a new semantic algorithm.

An actual DIFFERENT verdict from a support/native gate, candidate disagreement across matched
menus, or context leakage stops the campaign and preserves FAILED.json plus raw
receipts. A disagreement involving incomplete support selection is labeled
inconclusive selection rather than contradiction. Support UNKNOWN/REJECTED is
never classified as semantic contradiction. Native UNKNOWN is retained and retried where appropriate; no timeout
or slow repetition is discarded. Sources/binary changing invalidate the run.

## Commands and evidence levels

Prepare a freeze only after code review and test completion:

    PYTHONPATH=src python src/run_reuse.py --freeze-out corpora/reuse-frozen-v1.json

This writes no benchmark result. Record the returned SHA256, obtain the study
owner's execution authorization, then use that exact hash:

    PYTHONPATH=src python src/run_reuse.py \
      --freeze corpora/reuse-frozen-v1.json \
      --expect-freeze-sha256 EXACT_RETURNED_SHA256 \
      --binary /absolute/path/to/pinned/tau \
      --out results/reuse-run-v1

The destination must not already exist. Freeze files cannot be overwritten.
The CLI has no mocked-native mode. Unit tests use visibly labeled mock native
receipts to establish cache/control-flow contracts and independent support
fixtures to test neutral identities. Neither is reported as native evidence.
Unit coverage includes both final directions, identity gates, new equivalent
syntax, exact hits, forced native/support UNKNOWN, changed V/declarations,
alpha-renaming, profile mutation, invalid contexts, and the before-guard decision
cache requirement. Any later code change requires a new freeze and separately
identified execution; never rewrite an earlier run as if it used the new code.

Offline receipt verification uses the same explicit freeze identity:

    PYTHONPATH=src python src/run_reuse.py \
      --verify-out results/reuse-run-v1 \
      --expect-freeze-sha256 EXACT_RETURNED_SHA256

The verifier binds each forward and reverse receipt independently to the actual
emitted pair, universal variable order, argv flags/command, primary binary digest,
timeout, sanitized environment marker, strict exit/stdout/stderr classification,
and persisted ordinal file. It checks exact cached-certificate provenance across
requests, fresh-process accounting, raw request hashes, profiles, complete
request schedules, start/end source identities, and independently recomputed fixed-bank selections and cumulative
summaries. Every profile field and budget must match the frozen checker profile.
Timing checks require finite nonnegative clocks, zero fresh native cost on warm
hits, gate/record clock equality, recomputed residuals, and request ≥ nonoverlapping
selection components + gate ≥ fresh native cost. Positive native receipt durations
therefore prevent a consistently zeroed request/summary from passing verification. Unit mutation tests reject changed reverse commands, changed forward
or reverse argv, altered verdict output, double charging, and cross-profile
certificate reuse, timing zeroing, non-finite clocks, and fabricated warm native
cost. These mutation fixtures are explicitly mocked evidence.
Optimized Python is rejected as outside the frozen execution profile.
