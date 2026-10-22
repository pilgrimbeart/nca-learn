"""The knowing circuit: the baseline circuit (brains/baseline.py) plus a taste neuron that can learn what predicts pain
but can't act on it. The starting animal for recruitment (RECRUITMENT.md): it may know, and must recruit in order to act.
All circuit.

  The taste neuron T fires at a bad taste (innately: an amplifier from the taste node, on while the taste is bad),
  and, through a plastic synapse from each sensor, at whatever has come before bad tastes. Each synapse's strength is
  a memory node W (no leak, noisy only when written), charged by a bad taste and emptied by a good one while its
  sensor was recently active (that sensor's eligibility node, fading over ELIGIBLE seconds), as the mixed-signal
  brain's P. So T comes to fire on seeing the poison colour, before any meal: an anticipated pain.
  T has no outputs: what it knows reaches nothing, and the creature behaves as the baseline circuit does. Pain reaches
  only T, the taste organ; the sensors and motors never feel it.
"""

from __future__ import annotations

from brains.circuit import SIDE, STRONG, CircuitBrain
from mixed_feedback import Circuit
from units import C_TYP, I_TYP, T_TYP

ELIGIBLE = 0.1      # s over which a sensor's eligibility fades
PAIN = 3 * I_TYP    # A: how hard a bad taste drives T (a spike for every bad taste)
STEP = 0.3          # how far a taste moves a synapse's strength (0..1) while its sensor is fully eligible


class KnowingBrain(CircuitBrain):
    STREAMS = True                                      # comparable life for life with its variants
    learning_step = STEP                                # (0 for an experiment in which T can't learn)

    def build(self, c: Circuit) -> None:
        self.syn = {(s, m): c.synapse(m, s, SIDE) for s in self.sensors for m in self.motors}
        self.T = c.neuron("T")
        c.element(self.T, self.taste_node, PAIN, -0.5, slope=-20.0, sigmoid=True)    # innate: bad taste excites T
        fade = lambda seconds: seconds / (10 * C_TYP)           # R, with C = 10 C_TYP, for a node to fade over these
        self.W = {}
        for s in self.sensors:
            E = c.node(f"E{c.names[s]}", R=fade(ELIGIBLE), C=10 * C_TYP, lo=0.0, hi=1.0)
            c.element(E, s, 10 * I_TYP, 0.0, slope=5.0, sigmoid=True)           # the sensor's spike charges E
            W = c.node(f"W{c.names[s]}", R=None, lo=0.0, hi=1.0, start=0.0, memory=True)
            c.element(self.T, s, STRONG, 0.0, tau=0.5 * T_TYP, slope=5.0, sigmoid=True, gate=W)  # learned: s excites T
            g = self.learning_step * C_TYP / (1.3 * T_TYP)               # (taste stays above half for about 1.3 T_TYP)
            c.element(W, self.taste_node, g, -0.5, slope=-20.0, sigmoid=True, gate=E)    # bad: strengthen
            c.element(W, self.taste_node, -g, 0.5, slope=20.0, sigmoid=True, gate=E)     # good: weaken
            self.W[s] = W

    def drive(self, sensor: int) -> float:
        """Measuring and watching: every sensor always fires both motors (T acts on nothing)."""
        return 1.0

    def shown(self) -> list:
        return [("T taste", self.T)]
