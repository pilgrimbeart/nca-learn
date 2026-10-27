"""Pruning, a standard step after every polish (minimal/NOTEBOOK.md, M7): the polish (CMA-ES) tunes values and cannot
remove a part, so parts that have stopped mattering stay (N_E1_32p carried 7). Here every single simplification is
tried, each a part or more fewer: delete an element (and any node then read by nothing), take away an element's
filter or gate, a node's leak or a clamp. All are scored on the same lives (paired), lives of their own (neither the
search's nor the held-out ones), and the best that scores within TOL of where pruning started is kept; then again,
until none is; a circuit doing the job must go on doing it. Held to the start, not to the last step, so that small
losses can't add up. Judged by the objective the polish maximised (--by: the score, efficiency or gain rate), so a
part kept for speed isn't pruned for its cost.

    python -m minimal.prune RESULTS.json [--name NAME] [--by score|efficiency|gain]   (NAME: the file's, with _pruned)
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from minimal.spec import LIFE, OBJECTIVES, does_job, objective, parts, score, tidy, violations  # noqa: E402

SEEDS = range(15000, 15032)     # pruning's own lives (the polish's start at 10000, the open search's at 20000, the
                                # held-out are 100-163 and 200-231)
TOL = {"score": 0.1, "gain": 0.1, "efficiency": 0.05}
                                # the most pruning may cost, from where it started (paired lives), in each objective's
                                # units (efficiency's are about half the score's)
RESULTS = os.path.join(os.path.dirname(__file__), "results")


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


def prune(spec: dict, seeds=SEEDS, tol: float | None = None, seconds: float = LIFE, log=print, by: str = "score"):
    """(the pruned circuit, the steps taken as [(what, parts, the objective)]). A circuit that does the job on
    pruning's lives must go on doing it after every step (2026-10-23: pruning by the score alone, within its
    tolerance, took HR_31p_pol to 28 parts that stranded in 35% of silicon lives)."""
    tol = TOL[by] if tol is None else tol
    lives = score([spec], seeds=seeds, seconds=seconds)[0]
    start, job = objective(lives, by), does_job(lives)
    log(f"start: {parts(spec)['total']} parts, {by} {start:+.3f} (keeping within {tol} of it"
        + (", and doing the job)" if job else ")"))
    steps = []
    while True:
        options = simpler(spec)
        if not options:
            break
        lived = score([s for _, s in options], seeds=seeds, seconds=seconds)
        scores = [objective(l, by) for l in lived]
        ok = [(f, k) for k, (f, l) in enumerate(zip(scores, lived)) if f >= start - tol and (does_job(l) or not job)]
        if not ok:
            log("  nothing more can go")
            break
        f, k = max(ok)
        label, spec = options[k]
        steps.append((label, parts(spec)["total"], f))
        log(f"  {label}: {parts(spec)['total']} parts, {by} {f:+.3f} (best of {len(options)})")
    return spec, steps


if __name__ == "__main__":
    from minimal.search import report, validate
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--name")
    ap.add_argument("--by", choices=tuple(OBJECTIVES), default="score", help="what pruning may cost little of")
    ap.add_argument("--substrates", nargs="+", help="an experiment: judge with these substrates' noise"
                                                    " (mixed_feedback.SUBSTRATES), the worst counting (default spec.JUDGED)")
    a = ap.parse_args()
    if a.substrates:
        import minimal.spec
        minimal.spec.JUDGED = tuple(a.substrates)       # (lives are scored in this process, with these)

    found = json.load(open(a.results))
    name = a.name or os.path.basename(a.results)[:-5] + "_pruned"
    t0 = time.time()
    from minimal.spec import load
    spec, steps = prune(load(a.results), by=a.by)
    if not steps:
        print("nothing pruned")
        sys.exit()
    v = validate(spec)
    print(report(name, spec, v) + f"\n  ({time.time() - t0:.0f} s)")
    json.dump({"design": name, "pruned_from": os.path.basename(a.results)[:-5], "spec": spec, "held_out": v,
               "parts": parts(spec), "steps": steps}, open(os.path.join(RESULTS, f"{name}.json"), "w"), indent=1)
