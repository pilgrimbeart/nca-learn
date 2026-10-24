"""The open search for the minimal circuit (minimal/NOTEBOOK.md, method step 4): evolution over topologies and
parameters at once, from random circuits, none of the hand designs among them, so it may find what reasoning missed.

The user's three objectives (2026-10-22), each its own dimension, never traded: parts, down (the simplest brain that
does the job); efficiency (meals gained per meal spent resting, moving and thinking: the best driver for energy), up;
and gain rate (meals gained per 10 s: the best for speed and accuracy, energy free), up. Doing the job
(minimal/spec.py, JOB) is a constraint: a circuit doing it beats every one that doesn't, and among those that don't
the score (minimal/spec.py) leads towards it. Selection by non-dominated rank (NSGA-II, crowding replaced by
preferring the higher score within a front), so the first front answers all three questions at every complexity.
Every generation scores parents and children together on fresh seeds, with the simulator's own noise and mismatch,
so nothing survives on one lucky evaluation.

    python -m minimal.evolve [GENERATIONS] [--pop 48] [--seed 0] [--name evolve0] [--start ...] [--resume]
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from minimal.designs import BOUNDS  # noqa: E402
from minimal.spec import (LIFE, does_job, efficiency, gain, interface, net, parts, remove_node, score, tidy,  # noqa: E402
                          worst)
from units import C_TYP, I_TYP, R_TYP, T_TYP  # noqa: E402

RESULTS = os.path.join(os.path.dirname(__file__), "results")


def clip(v, lo, hi):
    return min(max(v, lo), hi)


def random_element(rng, n, taste):
    """A new element between random nodes: input and gate any node, into any node but the taste node."""
    to = int(rng.choice([i for i in range(n) if i != taste]))
    tau = T_TYP * float(math.exp(rng.uniform(math.log(0.5), math.log(50.0)))) if rng.random() < 0.3 else 0.0
    return [to, int(rng.integers(n)), int(rng.integers(n)) if rng.random() < 0.5 else -1,
            I_TYP * float(rng.choice((-1, 1)) * rng.uniform(0.5, 5.0)), float(rng.uniform(-1.5, 1.5)),
            float(rng.uniform(1.0, 20.0)), tau, bool(rng.random() < 0.7)]


def random_node(rng, name):
    if rng.random() < 0.4:                              # a memory
        return [name, 0.0, None, C_TYP * float(rng.uniform(0.5, 5.0)), 0.0, 1.0, float(rng.uniform(0.0, 1.0)), True]
    R = R_TYP * float(math.exp(rng.uniform(math.log(0.5), math.log(20.0))))
    return [name, float(rng.uniform(-1.5, 0.5)) / R, R,
            C_TYP * float(math.exp(rng.uniform(math.log(0.2), math.log(5.0)))), None, None, None, False]


def born(rng) -> dict:
    """A random circuit: the interface (two sensors, two motors, taste), a memory, and two to six random elements."""
    nodes = [random_node(rng, k) for k in ("S0", "S1", "M0", "M1", "T")]
    for i in range(5):                                  # the interface nodes leak (a sensor or taste must recover)
        if nodes[i][7]:
            nodes[i] = [nodes[i][0], -0.5 * I_TYP, R_TYP, C_TYP, None, None, None, False]
    nodes.append(random_node(rng, "m"))
    spec = {"nodes": nodes, "elements": [], "sensors": [0, 1], "motors": [2, 3], "taste": 4, "units": "SI"}
    for _ in range(int(rng.integers(2, 7))):
        spec["elements"].append(random_element(rng, len(nodes), 4))
    return spec


def mutate(spec, rng) -> dict:
    s = copy.deepcopy(spec)
    n, T = len(s["nodes"]), s["taste"]
    for _ in range(int(rng.integers(1, 4))):
        n = len(s["nodes"])
        k = rng.random()
        if k < 0.35:                                    # jitter parameters
            for nd in s["nodes"]:
                if rng.random() < 0.3:
                    if nd[2] is not None:
                        rest = nd[1] * nd[2]
                        nd[2] = clip(nd[2] * math.exp(0.3 * rng.normal()), *BOUNDS["R"])
                        nd[1] = clip(rest + 0.2 * rng.normal(), -BOUNDS["rest"], BOUNDS["rest"]) / nd[2]
                    nd[3] = clip(nd[3] * math.exp(0.3 * rng.normal()), *BOUNDS["C"])
                    if nd[7]:
                        nd[6] = clip((nd[6] or 0.0) + 0.1 * rng.normal(), 0.0, 1.0)
            for e in s["elements"]:
                if rng.random() < 0.3:
                    e[3] = clip(e[3] * math.exp(0.3 * rng.normal()), -BOUNDS["gain"], BOUNDS["gain"])
                    e[4] = clip(e[4] + 0.2 * rng.normal(), -BOUNDS["offset"], BOUNDS["offset"])
                    e[5] = clip(e[5] * math.exp(0.3 * rng.normal()), *BOUNDS["slope"])
                    if e[6] > 0:
                        e[6] = clip(e[6] * math.exp(0.3 * rng.normal()), *BOUNDS["tau"])
        elif k < 0.50:                                  # add an element
            s["elements"].append(random_element(rng, n, T))
        elif k < 0.62 and s["elements"]:                # remove one
            del s["elements"][int(rng.integers(len(s["elements"])))]
        elif k < 0.70:                                  # add a node, with an element in and one out
            s["nodes"].append(random_node(rng, f"n{n}"))
            e1, e2 = random_element(rng, n + 1, T), random_element(rng, n + 1, T)
            e1[0], e2[1] = n, n
            s["elements"] += [e1, e2]
        elif k < 0.76:                                  # remove a node the body doesn't use
            free = [i for i in range(n) if i not in interface(s)]
            if free:
                remove_node(s, int(rng.choice(free)))
        elif k < 0.84 and s["elements"]:                # re-route an element's input, gate or target
            e = s["elements"][int(rng.integers(len(s["elements"])))]
            which = int(rng.integers(3))
            if which == 0:
                e[1] = int(rng.integers(n))
            elif which == 1:
                e[2] = -1 if e[2] >= 0 and rng.random() < 0.5 else int(rng.integers(n))
            else:
                e[0] = int(rng.choice([i for i in range(n) if i != T]))
        elif k < 0.88 and s["elements"]:                # filter an element's input, or stop filtering it
            e = s["elements"][int(rng.integers(len(s["elements"])))]
            e[6] = 0.0 if e[6] > 0 else T_TYP * float(math.exp(rng.uniform(math.log(0.5), math.log(50.0))))
        elif k < 0.92:                                  # clamp a node, or unclamp it
            nd = s["nodes"][int(rng.integers(n))]
            if nd[4] is None:
                nd[4], nd[5] = (0.0, 1.0) if nd[7] else (-2.0, 2.0)
            else:
                nd[4] = nd[5] = None
        elif k < 0.96:                                  # a node not on the interface: leaky <-> memory
            free = [i for i in range(n) if i not in interface(s)]
            if free:
                i = int(rng.choice(free))
                nd = s["nodes"][i]
                s["nodes"][i] = random_node(rng, nd[0]) if nd[7] else [nd[0], 0.0, None, nd[3], 0.0, 1.0, 0.5, True]
        else:                                           # move a motor onto another node (merging)
            j = int(rng.integers(2))
            other = [i for i in range(n) if i != T and not s["nodes"][i][7]]
            s["motors"][j] = int(rng.choice(other))
    return tidy(s)


def dominates(a, b) -> bool:
    """a, b: (job, score, parts, efficiency, gain). Doing the job beats not doing it; between two that do, at least
    as good on parts (down), efficiency and gain (up), and not the same; between two that don't, a higher score."""
    if a[0] != b[0]:
        return a[0]
    if not a[0]:
        return a[1] > b[1]
    return a[2] <= b[2] and a[3] >= b[3] and a[4] >= b[4] and a[2:] != b[2:]


def fronts(objs):
    """Non-dominated fronts (dominates)."""
    left, out = list(range(len(objs))), []
    while left:
        f = [i for i in left if not any(dominates(objs[j], objs[i]) for j in left)]
        out.append(f)
        left = [i for i in left if i not in f]
    return out


def evolve(gens=200, pop=48, seed=0, seeds=8, seconds=LIFE, name="evolve0", log=print, start=None, resume=False):
    """start: specs to begin from (the population their copies and mutants), else random circuits. resume: carry on
    from the state last saved under this name (every 10 generations), on the same seeds as if never stopped (the
    mutations' random numbers differ: a machine that rebooted, 2026-10-23)."""
    rng = np.random.default_rng(seed)
    archive = {}                                        # parts -> (best score in one generation, spec)
    best_by = {"efficiency": {}, "gain": {}}            # parts -> (best in one generation, spec), doing the job
    path = os.path.join(RESULTS, f"{name}.json")
    first = 0
    if resume:
        saved = json.load(open(path))
        P, first = saved["population"], saved["gen"] + 1
        archive = {int(k): tuple(v) for k, v in saved["archive"].items()}
        best_by = {key: {int(k): tuple(v) for k, v in saved.get(f"best_{key}", {}).items()} for key in best_by}
        rng = np.random.default_rng([seed, first])
        log(f"resumed from generation {first - 1}")
    elif start:
        P = [copy.deepcopy(s) for s in start] + [mutate(start[i % len(start)], rng) for i in range(pop - len(start))]
    else:
        P = [tidy(born(rng)) for _ in range(pop)]
    for g in range(first, gens):
        kids = []
        for _ in range(pop):                            # tournament of two on score, then mutate
            a, b = rng.integers(len(P), size=2)
            kids.append(mutate(P[a] if rng.random() < 0.5 else P[b], rng))
        everyone = P + kids
        lives = score(everyone, seeds=range(20000 + seed * 100000 + g * seeds,
                                            20000 + seed * 100000 + (g + 1) * seeds),
                      seconds=seconds)
        objs = [(does_job(l), round(net(l), 3), parts(s)["total"], round(worst(l, efficiency), 2), round(worst(l, gain), 2))
                for s, l in zip(everyone, lives)]
        for (job, sc, pt, ef, gn), s in zip(objs, everyone):
            if pt not in archive or sc > archive[pt][0]:
                archive[pt] = (sc, s)
            for key, v in (("efficiency", ef), ("gain", gn)):
                if job and (pt not in best_by[key] or v > best_by[key][pt][0]):
                    best_by[key][pt] = (v, s)
        nxt = []
        for f in fronts(objs):
            f = sorted(f, key=lambda i: -objs[i][1])
            nxt += f[: pop - len(nxt)]
            if len(nxt) >= pop:
                break
        P = [everyone[i] for i in nxt]
        best = max(objs, key=lambda o: o[1])
        front = sorted({objs[i] for i in fronts(objs)[0] if objs[i][0]}, key=lambda o: o[2])
        log(f"gen {g:3d}  best score {best[1]:+.2f} ({best[2]} parts)  front (doing the job), parts/efficiency/gain: " +
            " ".join(f"{p}p/{e}e/{gn}g" for _, _, p, e, gn in front))
        if g % 10 == 9 or g == gens - 1:
            os.makedirs(RESULTS, exist_ok=True)
            json.dump({"gen": g, "population": P, "archive": {str(k): v for k, v in sorted(archive.items())},
                       **{f"best_{key}": {str(k): v for k, v in sorted(b.items())} for key, b in best_by.items()}},
                      open(path, "w"))
    return P, archive


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("gens", type=int, nargs="?", default=200)
    ap.add_argument("--pop", type=int, default=48)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--name", default="evolve0")
    ap.add_argument("--start", nargs="*", help="tuned designs' results files to begin from")
    ap.add_argument("--resume", action="store_true", help="carry on from the state last saved under --name")
    ap.add_argument("--substrates", nargs="+", help="an experiment: judge with these substrates' noise"
                                                    " (mixed_feedback.SUBSTRATES), the worst counting (default spec.JUDGED)")
    a = ap.parse_args()
    if a.substrates:
        import minimal.spec
        minimal.spec.JUDGED = tuple(a.substrates)       # (lives are scored in this process, with these)
    start = [json.load(open(path))["spec"] for path in a.start] if a.start else None
    t0 = time.time()
    evolve(a.gens, a.pop, a.seed, name=a.name, start=start, resume=a.resume)
    print(f"({time.time() - t0:.0f} s)")
