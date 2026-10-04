# Separate executable validation

These original validation scripts test semantics, typed parsing, scoped congruence, retained native receipt binding and cost accounting separately from the study runner. They are bounded executable audits, not peer review or proof of the Python/Tau implementation.

The final evidence replays passed:

- Heldout:336 cases, 3,360 arm-output gates, 3,030 changed-output checks, 3,875 accepted pairs; current-source and frozen-profile checks passed.
- Online reuse:30 runs, 7,680 arm requests, 8,892 native processes; fixed selections, context/certificate identity and measured accounting replayed.
- Resources:324 support rows and 216 search rows match on deterministic fields. Those graph outputs are not native-final-gated optimizer results.
- Lean: the support theorem and bounded Python/Lean correspondence replayed independently; exact set-model and implementation-gap limitations remain.
- Evidence mutation suite: all 19 local packet mutations were rejected while the unmodified control passed. Raw clocks and retained process logs remain trusted execution records, not attestations against coherent wholesale fabrication.

From this study directory, after extracting the evidence archives:

    python3 audit/audit_math_harness.py --source src --out /tmp/tau-math-audit.json
    python3 audit/audit_packet_mutations.py --source src --run results/final-prefreeze-smoke-004 --out /tmp/tau-packet-mutations

Use fresh output paths. The packet mutation command launches no native process and deliberately mutates only newly created local copies. Its historical-source mode checks the chosen saved fixture with the current validator; use src/validate_run.py without that exception for the final heldout current-source replay.

Native boundary/repeatability scripts require an explicitly supplied official Tau executable. No binary is included here. Other scripts expose their required paths through ordinary argparse usage.

The two discarded recursive-comparator implementations were development defects: one selected a raw class member before folding every alternative; one omitted congruence below binders. Regression witnesses are preserved by recursive_baseline_regression.py and the matched congruence audit. No result from those weaker comparators is credited to the final method.
