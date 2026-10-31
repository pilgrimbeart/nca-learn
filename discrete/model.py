"""The fast model (discrete/NOTEBOOK.md, D13): circuit B as its blocks' measured behaviour, a life in about a second
against minutes in SPICE. The lab for design questions; SPICE checks a design is close to physically realisable
(AGENTS.md: the fast model is the lab).

    python -m discrete.model [SEEDS] [k=v ...]   # B from its bench, judged robustly on SEEDS (default 50000:50032)

Each number comes from SPICE's bench (discrete/blocks.py; results/cmos_b_bench.json): the median over 32 seeds, and
each life draws its own from their spread (judged robustly, AGENTS.md); vary=0 for the nominal model, for debugging
only. Never transistors: each block is the few numbers that say what it does.

The blocks: the eye the bit says is food (F) restarts the drive's hold and boredom; the other (P) ends the drive. While
the hold lasts, both thrusters fire at the drive's beat rate; after boredom, at the run's; otherwise one thruster at
the scan's. Doubt (dq, in volts between the rails) steps up for a poison and down for a food and drifts down; at the
threshold V_H the bit flips and doubt resets to V_L."""

from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from units import TICK  # noqa: E402

RAIL = 1.8                                              # V: doubt's bounds are the rails, 0 and this
BENCH = os.path.join(os.path.dirname(__file__), "results", "cmos_b_bench.json")
TIMERS = ("hold", "bored", "scan", "drive", "run", "step", "fstep", "drift")   # drawn log-normally
LEVELS = ("V_H", "V_L")                                                        # drawn normally (V)


def from_bench(path=BENCH, skip=()):
    """(numbers, spread): each block's median over the benched seeds, and its spread (the sd of its log for TIMERS, its
    sd in V for LEVELS)."""
    rows = [r for r in json.load(open(path))["seeds"] if r["seed"] not in skip]
    p = {k: float(np.median([r[k] for r in rows])) for k in TIMERS + LEVELS}
    sd = {k: float(np.std(np.log([r[k] for r in rows]))) for k in TIMERS}
    sd |= {k: float(np.std([r[k] for r in rows])) for k in LEVELS}
    return p, sd


def drawn(p, spread, seed):
    """A life's own blocks: each number its design's, varied as the seed's tolerances vary it."""
    rng = np.random.default_rng(seed + 7_300_001)
    q = dict(p)
    for k in TIMERS:
        q[k] = p[k] * float(np.exp(rng.normal(0.0, spread[k])))
    for k in LEVELS:
        q[k] = p[k] + float(rng.normal(0.0, spread[k]))
    return q


class Model:
    """Circuit B's blocks, one life. p: the numbers (TIMERS, LEVELS), and
    start: doubt at birth (V; default the life's V_L, as the circuit is born at trust);
    lone: the fraction of the scan's beat in which a drive's start fires motor B alone, as the circuit does (D13);
    g0, g1: each motor's rates scaled (a body's balance, told: the oracle)."""

    def __init__(self, seed, p):
        self.p = {"lone": 0.0, "g0": 1.0, "g1": 1.0, **p}
        rng = np.random.default_rng(seed + 91)
        self.food = int(rng.integers(2))                # which eye the bit says is food
        self.phase, self.phase1 = rng.random(), rng.random()
        self.seen = [0, 0]
        self.t = 0.0
        self.last_drive = self.last_food = -1e9
        self.dq = self.p.get("start", self.p["V_L"])
        self.was_on = False                             # driving or running, last tick
        self.flips = []                                 # watching: when the bit flipped

    def stimulate(self, sensor, at):
        self.seen[sensor] += 1

    def taste(self, value, at):
        p = self.p
        if value < 0:
            self.dq = min(RAIL, self.dq + p["step"])
            if self.dq >= p["V_H"]:
                self.food = 1 - self.food
                self.flips.append(self.t)
                self.dq = p["V_L"]
        elif value > 0:
            self.dq = max(0.0, self.dq - p["fstep"])

    def drive(self, sensor):
        return 1.0

    def step(self):
        p = self.p
        F, P = self.seen[self.food], self.seen[1 - self.food]
        self.seen = [0, 0]
        self.t += TICK
        if F:
            self.last_drive = self.last_food = self.t
        if P:
            self.last_drive = -1e9
        driving = self.t - self.last_drive < p["hold"]
        running = not driving and self.t - self.last_food > p["bored"]
        self.dq = max(0.0, self.dq - p["drift"] * TICK)
        lone = [1] if p["lone"] and driving and not self.was_on and self.phase < p["lone"] else []
        if p.get("sync") and (driving or running) and not self.was_on:
            self.phase1 = self.phase                    # sync=1: each drive's two oscillators start in step
        self.was_on = driving or running
        r = p["drive"] if driving else p["run"] if running else p["scan"]
        if p.get("paired") and p["g1"] != p["g0"] and (driving or running):
            hi = max(p["g0"], p["g1"])                  # paired=1: a balance keeps the beats paired, the slower
            self.phase += r * hi * TICK                 # motor firing beside some of the faster one's beats, not
            beats = int(self.phase)                     # on an oscillator of its own (D20: unpaired beats wobble)
            self.phase -= beats
            out = list(lone)
            for _ in range(beats):
                self.phase1 += min(p["g0"], p["g1"]) / hi
                if self.phase1 >= 1:
                    self.phase1 -= 1
                    out += [0, 1]
                else:
                    out.append(0 if p["g0"] > p["g1"] else 1)
            return out
        self.phase += r * p["g0"] * TICK
        beats = int(self.phase)
        self.phase -= beats
        if not (driving or running):
            return [0] * beats
        if p["g1"] == p["g0"]:
            return lone + [0, 1] * beats
        self.phase1 += r * p["g1"] * TICK
        b1 = int(self.phase1)
        self.phase1 -= b1
        return lone + [0] * beats + [1] * b1


def life(job):
    """(p, spread, seed, seconds, poison) -> the life's Lived. p may also hold vary (0: the nominal model), body (1: the
    thrusters drawn, bodies.THRUSTERS) and oracle (with body: 1, the drive balanced for it; 2, every firing restored)."""
    from creature import Life
    from minimal.spec import SPAN, Lived, thirds
    p, spread, seed, seconds, poison = job
    q = drawn(p, spread, seed) if p.get("vary", 1) else dict(p)
    q = {k: v for k, v in q.items() if k not in ("vary", "body", "oracle")}
    lf = Life(seed, poison, brain=lambda s: Model(s, q))
    if p.get("body"):
        from discrete.bodies import THRUSTERS, draw, vary
        f = draw(seed, THRUSTERS)
        vary(lf, f)
        if p.get("oracle"):
            thr = {m: t for t, m in lf.motor.items()}   # motor -> thruster
            k0, k1 = f[thr[0]], f[thr[1]]
            g = (1 / k0, 1 / k1) if p["oracle"] == 2 else ((k1 / k0) ** 0.5, (k0 / k1) ** 0.5)
            lf.brain.p["g0"], lf.brain.p["g1"] = g
    ticks = int(round(seconds / TICK))
    while lf.t < ticks:
        lf.step()
    l = Lived(thirds(lf.meals, lf.moving, ticks, poison))
    l.power, l.firings, l.substrate = 3.7e-9, SPAN * len(lf.firings) / seconds, "silicon"
    return l


def lives(p, spread, seeds, seconds=100.0, workers=None):
    """Paired lives (red, then blue as poison, on each seed)."""
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(workers) as ex:
        return list(ex.map(life, [(p, spread, s, seconds, c) for s in seeds for c in ("red", "blue")]))


if __name__ == "__main__":
    from discrete.poison import show
    from minimal.spec import summary
    args = [a for a in sys.argv[1:] if "=" not in a]
    lo, hi = (int(x) for x in (args[0] if args else "50000:50032").split(":"))
    p, spread = from_bench()
    p |= {k: float(v) for k, v in (a.split("=") for a in sys.argv[1:] if "=" in a)}
    print(show(f"model of circuit B {p}", summary(lives(p, spread, range(lo, hi)))))
