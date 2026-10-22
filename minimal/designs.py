"""Circuits for the minimal circuit search (minimal/NOTEBOOK.md), each a function from its parameters to a spec
(minimal/spec.py), with its parameters' starting values and bounds. Mirror-image parts share parameters.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from minimal.spec import parts  # noqa: E402

TASTE_R = 0.5       # the taste node of every circuit brain so far (brains/circuit.py), to start from


def from_brain(cls, seed: int = 0) -> dict:
    """The spec of an existing circuit brain (for comparison: its parts and its score here)."""
    b = cls(seed)
    c = b.circuit
    nodes = [[c.names[i], bias, None if leak == 0 else 1.0 / leak, C, lo, hi, c.start[i], w > 0]
             for i, (bias, leak, C, lo, hi, w) in enumerate(c.nodes)]
    els = [[to, frm, gate, g, o, s, ta, sg] for (g, o, s, ta, sg), (to, frm, gate) in c.elements]
    return {"nodes": nodes, "elements": els, "sensors": list(b.sensors), "motors": list(b.motors),
            "taste": b.taste_node}


# A: six nodes. Sensors S0, S1 (capacitors with a leak); motors M0, M1 (resting below threshold: a kick, one spike);
# taste T; a memory m (the bit: high, sensor 0 is food). Each sensor drives its own motor; the other motor through m
# (S0 -> M1 while m is high, S1 -> M0 while m is low: the element's input is m, its gate the sensor). A good taste
# after a sensor was active (its filtered voltage: the eligibility) moves m towards it.
A_PARAMS = {  # name: (start, lo, hi)
    "s_R": (2.0, 0.25, 50.0),       # sensor: leak (C = 1) ...
    "s_rest": (-0.7, -3.0, 0.0),    # ... and where it rests (below 0, so its gates stay shut in noise)
    "m_rest": (-1.5, -3.0, -1.05),  # motor: where it rests ...
    "m_R": (1.0, 0.1, 50.0),        # ... its leak ...
    "m_C": (1.0, 0.05, 20.0),       # ... and capacitance (with the noise on every node: how often it fires alone)
    "d_gain": (4.0, 0.5, 10.0),     # sensor -> its own motor
    "d_off": (0.5, -1.0, 3.0),
    "x_gain": (4.0, 0.5, 10.0),     # m -> the other motor, gated by the sensor
    "x_slope": (10.0, 1.0, 30.0),
    "e_tau": (10.0, 0.5, 100.0),    # eligibility: the write element's input filter
    "e_off": (0.5, -1.0, 3.0),
    "e_slope": (8.0, 1.0, 30.0),
    "w_gain": (0.2, 0.005, 5.0),    # how fast a good taste writes m
    "t_R": (2.0, 0.1, 20.0),        # taste node's leak (C = 1) ...
    "t_rest": (-0.7, -3.0, 0.0),    # ... and where it rests
}


def A(p: dict, clamp: bool = True) -> dict:
    lo, hi = (0.0, 1.0) if clamp else (None, None)
    nodes = [["S0", p["s_rest"] / p["s_R"], p["s_R"], 1.0, None, None, None, False],
             ["S1", p["s_rest"] / p["s_R"], p["s_R"], 1.0, None, None, None, False],
             ["M0", p["m_rest"] / p["m_R"], p["m_R"], p["m_C"], None, None, None, False],
             ["M1", p["m_rest"] / p["m_R"], p["m_R"], p["m_C"], None, None, None, False],
             ["T", p["t_rest"] / p["t_R"], p["t_R"], 1.0, None, None, None, False],
             ["m", 0.0, None, 1.0, lo, hi, 0.5, True]]
    S0, S1, M0, M1, T, m = range(6)
    els = [[M0, S0, -1, p["d_gain"], p["d_off"], 5.0, 0.0, True],
           [M1, S1, -1, p["d_gain"], p["d_off"], 5.0, 0.0, True],
           [M1, m, S0, p["x_gain"], 0.5, p["x_slope"], 0.0, True],
           [M0, m, S1, p["x_gain"], 0.5, -p["x_slope"], 0.0, True],
           [m, S0, T, p["w_gain"], p["e_off"], p["e_slope"], p["e_tau"], True],
           [m, S1, T, -p["w_gain"], p["e_off"], p["e_slope"], p["e_tau"], True]]
    return {"nodes": nodes, "elements": els, "sensors": [S0, S1], "motors": [M0, M1], "taste": T}


DESIGNS = {"A": (A, A_PARAMS)}


def start(params: dict) -> dict:
    return {k: v[0] for k, v in params.items()}


if __name__ == "__main__":
    from brains.designed import DesignedBrain
    from minimal.spec import score, summary
    import time
    specs = {"designed circuit": from_brain(DesignedBrain), "A (hand)": A(start(A_PARAMS))}
    t0 = time.time()
    res = score(list(specs.values()), seeds=range(16))
    for (name, s), lives in zip(specs.items(), res):
        r = summary(lives)
        print(f"{name:20s} parts {parts(s)}  score {r['net']:+.2f} [{r['lo']:+.2f}, {r['hi']:+.2f}]  food {r['food']:.2f}"
              f"  poison {r['poison']:.2f}  last third {r['last']:.2f}  job {r['job']}")
    print(f"{time.time() - t0:.1f} s")


# G: A with each simplification as a switch, for pruning (minimal/NOTEBOOK.md, M2). clamp: m clamped to 0..1.
# writes: 2 (each sensor writes m its way) or 1 (only sensor 0 writes, from m = 0: a default guess, sensor 1 is food,
# corrected by evidence). merge: each sensor is its own motor (no separate motor nodes, no direct elements; a sensor
# node rests below -1, so a kick gives one spike). filt: the eligibility is the write element's input filter; without
# it, the sensor node's own decay.
G_PARAMS = dict(A_PARAMS)


def G(p: dict, clamp=True, writes=2, merge=False, filt=True) -> dict:
    S0, S1 = 0, 1
    nodes = [["S0", p["s_rest"] / p["s_R"], p["s_R"], 1.0, None, None, None, False],
             ["S1", p["s_rest"] / p["s_R"], p["s_R"], 1.0, None, None, None, False]]
    if merge:
        M0, M1 = S0, S1
    else:
        nodes += [["M0", p["m_rest"] / p["m_R"], p["m_R"], p["m_C"], None, None, None, False],
                  ["M1", p["m_rest"] / p["m_R"], p["m_R"], p["m_C"], None, None, None, False]]
        M0, M1 = 2, 3
    T, m = len(nodes), len(nodes) + 1
    lo, hi = (0.0, 1.0) if clamp else (None, None)
    nodes += [["T", p["t_rest"] / p["t_R"], p["t_R"], 1.0, None, None, None, False],
              ["m", 0.0, None, 1.0, lo, hi, 0.5 if writes == 2 or both else 0.0, True]]
    els = [] if merge else [[M0, S0, -1, p["d_gain"], p["d_off"], 5.0, 0.0, True],
                            [M1, S1, -1, p["d_gain"], p["d_off"], 5.0, 0.0, True]]
    els += [[M1, m, S0, p["x_gain"], 0.5, p["x_slope"], 0.0, True],
            [M0, m, S1, p["x_gain"], 0.5, -p["x_slope"], 0.0, True]]
    tau = p["e_tau"] if filt else 0.0
    els.append([m, S0, T, p["w_gain"], p["e_off"], p["e_slope"], tau, True])
    if writes == 2:
        els.append([m, S1, T, -p["w_gain"], p["e_off"], p["e_slope"], tau, True])
    return {"nodes": nodes, "elements": els, "sensors": [S0, S1], "motors": [M0, M1], "taste": T}


def _variant(**kw):
    return lambda p: G(p, **kw)


for _c in (True, False):
    for _w in (2, 1):
        for _m in (False, True):
            for _f in (True, False):
                DESIGNS[f"G{'c' if _c else ''}{_w}{'m' if _m else ''}{'f' if _f else ''}"] = (
                    _variant(clamp=_c, writes=_w, merge=_m, filt=_f), G_PARAMS)


# C: spin and search. Motor 1 is a relaxation oscillator (a neuron, as mixed_feedback.neuron, biased to fire on its
# own: fast positive feedback, slow negative): it fires at a rate its own parts set, not the noise, so the creature
# circles, its eyes sweeping all round. Motor 0 is a plain node resting below threshold: seeing food kicks it, both
# thrusters fire, and the creature drives straight at the food; poison leaves it circling, so it turns away. The bit
# m says which sensor kicks motor 0 (the element's input m, its gate the sensor, as in A); writes as in G.
# (bounds widened 2026-10-20 where tuned values sat on them: t_rest, w_gain, o_gain, o_tau, s_rest)
C_PARAMS = {
    "s_R": (2.0, 0.25, 50.0),
    "s_rest": (-0.7, -2.9, 0.0),
    "s_C": (1.0, 0.1, 50.0),        # sensor capacitance: bigger is quieter, but a pulse lifts it less
    "o_bias": (-0.5, -3.0, 3.0),    # the oscillator (a neuron biased to fire on its own): its bias (R = 1) ...
    "o_pos": (2.0, 0.2, 10.0),      # ... its fast positive feedback ...
    "o_gain": (2.0, 0.2, 50.0),     # ... and its slow negative feedback: how hard ...
    "o_tau": (10.0, 0.5, 300.0),    # ... and how slow ...
    "o_C": (1.0, 0.05, 20.0),       # ... and its capacitor
    "m_rest": (-1.5, -3.0, -1.05),  # motor 0 (R = 1, C = 1)
    "x_gain": (4.0, 0.5, 10.0),     # m -> motor 0, gated by the sensor
    "x_slope": (10.0, 1.0, 30.0),
    "e_tau": (10.0, 0.5, 100.0),
    "e_off": (0.5, -1.0, 3.0),
    "e_slope": (8.0, 1.0, 30.0),
    "w_gain": (0.2, 0.005, 20.0),
    "t_R": (2.0, 0.1, 20.0),
    "t_rest": (-0.7, -2.9, 0.0),
    "t_C": (1.0, 0.1, 50.0),        # taste node capacitance (noise opening the write gates wanders the memory)
    "b_depth": (1.0, 0.1, 5.0),     # bad-taste writes: how far below rest the taste node must fall ...
    "b_slope": (10.0, 1.0, 30.0),   # ... and how sharply the write turns on there
    "u_slope": (0.3, 0.01, 10.0),   # one write both ways: the tanh's slope (small: noise about rest writes little)
}


def C(p: dict, clamp=True, writes=2, filt=True, bad=False, both=False) -> dict:
    """bad: write from bad tastes instead, the taste node the write element's input (a steep threshold, below its
    rest) and the sensor its gate (so the eligibility is the sensor's own decay: no filter). With one write, from
    m = 0 (the guess: sensor 1 is food), a bad taste after sensor 1 sets m: a wrong guess eats the poison it approaches,
    and that is the evidence (good-taste writes never taste the food a wrong guess circles away from)."""
    S0, S1, M0, M1, T, m = range(6)
    lo, hi = (0.0, 1.0) if clamp else (None, None)
    nodes = [["S0", p["s_rest"] / p["s_R"], p["s_R"], p.get("s_C", 1.0), None, None, None, False],
             ["S1", p["s_rest"] / p["s_R"], p["s_R"], p.get("s_C", 1.0), None, None, None, False],
             ["M0", p["m_rest"], 1.0, 1.0, None, None, None, False],
             ["M1", p["o_bias"], 1.0, p["o_C"], None, None, None, False],
             ["T", p["t_rest"] / p["t_R"], p["t_R"], p.get("t_C", 1.0), None, None, None, False],
             ["m", 0.0, None, 1.0, lo, hi, 0.5 if writes == 2 else 0.0, True]]
    tau = p["e_tau"] if filt and not bad else 0.0
    els = [[M1, M1, -1, p["o_pos"], -1.5, 1.0, 0.0, False],
           [M1, M1, -1, -p["o_gain"], -1.5, 1.0, p["o_tau"], False],
           [M0, m, S0, p["x_gain"], 0.5, p["x_slope"], 0.0, True],
           [M0, m, S1, p["x_gain"], 0.5, -p["x_slope"], 0.0, True]]
    if both:                                    # one write, both ways: tanh of the taste node about its rest, gated
        els.append([m, T, S0, p["w_gain"], p["t_rest"], p["u_slope"], 0.0, False])   # by S0 (good: up, bad: down)
    elif bad:
        off = p["t_rest"] - p["b_depth"]
        els.append([m, T, S1, p["w_gain"], off, -p["b_slope"], 0.0, True])          # bad after S1: m up
        if writes == 2:
            els.append([m, T, S0, -p["w_gain"], off, -p["b_slope"], 0.0, True])    # bad after S0: m down
    else:
        els.append([m, S0, T, p["w_gain"], p["e_off"], p["e_slope"], tau, True])
        if writes == 2:
            els.append([m, S1, T, -p["w_gain"], p["e_off"], p["e_slope"], tau, True])
    return {"nodes": nodes, "elements": els, "sensors": [S0, S1], "motors": [M0, M1], "taste": T}


for _c in (True, False):
    for _w in (2, 1):
        for _f in (True, False):
            DESIGNS[f"C{'c' if _c else ''}{_w}{'f' if _f else ''}"] = (
                (lambda c, w, f: (lambda p: C(p, clamp=c, writes=w, filt=f)))(_c, _w, _f), C_PARAMS)
        DESIGNS[f"C{'c' if _c else ''}1t"] = ((lambda c: (lambda p: C(p, clamp=c, writes=1, both=True)))(_c), C_PARAMS)
        DESIGNS[f"C{'c' if _c else ''}{_w}b"] = ((lambda c, w: (lambda p: C(p, clamp=c, writes=w, bad=True)))(_c, _w),
                                                  C_PARAMS)


# Any circuit as a family of its own parameters (for polishing what the open search found): each leaky node's rest,
# leak and capacitance, a memory's starting value, and each element's gain, offset, slope and (if filtered) time
# constant; the topology fixed.
def hungry(spec: dict, tau: float = 8700.0, C: float = 8.7, rest: float = 1.0) -> dict:
    """A hunger added to a circuit (minimal/NOTEBOOK.md, M8): a node H charging towards rest over tau circuit ticks,
    drained by a good taste (an element from the taste node, its step at 1.5 V, well above the taste node's rest, so
    it doesn't leak at rest), and an element from the clock (motor 1) into motor 0 gated by H, so that while H is high
    both thrusters fire together and the spin becomes a straight run. The reads become tanh, so the colour the bit
    calls poison holds motor 0 down (a hungry run stops at poison). 5 parts more."""
    import copy
    s = copy.deepcopy(spec)
    M0, M1 = s["motors"]
    T = s["taste"]
    R = tau / C
    H = len(s["nodes"])
    s["nodes"].append(["H", rest / R, R, C, None, None, None, False])
    for e in s["elements"]:
        if e[0] == M0 and e[2] in s["sensors"]:
            e[7] = False                                # a read: tanh
    s["elements"].append([H, T, -1, -20.0, 1.5, 10.0, 0.0, True])          # a good taste drains H
    s["elements"].append([M0, M1, H, 3.0, 0.0, 5.0, 0.0, True])            # hungry: the clock drives motor 0 too
    return s


HOLD_ROAM = dict(ma_bias=0.0, ma_tau=20.0, ma_slow=-4.0, mb_bias=-2.6, syn=3.0, g_C=4.0, g_tau=200.0, g_rest=-1.5,
                 g_gain=4.0, r_C=8.0, r_tau=300.0, r_rest=2.5, r_th=1.0, r_gain=2.0, r_drain=-8.0)


def hold_roam(senses: dict, p: dict = HOLD_ROAM) -> dict:
    """The hold-and-roam circuit (minimal/NOTEBOOK.md, M11; HR_35p): the senses and memory of a spinning circuit
    (`senses`, EF_22p's: sensors S0, S1, taste T, the bit m, its two writes and two reads), its motor stage replaced.
    MA, an oscillator on one motor (fast positive feedback and a strong slow negative one, so its rate barely depends
    on mismatch), scans; G, a hold node (time constant g_tau circuit ticks), is charged by a sighting of the colour
    the bit calls food and drained by the other's, through the reads; MB, an excitable node on the other motor,
    copies MA's spikes while G is open, so both thrusters fire together and the creature goes straight; and Rt, a
    roam timer, fills while G is shut and, when full, opens G (a sharp drain: a sigmoid's tail at rest would match
    its charging current)."""
    import copy
    S0, S1, _, _, T, m = copy.deepcopy(senses["nodes"])
    e = senses["elements"]
    gR, rR = p["g_tau"] / p["g_C"], p["r_tau"] / p["r_C"]
    nodes = [S0, S1, T, m,
             ["G", p["g_rest"] / gR, gR, p["g_C"], None, None, None, False],
             ["MA", p["ma_bias"], 2.0, 1.0, None, None, None, False],
             ["MB", p["mb_bias"], 2.0, 1.0, None, None, None, False],
             ["Rt", p["r_rest"] / rR, rR, p["r_C"], None, None, None, False]]
    iS0, iS1, iT, im, iG, iA, iB, iR = range(8)
    elements = [
        [im, iS0, iT, *e[3][3:]],                                   # the writes
        [im, iS1, iT, *e[4][3:]],
        [iG, im, iS0, p["g_gain"], e[1][4], e[1][5], 0.0, False],   # the reads: approach if food, retreat if poison
        [iG, im, iS1, p["g_gain"] * e[2][3] / e[1][3], e[2][4], e[2][5], 0.0, False],
        [iA, iA, -1, 2.0, -1.5, 1.0, 0.0, False],                   # MA: the scan
        [iA, iA, -1, p["ma_slow"], -1.5, 1.0, p["ma_tau"], False],
        [iB, iB, -1, 2.0, -1.5, 1.0, 0.0, False],                   # MB: excitable, silent alone
        [iB, iB, -1, -2.0, -1.5, 1.0, 10.0, False],
        [iB, iA, iG, p["syn"], 0.0, 5.0, 0.0, True],                # ... copying MA's spikes while G is open
        [iG, iR, -1, p["r_gain"], p["r_th"], 4.0, 0.0, True],       # the timer full: open G
        [iR, iG, -1, p["r_drain"], 1.0, 8.0, 0.0, True],            # G open: empty the timer
    ]
    return {"nodes": nodes, "elements": elements, "sensors": [iS0, iS1], "motors": [iA, iB], "taste": iT}


def raw(spec: dict):
    """(design, params) for a raw spec: its numbers as parameters, each searched within a factor of 4 of where it is
    (offsets and rests +-1.5 V), inside the bounds of the open search."""
    import copy
    params, where = {}, []
    for i, n in enumerate(spec["nodes"]):
        if n[2] is not None:
            rest = n[1] * n[2]
            params[f"n{i}_rest"] = (rest, max(rest - 1.5, -2.9), min(rest + 1.5, 2.9))
            params[f"n{i}_R"] = (n[2], max(n[2] / 4, 0.1), min(n[2] * 4, 1000.0))
        elif n[6] is not None:
            params[f"n{i}_start"] = (n[6], 0.0, 1.0)
        params[f"n{i}_C"] = (n[3], max(n[3] / 4, 0.05), min(n[3] * 4, 100.0))
    for j, e in enumerate(spec["elements"]):
        g = e[3]
        params[f"e{j}_gain"] = (g, g * 4 if g < 0 else g / 4, g / 4 if g < 0 else g * 4) if g else (0.0, -1.0, 1.0)
        params[f"e{j}_off"] = (e[4], e[4] - 1.5, e[4] + 1.5)
        params[f"e{j}_slope"] = (e[5], max(e[5] / 4, 0.1), min(e[5] * 4, 30.0))
        if e[6] > 0:
            params[f"e{j}_tau"] = (e[6], max(e[6] / 4, 0.5), min(e[6] * 4, 300.0))
    params = {k: (v, min(lo, hi), max(lo, hi)) for k, (v, lo, hi) in params.items()}

    def design(p: dict) -> dict:
        s = copy.deepcopy(spec)
        for i, n in enumerate(s["nodes"]):
            if n[2] is not None:
                n[2] = p[f"n{i}_R"]
                n[1] = p[f"n{i}_rest"] / n[2]
            elif n[6] is not None:
                n[6] = p[f"n{i}_start"]
            n[3] = p[f"n{i}_C"]
        for j, e in enumerate(s["elements"]):
            e[3], e[4], e[5] = p[f"e{j}_gain"], p[f"e{j}_off"], p[f"e{j}_slope"]
            if e[6] > 0:
                e[6] = p[f"e{j}_tau"]
        return s
    return design, params
