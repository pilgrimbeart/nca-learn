"""Wiring, from averages only: once A and V have named themselves, each sends out a distance field; paths grow from R
and B down each field to its sink (channel 0 to A, channel 1 to V), and pulses run down them. Built on organs (its
numbers come first). Neighbours see only means, of numbers from -1 to 1, with noise.

  Distance. A sink is the source of a field (see.py): distance in steps, mod 5. Nothing in the rule says where the
  sinks are: the field starts wherever a cell named itself A or V, and fades if it goes.
  Path cells show their residue as a pattern on three flags, at a strength that says if they are a tip or carry a
  pulse: so each cell knows what path cells are one step nearer, level and one step farther (see.py).
  Growth. R and B are on the path once their distance has held still for STILL updates. A path cell with no path
  cell one step nearer is a tip. The cells one step nearer than a tip (they see a tip one step farther) are
  candidates: each raises a hand (a small step on the
  offer flag) or not, at random, now and then; one with another path cell above it as well only rarely (joining
  would give that path a second way on, splitting its pulses), so it is chosen only if no other cell offers. The tip shows "go" while it sees exactly one hand (twice
  in a row to start, LEASE updates at most); a candidate whose hand is up and has seen "go" three reads in a row
  joins. So a path grows one cell at a time, downhill, and a tip
  can't take two (that would split its pulses). A path cell with no path cell one step farther (it lost its way back
  to a source) leaves; so do cut-off paths, and their sources grow new ones.
  Pulses. A path cell takes a pulse when a path cell one step farther shows one, carries it ON updates, then rests
  REST more: pulses run only towards the sink. A sink counts the pulses it takes (an output: the body fires that
  thruster).
"""

import numpy as np
from numba import njit

from rules import organs, see

STILL = 20          # updates a source's distance must hold before it starts a path
LEASE = 6           # updates a tip's "go" lasts at most
GO_READS = 3        # reads of "go" in a row before a candidate joins
GO, HAND = 2.0, 0.2  # what a tip saying go, and a raised hand, add to the offer flag's sum (units)
REDRAW = 0.2        # chance per update that a candidate not yet told "go" redraws its hand
SHY = 0.02          # chance its hand is up after a redraw, if it also has another path cell above it
ON, REST = 6, 7     # updates a pulse is carried, then rested

FIELD = ("r", "pend", "times", "rest") + tuple(f"f{k}" for k in range(see.K))     # see.field's layout
CH = FIELD + ("p0", "p1", "p2", "offer", "on", "timer", "hand", "lease", "ones", "gos", "held", "gone", "fired")
VARS = organs.VARS + tuple(f"{v}_{c}" for c in "av" for v in CH)
SHARED = organs.SHARED + tuple(f"{v}_{c}" for c in "av" for v in tuple(f"f{k}" for k in range(see.K)) +
                               ("p0", "p1", "p2", "offer"))
INPUTS = ("send_a", "send_v")
OUTPUTS = ("fired_a", "fired_v")
BIRTH = {**organs.BIRTH, **{f"{v}_{c}": (-1.0 if v in FIELD[:2] + FIELD[4:] + ("p0", "p1", "p2", "offer") else 0.0)
                            for c in "av" for v in CH}}
BIRTH_NOISE = organs.BIRTH_NOISE
BASE, M_BASE = len(organs.VARS), len(organs.SHARED)
NV, NS = len(CH), see.K + 4                             # numbers per channel, shared numbers per channel
P0 = len(FIELD)                                         # the three path flags, then:
OFFER, ONV, TIMER, HANDV, LEASEV, ONES, GOS, HELD, GONE, FIRED = range(P0 + 3, NV)
SOURCES, SINKS = (organs.R, organs.B), (organs.A, organs.V)


@njit
def stage(me, mean, count, out, ch, send):
    """One channel: whether I am on the path (or a tip), my pulse. send: start a pulse, if I am a source."""
    v, m = BASE + NV * ch, M_BASE + NS * ch
    name = np.round(out[organs.NAME])
    source, sink = name == SOURCES[0] or name == SOURCES[1], name == SINKS[ch]
    d = see.field(me, mean, count, out, v, m, sink)
    known = d >= 0.0
    held = min(np.round(me[v + HELD]) + 1.0, STILL) if known and d == np.round(me[v]) else 0.0
    out[v + HELD] = held
    td = qd = pd = tu = qu = pu = 0.0
    if known:
        u = see.path_near(mean, m + see.K, count, d)
        td, qd, pd = see.kinds(u[0])                            # one step nearer
        tu, qu, pu = see.kinds(u[2])                            # one step farther
    nearer, farther = td + qd + pd > 0.0, tu + qu + pu > 0.0
    offers = count * mean[m + see.K + 3] + count                # units: GO per tip saying go, HAND per raised hand
    go = offers > GO - HAND / 2.0
    hands = np.round((offers - (GO if go else 0.0)) / HAND)
    on, gone = me[v + ONV] > 0.5, np.round(me[v + GONE])
    hand, gos = me[v + HANDV] > 0.5, np.round(me[v + GOS])
    candidate = False
    if sink:
        on = known
    elif source:
        on = known and (on or held >= STILL)
    elif on:
        gone = gone + 1.0 if not farther else 0.0
        on = known and gone < 2.0                               # no way back to a source: leave
    elif known and tu > 0.0:
        candidate = True                                        # below a tip
        gos = gos + 1.0 if go and hand else 0.0
        if gos >= GO_READS:
            on = True                                           # chosen: join
        elif not go and np.random.random() < REDRAW:
            hand = np.random.random() < (0.5 if qu + pu == 0.0 else SHY)    # above me another path: offer rarely
    if not candidate or on:
        hand, gos = False, 0.0
    out[v + ONV], out[v + GONE], out[v + HANDV], out[v + GOS] = 1.0 if on else 0.0, gone, 1.0 if hand else 0.0, gos
    tip = on and not sink and not nearer
    ones, lease = np.round(me[v + ONES]), max(np.round(me[v + LEASEV]) - 1.0, 0.0)
    if tip:
        ones = ones + 1.0 if hands == 1.0 else 0.0
        if hands != 1.0:
            lease = 0.0
        elif ones == 2.0:
            lease = float(LEASE)                                # exactly one hand, twice in a row: go
    else:
        ones, lease = 0.0, 0.0
    out[v + ONES], out[v + LEASEV] = ones, lease
    out[v + OFFER] = -1.0 + GO if lease > 0.0 else (-1.0 + HAND if hand else -1.0)
    timer = max(np.round(me[v + TIMER]) - 1.0, 0.0)
    fired = np.round(me[v + FIRED])
    if on and timer == 0.0 and ((source and send) or qu > 0.0):
        timer = ON + REST
        if sink:
            fired += 1.0
    out[v + TIMER], out[v + FIRED] = timer, fired
    kind = 0.0
    if on:
        kind = see.PULSE if timer > REST else (see.TIP if tip else see.PATH)
    see.show_path(d, kind, out, v + P0)


@njit
def update(me, mean, count, inp, out):
    organs.update(me, mean, count, inp, out)
    stage(me, mean, count, out, 0, inp[0] > 0.5)
    stage(me, mean, count, out, 1, inp[1] > 0.5)
