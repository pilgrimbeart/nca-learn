"""Is self-tuning worth having? (discrete/NOTEBOOK.md D5): for bodies built differently (discrete/bodies.py), the hold
and drive policy's best settings for each body against the settings best for the standard body. If every body's best
is the standard's, a fixed circuit is enough; the gap is what a circuit tuning itself in its life could gain.

    python -m discrete.variation [--seeds 12] [--seconds 60] [--workers N: default one per core]
"""

from __future__ import annotations

import itertools
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from discrete.policies import judge  # noqa: E402

GRID = [dict(scan=s, drive=d, hold=h) for s, d, h in
        itertools.product((8, 16, 32, 64), (16, 40, 80, 160), (0.05, 0.1, 0.2, 0.4))]
BODIES = {"standard": {}, "weak": {"strength": 0.5}, "strong": {"strength": 2.0},
          "left-strong": {"asymmetry": 1.25}, "right-strong": {"asymmetry": 0.8},
          "dim eyes": {"eyes": 0.5}, "bright eyes": {"eyes": 2.0},
          "slippery": {"drag": 0.67}, "sticky": {"drag": 1.5}}

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--seconds", type=float, default=60.0)
    ap.add_argument("--workers", type=int)
    a = ap.parse_args()
    seeds = range(4000, 4000 + a.seeds)
    out = {}
    with ProcessPoolExecutor(a.workers) as ex:
        for name, body in BODIES.items():
            res = [(p, judge("hold_drive", p, seeds, a.seconds, ex, body)) for p in GRID]
            out[name] = [(p, r["eff"], r["gain"]) for p, r in res]
            best = max(res, key=lambda x: x[1]["eff"])
            print(f"{name:13s} best {best[0]} eff {best[1]['eff']:.2f} gain {best[1]['gain']:.1f}", flush=True)
    std = max(out["standard"], key=lambda x: x[1])[0]
    print(f"\nthe standard body's best, {std}, on each body, against that body's own best (efficiency):")
    for name, rows in out.items():
        own = max(rows, key=lambda x: x[1])
        mine = next(r for r in rows if r[0] == std)
        print(f"  {name:13s} {mine[1]:5.2f} against {own[1]:5.2f} ({own[0]}): {100 * (own[1] - mine[1]) / own[1]:3.0f}% lost")
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "results", "variation.json"), "w"), indent=0)
