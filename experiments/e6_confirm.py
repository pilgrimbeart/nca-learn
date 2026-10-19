"""E6, confirmation on held-out lives (experiments/NOTEBOOK.md): settings chosen on seeds 0-31 (E4, E5b) are compared on
fresh seeds (100-131), so the choice isn't fitted to the lives it was chosen on. R3 (sharp routing, one bridge per
neuron) against R4 (R3 with faster frustration, 0.5, and a lower growth level, 0.6), with the knowing circuit and the
oracle O1 as references.

    python -m experiments.e6_confirm [LIVES]
"""

import functools
import pickle
import sys

from brains.recruiting import RecruitingBrain
from experiments.common import E3, paired, run, summary
from experiments.e1_oracle import o1
from experiments.e3_growth import growth

R = RecruitingBrain
FIRST = 100
VARIANTS = [("knowing (no growth)", functools.partial(R, grow=False, hold="T"), None),
            ("oracle O1", functools.partial(R, grow=False, hold="T"), o1),
            ("R3", functools.partial(R, **{**E3, "sharp": True, "once": True}), None),
            ("R4", functools.partial(R, sharp=True, once=True, frustrate=0.5, grow_at=0.6, hold="T"), None)]

if __name__ == "__main__":
    lives = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    res = {}
    for name, make, setup in VARIANTS:
        res[name] = (run(make, lives, setup=setup, first_seed=FIRST),
                     run(make, lives, all_food=True, setup=setup, first_seed=FIRST))
        print(summary(name, res[name][0]), flush=True)
        print(summary("", res[name][1], all_food=True), flush=True)
        if name in ("R3", "R4"):
            kinds, when = growth(res[name][0])
            print(f"{'':35s}bridges per poison life {kinds}; first at median tick {when}", flush=True)
    print("\\nnet food per 1,000 ticks, paired (held-out seeds 100-131)")
    for name in ("oracle O1", "R3", "R4"):
        d, lo, hi = paired(res["knowing (no growth)"][0], res[name][0])
        e, elo, ehi = paired(res["knowing (no growth)"][1], res[name][1])
        print(f"  {name:10s} vs knowing: poison lives {d:+.2f} [{lo:+.2f}, {hi:+.2f}]; all-food {e:+.2f}"
              f" [{elo:+.2f}, {ehi:+.2f}]")
    for a, b in (("oracle O1", "R3"), ("oracle O1", "R4"), ("R3", "R4")):
        d, lo, hi = paired(res[a][0], res[b][0])
        print(f"  {b} vs {a}: {d:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    pickle.dump(res, open("experiments/results/e6.pkl", "wb"))
