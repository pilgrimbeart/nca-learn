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

from units import C_MAX, C_TYP, I_TYP, R_MAX, R_TYP, RAIL, T_TYP, TAU_MAX, V_TYP  # noqa: E402


def rescale(spec: dict, volt: float = V_TYP) -> dict:
    """A copy of spec drawn at another typical voltage (units.V_TYP; a spec says its own in "volt", the designs before
    2026-10-26 at 1 V): the same behaviour, every voltage scaled by s = volt / spec's (offsets, rests, clamps, starts;
    slopes by 1 / s), and every current into a node by s too, the body's pulses included (they are typical currents of
    the technology: brains.circuit.PULSES), at the same capacitance, resistance and time constants, so that power falls
    as s^2. (Biology's noise scales with the voltage too, so the lives are the same but for silicon's.)"""
    sp = copy.deepcopy(spec)
    s = volt / spec.get("volt", 1.0)
    k = [s] * len(sp["nodes"])                          # each node's currents scale by k
    for i, n in enumerate(sp["nodes"]):
        n[1] *= k[i]
        if n[2] is not None:
            n[2] *= s / k[i]
        n[3] *= k[i] / s
        for j in (4, 5, 6):
            if n[j] is not None:
                n[j] *= s
    for e in sp["elements"]:
        e[3] *= k[e[0]]
        e[4] *= s
        e[5] /= s
    sp["volt"] = volt
    return sp


def from_brain(cls, seed: int = 0) -> dict:
    """The spec of an existing circuit brain (for comparison: its parts and its score here)."""
    b = cls(seed)
    c = b.circuit
    nodes = [[c.names[i], bias, None if leak == 0 else 1.0 / leak, C, lo, hi, c.start[i], w > 0]
             for i, (bias, leak, C, lo, hi, w) in enumerate(c.nodes)]
    els = [[to, frm, gate, g, o, s, ta, sg] for (g, o, s, ta, sg), (to, frm, gate) in c.elements]
    return rescale({"nodes": nodes, "elements": els, "sensors": list(b.sensors), "motors": list(b.motors),
                    "taste": b.taste_node, "units": "SI", "volt": c.volt})


BOUNDS = {"C": (0.05 * C_TYP, C_MAX), "R": (0.1 * R_TYP, R_MAX), "gain": 20 * I_TYP,
          "slope": (0.5 / V_TYP, 30.0 / V_TYP), "tau": (0.5 * T_TYP, min(300 * T_TYP, TAU_MAX)),
          "rest": RAIL - 0.1 * V_TYP, "offset": 3.0 * V_TYP}
                    # where a search may take a circuit's values: about the typical sizes (units.py), within a chip's
                    # limits (C_MAX, R_MAX, TAU_MAX), the rests and offsets within the rails


def on_chip(spec: dict) -> dict:
    """A copy of spec with every leak above R_MAX brought down to it, its node's capacitance, bias and the currents into
    it raised by the same factor: the same voltages and time constants (the node only quieter, being bigger), so a
    design from before the chip's limits became a rule (2026-10-23) can carry on from where it was."""
    s = copy.deepcopy(spec)
    for i, nd in enumerate(s["nodes"]):
        if nd[2] is not None and nd[2] > R_MAX:
            k = nd[2] / R_MAX
            nd[1], nd[2], nd[3] = nd[1] * k, R_MAX, nd[3] * k
            for e in s["elements"]:
                if e[0] == i:
                    e[3] *= k
    return s


def raw(spec: dict):
    """(design, params) for a raw spec: its numbers as parameters, each searched within a factor of 4 of where it is
    (offsets and rests 1.5 typical voltages), inside BOUNDS."""
    params = {}
    for i, n in enumerate(spec["nodes"]):
        if n[2] is not None:
            rest = n[1] * n[2]
            params[f"n{i}_rest"] = (rest, max(rest - 1.5 * V_TYP, -BOUNDS["rest"]), min(rest + 1.5 * V_TYP, BOUNDS["rest"]))
            params[f"n{i}_R"] = (n[2], max(n[2] / 4, BOUNDS["R"][0]), min(n[2] * 4, BOUNDS["R"][1]))
        elif n[6] is not None:
            params[f"n{i}_start"] = (n[6], 0.0, V_TYP)
        params[f"n{i}_C"] = (n[3], max(n[3] / 4, BOUNDS["C"][0]), min(n[3] * 4, BOUNDS["C"][1]))
    for j, e in enumerate(spec["elements"]):
        g = e[3]
        params[f"e{j}_gain"] = (g, g * 4 if g < 0 else g / 4, g / 4 if g < 0 else g * 4) if g else (0.0, -I_TYP, I_TYP)
        params[f"e{j}_off"] = (e[4], e[4] - 1.5 * V_TYP, e[4] + 1.5 * V_TYP)
        params[f"e{j}_slope"] = (e[5], max(e[5] / 4, 0.1 / V_TYP), min(e[5] * 4, BOUNDS["slope"][1]))
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
