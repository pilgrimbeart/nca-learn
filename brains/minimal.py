"""The minimal brain: the mixed-signal brain's four neurons and nothing else. Each sensor drives both motors through a
synapse that relays every spike, so the creature drives straight at any block it sees; taste reaches a node connected
to nothing. No learning, no hush. The baseline for recruitment (RECRUITMENT.md): what a brain does before it has any
machinery for telling food from poison.
"""

from __future__ import annotations

from brains.mixed_signal import SIDE, CircuitBrain
from mixed_feedback import Circuit


class MinimalBrain(CircuitBrain):
    def build(self, c: Circuit) -> None:
        for s in self.sensors:
            for m in self.motors:
                c.synapse(m, s, SIDE)

    def drive(self, sensor: int) -> float:
        """Measuring and watching: every sensor always fires both motors."""
        return 1.0
