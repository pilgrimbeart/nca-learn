"""The creature's brain, from averages only: organs, wiring, then choosing and learning. Built on wiring (its numbers
come first). Neighbours see only means.

  Both sensors run the same code, and both channels are treated alike: nothing here says what a sensor senses or what
  an actuator does. Swapping the two sensors, or the two actuators, changes nothing a cell does.
  Firing. A sensor fires when the body stimulates it. Each time, it sends a pulse down both channels with chance p,
  otherwise down one: always the same one, its side, chosen by a coin toss when it took its name. Born p = 1/2. It also
  fires now and then by itself (SPONTANEOUS), the same way, so a creature that sees nothing still moves.
  Taste. The body gives taste (+1 good, -1 bad) to the cells named T; each shows its sign on the taste flag for
  SHOW_TASTE updates. Taste says nothing about which sensor it is for.
  Learning: three factors. A sensor counts the updates since it was last stimulated. When it sees taste begin beside it
  (a T cell is always next to it), and it was stimulated within the last ELIGIBLE updates, p moves RATE of the way
  towards 1 (good) or 0 (bad): the sensor's own recent input, and the taste. So a sensor learns how hard to drive at
  what it senses: both channels, or one.
  Pings: only the sensor stimulated last should learn. A stimulated sensor shows a ping; a T cell that sees one shows
  it in turn, then rests, so a wave runs along the T cells to the other sensor, which forgets its own stimulus. A cell
  that has just pinged rests too, so it ignores its own echo.
  Every number a cell keeps is a whole number, re-rounded at each update (p in twentieths).
"""

import numpy as np
from numba import njit

from rules.interface import RULE

from rules import organs, wiring

STEPS = 20.0        # p is kept in twentieths
RATE = 0.5          # how far a taste moves p towards 1 (good) or 0 (bad)
SPONTANEOUS = 0.01  # a sensor fires by itself with this chance at each update
SHOW_TASTE = 3.0    # updates a T cell shows a taste
ELIGIBLE = 15.0     # a sensor learns from a taste only if it was stimulated within this many updates before
SHOW_PING = 2.0     # updates a cell shows a ping ...
REST_PING = 4.0     # ... then this many it neither relays one nor heeds one (so a wave runs one way, with no echo)

VARS = wiring.VARS + ("p", "side", "since", "tasting", "tshow", "taste", "pingt", "ping")
SHARED = wiring.SHARED + ("taste", "ping")
INPUTS = ("stimulus", "taste")
OUTPUTS = wiring.OUTPUTS
BIRTH = {**wiring.BIRTH, "p": STEPS / 2, "side": 0.0, "since": 99.0, "tasting": 0.0, "tshow": 0.0,
         "taste": 0.0, "pingt": 0.0, "ping": 0.0}
BIRTH_NOISE = wiring.BIRTH_NOISE
P, SIDE, SINCE, TASTING, TSHOW, TASTEV, PINGT, PINGV = range(len(wiring.VARS), len(wiring.VARS) + 8)
M_TASTE, M_PING = len(wiring.SHARED), len(wiring.SHARED) + 1
STIMULUS, TASTE = range(2)


@njit(RULE, cache=True)
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
    stimulated = inp[STIMULUS] > 0.5
    if sensor and (stimulated or np.random.random() < SPONTANEOUS):
        if np.random.random() < p / STEPS:
            send[0], send[1] = True, True                       # both
        else:
            send[int(side) - 1] = True                          # one: my side
    # taste: a T cell shows what it was given for a while
    tshow = np.round(me[TSHOW])
    tshow = tshow - np.sign(tshow)
    if name == organs.T and inp[TASTE] != 0.0:
        tshow = np.sign(inp[TASTE]) * SHOW_TASTE
    if name != organs.T:
        tshow = 0.0
    out[TSHOW], out[TASTEV] = tshow, np.sign(tshow)
    # pings: a stimulated sensor shows one; a T cell that sees one shows it in turn, so it runs along the T cells to
    # the other sensor, which forgets its stimulus (only the one stimulated last learns from a taste). Afterwards a
    # cell rests, so the wave runs one way and its source ignores the echo.
    since = min(np.round(me[SINCE]) + 1.0, 99.0)
    pingt = max(np.round(me[PINGT]) - 1.0, 0.0)
    pinged = count * mean[M_PING] > 0.5 and np.round(me[PINGT]) == 0.0
    if sensor and pinged:
        since = 99.0
    if (name == organs.T and pinged) or (sensor and stimulated):
        pingt = SHOW_PING + REST_PING
    if not (sensor or name == organs.T):
        pingt = 0.0
    if sensor and stimulated:
        since = 0.0
    out[PINGT], out[PINGV] = pingt, 1.0 if pingt > REST_PING else 0.0
    # learning: taste beside me, and I was stimulated lately
    seen = count * mean[M_TASTE]                                # +1 for each neighbour showing good, -1 bad
    tasting = abs(seen) > 0.5
    if sensor and tasting and me[TASTING] < 0.5 and since <= ELIGIBLE:
        good = seen > 0.0
        p = np.round(p + RATE * ((STEPS - p) if good else -p))
    out[P], out[SIDE], out[SINCE], out[TASTING] = p, side, since, 1.0 if tasting else 0.0
    wiring.stage(me, mean, count, out, 0, send[0])
    wiring.stage(me, mean, count, out, 1, send[1])
