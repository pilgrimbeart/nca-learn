"""E7, a local hold (experiments/NOTEBOOK.md): the bridge's hold was charged by the taste neuron T, so the growth rule
had to know which neuron's frustration summoned it, a piece of knowledge the circuit doesn't have. The alternative:
charge the hold by the sensor's own spikes gated by its synapse onto T (W: "my activity predicts pain"), using only
the sensor's own synapses. Compared hand-placed (each structure's ceiling) and grown, on the original seeds (0-31)
and on held-out seeds (100-131), paired with the knowing circuit.

    python -m experiments.e7_local_hold [LIVES]
"""

import functools
import pickle
import sys

from brains.recruiting import RecruitingBrain
from experiments.common import paired, run, summary
from experiments.e1_oracle import o1
from experiments.e3_growth import growth

R = RecruitingBrain
VARIANTS = [("knowing (no growth)", functools.partial(R, grow=False), None),
            ("oracle, T hold", functools.partial(R, grow=False, hold="T"), o1),
            ("oracle, local hold", functools.partial(R, grow=False, hold="sensor"), o1),
            ("R4, T hold", functools.partial(R, hold="T"), None),
            ("R4, local hold", functools.partial(R, hold="sensor"), None)]

if __name__ == "__main__":
    lives = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    res = {}
    for first in (0, 100):
        print(f"\\nseeds {first}-{first + lives // 2 - 1}")
        for name, make, setup in VARIANTS:
            res[(first, name)] = (run(make, lives, setup=setup, first_seed=first),
                                  run(make, lives, all_food=True, setup=setup, first_seed=first))
            print(summary(name, res[(first, name)][0]), flush=True)
            if name.startswith("R4"):
                kinds, when = growth(res[(first, name)][0])
                print(f"{'':35s}bridges per poison life {kinds}; first at median tick {when}", flush=True)
        base = res[(first, "knowing (no growth)")]
        for name in ("oracle, T hold", "oracle, local hold", "R4, T hold", "R4, local hold"):
            d, lo, hi = paired(base[0], res[(first, name)][0])
            e, elo, ehi = paired(base[1], res[(first, name)][1])
            print(f"  {name:20s} vs knowing: poison lives {d:+.2f} [{lo:+.2f}, {hi:+.2f}]; all-food {e:+.2f}"
                  f" [{elo:+.2f}, {ehi:+.2f}]")
        for a, b in (("oracle, T hold", "oracle, local hold"), ("R4, T hold", "R4, local hold")):
            d, lo, hi = paired(res[(first, a)][0], res[(first, b)][0])
            print(f"  {b} vs {a}: {d:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    pickle.dump(res, open("experiments/results/e7.pkl", "wb"))
