"""Measures recruitment's local signals (RECRUITMENT.md) by watching a circuit brain from outside: from a log of what
went in and what each neuron did, the quantities a neuron could know locally, by the role the body gave it (poison's
sensor, food's sensor, the motors). Watching may compute anything; nothing here feeds back into the brain. Lives with
poison (half red, half blue) and all-food lives, where nothing should stir. Over the second half of each life.

  involvement: how active the neuron was (its own spikes, fading over ELIGIBLE ticks) before tastes, good or bad;
  implication: how much more before bad tastes than good; confidence: implication over involvement (+1: my activity
  predicts pain; -1: a good taste); the same for what it received (stimuli, spikes along incoming synapses). Only the
  sensors feel taste; for the motors these are the observer's view, which they can't have.
  fires: the share of its input events after which it fired (that tick or the next); decided: |2 fires - 1| (1: its
  firing is certain, given its inputs); miss: for events that didn't make it fire, how far its highest voltage stayed
  below its threshold, as a share of the way from rest (0: a near miss).
  excitability: its knob, from 1 (empty) to 0 (full).
  For a brain with a taste neuron T (brains/knowing.py): each sensor's synapse onto T (0..1); T's spikes per 1,000
  ticks; anticipation: the share of poison meals T fired before (within WINDOW ticks before the taste, so its innate
  answer to the taste doesn't count); false alarms: the same for food meals; and its confidence: when it fired before a
  meal, how often the meal was poison.

    python recruit_test.py [LIVES] [TICKS] [BRAIN]
"""

import multiprocessing
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from creature import COLOURS, Life

ELIGIBLE = 10.0     # ticks over which a neuron's activity traces fade
THRESHOLD = -2.82   # the edge of a circuit neuron's fast positive feedback: where 0.5 - 2 sech^2(V + 1.5) = 0
TASTES, EVIDENCE = 5, 0.05  # with fewer tastes, or less involvement, no evidence: no confidence
WINDOW = 10         # ticks before a meal in which a spike of T counts as anticipating it


def watch(lf, units, ticks):
    """Runs the life, logging; returns, per neuron, the quantities above."""
    b = lf.brain
    b.log = []
    while lf.t < ticks:
        lf.step()
    c = b.circuit
    pre = {u: [f for (_, (t, f, _)) in c.elements if t == u and f in units and f != u] for u in units}
    fade = np.exp(-1.0 / ELIGIBLE)
    e, g = {u: 0.0 for u in units}, {u: 0.0 for u in units}
    at = {u: {"inv": [], "imp": [], "inv_got": [], "imp_got": []} for u in units}
    fired, miss, rest = ({u: [] for u in units} for _ in range(3))
    log, half = b.log, len(b.log) // 2
    for t, (inj, spikes, vmax, _) in enumerate(log):
        taste = np.sign(inj[b.taste_node])
        for u in units:
            got = (1.0 if inj[u] > 0 and u in b.sensors else 0.0) + sum(spikes[f] for f in pre[u])
            e[u] = e[u] * fade + spikes[u]
            g[u] = g[u] * fade + got
            if t < half:
                continue
            if taste != 0:
                at[u]["inv"].append(min(e[u], 1.0))
                at[u]["imp"].append(-taste * min(e[u], 1.0))
                at[u]["inv_got"].append(min(g[u], 1.0))
                at[u]["imp_got"].append(-taste * min(g[u], 1.0))
            if got > 0 and t + 1 < len(log):
                made = spikes[u] > 0 or log[t + 1][1][u] > 0
                fired[u].append(1.0 if made else 0.0)
                if not made:
                    miss[u].append(max(vmax[u], log[t + 1][2][u]))
            elif spikes[u] == 0 and (t == 0 or log[t - 1][1][u] == 0):
                rest[u].append(vmax[u])
    out = {}
    for u in units:
        a = {k: np.mean(v) if v else np.nan for k, v in at[u].items()}
        n = len(at[u]["inv"])
        conf = lambda imp, inv: a[imp] / a[inv] if n >= TASTES and a[inv] > EVIDENCE else np.nan
        r = np.mean(rest[u]) if rest[u] else np.nan
        f = np.mean(fired[u]) if fired[u] else np.nan
        out[u] = {"involve": a["inv"], "confidence": conf("imp", "inv"), "involve_got": a["inv_got"],
                  "confidence_got": conf("imp_got", "inv_got"), "fires": f, "decided": abs(2 * f - 1),
                  "miss": np.mean([min(max((THRESHOLD - p) / (THRESHOLD - r), 0.0), 1.0) for p in miss[u]])
                  if miss[u] else np.nan, "rest": r}
    return out


def taste_neuron(lf, poison, ticks):
    """The taste neuron, watched over the second half of the life: what it learned, and whether it anticipates."""
    b, half = lf.brain, ticks // 2
    spiked = [t for t, (_, spikes, _, _) in enumerate(b.log) if t >= half and spikes[b.T] > 0]
    before = lambda m: any(m - WINDOW < t <= m for t in spiked)
    meals = [(t, c) for t, c in lf.meals if t >= half]
    bad = [before(t) for t, c in meals if c == poison]
    good = [before(t) for t, c in meals if c != poison]
    synapse = lambda colour: float(b.circuit.V[b.W[b.sensors[lf.sensor[colour]]]])
    out = {"T": {"spikes per 1,000": 1000 * len(spiked) / (ticks - half),
                 "anticipates poison": np.mean(bad) if bad else np.nan,
                 "false alarms": np.mean(good) if good else np.nan,
                 "confidence": sum(bad) / (sum(bad) + sum(good)) if sum(bad) + sum(good) else np.nan}}
    if poison:
        out["T"]["synapse from poison's sensor"] = synapse(poison)
        out["T"]["from food's sensor"] = synapse("blue" if poison == "red" else "red")
    else:
        out["T"]["synapse from a sensor"] = (synapse("red") + synapse("blue")) / 2
    return out


def life(job):
    brain, seed, poison, ticks = job
    lf = Life(seed, poison, brain=brain)
    b = lf.brain
    units = b.sensors + b.motors
    stats = watch(lf, units, ticks)
    sensor = lambda colour: b.sensors[lf.sensor[colour]]
    roles = ({"poison's sensor": [sensor(poison)], "food's sensor": [sensor("blue" if poison == "red" else "red")]}
             if poison else {"a sensor": [sensor("red"), sensor("blue")]})
    roles["motors"] = list(b.motors)
    traces = {}
    for r, us in roles.items():
        traces[r] = {k: float(np.nanmean([stats[u][k] for u in us])) if any(np.isfinite(stats[u][k]) for u in us)
                     else np.nan for k in stats[us[0]]}
        if hasattr(b, "knob"):
            traces[r]["excitability"] = float(np.mean([1.0 - b.circuit.V[b.knob[u]] for u in us]))
    if hasattr(b, "T"):
        traces.update(taste_neuron(lf, poison, ticks))
    start = lf.moving if lf.moving is not None else ticks
    food = sum(1 for t, c in lf.meals if t >= start and c != poison)
    bad = sum(1 for t, c in lf.meals if t >= start and c == poison)
    return traces, food, bad, ticks - start


if __name__ == "__main__":
    lives = int(sys.argv[1]) if len(sys.argv) > 1 else 32
    ticks = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    brain = sys.argv[3] if len(sys.argv) > 3 else "adjusting-circuit"
    for world in ("poison", "all food"):
        jobs = [(brain, i // 2, COLOURS[i % 2] if world == "poison" else None, ticks) for i in range(lives)]
        with ProcessPoolExecutor(mp_context=multiprocessing.get_context("spawn")) as pool:
            results = list(pool.map(life, jobs))
        food, bad, t = (sum(r[k] for r in results) for k in (1, 2, 3))
        ratio = f"{food / bad:.1f}" if bad else f"{food}:0"
        print(f"{brain}, {world} lives ({lives}): food {1000 * food / t:.2f} and poison {1000 * bad / t:.2f} per"
              f" 1,000 ticks (food:poison {ratio})")
        for role in results[0][0]:
            vals = []
            for k in results[0][0][role]:
                x = [r[0][role][k] for r in results if np.isfinite(r[0][role][k])]
                vals.append(f"{k} {np.mean(x):+.2f}" if x else f"{k} (no evidence)")
            print(f"  {role:16s} {'  '.join(vals)}")
