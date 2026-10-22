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
from units import TICK  # noqa: E402

SECONDS = 100.0     # a life
# the recruiting circuit as E2-E3 ran it (before the defaults became E6's R4), pinned for reproducibility
E3 = dict(sharp=False, once=False, frustrate=0.3, grow_at=0.8, hold="T")
SAMPLE = 1.0        # s between samples of a brain's slow nodes


def one(job):
    """(make, seed, poison, seconds, setup) -> a record of the life: meals by third after moving (food, poison,
    seconds), bridges grown (when, in seconds, on whose sensor, to which motor), samples of frustration and help, and
    the taste neuron's synapses at the end."""
    make, seed, poison, seconds, setup = job
    ticks, every = int(round(seconds / TICK)), int(round(SAMPLE / TICK))
    lf = Life(seed, poison, brain=make)
    b = lf.brain
    if setup is not None:
        setup(lf)
    role = {b.sensors[lf.sensor[c]]: ("poison" if c == poison else "food") if poison else c for c in COLOURS}
    F, H, crossed = [], [], {}
    while lf.t < ticks:
        lf.step()
        if getattr(lf, "schedule", None) and lf.t == lf.schedule[0]:     # an intervention at a given tick (a count)
            lf.schedule[1](lf)
        for (s, m), x in getattr(b, "sprout", {}).items():     # when each sprout first reached the growth level
            if (s, m) not in crossed and b.circuit.V[x] > b.grow_at:
                crossed[(s, m)] = lf.t * TICK
        if lf.t % every == 0 and hasattr(b, "F"):
            F.append(float(b.circuit.V[b.F]))
            H.append({role[s]: float(b.circuit.V[h]) for s, h in b.help.items()})
    start = lf.moving if lf.moving is not None else ticks
    thirds = []
    for i in range(3):
        a, z = start + i * (ticks - start) / 3, start + (i + 1) * (ticks - start) / 3
        part = [c for t, c in lf.meals if a <= t < z]
        thirds.append((sum(c != poison for c in part), sum(c == poison for c in part), (z - a) * TICK))
    names = {b.sensors[lf.sensor[c]]: (("poison" if c == poison else "food") if poison else c) + " eye" for c in COLOURS}
    names.update({b.motors[lf.motor[t]]: "motor" for t in ("left", "right")})
    if hasattr(b, "T"):
        names[b.T] = "T"
    name = lambda n: names.get(n, b.circuit.names[n] if hasattr(b, "circuit") else str(n))
    recruits = []
    for r in getattr(b, "report", lambda: [])():         # a healing circuit's recruits, in the body's terms
        on = r["on"]
        if on is None:
            what = "nothing"
        elif on[0] == "gate":
            _, (to, frm, _) = b.circuit.elements[on[1]]
            what = f"gate {name(frm)} -> {name(to)}"
        else:
            what = f"{on[0]} {name(on[1])}"
        recruits.append((r["tick"] * TICK, r["wave"], what, {name(x): round(w, 2) for x, w in r["listen"].items()},
                         r.get("switches", 0), r.get("since", r["tick"]) * TICK))
    return {"thirds": thirds, "recruits": recruits,
            "bridges": [(t * TICK, role[s], b.circuit.names[m]) for t, s, m in getattr(b, "bridges", [])],
            "F": F, "help": H,
            "crossed": sorted((t, role[s], b.circuit.names[m]) for (s, m), t in crossed.items()),
            "W": {role[s]: float(b.circuit.V[w]) for s, w in b.W.items()} if hasattr(b, "W") else {}}


def run(make, lives=64, seconds=SECONDS, all_food=False, setup=None, first_seed=0):
    """lives lives of the brain make builds (a name, or a function from the seed to a brain); setup(life), if given,
    runs once after birth (an experimenter's intervention, such as an oracle placing a bridge). first_seed: where the
    seeds start (held-out lives, for confirming a choice made on others)."""
    jobs = [(make, first_seed + i // 2, None if all_food else COLOURS[i % 2], seconds, setup) for i in range(lives)]
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
    """Food and poison eaten per 10 s after moving (all of each life)."""
    food = sum(f for r in records for f, _, _ in r["thirds"])
    bad = sum(p for r in records for _, p, _ in r["thirds"])
    t = sum(t for r in records for _, _, t in r["thirds"])
    return 10 * food / t, 10 * bad / t


def summary(name, records, all_food=False):
    """One line: rates, and food:poison (whole life, and last third) with intervals; or, in all-food lives, food per
    10 s. Plus bridges grown."""
    food, bad = rates(records)
    grown = [b for r in records for b in r["bridges"]]
    where = {}
    for _, who, _ in grown:
        where[who] = where.get(who, 0) + 1
    bridges = f"bridges {len(grown)} in {sum(1 for r in records if r['bridges'])} of {len(records)} lives" + \
              (f" ({', '.join(f'{k} {v}' for k, v in sorted(where.items()))})" if where else "")
    if all_food:
        return f"{name:34s} all food: food {food:.2f} per 10 s; {bridges}"
    w, wlo, whi = ratio_ci(records)
    l, llo, lhi = ratio_ci(records, third=2)
    return (f"{name:34s} food {food:.2f}, poison {bad:.2f} per 10 s; food:poison {w:.2f} [{wlo:.2f}, {whi:.2f}],"
            f" last third {l:.2f} [{llo:.2f}, {lhi:.2f}]; {bridges}")


def per_life(records):
    """Per life: food, poison and net (food - poison) eaten per 10 s after moving."""
    out = []
    for r in records:
        t = sum(t for _, _, t in r["thirds"])
        f, p = sum(f for f, _, _ in r["thirds"]), sum(p for _, p, _ in r["thirds"])
        out.append((10 * f / t, 10 * p / t, 10 * (f - p) / t) if t else (0.0, 0.0, 0.0))  # never moved: none
    return np.array(out)


def paired(a, b, boots=2000, seed=0):
    """b minus a, life for life (the same seeds and, with STREAMS, the same noise): the mean difference in net food
    per 10 s and its bootstrap 95% interval."""
    d = per_life(b)[:, 2] - per_life(a)[:, 2]
    rng = np.random.default_rng(seed)
    boot = d[rng.integers(len(d), size=(boots, len(d)))].mean(1)
    return d.mean(), np.percentile(boot, 2.5), np.percentile(boot, 97.5)


BOARD = os.path.join(os.path.dirname(__file__), "results", "leaderboard.json")


def choices(records):
    """What recruits settled on, over poison lives: counts of each final choice (wave 1, and later waves)."""
    out = {}
    for r in records:
        for _, wave, what, *_ in r.get("recruits", []):
            key = what if wave == 1 else f"wave {wave}: {what}"
            out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def veer_share(records):
    """The share of poison lives in which some recruit settled on turning down the poison eye's synapse to a motor."""
    return np.mean([any(w.startswith("gate poison eye -> motor") for _, _, w, *_ in r.get("recruits", []))
                    or any(who == "poison" for _, who, _ in r.get("bridges", []))    # (the guided bridge's)
                    for r in records])


def board(name, seconds, poison, food, base_poison, base_food, note=""):
    """Add (or replace) a row on the leaderboard (results/leaderboard.json) and rewrite LEADERBOARD.md."""
    import json
    rows = json.load(open(BOARD)) if os.path.exists(BOARD) else []
    d, lo, hi = paired(base_poison, poison)
    e, elo, ehi = paired(base_food, food)
    last, llo, lhi = ratio_ci(poison, third=2)
    row = {"name": name, "seconds": seconds, "lives": len(poison), "net": d, "net_lo": lo, "net_hi": hi,
           "food_net": e, "food_lo": elo, "food_hi": ehi, "last": last, "last_lo": llo, "last_hi": lhi,
           "veer": float(veer_share(poison)), "food_recruits": sum(len(r.get("recruits", [])) for r in food),
           "note": note}
    rows = [r for r in rows if not (r["name"] == name and r["seconds"] == seconds)] + [row]
    json.dump(rows, open(BOARD, "w"), indent=1)
    lines = ["# Leaderboard: rules for recruiting (experiments/NOTEBOOK.md)", "",
             "Net food per 10 s against the knowing circuit (no recruitment), paired life for life (same seeds",
             "and noise), with bootstrap 95% intervals; in poison lives and in all-food lives (where nothing should",
             "be recruited); food:poison over the last third of life; the share of poison lives in which a recruit",
             "settled on turning down the poison eye's synapse to a motor (a veer); recruits grown in all-food lives.",
             "Generated by experiments/common.py; rows are comparable only within one life length. All rows ran under the simulator",
             "before 2026-10-20 (a fixed noise per node, no mismatch) and stand only for it.", "",
             "Rule names (the healing circuit, brains/healing.py; terms in the README): *wsls*, win-stay lose-shift;",
             "*listening full*, the recruit hears every attached neuron (otherwise it learns which predict pain;",
             "*inherit*, it shares its parent's learned strengths); *inhibit/gate only*, a menu without exciting;",
             "*neurons only*, without turning down synapses; *inputs:*, the synapses on the menu are those arriving",
             "at attached neurons (otherwise those leaving them); *share:*, options judged by the share of bad",
             "tastes after them (otherwise by rate); *gated:*, power gating (same behaviour); *cascade*, a recruit",
             "that fails grows another, one step further out; *root:*, every wave frustrated by T's own flag;",
             "*retire*, a recruit that fails stands down; *starve*, an option followed by no good tastes tires;",
             "*early*, *shadow*, recruiting before frustration peaks; *held out*, fresh lives (seeds from 100).", ""]
    for t in sorted({r["seconds"] for r in rows}):
        lines += [f"## Lives of {t:g} s", "",
                  "| rank | rule | lives | net food, poison lives | all-food lives | food:poison, last third | veer | recruits in all-food | note |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for k, r in enumerate(sorted((r for r in rows if r["seconds"] == t), key=lambda r: -r["net"])):
            lines.append(f"| {k + 1} | {r['name']} | {r['lives']} | {r['net']:+.2f} [{r['net_lo']:+.2f}, {r['net_hi']:+.2f}]"
                         f" | {r['food_net']:+.2f} [{r['food_lo']:+.2f}, {r['food_hi']:+.2f}]"
                         f" | {r['last']:.2f} [{r['last_lo']:.2f}, {r['last_hi']:.2f}] | {r['veer']:.0%}"
                         f" | {r['food_recruits']} | {r['note']} |")
        lines.append("")
    open(os.path.join(os.path.dirname(__file__), "LEADERBOARD.md"), "w").write("\n".join(lines))
