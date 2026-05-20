"""Grammar-versioned synthetic Tau data helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .core import TauProposalCandidate, default_energy_model
from .jepa import default_jepa_model


GRAMMAR_GLOBS: tuple[str, ...] = (
    "external/tau-lang/parser/*.tgf",
    "external/tau-lang/src/**/*.l",
    "external/tau-lang/src/**/*.y",
    "external/tau-lang-latest/parser/*.tgf",
)


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def build_tau_syntax_snapshot(root: Path | str = ".") -> dict[str, Any]:
    repo = Path(root)
    files: list[Path] = []
    for pattern in GRAMMAR_GLOBS:
        files.extend(sorted(path for path in repo.glob(pattern) if path.is_file()))
    digest = hashlib.sha256()
    for path in files:
        digest.update(_rel(path, repo).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return {
        "schema": "tau-syntax-snapshot-v1",
        "grammar_hash": digest.hexdigest() if files else "missing",
        "grammar_files": [_rel(path, repo) for path in files],
        "grammar_file_count": len(files),
        "drift_policy": "invalidate generated syntax rows when grammar_hash changes",
    }


def surface_tau_syntax_check(text: str) -> dict[str, Any]:
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack: list[str] = []
    for char in text:
        if char in pairs:
            stack.append(pairs[char])
        elif char in pairs.values():
            if not stack or stack.pop() != char:
                return {"ok": False, "reason": "unbalanced delimiters"}
    if stack:
        return {"ok": False, "reason": "unclosed delimiters"}
    local_home_marker = "/" + "home" + "/"
    local_user_marker = "trevor" + "moc"
    if local_home_marker in text or local_user_marker in text.lower():
        return {"ok": False, "reason": "local path leak"}
    if "out " not in text and "query" not in text.lower() and "claim" not in text.lower():
        return {"ok": False, "reason": "no observable Tau-facing claim"}
    return {"ok": True, "reason": "surface check only; run current Tau for authority"}


def semantic_templates() -> list[dict[str, Any]]:
    return [
        {
            "template_id": "one_hot_policy_gate",
            "intent": "A host computes action flags and Tau checks the allowed boolean shape.",
            "tau_text": "claim allow_trade := action_trade && has_receipt && !emergency_pause",
            "semantic_ir": {
                "inputs": ["action_trade", "has_receipt", "emergency_pause"],
                "guarantee": "allow_trade only when action_trade and has_receipt are true and emergency_pause is false",
            },
            "counterexamples": [
                {"action_trade": True, "has_receipt": False, "emergency_pause": False, "allow_trade": False},
                {"action_trade": True, "has_receipt": True, "emergency_pause": True, "allow_trade": False},
            ],
        },
        {
            "template_id": "grammar_drift_gate",
            "intent": "A generated Tau sketch must be tied to a grammar snapshot.",
            "tau_text": "claim sketch_current := grammar_hash_matches && syntax_probe_passed",
            "semantic_ir": {
                "inputs": ["grammar_hash_matches", "syntax_probe_passed"],
                "guarantee": "stale syntax rows are not promoted to current sketches",
            },
            "counterexamples": [
                {"grammar_hash_matches": False, "syntax_probe_passed": True, "sketch_current": False},
                {"grammar_hash_matches": True, "syntax_probe_passed": False, "sketch_current": False},
            ],
        },
        {
            "template_id": "tau_net_experiment_rollout",
            "intent": "A Tau Net proposal stays in an experiment lane until receipts exist.",
            "tau_text": "claim rollout_allowed := experiment_lane && receipt_bundle_passed && rollback_defined",
            "semantic_ir": {
                "inputs": ["experiment_lane", "receipt_bundle_passed", "rollback_defined"],
                "guarantee": "broad rollout needs experiment scope, receipts, and rollback",
            },
            "counterexamples": [
                {"experiment_lane": False, "receipt_bundle_passed": True, "rollback_defined": True, "rollout_allowed": False},
                {"experiment_lane": True, "receipt_bundle_passed": False, "rollback_defined": True, "rollout_allowed": False},
            ],
        },
    ]


def build_syntax_corpus(root: Path | str = ".", *, limit: int | None = None) -> dict[str, Any]:
    snapshot = build_tau_syntax_snapshot(root)
    rows: list[dict[str, Any]] = []
    model = default_energy_model()
    jepa = default_jepa_model()
    for template in semantic_templates()[:limit]:
        syntax_check = surface_tau_syntax_check(str(template["tau_text"]))
        candidate = TauProposalCandidate(
            candidate_id=f"syntax:{template['template_id']}",
            kind="tau_syntax_example",
            title=str(template["template_id"]),
            text=str(template["tau_text"]),
            features={
                "semantic_specificity": 0.9,
                "verifier_receipts": 0.2,
                "replay_cases": 0.6,
                "witness_schema_fields": 0.7,
                "syntax_snapshot_match": 0.8 if snapshot["grammar_hash"] != "missing" else 0.2,
                "grammar_drift_risk": 0.2 if snapshot["grammar_hash"] != "missing" else 0.65,
                "host_projection": 0.8,
                "counterexample_coverage": 0.7,
                "authority_overclaim": 0.0,
                "tau_net_blast_radius": 0.2 if template["template_id"] != "tau_net_experiment_rollout" else 0.6,
                "governance_scope": 0.2,
                "training_traceability": 0.9,
            },
            evidence=("synthetic semantic template", "surface syntax check"),
        )
        rows.append({
            "schema": "tau-syntax-training-row-v1",
            "template_id": template["template_id"],
            "grammar_hash": snapshot["grammar_hash"],
            "tau_text": template["tau_text"],
            "semantic_ir": template["semantic_ir"],
            "counterexamples": template["counterexamples"],
            "surface_syntax_check": syntax_check,
            "energy": model.energy(candidate),
            "jepa_top_scenario": jepa.rank([candidate])[0],
            "authority": "training data only; current Tau must parse and verify before use",
        })
    return {
        "schema": "tau-syntax-corpus-v1",
        "snapshot": snapshot,
        "row_count": len(rows),
        "rows": rows,
        "jsonl": "\n".join(json.dumps(row, sort_keys=True) for row in rows),
    }
