"""Screening a circuit's values on the bench (discrete/NOTEBOOK.md), before tuning it in closed loop: at rest, through a
single eye pulse (as a far block gives), and after it, each motor's rate and the power; then a random search for
values that behave as the best policy does (discrete/policies.py: scan with one thruster at rest, both after a pulse,
back to scanning soon after), as starts for discrete/tune.py.

    python -m discrete.screen CIRCUIT [--samples 200] [--spread 4] [--start k=v ...]
"""

from __future__ import annotations

import inspect
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from discrete.life import FALL, RISE, SUPPLY, bench  # noqa: E402

REST = (0.2, 0.6)       # s: scanning measured here, nothing seen
PULSES = (0.6, 1.2)     # s: then single pulses (a far block's) at these moments ...
HOLD = (0.01, 0.13)     # s: ... after each of which both motors should fire for this long (the policy's best hold:
                        # discrete/policies.py) ...
AFTER = (0.35, 0.6)     # s: ... and only one, scanning, by this long after the last
SEEN = (1.8, 2.2)       # s: then a near block: pulses at BURST per second, alternate eyes; both motors fast throughout
BURST = 40.0            # (frequent pulses hold the hold at its top: its current must not latch the switch on)


def firings(v, t, supply=SUPPLY):
    out, armed = [], True
    for x, tt in zip(v, t):
        if armed and x > RISE * supply:
            out.append(tt)
            armed = False
        elif x < FALL * supply:
            armed = True
    return np.array(out)


def measure(name: str, params: dict, cuts=()) -> dict:
    """Each motor's rate (per s) at rest, in the hold after a single pulse, and after; mean power at rest (W). cuts:
    parts taken out (discrete/prune.py)."""
    from discrete.prune import build
    net, supply = build(name, params, list(cuts), None)
    burst = np.arange(SEEN[0], SEEN[1], 1 / BURST)
    t, V, _ = bench(net, SEEN[1], list(dict.fromkeys(net.motor)), supply,
                    pulses=[(k, x) for k, x in enumerate(PULSES)] + [(k % 2, x) for k, x in enumerate(burst)])
    out = {}
    for m, node in enumerate(net.motor):
        f = firings(V[node], t, supply)
        n = lambda a, b: float(((f >= a) & (f < b)).sum())
        out[f"rest{m}"] = n(*REST) / (REST[1] - REST[0])
        out[f"hold{m}"] = sum(n(x + HOLD[0], x + HOLD[1]) for x in PULSES) / (len(PULSES) * (HOLD[1] - HOLD[0]))
        out[f"after{m}"] = n(PULSES[1] + AFTER[0], PULSES[1] + AFTER[1]) / (AFTER[1] - AFTER[0])
        out[f"seen{m}"] = n(SEEN[0] + 0.1, SEEN[1]) / (SEEN[1] - SEEN[0] - 0.1)
    _, _, p = bench(net, REST[1], [net.motor[0]], supply)
    out["power"] = p
    return out


def fitness(r: dict) -> float:
    """How like the best policy (hold and drive): scan on one motor at about 24 per s, the other silent; for about
    0.12 s after a single pulse, both, fast and together; after, scanning again. Higher is better; power a small
    charge (a meal per 10 s per uW, against meals of about 1 per 10 s per 10 per s of firing)."""
    scan = r["rest0"] + r["rest1"]
    f = -abs(math.log(max(scan, 1.0) / 24.0))                   # scanning at about 24 per s
    f -= min(r["rest0"], r["rest1"]) / 10.0                     # on one motor only
    both = min(r["hold0"], r["hold1"])
    f += min(math.log(max(both, 1.0) / 24.0), math.log(3.0))    # held, both fast (up to 3 times the scan) ...
    f -= abs(r["hold0"] - r["hold1"]) / max(both, 1.0)          # ... and together
    near = min(r["seen0"], r["seen1"])
    f += min(math.log(max(near, 1.0) / 24.0), math.log(3.0))    # a near block: both fast, not latched ...
    f -= abs(r["seen0"] - r["seen1"]) / max(near, 1.0)          # ... and together
    f -= abs(math.log(max(r["after0"] + r["after1"], 1.0) / max(scan, 1.0)))   # back to scanning
    f -= min(r["after0"], r["after1"]) / 10.0
    return f - r["power"] * 1e6


def _one(a):
    name, p, cuts = a if len(a) == 3 else (*a, ())
    try:
        r = measure(name, p, cuts)
        return p, r, fitness(r)
    except Exception as e:                              # noqa: BLE001
        return p, {"error": repr(e)}, -math.inf


def search(name, base: dict, cuts=(), samples=200, spread=4.0, ex=None, seed=1):
    """Random values around base (each within spread times, inside BOUNDS), screened: [(params, rates, fitness)], best
    first, base included."""
    from discrete.circuits import BOUNDS
    rng = np.random.default_rng(seed)
    cands = [base] + [{k: float(np.clip(v * spread ** rng.uniform(-1, 1), *BOUNDS[k[0]])) for k, v in base.items()}
                      for _ in range(samples)]
    jobs = [(name, c, tuple(cuts)) for c in cands]
    res = list(ex.map(_one, jobs)) if ex else [_one(j) for j in jobs]
    return sorted(res, key=lambda x: -x[2])


if __name__ == "__main__":
    import argparse
    from discrete.circuits import CIRCUITS
    ap = argparse.ArgumentParser()
    ap.add_argument("circuit")
    ap.add_argument("--samples", type=int, default=200)
    ap.add_argument("--spread", type=float, default=4.0)
    ap.add_argument("--start", nargs="*", default=[])
    ap.add_argument("--workers", type=int)
    a = ap.parse_args()
    build, _ = CIRCUITS[a.circuit]
    base = {k: p.default for k, p in inspect.signature(build).parameters.items()
            if k != "rng" and isinstance(p.default, float) and p.default}
    base.update({k: float(v) for k, v in (s.split("=") for s in a.start)})
    with ProcessPoolExecutor(a.workers) as ex:
        res = search(a.circuit, base, (), a.samples, a.spread, ex)
    for p, r, f in res[:8]:
        print(f"{f:+.2f}  " + " ".join(f"{k}={v:.3g}" for k, v in p.items()))
        print("       " + " ".join(f"{k} {v:.0f}" if k != "power" else f"power {v * 1e9:.0f} nW" for k, v in r.items()))
