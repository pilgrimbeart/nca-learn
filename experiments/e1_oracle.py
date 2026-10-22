"""E1, oracle structures (experiments/NOTEBOOK.md): which structure, placed by hand at birth by an oracle that knows
the poison colour, would best let the taste neuron's knowledge act? The ceiling for each target of recruitment.

    python -m experiments.e1_oracle [LIVES]
"""

import functools
import pickle
import sys

from brains.circuit import INHIBIT
from brains.recruiting import HOLD, RecruitingBrain
from experiments.common import paired, run, summary
from units import C_TYP, I_TYP

KNOWING = functools.partial(RecruitingBrain, grow=False, hold="T")       # the recruiting circuit, growth switched off


def poison_sensor(life):            # in all-food lives, red stands in (T learns nothing there, so it never acts)
    return life.brain.sensors[life.sensor[life.poison or "red"]]


def food_sensor(life):
    return life.brain.sensors[life.sensor["blue" if (life.poison or "red") == "red" else "red"]]


def one_motor(life):
    return life.brain.motors[life.brain.seed % 2]               # either motor: symmetric; alternated over seeds


def o1(life):                       # a bridge on one of the poison sensor's synapses
    life.brain.insert_bridge(poison_sensor(life), one_motor(life))


def o2(life):                       # a bridge on one of the food sensor's synapses (the wrong place)
    life.brain.insert_bridge(food_sensor(life), one_motor(life))


def o3(life):                       # bridges on both of the poison sensor's synapses
    for m in life.brain.motors:
        life.brain.insert_bridge(poison_sensor(life), m)


def o4(life):                       # bridges on all four synapses
    for s in life.brain.sensors:
        for m in life.brain.motors:
            life.brain.insert_bridge(s, m)


def o5(life):                       # T's hold inhibits one motor directly: danger -> one thruster down
    b, c = life.brain, life.brain.circuit
    m = one_motor(life)
    hold = c.node("Hm", R=HOLD / (10 * C_TYP), C=10 * C_TYP, lo=0.0, hi=1.0)
    c.element(hold, b.T, 10 * I_TYP, 0.0, slope=5.0, sigmoid=True)
    c.element(m, hold, -INHIBIT, 0.5, slope=10.0, sigmoid=True)
    c.grow()


CONDITIONS = [("baseline", "baseline-circuit", None), ("none (knowing)", KNOWING, None),
              ("O1 bridge, poison sensor", KNOWING, o1), ("O2 bridge, food sensor", KNOWING, o2),
              ("O3 bridges, poison sensor both", KNOWING, o3), ("O4 bridges, all four", KNOWING, o4),
              ("O5 hold one motor", KNOWING, o5), ("designed circuit", "designed-circuit", None)]

if __name__ == "__main__":
    lives = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    results = {}
    for name, make, setup in CONDITIONS:
        poison = run(make, lives, setup=setup)
        food = run(make, lives, all_food=True, setup=setup)
        results[name] = (poison, food)
        print(summary(name, poison), flush=True)
        print(summary("", food, all_food=True), flush=True)
    base = results["none (knowing)"]
    print("\nnet food per 10 s, paired with the knowing circuit (same lives, same noise): mean difference [95%]")
    for name, (poison, food) in results.items():
        d, lo, hi = paired(base[0], poison)
        e, elo, ehi = paired(base[1], food)
        print(f"  {name:32s} poison lives {d:+.2f} [{lo:+.2f}, {hi:+.2f}]   all-food lives {e:+.2f}"
              f" [{elo:+.2f}, {ehi:+.2f}]")
    pickle.dump(results, open("experiments/results/e1.pkl", "wb"))
