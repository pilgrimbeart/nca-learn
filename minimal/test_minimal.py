"""Checks the minimal circuit search keeps its rules (python -m minimal.test_minimal; AGENTS.md, The minimal circuit
search): the compiled life is creature.Life's, tick for tick; an illegal circuit can't be built (too fast for the
integration step, a self-feedback too fast, wiring that names no node, the interface misused, its noise turned down);
every node stays within the supply's rails; parts are counted as documented; and pruning renumbers
what it keeps. (The noise and mismatch themselves are
the simulator's: test_compiled.py.)
"""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from minimal.spec import RAIL, SpecBrain, make, parts, violations  # noqa: E402


def base() -> dict:
    """A legal circuit: two sensors, two motors, taste, a memory, one gated element."""
    nodes = [["S0", -0.5, 2.0, 1.0, None, None, None, False], ["S1", -0.5, 2.0, 1.0, None, None, None, False],
             ["M0", -1.5, 1.0, 1.0, None, None, None, False], ["M1", -1.5, 1.0, 1.0, None, None, None, False],
             ["T", -0.5, 2.0, 1.0, None, None, None, False], ["m", 0.0, None, 1.0, 0.0, 1.0, 0.5, True]]
    return {"nodes": nodes, "elements": [[2, 0, 5, 4.0, 0.5, 5.0, 0.0, True]], "sensors": [0, 1], "motors": [2, 3],
            "taste": 4}


def refused(spec) -> bool:
    try:
        SpecBrain(0, spec)
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    from creature import Life
    from brains.designed import DesignedBrain
    from minimal.fastlife import life
    failed = False

    def report(what, ok):
        global failed
        failed |= not ok
        print(f"{what}: {'ok' if ok else 'FAILED'}")

    same = True
    for seed, poison in ((0, "red"), (1, "blue"), (2, None)):
        lf = Life(seed, poison, brain=DesignedBrain)
        while lf.t < 3000:
            lf.step()
        meals, moving, _, _ = life(DesignedBrain, seed, poison, 3000)
        same &= [(a, c) for a, c in lf.meals] == meals and moving == lf.moving
    report("fastlife: the same lives as creature.Life (3 lives, 3,000 ticks)", same)

    report("a legal circuit is built", not violations(base()) and not refused(base()))
    s = base(); s["elements"][0][3] = 40.0
    report("an element too strong for its node's capacitor (40 / 1 per circuit tick) is refused", refused(s))
    s = base(); s["nodes"][2][3] = 0.1
    report("a capacitor too small for its leak (1 / RC = 10 / 1) and its element is refused", refused(s))
    s = base(); s["elements"].append([3, 3, -1, 3.0, 0.0, 1.0, 0.0, False])
    report("an unfiltered self-feedback faster than 10 steps (3 / 1 per circuit tick) is refused", refused(s))
    s = base(); s["elements"].append([3, 3, -1, 3.0, 0.0, 1.0, 20.0, False])
    report("the same self-feedback, filtered, is built", not refused(s))
    s = base(); s["nodes"][0][3] = 0.2
    report("a sensor whose pulse would move it 15 V per circuit tick is refused", refused(s))
    s = base(); s["elements"].append([9, 0, -1, 1.0, 0.0, 1.0, 0.0, True])
    report("an element naming no node is refused", refused(s))
    s = base(); s["taste"] = 0
    report("a taste node shared with a sensor is refused", refused(s))

    s = base(); s["nodes"][2] = ["M0", 2.5, 1.0, 1.0, None, None, None, False]     # rests at 2.5, kicked up by S0
    b = make(s)(0)
    hi = lo = 0.0
    for t in range(300):
        b.stimulate(0, 0.0)
        b.step()
        hi, lo = max(hi, b.circuit.V.max()), min(lo, b.circuit.V.min())
    report(f"every node within the rails (+-{RAIL:g} V): highest {hi:.2f}, lowest {lo:.2f}", hi <= RAIL and lo >= -RAIL)

    try:
        make(base(), noise=0.1)(0)
        quiet = True
    except AssertionError:
        quiet = False
    report("a circuit can't be built with its noise turned down (below mixed_feedback.NOISY)", not quiet)

    p = parts(base())
    report(f"parts counted (6 C, 5 R, 2 D, 2 T: {p['C']}, {p['R']}, {p['D']}, {p['T']})",
           (p["C"], p["R"], p["D"], p["T"]) == (6, 5, 2, 2))
    from minimal.prune import simpler
    from minimal.spec import Lived, net, tidy
    s = base()                                          # an extra node n, read only by an element into M1
    s["nodes"].insert(1, ["n", -0.5, 2.0, 1.0, None, None, None, False])
    s["elements"] = [[3, 0, 6, 4.0, 0.5, 5.0, 0.0, True], [4, 1, -1, 1.0, 0.0, 1.0, 0.0, True]]
    s["sensors"], s["motors"], s["taste"] = [0, 2], [3, 4], 5
    t = tidy(dict(s, elements=s["elements"][:1]))
    report("pruning: a node nothing reads goes, and the rest are renumbered",
           [n[0] for n in t["nodes"]] == ["S0", "S1", "M0", "M1", "T", "m"] and t["elements"] == base()["elements"]
           and (t["sensors"], t["motors"], t["taste"]) == ([0, 1], [2, 3], 4))
    options = dict(simpler(base()))
    report("pruning: each option is legal and has fewer parts",
           all(not violations(o) and parts(o)["total"] < parts(base())["total"] for o in options.values())
           and {"ungate M0<-S0|m", "no leak on T", "no low clamp on m"} <= set(options))
    even = [Lived([(2, 0, 1000)] * 3 + [(0, 0, 0)]) for _ in range(2)]            # two lives, each eating steadily
    strand = [Lived([(4, 0, 1000), (2, 0, 1000), (0, 0, 1000), (0, 0, 0)]), even[0]]  # the same food, one stranding
    report(f"the score counts starving life by life and third by third (even {net(even):+.2f}, one stranding"
           f" {net(strand):+.2f})", net(strand) < net(even))
    sys.exit(1 if failed else 0)
