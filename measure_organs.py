"""Measures the organs rule, life by life: when all four names are first taken, how many times a name moves or is
lost afterwards, how far each ends up from where it belongs (in cells: M1 and M2 W x half the width either side of
the middle of the organiser's y = -1 edge, S1 and S2 likewise on the y = 1 edge), and how near x and y are to straight
lines.

    python measure_organs.py [LIVES] [SIZE] [STEPS]   (steps of the sheet: sheet.py)
"""
import sys
import time

import numpy as np

import sheet
from rules import organs


def names(s):
    nm = np.round(s.view("name"))
    return {k: tuple(map(int, p[0])) for k in (organs.S1, organs.S2, organs.M1, organs.M2)
            for p in [np.argwhere(nm == k)] if len(p) == 1}


def truth(n, corner, at):
    """The true x and y (-1 to 1) of every cell, from where the organiser (corner) and M1 are."""
    (vr, vc), (ar, ac) = corner, at[organs.M1]
    r, c = np.mgrid[0:n, 0:n]
    along = (c if vc == 0 else n - 1 - c) if ar == vr else (r if vr == 0 else n - 1 - r)
    up = (r if vr == 0 else n - 1 - r) if ar == vr else (c if vc == 0 else n - 1 - c)
    return -1 + 2 * along / (n - 1), -1 + 2 * up / (n - 1)


def life(n, seed, steps):
    s = sheet.Sheet(organs, n, seed, update=0.9)
    first, moves, last = None, 0, None
    for t in range(0, steps, 10):
        s.step(10)
        at = names(s)
        if first is None and len(at) == 4:
            first = t + 10
        if first is not None and at != last and last is not None:
            moves += 1
        if first is not None:
            last = at
    if len(last or {}) < 4:
        return first, moves, None, None
    corner = tuple(map(int, np.argwhere(s.view("standing") > 0.5)[0]))
    tx, ty = truth(n, corner, last)
    half = (n - 1) / 2
    off = {k: (tx[last[k]] * half - want * organs.W * half, (ty[last[k]] - edge) * half)
           for k, want, edge in ((organs.S1, -1, 1), (organs.S2, 1, 1), (organs.M1, -1, -1), (organs.M2, 1, -1))}
    err = max(np.abs(s.view("x") - tx).max(), np.abs(s.view("y") - ty).max()) * half
    return first, moves, off, err


if __name__ == "__main__":
    lives = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 49
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else 4000
    letters = {organs.S1: "S1", organs.S2: "S2", organs.M1: "M1", organs.M2: "M2"}
    for seed in range(lives):
        t0 = time.time()
        first, moves, off, err = life(n, seed, steps)
        where = " ".join(f"{letters[k]} {dx:+.1f}" + (f"/{dy:+.1f}" if abs(dy) > 0.01 else "") for k, (dx, dy) in off.items()) if off else "-"
        e = f"{err:.2f}" if err is not None else "-"
        print(f"n {n} seed {seed}: all named from step {first}, then {moves} changes; cells off: {where}; "
              f"x, y within {e} columns  ({time.time() - t0:.1f}s)", flush=True)
