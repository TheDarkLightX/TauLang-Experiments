# Tables and figures for the completed study

This is a display specification, not an additional analysis endpoint or a result. Do not fill a cell from partial runs. Use `pending` for unavailable evidence, never a numeric zero or an empty field that could be read as zero. Preserve the frozen six comparisons, intervals, and denominators. Any additional analysis must be explicitly labeled exploratory and must not alter frozen study files.

## Input and validation rules

- Quality inputs: the completed run's `SUMMARY.json`, all `*/result.json`, `manifest-start.json`, `corpus-executed.json`, and the completed output of `analyze_results.py`. The analysis invokes the validator; preserve the separate validation receipt too.
- Reuse inputs: completed `summary.json`, immutable request streams and their hash, all compact run indexes and linked raw receipts, post-freeze stream validation, and the offline verifier's output. Do not silently import quality-run timing into this lane.
- Resource inputs: `support-results.json`, `search-results.json`, their matrix, `SUMMARY.json`, and the development receipt identities used by the search screen. This screen makes no new native certification claim.
- Proof inputs: versioned `Proofs.lean`, deterministic `Bridge.lean`, fixtures, manifest, and proof/correspondence receipts. Cite the exact theorem boundary separately from tested correspondence.
- Preserve full precision in machine-readable derived data. Round only display text. Compute any displayed percentage directly from raw integer totals and state its denominator.
- Bind completed derived tables to source-file digests and the exact released artifact revision. Figures must be reproducible from those tables. A figure caption is not evidence of validation.

## Table 1 Evidence boundaries

Rows: Lean set-algebra exactness; bounded Python/Lean correspondence; parser correspondence; changed final output gates; common-transcript quality; online reuse; resource screens.

Columns: scope, decisive observation, completed evidence location, and excluded claim. The theorem row states every nonempty atomless set subalgebra, all well-scoped formulas and assignments. The correspondence row reports 1,073 fixtures, 11,979 observations, and 19/273 refinement cases/children, without calling them holdout results. Completed empirical rows use the validated quality, resource, and online reuse records. Native receipts and clocks are trusted records, not attestations.

## Table 2 Corpus and execution coverage

Rows: each of the eight generated structural families, followed by seen-template subtotal, held-out-template subtotal, and all cases. Include test count, nominal budget range, declared and actually used free-variable distributions, binder-pattern distribution where relevant, successful result count, and cap/failure count.

Quality fields: `families`, `scope_and_caps.declared_variable_counts`, `scope_and_caps.used_free_variable_counts`, and `quantifier_pattern_counts`; family-specific detail can be recomputed from the unchanged completed rows. The designed total is 336, but successful/complete counts are measurements. Show 84/84 training/development separately. Do not fold the selected historical 24-case pilot into the test denominator.

## Table 3 Primary emitted-size comparison

Ten method rows in the protocol order. Columns:

1. Number of case outcomes and changed/retained-identity counts.
2. Sum of typed emitted expression bytes (`arms.<name>.expression_bytes`).
3. Expanded AST nodes and structural DAG nodes, separately.
4. Final gate statuses and fallbacks.
5. Hybrid wins/ties/regressions against this method, with the direction clearly labeled.

Below the aggregate table, show the six prespecified paired comparisons with mean difference, median difference, and the 95% family-stratified bootstrap interval for the **mean**. Negative means the first named arm is smaller. Use `intervals` from frozen analysis without substituting a median interval or rerunning until favorable.

Keep native unguarded output, native guarded output, and the native/SymPy portfolio distinct. Show native raw bytes in a separate diagnostic, not in the common-output column. Identify typed expression versus complete file bytes. Report alternative untyped display costs as sensitivity only.

## Table 4 Mechanism and cap audit

Rows: recursive congruence; no-rewrite semantic graph; full hybrid; root-only hybrid. Columns: outputs absent from explicit root menu, strict byte wins over root menu, checked pairs consumed, represented structure count if available, stop reasons, and final-gate status.

`composition` supplies the first two values for the available arms. `representation_byte_disagreements` supplies the complete disagreement list. For each disagreement, show both bytes, graph node count/stop reason, and whether the 1,000-enode cap affected the graph. The explicit recursive table is uncapped. Do not infer equality of the unbounded algorithms from matching finite observations. Do not infer data-structure superiority from cap-induced gaps. Extra hybrid rules are a candidate-generation difference.

If all representation bytes match, keep the table and report that result. If no composition improves over the explicit roots, do not replace it with a more favorable metric.

## Table 5 Fail-closed and evidence audit

Report denominators separately for normalization proposals, registry proposals, extracted changed candidates, final retained outputs, and distinct native invocations. Include every observed accepted, rejected, different, unknown, timeout, error, and structural-identity status. A retained output after an unknown is safe fallback evidence, not successful candidate certification.

Link known prefreeze controls and the final validator's outcomes for: direction-swapped receipt; wrong context or ordered interface; malformed emission; one-way implication; incomplete support; wrong source/profile; timing mutation in online receipts; and cross-context reuse. Distinguish executed mutation tests, mocked unit receipts, native process evidence, and formal lemmas. A mock-native mutation is not a native benchmark measurement.

## Table 6 Online reuse results

One row per stream, repetition, and arm (ten streams × three repetitions × four arms). Full rows belong in a supplementary machine-readable table; use small multiples for the paper.

Columns map to each run's `arms` object: `startup_s`, `total_wall_s`, `request_wall_s`, `native_processes`, `native_wall_s`, `final_gate_s`, `final_support_calls`, `final_support_observations`, `final_gate_non_native_s`, `exact_query_hits`, `final_certificate_hits`, `candidate_changes`, `output_bytes`, `gate_statuses`, and `work` counters. Do not sum nested clocks.

For each semantic-registry comparison, report `total_wall_difference_s`, `native_process_difference`, `first_observed_advantage_request`, `sustained_advantage_through_64_request`, and `output_or_status_mismatch_indices`. Missing break-even is displayed as “none observed through 64,” not infinity, zero, or a extrapolated future request. Preserve every repetition.

Report actual syntactic and context-qualified semantic novelty from stream validation; planned mixture labels do not supply measured novelty. Context safety is separate from favorable timing mixtures. Unsupported contexts should not be counted as successful optimizations.

## Table 7 Resource limits

Support panel: all 324 rows, grouped by free variables, support cap, state cap, family, and quantifier depth. Report status, reason, completion, elapsed time, states/node evaluations from `stats`, and observation counts. Separate initial cap rejection from exhausted traversal budgets.

Search panel: all 216 rows, grouped by the fixed 24 development cases and nine budget pairs. Report extracted bytes, enodes, classes, iterations, stop reason, and component times. Label every size as unvalidated search-screen extraction: no new native final gates ran in this screen. Do not combine this panel with the accepted primary endpoint.

## Figure 1 Semantic and check boundaries

A static schematic can have three aligned rows: mathematical support exactness; tested Python/parser correspondence; actual-output admission. Label proven arrows versus tested arrows in text and shape, not color alone. Show the native descriptor-to-theory relationship as an assumption. Do not draw an uninterrupted “verified compiler” arrow.

Optional inset: one occupied parent cell with outside-only, inside-only, and both-child refinements. Explicitly mark the both-child case as requiring atomless splitting. This is original explanatory artwork, not reproduced source material.

## Figure 2 Paired quality differences

Use family-faceted paired difference distributions for hybrid versus native/SymPy portfolio and hybrid versus recursive congruence. Show all cases including zero differences and cap/fallback cases. Use the same sign convention and byte scale where feasible. Overlay a zero reference line, label sample counts, and do not use log scaling that hides zeros or negative values. Do not turn bootstrap intervals into significance badges.

## Figure 3 Representation parity and cap differences

Plot semantic-graph bytes against recursive-congruence bytes, with the identity line. Distinguish cap-tagged points by shape. Annotate the number of coincident points when overlap would conceal sample size. Any apparent gain must be accompanied by the corresponding complete disagreement audit. If every point lies on the line, that is the figure's result.

## Figure 4 Cumulative online cost

Eight mixture panels (four mixtures × two sorts) with request index 1–64 on the horizontal axis and cumulative charged wall seconds on the vertical axis. Use a consistent color and dash combination for each arm. Preserve all three repetitions as thin lines; an optional bold summary must not hide them or imply independent samples. Include initialization in every curve. Plot native-process count curves in a companion panel so ordinary exact hits are distinguishable from selection overhead.

State in the caption that equivalent new syntax needs fresh native certification, fixed-bank signature lookup already determines the menu optimum, and the domain is synthetic. Context streams appear in a separate safety display. If noisy lines cross repeatedly, report that visibly rather than picking a favorable endpoint or run.

## Figure 5 Support-resource boundary

A discrete grid or small-multiple panel can show completion/unknown/rejection across n, state cap, and quantifier depth. Include family labels to expose short-circuit behavior. Show the theoretical support counts in the caption separately from measured work. Never imply a timed n = 5 full enumeration occurred when the initial-support cap rejected it.

## Display quality gate

Use color-safe palettes, readable axis labels, direct unit names, complete captions, and no invented confidence bars. Export vector figures when practical and inspect the final rendered PDF at actual page size. Validate every displayed number against the completed derived table. The manuscript remains draft until result-bearing figures and all pages pass content and visual review.
