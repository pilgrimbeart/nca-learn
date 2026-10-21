"""What a cell can read from its neighbours' means, and the pieces every stage uses. Not a rule: a library.

  Every shared number is clipped to -1..1 and shown with noise of 0.01. A neighbour moves the mean by at most
  2 / its count, so the sum over neighbours (count x mean) is what a cell reads: noise about 0.03 on it. Measured
  above -1 ("units": a neighbour showing -1 adds 0, one showing +1 adds 2), a flag's sum counts the neighbours
  showing +1, and a few well-spaced levels can be told apart too.

  A field: distance from some source cells, in steps, mod K = 5. A cell shows its residue on K flags (+1 on its
  residue's, -1 on the others; all -1 while it has none). In a settled field a cell's neighbours are one step
  nearer, level or one step farther: three residues of the five in a row, so the lowest is the one after the gap,
  and a cell is one more than that. A source is 0. A cell's value only ever falls: if one more than its lowest
  neighbour would be higher (or there is none), it lets go and rests REST updates before taking a value again, so a
  field whose source has gone fades instead of counting up for ever. A cell with no value takes one only after
  ATTACH reads in a row agree, and changes one after two: a misread changes nothing.

  A path along a field: a path cell shows its residue as a pattern on three flags (CODES: any three residues in a
  row are independent), at a strength that says whether it is a tip or carries a pulse. From the three sums
  a cell works out, for its neighbours one step nearer, level and one step farther, how many path cells there
  are, and whether one is a tip or carries a pulse.
"""

import numpy as np
from numba import njit

NONE = -1.0         # no residue: not reached
K = 5               # residues: distances are kept mod K (4 is not enough: one wrong cell can lock in)
ATTACH = 3.0        # reads in a row before a cell with no residue takes one
REST = 6.0          # updates a cell that let go waits before taking a residue again


@njit(cache=True)
def ups(mean, count):
    """How many neighbours show +1, from the mean of a flag."""
    return min(max(np.round(count * (mean + 1.0) / 2.0), 0.0), count)


@njit(cache=True)
def residues(mean, m, count):
    """Which residues the neighbours show, from the means of a field's K flags starting at m."""
    seen = np.zeros(K, dtype=np.bool_)
    for k in range(K):
        seen[k] = ups(mean[m + k], count) >= 1.0
    return seen


@njit(cache=True)
def lowest(seen):
    """The lowest residue the neighbours show (the one after the gap), or NONE if none, or -2 if it doesn't fit."""
    n = 0
    for k in range(K):
        n += seen[k]
    if n == 0:
        return NONE
    if n == K:
        return -2.0
    low = -2.0
    for k in range(K):
        if seen[k] and not seen[(k + K - 1) % K]:
            if low != -2.0:
                return -2.0                             # two runs: a gap on both sides
            low = float(k)
    return low


@njit(cache=True)
def field(me, mean, count, out, v, m, source):
    """One field. Kept numbers at v: residue, the value worked out last time, how many times in a row, rest. Shared
    flags: their means at m, their kept copies at v + 4 .. v + 3 + K (in out)."""
    r, pend, times, rest = np.round(me[v]), np.round(me[v + 1]), np.round(me[v + 2]), np.round(me[v + 3])
    if source:
        want = 0.0
    else:
        low = lowest(residues(mean, m, count))
        want = NONE if low < 0.0 else (low + 1.0) % K
    times = min(times + 1.0, ATTACH) if want == pend else 1.0
    pend = want
    if source:
        r, rest = 0.0, 0.0
    elif r == NONE:
        rest = max(rest - 1.0, 0.0)
        if rest == 0.0 and want != NONE and times >= ATTACH:
            r = want                                    # reached
    else:
        step = NONE if want == NONE else (want - r) % K
        if step == 0.0:
            pass
        elif step >= K - 2.0:
            if times >= 2.0:
                r = want                                # nearer than I thought
        elif times >= 2.0:
            r, rest = NONE, REST                        # would rise, or nothing below: let go, and rest
    out[v], out[v + 1], out[v + 2], out[v + 3] = r, pend, times, rest
    for k in range(K):
        out[v + 4 + k] = 1.0 if r == k else -1.0
    return r


CODES = np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 1.0], [1.0, 1.0, 1.0]])   # (the
#   choice that adds least noise when the sums are untangled: at most 1.41 times one sum's)
PATH, PULSE, TIP = 2.0, 0.4, 1.2   # what a path cell adds to each of its pattern's sums (units): with at most
                                    # two path cells in a class, every mix sums at least 0.4 apart


@njit(cache=True)
def show_path(r, kind, out, v):
    """A path cell at residue r shows its pattern at the strength for its kind (PATH, PULSE or TIP); 0: not path."""
    for j in range(3):
        out[v + j] = -1.0 + kind * CODES[int(r), j] if kind > 0.0 and r >= 0.0 else -1.0


def _inverses():
    """For each residue r: the matrix that turns the three path flags' sums into nearer, level and farther."""
    inv = np.empty((K, 3, 3))
    for r in range(K):
        inv[r] = np.linalg.inv(np.array([CODES[(r - 1 + i) % K] for i in range(3)]).T)
    return inv


INVERSES = _inverses()


@njit(cache=True)
def path_near(mean, m, count, r):
    """What path cells my neighbours one step nearer, level and one step farther show, in units (sums of PATH, PULSE
    and TIP), from the sums of the three path flags at m. r: my residue."""
    inv, out = INVERSES[int(r)], np.zeros(3)
    for j in range(3):
        u = count * mean[m + j] + count
        for i in range(3):
            out[i] += inv[i, j] * u                         # by hand: numba's @ needs scipy
    return out


@njit(cache=True)
def kinds(u):
    """(tips, pulses, paths) whose strengths sum to u: at most two cells, at most one of them a tip."""
    best, bt, bq, bp = 1e9, 0.0, 0.0, 0.0
    for tt in range(2):
        for qq in range(3 - tt):
            for pp in range(3 - tt - qq):
                e = abs(tt * TIP + qq * PULSE + pp * PATH - u)
                if e < best:
                    best, bt, bq, bp = e, float(tt), float(qq), float(pp)
    return bt, bq, bp
