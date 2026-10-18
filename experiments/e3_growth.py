"""E3, growth (experiments/NOTEBOOK.md): does the full local mechanism grow the best oracle structure (E1's O1: one
bridge, on the poison sensor, on one of its motor synapses), and nothing in all-food lives? Paired with the knowing
brain (growth off) and the oracle O1, life for life.

    python -m experiments.e3_growth [LIVES]
"""

import functools
import pickle
import sys
from collections import Counter

import numpy as np

from brains.recruiting import RecruitingBrain
from experiments.common import E3, paired, run, summary
from experiments.e1_oracle import o1

KNOWING = functools.partial(RecruitingBrain, grow=False, hold="T")
RECRUITING = functools.partial(RecruitingBrain, **E3)


def growth(records):
    """Where and when bridges grew: the share of lives with exactly one bridge on the poison sensor, and the rest."""
    kinds = Counter()
    first = []
    for r in records:
        b = r["bridges"]
        on = Counter(w for _, w, _ in b)
        kinds[f"{on.get('poison', 0)} on poison's sensor, {on.get('food', 0)} on food's" if b else "none"] += 1
        if b:
            first.append(b[0][0])
    return dict(kinds), (int(np.median(first)) if first else None)


if __name__ == "__main__":
    lives = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    res = {}
    for name, make, setup in (("knowing (no growth)", KNOWING, None), ("oracle O1", KNOWING, o1),
                              ("recruiting", RECRUITING, None)):
        res[name] = (run(make, lives, setup=setup), run(make, lives, all_food=True, setup=setup))
        print(summary(name, res[name][0]), flush=True)
        print(summary("", res[name][1], all_food=True), flush=True)
    kinds, when = growth(res["recruiting"][0])
    print(f"\\nrecruiting, poison lives: bridges per life {kinds}; first bridge at median tick {when}")
    print(f"recruiting, all-food lives: bridges per life {growth(res['recruiting'][1])[0]}")
    for name in ("oracle O1", "recruiting"):
        d, lo, hi = paired(res["knowing (no growth)"][0], res[name][0])
        e, elo, ehi = paired(res["knowing (no growth)"][1], res[name][1])
        print(f"net food vs knowing: {name:12s} poison lives {d:+.2f} [{lo:+.2f}, {hi:+.2f}]; all-food {e:+.2f}"
              f" [{elo:+.2f}, {ehi:+.2f}]")
    d, lo, hi = paired(res["oracle O1"][0], res["recruiting"][0])
    print(f"net food, recruiting vs oracle O1, poison lives: {d:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    pickle.dump(res, open("experiments/results/e3.pkl", "wb"))
