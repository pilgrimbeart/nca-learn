"""The league table of the minimal circuit search (minimal/LEAGUE.md): every tuned design in minimal/results,
re-validated under the current rules (held-out lives, with the simulator's noise and mismatch, the slew limit).

Entry: doing the job (minimal/spec.py, JOB), within the slew limit. Two dimensions, kept apart (the user's decision,
2026-10-21): parts, down, and the body's efficiency (meals eaten per meal spent resting, moving and thinking), up; so the table says what
the simplest circuit achieves, and the best efficiency found at any complexity. Pareto: no other design that does
the job has both as few parts and as high an efficiency. Listed by parts, then efficiency. The near misses (failing
the job) are listed apart: a small, efficient near miss is worth knowing about.

Every relative position is tested (the user's question, 2026-10-21: which are high-confidence results?): every
design lives the same held-out seeds, so two designs' efficiencies are compared paired, by a bootstrap over seeds
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

from minimal.spec import (ENERGY, JOB, NEED, SLEW, THRUST, area, boot_index, pack, parts, per_pair, resampled,  # noqa: E402
                          score, slew, summary, unpack)

HERE = os.path.dirname(__file__)
CACHE = os.path.join(HERE, "results", "league_cache.json")
SKIP = ("_round1", "_unlimited", "_start", "_feasible", "_fixednoise", "league_cache", "evolve", "C_tuned")  # (copies)
# (results tuned under the old noise, before 2026-10-20's model, are re-validated under the new like any other)
SEEDS = range(100, 164)         # the held-out seeds (minimal/search.py, validate)


def validated(spec):
    """The held-out lives and their summary, cached by the spec and the simulating and scoring code."""
    import inspect
    import minimal.fastlife
    import minimal.spec
    import mixed_feedback
    code = inspect.getsource(minimal.spec) + inspect.getsource(minimal.fastlife) + inspect.getsource(mixed_feedback)
    key = hashlib.sha1((json.dumps(spec, sort_keys=True) + code).encode()).hexdigest()
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    if key not in cache:
        cache = {k: v for k, v in cache.items() if isinstance(v, dict) and "lives" in v}     # (older entries go)
        cache[key] = {"lives": pack(score([spec], seeds=SEEDS)[0])}
        json.dump(cache, open(CACHE, "w"))
    lives = unpack(cache[key]["lives"])
    return lives, summary(lives)


def rows():
    from minimal.designs import DESIGNS
    out = []
    for path in sorted(glob.glob(os.path.join(HERE, "results", "*.json"))):
        name = os.path.basename(path)[:-5]
        if any(s in name for s in SKIP):
            continue
        r = json.load(open(path))
        if "spec" in r:                                 # a circuit the open search found (minimal/evolve.py)
            spec = r["spec"]
        elif r.get("design") in DESIGNS:
            spec = DESIGNS[r["design"]][0](r["params"])
        else:
            continue
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
        if sl > SLEW:
            fails.append(f"slew {sl:.0f}")
        ci = v["ci"]
        sure = ci["food"][0] >= JOB[0] and ci["last"][0] >= JOB[1] and ci["stranded"][1] <= JOB[2] and sl <= SLEW
        surely_not = ci["food"][1] < JOB[0] or ci["last"][1] < JOB[1] or ci["stranded"][0] > JOB[2] or sl > SLEW
        out.append({"name": name, "parts": pt["total"], "blocks": pt["nodes"] + pt["elements"], "area": area(spec),
                    "power": v["power"], "v": v, "job": not fails, "fails": fails, "pairs": per_pair(lives),
                    "sure": sure if not fails else surely_not})
    return out


PRIORITIES = (("efficiency", "efficiency", "meals eaten per meal spent", "the most efficient",
               "energy all told, resting included, so time matters too"),
              ("food", "speed", "food per 1,000 ticks", "the fastest", "speed: food as fast as possible"),
              ("thrift", "thrift", "food per 1,000 firings", "the thriftiest", "fuel: time no object"))


def compare(a, b, idx, key="efficiency") -> int:
    """+1 if a's measure (key) is surely above b's (paired: the 95% interval of the difference above 0), -1 if surely
    below, 0 if tied."""
    d = resampled(a["pairs"], idx)[key] - resampled(b["pairs"], idx)[key]
    lo, hi = np.percentile(d, (2.5, 97.5))
    return 1 if lo > 0 else -1 if hi < 0 else 0


def table() -> str:
    rs = rows()
    illegal = [r for r in rs if "illegal" in r]
    rs = [r for r in rs if "illegal" not in r]
    idx = boot_index(len(SEEDS))
    good = sorted((r for r in rs if r["job"]), key=lambda r: (r["parts"], -r["v"]["efficiency"]))
    every = {key: {(a["name"], b["name"]): compare(a, b, idx, key) for a in good for b in good if a is not b}
             for key, *_ in PRIORITIES}
    vs = every["efficiency"]
    for r in rs:
        r["eff"] = r["v"]["efficiency"]
    for r in good:                                      # the front, and how sure each place on or off it is
        rivals = [o for o in good if o is not r and o["parts"] <= r["parts"]]
        r["pareto"] = not any(o["eff"] >= r["eff"] and (o["parts"], o["eff"]) != (r["parts"], r["eff"]) for o in rivals)
        if r["pareto"]:
            tied = [o["name"] for o in rivals if vs[(r["name"], o["name"])] < 1]
            r["place"] = "Pareto, sure" if not tied else f"Pareto, but tied with {', '.join(tied)}"
        else:
            beaten = [o["name"] for o in rivals if vs[(o["name"], r["name"])] == 1]
            tied = [o["name"] for o in rivals if vs[(o["name"], r["name"])] == 0 and o["eff"] > r["eff"]]
            r["place"] = (f"surely beaten by {', '.join(beaten)}" if beaten else
                          f"off the front, but tied with {', '.join(tied)}")
    f2 = lambda x: f"{x:.2f}" if np.isfinite(x) else "inf"

    def line(r):
        v, ci = r["v"], r["v"]["ci"]
        return (f"| {r['name']} | {r['parts']} | {r['area']:.0f} | {r['eff']:.2f} [{ci['efficiency'][0]:.2f}, {ci['efficiency'][1]:.2f}]"
                f" | {v['thrift']:.1f} [{ci['thrift'][0]:.1f}, {ci['thrift'][1]:.1f}] | {v['firings']:.0f} | {r['power']:.1f} | {v['net']:+.2f} [{v['lo']:+.2f}, {v['hi']:+.2f}] |"
                f" {v['food']:.2f} [{ci['food'][0]:.2f}, {ci['food'][1]:.2f}] | {f2(v['last'])} [{f2(ci['last'][0])},"
                f" {f2(ci['last'][1])}] | {v['stranded']:.0%} [{ci['stranded'][0]:.0%}, {ci['stranded'][1]:.0%}] |"
                + (f" {'sure' if r['sure'] else 'marginal'} | {r['place']} |" if r["job"] else
                   f" {', '.join(r['fails'])} ({'surely' if r['sure'] else 'marginal'}) |"))
    head = ("| design | parts | area | efficiency [95%] | thrift [95%] | firings | power | score [95%] | speed: food [95%] |"
            " food:poison, last third [95%] | stranded [95%] |")
    val = lambda r, key: r["v"][key]
    ci = lambda r, key, d: f"[{r['v']['ci'][key][0]:.{d}f}, {r['v']['ci'][key][1]:.{d}f}]"
    if good:
        least = good[0]
        headline = [f"**The simplest circuit doing the job**: {least['name']} ({least['parts']} parts; doing the job"
                    f" {'surely' if least['sure'] else 'marginally: an interval crosses a limit'}), efficiency"
                    f" {least['eff']:.2f} {ci(least, 'efficiency', 2)}, speed {val(least, 'food'):.2f}"
                    f" {ci(least, 'food', 2)}, thrift {val(least, 'thrift'):.1f} {ci(least, 'thrift', 1)}.", "",
                    "**The best doing the job, by what a survival situation makes scarce:**", ""]
        for key, word, unit, best, why in PRIORITIES:
            top = max(good, key=lambda r: (val(r, key), -r["parts"]))
            ties = [o["name"] for o in good if o is not top and every[key][(top["name"], o["name"])] < 1]
            d = 1 if key == "thrift" else 2
            headline.append(f"- {why}: {best}, {top['name']} ({top['parts']} parts), {val(top, key):.{d}f}"
                            f" {ci(top, key, d)} {unit}; " + ("surely above every other design doing the job." if not
                                                               ties else f"tied within noise with {', '.join(ties)}."))
        headline = "\n".join(headline)
    else:
        headline = "Nothing does the job."
    mark = {1: "above", -1: "below", 0: "tied"}
    matrices = []
    for key, word, unit, *_ in PRIORITIES:
        matrices += ["", f"### {word.capitalize()} ({unit}), design against design (paired)", "",
                     f"| {word}: row against column | " + " | ".join(r["name"] for r in good) + " |",
                     "|---|" + "---|" * len(good)]
        for a in good:
            matrices.append(f"| {a['name']} | " + " | ".join("" if a is b else mark[every[key][(a["name"], b["name"])]]
                                                            for b in good) + " |")
    out = ["# League table: the minimal circuit search", "",
           "Generated by `python -m minimal.league` (minimal/NOTEBOOK.md). Every design re-validated under the current",
           f"rules: {len(SEEDS)} held-out seeds x 2, with the simulator's noise and mismatch (mixed_feedback.py), within the slew",
           f"limit ({SLEW:g} V per circuit tick). **Job**: food at least {JOB[0]:g} per 1,000 ticks, food:poison at least",
           f"{JOB[1]:g} in the last third, at most {JOB[2]:.0%} of lives stranded (no food in the last third). **Parts**:",
           "capacitors, resistors, diodes, transistors. **Area**: chip area by analogy with subthreshold analogue CMOS, in",
           "unit transistors (minimal/spec.py, AREA; the capacitor's price a guess; shown, not ranked on). **Efficiency**: the body's, meals eaten per meal spent: resting",
           f"(the {NEED:g} meal per 1,000 ticks every creature needs), moving and thinking, priced as in the score; above 1",
           "a creature gains, and both haste (fuel) and dawdling (resting cost) lower it. **Thrift**: food per 1,000",
           "thruster firings (fuel alone, time no object). **Speed**: food per 1,000 ticks.",
           "**Firings**: per 1,000 ticks. **Power**: what the circuit's devices dissipate, each its current times the",
           "voltage across it (mixed_feedback._step). **Score**: as in the notebook, moving and the circuit's power charged",
           f"in meals (a firing {THRUST:g} of a meal, a unit of power {ENERGY:g} per 1,000 ticks).",
           "",
           "**Confidence.** [95%]: bootstrap intervals over the seeds (each seed's two lives kept together; stranded, a",
           "Wilson interval over lives). **Job sure**: every interval within the job's limits; **marginal**: one crosses a",
           "limit, so other seeds might decide otherwise. **Place**: on the Pareto front (no design doing the job has as",
           "few parts and as high an efficiency) or off it, and against which designs that is sure: efficiencies are",
           "compared paired (the same seeds), surely different only if the 95% interval of the difference excludes 0; so",
           "are speed and thrift, below.",
           "Parts are counted exactly. Listed by parts, then efficiency.",
           "", headline, "", "## Doing the job", "", head + " job | place |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    out += [line(r) for r in good]
    out += matrices
    out += ["", "## Near misses (not doing the job)", "", head + " fails |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted((r for r in rs if not r["job"]), key=lambda r: (r["parts"], -r["eff"])):
        out.append(line(r))
    out += ["", "## Refused by the rules (tuned before a rule existed)", "", "| design | parts | why |", "|---|---|---|"]
    out += [f"| {r['name']} | {r['parts']} | {r['illegal']} |" for r in sorted(illegal, key=lambda r: r["parts"])]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    t = table()
    open(os.path.join(HERE, "LEAGUE.md"), "w").write(t)
    print(t)
