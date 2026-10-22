"""Circuits for the minimal circuit search (minimal/NOTEBOOK.md) made by hand, and any circuit as a family of its own
parameters (raw, for polishing). Values in SI (units.py). Every design found so far is stored whole in
minimal/results/ (the families of parameters the first designs were tuned in, A, G and C, were retired on
2026-10-22 when everything moved to SI: each of their results is stored as its circuit).
"""

from __future__ import annotations

import copy
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from units import C_TYP, I_TYP, R_TYP, RAIL, T_TYP  # noqa: E402


def from_brain(cls, seed: int = 0) -> dict:
    """The spec of an existing circuit brain (for comparison: its parts and its score here)."""
    b = cls(seed)
    c = b.circuit
    nodes = [[c.names[i], bias, None if leak == 0 else 1.0 / leak, C, lo, hi, c.start[i], w > 0]
             for i, (bias, leak, C, lo, hi, w) in enumerate(c.nodes)]
    els = [[to, frm, gate, g, o, s, ta, sg] for (g, o, s, ta, sg), (to, frm, gate) in c.elements]
    return {"nodes": nodes, "elements": els, "sensors": list(b.sensors), "motors": list(b.motors),
            "taste": b.taste_node, "units": "SI"}


def hungry(spec: dict, tau: float = 8700 * T_TYP, C: float = 8.7 * C_TYP, rest: float = 1.0) -> dict:
    """A hunger added to a circuit (minimal/NOTEBOOK.md, M8): a node H charging towards rest (V) over tau (s), drained by
    a good taste (an element from the taste node, its step at 1.5 V, well above the taste node's rest, so it doesn't
    leak at rest), and an element from the clock (motor 1) into motor 0 gated by H, so that while H is high both
    thrusters fire together and the spin becomes a straight run. The reads become tanh, so the colour the bit calls
    poison holds motor 0 down (a hungry run stops at poison). 5 parts more."""
    s = copy.deepcopy(spec)
    M0, M1 = s["motors"]
    T = s["taste"]
    R = tau / C
    H = len(s["nodes"])
    s["nodes"].append(["H", rest / R, R, C, None, None, None, False])
    for e in s["elements"]:
        if e[0] == M0 and e[2] in s["sensors"]:
            e[7] = False                                # a read: tanh
    s["elements"].append([H, T, -1, -20 * I_TYP, 1.5, 10.0, 0.0, True])        # a good taste drains H
    s["elements"].append([M0, M1, H, 3 * I_TYP, 0.0, 5.0, 0.0, True])          # hungry: the clock drives motor 0 too
    return s


HOLD_ROAM = dict(ma_bias=0.0, ma_tau=20 * T_TYP, ma_slow=-4 * I_TYP, mb_bias=-2.6 * I_TYP, syn=3 * I_TYP,
                 g_C=4 * C_TYP, g_tau=200 * T_TYP, g_rest=-1.5, g_gain=4 * I_TYP, r_C=8 * C_TYP, r_tau=300 * T_TYP,
                 r_rest=2.5, r_th=1.0, r_gain=2 * I_TYP, r_drain=-8 * I_TYP)


def hold_roam(senses: dict, p: dict = HOLD_ROAM) -> dict:
    """The hold-and-roam circuit (minimal/NOTEBOOK.md, M11; HR_35p): the senses and memory of a spinning circuit
    (`senses`, EF_22p's: sensors S0, S1, taste T, the bit m, its two writes and two reads), its motor stage replaced.
    MA, an oscillator on one motor (fast positive feedback and a strong slow negative one, so its rate barely depends
    on mismatch), scans; G, a hold node (time constant g_tau), is charged by a sighting of the colour the bit calls food
    and drained by the other's, through the reads; MB, an excitable node on the other motor, copies MA's spikes while G
    is open, so both thrusters fire together and the creature goes straight; and Rt, a roam timer, fills while G is
    shut and, when full, opens G (a sharp drain: a sigmoid's tail at rest would match its charging current)."""
    S0, S1, _, _, T, m = copy.deepcopy(senses["nodes"])
    e = senses["elements"]
    gR, rR = p["g_tau"] / p["g_C"], p["r_tau"] / p["r_C"]
    nodes = [S0, S1, T, m,
             ["G", p["g_rest"] / gR, gR, p["g_C"], None, None, None, False],
             ["MA", p["ma_bias"], 2 * R_TYP, C_TYP, None, None, None, False],
             ["MB", p["mb_bias"], 2 * R_TYP, C_TYP, None, None, None, False],
             ["Rt", p["r_rest"] / rR, rR, p["r_C"], None, None, None, False]]
    iS0, iS1, iT, im, iG, iA, iB, iR = range(8)
    elements = [
        [im, iS0, iT, *e[3][3:]],                                   # the writes
        [im, iS1, iT, *e[4][3:]],
        [iG, im, iS0, p["g_gain"], e[1][4], e[1][5], 0.0, False],   # the reads: approach if food, retreat if poison
        [iG, im, iS1, p["g_gain"] * e[2][3] / e[1][3], e[2][4], e[2][5], 0.0, False],
        [iA, iA, -1, 2 * I_TYP, -1.5, 1.0, 0.0, False],             # MA: the scan
        [iA, iA, -1, p["ma_slow"], -1.5, 1.0, p["ma_tau"], False],
        [iB, iB, -1, 2 * I_TYP, -1.5, 1.0, 0.0, False],             # MB: excitable, silent alone
        [iB, iB, -1, -2 * I_TYP, -1.5, 1.0, 10 * T_TYP, False],
        [iB, iA, iG, p["syn"], 0.0, 5.0, 0.0, True],                # ... copying MA's spikes while G is open
        [iG, iR, -1, p["r_gain"], p["r_th"], 4.0, 0.0, True],       # the timer full: open G
        [iR, iG, -1, p["r_drain"], 1.0, 8.0, 0.0, True],            # G open: empty the timer
    ]
    return {"nodes": nodes, "elements": elements, "sensors": [iS0, iS1], "motors": [iA, iB], "taste": iT, "units": "SI"}


BOUNDS = {"C": (0.05 * C_TYP, 100 * C_TYP), "R": (0.1 * R_TYP, 1000 * R_TYP), "gain": 20 * I_TYP,
          "slope": (0.5, 30.0), "tau": (0.5 * T_TYP, 300 * T_TYP), "rest": RAIL - 0.1, "offset": 3.0}
                    # where a search may take a circuit's values: about the typical sizes (units.py), the rests and
                    # offsets in volts, within the rails


def raw(spec: dict):
    """(design, params) for a raw spec: its numbers as parameters, each searched within a factor of 4 of where it is
    (offsets and rests +-1.5 V), inside BOUNDS."""
    params = {}
    for i, n in enumerate(spec["nodes"]):
        if n[2] is not None:
            rest = n[1] * n[2]
            params[f"n{i}_rest"] = (rest, max(rest - 1.5, -BOUNDS["rest"]), min(rest + 1.5, BOUNDS["rest"]))
            params[f"n{i}_R"] = (n[2], max(n[2] / 4, BOUNDS["R"][0]), min(n[2] * 4, BOUNDS["R"][1]))
        elif n[6] is not None:
            params[f"n{i}_start"] = (n[6], 0.0, 1.0)
        params[f"n{i}_C"] = (n[3], max(n[3] / 4, BOUNDS["C"][0]), min(n[3] * 4, BOUNDS["C"][1]))
    for j, e in enumerate(spec["elements"]):
        g = e[3]
        params[f"e{j}_gain"] = (g, g * 4 if g < 0 else g / 4, g / 4 if g < 0 else g * 4) if g else (0.0, -I_TYP, I_TYP)
        params[f"e{j}_off"] = (e[4], e[4] - 1.5, e[4] + 1.5)
        params[f"e{j}_slope"] = (e[5], max(e[5] / 4, 0.1), min(e[5] * 4, BOUNDS["slope"][1]))
        if e[6] > 0:
            params[f"e{j}_tau"] = (e[6], max(e[6] / 4, BOUNDS["tau"][0]), min(e[6] * 4, BOUNDS["tau"][1]))
    params = {k: (v, min(lo, hi), max(lo, hi)) for k, (v, lo, hi) in params.items()}

    def design(p: dict) -> dict:
        s = copy.deepcopy(spec)
        for i, n in enumerate(s["nodes"]):
            if n[2] is not None:
                n[2] = p[f"n{i}_R"]
                n[1] = p[f"n{i}_rest"] / n[2]
            elif n[6] is not None:
                n[6] = p[f"n{i}_start"]
            n[3] = p[f"n{i}_C"]
        for j, e in enumerate(s["elements"]):
            e[3], e[4], e[5] = p[f"e{j}_gain"], p[f"e{j}_off"], p[f"e{j}_slope"]
            if e[6] > 0:
                e[6] = p[f"e{j}_tau"]
        return s
    return design, params


if __name__ == "__main__":
    from brains.designed import DesignedBrain
    from minimal.spec import parts, score, summary
    s = from_brain(DesignedBrain)
    r = summary(score([s], seeds=range(16))[0])
    print(f"designed circuit: parts {parts(s)}  score {r['net']:+.2f} [{r['lo']:+.2f}, {r['hi']:+.2f}]  food"
          f" {r['food']:.2f}  poison {r['poison']:.2f}  last third {r['last']:.2f}  job {r['job']}")
