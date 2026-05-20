"""Export helpers for TauEnergy experiment artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: Path, data: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def export_packet(packet: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "packet": out_dir / "tau_energy_packet.json",
        "ranking": out_dir / "energy_ranking.json",
        "stress": out_dir / "stress_matrix.json",
        "repairs": out_dir / "repairs.json",
        "summary": out_dir / "README.md",
    }
    write_json(files["packet"], packet)
    write_json(files["ranking"], packet["energy_ranking"])
    write_json(files["stress"], packet["stress_matrix"])
    write_json(files["repairs"], packet["repairs"])
    summary = [
        "# TauEnergy Proposal Packet",
        "",
        f"Status: `{packet['status']}`",
        f"Grammar hash: `{packet['syntax_snapshot']['grammar_hash']}`",
        "",
        "Authority boundary:",
    ]
    for key, value in sorted(packet["authority"].items()):
        summary.append(f"- `{key}`: `{str(value).lower()}`")
    summary.extend([
        "",
        "Top candidate:",
        f"- `{packet['energy_ranking'][0]['candidate_id']}` with energy `{packet['energy_ranking'][0]['energy']}`",
        "",
        "Tau or a deterministic receipt must validate any Tau-facing claim before use.",
    ])
    files["summary"].write_text("\n".join(summary) + "\n", encoding="utf-8")
    return {name: path.as_posix() for name, path in files.items()}
