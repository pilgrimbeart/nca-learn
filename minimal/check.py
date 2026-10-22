"""The last honesty check for the minimal circuit search (minimal/NOTEBOOK.md): a design's lives in the real
creature.Life (not fastlife), at the usual integration step and at half of it, on held-out seeds, with each substrate
judged (spec.JUDGED; mismatch is the simulator's own). A design that leans on the step (an
Euler artefact) changes when the step does.

    python -m minimal.check RESULTS_FILE [--seeds 16]
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import sys
from concurrent.futures import ProcessPoolExecutor


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def one(job):
    spec, seed, poison, seconds, dt, substrate = job
    import mixed_feedback as mf
    from creature import Life
    from minimal.spec import SPAN, Lived, make, thirds
    from units import TICK
    mf.DT = dt
    ticks = int(round(seconds / TICK))
    lf = Life(seed, poison, brain=make(spec, substrate))
    while lf.t < ticks:
        lf.step()
    lived = Lived(thirds(lf.meals, lf.moving, ticks, poison))
    lived.power = lf.brain.circuit.power()
    lived.firings, lived.substrate = SPAN * len(lf.firings) / seconds, substrate
    return lived


def fine(spec, seeds=range(200, 216), seconds=None):
    from minimal.spec import JUDGED, LIFE, summary
    from units import DT
    out = {}
    with ProcessPoolExecutor(mp_context=multiprocessing.get_context("spawn")) as pool:
        for dt in (DT, DT / 2):
            jobs = [(spec, s, p, seconds or LIFE, dt, sb) for sb in JUDGED for s in seeds for p in ("red", "blue")]
            out[dt] = summary(list(pool.map(one, jobs)))
    return out


if __name__ == "__main__":
    from units import si
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--seeds", type=int, default=16)
    a = ap.parse_args()
    r = json.load(open(a.results))
    spec = r["spec"]
    name = os.path.basename(a.results)[:-5]
    for dt, v in fine(spec, seeds=range(200, 200 + a.seeds)).items():
        print(f"{name} step {si(dt, 's')}: score {v['net']:+.2f} (the worst substrate), job {v['job']}, food"
              f" {v['food']:.2f}, poison {v['poison']:.2f}, last third {v['last']:.2f}, stranded {v['stranded']:.0%},"
              f" power {si(v['power'], 'W')}")
        for k, w in v.get("by_substrate", {}).items():
            print(f"  {k}: score {w['net']:+.2f}, last third {w['last']:.2f}, stranded {w['stranded']:.0%},"
                  f" job {w['job']}")
