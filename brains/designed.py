"""The designed circuit: a small circuit of excitable neurons (mixed_feedback.py), designed by hand. Everything,
learning too, is nodes and elements; the body only injects currents into its input nodes and counts its motors'
spikes. The circuit's neurons are fast beside the world's tick (units.TICK), so its spikes come often and each kick
of a thruster is small.

  Four neurons alike: two sensors, two motors, each an excitable neuron (it rests; a pulse above threshold gives one
  spike; noise gives the odd spike of its own, so a creature that sees nothing still moves). A stimulus is a current
  pulse into its sensor; a motor's spike fires its thruster.
  Each sensor excites one motor, its side (by a coin toss at birth), through a strong synapse that relays every
  spike, and the other through a plastic synapse whose weight is STRONG times p: at p = 1 it relays nearly every
  spike, at p = 0 none, in between noise decides (graded for p up to about 0.4; at 1/2 it relays about 85%). So a
  sensor fires both motors or one, more often both the higher its p, as in the sheet brain.
  The sensors inhibit each other: a sensor's spikes charge its hush node H, which leaks away over HUSH seconds and
  while charged holds the other sensor down. So while it sees one colour the creature heeds that colour only.
  Learning: three factors, all in the circuit. Taste is a current pulse into one node, the same for both sensors
  (+ food, - poison). Each sensor's spikes charge its eligibility node E, which leaks away over ELIGIBLE seconds. p is
  the voltage on a big capacitor P (no leak, clamped to 0..1) that gates the plastic synapse; two amplifiers charge
  it while taste is good, or discharge it while bad, each with its bias current set by E: so a taste moves p by about
  LEARN x E, and only a sensor that fired lately learns. A sensor's spike also empties the other sensor's E (FORGET:
  cross-inhibition), so a taste goes to the one that fired last. Nothing here says what a sensor senses or what a
  motor does, or which sensor a taste is about.
"""

from __future__ import annotations

from brains.circuit import INHIBIT, I_TYP, SIDE, STRONG, CircuitBrain
from mixed_feedback import Circuit
from units import C_TYP, T_TYP

HUSH = 0.1          # s over which a sensor's hush on the other fades
ELIGIBLE = 0.1      # s over which a sensor's eligibility fades after it fires
LEARN = 0.3         # how far a taste moves p while the sensor is fully eligible
FORGET = 1.0        # how hard a sensor's spike empties the other sensor's eligibility
CP = 1000 * C_TYP   # F: P's capacitor, big, so its noise is small


class DesignedBrain(CircuitBrain):
    def build(self, c: Circuit) -> None:
        fade = lambda seconds: seconds / (10 * C_TYP)           # R, with C = 10 C_TYP, for a node to fade over these
        self.E = [c.node(f"E{k}", R=fade(ELIGIBLE), C=10 * C_TYP, lo=0.0, hi=1.0) for k in (0, 1)]
        self.P = []
        for k, s in enumerate(self.sensors):
            side = int(c.rng.integers(2))                       # a coin toss: this sensor's side
            c.synapse(self.motors[side], s, SIDE)
            P = c.node(f"P{k}", R=None, C=CP, lo=0.0, hi=1.0, start=0.5)
            c.element(self.motors[1 - side], s, STRONG, 0.0, tau=0.5 * T_TYP, slope=5.0, sigmoid=True, gate=P)
            H = c.node(f"H{k}", R=fade(HUSH), C=10 * C_TYP, lo=0.0, hi=1.0)
            c.element(H, s, 10 * I_TYP, 0.0, slope=5.0, sigmoid=True)           # a spike charges H ...
            c.element(self.sensors[1 - k], H, -INHIBIT, 0.5, slope=10.0, sigmoid=True)  # ... which hushes the other
            E = self.E[k]
            c.element(E, s, 10 * I_TYP, 0.0, slope=5.0, sigmoid=True)           # a spike charges E ...
            c.element(self.E[1 - k], s, -10 * I_TYP * FORGET, 0.0, slope=5.0, sigmoid=True)   # ... and empties the other's
            g = LEARN * CP / (1.3 * T_TYP)                          # (taste stays above half for about 1.3 T_TYP)
            c.element(P, self.taste_node, g, 0.5, slope=20.0, sigmoid=True, gate=E)      # good: charge
            c.element(P, self.taste_node, -g, -0.5, slope=-20.0, sigmoid=True, gate=E)   # bad: discharge
            self.P.append(P)

    def drive(self, sensor: int) -> float:
        """Measuring and watching: p, the voltage on the sensor's P."""
        c = self.circuit
        return float(c.V[self.P[sensor]]) if c.V is not None else c.start[self.P[sensor]]
