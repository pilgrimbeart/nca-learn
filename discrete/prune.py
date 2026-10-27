"""Paring a discrete circuit to the bone (discrete/NOTEBOOK.md): with its tuned values, try each part taken out: opened
(the part removed), shorted (a resistor, capacitor or diode made a wire), or for a transistor, two of its terminals
joined (base to emitter: the eyes straight into what it drove, say; base to collector; collector to emitter: a switch
always closed), the device gone; every variant living the same closed-loop lives in SPICE, and
keep the removal that does best if it does as well as the whole circuit within noise (against the whole, not the last
cut, so that small losses can't add up) (paired over seeds, the 95%
interval of the difference reaching 0); repeat until no part can go. What remains is what the job needs, for this
circuit's kind; what went is what it didn't.

    python -m discrete.prune RESULTS.json [--seeds 16] [--seconds 40]

RESULTS.json: discrete/tune.py's (its circuit and best values). Writes discrete/results/CIRCUIT_pruned.json.
"""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from discrete.life import STEP, live, lived  # noqa: E402

PART = ("R", "C", "D", "Q")


MOVES = {"R": ("open", "short"), "C": ("open", "short"), "D": ("open", "short"), "Q": ("open", "be", "bc", "ce")}


def build(name, params, cuts, seed):
    """The circuit for a seed (its tolerances), with cuts applied: (line index, a move in MOVES)."""
    from discrete.circuits import CIRCUITS
    b, supply = CIRCUITS[name]
    net = b(np.random.default_rng(seed + 5_000_011) if seed is not None else None, **params)
    for i, how in sorted(cuts, reverse=True):
        ln = net.lines[i]
        net.count[ln[0]] -= 1
        f = ln.split()
        if how == "short":
            net.lines[i] = f"Rshort{i} {f[1]} {f[2]} 1"
        elif how in ("be", "bc", "ce"):                 # a transistor's terminals: collector, base, emitter
            node = dict(zip("cbe", f[1:4]))
            net.lines[i] = f"Rjoin{i} {node[how[0]]} {node[how[1]]} 1"
        else:
            net.lines[i] = "* removed: " + ln
    return net, supply


def describe(name, params, i):
    net, _ = build(name, params, [], None)
    return net.lines[i]


RESCREEN = 3            # the best cuts of each round re-screened for values
SAMPLES = 80            # values tried for each on the bench, within SPREAD times of the circuit's
SPREAD = 3.0


def _one(a):
    name, params, cuts, seed, seconds, *more = a        # (and optionally a body, then a finer step)
    body, finer = (*more, None, None)[:2]
    net, supply = build(name, params, cuts, seed)
    try:
        return lived(live(net, seed, seconds, supply, body=body, step=STEP / (finer or 1)), seconds)
    except Exception:                                   # noqa: BLE001  (a cut that leaves no working circuit)
        return None


def judge(lives_list):
    """Each variant's robust value (discrete/tune.py) and its per-seed efficiencies' contributions, for pairing."""
    from discrete.tune import robust
    return [robust(l) if l and all(x is not None for x in l) else -np.inf for l in lives_list]


def paired(a, b, boot=2000, rng=np.random.default_rng(0)):
    """95% interval of robust(a) - robust(b) over seeds resampled together."""
    from discrete.tune import robust
    n = len(a)
    d = []
    for _ in range(boot):
        k = rng.integers(0, n, n)
        d.append(robust([a[j] for j in k]) - robust([b[j] for j in k]))
    return np.percentile(d, [2.5, 97.5])


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--seeds", type=int, default=16)
    ap.add_argument("--seconds", type=float, default=40.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--ladder", action="store_true", help="keep cutting the least harmful part while the job is done,"
                    " however much is lost: what each part buys")
    a = ap.parse_args()
    r = json.load(open(a.results))
    name, params = r["circuit"], r["best"]
    seeds = range(30000, 30000 + a.seeds)
    net, _ = build(name, params, [], None)
    parts = [i for i, ln in enumerate(net.lines) if ln[0] in PART]
    cuts = []
    with ProcessPoolExecutor(a.workers) as ex, ProcessPoolExecutor(a.workers) as bench_ex:
        # (two pools: ngspice run on the bench and in closed loop can't share a process)
        def run_with(p, variants):
            jobs = [(name, p, c, s, a.seconds) for c in variants for s in seeds]
            res = list(ex.map(_one, jobs))
            return [res[k * len(seeds):(k + 1) * len(seeds)] for k in range(len(variants))]

        def run(variants):
            return run_with(params, variants)
        whole = run([cuts])[0]
        print(f"whole: {len(parts)} parts, robust {judge([whole])[0]:+.2f}", flush=True)
        while True:
            left = [i for i in parts if i not in {c[0] for c in cuts}]
            variants = [cuts + [(i, m)] for i in left for m in MOVES[net.lines[i][0]]]
            lives = run(variants)
            vals = judge(lives)
            for v, c, l in sorted(zip(vals, variants, lives), key=lambda x: -x[0])[:6]:
                print(f"  {c[-1][1]:5s} {describe(name, params, c[-1][0]):40s} robust {v:+.2f}", flush=True)
            from discrete.screen import search
            order = [k for k in np.argsort(vals)[::-1][:RESCREEN] if vals[k] > -np.inf]
            trials = []                                 # (value, variant, params, lives)
            for k in order:
                trials.append((vals[k], variants[k], params, lives[k]))
                found = search(name, params, variants[k], SAMPLES, SPREAD, bench_ex)[:2]
                for p, rates, fit in found:
                    if fit > -np.inf and p is not params:
                        l = run_with(p, [variants[k]])[0]
                        v = judge([l])[0]
                        print(f"    {variants[k][-1][1]:5s} {describe(name, params, variants[k][-1][0]):38s} re-screened:"
                              f" robust {v:+.2f}", flush=True)
                        trials.append((v, variants[k], p, l))
            if not trials:
                break
            v, variant, p, l = max(trials, key=lambda x: x[0])
            lo, hi = paired(l, whole)
            if a.ladder:
                from minimal.spec import does_job, efficiency, gain
                if not does_job(l):
                    print(f"the best cut no longer does the job (efficiency {efficiency(l):.2f}): stop")
                    break
            elif hi < 0:
                print(f"no part can go: the best cut is surely worse ({lo:+.2f}, {hi:+.2f})")
                break
            cuts, params = variant, p
            from minimal.spec import efficiency, gain
            print(f"cut {cuts[-1]}: {describe(name, params, cuts[-1][0])}  ({lo:+.2f}, {hi:+.2f}); now"
                  f" {len(parts) - len(cuts)} parts, robust {v:+.2f}, efficiency {efficiency(l):.2f},"
                  f" gain {gain(l):.2f}", flush=True)
            print("  values: " + " ".join(f"{k}={x:.3g}" for k, x in params.items()), flush=True)
    out = os.path.join(os.path.dirname(a.results), f"{name}_{'ladder' if a.ladder else 'pruned'}.json")
    json.dump({"circuit": name, "best": params, "cuts": cuts,
               "removed": [describe(name, params, i) for i, _ in cuts]}, open(out, "w"), indent=1)
    print("written", out)
