"""Checks the discrete line's fast model and its circuit keep what they claim (python -m discrete.test_model;
discrete/NOTEBOOK.md, D13): the model lives the same lives as when circuit B's score was predicted; each life draws
its own blocks, the same for a seed every time; doubt is a bounded tally that flips the bit at its threshold; the
drive's stray first beat is there only when asked for; and circuit B is built as it was benched and lived in SPICE
(its parts, and each seed's tolerances in the same order, the latch built last so that it moves no other part's); the
self-tuning brain (discrete/tuner.py, D15) lives its lives as when it was moved, fixed it is B where born, and its
knobs move only by tuning and stay within their bounds.
No SPICE here: the bench (discrete/blocks.py) and the closed loop (discrete/life.py) need ngspice."""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from discrete import model as M  # noqa: E402
from discrete import tuner as T  # noqa: E402
from discrete.cmos import cmos_b  # noqa: E402

# B from its bench, judged robustly, on held-out seeds 50000-50001 (red, then blue as poison): each third's (food,
# poison), as the model lived them when it was moved into discrete/ (2026-10-29)
LIVED = [[(14, 6), (15, 0), (29, 5)], [(17, 4), (14, 4), (21, 2)], [(29, 3), (26, 4), (27, 4)],
         [(20, 5), (12, 6), (33, 1)]]
# the tuner on seed 50000 (red as poison), 300 s, on the standard body and a lopsided one, as when it was moved into
# discrete/ (2026-10-30; it reproduced D15's 10,000 s lives exactly)
TUNED = [[(49, 7), (80, 10), (57, 19)], [(7, 7), (6, 9), (33, 12)]]


if __name__ == "__main__":
    failed = False

    def report(what, ok):
        global failed
        failed |= not ok
        print(f"{what}: {'ok' if ok else 'FAILED'}")

    p, spread = M.from_bench()
    L = [M.life((p, spread, s, 100.0, c)) for s in (50000, 50001) for c in ("red", "blue")]
    report("the model lives B's lives as when they were predicted (4 lives, 100 s)",
           [[tuple(t[:2]) for t in l[:3]] for l in L] == LIVED)

    a, b, c = M.drawn(p, spread, 7), M.drawn(p, spread, 7), M.drawn(p, spread, 8)
    report("each life draws its own blocks, the same for a seed every time", a == b and a != c
           and all(a[k] > 0 for k in M.TIMERS))
    q = dict(p, vary=0)
    nominal = M.life((q, spread, 3, 10.0, "red"))
    report("the nominal model (vary=0, for debugging) lives", sum(t[0] + t[1] for t in nominal[:3]) >= 0)

    m = M.Model(0, p)
    bit, v0 = m.food, m.dq
    m.taste(+1, 0.0)
    down = m.dq
    m.taste(-1, 0.0)
    up = m.dq
    report(f"doubt: born at trust (V_L {p['V_L']:.2f} V), a food steps it down to its rail, a poison up by "
           f"{p['step']:.2f} V", v0 == p["V_L"] and down == 0.0 and abs(up - p["step"]) < 1e-12)
    n = 0
    while m.food == bit and n < 10:
        m.taste(-1, 0.0)
        n += 1
    report(f"doubt: poisons in a row ({n + 1}) reach V_H ({p['V_H']:.2f} V), flip the bit and reset it to V_L",
           m.food != bit and m.dq == p["V_L"] and len(m.flips) == 1)
    for _ in range(20):
        m.taste(-1, 0.0)
    report("doubt stays within the rails", 0.0 <= m.dq <= M.RAIL)

    def first_beats(lone):
        m = M.Model(0, dict(p, lone=lone, scan=1e-6, bored=1e12))   # (scanning, not bored)
        m.step()
        m.stimulate(m.food, 0.0)
        out = m.step()
        return out.count(1) - out.count(0)              # motor B's firings beyond A's
    report("a drive's stray first beat (motor B alone, D13) only when asked for (lone)",
           first_beats(0.0) == 0 and first_beats(1.0) == 1)

    rng = lambda s: np.random.default_rng(s + 5_000_011)
    n0, n1, e0 = cmos_b(rng(4)), cmos_b(rng(4)), cmos_b(rng(4), edge=1)
    report(f"circuit B is built of {n0.parts()} parts (151 as benched), each seed's the same every time",
           n0.parts() == 151 and n0.text() == n1.text() and cmos_b().parts() == 151)
    parts = lambda n: [ln.split(None, 1)[1] for ln in n.lines if ln[0] in "XRC"]   # (without their names)
    rest0 = [ln for ln in parts(n0) if not {"m1", "m1_m", "m1_bc"} & set(ln.split())]   # all but the AOI21
    report(f"the latch on motor B ({e0.parts()} parts) moves no other part's tolerance", e0.parts() == 163
           and parts(e0)[:-18] == rest0)   # (its 18 transistors, for the AOI21's 6)

    L = [T.life((dict(p, body=b), spread, 50000, 300.0, "red")) for b in (0, 1)]
    report("the self-tuning brain lives its lives as when it was moved (2 lives, 300 s)",
           [[tuple(t[:2]) for t in l[:3]] for l in L] == TUNED)
    report("its knobs stay within their bounds", all(np.log(T.BOUNDS[k][0]) <= v <= np.log(T.BOUNDS[k][1])
                                                     for l in L for _, x, _ in l.trace for k, v in x.items()))
    fixed = T.life((dict(p, tune=0), spread, 50001, 100.0, "blue"))
    born = T.mistuned(M.drawn(p, spread, 50001), 50001, 3.0)
    plain = M.life((dict(born, vary=0), spread, 50001, 100.0, "blue"))
    report("fixed (tune=0), it lives B's life with the knobs it was born with (the floor)",
           [tuple(t) for t in fixed] == [tuple(t) for t in plain])
    still = T.life((dict(p, eta=0.0), spread, 50000, 300.0, "red"))
    report("its knobs move only by tuning (eta=0: each stays where born, only wiggling)",
           all(x == still.trace[0][1] for _, x, _ in still.trace) and L[0].trace[-1][1] != L[0].trace[0][1])
    sys.exit(1 if failed else 0)
