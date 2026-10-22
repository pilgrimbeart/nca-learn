"""The world and the creature's body: blocks of two colours on a torus, the eyes, the two thrusters and the mouth.
Nothing here knows about brains.

The body: an equilateral triangle, point forward; the point is its mouth. Both thrusters, at the tail's two corners,
push it forward; one alone also turns it, away from its own side, so the creature veers; both at once drive it
straight ahead. Its eyes at the point look along parallel rays across the corridor its mouth will sweep, up to RANGE;
each ray stops at the first block it meets, so a near block hides what is behind it. A block counts less the farther
off it is, and each eye sees only its own colour. A block the point moves into is eaten, and reappears elsewhere.
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit

from units import MILLI, TICK

BODY = 4 * MILLI    # m: the triangle's side (an insect's size, matching a 10 ms tick: units.py)
WORLD = 60 * MILLI  # m: the world's side (a torus)
BLOCKS = 18         # blocks of each colour
EAT = 1 * MILLI     # m: a block this near the point (the mouth) is eaten; the eyes' corridor is twice this wide
SENSE = 50.0        # per s: the stimuli to an eye that sees its colour at full strength
REACH = 5 * MILLI   # m: a block this far off counts half as much as one at the eyes
RANGE = 15 * MILLI  # m: how far the eyes see
RAYS = 25           # the eyes' rays, side by side across the corridor ahead: each stops at the first block it meets
BLOCK = 1 * MILLI   # m: a block's radius (what it hides behind it)
PUSH = 20 * MILLI   # m/s: a thruster firing adds this much forward speed ...
TURN = 16.0         # rad/s: ... and this much turning speed, away from its side: both at once go straight
DRAG = 50.0         # per s: speed and turning fade at this rate
COLOURS = ("red", "blue")
THRUSTERS = ("left", "right")                           # at the tail's two corners, both pushing forward
ACROSS = -EAT + (np.arange(RAYS) + 0.5) * 2 * EAT / RAYS   # each ray's offset across the corridor
SHARE = (2 * EAT / RAYS) / (2 * BLOCK)                  # one ray's share of a block's width


@njit(cache=True)
def _wrap(d):
    return (d + WORLD / 2) % WORLD - WORLD / 2


@njit(cache=True)
def _look(xy, kind, h, f):
    """How far each ray goes (to the first block it meets, or RANGE), and that block's kind (or -1)."""
    far, hit_kind = np.full(RAYS, RANGE), np.full(RAYS, -1)
    for b in range(xy.shape[0]):
        dx, dy = _wrap(xy[b, 0] - h[0]), _wrap(xy[b, 1] - h[1])
        ahead, off = dx * f[0] + dy * f[1], dx * f[1] + dy * -f[0]
        if ahead <= -BLOCK or ahead - BLOCK >= RANGE or abs(off) >= EAT + BLOCK:
            continue
        for k in range(RAYS):
            gap = BLOCK ** 2 - (ACROSS[k] - off) * (ACROSS[k] - off)
            if gap > 0:
                hit = max(0.0, ahead - np.sqrt(gap))
                if hit < far[k]:
                    far[k], hit_kind[k] = hit, kind[b]
    return far, hit_kind


@njit(cache=True)
def _sees(far, hit_kind, kinds):
    seen = np.zeros(kinds)
    for k in range(RAYS):
        if hit_kind[k] >= 0:
            seen[hit_kind[k]] += SHARE / (1 + (far[k] / REACH) * (far[k] / REACH))
    return np.minimum(seen, 1.0)


@njit(cache=True)
def _touching(xy, h0, h1):
    """The blocks within EAT of the path the point moved along in a tick, from h0 to h1 (a straight line: it turns
    little in a tick), in order. Checked along the path, not only where it ends, so that a fast creature can't jump
    over a block (the user's decision, 2026-10-22)."""
    sx, sy = _wrap(h1[0] - h0[0]), _wrap(h1[1] - h0[1])
    ss = sx * sx + sy * sy
    out = []
    for b in range(xy.shape[0]):
        dx, dy = _wrap(xy[b, 0] - h0[0]), _wrap(xy[b, 1] - h0[1])
        u = min(max((dx * sx + dy * sy) / ss, 0.0), 1.0) if ss > 0.0 else 0.0
        ex, ey = dx - u * sx, dy - u * sy
        if np.sqrt(ex * ex + ey * ey) < EAT:
            out.append(b)
    return out


class Body:
    """Where the creature is and how it moves; the world's blocks (xy, and kind: an index into COLOURS)."""

    def __init__(self, rng):
        self.rng = rng
        self.pos = np.array([WORLD / 2, WORLD / 2])
        self.heading = rng.uniform(0, 2 * math.pi)
        self.speed, self.spin = np.zeros(2), 0.0
        self.kind = np.repeat(np.arange(len(COLOURS)), BLOCKS)
        self.xy = np.array([self.somewhere() for _ in self.kind])

    def somewhere(self):
        while True:
            p = self.rng.uniform(0, WORLD, 2)
            if np.linalg.norm(self.wrap(p - self.pos)) > 3 * EAT + BODY:
                return p

    @staticmethod
    def wrap(d):
        return (d + WORLD / 2) % WORLD - WORLD / 2

    def forward(self):
        return np.array([math.cos(self.heading), math.sin(self.heading)])

    def head(self):
        """The point: the mouth."""
        return self.pos + self.forward() * BODY / math.sqrt(3)

    def corners(self) -> list:
        """The body's outline, for drawing: the point, then the tail's left and right corners (the thrusters)."""
        f = self.forward()
        r = np.array([f[1], -f[0]])
        back = self.pos - f * BODY / (2 * math.sqrt(3))
        return [self.head(), back - r * BODY / 2, back + r * BODY / 2]

    def look(self) -> tuple:
        """The eyes' rays, parallel, across the corridor its mouth will sweep: for each, its offset across, how far it
        goes (to the first block it meets, or RANGE), and that block's kind (or -1)."""
        far, kind = _look(self.xy, self.kind, self.head(), self.forward())
        return ACROSS, far, kind

    def sees(self) -> dict:
        """How strongly each colour is seen, at most 1: a block wholly in view counts 1 / (1 + (distance / REACH)^2),
        less if part of it is hidden or out of the corridor."""
        _, far, kind = self.look()
        return dict(zip(COLOURS, _sees(far, kind, len(COLOURS))))

    def fire(self, thruster: str) -> None:
        self.speed += PUSH * self.forward()
        self.spin += TURN if thruster == "right" else -TURN    # the left one turns it right, and the right one left

    def move(self) -> list:
        """Moves on a tick (units.TICK); returns the colours of blocks eaten (each reappears elsewhere): those its point
        passed within EAT of, moving forward."""
        h0 = self.head()
        self.pos = (self.pos + self.speed * TICK) % WORLD
        self.heading += self.spin * TICK
        self.speed *= math.exp(-DRAG * TICK)
        self.spin *= math.exp(-DRAG * TICK)
        if self.speed @ self.forward() <= 0:                # it only eats what it moves forward into
            return []
        eaten = _touching(self.xy, h0, self.head())
        for b in eaten:
            self.xy[b] = self.somewhere()
        return [COLOURS[self.kind[b]] for b in eaten]
