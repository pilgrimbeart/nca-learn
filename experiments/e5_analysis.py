"""E5 (experiments/NOTEBOOK.md): (a) is R3's remaining shortfall against the oracle only the time before growth? A
time-matched oracle places O1 by hand at the very moment R3 grew its bridge in the same life. (b) How sensitive is R3 to
its two main settings? (c) Does it survive mismatch (every gain and bias a few percent off at birth), as robustness
through balance predicts, and how does the designed circuit fare? (d) What does the recruiting circuit cost?

    python -m experiments.e5_analysis [LIVES] [a] [b] [c] [d]
"""

import functools
import pickle
import sys

import numpy as np

from brains.designed import DesignedBrain
from brains.recruiting import RecruitingBrain
from creature import COLOURS, Life
from experiments.common import E3, paired, run, summary
from experiments.e3_growth import growth
from units import TICK

R3 = functools.partial(RecruitingBrain, **{**E3, "sharp": True, "once": True})
KNOWING = functools.partial(RecruitingBrain, grow=False, hold="T")


def insert_named(life, motor):
    b = life.brain
    b.insert_bridge(b.sensors[life.sensor[life.poison]], b.circuit.names.index(motor))


def time_matched(table, life):
    """Schedule O1 at the moment (s) R3 grew its (poison-sensor) bridge in this same life; none if it grew none."""
    when = table.get((life.brain.seed, life.poison))
    if when:
        life.schedule = (int(round(when[0] / TICK)), functools.partial(insert_named, motor=when[1]))


def mismatch(size, life, which="all"):
    """Gains and biases off by a random few percent (normal, sd size), fixed at birth. which: "all"; "intrinsic" (only
    each neuron's own fast and slow feedback elements); "other" (every other element: synapses, learning, growth); or
    "bias" (only the nodes' biases)."""
    c = life.brain.circuit
    rng = np.random.default_rng([life.brain.seed, 99])
    own = lambda link: link[0] == link[1]                       # an element on its own node: a neuron's feedback
    pick = {"all": lambda link: True, "intrinsic": own, "other": lambda link: not own(link), "bias": lambda link: False}
    c.elements = [((g * (1 + size * rng.standard_normal()) if pick[which](link) else g, o, sl, t, sg), link)
                  for (g, o, sl, t, sg), link in c.elements]
    if which in ("all", "bias"):
        c.nodes = [(bias * (1 + size * rng.standard_normal()),) + tuple(rest) for bias, *rest in c.nodes]


def cost(make, seed=0, poison="red", seconds=100.0):
    """Size and a static-energy proxy of the brain at the end of a life: nodes, elements, and the sum of every
    element's gain (each a transconductance amplifier drawing about its gain as bias current from the supply)."""
    lf = Life(seed, poison, brain=make)
    while lf.t * TICK < seconds:
        lf.step()
    c = lf.brain.circuit
    return len(c.names), len(c.elements), sum(abs(g) for (g, *_), _ in c.elements)


if __name__ == "__main__":
    lives = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 64
    parts = [p for p in "abcde" if p in sys.argv[1:]] or list("abcde")
    out = {}
    if "a" in parts:
        base, r3 = run(KNOWING, lives), run(R3, lives)
        table = {}
        for i, rec in enumerate(r3):
            mine = [(t, m) for t, who, m in rec["bridges"] if who == "poison"]
            if mine:
                table[(i // 2, COLOURS[i % 2])] = mine[0]
        tm = run(KNOWING, lives, setup=functools.partial(time_matched, table))
        o1 = run(KNOWING, lives, setup=functools.partial(time_matched, {k: (TICK, v[1]) for k, v in table.items()}))
        print(summary("R3", r3)); print(summary("time-matched oracle", tm)); print(summary("oracle from tick 1", o1))
        for name, x, y in (("R3 vs time-matched oracle", tm, r3), ("time-matched vs from-birth oracle", o1, tm),
                           ("R3 vs from-birth oracle", o1, r3)):
            d, lo, hi = paired(x, y)
            print(f"  {name:36s} {d:+.2f} [{lo:+.2f}, {hi:+.2f}]")
        out["a"] = (base, r3, tm, o1)
    if "b" in parts:
        base = run(KNOWING, lives)
        print()
        for name, kw in (("frustrate 0.2", dict(frustrate=0.2)), ("frustrate 0.3 (R3)", dict()),
                         ("frustrate 0.5", dict(frustrate=0.5)), ("frustrate 0.8", dict(frustrate=0.8)),
                         ("grow at 0.6", dict(grow_at=0.6)), ("grow at 0.95", dict(grow_at=0.95))):
            make = functools.partial(RecruitingBrain, **{**E3, "sharp": True, "once": True, **kw})
            p, f = run(make, lives), run(make, lives, all_food=True)
            kinds, when = growth(p)
            d, lo, hi = paired(base, p)
            exact = kinds.get("1 on poison's sensor, 0 on food's", 0)
            print(f"{name:20s} exactly O1 in {exact} of {lives}; first bridge median {when}; net vs knowing {d:+.2f}"
                  f" [{lo:+.2f}, {hi:+.2f}]; bridges in all-food lives {sum(len(r['bridges']) for r in f)}", flush=True)
            out[("b", name)] = (p, f)
    if "c" in parts:
        print()
        for name, make in (("R3", R3), ("designed circuit", DesignedBrain)):
            clean = run(make, lives)
            for size in (0.05, 0.10):
                off = run(make, lives, setup=functools.partial(mismatch, size))
                d, lo, hi = paired(clean, off)
                still = sum(1 for r in off if sum(t for _, _, t in r["thirds"]) == 0)
                print(f"{name:24s} mismatch {int(size * 100)}%: net food change {d:+.2f} [{lo:+.2f}, {hi:+.2f}];"
                      f" lives that never moved {still};{summary('', off)}", flush=True)
                out[("c", name, size)] = (clean, off)
    if "e" in parts:                                   # which mismatch hurts? one class of parameter at a time
        print()
        clean = run(R3, lives)
        for which in ("intrinsic", "other", "bias", "all"):
            off = run(R3, lives, setup=functools.partial(mismatch, 0.05, which=which))
            d, lo, hi = paired(clean, off)
            print(f"R3, 5% mismatch in {which:9s}: net food change {d:+.2f} [{lo:+.2f}, {hi:+.2f}];{summary('', off)}",
                  flush=True)
    if "d" in parts:
        print()
        for name, make in (("baseline", "baseline-circuit"), ("knowing", "knowing-circuit"),
                           ("R3 at the end of a poison life", R3),
                           ("designed circuit", "designed-circuit")):
            n, m, e = cost(make)
            print(f"{name:32s} nodes {n:3d}, elements {m:3d}, sum of gains {e:8.1f}")
    pickle.dump(out, open("experiments/results/e5.pkl", "wb"))
