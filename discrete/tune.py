"""Tuning a discrete circuit's part values (discrete/NOTEBOOK.md): minimal/search.py's CMA-ES, every candidate living
closed loop in SPICE (discrete/life.py) on the same seeds, every generation (so that the search isn't led by which
lives a generation drew; the result is judged afterwards on seeds it never saw), judged by efficiency (or gain rate),
a circuit counting only if it does the job (minimal/spec.py, objective). Each seed has its own parts' tolerances.

    python -m discrete.tune CIRCUIT [GENERATIONS] [--seconds 40] [--seeds 16] [--lam 10] [--by robust]
                                    [--workers 8] [--start k=v ...] [--poison] [--only k ...]

--poison: each seed lived twice, red then blue as poison (discrete/poison.py), for a circuit that learns; --only: tune
just these values, the rest kept at their defaults (or start's).

writes discrete/results/CIRCUIT_tuned.json (the best mean's values, and the history).
"""

from __future__ import annotations

import inspect
import json
import os
import signal
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from discrete.circuits import BOUNDS, CIRCUITS  # noqa: E402
from discrete.life import _one, lived  # noqa: E402
from minimal.search import cmaes  # noqa: E402
from minimal import spec  # noqa: E402

RESULTS = os.path.join(os.path.dirname(__file__), "results")


def params_of(name: str, start: dict, only=None) -> dict:
    """A circuit's tunable values: its builder's keyword defaults (or start's), each within BOUNDS for its kind (the
    first letters of its name: r, c)."""
    build, _ = CIRCUITS[name]
    out = {}
    for k, p in inspect.signature(build).parameters.items():
        if k == "rng" or not isinstance(p.default, float) or p.default == 0 or (only and k not in only):
            continue
        v = start.get(k, p.default)
        lo, hi = BOUNDS[k[0]]
        out[k] = (min(max(v, lo), hi), lo, hi)
    return out


def robust(lives) -> float:
    """Efficiency, less COST x the mean shortfall of each third of each life below the food every creature needs (as
    the score charges starving): no cliff where the job fails, so that a search isn't led by the riskiest of the
    candidates that fail it."""
    short = sum(max(0.0, spec.NEED - spec.SPAN * a / t) if t > 0 else spec.NEED for l in lives for a, _, t in l[:3])
    return spec.efficiency(lives) - spec.COST * short / (3 * len(lives))



if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("circuit")
    ap.add_argument("gens", nargs="?", type=int, default=40)
    ap.add_argument("--seconds", type=float, default=40.0)
    ap.add_argument("--seeds", type=int, default=16)
    ap.add_argument("--lam", type=int, default=10)
    ap.add_argument("--by", default="robust")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--sigma", type=float, default=0.04)    # in [0, 1] of each value's log range (1000 times for a
                                                            # resistor): 0.04 is about 1.3 times; the switch's window
                                                            # is only about 3 times wide
    ap.add_argument("--start", nargs="*", default=[])
    ap.add_argument("--poison", action="store_true")
    ap.add_argument("--only", nargs="*", default=None)
    a = ap.parse_args()
    start = {k: float(v) for k, v in (s.split("=") for s in a.start)}
    params = params_of(a.circuit, start, a.only)
    fixed = {k: v for k, v in start.items() if k not in params}
    os.makedirs(RESULTS, exist_ok=True)
    out = os.path.join(RESULTS, f"{a.circuit}_tuned.json")
    ex = ProcessPoolExecutor(a.workers)

    def stop(*_):                                   # killed: take the workers too, or they linger, orphaned
        for p in list(getattr(ex, "_processes", {}).values()):
            p.terminate()
        os._exit(1)

    signal.signal(signal.SIGTERM, stop)

    def evaluate(designs, seeds, seconds):
        seeds = range(20000, 20000 + a.seeds)       # the same seeds every generation: comparisons across generations
        if a.poison:
            from discrete import poison
            jobs = [(a.circuit, {**fixed, **d}, s, seconds, c) for d in designs for s in seeds for c in ("red", "blue")]
            ls = list(ex.map(poison._one, jobs))
            n = 2 * len(seeds)
            return [ls[i * n:(i + 1) * n] for i in range(len(designs))]
        jobs = [(a.circuit, {**fixed, **d}, s, seconds) for d in designs for s in seeds]
        rs = list(ex.map(_one, jobs))
        n = len(seeds)
        return [[lived(r, seconds) for r in rs[i * n:(i + 1) * n]] for i in range(len(designs))]

    def log(s):
        print(s, flush=True)

    best_mean, best, history = cmaes(lambda p: p, params, gens=a.gens, lam=a.lam, sigma=a.sigma, seeds=a.seeds, seconds=a.seconds,
                                     log=log, by=a.by, evaluate=evaluate, first_seed=20000,
                                     judge=robust if a.by == "robust" else None)
    json.dump({"circuit": a.circuit, "by": a.by, "final_mean": best_mean, "best": {**fixed, **best[1]},
               "best_value": best[0], "poison": a.poison,
               "history": history}, open(out, "w"), indent=1)
    print("best mean:", {k: f"{v:.3g}" for k, v in best[1].items()}, f"{best[0]:.3f}")
