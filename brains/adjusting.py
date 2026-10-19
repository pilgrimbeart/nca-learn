"""The adjusting circuit: rung 0 of recruitment (RECRUITMENT.md), all of it circuit. The minimal circuit's neurons
(brains/minimal.py), each sensor driving both motors, and every neuron given the same motif:

  eligibility, a leaky node charged by the neuron's own spikes, fading over ELIGIBLE ticks;
  a knob, a memory node (no leak, noisy only when written), driving a current of up to RANGE out of the neuron
  (an amplifier whose bias current the knob sets), so the more it holds the less excitable the neuron;
  and, for the sensors only (taste sits beside them; the motors never feel it), two amplifiers from the taste node
  into the knob, gated by eligibility: a bad taste charges it, a good one empties it, by about STEP while fully
  eligible.

Nothing else: no program runs beside the circuit. Nothing is recruited yet.
"""

from __future__ import annotations

from brains.circuit import SIDE, SPEED, CircuitBrain
from mixed_feedback import Circuit

ELIGIBLE = 10.0     # ticks over which eligibility fades
RANGE = 1.4         # the most current a full knob takes out of its neuron: its bias from -1.6 down to -3.0
STEP = 0.1          # how far a taste moves a knob (0..1) while the neuron is fully eligible


class AdjustingBrain(CircuitBrain):
    STREAMS = True                                      # comparable life for life with its variants

    def build(self, c: Circuit) -> None:
        for s in self.sensors:
            for m in self.motors:
                c.synapse(m, s, SIDE)
        fade = lambda ticks: ticks * SPEED / 10.0               # R, with C = 10, for a node to fade over these ticks
        self.knob = {}
        for n in self.sensors + self.motors:
            E = c.node(f"E{c.names[n]}", R=fade(ELIGIBLE), C=10.0, lo=0.0, hi=1.0)
            c.element(E, n, 10.0, 0.0, slope=5.0, sigmoid=True)                 # a spike charges E
            K = c.node(f"K{c.names[n]}", R=None, lo=0.0, hi=1.0, start=0.0, memory=True)
            c.element(n, K, -RANGE, -10.0, slope=1.0, sigmoid=True, gate=K)     # a current of RANGE x K out of n
            if n in self.sensors:                                               # taste sits beside the sensors
                g = STEP / 1.3                                  # (taste stays above half for about 1.3 ticks)
                c.element(K, self.taste_node, g, -0.5, slope=-20.0, sigmoid=True, gate=E)    # bad: charge
                c.element(K, self.taste_node, -g, 0.5, slope=20.0, sigmoid=True, gate=E)     # good: empty
            self.knob[n] = K

    def drive(self, sensor: int) -> float:
        """Measuring and watching: the sensor's excitability, from 1 (its knob empty) to 0 (full)."""
        return 1.0 - float(self.circuit.V[self.knob[self.sensors[sensor]]]) if self.circuit.V is not None else 1.0
