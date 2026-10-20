"""Pruning, a standard step after every polish (minimal/NOTEBOOK.md, M7): the polish (CMA-ES) tunes values and cannot
remove a part, so parts that have stopped mattering stay (N_E1_32p carried 7). Here every single simplification is
tried, each a part or more fewer: delete an element (and any node it leaves untouched), take away an element's filter
or gate, a node's leak or a clamp. All are scored on the same lives (paired), lives of their own (neither the
search's nor the held-out ones), and the best that scores within TOL of where pruning started is kept; then again,
until none is. Held to the start, not to the last step, so that small losses can't add up.

    python -m minimal.prune RESULTS.json [--name NAME]      (default NAME: the results file's, with _pruned)
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from minimal.spec import net, parts, score, violations  # noqa: E402

SEEDS = range(20000, 20032)     # pruning's own lives (the search's start at 10000, the held-out are 100-163, 200-231)
TOL = 0.1                       # the most pruning may cost in score, from where it started (paired lives)
RESULTS = os.path.join(os.path.dirname(__file__), "results")


def interface(spec: dict) -> set:
    return {*spec["sensors"], *spec["motors"], spec["taste"]}


def tidy(spec: dict) -> dict:
    """Delete every node that no element touches and the body doesn't use, renumbering the rest."""
    s = copy.deepcopy(spec)
    while True:
        used = interface(s) | {i for e in s["elements"] for i in e[:3] if i >= 0}
        idle = [i for i in range(len(s["nodes"])) if i not in used]
        if not idle:
            return s
        i = idle[0]
        at = lambda k: k - (k > i) if k >= 0 else k
        del s["nodes"][i]
        s["elements"] = [[at(e[0]), at(e[1]), at(e[2]), *e[3:]] for e in s["elements"]]
        s["sensors"], s["motors"], s["taste"] = [at(k) for k in s["sensors"]], [at(k) for k in s["motors"]], at(s["taste"])


def simpler(spec: dict) -> list:
    """Every legal circuit one simplification away: (what was taken away, the circuit)."""
    names = [n[0] for n in spec["nodes"]]
    out = []

    def add(label, s):
        s = tidy(s)
        if not violations(s):
            out.append((label, s))
    for j, e in enumerate(spec["elements"]):
        what = f"{names[e[0]]}<-{names[e[1]]}" + (f"|{names[e[2]]}" if e[2] >= 0 else "")
        s = copy.deepcopy(spec)
        del s["elements"][j]
        if s["elements"]:
            add(f"delete {what}", s)
        if e[6] > 0:
            s = copy.deepcopy(spec)
            s["elements"][j][6] = 0.0
            add(f"unfilter {what}", s)
        if e[2] >= 0:
            s = copy.deepcopy(spec)
            s["elements"][j][2] = -1
            add(f"ungate {what}", s)
    for i, n in enumerate(spec["nodes"]):
        if n[2] is not None:
            s = copy.deepcopy(spec)
            s["nodes"][i][1], s["nodes"][i][2] = 0.0, None
            add(f"no leak on {names[i]}", s)
        for k, side in ((4, "low"), (5, "high")):
            if n[k] is not None:
                s = copy.deepcopy(spec)
                s["nodes"][i][k] = None
                add(f"no {side} clamp on {names[i]}", s)
    return out


def prune(spec: dict, seeds=SEEDS, tol: float = TOL, ticks: int = 10000, log=print):
    """(the pruned circuit, the steps taken as [(what, parts, score)])."""
    start = net(score([spec], seeds=seeds, ticks=ticks)[0])
    log(f"start: {parts(spec)['total']} parts, score {start:+.3f} (keeping within {tol} of it)")
    steps = []
    while True:
        options = simpler(spec)
        if not options:
            break
        scores = [net(l) for l in score([s for _, s in options], seeds=seeds, ticks=ticks)]
        ok = [(f, k) for k, f in enumerate(scores) if f >= start - tol]
        if not ok:
            log("  nothing more can go")
            break
        f, k = max(ok)
        label, spec = options[k]
        steps.append((label, parts(spec)["total"], f))
        log(f"  {label}: {parts(spec)['total']} parts, score {f:+.3f} (best of {len(options)})")
    return spec, steps


if __name__ == "__main__":
    from minimal.search import report, validate
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--name")
    a = ap.parse_args()
    found = json.load(open(a.results))
    name = a.name or os.path.basename(a.results)[:-5] + "_pruned"
    t0 = time.time()
    spec, steps = prune(found["spec"])
    if not steps:
        print("nothing pruned")
        sys.exit()
    v = validate(spec)
    print(report(name, spec, v) + f"\n  ({time.time() - t0:.0f} s)")
    json.dump({"design": name, "pruned_from": os.path.basename(a.results)[:-5], "spec": spec, "held_out": v,
               "parts": parts(spec), "steps": steps}, open(os.path.join(RESULTS, f"{name}.json"), "w"), indent=1)
