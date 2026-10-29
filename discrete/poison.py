"""Discrete circuits with something to learn (discrete/NOTEBOOK.md D6): each seed lived twice, red then blue as poison
(the same world and parts), judged as minimal/spec.py judges every brain that faces poison (summary: efficiency, gain
rate, food:poison in the last third, stranding, the job, each with its 95% interval). A circuit that ignores taste
nets below 0.

    python -m discrete.poison CIRCUIT [--seeds 0:8] [--seconds 100] [--workers N: default one per core] [--set k=v ...] [--finer F]
        [--out F.lives]

Held out: --seeds 50000:50032 (discrete/judge.py's HELD_OUT).
"""

from __future__ import annotations

import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from discrete.life import STEP, lived, live  # noqa: E402


def _one(a):
    name, params, seed, seconds, poison, *finer = a
    from discrete.circuits import CIRCUITS
    build, supply = CIRCUITS[name]
    net = build(np.random.default_rng(seed + 5_000_011), **params)
    step = STEP / (finer[0] if finer else 1)
    return lived(live(net, seed, seconds, supply, poison=poison, step=step), seconds, poison)


def judge(name, params, seeds, seconds=100.0, workers=None, finer=1):
    """The paired lives (red, then blue as poison, on each seed) and their summary (finer: life.STEP divided)."""
    from minimal.spec import summary
    with ProcessPoolExecutor(workers) as ex:
        lives = list(ex.map(_one, [(name, params, s, seconds, c, finer) for s in seeds for c in ("red", "blue")]))
    return summary(lives), lives


def show(name, s) -> str:
    ci = s["ci"]
    return (f"{name}: efficiency {s['efficiency']:.2f} [{ci['efficiency'][0]:.2f}, {ci['efficiency'][1]:.2f}]  gain "
            f"{s['gain']:.2f}  food {s['food']:.2f}  poison {s['poison']:.2f}  last third {s['last']:.2f} "
            f"[{ci['last'][0]:.2f}, {ci['last'][1]:.2f}]  stranded {s['stranded']:.0%}  firings {s['firings']:.0f}"
            f"  power {s['power'] * 1e9:.0f} nW  job {s['job']}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("circuit")
    ap.add_argument("--seeds", default="0:8")
    ap.add_argument("--seconds", type=float, default=100.0)
    ap.add_argument("--workers", type=int)
    ap.add_argument("--set", nargs="*", default=[])
    ap.add_argument("--finer", type=float, default=1, help="divide SPICE's largest step by this (a result must hold)")
    ap.add_argument("--out", default=None, help="keep the lives here (a pickle, for discrete.judge --compare)")
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.seeds.split(":"))
    params = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    s, lives = judge(a.circuit, params, range(lo, hi), a.seconds, a.workers, a.finer)
    print(show(a.circuit, s))
    if a.out:
        import pickle
        pickle.dump(lives, open(a.out, "wb"))
