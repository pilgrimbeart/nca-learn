"""The creature's brain, from averages only: organs, wiring, then choosing and learning. Built on wiring (its numbers
come first). Neighbours see only means.

  Both sensors run the same code, and both channels are treated alike: nothing here says what a sensor senses or what
  an actuator does. Swapping the two sensors, or the two actuators, changes nothing a cell does.
  Firing. A sensor fires when the body stimulates it. Each time, it sends a pulse down both channels with chance p,
  otherwise down one: always the same one, its side, chosen by a coin toss when it took its name. Born p = 1/2. It also
  fires now and then by itself (SPONTANEOUS), the same way, so a creature that sees nothing still moves.
  Learning. A reward (+1 or -1) moves p RATE of the way towards 1 or 0: two factors, the sensor's own input and the
  reward. So a sensor learns how hard to drive at what it senses: both channels, or one.
  Every number a cell keeps is a whole number, re-rounded at each update (p in twentieths).
"""

import numpy as np
from numba import njit

from rules import organs, wiring

STEPS = 20.0        # p is kept in twentieths
RATE = 0.5          # how far a reward moves p towards 1 (good) or 0 (bad)
SPONTANEOUS = 0.01  # a sensor fires by itself with this chance at each update

VARS = wiring.VARS + ("p", "side")
SHARED = wiring.SHARED
INPUTS = ("stimulus", "reward")
OUTPUTS = wiring.OUTPUTS
BIRTH = {**wiring.BIRTH, "p": STEPS / 2, "side": 0.0}
BIRTH_NOISE = wiring.BIRTH_NOISE
P, SIDE = range(len(wiring.VARS), len(wiring.VARS) + 2)
STIMULUS, REWARD = range(2)


@njit
def update(me, mean, count, inp, out):
    organs.update(me, mean, count, inp, out)
    name = np.round(out[organs.NAME])
    sensor = name == wiring.SOURCES[0] or name == wiring.SOURCES[1]
    p = min(max(np.round(me[P]), 0.0), STEPS)
    side = np.round(me[SIDE])
    if not sensor:
        side = 0.0
    elif side != 1.0 and side != 2.0:
        side = 1.0 if np.random.random() < 0.5 else 2.0         # a new sensor tosses for its side
    send = np.zeros(2, dtype=np.bool_)
    if sensor and (inp[STIMULUS] > 0.5 or np.random.random() < SPONTANEOUS):
        if np.random.random() < p / STEPS:
            send[0], send[1] = True, True                       # both
        else:
            send[int(side) - 1] = True                          # one: my side
    reward = inp[REWARD]
    if sensor and reward != 0.0:
        p = np.round(p + RATE * reward * (STEPS - p if reward > 0.0 else p))
    out[P], out[SIDE] = p, side
    wiring.stage(me, mean, count, out, 0, send[0])
    wiring.stage(me, mean, count, out, 1, send[1])
