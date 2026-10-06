"""Input rendering adapted from Andrei's Tau issue 203 reproduction.
Use the bounded check and comparison scripts in this package.
"""
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

AMOUNT, ID_STREAM, KEY_STREAM = 1, 12, 18
CHAIN_THRESHOLDS = (1000, 10000, 100000)
BASE_RULE = "always ( o1[t]:bv[24] = i1[t]:bv[24] ).\n"
ROUTER = "((!(i0[t] = 0)) ? ( u[t] = i0[t] && o0[t] = 0 ) : o0[t] = 1).\n"
FIRST_PROMPT = "Execution step: 0"
POLL_SECONDS = 0.5

Const = Tuple[int, int, int]  # (small id, 384-bit tag byte, 384-bit counter)


# ---------------------------------------------------------------- rule text

def num24(v: int) -> str:
    return "{ #x%06x }:bv[24]" % v


class Ids:
    """Renders ids and keys as small integers (W=8) or 384-bit constants (W=384)."""

    def __init__(self, width: int, largest: int) -> None:
        self.width = width
        # bv[8] holds ids up to 254; a larger id space needs bv[16].
        self.bits = 384 if width == 384 else (8 if largest <= 254 else 16)

    def lit(self, c: Const) -> str:
        small, tag, count = c
        if self.width == 384:
            return "#x" + ("%02x%04x" % (tag, count)) * 16
        return str(small)

    def text(self, c: Const) -> str:
        return "{ %s }:bv[%d]" % (self.lit(c), self.bits)


@dataclass
class Branch:
    ident: Const
    keys: List[Const]       # keys[j] and thresholds[j] make up the term on stream KEY_STREAM + j
    thresholds: List[int]


def chain_branch(a: int) -> Branch:
    base = 4 * (a - 1) + 1
    return Branch((base, 0xAB, a),
                  [(base + 1 + j, 0xCA + j, a) for j in range(3)],
                  list(CHAIN_THRESHOLDS))


def terms_branch(k: int) -> Branch:
    return Branch((1, 0xAB, 1),
                  [(j + 2, 0xCD, j + 1) for j in range(k)],
                  [1000 * (j + 1) for j in range(k)])


def clause(ids: Ids, br: Branch) -> str:
    terms = ["(i1[t]:bv[24] > %s && !(i%d[t]:bv[%d] = %s))"
             % (num24(br.thresholds[j]), KEY_STREAM + j, ids.bits, ids.text(br.keys[j]))
             for j in reversed(range(len(br.keys)))]
    return "( ( %s ) ? (o5[t]:bv[24] = %s) : (o5[t]:bv[24] = %s) )" % (
        " || ".join(terms), num24(0), num24(1))


def nested(ids: Ids, branches: List[Branch]) -> str:
    rest = "(o5[t]:bv[24] = %s)" % num24(1)
    for br in reversed(branches):
        rest = "((i12[t]:bv[%d] = %s) ? ( %s ) : %s)" % (
            ids.bits, ids.text(br.ident), clause(ids, br), rest)
    return rest


@dataclass
class Check:
    label: str
    expect: int
    values: Dict[int, str]  # stdin value per stream; unlisted streams read 0


@dataclass
class Workload:
    bits: int
    streams: List[int]      # input streams in prompt order
    spec: str               # boot file of the spec path
    rule: str               # rule typed at i0 on the revision path
    checks: List[Check]


def key_checks(ids: Ids, br: Branch, name: str) -> List[Check]:
    bare = {AMOUNT: "1001", ID_STREAM: ids.lit(br.ident)}
    keyed = dict(bare)
    keyed[KEY_STREAM] = ids.lit(br.keys[0])
    return [Check("%s, no key" % name, 0, bare), Check("%s, key on i18" % name, 1, keyed)]


def chain_workload(n: int, width: int, live_only: bool) -> Workload:
    ids = Ids(width, 4 * n)
    shown = [n] if live_only else list(range(1, n + 1))
    body = nested(ids, [chain_branch(a) for a in shown])
    picked = shown if (live_only or n <= 8) else sorted({1, (n + 1) // 2, n})
    checks: List[Check] = []
    for a in picked:
        checks += key_checks(ids, chain_branch(a), "branch %d" % a)
    return Workload(
        bits=ids.bits,
        streams=[AMOUNT, ID_STREAM, 18, 19, 20],
        spec="always ( (o1[t]:bv[24] = i1[t]:bv[24]) && (%s) ).\n" % body,
        rule="always ( %s ).\n" % body,
        checks=checks)


def terms_workload(k: int, width: int) -> Workload:
    ids = Ids(width, k + 1)
    br = terms_branch(k)
    body = nested(ids, [br])
    base = {AMOUNT: str(1000 * k + 1), ID_STREAM: ids.lit(br.ident)}
    every = dict(base)
    every.update({KEY_STREAM + j: ids.lit(br.keys[j]) for j in range(k)})
    short = dict(every)
    del short[KEY_STREAM + k - 1]
    return Workload(
        bits=ids.bits,
        streams=[AMOUNT, ID_STREAM] + [KEY_STREAM + j for j in range(k)],
        spec="always ( (o1[t]:bv[24] = i1[t]:bv[24]) && (%s) ).\n" % body,
        rule="always ( %s ).\n" % body,
        checks=[Check("no keys", 0, base),
                Check("all %d keys" % k, 1, every),
                Check("all but the last key", 0, short)])


def check_lines(wl: Workload, with_i0: bool) -> List[str]:
    lines: List[str] = []
    for c in wl.checks:
        if with_i0:
            lines.append("F")
        lines += [c.values.get(s, "0") for s in wl.streams]
    return lines


def stdin_spec(wl: Workload) -> str:
    return "\n".join(check_lines(wl, False)) + "\n"


def stdin_router(wl: Workload) -> str:
    head = [BASE_RULE.rstrip("\n"), wl.rule.rstrip("\n"), "0"]
    return "\n".join(head + check_lines(wl, True)) + "\n"


def stdin_reparse(wl: Workload) -> str:
    return "\n".join(check_lines(wl, True)) + "\n"



UPDATED = re.compile(r"^Updated specification(?: \(\d+ chars\))?: (.*)$", re.M)
