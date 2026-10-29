"""A circuit's blocks on SPICE's bench, as the numbers the fast model takes (discrete/model.py; NOTEBOOK.md, D13):
short runs of known pulses, one seed's tolerances each, no body.

    python -m discrete.blocks SEEDS [OUT.json] [k=v ...]   # e.g. 0:32: circuit B on those seeds, 8 at a time

Bench runs and closed-loop lives can't share a process (AGENTS.md), so each seed is benched in a process of its own.
The 32 seeds circuit B was benched on: results/cmos_b_bench.json."""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

H = 0.9                                                 # V: a logic node high above it


def bench_b(seed=None, **values) -> dict:
    """Circuit B's numbers on the bench for one seed's tolerances (None: nominal): the drive's hold after the last food
    pulse (s), boredom (s), the beat rates (per s) in scan, drive and run, doubt's step up for a poison and down for a
    food (V), its drift (V/s), the threshold V_H and the reset V_L (V), and the power (nW)."""
    from discrete.cmos import cmos_b
    from discrete.life import bench
    n = cmos_b(None if seed is None else np.random.default_rng(int(seed) + 5_000_011), **values)
    t, V, _ = bench(n, 0.3, ["q"], supply=1.8, step=2e-4)
    food = 0 if V["q"][-1] < H else 1                   # the eye the bit says is food
    pul = [(food, 4.0 + 0.02 * k) for k in range(10)]   # a train, then nothing: drive hold, boredom
    pul += [("poison", 20.0), ("poison", 20.5), ("food", 21.5)]   # doubt: two steps up, one down
    pul += [("poison", 23.0), ("poison", 23.4), ("poison", 23.8)]  # to the threshold: the flip and reset
    nodes = ["dn", "run", "m0", "m1", "dq", "T", "q"]
    t, V, p = bench(n, 26.0, nodes, pulses=pul, supply=1.8, step=2e-4)
    lo = {k: V[k] < H for k in nodes}

    def first(cond, a):
        m = (t >= a) & cond
        return float(t[m][0]) if m.any() else None

    def rate(v, a, b):
        w, c, arm = v[(t >= a) & (t < b)], 0, True
        for x in w:
            if arm and x > 1.2:
                c, arm = c + 1, False
            elif x < 0.6:
                arm = True
        return c / (b - a)

    d = V["dq"]
    at = lambda x: float(d[np.searchsorted(t, x)])
    out = dict(seed=seed, power_nW=p * 1e9)
    out["hold"] = first(~lo["dn"], 4.181) - 4.18
    out["bored"] = first(~lo["run"], 4.2) - 4.18
    rs = first(~lo["run"], 4.2)
    out["run"] = rate(V["m1"], rs + 0.1, 19.9) if rs and rs < 19 else None
    out["drive"] = rate(V["m1"], 4.0, 4.18)
    out["scan"] = rate(V["m0"], 4.5, 4.18 + out["bored"] - 0.2)
    out["step"] = at(20.05) - at(19.95)
    out["fstep"] = at(21.45) - at(21.55)
    out["drift"] = (at(20.1) - at(20.45)) / 0.35
    tr = np.flatnonzero(np.diff(lo["T"].astype(int)) == -1)     # T rising: the flip
    tr = tr[t[tr] > 22.9]
    if len(tr):
        tf = first(lo["T"], float(t[tr[0]]) + 1e-4)
        out["V_L"] = at(tf + 0.001) if tf else None
    out["flipped"] = bool(lo["q"][np.searchsorted(t, 22.9)] != lo["q"][np.searchsorted(t, 25.9)])
    n.lines.append("I_ramp 0 dq dc 1.5e-11")            # the threshold: dq ramped slowly up (1.1 V/s)
    t2, V2, _ = bench(n, 2.5, ["dq", "T"], supply=1.8, step=2e-4)
    k = np.flatnonzero((t2 > 0.5) & (V2["T"] > H))
    out["V_H"] = float(V2["dq"][k[0]]) if len(k) else None
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in out.items()}


def _one(a):
    seed, values = a
    return bench_b(seed, **values)


if __name__ == "__main__":
    lo, hi = (int(x) for x in sys.argv[1].split(":"))
    out = next((a for a in sys.argv[2:] if a.endswith(".json")), None)
    values = {k: float(v) for k, v in (a.split("=") for a in sys.argv[2:] if "=" in a)}
    with ProcessPoolExecutor(8, max_tasks_per_child=1) as ex:
        rows = list(ex.map(_one, [(s, values) for s in range(lo, hi)]))
    for r in rows:
        print(json.dumps(r))
    if out:
        json.dump({"values": values, "seeds": rows}, open(out, "w"), indent=1)
