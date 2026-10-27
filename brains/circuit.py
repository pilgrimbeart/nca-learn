"""What every circuit brain shares (README: The circuit brains; the minimal search's circuits too, minimal/spec.py): a
mixed-feedback circuit (mixed_feedback.py) with two sensor and two motor neurons and a taste node, run for each tick of
the world (units.TICK); the body gives pulses of current to the sensors and the taste node, each at a moment of its
own within the tick, and counts the motors' spikes. Each brain wires its own circuit between them (build). Values in SI
(units.py).
"""

from __future__ import annotations

from collections import deque

import numpy as np

from mixed_feedback import Circuit
from units import C_TYP, PULSE, R_TYP, T_TYP, TICK

VOLT = 1.0              # V: the recruitment line's typical voltage: its circuits were drawn at 1 V before the supply was
                        # fixed (2026-10-26), and keep it (mixed_feedback.Circuit's volt); not yet built in transistors
I_TYP = C_TYP * VOLT / T_TYP    # A: its typical current, 1 nA (units.I_TYP is the chip's, at units.V_TYP)
PULSES = 3.0            # the current a stimulus injects into its sensor for units.PULSE, and taste into the taste node
                        # (x +1 food, -1 poison), in typical currents of the brain's technology (Circuit.unit: the
                        # user's decision, 2026-10-26: the body's pulses match the technology in use); a neuron's
                        # threshold needs about a third of that charge
STIMULUS = PULSES * I_TYP   # A: so here (at 1 V typical)
SIDE = 1 * I_TYP        # A: the weight of a synapse that relays every spike
STRONG = 0.7 * I_TYP    # A: a gated synapse's weight when fully open: relays nearly every spike
INHIBIT = 1.5 * I_TYP   # A: how hard a hold or hush node holds a neuron down (a current out of it)
TASTE = PULSES * I_TYP  # A: and taste's
TRACE = 490             # watching: ticks of history drawn


class CircuitBrain:
    """A brain that is a mixed-feedback circuit: two sensor and two motor neurons and a taste node, and whatever a
    subclass wires between them (in build). The body injects currents and counts the motors' spikes. STREAMS: each
    node's noise from its own stream (mixed_feedback.Circuit), so variants of a brain can be compared life for life."""

    STREAMS = False

    def __init__(self, seed: int):
        self.seed = seed
        c = self.circuit = Circuit(seed=seed + 1_000_003, streams=self.STREAMS, volt=VOLT,
                                                on_chip=False)   # its own noise, not the world's
        self.sensors = [c.neuron(f"S{k}") for k in (0, 1)]
        self.motors = [c.neuron(f"M{k}") for k in (0, 1)]
        self.taste_node = c.node("taste", R=0.5 * R_TYP)
        self.build(c)
        self.last_inject = np.zeros(len(c.names))              # (watching: the charge each node took last tick)
        self.history = deque(maxlen=TRACE)                      # watching: (voltages, spikes) each tick
        self.log = None                                         # measuring: a list, to record every tick

    def build(self, c: Circuit) -> None:
        raise NotImplementedError

    def stimulate(self, sensor: int, at: float) -> None:
        """A stimulus, `at` seconds into the next tick."""
        self.circuit.pulse(self.sensors[sensor], PULSES * self.circuit.unit(), at, PULSE)

    def taste(self, value: float, at: float) -> None:
        self.circuit.pulse(self.taste_node, PULSES * self.circuit.unit() * value, at, PULSE)

    def step(self) -> list:
        return self._motors(self._tick())

    def _tick(self) -> np.ndarray:
        """One tick of the world: the circuit's spikes, per node."""
        spikes = self.circuit.run(TICK)
        injected = self.last_inject = self.circuit.last_charge  # (watching: the charge the pulses brought this tick)
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
        """Its panel: each neuron's voltage over the last TRACE ticks in sky blue (Okabe-Ito), a white mark at each
        spike; labelled with what the body wired it to. lit: a sensor to highlight, or None."""
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
                pygame.draw.lines(screen, (86, 180, 233), False, pts, 1)
            for x, (_, sp) in enumerate(self.history):
                if n < len(sp) and sp[n]:
                    pygame.draw.line(screen, (255, 255, 255), (x * side // TRACE, top + 8), (x * side // TRACE, top + h - 8), 2)
            screen.blit(font.render(label, True, (0, 0, 0) if hot else (255, 255, 255),
                                    (255, 255, 255) if hot else (60, 60, 60)), (6, top + 8))
