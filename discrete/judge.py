"""Judging discrete circuits honestly (discrete/NOTEBOOK.md): full lives on seeds no search saw, each with its own
parts' tolerances, all food; every measure with its 95% interval (minimal/spec.py's bootstrap over seeds).

    python -m discrete.judge RESULTS.json [--cuts N] [--seeds 32] [--seconds 100] [--motors X] [--finer F]
    python -m discrete.judge --compare A.lives B.lives ...

Each judging keeps its lives beside RESULTS.json (.lives, a pickle), so that circuits judged on the same seeds can be
compared paired (--compare: each pair's difference in efficiency and gain with its 95% interval, seeds resampled
together). --motors X: each life's thrusters unequal, one stronger than the other by up to X times
(discrete/bodies.py; NOTEBOOK.md D5); its lives are kept as ..._motorsX.lives. --finer F: SPICE's largest step
divided by F (a result must hold at a finer step); kept as ..._finerF.lives.

RESULTS.json: discrete/tune.py's, prune.py's or a hand-written {"circuit", "best", "cuts"}; --cuts N applies the
first N of its cuts (a rung of a ladder) with the values that rung was found with ("rungs", if recorded) or "best".
"""

from __future__ import annotations

import json
import os
import pickle
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from discrete.prune import _one, build  # noqa: E402

HELD_OUT = 50000        # the first seed judged: no search used seeds from here on


def judge(name, params, cuts, seeds, seconds, workers=None, motors=None, finer=1):
    from discrete.bodies import draw
    from minimal.spec import efficiency, gain, interval
    body = (lambda s: draw(s, {"asymmetry": motors})) if motors else (lambda s: None)
    with ProcessPoolExecutor(workers) as ex:
        lives = list(ex.map(_one, [(name, params, cuts, s, seconds, body(s), finer) for s in seeds]))
    ok = [l for l in lives if l is not None]
    rng = np.random.default_rng(0)
    boot = lambda f: interval([f([ok[i] for i in rng.integers(0, len(ok), len(ok))]) for _ in range(1000)])
    t = sum(t for l in ok for _, _, t in l)
    return {"parts": build(name, params, cuts, None)[0].parts(), "lives": len(ok), "failed": len(lives) - len(ok),
            "efficiency": efficiency(ok), "eff_ci": boot(efficiency), "gain": gain(ok), "gain_ci": boot(gain),
            "food": 10 * sum(a for l in ok for a, _, _ in l) / t, "stranded": float(np.mean([l[2][0] == 0 for l in ok])),
            "firings": float(np.mean([l.firings for l in ok])), "power": float(np.mean([l.power for l in ok])),
            "all": lives}


def compare(files):
    """Each pair of judged circuits' differences, paired on seeds both lived."""
    from minimal.spec import efficiency, gain, interval
    runs = {os.path.basename(f): pickle.load(open(f, "rb")) for f in files}
    names = list(runs)
    rng = np.random.default_rng(0)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            A, B = runs[a], runs[b]
            both = [k for k in range(min(len(A), len(B))) if A[k] is not None and B[k] is not None]
            for label, f in (("efficiency", efficiency), ("gain", gain)):
                d = []
                for _ in range(2000):
                    k = [both[j] for j in rng.integers(0, len(both), len(both))]
                    d.append(f([A[j] for j in k]) - f([B[j] for j in k]))
                lo, hi = interval(d)
                verdict = "tied" if lo <= 0 <= hi else (f"{a} better" if lo > 0 else f"{b} better")
                print(f"{a} - {b}  {label:10s} {f([A[j] for j in both]) - f([B[j] for j in both]):+6.2f} "
                      f"[{lo:+.2f}, {hi:+.2f}]  {verdict}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="?")
    ap.add_argument("--compare", nargs="+")
    ap.add_argument("--cuts", type=int, default=None)
    ap.add_argument("--seeds", type=int, default=32)
    ap.add_argument("--seconds", type=float, default=100.0)
    ap.add_argument("--set", nargs="*", default=[])
    ap.add_argument("--motors", type=float, default=None)
    ap.add_argument("--finer", type=float, default=1)
    a = ap.parse_args()
    if a.compare:
        compare(a.compare)
        sys.exit()
    r = json.load(open(a.results))
    cuts = [tuple(c) for c in r.get("cuts", [])][: a.cuts]
    params = dict(r.get("rungs", {}).get(str(len(cuts)), r["best"]))
    params.update({k: float(v) for k, v in (s.split("=") for s in a.set)})
    j = judge(r["circuit"], params, cuts, range(HELD_OUT, HELD_OUT + a.seeds), a.seconds, motors=a.motors,
              finer=a.finer)
    print(f"{r['circuit']} with {len(cuts)} cuts: {j['parts']} parts  efficiency {j['efficiency']:.2f} "
          f"[{j['eff_ci'][0]:.2f}, {j['eff_ci'][1]:.2f}]  gain {j['gain']:.2f} [{j['gain_ci'][0]:.2f}, {j['gain_ci'][1]:.2f}]"
          f"  food {j['food']:.2f}  stranded {j['stranded']:.0%}  firings {j['firings']:.0f}/10s"
          f"  power {j['power'] * 1e9:.0f} nW  ({j['lives']} lives, {j['failed']} failed)")
    pickle.dump(j["all"], open(os.path.splitext(a.results)[0] + (f"_{len(cuts)}cuts" if cuts else "")
                          + (f"_motors{a.motors:g}" if a.motors else "")
                          + (f"_finer{a.finer:g}" if a.finer != 1 else "") + ".lives", "wb"))
