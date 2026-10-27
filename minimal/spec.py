"""A circuit brain written as a plain description (a spec), its parts counted, and lives of it scored (the minimal
circuit search: minimal/NOTEBOOK.md).

A spec is a dict, in SI units (units.py; "units": "SI", which check requires, so that no design from before
2026-10-22, in ticks, can be lived by mistake):
  nodes: [name, bias (A), R (ohm; None: no leak), C (F), lo, hi, start (V; None: where it rests), memory], ...
  elements: [to, from, gate (-1: none), gain (A), offset (V), slope (per V), tau (s), sigmoid], ...: node indices, as
  mixed_feedback
  sensors: the two nodes the body stimulates; motors: the two whose spikes fire the thrusters (any nodes, the same
  node allowed); taste: the node taste is injected into.

A spec is drawn at a typical voltage ("volt", units.V_TYP; check requires the current one, and load converts an
older design, minimal/designs.py's rescale: those before 2026-10-26 were drawn at 1 V).

Parts, counted as the circuit is built in transistors (the user's decision, 2026-10-26: the minimal analogue circuit is
counted in real devices, so that designs at other levels, op-amps or Sepulchre's blocks, can be compared with it):
chip.py's blocks, as minimal/spice.py writes them, counted there (count): transistors, resistors, capacitors, diodes,
and bias sources (each a bias generator's output).
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
from mixed_feedback import SUBSTRATES, Circuit  # noqa: E402
from units import (C_MAX, C_TYP, CAP_DENSITY, I_MIN, MICRO, NANO, R_MAX, RAIL, SLEW, TAU_LEAK, TAU_LOOP,  # noqa: E402
                   TAU_MAX, T_TYP, TICK, UNIT_AREA, V_TYP, si)

# RAIL: the supply's rails, +-RAIL (V): no node can go beyond them (the user's question, 2026-10-20: the body's pulses
# are a current source, and nothing stopped a pulse lifting a node 10 V); a clamp inside them is a part (two diodes),
# the rails themselves are the supply's. Noise and mismatch are mixed_feedback's, which no spec can change.


class SpecBrain(CircuitBrain):
    """A circuit brain built from a spec. STREAMS False: one noise stream (fastlife needs it). substrate: whose noise
    (mixed_feedback.SUBSTRATES). level0: watched in the node view (blocks.NodeView), having no neurons."""

    level0 = True

    def __init__(self, seed: int, spec: dict, substrate: str = "biology"):
        check(spec)
        self.seed, self.spec = seed, spec
        c = self.circuit = Circuit(seed=seed + 1_000_003, substrate=substrate)
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


def make(spec: dict, substrate: str = "biology"):
    return functools.partial(SpecBrain, spec=spec, substrate=substrate)


def load(path: str) -> dict:
    """The spec stored in a results file, at the current typical voltage (converted if drawn at another)."""
    import json
    from minimal.designs import rescale
    spec = json.load(open(path))["spec"]
    return spec if math.isclose(spec.get("volt", 1.0), V_TYP) else rescale(spec)


def parts(spec: dict) -> dict:
    """The parts the circuit takes in transistors (minimal/spice.py's count): transistors, resistors, capacitors,
    diodes, bias sources, and their total; a clamp inside the rails is two diodes more (only where the body's pulses
    enter does the build have clamps; elsewhere the amplifiers can't pass the rails)."""
    from minimal.spice import count
    n = count(spec)
    pulsed = set(spec["sensors"]) | {spec["taste"]}
    n["D"] += sum((lo is not None and math.isfinite(lo)) + (hi is not None and math.isfinite(hi))
                  for i, (_, _, _, _, lo, hi, _, _) in enumerate(spec["nodes"]) if i not in pulsed)
    return {**n, "total": n["T"] + n["R"] + n["C"] + n["D"] + n["sources"], "nodes": len(spec["nodes"]),
            "elements": len(spec["elements"])}


AREA = {"element": 5, "gate": 3, "leak": 2, "clamp": 1, "memory": 5}
                    # chip area, in unit transistors (units.UNIT_AREA, an analogue-sized MOSFET with its spacing), by
                    # analogy with subthreshold analogue CMOS (the user's question, 2026-10-21: what does a gate cost?):
                    # an element is a transconductance amplifier (differential pair, current mirror, bias), a gate a
                    # two-quadrant multiplier stacked on it, a leak a pseudo-resistor, a memory node's floating gate its
                    # tunnelling and injection structures; a capacitor takes its own area (capacitor_area), and a
                    # filter is an amplifier and a capacitor of units.C_TYP. Reported, not ranked on.


def capacitor_area(C: float) -> float:
    """A capacitor's area in unit transistors: a MOS capacitor (units.CAP_DENSITY)."""
    return C / CAP_DENSITY / UNIT_AREA


def area(spec: dict) -> float:
    """The chip area an analogue build would take (AREA), in unit transistors."""
    a = 0.0
    for _, _, r, c, lo, hi, _, mem in spec["nodes"]:
        a += capacitor_area(c) + AREA["leak"] * (r is not None) + AREA["memory"] * bool(mem)
        a += AREA["clamp"] * ((lo is not None and math.isfinite(lo)) + (hi is not None and math.isfinite(hi)))
    for _, _, gate, _, _, _, tau, _ in spec["elements"]:
        a += AREA["element"] + AREA["gate"] * (gate >= 0) + (AREA["element"] + capacitor_area(C_TYP)) * (tau > 0)
    return a


def slew(spec: dict) -> float:
    """How fast the circuit is against the honesty limits (units.py: SLEW, TAU_LEAK, TAU_LOOP, all from the
    integration step), as a share of them (above 1 is illegal): the fastest a node can be moved, by an element
    (|gain| / C) or the body's pulse into a sensor or the taste node, against SLEW; the fastest leak (1 / RC) against
    1 / TAU_LEAK; and the fastest unfiltered element on its own node (gain x its f's steepest slope / C: a device fed
    back to itself must not be infinitely fast, the user's question, 2026-10-20) against 1 / TAU_LOOP."""
    from brains.circuit import PULSES
    STIMULUS = TASTE = PULSES * C_TYP * V_TYP / T_TYP        # (the body's pulses, in the chip's typical currents)
    C = [n[3] for n in spec["nodes"]]
    out = [abs(e[3]) / C[e[0]] / SLEW for e in spec["elements"]]
    out += [TAU_LEAK / (n[2] * n[3]) for n in spec["nodes"] if n[2] is not None]
    out += [STIMULUS / C[i] / SLEW for i in spec["sensors"]] + [TASTE / C[spec["taste"]] / SLEW]
    out += [abs(e[3]) * (e[5] / 4 if e[7] else e[5]) / C[e[0]] * TAU_LOOP
            for e in spec["elements"] if e[0] == e[1] and e[6] == 0]
    return max(out)


def violations(spec: dict) -> list:
    """What breaks the rules (AGENTS.md, The minimal circuit search): wiring that names no node, the interface
    misused, the honesty limits against the integration step (SLEW, LOOP), and a chip's limits (units.py: no resistance
    above R_MAX, capacitor above C_MAX, leak or filter slower than TAU_MAX, element current below I_MIN; the user's
    decision, 2026-10-23: a design must be buildable); and for a spec declaring
    rules "mixed" (Sepulchre's rules, an experiment: MIXED_FEEDBACK.md), every node leaky but memory nodes, and no
    clamps. Sepulchre is silent on learning and non-volatile storage, so our own components for them, gates and
    memory nodes (floating gates), stay allowed under his rules (the user's decision, 2026-10-21). Empty: a legal
    circuit."""
    n, out = len(spec["nodes"]), []
    if spec.get("units") != "SI":
        return ["not in SI units (a design from before 2026-10-22, in ticks: convert it)"]
    if not math.isclose(spec.get("volt", 1.0), V_TYP):
        return [f"drawn at {spec.get('volt', 1.0):g} V typical, not {V_TYP:.4g} (minimal/designs.py's rescale, or load)"]
    for e in spec["elements"]:
        if not (0 <= e[0] < n and 0 <= e[1] < n and -1 <= e[2] < n):
            out.append(f"element {e[:3]} names no node")
    if len(set(spec["sensors"])) != 2 or spec["taste"] in spec["sensors"] or \
            not all(0 <= i < n for i in [*spec["sensors"], *spec["motors"], spec["taste"]]):
        out.append("interface: two distinct sensors, a taste node apart from them, motors on nodes")
    for nd in spec["nodes"]:
        if nd[3] <= 0 or (nd[2] is not None and nd[2] <= 0):
            out.append(f"node {nd[0]}: capacitance and leak must be positive")
        if spec.get("rules") == "mixed" and ((nd[2] is None and not nd[7]) or nd[4] is not None or nd[5] is not None):
            out.append(f"mixed feedback's rules: node {nd[0]} must leak (unless a memory node), with no clamp")
    for nd in spec["nodes"]:                            # a chip's limits
        if nd[2] is not None and nd[2] > R_MAX * (1 + 1e-9):
            out.append(f"node {nd[0]}: a leak of {si(nd[2], 'Ω')}, above the {si(R_MAX, 'Ω')} a chip can set")
        if nd[3] > C_MAX * (1 + 1e-9):
            out.append(f"node {nd[0]}: a capacitor of {si(nd[3], 'F')}, above the {si(C_MAX, 'F')} a chip can hold")
        if nd[2] is not None and nd[2] * nd[3] > TAU_MAX * (1 + 1e-9):
            out.append(f"node {nd[0]}: a leak slower than the {si(TAU_MAX, 's')} a chip can hold")
    for e in spec["elements"]:
        if 0 < abs(e[3]) < I_MIN * (1 - 1e-9):
            out.append(f"element {e[:3]}: a current below the {si(I_MIN, 'A')} a chip can bias")
        if e[6] > TAU_MAX * (1 + 1e-9):
            out.append(f"element {e[:3]}: a filter slower than the {si(TAU_MAX, 's')} a chip can hold")
    if not out and slew(spec) > 1 + 1e-9:
        out.append(f"too fast for the step: {slew(spec):.0%} of the limits (units.py: SLEW, TAU_LEAK, TAU_LOOP)")
    return out


def check(spec: dict) -> None:
    """Refuse a circuit that breaks the rules: no illegal circuit can be built (SpecBrain calls this)."""
    bad = violations(spec)
    if bad:
        raise ValueError("illegal circuit: " + "; ".join(bad))


class Lived(list):
    """A life's thirds (a list of (food, poison, seconds)), with its circuit's mean power (W), its thrusters' firings
    per SPAN, how far the circuit is over the honesty limits, and the substrate whose noise it lived with."""
    power = 0.0
    firings = 0.0
    over = 0.0
    substrate = "biology"


def thirds(meals, moving, ticks, poison) -> list:
    """A life's meals [(tick, colour)] as (food, poison, seconds) after moving began, by third of life, then (0, 0,
    seconds before moving), so that rates over all four are per second of life."""
    start = moving if moving is not None else ticks
    out = []
    for i in range(3):
        a, z = start + i * (ticks - start) / 3, start + (i + 1) * (ticks - start) / 3
        part = [c for t, c in meals if a <= t < z]
        out.append((sum(c != poison for c in part), sum(c == poison for c in part), (z - a) * TICK))
    return out + [(0, 0, start * TICK)]


def one(job):
    """(spec, seed, poison, seconds, learning, substrate) -> the life's thirds (thirds). Mismatch comes with every
    circuit (mixed_feedback.MISMATCH), drawn from the seed."""
    from minimal.fastlife import life
    spec, seed, poison, seconds, learning, substrate = job
    ticks = int(round(seconds / TICK))
    meals, moving, power, firings = life(make(spec, substrate), seed, poison, ticks, learning)
    lived = Lived(thirds(meals, moving, ticks, poison))
    lived.power, lived.firings, lived.over = power, SPAN * firings / (ticks * TICK), max(0.0, slew(spec) - 1.0)
    lived.substrate = substrate
    return lived


_POOL = None


def pool():
    global _POOL
    if _POOL is None:
        _POOL = ProcessPoolExecutor(mp_context=multiprocessing.get_context("spawn"))
    return _POOL


JUDGED = ("silicon", "biology", "biology x2")  # the substrates whose noise a circuit is judged with (mixed_feedback.
                    # SUBSTRATES), the worst counting and the job required in each, in every polish, pruning, open search
                    # and final judgement (the user's decisions, 2026-10-22: judged at one level, pruning traded
                    # mechanism for noise, which costs no parts; then silicon, biology and twice biology's, so that a
                    # design must also work as built in silicon, where one leaning on noise fails); --substrates
                    # judges with others
LIFE = 100.0        # s: a life (10,000 ticks)
SPAN = 10.0         # s: rates are per SPAN (the same numbers as "per 1,000 ticks" before 2026-10-22)


def score(specs, seeds=range(8), seconds=LIFE, learning=True, all_food=False, substrate=None):
    """Each spec over the given seeds, each seed lived twice, red then blue as poison (a circuit that ignores taste
    lives the same life twice with the labels swapped, so it nets exactly 0), or once in all food; with each substrate's
    noise (one, or several; default JUDGED), substrate after substrate. Per spec: a list of lives (Lived)."""
    subs = JUDGED if substrate is None else (substrate,) if isinstance(substrate, str) else tuple(substrate)
    poisons = (None,) if all_food else ("red", "blue")
    legal = [not violations(s) for s in specs]
    jobs = [(s, seed, p, seconds, learning, sb) for s, ok in zip(specs, legal) if ok
            for sb in subs for seed in seeds for p in poisons]
    res = iter(pool().map(one, jobs, chunksize=max(1, len(jobs) // 64)))
    k = len(seeds) * len(poisons)
    out = []
    for s, ok in zip(specs, legal):
        if ok:
            out.append([next(res) for _ in range(k * len(subs))])
        else:                                           # not lived: a starving life, and a penalty graded by how far
            lives = []                                  # over the limits (so a search can find its way back), or a
            for sb in subs:                             # fixed one if it can't be measured
                dead = Lived([(0, 0, seconds / 3)] * 3 + [(0, 0, 0)])
                try:
                    dead.over = max(0.0, slew(s) - 1.0) + 0.1
                except (IndexError, ZeroDivisionError, TypeError):
                    dead.over = 10.0
                dead.substrate = sb
                lives += [dead] * k
            out.append(lives)
    return out


# What a creature spends and gains, in meals (the user's decisions, 2026-10-21: a low-energy brain is no use if it
# drives the body wastefully; the simplest brain should cost little beside its body). Three axioms, guesses to adjust:
MEAL = 10 * MICRO   # J: what a meal is worth
METABOLISM = 1 * MICRO  # W: what a creature burns at rest, whatever it does (a small insect's order)
FIRING = 20 * NANO  # J: what a thruster firing costs (a typical winner of the free-moving search, 2 meals and 280
                    # firings per SPAN, spends about 30% of what it eats; a circuit of a few nW about a hundredth of
                    # what moving costs)
COST = 2.0          # a poison meal counts as this many food meals lost: eating without telling them apart loses
NEED = METABOLISM * SPAN / MEAL     # meals per SPAN a creature needs, in every third of every life (1): each meal
                    # short of it costs COST (starving) ...
THRUST = FIRING / MEAL  # meals a firing costs (0.002)
ENERGY = SPAN / MEAL    # meals per SPAN per watt of the circuit's mean power (mixed_feedback._step: what the supply
                        # delivers to its transistors, chip.py)
JOB = (1.0, 3.0, 0.05)  # ... and the job: at least this much food per SPAN, this food:poison in the last third, and at
                    # most this share of lives stranded (no food at all in the last third; a creature eating 1.4 per
                    # SPAN goes a last third without food by chance about 1% of the time)


def net(lives, cost: float = COST, need: float = NEED, energy: float = ENERGY) -> float:
    """The score: food - cost x poison, per SPAN of life (counted from birth), less cost x how far each third of each
    life falls short of need (a third with no time, as when a creature never moves, wholly short), less THRUST x its
    thruster firings per SPAN (each a share of a meal), energy x its mean power, and a heavy penalty for a circuit over
    the honesty limits. Starving is counted life by life and third by third, so a life that strands (eats, then finds
    nothing more) costs in its own last third instead of hiding among other lives' meals (the user's question,
    2026-10-20: a creature that spun on the spot forever once it had eaten what was near; a fifth of the winners'
    lives did). With cost above 1 a circuit that ignores taste scores below 0 (in paired lives, -(cost - 1) x what it
    eats, less any starving), and one that stays still scores -cost x need; only learning scores above 0. Lives with
    several substrates' noise: the worst substrate's score."""
    levels = by_level(lives)
    if len(levels) > 1:
        return min(net(v, cost, need, energy) for v in levels.values())
    f = sum(a for l in lives for a, _, _ in l)
    p = sum(b for l in lives for _, b, _ in l)
    time = sum(t for l in lives for _, _, t in l)
    fr, pr = SPAN * f / time, SPAN * p / time
    short = float(np.mean([max(0.0, need - SPAN * a / t) if t > 0 else need for l in lives for a, _, t in l[:3]]))
    power = float(np.mean([getattr(l, "power", 0.0) for l in lives]))
    over = max(getattr(l, "over", 0.0) for l in lives)
    thrust = THRUST * float(np.mean([getattr(l, "firings", 0.0) for l in lives]))
    return fr - cost * pr - cost * short - energy * power - thrust - 10.0 * over


def spent(l) -> float:
    """What a life spends, in meals: resting (NEED per SPAN, the food every creature needs whatever it does), moving
    (THRUST a firing) and thinking (ENERGY per watt of the circuit's power, per SPAN)."""
    return (NEED + THRUST * l.firings + ENERGY * l.power) * sum(t for _, _, t in l) / SPAN


def efficiency(lives) -> float:
    """Meals gained per meal spent (gained: food less COST a poison; spent: resting, moving, thinking), over the
    lives: the body's efficiency, the dimension ranked against parts in the league and the open search. Above 1 a
    creature gains; going too fast wastes fuel and too slowly the resting cost, so it has a best speed between (the
    user's balance, 2026-10-21: a careful creature thinks before it moves, but eats less in a given time). Poison
    counts as in the score (the user's decision, 2026-10-21): with poison free, the most efficient scripted policy
    ate a poison for every three meals, driving into whatever lay ahead."""
    return (sum(a - COST * b for l in lives for a, b, _ in l)) / sum(spent(l) for l in lives)


def gain(lives) -> float:
    """Meals gained (food less COST a poison) per SPAN of life: speed and accuracy, energy free."""
    return SPAN * sum(a - COST * b for l in lives for a, b, _ in l) / sum(t for l in lives for _, _, t in l)


def does_job(lives) -> bool:
    """The job (JOB): enough food, food:poison in the last third, few lives stranded; with every substrate judged."""
    levels = by_level(lives)
    if len(levels) > 1:
        return all(does_job(v) for v in levels.values())
    t = sum(t for l in lives for _, _, t in l)
    lf, lp = sum(l[2][0] for l in lives), sum(l[2][1] for l in lives)
    return bool(t and SPAN * sum(a for l in lives for a, _, _ in l) / t >= JOB[0]
                and (lf / lp if lp else math.inf) >= JOB[1] and sum(l[2][0] == 0 for l in lives) / len(lives) <= JOB[2])


OBJECTIVES = {"score": net, "efficiency": efficiency, "gain": gain}
                    # what a polish or pruning maximises (the user's three objectives, 2026-10-22: the simplest brain
                    # doing the job, parts, is the open search's and the league's; the best driver for energy,
                    # efficiency; and for speed and accuracy, gain), the score the default
FAIL = 10.0         # a circuit not doing the job, judged by efficiency or gain: its score less this, so that any
                    # circuit doing the job ranks above it and among failures the score still leads towards the job


def objective(lives, by: str = "score") -> float:
    """The lives judged by one of OBJECTIVES; for efficiency or gain, only a circuit doing the job counts (FAIL), and
    across substrates the worst one's."""
    if by == "score":
        return net(lives)
    if not does_job(lives):
        return net(lives) - FAIL
    return worst(lives, OBJECTIVES[by])


def by_level(lives) -> dict:
    """The lives with each substrate's noise, in SUBSTRATES' order (score lives them substrate by substrate, each
    seed's pair together)."""
    out = {}
    for l in lives:
        out.setdefault(getattr(l, "substrate", "biology"), []).append(l)
    order = list(SUBSTRATES)
    return dict(sorted(out.items(), key=lambda kv: order.index(kv[0]) if kv[0] in order else len(order)))


def worst(lives, f) -> float:
    """A measure (higher is better) with the worst substrate's noise."""
    return min(f(v) for v in by_level(lives).values())


BOOT = 2000         # bootstrap resamples, over seeds, each seed's pair of lives kept together (the user's question,
                    # 2026-10-21: are the league's relative positions high-confidence results, or not?)


def boot_index(n_pairs: int) -> np.ndarray:
    """The resamples: the same for every design lived on the same seeds, so differences between designs are paired."""
    return np.random.default_rng(0).integers(n_pairs, size=(BOOT, n_pairs))


def per_pair(lives) -> dict:
    """Each seed's pair of lives summed: food, poison, seconds, last third's food and poison, lives stranded, meals
    spent, firings."""
    def col(f):
        x = np.array([f(l) for l in lives], dtype=float)
        return x[0::2] + x[1::2]
    return {"food": col(lambda l: sum(a for a, _, _ in l)), "poison": col(lambda l: sum(b for _, b, _ in l)),
            "time": col(lambda l: sum(t for _, _, t in l)), "lf": col(lambda l: l[2][0]), "lp": col(lambda l: l[2][1]),
            "stranded": col(lambda l: l[2][0] == 0),
            "spent": col(spent), "fired": col(lambda l: l.firings * sum(t for _, _, t in l) / SPAN)}


def resampled(pp: dict, idx: np.ndarray) -> dict:
    """Per resample: food per SPAN, gain rate (food less COST a poison, per SPAN: speed and accuracy, energy free),
    efficiency (poison counted), thrift (food per 1,000 firings), last third's food:poison, share stranded."""
    s = {k: v[idx].sum(axis=1) for k, v in pp.items()}
    with np.errstate(divide="ignore", invalid="ignore"):
        return {"food": SPAN * s["food"] / s["time"], "gain": SPAN * (s["food"] - COST * s["poison"]) / s["time"],
                "efficiency": (s["food"] - COST * s["poison"]) / s["spent"],
                "thrift": np.where(s["fired"] > 0, 1000 * s["food"] / np.maximum(s["fired"], 1e-9), 0.0),
                "last": np.where(s["lp"] > 0, s["lf"] / np.maximum(s["lp"], 1e-9), np.inf),
                "stranded": s["stranded"] / (2 * idx.shape[1])}


LOWER_IS_WORSE = ("food", "gain", "efficiency", "thrift", "last")     # (and "stranded" higher is worse)


def worst_resampled(levels: dict, idx: np.ndarray) -> dict:
    """resampled with each substrate (levels: each one's per_pair) with the same resamples (a seed drawn with one is
    drawn with every one), and the worst substrate's value in each resample: the statistic the judging uses."""
    rs = [resampled(pp, idx) for pp in levels.values()]
    return {k: (np.min if k in LOWER_IS_WORSE else np.max)(np.stack([r[k] for r in rs]), axis=0) for k in rs[0]}


def interval(x) -> list:
    """The bootstrap 95% interval."""
    return [float(np.nanpercentile(x, 2.5)), float(np.nanpercentile(x, 97.5))]


def summary(lives) -> dict:
    """The score (net, above; with a bootstrap 95% interval over seeds, each seed's pair kept together), plain net
    (food - poison), food and poison per SPAN of life, food:poison over the last third, the share of lives stranded
    (no food in the last third), firings per SPAN, gain rate (food less COST a poison per SPAN), efficiency (meals
    gained per meal spent), thrift (food per 1,000 firings), whether it does the job (JOB), and 95% intervals (ci) for
    food, gain, efficiency, thrift, food:poison and stranded. Lives with several substrates' noise: every measure is the
    worst substrate's (its interval resampled with the same seeds for every substrate), the job must be done with every
    one, and by_substrate holds each one's summary."""
    levels = by_level(lives)
    if len(levels) > 1:                                 # every measure the worst substrate's, its interval resampled jointly
        by = {k: summary(v) for k, v in levels.items()}
        n = len(next(iter(levels.values()))) // 2
        idx = boot_index(n)
        rs = worst_resampled({k: per_pair(v) for k, v in levels.items()}, idx)
        boot = np.min([[net([l for i in row for l in v[2 * i:2 * i + 2]]) for row in idx] for v in levels.values()], axis=0)
        w = lambda key, f=min: f(s[key] for s in by.values())
        sw = max(by.values(), key=lambda s: s["stranded"])
        return {"net": net(lives), "plain": w("plain"), "power": float(np.mean([s["power"] for s in by.values()])),
                "over": w("over", max), "lo": float(np.nanpercentile(boot, 2.5)), "hi": float(np.nanpercentile(boot, 97.5)),
                "food": w("food"), "poison": w("poison", max), "gain": w("gain"), "last": w("last"),
                "stranded": sw["stranded"], "firings": float(np.mean([s["firings"] for s in by.values()])),
                "efficiency": w("efficiency"), "thrift": w("thrift"), "job": all(s["job"] for s in by.values()),
                "ci": {**{k: interval(v) for k, v in rs.items() if k != "stranded"}, "stranded": sw["ci"]["stranded"]},
                "by_substrate": by}
    pairs = [lives[i:i + 2] for i in range(0, len(lives), 2)]
    idx = boot_index(len(pairs))
    boot = [net([l for i in row for l in pairs[i]]) for row in idx]
    pp = per_pair(lives)
    rs = resampled(pp, idx)
    rs_all = resampled(pp, np.arange(len(pairs))[None, :])     # (every seed once: the estimate itself)
    f = sum(a for l in lives for a, _, _ in l)
    p = sum(b for l in lives for _, b, _ in l)
    t = sum(t for l in lives for _, _, t in l)
    lf = sum(l[2][0] for l in lives)
    lp = sum(l[2][1] for l in lives)
    stranded = sum(l[2][0] == 0 for l in lives) / len(lives)
    return {"net": net(lives), "plain": net(lives, 1.0, 0.0, 0.0), "power": float(np.mean([l.power for l in lives])),
            "over": max(l.over for l in lives), "lo": float(np.nanpercentile(boot, 2.5)), "hi": float(np.nanpercentile(boot, 97.5)),
            "food": SPAN * f / t if t else 0.0, "poison": SPAN * p / t if t else 0.0,
            "gain": SPAN * (f - COST * p) / t if t else 0.0,
            "last": lf / lp if lp else math.inf, "stranded": stranded,
            "firings": float(np.mean([l.firings for l in lives])), "efficiency": efficiency(lives),
            "thrift": float(rs_all["thrift"][0]),
            "job": does_job(lives), "ci": {**{k: interval(v) for k, v in rs.items() if k != "stranded"},
                                    "stranded": wilson(int(round(stranded * len(lives))), len(lives))}}


def wilson(k: int, n: int) -> list:
    """The 95% (Wilson) interval of a share k / n: the bootstrap's would be [0, 0] when no life strands."""
    z = 1.96
    c, h = (k + z * z / 2) / (n + z * z), z * math.sqrt(k * (n - k) / n + z * z / 4) / (n + z * z)
    return [max(0.0, c - h), min(1.0, c + h)]


def pack(lives) -> list:
    """Lives as plain lists (for a cache), and back (unpack), each with its substrate (once dropped, which pooled the
    league's noise levels instead of judging the worst)."""
    return [[[list(x) for x in l], l.power, l.firings, l.over, l.substrate] for l in lives]


def unpack(packed) -> list:
    out = []
    for thirds_, power, firings, over, substrate in packed:
        l = Lived([tuple(x) for x in thirds_])
        l.power, l.firings, l.over, l.substrate = power, firings, over, substrate
        out.append(l)
    return out
