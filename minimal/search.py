"""Tuning a circuit's parameters for the minimal circuit search (minimal/NOTEBOOK.md): CMA-ES (Hansen's covariance
matrix adaptation evolution strategy, in its plain form) on net food per 1,000 ticks. Each parameter is searched in
[0, 1], mapped onto its bounds (on a log scale when they are both positive). Every generation scores its candidates
on fresh seeds, the same seeds for all of them (paired), so that no candidate is tuned to particular lives. Noise and
mismatch are the simulator's own (mixed_feedback), at the nominal noise (the user's decision, 2026-10-20). Every
polish ends with pruning (minimal/prune.py), saved beside it as NAME_pruned if anything could go.

    python -m minimal.search DESIGN|RESULTS.json [GENERATIONS] [--ticks 10000] [--seeds 8] [--lam 16] [--name NAME]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from minimal.spec import net, parts, score, summary  # noqa: E402

RESULTS = os.path.join(os.path.dirname(__file__), "results")


def decode(u, params: dict) -> dict:
    """[0, 1] per parameter (clipped) -> its value."""
    out = {}
    for x, (k, (_, lo, hi)) in zip(np.clip(u, 0.0, 1.0), params.items()):
        out[k] = math.exp(math.log(lo) + x * (math.log(hi) - math.log(lo))) if lo > 0 and hi > 0 else lo + x * (hi - lo)
    return out


def encode(p: dict, params: dict):
    u = []
    for k, (_, lo, hi) in params.items():
        v = p[k]
        u.append((math.log(v) - math.log(lo)) / (math.log(hi) - math.log(lo)) if lo > 0 and hi > 0 else (v - lo) / (hi - lo))
    return np.array(u)


def cmaes(design, params: dict, gens: int = 60, lam: int = 16, seeds: int = 8, ticks: int = 10000,
          sigma: float = 0.15, start: dict | None = None, log=print, first_seed: int = 10000):
    """Maximise net food. Returns (best parameters by their generation's mean, history)."""
    n = len(params)
    mean = encode(start or {k: v[0] for k, v in params.items()}, params)
    mu = lam // 2
    w = np.log(mu + 0.5) - np.log(np.arange(1, mu + 1))
    w /= w.sum()
    mueff = 1 / (w ** 2).sum()
    cc, cs = (4 + mueff / n) / (n + 4 + 2 * mueff / n), (mueff + 2) / (n + mueff + 5)
    c1 = 2 / ((n + 1.3) ** 2 + mueff)
    cmu = min(1 - c1, 2 * (mueff - 2 + 1 / mueff) / ((n + 2) ** 2 + mueff))
    damps = 1 + 2 * max(0, math.sqrt((mueff - 1) / (n + 1)) - 1) + cs
    chin = math.sqrt(n) * (1 - 1 / (4 * n) + 1 / (21 * n * n))
    pc, ps, C = np.zeros(n), np.zeros(n), np.eye(n)
    rng = np.random.default_rng(0)
    history, best = [], (-math.inf, None)
    for g in range(gens):
        evals, B = np.linalg.eigh(C)
        D = np.sqrt(np.maximum(evals, 1e-20))
        z = rng.standard_normal((lam, n))
        y = z @ np.diag(D) @ B.T
        x = mean + sigma * y
        x[-1] = mean                                            # (the mean itself, scored on the same lives)
        specs = [design(decode(xi, params)) for xi in x]
        lives = score(specs, seeds=range(first_seed + g * seeds, first_seed + (g + 1) * seeds), ticks=ticks)
        f = np.array([net(l) for l in lives])
        order = np.argsort(-f[:-1])
        if f[-1] > best[0]:
            best = (f[-1], decode(mean, params))
        history.append({"gen": g, "mean_net": float(f[-1]), "best_net": float(f[:-1].max()), "sigma": sigma})
        log(f"gen {g:3d}  mean {f[-1]:+.3f}  best {f[:-1].max():+.3f}  sigma {sigma:.3f}")
        sel = order[:mu]
        old = mean
        mean = (w[:, None] * x[sel]).sum(0)
        ymean = (mean - old) / sigma
        Cinvsqrt = B @ np.diag(1 / D) @ B.T
        ps = (1 - cs) * ps + math.sqrt(cs * (2 - cs) * mueff) * Cinvsqrt @ ymean
        hsig = np.linalg.norm(ps) / math.sqrt(1 - (1 - cs) ** (2 * (g + 1))) / chin < 1.4 + 2 / (n + 1)
        pc = (1 - cc) * pc + hsig * math.sqrt(cc * (2 - cc) * mueff) * ymean
        ysel = (x[sel] - old) / sigma
        C = (1 - c1 - cmu) * C + c1 * (np.outer(pc, pc) + (1 - hsig) * cc * (2 - cc) * C) + \
            cmu * (w[:, None] * ysel).T @ ysel
        sigma *= math.exp((cs / damps) * (np.linalg.norm(ps) / chin - 1))
        sigma = min(sigma, 0.5)
    return decode(mean, params), best, history


def validate(spec, seeds=range(100, 164), ticks: int = 10000) -> dict:
    """Held-out lives (seeds the search never saw)."""
    return summary(score([spec], seeds=seeds, ticks=ticks)[0])


def report(name, spec, v: dict) -> str:
    """The held-out summary v as a line or two; it does the job only within the rules too."""
    from minimal.spec import SLEW, slew
    done = v["job"] and v["over"] == 0
    return (f"{name}: parts {parts(spec)}; fastest slew {slew(spec):.1f} per circuit tick (limit {SLEW:g})\n"
            f"  net {v['net']:+.2f} [{v['lo']:+.2f}, {v['hi']:+.2f}] (food - poison {v['plain']:+.2f}), food"
            f" {v['food']:.2f}, poison {v['poison']:.2f}, last third {v['last']:.2f}, stranded {v['stranded']:.0%},"
            f" power {v['power']:.2f}, thruster firings {v['firings']:.0f} per 1,000, efficiency"
            f" {v['efficiency']:.2f} meals eaten per meal spent\n"
            + "".join(f"  at x{k} noise: net {w['net']:+.2f}, food {w['food']:.2f}, last third {w['last']:.2f},"
                      f" stranded {w['stranded']:.0%}, efficiency {w['efficiency']:.2f}, job {w['job']}\n"
                      for k, w in v.get("by_noise", {}).items())
            + f"  {'DOES THE JOB' if done else 'does not do the job'}")


if __name__ == "__main__":
    from minimal.designs import DESIGNS
    ap = argparse.ArgumentParser()
    ap.add_argument("design")
    ap.add_argument("gens", type=int, nargs="?", default=60)
    ap.add_argument("--ticks", type=int, default=10000)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--lam", type=int, default=16)
    ap.add_argument("--start", help="a results file to start from")
    ap.add_argument("--name", help="the results file's name (default: the design's)")
    ap.add_argument("--thrust", type=float, help="an experiment: the score's cost per thruster firing, in meals"
                                                 " (default spec.THRUST)")
    ap.add_argument("--noises", type=float, nargs="+", help="an experiment: judge at these noise levels (shares of"
                                                                 " the usual), the worst counting (default spec.JUDGED)")
    a = ap.parse_args()
    if a.noises:
        import minimal.spec
        minimal.spec.JUDGED = tuple(a.noises)           # (lives are scored in this process, at these levels)
    import minimal.spec
    if a.thrust is not None:
        minimal.spec.THRUST = a.thrust                  # (the score is reckoned here, in this process)
    if a.design.endswith(".json"):                     # polish a raw circuit (one the open search found)
        from minimal.designs import raw
        found = json.load(open(a.design))
        design, params = raw(found["spec"])
        a.design = os.path.basename(a.design)[:-5]
        start = None
    else:
        design, params = DESIGNS[a.design]
        start = json.load(open(a.start))["params"] if a.start else None
    t0 = time.time()
    final, best, hist = cmaes(design, params, a.gens, a.lam, a.seeds, a.ticks, start=start)
    spec = design(final)
    v = validate(spec, ticks=a.ticks)
    print(report(a.name or a.design, spec, v) + f"\n  ({time.time() - t0:.0f} s)")
    os.makedirs(RESULTS, exist_ok=True)
    json.dump({"design": a.design, "params": final, "spec": spec, "held_out": v, "parts": parts(spec),
               "history": hist, "args": vars(a)}, open(os.path.join(RESULTS, f"{a.name or a.design}.json"), "w"), indent=1)
    from minimal.prune import prune                     # then pruned, as standard (minimal/prune.py)
    pruned, steps = prune(spec)
    if steps:
        name = f"{a.name or a.design}_pruned"
        v = validate(pruned, ticks=a.ticks)
        print(report(name, pruned, v))
        json.dump({"design": name, "pruned_from": a.name or a.design, "spec": pruned, "held_out": v,
                   "parts": parts(pruned), "steps": steps}, open(os.path.join(RESULTS, f"{name}.json"), "w"), indent=1)
