"""Discrete circuits in SKY130 CMOS (discrete/NOTEBOOK.md, D12, D13): Netlist(chip=True) on a 1.8 V supply, eyes s0, s1,
motors m0, m1. Built part by part in a fixed order: each part draws its seed's tolerance in turn, so reordering
parts changes every seed's circuit."""

from __future__ import annotations

from discrete.life import Netlist

VDD = 1.8


def inv(n, i, o, w=1.0, l=4.0):
    n.M("N", o, i, "0", w, l)
    n.M("P", o, i, "vdd", w, l)


def sinv(n, i, o, w=1.0, l=4.0):
    """A current-starved inverter: its pull-up and pull-down each through a limiter on a bias line (about a nanoamp)."""
    n.M("P", o, i, o + "_sp", w, l)
    n.M("P", o + "_sp", "vbp", "vdd", w, l)
    n.M("N", o, i, o + "_sn", w, l)
    n.M("N", o + "_sn", "vbn", "0", w, l)


def sschmitt(n, i, o, w=1.0, l=4.0):
    """A starved Schmitt inverter: two nMOS in series to ground (their middle pulled up by an nMOS the output drives),
    two pMOS in series to the supply (their middle pulled down), each stack through a limiter on a bias line: positive
    feedback, so it switches cleanly with hysteresis, on about a nanoamp."""
    n.M("N", o, i, o + "_n", w, l)
    n.M("N", o + "_n", i, o + "_gn", w, l)
    n.M("N", o + "_gn", "vbn", "0", w, l)
    n.M("N", "vdd", o, o + "_n", w, l)
    n.M("P", o, i, o + "_p", w, l)
    n.M("P", o + "_p", i, o + "_gp", w, l)
    n.M("P", o + "_gp", "vbp", "vdd", w, l)
    n.M("P", "0", o, o + "_p", w, l)


def oai22(n, a, b, c, d, o):
    """o = not((a or b) and (c or d))."""
    n.M("N", o, a, o + "_m", 1.0); n.M("N", o, b, o + "_m", 1.0)
    n.M("N", o + "_m", c, "0", 1.0); n.M("N", o + "_m", d, "0", 1.0)
    n.M("P", o + "_ab", a, "vdd", 1.0); n.M("P", o, b, o + "_ab", 1.0)
    n.M("P", o + "_cd", c, "vdd", 1.0); n.M("P", o, d, o + "_cd", 1.0)


def aoi21(n, a, b, c, o):
    """o = not(a or (b and c))."""
    n.M("N", o, a, "0", 1.0)
    n.M("N", o, b, o + "_m", 1.0); n.M("N", o + "_m", c, "0", 1.0)
    n.M("P", o + "_bc", b, "vdd", 1.0); n.M("P", o + "_bc", c, "vdd", 1.0)
    n.M("P", o, a, o + "_bc", 1.0)


def tg(n, a, b, gn, gp):
    """A transmission gate between a and b: on while gn is high and gp low."""
    n.M("N", a, gn, b, 1.0)
    n.M("P", a, gp, b, 1.0)


def cmos_b(rng=None, vbn=0.38, vbp=1.05, vbw=0.25, vbf=1.1, cs=5e-13, ch=1.6e-11, cb=4.5e-11, cx=1e-11, wslow=0.5,
           lslow=8.0, wfast=2.0, lfast=4.0, lbl=20.0, wbt=0.6, gain=4, cdq=1.38e-11, rest=0.58, wm=1.0, lm=4.0,
           edge=0):
    """Circuit B (D13; 151 parts, about 3.7 nW): the fast model's best design, foraging and learning the bit.
    - each eye's node (cs, a weak leak) held up a few ms by each pulse, read by a starved Schmitt (e0, e1: low = seen);
    - the bit (q, qb) chooses which is food: F = seen by the eye q says is food, P = by the other (two OAI22 gates);
    - drive: F charges hd (ch, a weak leak: about 0.18 s), P empties it; a Schmitt reads it (dn low = DRIVE);
    - bored: F charges bt (cb, a weaker leak: about 6 s); a Schmitt reads it (run high = RUN, until the next F);
    - one oscillator (x, cx) charged and discharged by a starved pair (wslow), and by a second pair (wfast) while DRIVE
      or RUN: slow scan, fast drive and run; motor A on every beat, motor B on beats during DRIVE or RUN (an AOI21);
    - doubt, a bounded tally on dq: each poison's pulse drawn through a pMOS diode (tm) and copied gain times into dq
      (unit copies: a pMOS's current isn't proportional to its width), each food's through a pMOS from the taste node
      (its gate at vbf, so it passes nothing at rest) into an nMOS diode copied as many times from dq; no leak, the
      rails its bounds, its capacitor split between them so that a life begins at rest;
    - at its Schmitt's threshold (T rises) the bit's master-slave flip-flop toggles, and T pulls dq down until the
      Schmitt lets go (self-timed).
    edge: motor B latched to the beat (DRIVE-or-RUN held through each beat by a keeper), a fix for the drive's first
    beat, in which B fires alone; it only halved it (D13). Built last, so that every other part keeps its tolerance."""
    n = Netlist(rng, chip=True)
    for name, v in (("vbn", vbn), ("vbp", vbp), ("vbw", vbw), ("vbf", vbf)):
        n.lines.append(f"V{name} {name} 0 {v:g}")
        n.count["V"] = n.count.get("V", 0) + 1
    n.eye, n.motor, n.taste = ["s0", "s1"], ["m0", "m1"], "tm"
    for k in (0, 1):                                    # eyes
        n.C(f"s{k}", "0", cs)
        n.M("N", f"s{k}", "vbw", "0")
        sschmitt(n, f"s{k}", f"e{k}")
    oai22(n, "e0", "q", "e1", "qb", "F")                # food seen, poison seen
    oai22(n, "e0", "qb", "e1", "q", "P")
    inv(n, "F", "Fn")
    n.M("P", "hd", "Fn", "vdd")                         # drive
    n.M("N", "hd", "P", "0")
    n.M("N", "hd", "vbw", "0")
    n.C("hd", "0", ch)
    sschmitt(n, "hd", "dn")
    inv(n, "dn", "dr")
    n.M("P", "bt", "Fn", "vdd")                         # bored
    n.M("N", "bt", "vbw", "0", wbt, lbl)
    n.C("bt", "0", cb)
    sschmitt(n, "bt", "run")
    inv(n, "run", "runn")
    n.C("x", "0", cx)                                   # the oscillator
    sschmitt(n, "x", "y")
    sinv(n, "y", "m0")
    n.M("P", "x", "m0", "x_cp", wslow, lslow); n.M("P", "x_cp", "vbp", "vdd", wslow, lslow)
    n.M("N", "x", "m0", "x_cn", wslow, lslow); n.M("N", "x_cn", "vbn", "0", wslow, lslow)
    n.M("N", "idle", "dn", "idle_m", 1.0); n.M("N", "idle_m", "runn", "0", 1.0)   # idle = nand(dn, runn): DRIVE or RUN
    n.M("P", "idle", "dn", "vdd", 1.0); n.M("P", "idle", "runn", "vdd", 1.0)
    inv(n, "idle", "dorn")
    n.M("P", "x", "m0", "x_fp"); n.M("P", "x_fp", "dorn", "x_fp2"); n.M("P", "x_fp2", "vbp", "vdd", wfast, lfast)
    n.M("N", "x", "m0", "x_fn"); n.M("N", "x_fn", "idle", "x_fn2"); n.M("N", "x_fn2", "vbn", "0", wfast, lfast)
    if edge:                                            # (the AOI21's six draws taken, built below)
        for _ in range(6 if n.rng is not None else 0):
            n.rng.normal()
    else:
        aoi21(n, "y", "dn", "runn", "m1")               # motor B: beat and (DRIVE or RUN)
    n.M("P", "tm", "tm", "vdd", 1.0)                    # doubt: poison up
    for _ in range(int(gain)):
        n.M("P", "dq", "tm", "vdd", 1.0)
    n.M("P", "fdn", "vbf", "tm", 1.0)                   # food down
    n.M("N", "fdn", "fdn", "0", wm, lm)
    for _ in range(int(gain)):
        n.M("N", "dq", "fdn", "0", wm, lm)
    n.M("N", "dq", "T", "dq_r", 1.0)                    # the flip's reset
    n.M("N", "dq_r", "vbn", "0", 1.0)
    n.C("dq", "vdd", cdq * rest)
    n.C("dq", "0", cdq * (1 - rest))
    sschmitt(n, "dq", "Tx")
    inv(n, "Tx", "T")
    inv(n, "T", "Tn")                                   # the bit: a master-slave flip-flop toggled as T rises (T
    inv(n, "Tn", "Tb")                                  # sharpened through two inverters): the master follows qb while
    n.R("qb", "qd", 1e9)                                # T is low, slowly (so that it can't follow the slave in the
    n.C("qd", "0", 1e-12)                               # moment both gates are half open), and holds while T is high,
    tg(n, "qd", "ma", "Tn", "Tb")                       # when the slave takes qb from it (so q flips)
    inv(n, "ma", "mb")
    inv(n, "mb", "mc")
    tg(n, "mc", "ma", "Tb", "Tn")
    tg(n, "mb", "qb", "Tb", "Tn")
    inv(n, "qb", "q")
    inv(n, "q", "qc")
    tg(n, "qc", "qb", "Tn", "Tb")
    if edge:                                            # motor B: beat and (DRIVE or RUN) as it was when the beat began:
        sinv(n, "y", "yb")                              # dorn latched while y is high, held through the beat
        tg(n, "dorn", "el", "y", "yb")
        sinv(n, "el", "elb")
        n.M("N", "el", "elb", "el_n", 0.36, 8.0); n.M("N", "el_n", "yb", "0", 0.36, 8.0)   # weak keeper, on while
        n.M("P", "el", "elb", "el_p", 0.42, 8.0); n.M("P", "el_p", "y", "vdd", 0.42, 8.0)  # the gate is shut
        n.M("P", "m1_p", "y", "vdd", 1.0); n.M("P", "m1", "el", "m1_p", 1.0)               # m1 = nor(y, el)
        n.M("N", "m1", "y", "0", 1.0); n.M("N", "m1", "el", "0", 1.0)
    return n
