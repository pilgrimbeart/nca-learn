"""The minimal circuit: the designed circuit's four neurons and nothing else. Each sensor drives both motors through a
synapse that relays every spike, so the creature drives straight at any block it sees; taste reaches a node connected
to nothing. No learning, no hush. The baseline for recruitment (RECRUITMENT.md): what a brain does before it has any
machinery for telling food from poison.
"""

from __future__ import annotations

from brains.circuit import SIDE, CircuitBrain
from mixed_feedback import Circuit


class MinimalBrain(CircuitBrain):
    STREAMS = True                                      # comparable life for life with its variants

    def build(self, c: Circuit) -> None:
        for s in self.sensors:
            for m in self.motors:
                c.synapse(m, s, SIDE)

    def drive(self, sensor: int) -> float:
        """Measuring and watching: every sensor always fires both motors."""
        return 1.0
