"""E2, frustration (experiments/NOTEBOOK.md): does the frustration node F signal "my predictions don't prevent pain",
and only that? Growth off; what would have grown is recorded (the first sprout to reach the growth level).

    python -m experiments.e2_frustration [LIVES]
"""

import functools
import pickle
import sys

import numpy as np

from brains.recruiting import RecruitingBrain
from experiments.common import E3, SAMPLE, run
from units import T_TYP

FIRST = [("A guard, learning", dict(guard=3 * T_TYP, frustrate=0.1)),
         ("B no guard, learning", dict(guard=0.0, frustrate=0.1)),
         ("C guard, no learning", dict(guard=3 * T_TYP, frustrate=0.1, learn=False)),
         ("D no guard, no learning", dict(guard=0.0, frustrate=0.1, learn=False))]
SECOND = [("E recalibrated, learning", dict()), ("F recalibrated, no learning", dict(learn=False))]   # (E2b)
CONDITIONS = SECOND if "--second" in sys.argv else FIRST


def describe(records):
    F = np.array([r["F"] for r in records])                     # lives x samples
    at = lambda seconds: F[:, int(round(seconds / SAMPLE)) - 1].mean()
    over = [next((i + 1) * SAMPLE for i, f in enumerate(r["F"]) if f > 0.5) if max(r["F"]) > 0.5 else None
            for r in records]
    hit = [t for t in over if t is not None]
    first = [r["crossed"][0] if r["crossed"] else None for r in records]
    who = {}
    for f in first:
        if f:
            who[f[1]] = who.get(f[1], 0) + 1
    hp = [np.mean([h.get("poison", h.get("red", 0)) for h, f in zip(r["help"], r["F"]) if f > 0.5] or [np.nan])
          for r in records]
    hf = [np.mean([h.get("food", h.get("blue", 0)) for h, f in zip(r["help"], r["F"]) if f > 0.5] or [np.nan])
          for r in records]
    return (f"F at 10 / 30 / 100 s {at(10):.2f} / {at(30):.2f} / {at(100):.2f}; F > 0.5 in "
            f"{len(hit)} of {len(records)} lives" + (f" (median first at {np.median(hit):.0f} s)" if hit else "") +
            f"; help while F > 0.5: poison's sensor {np.nanmean(hp):.2f}, food's {np.nanmean(hf):.2f}" +
            f"; first sprout to reach growth: {who or 'none'}" +
            (f" at median {np.median([f[0] for f in first if f]):.1f} s" if any(first) else ""))


if __name__ == "__main__":
    lives = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 64
    results = {}
    for name, kw in CONDITIONS:
        make = functools.partial(RecruitingBrain, grow=False, **{**E3, **kw})
        poison, food = run(make, lives), run(make, lives, all_food=True)
        results[name] = (poison, food)
        print(f"{name:24s} poison lives: {describe(poison)}", flush=True)
        print(f"{'':24s} all-food lives: {describe(food)}", flush=True)
    pickle.dump(results, open(f"experiments/results/e2{'b' if CONDITIONS is SECOND else ''}.pkl", "wb"))
