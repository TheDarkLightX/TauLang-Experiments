#!/usr/bin/env python3
"""Enable the extra printer suite, retaining the other preset exclusions."""
from pathlib import Path
import subprocess

cache = Path("build/release/CMakeCache.txt")
lines = cache.read_text().splitlines()
value = next(line.split("=", 1)[1] for line in lines
             if line.startswith("TAU_SKIP_TESTS:STRING="))
kept = [name for name in value.split(";") if name != "test_tau_tree_printers"]
subprocess.run(["cmake", "-S", ".", "-B", "build/release",
                "-DTAU_SKIP_TESTS=" + ";".join(kept)], check=True)
subprocess.run(["cmake", "--build", "build/release", "--target",
                "test_tau_tree_printers", "--parallel", "4"], check=True)
