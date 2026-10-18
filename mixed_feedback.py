"""Mixed-feedback circuits, after Ribar and Sepulchre, "Neuromorphic Control" (2021): every circuit is nodes and one
kind of element.

  A node is a leaky capacitor: C dV/dt = -V / R + bias + (the currents of the elements into it) + (what is injected),
  with noise on every node (a noise current, so a big capacitor's voltage is quieter); it may be clamped between two
  voltages (diodes to two rails). An element puts a current into one node, gain x f(slope x (Vx - offset)), from a
  node's voltage Vx (its own: an ion channel; another's: a synapse), low-pass filtered with time constant tau (0: at
  once). f is tanh (an ion channel) or the logistic sigmoid (a synapse). An element may be gated by a third node: its
  current is then also multiplied by that node's voltage, clipped to 0..1 (an amplifier whose bias current a voltage
  sets). Its sign sets the feedback: an element on its own node with positive gain is positive feedback (it makes the
  node switch), with negative gain negative feedback (it restores it); the timescales at which each acts set the
  behaviour (an excitable neuron: fast positive feedback, slow negative).
  A memory node (a floating gate or memristor) has no leak, and its noise comes only with writing it: each step's
  change is rough by WRITE of itself, so it holds its value perfectly while nothing writes it (noise every step would
  walk it away: a leak by another name).

Time is in ticks, integrated in steps of DT (Euler; the noise scaled by sqrt(DT)), compiled: one call runs many
ticks. A node spikes when its voltage rises through SPIKE, and can spike again once it has fallen below RESET.
"""

from __future__ import annotations

import numpy as np
from numba import njit

DT = 0.05           # integration step (ticks)
SPIKE, RESET = 0.0, -1.0
SETTLE = 200        # ticks a new circuit runs without noise, to settle at rest
WRITE = 0.1         # a memory node's noise: this share of each change written to it
NONE = np.zeros(0, dtype=np.bool_)


@njit(cache=True)
def _run(V, Vx, armed, spikes, vmax, inject, inject_steps, node, el, link, z, noise, dt, steps, fixed, born):
    """steps integration steps. node: each node's (bias, leak, cap, lo, hi, write: > 0 for a memory); el: each
    element's (gain, offset, slope, tau, sigmoid); link: each element's (to, from, gate). inject: currents into the nodes for the first inject_steps.
    z: a standard normal draw for each node at each step (drawn beforehand: numpy's generator, the same stream).
    Settling (fixed given): no noise and no spikes, and the fixed nodes are put back to born after every step.
    vmax: each node's highest voltage over these steps (raised, never lowered, here)."""
    n, m = V.shape[0], link.shape[1]
    settling = fixed.shape[0] > 0
    bias, leak, cap, lo, hi, write = node[0], node[1], node[2], node[3], node[4], node[5]
    gain, offset, slope, tau, sig = el[0], el[1], el[2], el[3], el[4]
    to, frm, gate = link[0], link[1], link[2]
    dV = np.empty(n)
    scale = noise * np.sqrt(dt)
    for k in range(steps):
        for e in range(m):                                  # each element's input, filtered
            if tau[e] > 0.0:
                Vx[e] = Vx[e] + dt * (V[frm[e]] - Vx[e]) / tau[e]
            else:
                Vx[e] = V[frm[e]]
        for i in range(n):
            dV[i] = -leak[i] * V[i] + bias[i] + (inject[i] if k < inject_steps else 0.0)
        for e in range(m):                                  # each element's current, in order
            x = slope[e] * (Vx[e] - offset[e])
            f = 1.0 / (1.0 + np.exp(-x)) if sig[e] > 0.5 else np.tanh(x)
            if gate[e] >= 0:
                f = f * min(max(V[gate[e]], 0.0), 1.0)
            dV[to[e]] += gain[e] * f
        if settling:
            for i in range(n):
                V[i] = min(max(V[i] + dt * dV[i] / cap[i], lo[i]), hi[i])
                if fixed[i]:
                    V[i] = born[i]
            continue
        for i in range(n):
            if write[i] > 0.0:                                  # a memory: rough only by what is written
                d = dt * dV[i] / cap[i]
                v = V[i] + d
                v = v + write[i] * abs(d) * z[k, i]
            else:
                v = V[i] + dt * dV[i] / cap[i]
                v = v + scale * z[k, i] / cap[i]
            V[i] = min(max(v, lo[i]), hi[i])
            vmax[i] = max(vmax[i], V[i])
            up = armed[i] and V[i] > SPIKE
            spikes[i] += up
            armed[i] = (armed[i] and not up) or V[i] < RESET


class Circuit:
    def __init__(self, seed: int = 0, noise: float = 0.2):
        self.rng, self.noise = np.random.default_rng(seed), noise
        self.nodes, self.elements, self.names, self.start = [], [], [], []
        self.V = None

    def node(self, name: str, bias: float = 0.0, R: float | None = 2.0, C: float = 1.0, lo: float = -np.inf,
             hi: float = np.inf, start: float | None = None, memory: bool = False) -> int:
        """A node; R None: no leak. start: its voltage at birth (else where it settles at rest). memory: a memory node
        (no leak; noisy only when written)."""
        assert not memory or R is None, "a memory node has no leak"
        self.nodes.append((bias, 0.0 if R is None else 1.0 / R, C, lo, hi, WRITE if memory else 0.0))
        self.names.append(name)
        self.start.append(start)
        return len(self.names) - 1

    def element(self, to: int, frm: int, gain: float, offset: float, tau: float = 0.0, slope: float = 1.0,
                sigmoid: bool = False, gate: int = -1) -> int:
        self.elements.append(((gain, offset, slope, tau, float(sigmoid)), (to, frm, gate)))
        return len(self.elements) - 1

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
        """Once built: the arrays the integration runs on, and every node settled at rest."""
        if self.V is not None:
            return
        self.node_arr = np.array(self.nodes, dtype=float).T.copy()
        self.el_arr = np.array([e for e, _ in self.elements], dtype=float).T.copy()
        self.link = np.array([l for _, l in self.elements], dtype=np.int64).T.copy()
        fixed = np.array([v is not None for v in self.start])
        self.V = np.array([-3.0 if v is None else v for v in self.start])
        self.V = np.minimum(np.maximum(self.V, self.node_arr[3]), self.node_arr[4])
        self.Vx = self.V[self.link[1]].copy()
        self.armed = np.ones(len(self.names), dtype=np.bool_)
        self.spikes = np.zeros(len(self.names), dtype=np.int64)
        self.vmax = np.full(len(self.names), -np.inf)
        _run(self.V, self.Vx, self.armed, self.spikes, self.vmax, np.zeros(len(self.names)), 0, self.node_arr,
             self.el_arr, self.link, np.zeros((0, 0)), 0.0, DT, int(SETTLE / DT), fixed, self.V.copy())

    def tick(self, inject, ticks: int = 1) -> np.ndarray:
        """Runs this many ticks, with these currents injected into the nodes during the first (a pulse one tick long);
        how many times each node spiked. Afterwards vmax holds each node's highest voltage over them."""
        self._ready()
        per = int(round(1 / DT))
        self.spikes[:] = 0
        self.vmax[:] = -np.inf
        z = self.rng.standard_normal((per * ticks, len(self.names)))
        _run(self.V, self.Vx, self.armed, self.spikes, self.vmax, np.asarray(inject, dtype=float), per, self.node_arr,
             self.el_arr, self.link, z, self.noise, DT, per * ticks, NONE, np.zeros(0))
        return self.spikes.copy()
