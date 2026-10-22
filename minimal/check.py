"""The last honesty check for the minimal circuit search (minimal/NOTEBOOK.md): a design's lives in the real
creature.Life (not fastlife), at the usual integration step and at half of it, on held-out seeds, at each noise level
judged (spec.JUDGED; mismatch is the simulator's own). A design that leans on the step (an Euler artefact) changes when
the step does.

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
    spec, seed, poison, ticks, dt, noise = job
    import mixed_feedback as mf
    from creature import Life
    from minimal.spec import Lived, make
    mf.DT = dt
    lf = Life(seed, poison, brain=make(spec, noise))
    while lf.t < ticks:
        lf.step()
    start = lf.moving if lf.moving is not None else ticks
    out = []
    for i in range(3):
        a, z = start + i * (ticks - start) / 3, start + (i + 1) * (ticks - start) / 3
        part = [c for t, c in lf.meals if a <= t < z]
        out.append((sum(c != poison for c in part), sum(c == poison for c in part), z - a))
    lived = Lived(out + [(0, 0, start)])
    c = lf.brain.circuit
    lived.power = c.energy / max(c.steps, 1)
    lived.firings, lived.noise = 1000 * len(lf.firings) / ticks, noise
    return lived


def fine(spec, seeds=range(200, 216), ticks=10000):
    from minimal.spec import JUDGED, summary
    out = {}
    with ProcessPoolExecutor(mp_context=multiprocessing.get_context("spawn")) as pool:
        for dt in (0.05, 0.025):
            jobs = [(spec, s, p, ticks, dt, nz) for nz in JUDGED for s in seeds for p in ("red", "blue")]
            out[dt] = summary(list(pool.map(one, jobs)))
    return out


if __name__ == "__main__":
    from minimal.designs import DESIGNS
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--seeds", type=int, default=16)
    a = ap.parse_args()
    r = json.load(open(a.results))
    spec = r["spec"] if "spec" in r else DESIGNS[r["design"]][0](r["params"])
    name = os.path.basename(a.results)[:-5]
    for dt, v in fine(spec, seeds=range(200, 200 + a.seeds)).items():
        print(f"{name} step {dt}: score {v['net']:+.2f} (the worst level), job {v['job']}, food {v['food']:.2f},"
              f" poison {v['poison']:.2f}, last third {v['last']:.2f}, stranded {v['stranded']:.0%}, power {v['power']:.2f}")
        for k, w in v.get("by_noise", {}).items():
            print(f"  x{k} noise: score {w['net']:+.2f}, last third {w['last']:.2f}, stranded {w['stranded']:.0%},"
                  f" job {w['job']}")
