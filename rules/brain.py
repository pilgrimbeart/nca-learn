"""The creature's brain, from averages only: organs, wiring, then choosing and learning. Built on wiring (its numbers
come first). Neighbours see only means.

  Choosing. When the body kicks R or B (its sensor saw that colour), that cell sends a pulse towards A (forward, at
  what it sees) with chance b, its balance; otherwise towards V (back off and turn). Born b = 0.9: a new-born
  creature is drawn to anything it sees. R and B also send towards V now and then by themselves: a tumble, so the
  creature searches.
  The trace. A kicked cell keeps how many updates since its kick, and starts a news wave: every cell is excitable on
  the news flag (excited for a moment, then resting a while, so a wave runs outwards and dies at the edges and where
  waves meet). A sensor that sees news around it once its own has gone by (a few updates after its kick: a wave
  never comes back) knows the other sensor was kicked since, and forgets its own kick, even if it is still resting
  from sending its own. So of R and B only the more recently kicked keeps a trace.
  A taste (+1 good, -1 bad, delivered to R and B) moves b by taste x exp(-trace / TRACE), towards 0 or 1: two
  factors (a recent input and the taste; which way the cell sent its pulse doesn't enter). A bad taste also makes R and B recoil, sending pulses towards V, for a while.
  Every number a cell keeps is a whole number, re-rounded at each update (b in twentieths).
"""

import numpy as np
from numba import njit

from rules import organs, wiring

FAR = 1e9          # "never": a kick long ago, or forgotten
STEPS = 20.0        # b is kept in twentieths
INNATE = 18.0       # born b = 0.9
TRACE = 30.0        # how long a trace lasts (updates)
NE, NR = 2.0, 10.0  # updates a cell is excited by news, then resting
DISGUST = 40.0      # how long a bad taste lasts (updates) ...
RECOIL = 0.2        # ... sending a pulse towards V with this chance at each update
TUMBLE = 0.01       # R and B each send towards V by themselves with this chance at each update: a tumble

VARS = wiring.VARS + ("balance", "kicked", "disgust", "news", "nstate")
SHARED = wiring.SHARED + ("news",)
INPUTS = ("see", "taste", "learn")          # learn: the experiment's control (with it off, tastes don't move b)
OUTPUTS = wiring.OUTPUTS
BIRTH = {**wiring.BIRTH, "balance": INNATE, "kicked": FAR, "disgust": 0.0, "news": -1.0, "nstate": 0.0}
BIRTH_NOISE = wiring.BIRTH_NOISE
BALANCE, KICKED, DISGUSTED, NEWS, NSTATE = range(len(wiring.VARS), len(wiring.VARS) + 5)
M_NEWS = len(wiring.SHARED)
SEE, TASTE, LEARN = range(3)


@njit
def update(me, mean, count, inp, out):
    organs.update(me, mean, count, inp, out)
    name = np.round(out[organs.NAME])
    source = name == wiring.SOURCES[0] or name == wiring.SOURCES[1]
    b = min(max(np.round(me[BALANCE]), 0.0), STEPS)
    kicked = min(np.round(me[KICKED]) + 1.0, FAR)
    nstate = np.round(me[NSTATE])
    news = mean[M_NEWS] > -1.0 + 1.0 / count                    # a neighbour is excited by news
    heard = nstate == 0.0 and news                              # a news wave reaches me
    if source and news and kicked > NE + 2.0:
        kicked = FAR                                            # news, and not mine (gone by now): forget my kick
    send_a = send_v = False
    if source and inp[SEE] > 0.5:
        kicked, heard = 0.0, False
        nstate = NE + NR                                    # my news
        if np.random.random() < b / STEPS:
            send_a = True
        else:
            send_v = True
    elif heard:
        nstate = NE + NR                                    # pass it on
    elif nstate > 0.0:
        nstate -= 1.0
    out[NSTATE], out[NEWS] = nstate, 1.0 if nstate > NR else -1.0
    disgust = max(np.round(me[DISGUSTED]) - 1.0, 0.0)
    taste = inp[TASTE]
    if source and taste != 0.0:
        if inp[LEARN] > 0.5:
            trace = np.exp(-kicked / TRACE)
            b = np.round(b + taste * trace * (b if taste < 0.0 else STEPS - b))
        if taste < 0.0:
            disgust = DISGUST
    if source and disgust > 0.0 and np.random.random() < RECOIL:
        send_v = True
    if source and np.random.random() < TUMBLE:
        send_v = True                                       # a tumble
    out[BALANCE], out[KICKED], out[DISGUSTED] = b, kicked, disgust
    wiring.stage(me, mean, count, out, 0, send_a)
    wiring.stage(me, mean, count, out, 1, send_v)
