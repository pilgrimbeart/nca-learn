"""H1, rules for a generic recruit (experiments/NOTEBOOK.md, H series): the healing circuit (brains/healing.py), whose
recruits know nothing of the circuit, under different rules for listening, choosing and acting, against the knowing
circuit (no recruitment) and the guided recruiting circuit (the bridge, rung 1) on the same lives.

    python -m experiments.h1_rules [LIVES] [TICKS] [names...]
"""

import functools
import pickle
import sys

from brains.healing import HealingBrain
from brains.recruiting import RecruitingBrain
from experiments.common import board, choices, paired, run, summary

H = HealingBrain
CONDITIONS = {
    "knowing (no recruitment)": functools.partial(H, grow=False),
    "guided bridge (recruiting circuit)": functools.partial(RecruitingBrain),
    "wsls, menu with synapses": functools.partial(H),
    "wsls, menu of neurons only": functools.partial(H, menu="neurons"),
    "all options on, with synapses": functools.partial(H, select="all"),
    "one random option, with synapses": functools.partial(H, select="random"),
    "wsls, no listening": functools.partial(H, listen="none"),
    "wsls, listening fixed full": functools.partial(H, listen="all"),
    "wsls, inhibit/gate only": functools.partial(H, sign="inh"),
    "wsls, excite/gate only": functools.partial(H, sign="exc"),
    "wsls, learning from anticipated pain (wireheading?)": functools.partial(H, ouch="anticipated"),
}

if __name__ == "__main__":
    args = sys.argv[1:]
    lives = int(args.pop(0)) if args and args[0].isdigit() else 64
    ticks = int(args.pop(0)) if args and args[0].isdigit() else 30000
    names = [n for n in CONDITIONS if not args or any(a in n for a in args)]
    base = (run(CONDITIONS["knowing (no recruitment)"], lives, ticks),
            run(CONDITIONS["knowing (no recruitment)"], lives, ticks, all_food=True))
    res = {}
    for name in names:
        if name.startswith("knowing"):
            continue
        p, f = run(CONDITIONS[name], lives, ticks), run(CONDITIONS[name], lives, ticks, all_food=True)
        res[name] = (p, f)
        d, lo, hi = paired(base[0], p)
        print(summary(name, p), flush=True)
        print(f"{'':35s}net vs knowing {d:+.2f} [{lo:+.2f}, {hi:+.2f}]; choices {choices(p)};"
              f" all-food recruits {sum(len(r.get('recruits', [])) for r in f)}", flush=True)
        board(name, ticks, p, f, base[0], base[1])
    pickle.dump((base, res), open(f"experiments/results/h1_{ticks}.pkl", "wb"))
