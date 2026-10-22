"""E4, ablations and improvements (experiments/NOTEBOOK.md): which parts of the growth mechanism matter, and do the two
fixes suggested by E3 (sharp routing; one bridge per neuron) close the gap to the oracle? All paired with the knowing
brain and the oracle O1, life for life.

    python -m experiments.e4_variants [LIVES]
"""

import functools
import pickle
import sys

from brains.recruiting import RecruitingBrain
from experiments.common import E3, paired, run, summary
from experiments.e1_oracle import o1
from experiments.e3_growth import growth

R = RecruitingBrain
VARIANTS = [("knowing (no growth)", functools.partial(R, grow=False, hold="T"), None),
            ("oracle O1", functools.partial(R, grow=False, hold="T"), o1),
            ("R0 as E3", functools.partial(R, **E3), None),
            ("A1 no routing", functools.partial(R, **E3, route=False), None),
            ("A2 no competition", functools.partial(R, **E3, compete=False), None),
            ("R1 sharp routing", functools.partial(R, **{**E3, "sharp": True}), None),
            ("R2 one bridge per neuron", functools.partial(R, **{**E3, "once": True}), None),
            ("R3 sharp + one per neuron", functools.partial(R, **{**E3, "sharp": True, "once": True}), None)]

if __name__ == "__main__":
    lives = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    res = {}
    for name, make, setup in VARIANTS:
        res[name] = (run(make, lives, setup=setup), run(make, lives, all_food=True, setup=setup))
        print(summary(name, res[name][0]), flush=True)
        print(summary("", res[name][1], all_food=True), flush=True)
        if name not in ("knowing (no growth)", "oracle O1"):
            kinds, when = growth(res[name][0])
            print(f"{'':35s}bridges per poison life {kinds}; first at median {when} s", flush=True)
    print("\\nnet food per 10 s, paired: against knowing (poison lives; all-food lives), and against oracle O1")
    for name in res:
        d, lo, hi = paired(res["knowing (no growth)"][0], res[name][0])
        e, elo, ehi = paired(res["knowing (no growth)"][1], res[name][1])
        o, olo, ohi = paired(res["oracle O1"][0], res[name][0])
        print(f"  {name:28s} {d:+.2f} [{lo:+.2f}, {hi:+.2f}];  {e:+.2f} [{elo:+.2f}, {ehi:+.2f}];"
              f"  vs O1 {o:+.2f} [{olo:+.2f}, {ohi:+.2f}]")
    pickle.dump(res, open("experiments/results/e4.pkl", "wb"))
