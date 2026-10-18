"""Shared by the rung-1 experiments (experiments/NOTEBOOK.md): run lives of a brain in parallel, in poison lives (half
red, half blue: each seed run once with each, so a brain that ignores taste scores exactly 1.0) and all-food lives,
and summarise them with bootstrap 95% confidence intervals over lives.
"""

from __future__ import annotations

import multiprocessing
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from creature import COLOURS, Life  # noqa: E402

TICKS = 10000
# the recruiting brain as E2-E3 ran it (before the defaults became E6's R4), pinned for reproducibility
E3 = dict(sharp=False, once=False, frustrate=0.3, grow_at=0.8, hold="T")
SAMPLE = 100        # ticks between samples of a brain's slow nodes


def one(job):
    """(make, seed, poison, ticks, setup) -> a record of the life: meals by third after moving, bridges grown (when,
    on whose sensor, to which motor), samples of frustration and help, and the taste neuron's synapses at the end."""
    make, seed, poison, ticks, setup = job
    lf = Life(seed, poison, brain=make)
    b = lf.brain
    if setup is not None:
        setup(lf)
    role = {b.sensors[lf.sensor[c]]: ("poison" if c == poison else "food") if poison else c for c in COLOURS}
    F, H, crossed = [], [], {}
    while lf.t < ticks:
        lf.step()
        if getattr(lf, "schedule", None) and lf.t == lf.schedule[0]:     # an intervention at a given tick
            lf.schedule[1](lf)
        for (s, m), x in getattr(b, "sprout", {}).items():     # when each sprout first reached the growth level
            if (s, m) not in crossed and b.circuit.V[x] > b.grow_at:
                crossed[(s, m)] = lf.t
        if lf.t % SAMPLE == 0 and hasattr(b, "F"):
            F.append(float(b.circuit.V[b.F]))
            H.append({role[s]: float(b.circuit.V[h]) for s, h in b.help.items()})
    start = lf.moving if lf.moving is not None else ticks
    thirds = []
    for i in range(3):
        a, z = start + i * (ticks - start) / 3, start + (i + 1) * (ticks - start) / 3
        part = [c for t, c in lf.meals if a <= t < z]
        thirds.append((sum(c != poison for c in part), sum(c == poison for c in part), z - a))
    return {"thirds": thirds,
            "bridges": [(t, role[s], b.circuit.names[m]) for t, s, m in getattr(b, "bridges", [])],
            "F": F, "help": H,
            "crossed": sorted((t, role[s], b.circuit.names[m]) for (s, m), t in crossed.items()),
            "W": {role[s]: float(b.circuit.V[w]) for s, w in b.W.items()} if hasattr(b, "W") else {}}


def run(make, lives=64, ticks=TICKS, all_food=False, setup=None, first_seed=0):
    """lives lives of the brain make builds (a name, or a function from the seed to a brain); setup(life), if given,
    runs once after birth (an experimenter's intervention, such as an oracle placing a bridge). first_seed: where the
    seeds start (held-out lives, for confirming a choice made on others)."""
    jobs = [(make, first_seed + i // 2, None if all_food else COLOURS[i % 2], ticks, setup) for i in range(lives)]
    with ProcessPoolExecutor(mp_context=multiprocessing.get_context("spawn")) as pool:
        return list(pool.map(one, jobs))


def ratio_ci(records, third=None, boots=2000, seed=0):
    """Food:poison (over the given third, or the whole life after moving) and its bootstrap 95% interval over lives."""
    pick = (lambda r: r["thirds"]) if third is None else (lambda r: [r["thirds"][third]])
    food = np.array([sum(f for f, _, _ in pick(r)) for r in records], dtype=float)
    bad = np.array([sum(p for _, p, _ in pick(r)) for r in records], dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(len(records), size=(boots, len(records)))
    with np.errstate(divide="ignore", invalid="ignore"):
        boot = food[idx].sum(1) / bad[idx].sum(1)
    est = food.sum() / bad.sum() if bad.sum() else np.inf
    return est, np.nanpercentile(boot, 2.5), np.nanpercentile(boot, 97.5)


def rates(records):
    """Food and poison eaten per 1,000 ticks after moving (all of each life)."""
    food = sum(f for r in records for f, _, _ in r["thirds"])
    bad = sum(p for r in records for _, p, _ in r["thirds"])
    t = sum(t for r in records for _, _, t in r["thirds"])
    return 1000 * food / t, 1000 * bad / t


def summary(name, records, all_food=False):
    """One line: rates, and food:poison (whole life, and last third) with intervals; or, in all-food lives, food per
    1,000 ticks. Plus bridges grown."""
    food, bad = rates(records)
    grown = [b for r in records for b in r["bridges"]]
    where = {}
    for _, who, _ in grown:
        where[who] = where.get(who, 0) + 1
    bridges = f"bridges {len(grown)} in {sum(1 for r in records if r['bridges'])} of {len(records)} lives" + \
              (f" ({', '.join(f'{k} {v}' for k, v in sorted(where.items()))})" if where else "")
    if all_food:
        return f"{name:34s} all food: food {food:.2f} per 1,000 ticks; {bridges}"
    w, wlo, whi = ratio_ci(records)
    l, llo, lhi = ratio_ci(records, third=2)
    return (f"{name:34s} food {food:.2f}, poison {bad:.2f} per 1,000; food:poison {w:.2f} [{wlo:.2f}, {whi:.2f}],"
            f" last third {l:.2f} [{llo:.2f}, {lhi:.2f}]; {bridges}")


def per_life(records):
    """Per life: food, poison and net (food - poison) eaten per 1,000 ticks after moving."""
    out = []
    for r in records:
        t = sum(t for _, _, t in r["thirds"])
        f, p = sum(f for f, _, _ in r["thirds"]), sum(p for _, p, _ in r["thirds"])
        out.append((1000 * f / t, 1000 * p / t, 1000 * (f - p) / t) if t else (0.0, 0.0, 0.0))  # never moved: none
    return np.array(out)


def paired(a, b, boots=2000, seed=0):
    """b minus a, life for life (the same seeds and, with STREAMS, the same noise): the mean difference in net food
    per 1,000 ticks and its bootstrap 95% interval."""
    d = per_life(b)[:, 2] - per_life(a)[:, 2]
    rng = np.random.default_rng(seed)
    boot = d[rng.integers(len(d), size=(boots, len(d)))].mean(1)
    return d.mean(), np.percentile(boot, 2.5), np.percentile(boot, 97.5)
