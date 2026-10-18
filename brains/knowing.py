"""The knowing brain: the minimal brain (brains/minimal.py) plus a taste neuron that can learn what predicts pain but
can't act on it. The starting animal for recruitment (RECRUITMENT.md): it may know, and must recruit in order to act.
All circuit.

  The taste neuron T fires at a bad taste (innately: an amplifier from the taste node, on while the taste is bad),
  and, through a plastic synapse from each sensor, at whatever has come before bad tastes. Each synapse's strength is
  a memory node W (no leak, noisy only when written), charged by a bad taste and emptied by a good one while its
  sensor was recently active (that sensor's eligibility node, fading over ELIGIBLE ticks), as the mixed-signal
  brain's P. So T comes to fire on seeing the poison colour, before any meal: an anticipated pain.
  T has no outputs: what it knows reaches nothing, and the creature behaves as the minimal brain does. Pain reaches
  only T, the taste organ; the sensors and motors never feel it.
"""

from __future__ import annotations

from brains.circuit import SIDE, SPEED, STRONG, CircuitBrain
from mixed_feedback import Circuit

ELIGIBLE = 10.0     # ticks over which a sensor's eligibility fades
PAIN = 3.0          # how hard a bad taste drives T (a spike for every bad taste)
STEP = 0.3          # how far a taste moves a synapse's strength (0..1) while its sensor is fully eligible


class KnowingBrain(CircuitBrain):
    STREAMS = True                                      # comparable life for life with its variants
    learning_step = STEP                                # (0 for an experiment in which T can't learn)

    def build(self, c: Circuit) -> None:
        self.syn = {(s, m): c.synapse(m, s, SIDE) for s in self.sensors for m in self.motors}
        self.T = c.neuron("T")
        c.element(self.T, self.taste_node, PAIN, -0.5, slope=-20.0, sigmoid=True)    # innate: bad taste excites T
        fade = lambda ticks: ticks * SPEED / 10.0               # R, with C = 10, for a node to fade over these ticks
        self.W = {}
        for s in self.sensors:
            E = c.node(f"E{c.names[s]}", R=fade(ELIGIBLE), C=10.0, lo=0.0, hi=1.0)
            c.element(E, s, 10.0, 0.0, slope=5.0, sigmoid=True)                 # the sensor's spike charges E
            W = c.node(f"W{c.names[s]}", R=None, lo=0.0, hi=1.0, start=0.0, memory=True)
            c.element(self.T, s, STRONG, 0.0, tau=0.5, slope=5.0, sigmoid=True, gate=W)  # learned: s excites T
            g = self.learning_step / 1.3                                 # (taste stays above half for about 1.3 ticks)
            c.element(W, self.taste_node, g, -0.5, slope=-20.0, sigmoid=True, gate=E)    # bad: strengthen
            c.element(W, self.taste_node, -g, 0.5, slope=20.0, sigmoid=True, gate=E)     # good: weaken
            self.W[s] = W

    def drive(self, sensor: int) -> float:
        """Measuring and watching: every sensor always fires both motors (T acts on nothing)."""
        return 1.0

    def shown(self) -> list:
        return [("T taste", self.T)]
