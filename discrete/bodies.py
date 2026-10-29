"""Bodies that differ (the user's question, 2026-10-26: can a circuit tune itself to the body it finds itself in?): each
life's creature built a little differently, as two copies of a real robot would be, so that no fixed circuit is best
for all. What may differ, as factors on world.py's values (my choices, to confirm):

- strength: both thrusters' push and turn together (a weaker or stronger motor pair, or a heavier body);
- asymmetry: the left thruster's push and turn against the right's (two motors never match);
- eyes: how often the eyes pulse for what they see (sensitivity);
- drag: how fast speed and turning fade (friction);
- left, right: each thruster's push and turn on its own (the user's choice, 2026-10-28, log-uniform confirmed
  2026-10-29: each drawn independently, 0.5 to 2 times world.py's, so most bodies are lopsided and their speeds
  differ: `THRUSTERS`).

world.py is unchanged: a life's Body becomes a VariedBody after creature.Life builds it (the same world, wiring and
start as the unvaried life of that seed).
"""

from __future__ import annotations

import math

import numpy as np

import world
from units import TICK

SPREAD = {"strength": 2.0, "asymmetry": 1.25, "eyes": 2.0, "drag": 1.5}   # each factor drawn log-uniform within
                    # 1/x to x of world.py's value
THRUSTERS = {"left": 2.0, "right": 2.0}                 # the user's bodies: each thruster 0.5 to 2 (log-uniform: the
                                                        # median body as world.py's)


def draw(seed: int, spread=SPREAD) -> dict:
    """A body's factors for a seed (its own stream: the world's is untouched)."""
    rng = np.random.default_rng(seed + 9_100_003)
    return {k: float(x ** rng.uniform(-1, 1)) for k, x in spread.items()}


class VariedBody(world.Body):
    """world.Body with its own factors (draw)."""

    def fire(self, thruster: str) -> None:
        f = self.factors
        side = math.sqrt(f.get("asymmetry", 1.0)) ** (1 if thruster == "left" else -1)
        k = f.get("strength", 1.0) * side * f.get(thruster, 1.0)
        self.speed += k * world.PUSH * self.forward()
        self.spin += k * (world.TURN if thruster == "right" else -world.TURN)

    def move(self) -> list:
        out = super().move()                            # (it fades by world.DRAG; then by the rest of this body's)
        extra = math.exp(-(self.factors.get("drag", 1.0) - 1.0) * world.DRAG * TICK)
        self.speed *= extra
        self.spin *= extra
        return out

    def sees(self) -> dict:
        e = self.factors.get("eyes", 1.0)
        return {c: e * v for c, v in super().sees().items()}


def vary(life, factors: dict):
    """Make a creature.Life's body a VariedBody with these factors (before its first step)."""
    life.body.__class__ = VariedBody
    life.body.factors = dict(factors)
    return life
