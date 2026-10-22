"""The H series' runner (experiments/NOTEBOOK.md): any named rules for recruiting, in lives of any length, against the
knowing circuit (no recruitment) on the same lives; each result goes on the leaderboard (LEADERBOARD.md).

    python -m experiments.h_run LIVES SECONDS name [name ...]      (a name may be a fragment: every match runs)
"""

import functools
import pickle
import sys

import numpy as np

from brains.healing import HealingBrain
from brains.recruiting import RecruitingBrain
from experiments.common import board, choices, paired, run, summary

H = HealingBrain
RULES = {
    "guided bridge (recruiting circuit)": functools.partial(RecruitingBrain),
    "wsls": functools.partial(H),
    "wsls, listening full": functools.partial(H, listen="all"),
    "wsls, inhibit/gate only": functools.partial(H, sign="inh"),
    "wsls, listening full, inhibit/gate only": functools.partial(H, listen="all", sign="inh"),
    "reinforce": functools.partial(H, select="reinforce"),
    "reinforce, listening full": functools.partial(H, select="reinforce", listen="all"),
    "reinforce, listening full, inhibit/gate only": functools.partial(H, select="reinforce", listen="all", sign="inh"),
    "wsls, listening full, inhibit/gate only, early": functools.partial(H, listen="all", sign="inh", grow_at=0.15),
    "wsls, inhibit/gate only, early": functools.partial(H, sign="inh", grow_at=0.15),
    "wsls, inhibit/gate only, shadow": functools.partial(H, sign="inh", grow_at=0.15, shadow="flag"),
    "wsls, inhibit/gate only, shadow, commissioned": functools.partial(H, sign="inh", grow_at=0.15, shadow="latch"),
    "wsls, inhibit/gate only, inherit, shadow, commissioned": functools.partial(H, sign="inh", listen="inherit",
                                                                                grow_at=0.15, shadow="latch"),
    "wsls, neurons only, inherit, inhibit only, cascade": functools.partial(H, menu="neurons", listen="inherit",
                                                                            sign="inh", cascade=True),
    "wsls, inhibit/gate only, inherit": functools.partial(H, sign="inh", listen="inherit"),
    "wsls, inhibit/gate only, inherit, shadow": functools.partial(H, sign="inh", listen="inherit", grow_at=0.15,
                                                                  shadow="flag"),
    "wsls, neurons only, cascade": functools.partial(H, menu="neurons", cascade=True),
    "share: wsls, listening full, inhibit/gate only": functools.partial(H, listen="all", sign="inh", judge="share", tire=0.05),
    "share (step 0.15): wsls, listening full, inhibit/gate only": functools.partial(H, listen="all", sign="inh",
                                                                                   judge="share"),
    "share: wsls, listening full": functools.partial(H, listen="all", judge="share", tire=0.05),
    "share: wsls, inhibit/gate only, inherit": functools.partial(H, sign="inh", listen="inherit", judge="share", tire=0.05),
    "share: wsls": functools.partial(H, judge="share", tire=0.05),
    "inputs: no cascade (control)": functools.partial(H, menu="inputs", listen="all", sign="inh", judge="share",
                                                      tire=0.05),
    "inputs: cascade, listening full, inhibit/gate only": functools.partial(H, menu="inputs", listen="all", sign="inh",
                                                                            cascade=True, judge="share", tire=0.05),
    "inputs: cascade, inherit, inhibit/gate only": functools.partial(H, menu="inputs", listen="inherit", sign="inh",
                                                                     cascade=True, judge="share", tire=0.05),
    "inputs: cascade, learned listening, inhibit/gate only": functools.partial(H, menu="inputs", sign="inh",
                                                                               cascade=True, judge="share", tire=0.05),
    "inputs: cascade, listening full, both signs": functools.partial(H, menu="inputs", listen="all", cascade=True,
                                                                     judge="share", tire=0.05),
    "inputs: cascade, inherit, both signs": functools.partial(H, menu="inputs", listen="inherit", cascade=True,
                                                              judge="share", tire=0.05),
    "gated: share: wsls, listening full, inhibit/gate only": functools.partial(H, listen="all", sign="inh",
                                                                              judge="share", tire=0.05),
    "gated: inputs: cascade, listening full, inhibit/gate only": functools.partial(H, menu="inputs", listen="all",
                                                                                  sign="inh", cascade=True,
                                                                                  judge="share", tire=0.05),
    "gated: inputs: cascade, retire": functools.partial(H, menu="inputs", listen="all", sign="inh", cascade=True,
                                                        judge="share", tire=0.05, retire=True),
    "gated: inputs: cascade, starve": functools.partial(H, menu="inputs", listen="all", sign="inh", cascade=True,
                                                        judge="share", tire=0.05, starve=True),
    "gated: inputs: cascade, retire, starve": functools.partial(H, menu="inputs", listen="all", sign="inh",
                                                                cascade=True, judge="share", tire=0.05, retire=True,
                                                                starve=True),
    "gated: inputs: cascade, inherit, retire, starve": functools.partial(H, menu="inputs", listen="inherit",
                                                                         sign="inh", cascade=True, judge="share",
                                                                         tire=0.05, retire=True, starve=True),
    "gated: share, starve: wsls, listening full, inhibit/gate only": functools.partial(H, listen="all", sign="inh",
                                                                                      judge="share", tire=0.05,
                                                                                      starve=True),
    "root, 30k: inputs: cascade": functools.partial(H, menu="inputs", listen="all", sign="inh", cascade=True,
                                                    trigger="root", persist=300.0, judge="share", tire=0.05),
    "root, 30k: inputs: cascade, retire": functools.partial(H, menu="inputs", listen="all", sign="inh", cascade=True,
                                                            trigger="root", persist=300.0, judge="share", tire=0.05,
                                                            retire=True),
    "root, 30k: inputs: cascade, retire, starve 20k": functools.partial(H, menu="inputs", listen="all", sign="inh",
                                                                        cascade=True, trigger="root", persist=300.0,
                                                                        judge="share", tire=0.05, retire=True,
                                                                        starve=200.0),
    "root: inputs: cascade": functools.partial(H, menu="inputs", listen="all", sign="inh", cascade=True,
                                               trigger="root", judge="share", tire=0.05),
    "root: inputs: cascade, retire": functools.partial(H, menu="inputs", listen="all", sign="inh", cascade=True,
                                                       trigger="root", judge="share", tire=0.05, retire=True),
    "root: inputs: cascade, retire, starve 20k": functools.partial(H, menu="inputs", listen="all", sign="inh",
                                                                   cascade=True, trigger="root", judge="share",
                                                                   tire=0.05, retire=True, starve=200.0),
    "root: inputs: cascade, starve 20k": functools.partial(H, menu="inputs", listen="all", sign="inh", cascade=True,
                                                           trigger="root", judge="share", tire=0.05, starve=200.0),
    "root: inputs: cascade, inherit, retire, starve 20k": functools.partial(H, menu="inputs", listen="inherit",
                                                                            sign="inh", cascade=True, trigger="root",
                                                                            judge="share", tire=0.05, retire=True,
                                                                            starve=200.0),
    "share: wsls, neurons only, cascade": functools.partial(H, menu="neurons", cascade=True, judge="share", tire=0.05),
    "share: wsls, neurons only, inherit, inhibit only, cascade": functools.partial(H, menu="neurons", listen="inherit",
                                                                                   sign="inh", cascade=True,
                                                                                   judge="share", tire=0.05),
    "share: wsls, neurons only, inherit, cascade": functools.partial(H, menu="neurons", listen="inherit",
                                                                     cascade=True, judge="share", tire=0.05),
    "wsls, neurons only, listening full, cascade": functools.partial(H, menu="neurons", listen="all", cascade=True),
    "wsls, neurons only, listening full, inhibit only, cascade": functools.partial(H, menu="neurons", listen="all",
                                                                                   sign="inh", cascade=True),
}


def knowing(lives, seconds, first_seed=0):
    """The baseline, run once per life length and seed set, and kept."""
    import os
    path = f"experiments/results/knowing_{lives}_{seconds:g}s" + (f"_from{first_seed}" if first_seed else "") + ".pkl"
    if os.path.exists(path):
        return pickle.load(open(path, "rb"))
    make = functools.partial(H, grow=False)
    base = (run(make, lives, seconds, first_seed=first_seed), run(make, lives, seconds, all_food=True,
                                                                 first_seed=first_seed))
    pickle.dump(base, open(path, "wb"))
    return base


if __name__ == "__main__":
    args = sys.argv[1:]
    first_seed = int(args.pop(args.index("--seed") + 1)) if "--seed" in args else 0   # held-out lives: --seed 100
    args = [a for a in args if a != "--seed"]
    lives, seconds, wanted = int(args[0]), float(args[1]), args[2:]
    base = knowing(lives, seconds, first_seed)
    tag = f" (held out, seeds from {first_seed})" if first_seed else ""
    for name, make in RULES.items():
        if not any(w == name or (w.endswith("*") and name.startswith(w[:-1])) for w in wanted):
            continue
        p, f = run(make, lives, seconds, first_seed=first_seed), run(make, lives, seconds, all_food=True,
                                                                    first_seed=first_seed)
        d, lo, hi = paired(base[0], p)
        waves = {}
        for r in p:
            w = max([wv for _, wv, *_ in r.get("recruits", [])] or [0])
            waves[w] = waves.get(w, 0) + 1
        settle = [since for r in p for _, wv, what, _, sw, since in r.get("recruits", []) if wv == 1]
        switches = [sw for r in p for _, wv, what, _, sw, since in r.get("recruits", []) if wv == 1]
        print(summary(name + tag, p), flush=True)
        if settle:
            print(f"{'':35s}wave-1 recruits: median last switch at {np.median(settle):.1f} s, median switches"
                  f" {int(np.median(switches))}", flush=True)
        print(f"{'':35s}net vs knowing {d:+.2f} [{lo:+.2f}, {hi:+.2f}]; deepest wave {dict(sorted(waves.items()))};"
              f" choices {choices(p)}; all-food recruits {sum(len(r.get('recruits', [])) for r in f)}", flush=True)
        board(name + tag, seconds, p, f, base[0], base[1])
        pickle.dump((p, f), open(f"experiments/results/h_{name.replace(' ', '_').replace('/', '-')}_{seconds:g}s"
                                 + (f"_from{first_seed}" if first_seed else "") + ".pkl", "wb"))
