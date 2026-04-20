#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TAU_BIN = ROOT / "external" / "tau-lang" / "build-Release" / "tau"
DEFAULT_OUT = ROOT / "results" / "local" / "eml-qns-llm-memory-demo.json"
DEFAULT_PROPOSALS = ROOT / "examples" / "eml-qns" / "llm_candidate_proposals_v1.json"
DEFAULT_TAU_SOURCE = ROOT / "examples" / "tau" / "eml_qns_evidence_memory_v1.tau"
DEFAULT_TABLE_SOURCE = ROOT / "examples" / "tau" / "eml_symbolic_memory_table_v1.tau"
DEFAULT_REPORT_OUT = ROOT / "results" / "local" / "eml-qns-llm-memory-demo.md"

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
QNS_VALUE_RE = re.compile(r"^%\d+:\s*\{\s*(\d+)\s*\}:qns(?:8|64)\s*$")
PLAIN_VALUE_RE = re.compile(r"^%\d+:\s*(\d+)\s*$")

TOP = 0xFF
QNS_MEMORY_REVISION_DEFINITION = "memory_revise_qns8(old, guard, replacement)"
EVIDENCE_BITS = {
    "proposed": 0,
    "parse_ok": 1,
    "domain_ok": 2,
    "train_fit": 3,
    "holdout_fit": 4,
    "memory_update_ready": 5,
    "unused": 6,
    "review_required": 7,
}
REQUIRED_MASK = (
    (1 << EVIDENCE_BITS["proposed"])
    | (1 << EVIDENCE_BITS["parse_ok"])
    | (1 << EVIDENCE_BITS["domain_ok"])
    | (1 << EVIDENCE_BITS["train_fit"])
    | (1 << EVIDENCE_BITS["holdout_fit"])
    | (1 << EVIDENCE_BITS["memory_update_ready"])
)


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class Tree:
    kind: str
    left: "Tree | None" = None
    right: "Tree | None" = None

    def pretty(self) -> str:
        if self.kind == "x":
            return "x"
        if self.kind == "one":
            return "1"
        if self.left is None or self.right is None:
            raise ValueError("malformed EML node")
        return f"eml({self.left.pretty()},{self.right.pretty()})"

    def eval(self, x: float) -> float:
        if self.kind == "x":
            return x
        if self.kind == "one":
            return 1.0
        if self.left is None or self.right is None:
            raise ValueError("malformed EML node")
        left = self.left.eval(x)
        right = self.right.eval(x)
        if right <= 0:
            raise ValueError("real log domain failure")
        if abs(left) > 80:
            raise ValueError("exp guard failure")
        out = math.exp(left) - math.log(right)
        if not math.isfinite(out):
            raise ValueError("non-finite output")
        return out


X = Tree("x")
ONE = Tree("one")


class TreeParser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.i = 0

    def skip_ws(self) -> None:
        while self.i < len(self.text) and self.text[self.i].isspace():
            self.i += 1

    def eat(self, token: str) -> bool:
        self.skip_ws()
        if self.text.startswith(token, self.i):
            self.i += len(token)
            return True
        return False

    def expect(self, token: str) -> None:
        if not self.eat(token):
            raise ParseError(f"expected {token!r} at offset {self.i}")

    def parse_tree(self) -> Tree:
        self.skip_ws()
        if self.eat("x"):
            return X
        if self.eat("1"):
            return ONE
        if self.eat("eml"):
            self.expect("(")
            left = self.parse_tree()
            self.expect(",")
            right = self.parse_tree()
            self.expect(")")
            return Tree("eml", left, right)
        raise ParseError(f"expected x, 1, or eml(...) at offset {self.i}")

    def parse(self) -> Tree:
        tree = self.parse_tree()
        self.skip_ws()
        if self.i != len(self.text):
            raise ParseError(f"unexpected trailing text at offset {self.i}")
        return tree


def parse_tree_expr(text: str) -> Tree:
    return TreeParser(text).parse()


def target_fn(name: str) -> Callable[[float], float] | None:
    if name == "exp(x)":
        return math.exp
    if name in {"ln(x)", "log(x)"}:
        return math.log
    if name == "exp(exp(x))":
        return lambda x: math.exp(math.exp(x))
    return None


def build_prompt(candidate_count: int) -> str:
    return f"""Return one JSON object only. No Markdown.

Allowed grammar only:
T ::= x | 1 | eml(T,T)

Never write exp(...), log(...), ln(...), 0, +, -, *, or / inside expr.

Meaning examples:
- exp(x) is eml(x,1)
- exp(exp(x)) is eml(eml(x,1),1)
- a candidate for ln(x) in this demo is eml(1,eml(eml(1,x),1))

Return exactly this schema with a single candidates key:
{{
  "schema": "eml_candidate_proposals_v1",
  "candidates": [
    {{
      "target": "exp(x)",
      "origin": "local_llm",
      "expr": "eml(x,1)",
      "note": "brief reason"
    }}
  ]
}}

Propose at most {candidate_count} candidates for targets exp(x), ln(x), and exp(exp(x)).
"""


def extract_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object found in model output")
    return json.loads(text[start : end + 1])


def call_ollama(
    model: str,
    prompt: str,
    *,
    url: str,
    timeout_s: float,
    num_gpu: int,
    num_predict: int,
    temperature: float,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
            "num_gpu": num_gpu,
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        data = json.loads(response.read().decode("utf-8"))
    return {
        "raw_response": data.get("response", ""),
        "model": data.get("model", model),
        "total_duration_ns": data.get("total_duration"),
        "load_duration_ns": data.get("load_duration"),
        "prompt_eval_count": data.get("prompt_eval_count"),
        "eval_count": data.get("eval_count"),
        "temperature": temperature,
        "num_predict": num_predict,
        "num_gpu": num_gpu,
    }


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def qns_const(mask: int) -> str:
    return f"{{ #x{mask & TOP:02X} }}:qns8"


def report_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return path.name


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(data: Any) -> str:
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def qns_table_expr(guard: int, replacement: int, old: int) -> str:
    return (
        "table { "
        f"when {qns_const(guard)} => {qns_const(replacement)}; "
        f"else => {qns_const(old)} "
        "}"
    )


def qns_table_call_expr(old: int, guard: int, replacement: int) -> str:
    return f"memory_revise_qns8({qns_const(old)}, {qns_const(guard)}, {qns_const(replacement)})"


def expected_qns_table_revision(guard: int, replacement: int, old: int) -> int:
    return ((guard & replacement) | ((TOP ^ guard) & old)) & TOP


def tau_source(path: Path) -> str:
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("#"):
            lines.append(line)
    return "\n".join(lines)


def clean_lines(text: str) -> list[str]:
    return [strip_ansi(line).strip() for line in text.splitlines() if strip_ansi(line).strip()]


def run_tau_qns(tau_bin: Path, expr: str, *, timeout_s: float, source: str) -> tuple[int, str]:
    env = dict(os.environ)
    env["TAU_ENABLE_QNS_BA"] = "1"
    env["TAU_ENABLE_SAFE_TABLES"] = "1"
    program = f"{source}\nn {expr}"
    proc = subprocess.run(
        [str(tau_bin), "--severity", "error", "--charvar", "false", "-e", program],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_s,
        env=env,
        cwd=str(ROOT),
    )
    text = strip_ansi((proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else ""))
    if proc.returncode != 0:
        raise RuntimeError(text.strip() or f"Tau failed with rc={proc.returncode}")
    for line in reversed([part.strip() for part in text.splitlines() if part.strip()]):
        match = QNS_VALUE_RE.match(line) or PLAIN_VALUE_RE.match(line)
        if match is not None:
            return int(match.group(1)), text.strip()
    raise RuntimeError(f"could not parse Tau qns output: {text.strip()!r}")


def run_tau_table_check(tau_bin: Path, table_source: Path, *, timeout_s: float) -> dict[str, Any]:
    source = tau_source(table_source)
    query = (
        f"{source}\n"
        "solve --tau (eml_memory_update_table(old,guard,replacement) != "
        "eml_memory_update_raw(old,guard,replacement))"
    )
    env = dict(os.environ)
    env["TAU_ENABLE_SAFE_TABLES"] = "1"
    proc = subprocess.run(
        [str(tau_bin), "--charvar", "false", "-e", query, "--severity", "info", "--color", "false", "--status", "true"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout_s,
        env=env,
        cwd=str(ROOT),
    )
    lines = clean_lines(proc.stdout)
    last_line = lines[-1] if lines else ""
    return {
        "source": str(table_source.relative_to(ROOT)),
        "ok": proc.returncode == 0 and last_line == "no solution",
        "returncode": proc.returncode,
        "last_line": last_line,
    }


def run_qns_table_regressions(tau_bin: Path, *, timeout_s: float, source: str) -> dict[str, Any]:
    cases = [
        {
            "name": "top_guard_replaces",
            "guard": TOP,
            "replacement": REQUIRED_MASK,
            "old": 0x05,
        },
        {
            "name": "bottom_guard_preserves",
            "guard": 0,
            "replacement": REQUIRED_MASK,
            "old": 0x05,
        },
        {
            "name": "partial_guard_splices",
            "guard": 0x0F,
            "replacement": 0x35,
            "old": 0xA0,
        },
    ]
    rows: list[dict[str, Any]] = []
    for case in cases:
        direct_expr = qns_table_expr(case["guard"], case["replacement"], case["old"])
        named_expr = qns_table_call_expr(case["old"], case["guard"], case["replacement"])
        direct_actual, direct_raw = run_tau_qns(tau_bin, direct_expr, timeout_s=timeout_s, source=source)
        named_actual, named_raw = run_tau_qns(tau_bin, named_expr, timeout_s=timeout_s, source=source)
        expected = expected_qns_table_revision(case["guard"], case["replacement"], case["old"])
        rows.append(
            {
                **case,
                "direct_expression": direct_expr,
                "named_expression": named_expr,
                "expected": expected,
                "direct_actual": direct_actual,
                "named_actual": named_actual,
                "ok": direct_actual == expected and named_actual == expected,
                "raw": {
                    "direct": direct_raw,
                    "named": named_raw,
                },
            }
        )
    return {
        "claim": "Direct qns8 table syntax and the named Tau memory revision implement guarded pointwise revision.",
        "ok": all(row["ok"] for row in rows),
        "rows": rows,
    }


def evidence_names(mask: int) -> list[str]:
    return [name for name, bit in EVIDENCE_BITS.items() if mask & (1 << bit)]


def format_mask(mask: int) -> str:
    return f"0x{mask & TOP:02X}"


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def report_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def candidate_evidence(item: dict[str, Any]) -> dict[str, Any]:
    accepted = 1 << EVIDENCE_BITS["proposed"]
    reasons: list[str] = []
    expr = item.get("expr")
    target = item.get("target")
    if not isinstance(expr, str):
        return {
            "accepted_mask": accepted,
            "review_mask": 1 << EVIDENCE_BITS["review_required"],
            "review_reasons": ["expr is not a string"],
        }
    try:
        tree = parse_tree_expr(expr)
    except ParseError as exc:
        return {
            "accepted_mask": accepted,
            "review_mask": 1 << EVIDENCE_BITS["review_required"],
            "review_reasons": [str(exc)],
        }
    accepted |= 1 << EVIDENCE_BITS["parse_ok"]
    fn = target_fn(str(target))
    if fn is None:
        reasons.append("unknown target")
    train_xs = (0.25, 0.5, 1.0, 1.5)
    holdout_xs = (0.75, 1.25, 2.0)
    try:
        train_err = max(abs(tree.eval(x) - fn(x)) for x in train_xs) if fn else math.inf
        holdout_err = max(abs(tree.eval(x) - fn(x)) for x in holdout_xs) if fn else math.inf
        accepted |= 1 << EVIDENCE_BITS["domain_ok"]
    except (OverflowError, ValueError) as exc:
        train_err = math.inf
        holdout_err = math.inf
        reasons.append(str(exc))
    tol = 1.0e-8
    if train_err <= tol:
        accepted |= 1 << EVIDENCE_BITS["train_fit"]
    else:
        reasons.append(f"train error {train_err}")
    if holdout_err <= tol:
        accepted |= 1 << EVIDENCE_BITS["holdout_fit"]
    else:
        reasons.append(f"holdout error {holdout_err}")
    update_ready_prereqs = (
        (1 << EVIDENCE_BITS["proposed"])
        | (1 << EVIDENCE_BITS["parse_ok"])
        | (1 << EVIDENCE_BITS["domain_ok"])
        | (1 << EVIDENCE_BITS["train_fit"])
        | (1 << EVIDENCE_BITS["holdout_fit"])
    )
    if not reasons and (accepted & update_ready_prereqs) == update_ready_prereqs:
        accepted |= 1 << EVIDENCE_BITS["memory_update_ready"]
    return {
        "canonical_expr": tree.pretty(),
        "accepted_mask": accepted,
        "review_mask": (1 << EVIDENCE_BITS["review_required"]) if reasons else 0,
        "review_reasons": reasons,
        "train_max_abs_error": train_err,
        "holdout_max_abs_error": holdout_err,
    }


def tau_promote_and_revise(
    tau_bin: Path,
    old_memory: int,
    accepted_mask: int,
    review_mask: int,
    *,
    timeout_s: float,
    source: str,
) -> dict[str, Any]:
    accepted = qns_const(accepted_mask)
    review = qns_const(review_mask)
    missing_expr = f"missing_required({accepted})"
    blocker_expr = f"blocker({accepted}, {review})"
    missing, missing_raw = run_tau_qns(tau_bin, missing_expr, timeout_s=timeout_s, source=source)
    blocker, blocker_raw = run_tau_qns(tau_bin, blocker_expr, timeout_s=timeout_s, source=source)
    promoted = missing == 0 and blocker == 0
    guard = TOP if promoted else 0
    revision_expr = qns_table_call_expr(old_memory, guard, accepted_mask)
    direct_revision_expr = qns_table_expr(guard, accepted_mask, old_memory)
    revised, revised_raw = run_tau_qns(tau_bin, revision_expr, timeout_s=timeout_s, source=source)
    expected = expected_qns_table_revision(guard, accepted_mask, old_memory)
    if revised != expected:
        raise RuntimeError(
            "direct qns8 table revision mismatch: "
            f"expected {expected}, got {revised}, expression={revision_expr}"
        )
    return {
        "missing_required_mask": missing,
        "blocker_mask": blocker,
        "promoted": promoted,
        "old_memory_mask": old_memory,
        "new_memory_mask": revised,
        "table_revision": {
            "call_expression": revision_expr,
            "definition": QNS_MEMORY_REVISION_DEFINITION,
            "direct_table_expression": direct_revision_expr,
            "guard_mask": guard,
            "replacement_mask": accepted_mask,
            "else_mask": old_memory,
            "expected_mask": expected,
            "actual_mask": revised,
            "ok": revised == expected,
        },
        "raw": {
            "missing_required": missing_raw,
            "blocker": blocker_raw,
            "revision": revised_raw,
        },
    }


def load_or_call_model(args: argparse.Namespace, prompt: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if args.llm_output is not None and not args.live_ollama:
        data = json.loads(args.llm_output.read_text(encoding="utf-8"))
        return {"source": "file", "path": report_path(args.llm_output)}, data
    ollama = call_ollama(
        args.model,
        prompt,
        url=args.ollama_url,
        timeout_s=args.ollama_timeout_s,
        num_gpu=args.num_gpu,
        num_predict=args.num_predict,
        temperature=args.temperature,
    )
    data = extract_json_object(str(ollama["raw_response"]))
    return {"source": "ollama", **ollama}, data


def render_markdown_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# EML/qNS LLM Memory Demo Receipt",
        "",
        "This receipt is generated by the TauLang-Experiments demo harness.",
        "It records a bounded proposer-checker-memory run, not a full symbolic-regression proof.",
        "",
        "## Scope",
        "",
        f"- Claim: {result['scope']['claim']}",
        "- Not claimed:",
    ]
    lines.extend(f"  - {item}" for item in result["scope"]["not_claimed"])
    lines.extend(
        [
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
        ]
    )
    for key in [
        "candidate_count",
        "parse_ok_count",
        "promoted_count",
        "review_count",
        "memory_updated_count",
        "rejected_count",
        "rejected_preserved_count",
        "qns_table_regression_ok",
        "symbolic_tau_table_check_ok",
        "ok",
    ]:
        value = summary.get(key)
        lines.append(f"| `{key}` | `{report_value(value)}` |")

    lines.extend(
        [
            "",
            "## Input Hashes",
            "",
            "| Input | SHA-256 |",
            "| --- | --- |",
        ]
    )
    for key, value in result["input_hashes"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(
        [
            "",
            "## Final Memory",
            "",
            "| Target | Mask | Evidence atoms |",
            "| --- | ---: | --- |",
        ]
    )
    for target, memory in result["memory"].items():
        atoms = ", ".join(memory["atoms"]) if memory["atoms"] else "(none)"
        lines.append(f"| `{target}` | `{format_mask(memory['mask'])}` | {atoms} |")

    lines.extend(
        [
            "",
            "## Candidate Decisions",
            "",
            "| Target | Expression | Promoted | Old | New | Review reasons |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in result["rows"]:
        tau_check = row["tau_check"]
        reasons = "; ".join(row["review_reasons"]) if row["review_reasons"] else "(none)"
        lines.append(
            "| "
            f"`{row.get('target')}` | "
            f"`{row.get('expr')}` | "
            f"{yes_no(bool(tau_check['promoted']))} | "
            f"`{format_mask(tau_check['old_memory_mask'])}` | "
            f"`{format_mask(tau_check['new_memory_mask'])}` | "
            f"{reasons} |"
        )

    lines.extend(
        [
            "",
            "## qNS Table Regression",
            "",
            "| Case | Named result | Direct result | Expected | OK |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in result["qns_table_regression"]["rows"]:
        lines.append(
            "| "
            f"`{row['name']}` | "
            f"`{format_mask(row['named_actual'])}` | "
            f"`{format_mask(row['direct_actual'])}` | "
            f"`{format_mask(row['expected'])}` | "
            f"{yes_no(bool(row['ok']))} |"
        )

    lines.extend(
        [
            "",
            "## Table Expressions",
            "",
        ]
    )
    for row in result["rows"]:
        table_revision = row["tau_check"]["table_revision"]
        lines.extend(
            [
                f"### {row.get('target')}",
                "",
                "Named Tau call:",
                "",
                "```tau",
                table_revision["call_expression"],
                "```",
                "",
                "Equivalent direct table expression:",
                "",
                "```tau",
                table_revision["direct_table_expression"],
                "```",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local LLM -> EML -> qNS -> table-memory smoke demo.")
    parser.add_argument("--model", default=os.environ.get("QNS_LOCAL_MODEL", "llama3.2:3b"))
    parser.add_argument("--ollama-url", default=os.environ.get("QNS_OLLAMA_URL", "http://127.0.0.1:11434/api/generate"))
    parser.add_argument("--ollama-timeout-s", type=float, default=180.0)
    parser.add_argument("--num-gpu", type=int, default=int(os.environ.get("QNS_OLLAMA_NUM_GPU", "0")))
    parser.add_argument("--num-predict", type=int, default=int(os.environ.get("QNS_OLLAMA_NUM_PREDICT", "512")))
    parser.add_argument("--temperature", type=float, default=float(os.environ.get("QNS_OLLAMA_TEMPERATURE", "0.0")))
    parser.add_argument("--candidate-count", type=int, default=5)
    parser.add_argument("--live-ollama", action="store_true", help="Call Ollama instead of using fixture proposals.")
    parser.add_argument(
        "--llm-output",
        type=Path,
        default=DEFAULT_PROPOSALS,
        help="Use an existing proposal JSON. This is the default public path.",
    )
    parser.add_argument("--tau-bin", type=Path, default=DEFAULT_TAU_BIN)
    parser.add_argument("--tau-source", type=Path, default=DEFAULT_TAU_SOURCE)
    parser.add_argument("--table-source", type=Path, default=DEFAULT_TABLE_SOURCE)
    parser.add_argument("--tau-timeout-s", type=float, default=30.0)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report-out", type=Path, default=DEFAULT_REPORT_OUT)
    args = parser.parse_args()

    prompt = build_prompt(args.candidate_count)
    model_meta, proposal_data = load_or_call_model(args, prompt)
    source = tau_source(args.tau_source)
    table_check = run_tau_table_check(args.tau_bin, args.table_source, timeout_s=args.tau_timeout_s)
    qns_table_regression = run_qns_table_regressions(
        args.tau_bin, timeout_s=args.tau_timeout_s, source=source
    )
    if proposal_data.get("schema") != "eml_candidate_proposals_v1":
        raise SystemExit("proposal schema must be eml_candidate_proposals_v1")
    candidates = proposal_data.get("candidates")
    if not isinstance(candidates, list):
        raise SystemExit("proposal candidates must be a list")

    rows: list[dict[str, Any]] = []
    for index, item in enumerate(candidates):
        if not isinstance(item, dict):
            item = {"expr": None, "target": None, "origin": "invalid"}
        evidence = candidate_evidence(item)
        rows.append(
            {
                "index": index,
                "target": item.get("target"),
                "origin": item.get("origin"),
                "expr": item.get("expr"),
                **evidence,
                "accepted_atoms": evidence_names(evidence["accepted_mask"]),
                "review_atoms": evidence_names(evidence["review_mask"]),
            }
        )
    memory: dict[str, int] = {"exp(x)": 0, "ln(x)": 0, "exp(exp(x))": 0}
    for row in rows:
        target = str(row.get("target"))
        old = memory.get(target, 0)
        tau_check = tau_promote_and_revise(
            args.tau_bin,
            old,
            row["accepted_mask"],
            row["review_mask"],
            timeout_s=args.tau_timeout_s,
            source=source,
        )
        if target in memory:
            memory[target] = tau_check["new_memory_mask"]
        row["tau_check"] = tau_check

    result = {
        "schema": "eml_qns_llm_memory_demo_v1",
        "scope": {
            "claim": "A local LLM can act as an untrusted EML proposer, while Tau qns8 gates promotion and pointwise table-memory updates.",
            "not_claimed": [
                "not full symbolic regression",
                "not proof by model output",
                "not native Tau analytic EML semantics",
                "not full TABA tables",
            ],
        },
        "prompt": prompt,
        "model": model_meta,
        "input_hashes": {
            "proposal_file": (
                sha256_file(args.llm_output)
                if model_meta.get("source") == "file" and args.llm_output is not None
                else None
            ),
            "proposal_data": sha256_json(proposal_data),
            "tau_source": sha256_file(args.tau_source),
            "table_source": sha256_file(args.table_source),
        },
        "tau_source": report_path(args.tau_source),
        "tau_table_check": table_check,
        "qns_table_regression": qns_table_regression,
        "evidence_bits": EVIDENCE_BITS,
        "required_mask": REQUIRED_MASK,
        "summary": {
            "candidate_count": len(rows),
            "parse_ok_count": sum(1 for row in rows if "parse_ok" in row["accepted_atoms"]),
            "promoted_count": sum(1 for row in rows if row["tau_check"]["promoted"]),
            "review_count": sum(1 for row in rows if row["review_mask"] != 0),
            "memory_updated_count": sum(1 for row in rows if row["tau_check"]["new_memory_mask"] != row["tau_check"]["old_memory_mask"]),
            "rejected_count": sum(1 for row in rows if not row["tau_check"]["promoted"]),
            "rejected_preserved_count": sum(
                1
                for row in rows
                if not row["tau_check"]["promoted"]
                and row["tau_check"]["new_memory_mask"] == row["tau_check"]["old_memory_mask"]
            ),
            "qns_table_regression_ok": qns_table_regression["ok"],
            "symbolic_tau_table_check_ok": table_check["ok"],
            "ok": (
                table_check["ok"]
                and qns_table_regression["ok"]
                and any(row["tau_check"]["promoted"] for row in rows)
                and all(row["tau_check"]["table_revision"]["ok"] for row in rows)
            ),
        },
        "memory": {
            target: {"mask": mask, "atoms": evidence_names(mask)}
            for target, mask in memory.items()
        },
        "proposal": proposal_data,
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.write_text(render_markdown_report(result), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    if not result["summary"]["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
