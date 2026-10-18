"""The mixed-signal brain: a small circuit of excitable neurons (mixed_feedback.py), designed, not grown. Everything,
learning too, is nodes and elements; the body only injects currents into its input nodes and counts its motors'
spikes. The circuit runs SPEED of its ticks to each tick of the world, so its spikes come often and each kick of a
thruster is small.

  Four neurons alike: two sensors, two motors, each an excitable neuron (it rests; a pulse above threshold gives one
  spike; noise gives the odd spike of its own, so a creature that sees nothing still moves). A stimulus is a current
  pulse into its sensor; a motor's spike fires its thruster.
  Each sensor excites one motor, its side (by a coin toss at birth), through a strong synapse that relays every
  spike, and the other through a plastic synapse whose weight is STRONG times p: at p = 1 it relays nearly every
  spike, at p = 0 none, at p = 1/2 noise decides, about half the time. So a sensor fires both motors or one, more
  often both the higher its p, as in the grown brain.
  The sensors inhibit each other: a sensor's spikes charge its hush node H, which leaks away over HUSH ticks and
  while charged holds the other sensor down. So while it sees one colour the creature heeds that colour only.
  Learning: three factors, all in the circuit. Taste is a current pulse into one node, the same for both sensors
  (+ food, - poison). Each sensor's spikes charge its eligibility node E, which leaks away over ELIGIBLE ticks. p is
  the voltage on a big capacitor P (no leak, clamped to 0..1) that gates the plastic synapse; two amplifiers charge
  it while taste is good, or discharge it while bad, each with its bias current set by E: so a taste moves p by about
  LEARN x E, and only a sensor that fired lately learns. A sensor's spike also empties the other sensor's E (FORGET:
  cross-inhibition), so a taste goes to the one that fired last. Nothing here says what a sensor senses or what a
  motor does, or which sensor a taste is about.
"""

from __future__ import annotations

import numpy as np

from mixed_feedback import Circuit

SPEED = 4           # circuit ticks per tick of the world: how fast the brain runs beside the body
STIMULUS = 3.0      # the current a stimulus injects into its sensor for a circuit tick (threshold about 1)
SIDE = 1.0          # the weight of a sensor's synapse to its side's motor: relays every spike
STRONG = 0.7        # the plastic synapse's weight at p = 1: relays nearly every spike
INHIBIT = 1.5       # how hard a sensor that fired lately holds the other down (a current out of it)
HUSH = 10.0         # ticks over which that fades
TASTE = 3.0         # the current taste injects into the taste node for a circuit tick (x +1 food, -1 poison)
ELIGIBLE = 10.0     # ticks over which a sensor's eligibility fades after it fires
LEARN = 0.3         # how far a taste moves p while the sensor is fully eligible
FORGET = 1.0        # how hard a sensor's spike empties the other sensor's eligibility
CP = 1000.0         # P's capacitor: big, so its noise is small
TRACE = 490         # watching: ticks of history drawn


class MixedSignalBrain:
    def __init__(self, seed: int):
        c = self.circuit = Circuit(seed=seed + 1_000_003)       # its own noise, apart from the world's
        self.sensors = [c.neuron(f"S{k}") for k in (0, 1)]
        self.motors = [c.neuron(f"M{k}") for k in (0, 1)]
        self.taste_node = c.node("taste", R=0.5)
        fade = lambda ticks: ticks * SPEED / 10.0               # R, with C = 10, for a node to fade over these ticks
        self.E = [c.node(f"E{k}", R=fade(ELIGIBLE), C=10.0, lo=0.0, hi=1.0) for k in (0, 1)]
        self.P = []
        for k, s in enumerate(self.sensors):
            side = int(c.rng.integers(2))                       # a coin toss: this sensor's side
            c.synapse(self.motors[side], s, SIDE)
            P = c.node(f"P{k}", R=None, C=CP, lo=0.0, hi=1.0, start=0.5)
            c.element(self.motors[1 - side], s, STRONG, 0.0, tau=0.5, slope=5.0, sigmoid=True, gate=P)
            H = c.node(f"H{k}", R=fade(HUSH), C=10.0, lo=0.0, hi=1.0)
            c.element(H, s, 10.0, 0.0, slope=5.0, sigmoid=True)                 # a spike charges H ...
            c.element(self.sensors[1 - k], H, -INHIBIT, 0.5, slope=10.0, sigmoid=True)  # ... which hushes the other
            E = self.E[k]
            c.element(E, s, 10.0, 0.0, slope=5.0, sigmoid=True)                 # a spike charges E ...
            c.element(self.E[1 - k], s, -10.0 * FORGET, 0.0, slope=5.0, sigmoid=True)   # ... and empties the other's
            g = LEARN * CP / 1.3                                    # (taste stays above half for about 1.3 ticks)
            c.element(P, self.taste_node, g, 0.5, slope=20.0, sigmoid=True, gate=E)      # good: charge
            c.element(P, self.taste_node, -g, -0.5, slope=-20.0, sigmoid=True, gate=E)   # bad: discharge
            self.P.append(P)
        self.inject = np.zeros(len(c.names))
        self.history = []                                       # watching: (voltages, spikes) each tick

    def stimulate(self, sensor: int) -> None:
        self.inject[self.sensors[sensor]] = STIMULUS

    def taste(self, value: float) -> None:
        self.inject[self.taste_node] = TASTE * value

    def step(self) -> list:
        spikes = self.circuit.tick(self.inject)                 # inputs last one circuit tick
        self.inject = np.zeros(len(self.inject))
        for _ in range(SPEED - 1):
            spikes = spikes + self.circuit.tick(self.inject)
        self.history = (self.history + [(self.circuit.V.copy(), spikes)])[-TRACE:]
        return [m for m, n in enumerate(self.motors) for _ in range(spikes[n])]

    def drive(self, sensor: int) -> float:
        """Measuring and watching: p, the voltage on the sensor's P."""
        c = self.circuit
        return float(c.V[self.P[sensor]]) if c.V is not None else c.start[self.P[sensor]]

    def built(self) -> bool:
        return True

    def stage(self) -> str:
        return "waiting"

    def draw(self, screen, side: int, font, sensors: list, motors: list, lit) -> None:
        """Its panel, in greys: each neuron's voltage over the last TRACE ticks, a white mark at each spike; labelled
        with what the body wired it to. lit: a sensor to highlight, or None."""
        import pygame
        rows = [(f"S{k} {sensors[k]}", self.sensors[k], k == lit) for k in (0, 1)] + \
               [(f"M{k} {motors[k]}", self.motors[k], False) for k in (0, 1)]
        h = side // 4
        for i, (label, n, hot) in enumerate(rows):
            top = i * h
            pygame.draw.rect(screen, (30, 30, 30), (0, top + 4, side, h - 8))
            pts = [(x * side // TRACE, top + h // 2 - int(v[n] * h / 10)) for x, (v, _) in enumerate(self.history)]
            if len(pts) > 1:
                pygame.draw.lines(screen, (160, 160, 160), False, pts, 1)
            for x, (_, sp) in enumerate(self.history):
                if sp[n]:
                    pygame.draw.line(screen, (255, 255, 255), (x * side // TRACE, top + 8), (x * side // TRACE, top + h - 8), 2)
            screen.blit(font.render(label, True, (0, 0, 0) if hot else (255, 255, 255),
                                    (255, 255, 255) if hot else (60, 60, 60)), (6, top + 8))
