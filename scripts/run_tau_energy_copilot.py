#!/usr/bin/env python3
"""Build or verify an advisory TauEnergy proposal packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tau_energy.copilot import build_proposal_packet
from tau_energy.export import export_packet, write_json


def verify(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    ok = (
        data.get("schema") == "tau-energy-proposal-packet-v1"
        and data.get("status") == "advisory_packet_ready"
        and data.get("authority", {}).get("tau_energy_can_accept") is False
        and data.get("authority", {}).get("tau_jepa_can_verify") is False
        and data.get("authority", {}).get("llm_can_execute_tau") is False
        and len(data.get("energy_ranking", [])) >= 1
        and all(row.get("label") != "accepted" for row in data.get("energy_ranking", []))
    )
    print(json.dumps({"ok": ok, "verified": path.as_posix()}, indent=2, sort_keys=True))
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", default="Create a TauEnergy chatbot workbench for Tau Language proposals.")
    parser.add_argument("--out", type=Path, default=Path("results/local/tau-energy/tau_energy_packet.json"))
    parser.add_argument("--export-dir", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()

    if args.verify:
        return verify(args.verify)

    packet = build_proposal_packet(args.prompt, root=str(ROOT))
    write_json(args.out, packet)
    exported = export_packet(packet, args.export_dir) if args.export_dir else {}
    print(json.dumps({
        "status": packet["status"],
        "out": args.out.as_posix(),
        "exported": exported,
        "top_candidate": packet["energy_ranking"][0],
        "top_stress": packet["stress_matrix"][0],
        "authority": packet["authority"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
