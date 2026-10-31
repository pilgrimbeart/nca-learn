"""Self-tuning without a coordinator (discrete/NOTEBOOK.md, D15): circuit B's blocks (model.py) whose spending knobs
tune themselves towards better outcomes in the life, by continuous-time node perturbation (Fiete and Seung, 2006).

    python -m discrete.tuner [SEEDS] [seconds=10000] [body=0] [tune=1] [k=v ...]

- each knob (hold, boredom, scan, drive and run rates, in the log; with body=1 also the drive's balance) wiggles at
  its own random moments (on average every `wig` s) to a new random offset within +-delta;
- one outcome node: a leaky tally of what taste brings (food 1, poison -2, a food sighting beta) over a leaky tally of
  what is spent (resting and the brain's own firings), both with time constant tau_r: an efficiency rate;
- its own slower average (tau_b); the difference, "better than usual", is broadcast;
- each knob keeps a trace of its own offset (tau_r) and moves by eta x broadcast x trace, every 0.1 s;
- meta=1: each knob its own rate (delta-bar-delta, Jacobs 1988; IDBD, Sutton 1992; the user's layers, 2026-10-30):
  it keeps a leaky memory of its own steps (tau_m) and their size; its log-rate rises while a step agrees with that
  memory as it was `lag` s ago and falls while it disagrees (by theta, each step against the steps' typical size),
  within x10 of eta. The memory is delayed beyond the steps' own correlation (the trace's and the outcome's, some
  20 s): compared with its fresh memory every rate climbed, steps agreeing with themselves even in noise.

No epochs, no shared clock, no accountant: every quantity a node, each knob knowing only itself and the broadcast. A
block model, not yet a circuit. Lives: each knob drawn up to `mistune` times off B's at birth (log-uniform, from the
seed); body=1, each thruster 0.5 to 2 (bodies.THRUSTERS), the balance starting level; tune=0, the knobs fixed where
born (the floor); hold_only=1, only the hold tuned; fbal, the balance's rate
scaled (a hand-picked rate, to measure what learning rates could gain)."""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from discrete import model as M  # noqa: E402
from minimal.spec import NEED, SPAN, THRUST  # noqa: E402
from units import TICK  # noqa: E402

REST = NEED / SPAN                                      # meals a second resting costs
KNOBS = ("hold", "bored", "scan", "drive", "run")
BOUNDS = dict(hold=(0.03, 1.5), bored=(1.0, 30.0), scan=(3.0, 50.0), drive=(10.0, 100.0), run=(10.0, 100.0),
              bal=(np.exp(-1.4), np.exp(1.4)))         # (the balance: motor 0's rate against motor 1's)
TUNING = dict(eta=0.01, delta=0.3, wig=20.0, tau_r=20.0, tau_b=200.0, beta=0.02,   # D15's best
              tau_m=200.0, theta=0.002, lag=100.0)


def mistuned(p, seed, factor):
    """Each spending knob off by up to factor either way (log-uniform), drawn from the seed."""
    rng = np.random.default_rng(seed + 31_337)
    return {**p, **{k: float(np.clip(p[k] * np.exp(rng.uniform(-np.log(factor), np.log(factor))), *BOUNDS[k]))
                    for k in KNOBS}}


class Tuned(M.Model):
    """B with each knob tuning itself. p: B's numbers, TUNING's, and tune (0: fixed), knobs (which tune)."""

    def __init__(self, seed, p):
        super().__init__(seed, {**TUNING, **p})
        self.rng = np.random.default_rng(seed + 525_252)
        self.knobs = self.p.get("knobs", KNOBS)
        self.lo = {k: np.log(BOUNDS[k][0]) for k in self.knobs}
        self.hi = {k: np.log(BOUNDS[k][1]) for k in self.knobs}
        self.x = {k: 0.0 if k == "bal" else float(np.log(self.p[k])) for k in self.knobs}   # each knob (log)
        self.off = dict.fromkeys(self.knobs, 0.0)       # its wiggle now
        self.tr = dict.fromkeys(self.knobs, 0.0)        # its trace of its wiggle
        self.when = {k: self.rng.exponential(self.p["wig"]) for k in self.knobs}   # its next moment
        self.G, self.E = 0.0, REST * self.p["tau_r"]    # the outcome node: leaky gain over leaky spending
        self.base = None                                # its slower average
        self.got, self.slow = 0.0, 0
        self.rate = dict.fromkeys(self.knobs, float(np.log(max(self.p["eta"], 1e-12))))   # each knob's own log-rate (meta)
        self.mem = dict.fromkeys(self.knobs, 0.0)       # its leaky memory of its own steps
        self.size = dict.fromkeys(self.knobs, 1e-12)    # and of their squares
        from collections import deque
        self.past = {k: deque([0.0] * int(self.p["lag"] / (10 * TICK)), maxlen=int(self.p["lag"] / (10 * TICK)))
                     for k in self.knobs}               # its memory, delayed
        self.trace, self.next_log = [], 0.0             # watching: (t, knobs) each 100 s

    def _set(self):
        for k in self.knobs:
            v = float(np.clip(self.x[k] + self.off[k], self.lo[k], self.hi[k]))
            if k == "bal":
                self.p["g0"], self.p["g1"] = float(np.exp(v / 2)), float(np.exp(-v / 2))
            else:
                self.p[k] = float(np.exp(v))

    def taste(self, value, at):
        super().taste(value, at)
        self.got += 1.0 if value > 0 else -2.0

    def step(self):
        p = self.p
        self.got += p["beta"] * self.seen[self.food]
        out = super().step()
        if not p.get("tune", 1):
            return out
        a = TICK / p["tau_r"]
        self.G += self.got - a * self.G
        self.E += REST * TICK + THRUST * len(out) - a * self.E
        self.got = 0.0
        R = self.G / self.E
        self.base = R if self.base is None else self.base + TICK / p["tau_b"] * (R - self.base)
        better = R - self.base                          # the broadcast
        self.slow += 1
        if self.slow < 10:                              # knobs, traces and wiggles move every 0.1 s
            return out
        self.slow, dt = 0, 10 * TICK
        for k in self.knobs:
            self.tr[k] += dt / p["tau_r"] * (self.off[k] - self.tr[k])
            g = better * self.tr[k]                     # its own estimate of the slope
            if p.get("meta"):
                m = dt / p["tau_m"]
                self.rate[k] = float(np.clip(self.rate[k] + p["theta"] * g * self.past[k][0] / self.size[k],
                                             np.log(p["eta"] / 10), np.log(p["eta"] * 10)))
                self.mem[k] += m * (g - self.mem[k])
                self.size[k] += m * (g * g - self.size[k])
                self.past[k].append(self.mem[k])
            eta = (float(np.exp(self.rate[k])) if p.get("meta")
                   else p["eta"] * (p.get("fbal", 1.0) if k == "bal" else 1.0))
            self.x[k] = float(np.clip(self.x[k] + eta * dt * g, self.lo[k], self.hi[k]))
            if self.t >= self.when[k]:
                self.off[k] = p["delta"] * self.rng.uniform(-1.0, 1.0)
                self.when[k] = self.t + self.rng.exponential(p["wig"])
        self._set()
        if self.t >= self.next_log:
            self.next_log += 100.0
            self.trace.append((self.t, dict(self.x), dict(self.rate)))
        return out


def life(job):
    """(p, spread, seed, seconds, poison) -> the life's Lived, with its knobs' trace. p may also hold mistune (default
    3), body, tune, hold_only."""
    from creature import Life
    from minimal.spec import Lived, thirds
    p, spread, seed, seconds, poison = job
    q = mistuned(M.drawn(p, spread, seed), seed, p.get("mistune", 3.0))
    q = {k: v for k, v in q.items() if k not in ("body", "mistune", "hold_only")}
    q["knobs"] = ("hold",) if p.get("hold_only") else KNOBS + (("bal",) if p.get("body") else ())
    lf = Life(seed, poison, brain=lambda s: Tuned(s, q))
    if p.get("body"):
        from discrete.bodies import THRUSTERS, draw, vary
        vary(lf, draw(seed, THRUSTERS))
    ticks = int(round(seconds / TICK))
    while lf.t < ticks:
        lf.step()
    l = Lived(thirds(lf.meals, lf.moving, ticks, poison))
    l.power, l.firings, l.substrate = 3.7e-9, SPAN * len(lf.firings) / seconds, "silicon"
    l.trace = lf.brain.trace
    return l


def lives(p, spread, seeds, seconds, workers=None):
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(workers) as ex:
        return list(ex.map(life, [(p, spread, s, seconds, c) for s in seeds for c in ("red", "blue")]))


if __name__ == "__main__":
    import pickle
    from discrete.poison import show
    from minimal.spec import summary
    args = [a for a in sys.argv[1:] if "=" not in a]
    lo, hi = (int(x) for x in (args[0] if args else "50000:50032").split(":"))
    kw = {k: float(v) for k, v in (a.split("=") for a in sys.argv[1:] if "=" in a)}
    seconds = kw.pop("seconds", 10000.0)
    p, spread = M.from_bench()
    L = lives(dict(p, **kw), spread, range(lo, hi), seconds)
    print(show(f"tuner {kw}", summary(L)))
    out = os.path.join(os.environ.get("LIVES", os.path.join(os.path.dirname(__file__), "results")),   # (LIVES: elsewhere)
                       "tuner" + "".join(f"_{k}{v:g}" for k, v in sorted(kw.items())) + ".lives")
    pickle.dump(L, open(out, "wb"))
