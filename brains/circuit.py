"""What every circuit brain shares (the designed, minimal, adjusting, knowing and recruiting circuits): a
mixed-feedback circuit (mixed_feedback.py) with two sensor and two motor neurons and a taste node, run SPEED circuit
ticks to each tick of the world; the body injects currents into the sensors and the taste node, and counts the motors'
spikes. Each brain wires its own circuit between them (build).
"""

from __future__ import annotations

from collections import deque

import numpy as np

from mixed_feedback import Circuit

SPEED = 4           # circuit ticks per tick of the world: how fast the brain runs beside the body
STIMULUS = 3.0      # the current a stimulus injects into its sensor for a circuit tick (threshold about 1)
SIDE = 1.0          # the weight of a synapse that relays every spike
STRONG = 0.7        # a gated synapse's weight when fully open: relays nearly every spike
INHIBIT = 1.5       # how hard a hold or hush node holds a neuron down (a current out of it)
TASTE = 3.0         # the current taste injects into the taste node for a circuit tick (x +1 food, -1 poison)
TRACE = 490         # watching: ticks of history drawn


class CircuitBrain:
    """A brain that is a mixed-feedback circuit: two sensor and two motor neurons and a taste node, and whatever a
    subclass wires between them (in build). The body injects currents and counts the motors' spikes. STREAMS: each
    node's noise from its own stream (mixed_feedback.Circuit), so variants of a brain can be compared life for life."""

    STREAMS = False

    def __init__(self, seed: int):
        self.seed = seed
        c = self.circuit = Circuit(seed=seed + 1_000_003, streams=self.STREAMS)   # its own noise, not the world's
        self.sensors = [c.neuron(f"S{k}") for k in (0, 1)]
        self.motors = [c.neuron(f"M{k}") for k in (0, 1)]
        self.taste_node = c.node("taste", R=0.5)
        self.build(c)
        self.inject = np.zeros(len(c.names))
        self.history = deque(maxlen=TRACE)                      # watching: (voltages, spikes) each tick
        self.log = None                                         # measuring: a list, to record every tick

    def build(self, c: Circuit) -> None:
        raise NotImplementedError

    def stimulate(self, sensor: int) -> None:
        self.inject[self.sensors[sensor]] = STIMULUS

    def taste(self, value: float) -> None:
        self.inject[self.taste_node] = TASTE * value

    def step(self) -> list:
        return self._motors(self._tick())

    def _tick(self) -> np.ndarray:
        """One tick of the world: the circuit's spikes, per node."""
        injected = self.last_inject = self.inject.copy()          # (watching: what went in this tick)
        spikes = self.circuit.tick(self.inject, SPEED)          # inputs last the first circuit tick
        self.inject[:] = 0.0
        self.history.append((self.circuit.V.copy(), spikes))
        if self.log is not None:                                # measuring: what went in, and what happened
            self.log.append((injected, spikes, self.circuit.vmax.copy(), self.circuit.V.copy()))
        return spikes

    def _motors(self, spikes) -> list:
        """The motors that fired: a motor once for each of its spikes."""
        return [m for m, n in enumerate(self.motors) for _ in range(spikes[n])]

    def shown(self) -> list:
        """Watching: any other neurons to draw, as (label, node)."""
        return []

    def built(self) -> bool:
        return True

    def stage(self) -> str:
        return "waiting"

    def draw(self, screen, side: int, font, sensors: list, motors: list, lit) -> None:
        """Its panel, in greys: each neuron's voltage over the last TRACE ticks, a white mark at each spike; labelled
        with what the body wired it to. lit: a sensor to highlight, or None."""
        import pygame
        rows = [(f"S{k} {sensors[k]}", self.sensors[k], k == lit) for k in (0, 1)] + \
               [(f"M{k} {motors[k]}", self.motors[k], False) for k in (0, 1)] + \
               [(label, n, False) for label, n in self.shown()]
        h = side // len(rows)
        for i, (label, n, hot) in enumerate(rows):
            top = i * h
            pygame.draw.rect(screen, (30, 30, 30), (0, top + 4, side, h - 8))
            pts = [(x * side // TRACE, top + h // 2 - int(v[n] * h / 10)) for x, (v, _) in enumerate(self.history)
                   if n < len(v)]                       # (a neuron grown in the life has no history before it)
            if len(pts) > 1:
                pygame.draw.lines(screen, (160, 160, 160), False, pts, 1)
            for x, (_, sp) in enumerate(self.history):
                if n < len(sp) and sp[n]:
                    pygame.draw.line(screen, (255, 255, 255), (x * side // TRACE, top + 8), (x * side // TRACE, top + h - 8), 2)
            screen.blit(font.render(label, True, (0, 0, 0) if hot else (255, 255, 255),
                                    (255, 255, 255) if hot else (60, 60, 60)), (6, top + 8))
