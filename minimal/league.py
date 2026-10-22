"""The league table of the minimal circuit search (minimal/LEAGUE.md): every tuned design in minimal/results,
re-validated under the current rules (held-out lives, with the simulator's noise and mismatch, the honesty limits).

Entry: doing the job (minimal/spec.py, JOB), within the honesty limits. The user's three objectives (2026-10-22), each its
own dimension, never traded: parts, down (the simplest brain doing the job); efficiency, up (the best driver for
energy: meals gained, food less COST a poison, per meal spent resting, moving and thinking); and gain rate, up (the
best for speed and accuracy, energy free: meals gained per 10 s). Pareto: no other design that does the job is
as simple and as good on both. Listed by parts, then efficiency. The near misses (failing the job) are listed apart:
a small, efficient near miss is worth knowing about.

Every relative position is tested (the user's question, 2026-10-21: which are high-confidence results?): every
design lives the same held-out seeds, so two designs' measures are compared paired, by a bootstrap over seeds
(each seed's two lives kept together); one is surely above another only if the 95% interval of the difference
excludes 0, else they are tied. Each measure is shown with its 95% interval, and doing the job is marked sure only
if every interval is within the job's limits.

    python -m minimal.league
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from minimal.spec import (COST, FIRING, JOB, JUDGED, MEAL, METABOLISM, SPAN, area, boot_index, by_level,  # noqa: E402
                          pack, parts, per_pair, score, slew, summary, unpack, worst_resampled)
from units import si  # noqa: E402

HERE = os.path.dirname(__file__)
CACHE = os.path.join(HERE, "results", "league_cache.json")
SKIP = ("_round1", "_unlimited", "_start", "_feasible", "_fixednoise", "league_cache", "evolve", "C_tuned")  # (copies)
LIVED = ("minimal/spec.py", "minimal/fastlife.py", "mixed_feedback.py", "units.py", "world.py", "creature.py",
         "brains/circuit.py")   # the code that shapes a life or its judging: the cache is keyed by it
# (results tuned under the old noise, before 2026-10-20's model, are re-validated under the new like any other)
SEEDS = range(100, 164)         # the held-out seeds (minimal/search.py, validate)


def validated(spec):
    """The held-out lives and their summary, cached by the spec and the code that shapes a life (LIVED)."""
    root = os.path.join(HERE, "..")
    code = "".join(open(os.path.join(root, f)).read() for f in LIVED)
    key = hashlib.sha1((json.dumps(spec, sort_keys=True) + code).encode()).hexdigest()
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    if key not in cache:
        cache = {k: v for k, v in cache.items() if isinstance(v, dict) and "lives" in v}     # (older entries go)
        cache[key] = {"lives": pack(score([spec], seeds=SEEDS)[0])}
        json.dump(cache, open(CACHE, "w"))
    lives = unpack(cache[key]["lives"])
    return lives, summary(lives)


def rows():
    out = []
    for path in sorted(glob.glob(os.path.join(HERE, "results", "*.json"))):
        name = os.path.basename(path)[:-5]
        if any(s in name for s in SKIP):
            continue
        r = json.load(open(path))
        if "spec" not in r:
            continue
        spec = r["spec"]
        from minimal.spec import violations
        bad = violations(spec)
        if bad:                                         # refused by the rules: not lived, listed apart
            out.append({"name": name, "parts": parts(spec)["total"], "illegal": "; ".join(bad)})
            continue
        lives, v = validated(spec)
        pt = parts(spec)
        sl = slew(spec)
        fails = []
        if v["food"] < JOB[0]:
            fails.append(f"food {v['food']:.2f}")
        if v["last"] < JOB[1]:
            fails.append(f"food:poison {v['last']:.2f}")
        if v["stranded"] > JOB[2]:
            fails.append(f"stranded {v['stranded']:.0%}")
        if sl > 1 + 1e-9:                               # (as spec.violations: rounding at the limit)
            fails.append(f"too fast for the step ({sl:.0%})")
        ci = v["ci"]
        sure = ci["food"][0] >= JOB[0] and ci["last"][0] >= JOB[1] and ci["stranded"][1] <= JOB[2] and sl <= 1 + 1e-9
        surely_not = ci["food"][1] < JOB[0] or ci["last"][1] < JOB[1] or ci["stranded"][0] > JOB[2] or sl > 1 + 1e-9
        out.append({"name": name, "parts": pt["total"], "blocks": pt["nodes"] + pt["elements"], "area": area(spec),
                    "power": v["power"], "v": v, "job": not fails, "fails": fails, "levels": {k: per_pair(v) for k, v in by_level(lives).items()},
                    "sure": sure if not fails else surely_not})
    return out


OBJECTIVES = (("efficiency", "efficiency", "meals gained per meal spent", "the most efficient",
               "the best driver for energy: meals gained per meal spent resting, moving and thinking"),
              ("gain", "gain rate", "meals gained per 10 s", "the fastest and most accurate",
               "the best driver for speed and accuracy, energy free: meals gained per 10 s"))
                    # with parts, the user's three objectives (2026-10-22); thrift is shown, no longer ranked


def compare(a, b, idx, key="efficiency") -> int:
    """+1 if a's measure (key) is surely above b's (paired: the 95% interval of the difference above 0), -1 if surely
    below, 0 if tied; each the worst substrate's, resampled with the same seeds for every substrate."""
    d = worst_resampled(a["levels"], idx)[key] - worst_resampled(b["levels"], idx)[key]
    lo, hi = np.percentile(d, (2.5, 97.5))
    return 1 if lo > 0 else -1 if hi < 0 else 0


def table() -> str:
    rs = rows()
    illegal = [r for r in rs if "illegal" in r]
    rs = [r for r in rs if "illegal" not in r]
    idx = boot_index(len(SEEDS))
    good = sorted((r for r in rs if r["job"]), key=lambda r: (r["parts"], -r["v"]["efficiency"]))
    every = {key: {(a["name"], b["name"]): compare(a, b, idx, key) for a in good for b in good if a is not b}
             for key, *_ in OBJECTIVES}
    val = lambda r, key: r["v"][key]
    for r in good:                                      # the front (parts, efficiency, gain), and how sure each place is
        rivals = [o for o in good if o is not r and o["parts"] <= r["parts"]]
        r["pareto"] = not any(all(val(o, k) >= val(r, k) for k, *_ in OBJECTIVES) and
                              (o["parts"], *(val(o, k) for k, *_ in OBJECTIVES)) !=
                              (r["parts"], *(val(r, k) for k, *_ in OBJECTIVES)) for o in rivals)
        cmp = lambda o: [every[k][(o["name"], r["name"])] for k, *_ in OBJECTIVES]
        if r["pareto"]:                                 # rivals as simple that no measure surely puts below it
            tied = [o["name"] for o in rivals if all(c >= 0 for c in cmp(o))]
            r["place"] = "Pareto, sure" if not tied else f"Pareto, but tied with {', '.join(tied)}"
        else:                                           # surely beaten: as simple, surely above on one, below on none
            beaten = [o["name"] for o in rivals if all(c >= 0 for c in cmp(o)) and
                      (o["parts"] < r["parts"] or any(c > 0 for c in cmp(o)))]
            r["place"] = (f"surely beaten by {', '.join(beaten)}" if beaten else "off the front, within noise")
    f2 = lambda x: f"{x:.2f}" if np.isfinite(x) else "inf"
    ci = lambda r, key, d: f"[{r['v']['ci'][key][0]:.{d}f}, {r['v']['ci'][key][1]:.{d}f}]"

    def line(r):
        v = r["v"]
        return (f"| {r['name']} | {r['parts']} | {r['area']:.0f} | {v['efficiency']:.2f} {ci(r, 'efficiency', 2)}"
                f" | {v['gain']:.2f} {ci(r, 'gain', 2)} | {v['food']:.2f} | {v['poison']:.2f} | {v['firings']:.0f}"
                f" | {r['power'] / 1e-9:.1f} | {v['net']:+.2f} [{v['lo']:+.2f}, {v['hi']:+.2f}] | {v['thrift']:.1f}"
                f" | {f2(v['last'])} [{f2(v['ci']['last'][0])}, {f2(v['ci']['last'][1])}] |"
                f" {v['stranded']:.0%} [{v['ci']['stranded'][0]:.0%}, {v['ci']['stranded'][1]:.0%}] |"
                + (f" {'sure' if r['sure'] else 'marginal'} | {r['place']} |" if r["job"] else
                   f" {', '.join(r['fails'])} ({'surely' if r['sure'] else 'marginal'}) |"))
    head = ("| design | parts | area | efficiency [95%] | gain rate [95%] | food | poison | firings | power (nW) | score [95%] |"
            " thrift | food:poison, last third [95%] | stranded [95%] |")
    if good:
        least = good[0]
        headline = ["**The three objectives** (the user's, 2026-10-22), each among the designs doing the job:", "",
                    f"1. the simplest brain doing the job: {least['name']}, {least['parts']} parts (doing it"
                    f" {'surely' if least['sure'] else 'marginally: an interval crosses a limit'}; efficiency"
                    f" {val(least, 'efficiency'):.2f}, gain rate {val(least, 'gain'):.2f})."]
        for n, (key, word, unit, best, why) in enumerate(OBJECTIVES, 2):
            top = max(good, key=lambda r: (val(r, key), -r["parts"]))
            ties = [o["name"] for o in good if o is not top and every[key][(top["name"], o["name"])] < 1]
            headline.append(f"{n}. {why}: {best}, {top['name']} ({top['parts']} parts), {val(top, key):.2f}"
                            f" {ci(top, key, 2)}; " + ("surely above every other design doing the job." if not
                                                       ties else f"tied within noise with {', '.join(ties)}."))
        headline = "\n".join(headline)
    else:
        headline = "Nothing does the job."
    mark = {1: "above", -1: "below", 0: "tied"}
    matrices = []
    for key, word, unit, *_ in OBJECTIVES:
        matrices += ["", f"### {word.capitalize()} ({unit}), design against design (paired)", "",
                     f"| {word}: row against column | " + " | ".join(r["name"] for r in good) + " |",
                     "|---|" + "---|" * len(good)]
        for a in good:
            matrices.append(f"| {a['name']} | " + " | ".join("" if a is b else mark[every[key][(a["name"], b["name"])]]
                                                            for b in good) + " |")
    cols = head.count("|") - 1
    out = ["# League table: the minimal circuit search", "",
           "Generated by `python -m minimal.league` (minimal/NOTEBOOK.md). Every design re-validated under the current",
           f"rules: {len(SEEDS)} held-out seeds x 2 with the noise of {', '.join(JUDGED)} (mixed_feedback.py), every",
           "measure the worst substrate's and the job required with each, with the simulator's mismatch, within the",
           f"honesty limits (units.py). **Job**: food at least {JOB[0]:g} per {SPAN:g} s, food:poison at least {JOB[1]:g}",
           f"in the last third, at most {JOB[2]:.0%} of lives stranded (no food in the last third). **Parts**:",
           "capacitors, resistors, diodes, transistors. **Area**: chip area by analogy with subthreshold analogue CMOS, in",
           "unit transistors (minimal/spec.py, AREA; units.py; shown, not ranked on).",
           f"**Meals gained**: food, less {COST:g} for each poison (as in the score). **Efficiency**: meals gained per meal",
           f"spent: resting ({si(METABOLISM, 'W')}, a meal being worth {si(MEAL, 'J')}), moving and thinking, priced as in",
           "the score; above 1 a creature gains, and both haste (fuel) and dawdling (resting cost) lower it. **Gain rate**:",
           f"meals gained per {SPAN:g} s, energy free. **Food**, **poison**, **firings**: per {SPAN:g} s. **Power**: what",
           "the circuit's devices dissipate, each its current times the voltage across it (mixed_feedback._step).",
           f"**Score**: as in the notebook, moving and the circuit's power charged in meals (a firing {si(FIRING, 'J')},",
           f"the circuit's energy at a meal per {si(MEAL, 'J')}). **Thrift**: food per 1,000 firings (shown, not ranked).",
           "",
           "**Confidence.** [95%]: bootstrap intervals over the seeds (each seed's two lives kept together; stranded, a",
           "Wilson interval over lives). **Job sure**: every interval within the job's limits; **marginal**: one crosses a",
           "limit, so other seeds might decide otherwise. **Place**: on the Pareto front of the three objectives (no design",
           "doing the job has as few parts and as high an efficiency and gain rate) or off it, and how sure: designs are",
           "compared paired (the same seeds), one surely above another on a measure only if the 95% interval of the",
           "difference excludes 0. Surely beaten: by a design as simple, surely above on a measure and below on none.",
           "Parts are counted exactly. Listed by parts, then efficiency.",
           "", headline, "", "## Doing the job", "", head + " job | place |", "|---" * (cols + 2) + "|"]
    out += [line(r) for r in good]
    out += matrices
    out += ["", "## Near misses (not doing the job)", "", head + " fails |", "|---" * (cols + 1) + "|"]
    for r in sorted((r for r in rs if not r["job"]), key=lambda r: (r["parts"], -r["v"]["efficiency"])):
        out.append(line(r))
    out += ["", "## Refused by the rules (tuned before a rule existed)", "", "| design | parts | why |", "|---|---|---|"]
    out += [f"| {r['name']} | {r['parts']} | {r['illegal']} |" for r in sorted(illegal, key=lambda r: r["parts"])]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    t = table()
    open(os.path.join(HERE, "LEAGUE.md"), "w").write(t)
    print(t)
