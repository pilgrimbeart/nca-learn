"""A circuit brain written as a plain description (a spec), its parts counted, and lives of it scored (the minimal
circuit search: minimal/NOTEBOOK.md).

A spec is a dict:
  nodes: [name, bias, R (None: no leak), C, lo, hi, start (None: where it rests), memory], ...
  elements: [to, from, gate (-1: none), gain, offset, slope, tau, sigmoid], ...: node indices, as mixed_feedback
  sensors: the two nodes the body stimulates; motors: the two whose spikes fire the thrusters (any nodes, the same
  node allowed); taste: the node taste is injected into.

Parts, counted as an analogue circuit would be built (mixed_feedback's docstring): a node is a capacitor, plus a
resistor to a rail if it leaks (its bias sets which rail: no extra part), plus a diode per clamp inside the supply's
rails (every node is within them, RAIL); an element is a
transistor (a transconductor), plus one in series if gated, plus a resistor and capacitor if its input is filtered.
"""

from __future__ import annotations

import functools
import math
import multiprocessing
import os
import sys
from collections import deque
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brains.circuit import CircuitBrain, TRACE  # noqa: E402
from mixed_feedback import RAIL, Circuit  # noqa: E402

# RAIL: the supply's rails, +-RAIL (V): no node can go beyond them (the user's question, 2026-10-20: the body's pulses
# are a current source, and nothing stopped a pulse lifting a node 10 V); a clamp inside them is a part (two diodes),
# the rails themselves are the supply's. Noise and mismatch are mixed_feedback's, which no spec can change.


class SpecBrain(CircuitBrain):
    """A circuit brain built from a spec. STREAMS False: one noise stream (fastlife needs it). noise: a share of the
    usual, within mixed_feedback.NOISY. level0: watched in the node view (blocks.NodeView), having no neurons."""

    level0 = True

    def __init__(self, seed: int, spec: dict, noise: float = 1.0):
        check(spec)
        self.seed, self.spec = seed, spec
        c = self.circuit = Circuit(seed=seed + 1_000_003, noise=noise)
        for name, bias, R, C, lo, hi, start, memory in spec["nodes"]:     # every node within the supply's rails
            c.node(name, bias, R, C, -RAIL if lo is None else max(lo, -RAIL), RAIL if hi is None else min(hi, RAIL),
                   start, memory)
        for to, frm, gate, gain, offset, slope, tau, sigmoid in spec["elements"]:
            c.element(to, frm, gain, offset, tau, slope, bool(sigmoid), gate)
        if not spec["elements"]:                        # (the simulator needs one; it does nothing, and isn't a part)
            c.element(0, 0, 0.0, 0.0)
        self.sensors, self.motors, self.taste_node = list(spec["sensors"]), list(spec["motors"]), spec["taste"]
        self.last_inject = np.zeros(len(c.names))
        self.history = deque(maxlen=TRACE)
        self.log = None

    def build(self, c):
        pass

    def shown(self) -> list:
        """Watching: every node but the sensors and motors (the taste node, the bit ...)."""
        return [(n[0], i) for i, n in enumerate(self.spec["nodes"]) if i not in (*self.sensors, *self.motors)]

    def drive(self, sensor: int) -> float:
        return 1.0


def interface(spec: dict) -> set:
    """The nodes the body uses."""
    return set(spec["sensors"]) | set(spec["motors"]) | {spec["taste"]}


def remove_node(spec: dict, i: int) -> None:
    """Drop node i (not one the body uses) and every element touching it; renumber."""
    spec["elements"] = [e for e in spec["elements"] if i not in (e[0], e[1]) and e[2] != i]
    del spec["nodes"][i]
    re = lambda j: j - (j > i)
    for e in spec["elements"]:
        e[0], e[1] = re(e[0]), re(e[1])
        if e[2] >= 0:
            e[2] = re(e[2])
    spec["sensors"] = [re(j) for j in spec["sensors"]]
    spec["motors"] = [re(j) for j in spec["motors"]]
    spec["taste"] = re(spec["taste"])


def tidy(spec: dict) -> dict:
    """Drop nodes nothing reads and the body doesn't use (they can't matter), and the elements into them (in place)."""
    while True:
        read = {e[1] for e in spec["elements"]} | {e[2] for e in spec["elements"] if e[2] >= 0}
        dead = [i for i in range(len(spec["nodes"])) if i not in interface(spec) and i not in read]
        if not dead:
            return spec
        remove_node(spec, dead[-1])


def make(spec: dict, noise: float = 1.0):
    return functools.partial(SpecBrain, spec=spec, noise=noise)


def parts(spec: dict) -> dict:
    """The parts an analogue build would need: capacitors, resistors, diodes, transistors, and their total."""
    C = R = D = T = 0
    for _, _, r, _, lo, hi, _, _ in spec["nodes"]:
        C += 1
        R += r is not None
        D += (lo is not None and math.isfinite(lo)) + (hi is not None and math.isfinite(hi))
    for _, _, gate, _, _, _, tau, _ in spec["elements"]:
        T += 1 + (gate >= 0)
        if tau > 0:
            R, C = R + 1, C + 1
    return {"C": C, "R": R, "D": D, "T": T, "total": C + R + D + T,
            "nodes": len(spec["nodes"]), "elements": len(spec["elements"])}


SLEW = 10.0         # the most any element, leak or input pulse may move a node per circuit tick (0.5 V per step of
                    # 0.05): the honesty limit on gains and time constants against the step (AGENTS.md)


LOOP = 2.0          # the fastest an unfiltered element on its own node may act, gain x (its f's steepest slope) / C, per
                    # circuit tick: a time constant of at least 10 integration steps (the user's question, 2026-10-20:
                    # a device fed back to itself "implies infinite speed"; the designed circuit's neurons sit at 2)


def slew(spec: dict) -> float:
    """How fast the circuit is against its limits, as a slew (the limit is SLEW): the fastest a node can be moved per
    circuit tick, by an element (|gain| / C), its leak (1 / RC), or the body's pulse into a sensor or the taste node
    (3 / C); and the fastest unfiltered self-feedback, scaled so that LOOP maps to SLEW."""
    from brains.circuit import STIMULUS, TASTE
    C = [n[3] for n in spec["nodes"]]
    out = [abs(e[3]) / C[e[0]] for e in spec["elements"]]
    out += [1.0 / (n[2] * n[3]) for n in spec["nodes"] if n[2] is not None]
    out += [STIMULUS / C[i] for i in spec["sensors"]] + [TASTE / C[spec["taste"]]]
    out += [abs(e[3]) * (e[5] / 4 if e[7] else e[5]) / C[e[0]] * SLEW / LOOP
            for e in spec["elements"] if e[0] == e[1] and e[6] == 0]
    return max(out)


def violations(spec: dict) -> list:
    """What breaks the rules (AGENTS.md, The minimal circuit search): wiring that names no node, the interface
    misused, and the honesty limits against the integration step (SLEW, LOOP). Empty: a legal circuit."""
    n, out = len(spec["nodes"]), []
    for e in spec["elements"]:
        if not (0 <= e[0] < n and 0 <= e[1] < n and -1 <= e[2] < n):
            out.append(f"element {e[:3]} names no node")
    if len(set(spec["sensors"])) != 2 or spec["taste"] in spec["sensors"] or \
            not all(0 <= i < n for i in [*spec["sensors"], *spec["motors"], spec["taste"]]):
        out.append("interface: two distinct sensors, a taste node apart from them, motors on nodes")
    for nd in spec["nodes"]:
        if nd[3] <= 0 or (nd[2] is not None and nd[2] <= 0):
            out.append(f"node {nd[0]}: capacitance and leak must be positive")
    if not out and slew(spec) > SLEW * (1 + 1e-9):
        out.append(f"too fast for the step: {slew(spec):.1f} against the limit {SLEW:g} (SLEW, LOOP)")
    return out


def check(spec: dict) -> None:
    """Refuse a circuit that breaks the rules: no illegal circuit can be built (SpecBrain calls this)."""
    bad = violations(spec)
    if bad:
        raise ValueError("illegal circuit: " + "; ".join(bad))


class Lived(list):
    """A life's thirds (a list), with its circuit's mean power, its thrusters' firings per 1,000 ticks, and how far
    the circuit is over the slew limit."""
    power = 0.0
    firings = 0.0
    over = 0.0


def one(job):
    """(spec, seed, poison, ticks, learning, noise) -> (food, poison, ticks) after moving, by third of life, then
    (0, 0, ticks before moving), so that rates over all four are per tick of life. Mismatch comes with every circuit
    (mixed_feedback.MISMATCH), drawn from the seed."""
    from minimal.fastlife import life
    spec, seed, poison, ticks, learning, noise = job
    meals, moving, power, firings = life(make(spec, noise), seed, poison, ticks, learning)
    start = moving if moving is not None else ticks
    out = []
    for i in range(3):
        a, z = start + i * (ticks - start) / 3, start + (i + 1) * (ticks - start) / 3
        part = [c for t, c in meals if a <= t < z]
        out.append((sum(c != poison for c in part), sum(c == poison for c in part), z - a))
    lived = Lived(out + [(0, 0, start)])
    lived.power, lived.firings, lived.over = power, 1000 * firings / ticks, max(0.0, slew(spec) / SLEW - 1.0)
    return lived


_POOL = None


def pool():
    global _POOL
    if _POOL is None:
        _POOL = ProcessPoolExecutor(mp_context=multiprocessing.get_context("spawn"))
    return _POOL


def score(specs, seeds=range(8), ticks=10000, learning=True, all_food=False, noise=1.0):
    """Each spec over the given seeds, each seed lived twice, red then blue as poison (a circuit that ignores taste
    lives the same life twice with the labels swapped, so it nets exactly 0), or once in all food. noise: a share of
    the usual (mixed_feedback.NOISY). Per spec: a list of lives, each its thirds [(food, poison, ticks)]."""
    poisons = (None,) if all_food else ("red", "blue")
    legal = [not violations(s) for s in specs]
    jobs = [(s, seed, p, ticks, learning, noise) for s, ok in zip(specs, legal) if ok
            for seed in seeds for p in poisons]
    res = iter(pool().map(one, jobs, chunksize=max(1, len(jobs) // 64)))
    k = len(seeds) * len(poisons)
    out = []
    for s, ok in zip(specs, legal):
        if ok:
            out.append([next(res) for _ in range(k)])
        else:                                           # not lived: a starving life, and a penalty graded by how far
            dead = Lived([(0, 0, ticks / 3)] * 3 + [(0, 0, 0)])     # over the limits (so a search can find its way
            try:                                                    # back), or a fixed one if it can't be measured
                dead.over = max(0.0, slew(s) / SLEW - 1.0) + 0.1
            except (IndexError, ZeroDivisionError):
                dead.over = 10.0
            out.append([dead] * k)
    return out


COST = 2.0          # a poison meal counts as this many food meals lost: eating without telling them apart loses
ENERGY = 0.01       # the score's cost per unit of mean power (mixed_feedback._step: what each device dissipates, its
                    # current times the voltage across it), so that stages don't fight (the user's question, 2026-10-20:
                    # C2's clock drew 7 units of current, its reads 0.25)
NEED = 1.0          # food per 1,000 ticks a creature needs, in every third of every life: each meal short of it
                    # costs COST (starving) ...
THRUST = 0.0        # the score's cost per thruster firing per 1,000 ticks: the body's energy, 0 (not counted) unless
                    # an experiment sets it (search.py --thrust; the user's question, 2026-10-20: should moving cost?)
JOB = (1.0, 3.0, 0.05)  # ... and the job: at least this much food per 1,000 ticks, this food:poison in the last third,
                    # and at most this share of lives stranded (no food at all in the last third; a creature eating
                    # 1.4 per 1,000 goes a last third without food by chance about 1% of the time)


def net(lives, cost: float = COST, need: float = NEED, energy: float = ENERGY) -> float:
    """The score: food - cost x poison, per 1,000 ticks of life (counted from birth), less cost x how far each third
    of each life falls short of need (a third with no ticks, as when a creature never moves, wholly short), less
    energy x its mean power, and a heavy penalty for a circuit over the slew limit. Starving is counted life by life
    and third by third, so a life that strands (eats, then finds nothing more) costs in its own last third instead of
    hiding among other lives' meals (the user's question, 2026-10-20: a creature that spun on the spot forever once
    it had eaten what was near; a fifth of the winners' lives did). With cost above 1 a circuit that ignores taste
    scores below 0 (in paired lives, -(cost - 1) x what it eats, less any starving), and one that stays still scores
    -cost x need; only learning scores above 0."""
    f = sum(a for l in lives for a, _, _ in l)
    p = sum(b for l in lives for _, b, _ in l)
    ticks = sum(t for l in lives for _, _, t in l)
    fr, pr = 1000 * f / ticks, 1000 * p / ticks
    short = float(np.mean([max(0.0, need - 1000 * a / t) if t > 0 else need for l in lives for a, _, t in l[:3]]))
    power = float(np.mean([getattr(l, "power", 0.0) for l in lives]))
    over = max(getattr(l, "over", 0.0) for l in lives)
    thrust = THRUST * float(np.mean([getattr(l, "firings", 0.0) for l in lives]))
    return fr - cost * pr - cost * short - energy * power - thrust - 10.0 * over


def summary(lives) -> dict:
    """The score (net, above; with a bootstrap 95% interval over seeds, each seed's pair kept together), plain net
    (food - poison), food and poison per 1,000 ticks of life, food:poison over the last third, the share of lives
    stranded (no food in the last third), and whether it does the job (JOB)."""
    pairs = [lives[i:i + 2] for i in range(0, len(lives), 2)]
    rng = np.random.default_rng(0)
    idx = rng.integers(len(pairs), size=(2000, len(pairs)))
    boot = [net([l for i in row for l in pairs[i]]) for row in idx]
    f = sum(a for l in lives for a, _, _ in l)
    p = sum(b for l in lives for _, b, _ in l)
    t = sum(t for l in lives for _, _, t in l)
    lf = sum(l[2][0] for l in lives)
    lp = sum(l[2][1] for l in lives)
    stranded = sum(l[2][0] == 0 for l in lives) / len(lives)
    return {"net": net(lives), "plain": net(lives, 1.0, 0.0, 0.0), "power": float(np.mean([l.power for l in lives])),
            "over": max(l.over for l in lives), "lo": float(np.nanpercentile(boot, 2.5)), "hi": float(np.nanpercentile(boot, 97.5)),
            "food": 1000 * f / t if t else 0.0, "poison": 1000 * p / t if t else 0.0,
            "last": lf / lp if lp else math.inf, "stranded": stranded,
            "firings": float(np.mean([l.firings for l in lives])),
            "job": bool(1000 * f / t >= JOB[0] and (lf / lp if lp else math.inf) >= JOB[1] and stranded <= JOB[2])
            if t else False}
