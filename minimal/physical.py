"""Could it be built? A finger-in-the-air check of a circuit against what a chip can do (the user's question,
2026-10-22): every capacitor, resistor, time constant and current in real units, the chip's limits from units.py's
axioms (the largest resistance a design can set, R_MAX; the largest capacitor, C_MAX; the slowest time constant without
a floating gate, TAU_MAX; the smallest usable bias current, I_MIN), and the area (minimal/spec.py). Not a rule: a
design past a limit is flagged, not refused.

    python -m minimal.physical RESULTS.json [...]
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from minimal.spec import area, parts  # noqa: E402
from units import C_MAX, I_MIN, MICRO, R_MAX, TAU_MAX, UNIT_AREA, si  # noqa: E402


def values(spec: dict) -> dict:
    """The circuit's parts in real units: (name, value) lists of capacitors, resistors, time constants and currents."""
    names = [n[0] for n in spec["nodes"]]
    C = [(n[0], n[3]) for n in spec["nodes"]]
    R = [(n[0], n[2]) for n in spec["nodes"] if n[2] is not None]
    tau = [(f"{n[0]} leak", n[2] * n[3]) for n in spec["nodes"] if n[2] is not None]
    tau += [(f"{names[e[0]]}<-{names[e[1]]} filter", e[6]) for e in spec["elements"] if e[6] > 0]
    I = [(f"{names[e[0]]}<-{names[e[1]]}", abs(e[3])) for e in spec["elements"] if e[3]]
    return {"C": C, "R": R, "tau": tau, "I": I}


def flags(spec: dict) -> list:
    """What a chip couldn't easily do: each part past a limit (with the rules' rounding tolerance, minimal/spec.py)."""
    v, out = values(spec), []
    out += [f"capacitor {k} {si(c, 'F')} above {si(C_MAX, 'F')}" for k, c in v["C"] if c > C_MAX * (1 + 1e-9)]
    out += [f"resistor {k} {si(r, 'Ω')} above {si(R_MAX, 'Ω')} (its bias current below {si(I_MIN, 'A')})"
            for k, r in v["R"] if r > R_MAX * (1 + 1e-9)]
    out += [f"time constant {k} {si(t, 's')} above {si(TAU_MAX, 's')} (needs a floating gate)" for k, t in v["tau"]
            if t > TAU_MAX * (1 + 1e-9)]
    out += [f"current {k} {si(i, 'A')} below {si(I_MIN, 'A')}" for k, i in v["I"] if i < I_MIN * (1 - 1e-9)]
    return out


def report(name: str, spec: dict) -> str:
    v = values(spec)
    span = lambda xs, unit: f"{si(min(x for _, x in xs), unit)} to {si(max(x for _, x in xs), unit)}" if xs else "none"
    a = area(spec)
    f = flags(spec)
    return (f"{name}: {parts(spec)['total']} parts; capacitors {span(v['C'], 'F')}, resistors {span(v['R'], 'Ω')},"
            f" time constants {span(v['tau'], 's')}, currents {span(v['I'], 'A')}; area {a:.0f} unit transistors"
            f" ({a * UNIT_AREA / MICRO ** 2 / 1e6:.3f} mm²)\n"
            + ("  buildable within units.py's chip limits" if not f else "".join(f"  past a limit: {x}\n" for x in f)
               .rstrip()))


if __name__ == "__main__":
    for path in sys.argv[1:]:
        print(report(os.path.basename(path)[:-5], json.load(open(path))["spec"]))
