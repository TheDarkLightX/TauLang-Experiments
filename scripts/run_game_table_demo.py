#!/usr/bin/env python3
"""Bounded game-table demo for the post-AGI tokenomics example.

The script has two layers:

1. A finite Python model that mirrors the Lean kernel in
   proofs/game_tables_math_v001.
2. An optional Tau equivalence check showing that the table syntax lowers to
   the hand-expanded guarded-choice expression.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


AGENT_ACTIONS = ("contribute", "extract", "exit")
PROTOCOL_ACTIONS = ("reward", "tax", "quarantine")

PAYOFF: dict[tuple[str, str], int] = {
    ("contribute", "reward"): 42,
    ("extract", "reward"): 31,
    ("exit", "reward"): 10,
    ("contribute", "tax"): 25,
    ("extract", "tax"): 20,
    ("exit", "tax"): 10,
    ("contribute", "quarantine"): 12,
    ("extract", "quarantine"): 0,
    ("exit", "quarantine"): 10,
}


@dataclass(frozen=True)
class Profile:
    agent: str
    protocol: str

    def key(self) -> str:
        return f"{self.agent}/{self.protocol}"


def all_profiles() -> list[Profile]:
    return [Profile(agent, protocol) for protocol in PROTOCOL_ACTIONS for agent in AGENT_ACTIONS]


def allowed(profile: Profile) -> bool:
    return not (profile.agent == "extract" and profile.protocol == "reward")


def desired(profile: Profile) -> bool:
    return profile.agent == "contribute" and profile.protocol == "reward"


def payoff(profile: Profile) -> int:
    return PAYOFF[(profile.agent, profile.protocol)]


def deviations(profile: Profile) -> Iterable[Profile]:
    for agent_action in AGENT_ACTIONS:
        yield Profile(agent_action, profile.protocol)


def best_response(profile: Profile) -> bool:
    return all(
        (not allowed(candidate)) or payoff(candidate) <= payoff(profile)
        for candidate in deviations(profile)
    )


def nash(profile: Profile) -> bool:
    return allowed(profile) and best_response(profile)


def safe_nash(profile: Profile) -> bool:
    return nash(profile) and allowed(profile) and desired(profile)


def has_profitable_deviation(profile: Profile) -> bool:
    return any(
        allowed(candidate) and payoff(profile) < payoff(candidate)
        for candidate in deviations(profile)
    )


def classify(profile: Profile) -> str:
    if safe_nash(profile):
        return "safe_nash"
    if not allowed(profile):
        return "unsafe_extract"
    if nash(profile):
        return "allowed_but_not_equilibrium"
    return "not_desired"


def tau_source(path: Path) -> str:
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("#"):
            lines.append(line)
    return "\n".join(lines)


def run_tau_equivalence(repo_root: Path, tau_bin: str) -> dict[str, object]:
    example = repo_root / "examples/tau/post_agi_tokenomics_game_table_v1.tau"
    src = tau_source(example)
    args = (
        "contribute,extract,exit,reward,tax,quarantine,"
        "safe_nash,unsafe_extract,allowed_but_not_equilibrium,not_desired,invalid_profile"
    )
    query = (
        f"{src}\n"
        "solve --tau "
        f"(post_agi_tokenomics_table({args}) != post_agi_tokenomics_raw({args}))"
    )
    env = dict(os.environ)
    env["TAU_ENABLE_SAFE_TABLES"] = "1"
    proc = subprocess.run(
        [
            tau_bin,
            "--charvar",
            "false",
            "-e",
            query,
            "--severity",
            "info",
            "--color",
            "false",
            "--status",
            "true",
        ],
        cwd=repo_root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    clean_lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    last_line = clean_lines[-1] if clean_lines else ""
    return {
        "ran": True,
        "ok": proc.returncode == 0 and last_line == "no solution",
        "returncode": proc.returncode,
        "last_line": last_line,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tau-bin", default=None)
    parser.add_argument("--out", default="results/local/game-table-demo.json")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    profiles = all_profiles()
    rows = [
        {
            "profile": profile.key(),
            "allowed": allowed(profile),
            "payoff": payoff(profile),
            "best_response": best_response(profile),
            "nash": nash(profile),
            "desired": desired(profile),
            "safe_nash": safe_nash(profile),
            "profitable_deviation": has_profitable_deviation(profile),
            "classification": classify(profile),
        }
        for profile in profiles
    ]
    safe_profiles = [row["profile"] for row in rows if row["safe_nash"]]
    expected_safe_profiles = ["contribute/reward"]
    pruned_rows = [row for row in rows if not row["profitable_deviation"]]
    pruned_safe_profiles = [row["profile"] for row in pruned_rows if row["safe_nash"]]

    tau_equivalence = {"ran": False, "ok": None}
    if args.tau_bin:
        tau_equivalence = run_tau_equivalence(repo_root, args.tau_bin)

    result = {
        "ok": safe_profiles == expected_safe_profiles
        and pruned_safe_profiles == safe_profiles
        and (tau_equivalence["ok"] is not False),
        "profile_count": len(rows),
        "pruned_profile_count": len(pruned_rows),
        "pruned_by_profitable_deviation": len(rows) - len(pruned_rows),
        "safe_profiles": safe_profiles,
        "pruned_safe_profiles": pruned_safe_profiles,
        "rows": rows,
        "tau_equivalence": tau_equivalence,
        "scope": [
            "finite listed pure-strategy game",
            "one-player deviation check in this fixture",
            "no mixed strategies",
            "no continuous actions",
            "Tau check is table-vs-raw equivalence, not native payoff arithmetic",
        ],
    }

    out_path = repo_root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        display_out = str(out_path.relative_to(repo_root))
    except ValueError:
        display_out = args.out

    print("Bounded game-table demo")
    print(f"profiles:       {len(rows)}")
    print(f"after pruning:  {len(pruned_rows)}")
    print(f"safe profiles:  {', '.join(safe_profiles) if safe_profiles else '(none)'}")
    model_ok = safe_profiles == expected_safe_profiles and pruned_safe_profiles == safe_profiles
    print(f"model check:    {'passed' if model_ok else 'failed'}")
    if tau_equivalence["ran"]:
        print(f"Tau equivalence: {'passed' if tau_equivalence['ok'] else 'failed'}")
    else:
        print("Tau equivalence: skipped")
    print(f"result:         {display_out}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
