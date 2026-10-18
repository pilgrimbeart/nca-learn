"""Where am I, from averages only: every cell comes to know its place across the sheet (x and y, from -1 to 1), and
the sheet names its organs: two sensors, S1 and S2, either side of the middle of one edge (y = 1), between them the
taste organ T (a few cells), and two actuators, M1 and M2, either side of the middle of the opposite edge (y = -1). The two of a kind are found by the same
rule and differ only in which side of the middle they are (x < 0: 1); which side is which was settled by a coin toss.
Nothing here says what an organ is for. Neighbours see only means, of numbers from -1 to 1, with noise.

  1. The race. Every cell is excitable (the wave: excited for a moment, then resting a while). Each corner (3
     neighbours) is a pacemaker with its own random period; a corner reached by a wave while resting stands down for
     good. The faster corner's waves reach the slower ones before they fire, so in the end one corner is left: the
     organiser. It goes on beating. Each beat carries its number mod 3 (on two flags: +-, -+, ++), and a cell takes
     only the next beat after the last it took: a wave curling back on cells it has excited, or a stray piece of an
     older beat, is refused, so no wave can circle for ever (a spiral, which damage would otherwise start, and which
     would knock the organiser out).
  2. Handedness. Corners show 1 on hand while they stand, 0.75 once they have stood down; so an edge cell knows if
     it is next to a corner, and if that corner stands. The organiser's two edge neighbours (each other's neighbours
     too) each show a coin, +-0.5, and toss again while the other's is the same. The one with +0.5 is on the edge
     that will be y = -1.
  3. Edge labels. Each time the organiser beats, its two coin-tossed neighbours start a label pulse along their
     edges: yl -1 along one, xl -1 along the other. An edge cell takes the label an edge neighbour shows, shows it a
     moment, then rests (so pulses run one way). Next to a corner it shows it at half strength, which edge cells
     ignore and corners take: a label stops at the corner instead of leaking round it. A corner that holds -1 on one
     axis starts +1 on the other (at 0.75, taken by the edge cell beside it when it sees no full label): the far edges
     get +1. A cell holds a label once two pulses in a row agree, and forgets it after STALE of the organiser's beats
     with none: if the winner changes, the labels follow it.
  4. Coordinates. Cells holding a label hold x (or y) at it; every other cell takes its neighbours' mean, so x runs
     straight from -1 to 1 across the sheet, and y likewise. While a cell's place is still drifting (a short and a
     long average of it differ) it also carries on part of its last move (momentum): settling then takes about
     size updates instead of size^2.
  5. Naming. A cell on either labelled edge y = -1 or y = 1 shows mark +1 where -W < x < W (with a margin, so a mark
     doesn't flicker). A cell on such an edge outside the mark but next to it takes a place: on y = 1 a sensor, on
     y = -1 an actuator; 1 if x < 0, else 2. A marked cell on y = 1 takes the place T. A cell takes a place only once
     its x and y have stopped drifting, and a name once it has held the place for HOLD updates. A named sensor or
     actuator shows 0 on mark (between a mark and none), so no neighbour takes the same name, and keeps its name while
     its x stays within TOL of the place's. A T cell shows mark +1, and keeps its name while marked or beside a
     sensor. The mark's end can drift a cell after a sensor has taken its name; a cell on y = 1 between a named sensor
     and the mark then takes the place T too. So each sensor has a T cell beside it.
"""

import numpy as np
from numba import njit

EX, RF = 2.0, 10.0          # updates a cell is excited, then resting before it can be excited again
LE, LR = 3.0, 8.0           # updates an edge cell shows a label pulse, then rests from them
PMIN, PMAX = 30.0, 90.0     # a corner's period, random from birth (updates)
W = 0.125                   # the organs sit at x = -W and +W on their edges
TAU = 50.0                  # updates over which a cell averages its x and y for naming
SLOW = 150.0                # ... and over a longer time: when the two agree, x and y have stopped drifting
BETA = 0.9                  # momentum, while a cell's place is still drifting
STILL = 0.03                # (above the slow wobbles the noise keeps up: about half a column at 49)
TOL = 0.15                  # how far a named cell's x may stray before it gives the name up
SURE = 0.05                 # how far past a place's x a cell must be to change its mark
STALE = 6.0                 # organiser's beats without a label pulse before a cell forgets its label (one missed
                            # beat costs a cell three: it then refuses the next two as out of turn)
HOLD = 300                  # updates a cell must hold a name before it takes it
S1, S2, M1, M2, T = 1.0, 2.0, 3.0, 4.0, 5.0        # names: sensors and actuators, each 1 (x < 0) and 2; taste

VARS = ("w", "w2", "state", "par", "timer", "period", "standing", "hand", "coin", "xl", "yl", "lstate", "cx", "cy", "start", "px",
        "py", "missx", "missy", "lx", "ly", "x", "y", "xv", "yv", "xs", "ys", "xss", "yss", "mark", "place", "held",
        "name")
SHARED = ("w", "w2", "hand", "xl", "yl", "x", "y", "mark")
INPUTS = ()
BIRTH = {v: 0.0 for v in VARS}
BIRTH.update({"w": -1.0, "w2": -1.0, "period": PMIN, "standing": 1.0, "hand": -1.0, "coin": -0.5, "mark": -1.0})
BIRTH_NOISE = {"timer": PMAX, "period": PMAX - PMIN, "coin": 1.0}     # coin: -0.5 or +0.5 once rounded to its sign
(WV, WV2, STATE, PAR, TIMER, PERIOD, STANDING, HAND, COIN, XL, YL, LSTATE, CX, CY, START, PX, PY, MISSX, MISSY, LX, LY, X, Y,
 XV, YV, XS, YS, XSS, YSS, MARK, PLACE, HELD, NAME) = range(len(VARS))
M_W, M_W2, M_HAND, M_XL, M_YL, M_X, M_Y, M_MARK = range(8)


@njit
def update(me, mean, count, inp, out):
    corner, edge = count == 3, count < 8
    # 1. the race
    state, timer, period = np.round(me[STATE]), np.round(me[TIMER]), np.round(me[PERIOD])
    par = np.round(me[PAR])
    standing = corner and me[STANDING] > 0.5
    fire = False
    a = np.round(count * (mean[M_W] + 1.0) / 2.0)              # excited neighbours showing +1 on the first wave flag
    b = np.round(count * (mean[M_W2] + 1.0) / 2.0)             # ... and on the second
    phase = 0.0 if a > b else (1.0 if b > a else 2.0)           # the phase they show (+-, -+, ++)
    if state == 0.0 and a + b >= 1.0 and phase == (par + 1.0) % 3.0:
        fire, standing, par = True, False, phase                # the next beat (another's wave reached me first)
    if standing:
        timer -= 1.0
        if timer <= 0.0 and state == 0.0:
            fire, timer, par = True, period, (par + 1.0) % 3.0
    if fire:
        state = EX + RF
    elif state > 0.0:
        state -= 1.0
    out[STATE], out[TIMER], out[PERIOD], out[STANDING], out[PAR] = state, timer, period, 1.0 if standing else 0.0, par
    excited = state > RF
    out[WV] = 1.0 if excited and par != 1.0 else -1.0
    out[WV2] = 1.0 if excited and par != 0.0 else -1.0
    # 2. handedness: z is what my neighbours show on hand, above all of them showing -1
    z = count * mean[M_HAND] + count
    q = np.round(4.0 * z)                                       # a corner adds 8 (standing) or 7, a coin 2 or 6
    by_corner = edge and not corner and z > 1.625
    by_organiser = by_corner and q % 2 == 0
    coin = 0.5 if me[COIN] > 0.0 else -0.5
    other = 0.0                                                 # the other's coin, or 0 if it shows none
    if by_organiser:
        rest = z - 2.0
        other = 0.5 if rest > 1.0 else (-0.5 if rest > 0.25 else 0.0)
        if other == coin and np.random.random() < 0.5:
            coin = -coin                                        # the same: toss again
    out[COIN] = coin
    out[HAND] = (1.0 if standing else 0.75) if corner else (coin if by_organiser else -1.0)
    role = coin if by_organiser and other == -coin else 0.0    # +0.5: the y = -1 edge starts here; -0.5: x = -1
    # 3. edge labels: pulses along the edges, started at the organiser each time it fires
    lstate = np.round(me[LSTATE])
    cx, cy, start = np.round(me[CX]), np.round(me[CY]), np.round(me[START])
    took = False
    if lstate == 0.0 and edge and not standing:
        sx, sy = count * mean[M_XL], count * mean[M_YL]
        if role != 0.0:
            if fire:                                            # the organiser fired: start its two edges' labels
                cx, cy, start, took = (0.0, -1.0, 1.0, True) if role > 0.0 else (-1.0, 0.0, 1.0, True)
        elif corner:                                            # a corner takes half-strength labels too
            if abs(sx) > 0.375 or abs(sy) > 0.375:
                cx = np.sign(sx) if abs(sx) > 0.375 else 0.0
                cy = np.sign(sy) if abs(sy) > 0.375 else 0.0
                start, took = 0.0, True
        elif not by_organiser:
            if abs(sy) > 0.875:
                cx, cy, start, took = 0.0, np.sign(sy), 0.0, True
            elif abs(sx) > 0.875:
                cx, cy, start, took = np.sign(sx), 0.0, 0.0, True
            elif abs(sy) > 0.625:
                cx, cy, start, took = 0.0, np.sign(sy), 1.0, True       # from a corner: the start of an edge
            elif abs(sx) > 0.625:
                cx, cy, start, took = np.sign(sx), 0.0, 1.0, True
    if took:
        lstate = LE + LR
    elif lstate > 0.0:
        lstate -= 1.0
    out[LSTATE], out[CX], out[CY], out[START] = lstate, cx, cy, start
    lx, ly = np.round(me[LX]), np.round(me[LY])
    px, py = np.round(me[PX]), np.round(me[PY])
    missx, missy = np.round(me[MISSX]), np.round(me[MISSY])
    if fire:                                                    # an organiser's beat: one more since each label was renewed
        missx, missy = missx + 1.0, missy + 1.0
    if lstate == 1.0:                                           # the pulse has passed: two in a row agree?
        if corner:                                              # a corner keeps each axis apart
            if cx != 0.0:
                lx = cx if cx == px else lx
                px, missx = cx, 0.0
            if cy != 0.0:
                ly = cy if cy == py else ly
                py, missy = cy, 0.0
        else:
            if cx == px and cy == py:
                lx, ly = cx, cy
            px, py, missx, missy = cx, cy, 0.0, 0.0
    if missx > STALE:
        lx, px = 0.0, 0.0                                       # no pulse for several beats: forget the label
    if missy > STALE:
        ly, py = 0.0, 0.0
    out[PX], out[PY], out[MISSX], out[MISSY] = px, py, min(missx, STALE + 1.0), min(missy, STALE + 1.0)
    sx_, sy_ = 0.0, 0.0                                         # what a corner starts: +1 on its other axis
    if corner and not standing:
        if ly == -1.0 and lx != -1.0:
            sx_ = 1.0
        elif lx == -1.0 and ly != -1.0:
            sy_ = 1.0
    showing = lstate > LR
    if not (showing and edge):
        out[XL], out[YL] = 0.0, 0.0
    elif corner:                                                # a corner passing a pulse starts its own
        out[XL], out[YL] = (0.75 * sx_, 0.75 * sy_) if not standing else (0.0, 0.0)
    else:
        strength = 0.5 if by_corner and start == 0.0 else 1.0  # the end of an edge: only a corner takes it
        out[XL], out[YL] = strength * cx, strength * cy
    hx, hy = (sx_ if sx_ != 0.0 else lx), (sy_ if sy_ != 0.0 else ly)   # a corner also holds what it starts
    if standing:
        hx, hy = -1.0, -1.0
    if not edge:
        lx, ly, hx, hy = 0.0, 0.0, 0.0, 0.0
    out[LX], out[LY] = lx, ly
    # 4. coordinates
    drift = abs(me[XS] - me[XSS]) > STILL or abs(me[YS] - me[YSS]) > STILL
    beta = BETA if drift else 0.0                               # while drifting, carry on part of the last move
    x = hx if hx != 0.0 else min(max(mean[M_X] + beta * me[XV], -1.0), 1.0)
    y = hy if hy != 0.0 else min(max(mean[M_Y] + beta * me[YV], -1.0), 1.0)
    out[XV], out[YV] = x - me[X], y - me[Y]
    out[X], out[Y] = x, y
    xs, ys = me[XS] + (x - me[XS]) / TAU, me[YS] + (y - me[YS]) / TAU
    xss, yss = me[XSS] + (x - me[XSS]) / SLOW, me[YSS] + (y - me[YSS]) / SLOW
    out[XS], out[YS], out[XSS], out[YSS] = xs, ys, xss, yss
    still = abs(xs - xss) < STILL and abs(ys - yss) < STILL     # my place has stopped drifting
    # 5. naming
    lo, hi = edge and not corner and hy == -1.0, edge and not corner and hy == 1.0
    was = me[MARK] > 0.5                                        # hysteresis: a mark flips only when x is clearly past
    h = -SURE if was else SURE
    mark = (lo or hi) and -W + h < xs < W - h
    seen = np.round(count * (mean[M_MARK] + 1.0))              # units: 2 per mark, 1 per named cell
    marks, named_by = np.floor(seen / 2.0), seen % 2.0 == 1.0
    name = np.round(me[NAME])
    if name == T:
        if not (hi and (mark or named_by)):                     # taste: keep it while marked, or beside a sensor
            name = 0.0
        place, held = name, 0.0
    elif name != 0.0:                                           # named: keep it while still about right
        side = -W if name == S1 or name == M1 else W
        keep = (hi if name <= S2 else lo) and abs(xs - side) < TOL
        if not keep:
            name = 0.0
        place, held = name, 0.0
    else:
        place = 0.0
        if hi and not mark and marks >= 1.0 and named_by:
            place = T                                           # between a sensor and the mark: taste too
        elif (lo or hi) and not mark and marks >= 1.0:
            place = (S1 if hi else M1) + (0.0 if xs < 0.0 else 1.0)
        elif hi and mark:
            place = T
        if not still or (named_by and place != T):
            place = 0.0                                         # still drifting, or a neighbour has the name already
        held = min(np.round(me[HELD]) + 1.0, HOLD) if place == np.round(me[PLACE]) and place != 0.0 else 0.0
        if held >= HOLD:
            name = place
    out[PLACE], out[HELD], out[NAME] = place, held, name
    out[MARK] = 1.0 if name == T else (0.0 if name != 0.0 else (1.0 if mark else -1.0))
