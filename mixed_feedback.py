"""Mixed-feedback circuits, after Ribar and Sepulchre, "Neuromorphic Control" (2021): every circuit is nodes and one
kind of element.

  A node is a leaky capacitor: C dV/dt = -V / R + bias + (the currents of the elements into it) + (what is injected),
  with noise on every node (a noise current, so a big capacitor's voltage is quieter); it may be clamped between two
  voltages (diodes to two rails). An element puts a current into one node, gain x f(slope x (Vx - offset)), from a
  node's voltage Vx (its own: an ion channel; another's: a synapse), low-pass filtered with time constant tau (0: at
  once). f is tanh (an ion channel) or the logistic sigmoid (a synapse). An element may be gated by a third node: its
  current is then also multiplied by that node's voltage, clipped to 0..1 (an amplifier whose bias current a voltage
  sets). Its sign sets the feedback: an element on its own
  node with positive gain is positive feedback (it makes the node switch), with negative gain negative feedback (it
  restores it); the timescales at which each acts set the behaviour (an excitable neuron: fast positive feedback,
  slow negative).

Time is in ticks, integrated in steps of DT. A node spikes when its voltage rises through SPIKE, and can spike again
once it has fallen below RESET.
"""

from __future__ import annotations

import numpy as np

DT = 0.05           # integration step (ticks)
SPIKE, RESET = 0.0, -1.0


class Circuit:
    def __init__(self, seed: int = 0, noise: float = 0.2):
        self.rng, self.noise = np.random.default_rng(seed), noise
        self.bias, self.leak, self.cap, self.lo, self.hi, self.start, self.names = [], [], [], [], [], [], []
        self.to, self.frm, self.gain, self.offset, self.slope, self.tau, self.sigmoid, self.gate = ([] for _ in range(8))
        self.V = self.Vx = None

    def node(self, name: str, bias: float = 0.0, R: float | None = 2.0, C: float = 1.0, lo: float = -np.inf,
             hi: float = np.inf, start: float | None = None) -> int:
        """A node; R None: no leak. start: its voltage at birth (else where it settles at rest)."""
        for lst, v in ((self.names, name), (self.bias, bias), (self.leak, 0.0 if R is None else 1.0 / R),
                       (self.cap, C), (self.lo, lo), (self.hi, hi), (self.start, start)):
            lst.append(v)
        return len(self.names) - 1

    def element(self, to: int, frm: int, gain: float, offset: float, tau: float = 0.0, slope: float = 1.0,
                sigmoid: bool = False, gate: int = -1) -> int:
        for lst, v in ((self.to, to), (self.frm, frm), (self.gain, gain), (self.offset, offset), (self.slope, slope),
                       (self.tau, tau), (self.sigmoid, sigmoid), (self.gate, gate)):
            lst.append(v)
        return len(self.to) - 1

    def neuron(self, name: str, bias: float = -1.6, tau: float = 10.0, strength: float = 2.0) -> int:
        """An excitable neuron: fast positive feedback (it fires), slow negative feedback (it recovers). At rest
        below its threshold, a pulse above it gives one spike; noise gives the odd spike of its own."""
        n = self.node(name, bias)
        self.element(n, n, strength, -1.5)                      # fast: positive feedback, all-or-none
        self.element(n, n, -strength, -1.5, tau=tau)            # slow: negative feedback, recovery
        return n

    def synapse(self, to: int, frm: int, weight: float, tau: float = 0.5, slope: float = 5.0) -> int:
        """A current into `to` while `frm` spikes (excitatory if weight > 0)."""
        return self.element(to, frm, weight, SPIKE, tau=tau, slope=slope, sigmoid=True)

    def _ready(self):
        if self.V is None:
            self.arr = {k: np.array(getattr(self, k), dtype=float) for k in
                        ("bias", "leak", "cap", "lo", "hi", "gain", "offset", "slope", "tau")}
            self.ito, self.ifrm, self.igate = np.array(self.to), np.array(self.frm), np.array(self.gate)
            self.sig = np.array(self.sigmoid, dtype=bool)
            self.fixed = np.array([v is not None for v in self.start])
            self.V = np.array([-3.0 if v is None else v for v in self.start])
            self.V = np.clip(self.V, self.arr["lo"], self.arr["hi"])
            self.Vx = self.V[self.ifrm].copy()
            self.armed = np.ones(len(self.names), dtype=bool)
            born = self.V[self.fixed].copy()
            for _ in range(int(200 / DT)):                      # settle at rest (a node given a start keeps it)
                self._advance(np.zeros(len(self.names)), noise=False)
                self.V[self.fixed] = born

    def _advance(self, inject, noise=True):
        a = self.arr
        slow = a["tau"] > 0
        target = self.V[self.ifrm]
        self.Vx = np.where(slow, self.Vx + DT * (target - self.Vx) / np.where(slow, a["tau"], 1.0), target)
        x = a["slope"] * (self.Vx - a["offset"])
        f = np.where(self.sig, 1.0 / (1.0 + np.exp(-x)), np.tanh(x))
        f = np.where(self.igate >= 0, f * np.clip(self.V[self.igate], 0.0, 1.0), f)
        dV = -a["leak"] * self.V + a["bias"] + inject
        np.add.at(dV, self.ito, a["gain"] * f)
        self.V = self.V + DT * dV / a["cap"]
        if noise:
            self.V += self.noise * np.sqrt(DT) * self.rng.standard_normal(len(self.V)) / a["cap"]
        self.V = np.clip(self.V, a["lo"], a["hi"])

    def tick(self, inject) -> np.ndarray:
        """Runs one tick with these currents injected into the nodes; how many times each node spiked."""
        self._ready()
        spikes = np.zeros(len(self.names), dtype=int)
        for _ in range(int(round(1 / DT))):
            self._advance(inject)
            up = self.armed & (self.V > SPIKE)
            spikes += up
            self.armed = (self.armed & ~up) | (self.V < RESET)
        return spikes
