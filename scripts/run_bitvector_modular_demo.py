#!/usr/bin/env python3
"""Exhaustive fixed-width modular-arithmetic checks for Tau future work.

This is a community experiment for Tau's fixed-width bitvector future-work
lane. It checks which algebraic rewrites are safe under modulo 2^w semantics
and records counterexamples for tempting integer rewrites that fail after
overflow.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path


def mask(width: int) -> int:
    if width < 1:
        raise ValueError("width must be positive")
    return (1 << width) - 1


def bv(width: int, value: int) -> int:
    return value & mask(width)


def add(width: int, x: int, y: int) -> int:
    return bv(width, x + y)


def sub(width: int, x: int, y: int) -> int:
    return bv(width, x - y)


def mul(width: int, x: int, y: int) -> int:
    return bv(width, x * y)


def bit_not(width: int, x: int) -> int:
    return bv(width, ~x)


def shl(width: int, x: int, amount: int) -> int:
    return bv(width, x << amount)


def shr(width: int, x: int, amount: int) -> int:
    return bv(width, x >> amount)


def find_counterexample(
    width: int,
    arity: int,
    predicate: Callable[..., bool],
) -> list[int] | None:
    domain = range(1 << width)

    def go(prefix: list[int]) -> list[int] | None:
        if len(prefix) == arity:
            return None if predicate(*prefix) else prefix
        for value in domain:
            found = go([*prefix, value])
            if found is not None:
                return found
        return None

    return go([])


def check_width(width: int) -> dict[str, object]:
    modulus = 1 << width
    domain = range(modulus)
    shifts = range(width + 1)

    safe_laws = {
        "add_zero_right": all(add(width, x, 0) == x for x in domain),
        "add_comm": all(add(width, x, y) == add(width, y, x) for x in domain for y in domain),
        "add_assoc": all(
            add(width, add(width, x, y), z) == add(width, x, add(width, y, z))
            for x in domain
            for y in domain
            for z in domain
        ),
        "sub_self": all(sub(width, x, x) == 0 for x in domain),
        "mul_one_right": all(mul(width, x, 1) == x for x in domain),
        "mul_zero_right": all(mul(width, x, 0) == 0 for x in domain),
        "mul_comm": all(mul(width, x, y) == mul(width, y, x) for x in domain for y in domain),
        "mul_assoc": all(
            mul(width, mul(width, x, y), z) == mul(width, x, mul(width, y, z))
            for x in domain
            for y in domain
            for z in domain
        ),
        "left_shift_is_mul_pow2_mod": all(
            shl(width, x, s) == mul(width, x, 1 << s) for x in domain for s in shifts
        ),
        "bit_not_involution": all(bit_not(width, bit_not(width, x)) == x for x in domain),
    }

    invalid_rewrites = {
        "add_preserves_unsigned_order": find_counterexample(
            width,
            3,
            lambda x, y, z: not (x <= y) or add(width, x, z) <= add(width, y, z),
        ),
        "add_result_ge_left": find_counterexample(
            width,
            2,
            lambda x, y: add(width, x, y) >= x,
        ),
        "mul_cancel_nonzero": find_counterexample(
            width,
            3,
            lambda x, y, z: x == 0 or mul(width, x, y) != mul(width, x, z) or y == z,
        ),
        "shift_left_then_right_roundtrip": find_counterexample(
            width,
            2,
            lambda x, s: s > width or shr(width, shl(width, x, s), s) == x,
        ),
    }

    return {
        "width": width,
        "modulus": modulus,
        "safe_laws": safe_laws,
        "all_safe_laws_passed": all(safe_laws.values()),
        "invalid_rewrite_counterexamples": invalid_rewrites,
        "all_invalid_rewrites_refuted": all(v is not None for v in invalid_rewrites.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-width", type=int, default=6)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results/local/bitvector-modular-demo.json"),
    )
    args = parser.parse_args()

    rows = [check_width(width) for width in range(1, args.max_width + 1)]
    invalid_names = sorted(rows[0]["invalid_rewrite_counterexamples"]) if rows else []
    invalid_refuted_some_width = {
        name: any(row["invalid_rewrite_counterexamples"][name] is not None for row in rows)
        for name in invalid_names
    }
    ok = all(row["all_safe_laws_passed"] for row in rows) and all(
        invalid_refuted_some_width.values()
    )
    summary = {
        "scope": "exhaustive fixed-width modular arithmetic checks for small widths",
        "max_width": args.max_width,
        "ok": ok,
        "invalid_rewrites_refuted_some_width": invalid_refuted_some_width,
        "rows": rows,
        "boundary": (
            "This is an exhaustive small-width corpus and rewrite triage. "
            "It is not a full Tau bitvector implementation or solver proof."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
