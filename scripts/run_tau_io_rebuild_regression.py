#!/usr/bin/env python3
"""Check the opt-in Tau IO rebuild skip against vector and file streams.

The optimization is only safe for streams whose rebuild operation is declared
state-preserving by the stream class. File streams deliberately do not make that
claim, because rebuilding a file input resets its read position and rebuilding a
file output reopens the file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
from pathlib import Path


RUN_STATS_RE = re.compile(r"\[run_step\]\s+(.*)")
UPDATE_STATS_RE = re.compile(r"\[update_revision\]\s+(.*)")
KV_RE = re.compile(r"([A-Za-z_]+)=([^ ]+)")


HARNESS = r'''
#include "api.h"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

using namespace idni::tau_lang;
using node_t = node<tau_ba<bv, sbf_ba>, bv, sbf_ba>;
using tau_tree = tree<node_t>;

std::string join_values(const std::vector<std::string>& values) {
	std::ostringstream out;
	for (size_t i = 0; i < values.size(); ++i) {
		if (i) out << "|";
		out << values[i];
	}
	return out.str();
}

std::vector<std::string> read_lines(const std::filesystem::path& path) {
	std::vector<std::string> values;
	std::ifstream in(path);
	std::string line;
	while (std::getline(in, line)) values.push_back(line);
	return values;
}

void set_skip(bool skip) {
	setenv("TAU_RUN_STATS", "1", 1);
	if (skip) setenv("TAU_SKIP_UNCHANGED_IO_REBUILD", "1", 1);
	else unsetenv("TAU_SKIP_UNCHANGED_IO_REBUILD");
}

int run_vector_case(bool skip) {
	set_skip(skip);
	std::cerr << "[case] name=vector mode=" << (skip ? "skip" : "baseline") << "\n";
	std::vector<std::string> updates = {
		"o1[t] = 1",
		"o2[t] = 0",
		"o1[t] = 0"
	};
	auto i1 = std::make_shared<vector_input_stream>(updates);
	auto u = std::make_shared<vector_output_stream>();
	auto o1 = std::make_shared<vector_output_stream>();
	auto o2 = std::make_shared<vector_output_stream>();
	io_context<node_t> ctx;
	ctx.add_input("i1", tau_type_id<node_t>(), i1);
	ctx.add_output("u", tau_type_id<node_t>(), u);
	ctx.add_output("o1", tau_type_id<node_t>(), o1);
	ctx.add_output("o2", tau_type_id<node_t>(), o2);
	tref parsed = tau_tree::get("u[t] = i1[t].");
	auto nso_rr = get_nso_rr<node_t>(ctx, parsed);
	if (!nso_rr.has_value()) return 2;
	auto maybe_i = run<node_t>(nso_rr.value().main->get(), ctx, updates.size());
	if (!maybe_i.has_value()) return 3;
	std::cout << "CASE\tvector\t" << (skip ? "skip" : "baseline")
		<< "\tU\t" << join_values(u->get_values())
		<< "\tO1\t" << join_values(o1->get_values())
		<< "\tO2\t" << join_values(o2->get_values()) << "\n";
	return 0;
}

int run_file_case(bool skip, const std::filesystem::path& root) {
	set_skip(skip);
	const auto mode = skip ? "skip" : "baseline";
	std::cerr << "[case] name=file mode=" << mode << "\n";
	const auto dir = root / mode;
	std::filesystem::create_directories(dir);
	const auto input_path = dir / "updates.in";
	const auto u_path = dir / "u.out";
	const auto o1_path = dir / "o1.out";
	const auto o2_path = dir / "o2.out";
	{
		std::ofstream updates(input_path);
		updates << "o1[t] = 1\n";
		updates << "o2[t] = 0\n";
		updates << "o1[t] = 0\n";
	}
	{
		auto i1 = std::make_shared<file_input_stream>(input_path.string());
		auto u = std::make_shared<file_output_stream>(u_path.string());
		auto o1 = std::make_shared<file_output_stream>(o1_path.string());
		auto o2 = std::make_shared<file_output_stream>(o2_path.string());
		io_context<node_t> ctx;
		ctx.add_input("i1", tau_type_id<node_t>(), i1);
		ctx.add_output("u", tau_type_id<node_t>(), u);
		ctx.add_output("o1", tau_type_id<node_t>(), o1);
		ctx.add_output("o2", tau_type_id<node_t>(), o2);
		tref parsed = tau_tree::get("u[t] = i1[t].");
		auto nso_rr = get_nso_rr<node_t>(ctx, parsed);
		if (!nso_rr.has_value()) return 4;
		auto maybe_i = run<node_t>(nso_rr.value().main->get(), ctx, 3);
		if (!maybe_i.has_value()) return 5;
	}
	std::cout << "CASE\tfile\t" << mode
		<< "\tU\t" << join_values(read_lines(u_path))
		<< "\tO1\t" << join_values(read_lines(o1_path))
		<< "\tO2\t" << join_values(read_lines(o2_path)) << "\n";
	return 0;
}

int main(int argc, char** argv) {
	if (argc != 2) return 1;
	std::filesystem::path root = argv[1];
	for (bool skip : {false, true}) {
		if (int rc = run_vector_case(skip); rc != 0) return rc;
	}
	for (bool skip : {false, true}) {
		if (int rc = run_file_case(skip, root); rc != 0) return rc;
	}
	return 0;
}
'''


def parse_stats(output: str, pattern: re.Pattern[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for match in pattern.finditer(output):
        row: dict[str, object] = {}
        for key, value in KV_RE.findall(match.group(1)):
            if key.endswith("_ms"):
                row[key] = float(value)
            else:
                row[key] = int(value)
        rows.append(row)
    return rows


def parse_case_stats(stderr: str) -> dict[str, dict[str, int]]:
    case_stats: dict[str, list[dict[str, object]]] = {}
    current: str | None = None
    for line in stderr.splitlines():
        if line.startswith("[case] "):
            fields = dict(KV_RE.findall(line))
            current = f"{fields.get('name', 'unknown')}_{fields.get('mode', 'unknown')}"
            case_stats.setdefault(current, [])
            continue
        match = UPDATE_STATS_RE.search(line)
        if match and current:
            row: dict[str, object] = {}
            for key, value in KV_RE.findall(match.group(1)):
                if key.endswith("_ms"):
                    row[key] = float(value)
                else:
                    row[key] = int(value)
            case_stats.setdefault(current, []).append(row)
    return {
        key: summarize_update_stats(rows)
        for key, rows in case_stats.items()
    }


def summarize_update_stats(update_stats: list[dict[str, object]]) -> dict[str, int]:
    accepted = [row for row in update_stats if int(row.get("accepted", 0)) == 1]
    return {
        "accepted_updates": len(accepted),
        "input_rebuild_skipped": sum(
            int(row.get("input_rebuild_skipped", 0)) for row in accepted
        ),
        "output_rebuild_skipped": sum(
            int(row.get("output_rebuild_skipped", 0)) for row in accepted
        ),
    }


def extract_compile_flags(tau_root: Path, build_dir: Path) -> list[str]:
    compile_commands = build_dir / "compile_commands.json"
    data = json.loads(compile_commands.read_text(encoding="utf-8"))
    main_cmd = next(
        row["command"] for row in data if row["file"].endswith("/src/main.cpp")
    )
    tokens = shlex.split(main_cmd)
    flags: list[str] = []
    skip_next = False
    for token in tokens[1:]:
        if skip_next:
            skip_next = False
            continue
        if token in {"-o", "-c"}:
            skip_next = True
            continue
        if token.endswith("/src/main.cpp") or token.endswith("main.cpp"):
            continue
        if token.startswith("-W") or token in {"-flto=auto"}:
            continue
        flags.append(token)
    flags.extend(
        [
            f"-I{tau_root / 'tests'}",
            f"-I{tau_root / 'tests' / 'integration'}",
        ]
    )
    return flags


def extract_link_flags(build_dir: Path) -> list[str]:
    link_txt = build_dir / "src" / "CMakeFiles" / "tau.dir" / "link.txt"
    tokens = shlex.split(link_txt.read_text(encoding="utf-8"))
    cvc5 = next((token for token in tokens if "libcvc5.so" in token), None)
    flags = [
        str(build_dir / "libTAU.a"),
    ]
    if cvc5:
        flags.append(cvc5)
    flags.extend(
        [
            str(build_dir / "libtauparser.a"),
            "/usr/lib/x86_64-linux-gnu/libboost_log.a",
            "-lrt",
            "/usr/lib/x86_64-linux-gnu/libboost_chrono.a",
            "/usr/lib/x86_64-linux-gnu/libboost_filesystem.a",
            "/usr/lib/x86_64-linux-gnu/libboost_atomic.a",
            "/usr/lib/x86_64-linux-gnu/libboost_regex.a",
            "-licudata",
            "-licui18n",
            "-licuuc",
            "/usr/lib/x86_64-linux-gnu/libboost_thread.a",
        ]
    )
    if cvc5:
        flags.append(f"-Wl,-rpath,{Path(cvc5).parent}")
    return flags


def parse_case_lines(stdout: str) -> dict[str, dict[str, str]]:
    cases: dict[str, dict[str, str]] = {}
    for line in stdout.splitlines():
        if not line.startswith("CASE\t"):
            continue
        parts = line.split("\t")
        key = f"{parts[1]}_{parts[2]}"
        cases[key] = {
            "u": parts[4] if len(parts) > 4 else "",
            "o1": parts[6] if len(parts) > 6 else "",
            "o2": parts[8] if len(parts) > 8 else "",
        }
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-root", type=Path, default=Path("external/tau-lang"))
    parser.add_argument(
        "--build-dir", type=Path, default=Path("external/tau-lang/build-Release")
    )
    parser.add_argument("--out", type=Path, default=Path("results/local/tau-io-rebuild-regression.json"))
    args = parser.parse_args()

    tau_root = args.tau_root.resolve()
    build_dir = args.build_dir.resolve()
    work_dir = args.out.parent / "tau-io-rebuild-regression"
    work_dir.mkdir(parents=True, exist_ok=True)
    source = work_dir / "harness.cpp"
    binary = work_dir / "harness"
    runtime_dir = work_dir / "runtime"
    source.write_text(HARNESS, encoding="utf-8")

    compile_cmd = [
        "c++",
        *extract_compile_flags(tau_root, build_dir),
        str(source),
        "-o",
        str(binary),
        *extract_link_flags(build_dir),
    ]
    compile_proc = subprocess.run(
        compile_cmd, text=True, capture_output=True, check=False
    )
    if compile_proc.returncode != 0:
        print(compile_proc.stdout)
        print(compile_proc.stderr)
        return compile_proc.returncode

    run_proc = subprocess.run(
        [str(binary), str(runtime_dir)],
        text=True,
        capture_output=True,
        check=False,
    )
    combined = run_proc.stdout + run_proc.stderr
    update_stats = parse_stats(combined, UPDATE_STATS_RE)
    run_stats = parse_stats(combined, RUN_STATS_RE)
    cases = parse_case_lines(run_proc.stdout)
    case_stats = parse_case_stats(run_proc.stderr)
    vector_skip_stats = case_stats.get("vector_skip", {})
    file_skip_stats = case_stats.get("file_skip", {})
    summary = {
        "ok": (
            run_proc.returncode == 0
            and cases.get("vector_baseline") == cases.get("vector_skip")
            and cases.get("file_baseline") == cases.get("file_skip")
            and int(vector_skip_stats.get("input_rebuild_skipped", 0)) > 0
            and int(vector_skip_stats.get("output_rebuild_skipped", 0)) > 0
            and int(file_skip_stats.get("input_rebuild_skipped", 0)) == 0
            and int(file_skip_stats.get("output_rebuild_skipped", 0)) == 0
        ),
        "scope": "native Tau IO rebuild skip regression over vector remaps and file remaps",
        "cases": cases,
        "case_update_stats": case_stats,
        "run_stats_count": len(run_stats),
        "update_stats": summarize_update_stats(update_stats),
        "stdout": run_proc.stdout,
        "stderr_tail": run_proc.stderr[-1600:],
        "boundary": (
            "Vector remaps may skip unchanged rebuilds. File remaps must not skip, "
            "because their rebuild operation intentionally reopens the file."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
