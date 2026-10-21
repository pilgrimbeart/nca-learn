"""The sheet: the only code that knows there is a grid. A cell rule never sees it.

A rule is a module that declares its cell's numbers and one compiled function:

    VARS = ("a", "b", ...)          # every number a cell holds, in order (its layers)
    SHARED = ("a", ...)             # the ones its neighbours can read: they only ever get the MEAN of what each
                                    # neighbour shows: the number held, clipped to -1..1, plus noise of SHOW
    INPUTS = ("kick", ...)          # what the body can deliver to a cell
    OUTPUTS = ("fired", ...)        # (optional) counts the body may take away (reading them sets them to 0)
    BIRTH = {"a": 0.0, ...}         # every cell is born with these ...
    BIRTH_NOISE = {"b": 1.0}        # ... plus, for these, an independent random number up to this size (uniform)

    @njit(RULE, cache=True)             # (RULE from rules.interface: the compiler is told what update is)
    def update(me, mean, count, inp, out):
        # me: this cell's numbers; mean: its neighbours' mean of each shared number (in SHARED's order);
        # count: how many neighbours it has (3 at a corner, 5 on an edge, 8 inside); inp: what the body delivered
        # since it last updated; out: write its new numbers here (out starts as a copy of me).

Each tick, every cell, with chance UPDATE, updates (never all in lockstep); the others keep their numbers, and
what the body delivered to them waits for their next update. After an update every number it keeps gets a little
noise (NOISE). What a cell shows its neighbours is cruder: each shared number is clipped to -1..1 and gets noise of SHOW
(0.01), drawn afresh every tick. A neighbour moves a cell's mean by at most 2 / its count, so a shared number carries
little: a flag (+1 or -1) is read exactly, a smooth value shared by many neighbours (a gradient) closely, a value
squeezed small or spread over orders of magnitude not at all. The rule is given nothing else: not the grid, not its position, not the size,
not a clock, not its neighbours one by one.

A rule may build on another by extending its VARS and SHARED (its numbers keep their places) and calling its update.

The body touches the sheet only through cells(), give(), get() and take(): it finds cells by what they hold (a name they
gave themselves), delivers inputs to them, and reads their numbers. Watching may use view(); the experimenter may
damage() cells (replace them with new-born ones), as with the lizard.
"""

from __future__ import annotations

import numpy as np
from numba import njit, types

from rules.interface import RULE    # a rule's update, declared (so the sheet, taking one, can be cached)

UPDATE = 0.5        # the chance that a cell updates in a tick
NOISE = 1e-3        # noise added to every number a cell keeps, at every update
SHOW = 0.01         # noise on what a cell shows its neighbours (each shared number clipped to -1..1), every tick
_SHEET = types.float64[:, :, ::1]


@njit(cache=True)
def _seed(seed):
    np.random.seed(seed)


@njit(types.void(_SHEET, _SHEET, _SHEET, types.float64[:, ::1], _SHEET, types.int64[::1], types.FunctionType(RULE),
                  types.int64, types.float64, types.float64, types.float64), cache=True)
def _ticks(s, s2, mean, count, inp, shared, update, ticks, p, noise, show):
    n = s.shape[0]
    nv, ns, ni = s.shape[2], shared.shape[0], inp.shape[2]
    me, out, avg, got = np.empty(nv), np.empty(nv), np.empty(mean.shape[2]), np.empty(ni)   # the rule's own arrays:
    shown = np.empty((n, n, ns))                            # what each cell shows: a shared number, clipped, noisy
    for _ in range(ticks):                                  # (the rule never holds a view into the sheet)
        for y in range(n):
            for x in range(n):
                for k in range(ns):
                    shown[y, x, k] = min(max(s[y, x, shared[k]], -1.0), 1.0) + show * np.random.standard_normal()
        for y in range(n):                                  # each cell's neighbours' means of what they show
            for x in range(n):
                for k in range(ns):
                    acc = 0.0
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            yy, xx = y + dy, x + dx
                            if (dy or dx) and 0 <= yy < n and 0 <= xx < n:
                                acc += shown[yy, xx, k]
                    mean[y, x, k] = acc / count[y, x]
        for y in range(n):
            for x in range(n):
                s2[y, x, :] = s[y, x, :]
                if np.random.random() < p:                  # this cell updates now
                    me[:] = s[y, x]
                    out[:] = s[y, x]
                    avg[:] = mean[y, x]
                    got[:] = inp[y, x]
                    update(me, avg, count[y, x], got, out)
                    for v in range(nv):
                        s2[y, x, v] = out[v] + noise * np.random.standard_normal()
                    inp[y, x, :] = 0.0
        s[:, :, :] = s2


class Sheet:
    """n x n cells running one rule."""

    def __init__(self, rule, n: int, seed: int = 0, update: float = UPDATE, noise: float = NOISE, show: float = SHOW):
        self.rule, self.n, self.p, self.noise, self.show = rule, n, update, noise, show
        self.index = {name: i for i, name in enumerate(rule.VARS)}
        self.inputs = {name: i for i, name in enumerate(rule.INPUTS)}
        assert set(rule.SHARED) <= set(rule.VARS) and set(rule.BIRTH) == set(rule.VARS)
        rng = np.random.default_rng(seed)
        self._s = np.empty((n, n, len(rule.VARS)))
        for name, i in self.index.items():
            self._s[:, :, i] = rule.BIRTH[name]
            if name in rule.BIRTH_NOISE:
                self._s[:, :, i] += rule.BIRTH_NOISE[name] * rng.random((n, n))
        self._s2 = np.empty_like(self._s)
        self._mean = np.zeros((n, n, max(1, len(rule.SHARED))))
        self._inp = np.zeros((n, n, max(1, len(rule.INPUTS))))
        self._shared = np.array([self.index[name] for name in rule.SHARED], dtype=np.int64)
        edge = lambda i: 2 if i in (0, n - 1) else 3
        self._count = np.array([[edge(y) * edge(x) - 1 for x in range(n)] for y in range(n)], dtype=float)
        self.t = 0
        _seed(seed)

    def step(self, ticks: int = 1) -> None:
        _ticks(self._s, self._s2, self._mean, self._count, self._inp, self._shared, self.rule.update, ticks, self.p,
               self.noise, self.show)
        self.t += ticks

    # The body's only ways in and out.
    def cells(self, var: str, value: float) -> np.ndarray:
        """The cells holding this value in this number (to the nearest whole number): e.g. those named R."""
        return np.abs(self._s[:, :, self.index[var]] - value) < 0.5

    def give(self, where: np.ndarray, input_: str, amount: float = 1.0) -> None:
        """Deliver an input to these cells (it waits for each cell's next update)."""
        self._inp[where, self.inputs[input_]] += amount

    def get(self, where: np.ndarray, var: str) -> np.ndarray:
        """These cells' values of a number."""
        return self._s[where, self.index[var]]

    def take(self, where: np.ndarray, var: str) -> np.ndarray:
        """These cells' values of an output (a count the cell keeps up), which the body takes: they go back to 0."""
        assert var in getattr(self.rule, "OUTPUTS", ())
        i = self.index[var]
        out = np.round(self._s[where, i])
        self._s[where, i] = 0.0
        return out

    def damage(self, where: np.ndarray) -> None:
        """The experimenter, not the body: these cells die and are replaced by new-born ones (birth values and noise)."""
        rng = np.random.default_rng()
        for name, i in self.index.items():
            self._s[where, i] = self.rule.BIRTH[name]
            if name in self.rule.BIRTH_NOISE:
                self._s[where, i] += self.rule.BIRTH_NOISE[name] * rng.random(int(where.sum()))
        self._inp[where] = 0.0

    def view(self, var: str) -> np.ndarray:
        """Watching only: a copy of one number over the whole sheet."""
        return self._s[:, :, self.index[var]].copy()
