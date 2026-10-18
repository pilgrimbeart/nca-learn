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

BODY = 4.0          # the triangle's side, in world units
WORLD = 60.0        # the world's side (a torus)
BLOCKS = 18         # blocks of each colour
EAT = 1.0           # a block this near the point (the mouth) is eaten; the eyes' corridor is twice this wide
SENSE = 0.5         # stimuli per tick to an eye that sees its colour at full strength
REACH = 5.0         # a block this far off counts half as much as one at the eyes
RANGE = 15.0        # how far the eyes see
RAYS = 25           # the eyes' rays, side by side across the corridor ahead: each stops at the first block it meets
BLOCK = 1.0         # a block's radius (what it hides behind it)
PUSH = 0.2          # a thruster firing adds this much forward speed ...
TURN = 0.16         # ... and this much turning speed, away from its side (radians per tick): both at once go straight
DRAG = 0.5          # speed and turning fade at this rate
COLOURS = ("red", "blue")
THRUSTERS = ("left", "right")                           # at the tail's two corners, both pushing forward


class Body:
    """Where the creature is and how it moves; the world's blocks."""

    def __init__(self, rng):
        self.rng = rng
        self.pos = np.array([WORLD / 2, WORLD / 2])
        self.heading = rng.uniform(0, 2 * math.pi)
        self.speed, self.spin = np.zeros(2), 0.0
        self.blocks = [[*self.somewhere(), c] for c in COLOURS for _ in range(BLOCKS)]

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
        goes (to the first block it meets, or RANGE), and that block's colour (or None)."""
        f, h = self.forward(), self.head()
        side, w = np.array([f[1], -f[0]]), EAT
        across = -w + (np.arange(RAYS) + 0.5) * 2 * w / RAYS
        far, colour = np.full(RAYS, RANGE), [None] * RAYS
        for x, y, c in self.blocks:
            d = self.wrap(np.array([x, y]) - h)
            ahead, off = d @ f, d @ side
            if ahead <= -BLOCK or ahead - BLOCK >= RANGE or abs(off) >= w + BLOCK:
                continue
            gap = BLOCK ** 2 - (across - off) ** 2
            for k in np.nonzero(gap > 0)[0]:
                hit = max(0.0, ahead - np.sqrt(gap[k]))
                if hit < far[k]:
                    far[k], colour[k] = hit, c
        return across, far, colour

    def sees(self) -> dict:
        """How strongly each colour is seen, at most 1: a block wholly in view counts 1 / (1 + (distance / REACH)^2),
        less if part of it is hidden or out of the corridor."""
        _, far, colour = self.look()
        share = (2 * EAT / RAYS) / (2 * BLOCK)              # one ray's share of a block's width
        seen = {c: 0.0 for c in COLOURS}
        for d, c in zip(far, colour):
            if c is not None:
                seen[c] += share / (1 + (d / REACH) ** 2)
        return {c: min(1.0, v) for c, v in seen.items()}

    def fire(self, thruster: str) -> None:
        self.speed += PUSH * self.forward()
        self.spin += TURN if thruster == "right" else -TURN    # the left one turns it right, and the right one left

    def move(self) -> list:
        """Moves on a tick; returns the colours of blocks eaten (each reappears elsewhere)."""
        self.pos = (self.pos + self.speed) % WORLD
        self.heading += self.spin
        self.speed *= math.exp(-DRAG)
        self.spin *= math.exp(-DRAG)
        eaten, h = [], self.head()
        if self.speed @ self.forward() <= 0:                # it only eats what it moves forward into
            return eaten
        for b in self.blocks:
            if np.linalg.norm(self.wrap(np.array(b[:2]) - h)) < EAT:
                eaten.append(b[2])
                b[0], b[1] = self.somewhere()
        return eaten

