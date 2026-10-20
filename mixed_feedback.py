"""Mixed-feedback circuits, after Ribar and Sepulchre, "Neuromorphic Control" (2021): every circuit is nodes and one
kind of element.

  A node is a capacitor: C dV/dt = (bias - V / R) + (the currents of the elements into it) + (the pulses into it),
  where bias - V / R is its leak, a resistor to its rest voltage bias x R (with no leak, bias is a steady current); it
  may be clamped between two voltages (diodes to two rails). An element puts a current into one node,
  gain x f(slope x (Vx - offset)), from a node's voltage Vx (its own: an ion channel; another's: a synapse), low-pass
  filtered with time constant tau (0: at once). f is tanh (an ion channel) or the logistic sigmoid (a synapse). An
  element may be gated by a third node: its current is then also multiplied by that node's voltage, clipped to 0..1
  (an amplifier whose bias current a voltage sets). Its sign sets the feedback: an element on its own node with
  positive gain is positive feedback (it makes the node switch), with negative gain negative feedback (it restores
  it); the timescales at which each acts set the behaviour (an excitable neuron: fast positive feedback, slow
  negative). A memory node (a floating gate or memristor, or a synapse's weight) has no leak and no membrane.

Noise and mismatch are as biology (and subthreshold silicon) make them, and built in here, where no circuit, brain or
search can turn them off (the user's decision, 2026-10-20; the reasoning in LESSONS.md, Noise as biology makes it):

  Shot noise: every current is carried by discrete events (channels opening, vesicles released, electrons crossing a
  transistor's barrier), so each device's current I carries noise of variance SHOT x |I| per tick. It is summed over
  every device on a node, gross, not net (two big currents that cancel still flicker), the body's pulses included.
  Raising a node's currents to drown its noise works only as the square root, and costs power in proportion.
  Membrane noise: a node's capacitance is membrane area, and area holds leak channels that flicker even at rest, so
  every node but a memory adds variance MEMBRANE x C per tick. A node scaled up k times, capacitance and currents
  together (the same behaviour), is quieter only by sqrt(k), for k times the power and area. (A noise fixed per node,
  as before, let the same scaling silence a node for free.)
  A memory node gets only its writers' shot noise: perfectly still while nothing writes it; written, rough by the
  charge moved (variance in proportion to what is written: a weight built of discrete steps). (Before, each step's
  write was rough by a share of itself, which made a memory quieter at a finer step.)
  Both are rates per tick, so the integration step doesn't change them (Euler-Maruyama, noise scaled by sqrt(DT)).
  SHOT and MEMBRANE share the old noise (0.2 per node, which gave the paper's neuron about 6.5 spikes of its own
  per 1,000 ticks; awake cortex fluctuates by about 10-25% of the way from rest to threshold) about equally for the
  standard neuron at rest; a node far from it in size or currents now differs. Circuit(noise=...) scales both, as a
  sensitivity check, only within NOISY.
  Mismatch: no two parts are alike (analogue silicon differs by 10% or more; identified neurons of one type by 2-5
  times, held in shape by homeostasis these circuits lack). Every node's bias, leak and capacitance and every
  element's gain, slope and time constant is off by about MISMATCH of itself, and every offset by about MISMATCH
  volts, drawn once for each part from the circuit's seed when the integration's arrays are built (also for parts
  grown in a life, or changed by growth), so no design can lean on a knife-edge or an exact cancellation.
  Pulses: the body's inputs are charges at moments it gives, anywhere within a tick (pulse()), spread over the steps
  they overlap; never on tick boundaries, which would let a circuit lock to the tick (lockstep).

Time is in ticks, integrated in steps of DT, compiled: one call runs many ticks. A node spikes when its voltage rises
through SPIKE, and can spike again once it has fallen below RESET.
"""

from __future__ import annotations

import numpy as np
from numba import njit

DT = 0.05           # integration step (ticks)
SPIKE, RESET = 0.0, -1.0
SETTLE = 200        # ticks a new circuit runs without noise, to settle at rest
SHOT = 0.005        # shot noise: variance per tick per unit of a device's current
MEMBRANE = 0.02     # membrane noise: variance per tick per unit of a node's capacitance (none on a memory)
NOISY = (0.5, 2.0)  # the noise may be scaled within these (a sensitivity check), never turned off
MISMATCH = 0.1      # every part off by about this share of itself at birth (offsets by this many volts)
RAIL = 3.0          # the supply's rails, +-RAIL (V): power is reckoned against them (an element feeding a node draws
                    # from +RAIL, one draining it sinks to -RAIL)


@njit(cache=True)
def _step(V, Vx, armed, spikes, vmax, drive, node, el, link, z, noise, dt, dV, gross):
    """One integration step, shared by every simulation of a circuit (here and minimal/fastlife.py), so the noise
    can't be left out of one. node: each node's (bias, leak, cap, lo, hi, memory); el: each element's (gain, offset,
    slope, tau, sigmoid); link: each element's (to, from, gate); drive: each node's pulse current in this step; z: a
    standard normal draw for each node. Returns the power the devices dissipate: an element feeding a node,
    |I| x (RAIL - V); one draining it, |I| x (V + RAIL); a leak, its current squared over its conductance (a
    capacitor gives back what it stores)."""
    n, m = V.shape[0], link.shape[1]
    bias, leak, cap, lo, hi, memory = node[0], node[1], node[2], node[3], node[4], node[5]
    gain, offset, slope, tau, sig = el[0], el[1], el[2], el[3], el[4]
    to, frm, gate = link[0], link[1], link[2]
    power = 0.0
    for e in range(m):                                  # each element's input, filtered
        if tau[e] > 0.0:
            Vx[e] = Vx[e] + dt * (V[frm[e]] - Vx[e]) / tau[e]
        else:
            Vx[e] = V[frm[e]]
    for i in range(n):
        I = bias[i] - leak[i] * V[i]                    # the leak (or, with none, a steady current)
        dV[i] = I + drive[i]
        gross[i] = abs(I) + abs(drive[i])
        if leak[i] > 0.0:
            power += I * I / leak[i]
        else:
            power += abs(I) * max(RAIL - V[i] if I > 0.0 else V[i] + RAIL, 0.0)
    for e in range(m):                                  # each element's current, in order
        x = slope[e] * (Vx[e] - offset[e])
        f = 1.0 / (1.0 + np.exp(-x)) if sig[e] > 0.5 else np.tanh(x)
        if gate[e] >= 0:
            f = f * min(max(V[gate[e]], 0.0), 1.0)
        I = gain[e] * f
        dV[to[e]] += I
        gross[to[e]] += abs(I)
        power += abs(I) * max(RAIL - V[to[e]] if I > 0.0 else V[to[e]] + RAIL, 0.0)
    root = noise * np.sqrt(dt)
    for i in range(n):
        var = SHOT * gross[i] + (0.0 if memory[i] > 0.0 else MEMBRANE * cap[i])
        v = V[i] + (dt * dV[i] + root * np.sqrt(var) * z[i]) / cap[i]
        V[i] = min(max(v, lo[i]), hi[i])
        vmax[i] = max(vmax[i], V[i])
        up = armed[i] and V[i] > SPIKE
        spikes[i] += up
        armed[i] = (armed[i] and not up) or V[i] < RESET
    return power


@njit(cache=True)
def _run(V, Vx, armed, spikes, vmax, drive, node, el, link, z, noise, dt, steps):
    """steps integration steps (_step); drive and z: (steps, nodes). Returns the energy dissipated (power x steps)."""
    n = V.shape[0]
    dV, gross = np.empty(n), np.empty(n)
    energy = 0.0
    for k in range(steps):
        energy += _step(V, Vx, armed, spikes, vmax, drive[k], node, el, link, z[k], noise, dt, dV, gross)
    return energy


@njit(cache=True)
def _settle(V, Vx, node, el, link, dt, steps, fixed, born):
    """Birth: steps without noise, pulses or spikes counted, the fixed nodes put back to born after every step."""
    n = V.shape[0]
    dV, gross, zero = np.empty(n), np.empty(n), np.zeros(n)
    armed, spikes, vmax = np.zeros(n, dtype=np.bool_), np.zeros(n, dtype=np.int64), np.zeros(n)
    for k in range(steps):
        _step(V, Vx, armed, spikes, vmax, zero, node, el, link, zero, 0.0, dt, dV, gross)
        for i in range(n):
            if fixed[i]:
                V[i] = born[i]


@njit(cache=True)
def _pulse(drive, node, current, at, length, dt):
    """Adds a pulse of current into node, from `at` to `at + length` (circuit ticks from drive's first step), to
    drive (steps, nodes): each step gets the share of it that falls within the step, so the charge delivered and
    its timing don't depend on the step."""
    k0, k1 = int(at / dt), min(int(np.ceil((at + length) / dt)), drive.shape[0])
    for k in range(k0, k1):
        overlap = min((k + 1) * dt, at + length) - max(k * dt, at)
        if overlap > 0.0:
            drive[k, node] += current * overlap / dt


class Circuit:
    """streams: every node draws its noise from its own stream, seeded by the circuit's seed and the node's index, so
    adding nodes (or growing them in a life) leaves every other node's noise unchanged: the same random numbers for the
    same node in every variant of a brain (common random numbers), so that variants can be compared life for life.
    Without it all nodes draw from one stream, and adding a node reshuffles everyone's noise. Mismatch is drawn for
    each part from its own stream (the seed and its index) either way.
    noise: the noise as a share of its usual, within NOISY (a sensitivity check)."""

    def __init__(self, seed: int = 0, streams: bool = False, noise: float = 1.0):
        assert NOISY[0] <= noise <= NOISY[1], f"the noise can be scaled only within {NOISY}, never turned off"
        self.rng, self.noise, self.seed, self.streams = np.random.default_rng(seed), noise, seed, streams
        self.nodes, self.elements, self.names, self.start = [], [], [], []
        self.node_rng = []
        self.V = None
        self.drive = np.zeros((0, 0))                   # pulses to come: (steps, nodes)
        self.energy, self.steps = 0.0, 0                # watching: what the devices dissipated, over how many steps

    def node(self, name: str, bias: float = 0.0, R: float | None = 2.0, C: float = 1.0, lo: float = -np.inf,
             hi: float = np.inf, start: float | None = None, memory: bool = False) -> int:
        """A node; R None: no leak. start: its voltage at birth (else where it settles at rest). memory: a memory node
        (no leak, no membrane: noisy only when written)."""
        assert not memory or R is None, "a memory node has no leak"
        self.nodes.append((bias, 0.0 if R is None else 1.0 / R, C, lo, hi, float(memory)))
        self.names.append(name)
        self.start.append(start)
        if self.streams:
            self.node_rng.append(np.random.default_rng([self.seed, len(self.names) - 1]))
        return len(self.names) - 1

    def element(self, to: int, frm: int, gain: float, offset: float, tau: float = 0.0, slope: float = 1.0,
                sigmoid: bool = False, gate: int = -1) -> int:
        self.elements.append(((gain, offset, slope, tau, float(sigmoid)), (to, frm, gate)))
        return len(self.elements) - 1

    def redirect(self, e: int, to: int) -> None:
        """Growth: element e now drives node `to` (as when a new unit splits a synapse). grow() makes it count."""
        params, (_, frm, gate) = self.elements[e]
        self.elements[e] = (params, (to, frm, gate))

    def regate(self, e: int, gate: int) -> None:
        """Growth: element e is now gated by node `gate` (so something can turn it down). grow() makes it count."""
        params, (to, frm, _) = self.elements[e]
        self.elements[e] = (params, (to, frm, gate))

    def _arrays(self) -> None:
        """The arrays the integration runs on: every part as built, mismatched (MISMATCH), each by draws of its own."""
        node = np.array(self.nodes, dtype=float).T.copy()
        for i in range(node.shape[1]):
            d = np.random.default_rng([self.seed, 7, i]).standard_normal(3)
            node[:3, i] *= 1.0 + MISMATCH * d                   # bias, leak, capacitance
        el = np.array([e for e, _ in self.elements], dtype=float).reshape(-1, 5).T.copy()
        for j in range(el.shape[1]):
            d = np.random.default_rng([self.seed, 8, j]).standard_normal(4)
            el[0, j] *= 1.0 + MISMATCH * d[0]                   # gain
            el[1, j] += MISMATCH * d[1]                         # offset (volts)
            el[2, j] *= 1.0 + MISMATCH * d[2]                   # slope
            el[3, j] *= 1.0 + MISMATCH * d[3]                   # time constant
        self.node_arr, self.el_arr = node, el
        self.link = np.array([l for _, l in self.elements], dtype=np.int64).reshape(-1, 3).T.copy()

    def grow(self) -> None:
        """Growth, during a life: after nodes or elements were added, or an element redirected, rebuild the arrays the
        integration runs on, keeping every existing node's and element's state. A new node starts at its start voltage,
        or else where its leak alone would rest it (bias x R; 0 with no leak); a new element's filtered input starts at
        its source's voltage."""
        if self.V is None:
            return
        n0, m0 = len(self.V), len(self.Vx)
        self._arrays()
        bias, leak, lo, hi = self.node_arr[0], self.node_arr[1], self.node_arr[3], self.node_arr[4]
        born = [self.start[i] if self.start[i] is not None else (bias[i] / leak[i] if leak[i] > 0 else 0.0)
                for i in range(n0, len(self.names))]
        self.V = np.concatenate([self.V, np.minimum(np.maximum(np.array(born, dtype=float), lo[n0:]), hi[n0:])])
        self.Vx = np.concatenate([self.Vx, self.V[self.link[1, m0:]]])
        grown = len(self.names) - n0
        self.armed = np.concatenate([self.armed, np.ones(grown, dtype=np.bool_)])
        self.spikes = np.concatenate([self.spikes, np.zeros(grown, dtype=np.int64)])
        self.vmax = np.concatenate([self.vmax, np.full(grown, -np.inf)])
        self.drive = np.concatenate([self.drive, np.zeros((len(self.drive), grown))], axis=1)

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
        self._arrays()
        n = len(self.names)
        fixed = np.array([v is not None for v in self.start])
        self.V = np.array([-3.0 if v is None else v for v in self.start])
        self.V = np.minimum(np.maximum(self.V, self.node_arr[3]), self.node_arr[4])
        self.Vx = self.V[self.link[1]].copy()
        _settle(self.V, self.Vx, self.node_arr, self.el_arr, self.link, DT, int(SETTLE / DT), fixed, self.V.copy())
        self.armed = np.ones(n, dtype=np.bool_)
        self.spikes = np.zeros(n, dtype=np.int64)
        self.vmax = np.full(n, -np.inf)
        self.drive = np.zeros((self.drive.shape[0], n))

    def pulse(self, node: int, current: float, at: float, length: float = 1.0) -> None:
        """A pulse of current into node, starting `at` circuit ticks after the next tick() begins (any time, not a
        whole number), lasting `length` circuit ticks; it may run on into later ticks."""
        self._ready()
        need = int(np.ceil((at + length) / DT)) + 1
        if need > len(self.drive):
            self.drive = np.concatenate([self.drive, np.zeros((need - len(self.drive), len(self.names)))])
        _pulse(self.drive, node, current, at, length, DT)

    def tick(self, ticks: int = 1) -> np.ndarray:
        """Runs this many ticks, with the pulses given (pulse()); how many times each node spiked. Afterwards vmax
        holds each node's highest voltage over them, and last_charge the charge the pulses brought into each node."""
        self._ready()
        steps = int(round(1 / DT)) * ticks
        n = len(self.names)
        self.spikes[:] = 0
        self.vmax[:] = -np.inf
        if self.streams:
            z = np.empty((steps, n))
            for i, g in enumerate(self.node_rng):
                z[:, i] = g.standard_normal(steps)
        else:
            z = self.rng.standard_normal((steps, n))
        if len(self.drive) < steps:
            self.drive = np.concatenate([self.drive, np.zeros((steps - len(self.drive), n))])
        drive, self.drive = self.drive[:steps], self.drive[steps:].copy()
        self.last_charge = drive.sum(axis=0) * DT
        self.energy += _run(self.V, self.Vx, self.armed, self.spikes, self.vmax, np.ascontiguousarray(drive),
                            self.node_arr, self.el_arr, self.link, z, self.noise, DT, steps)
        self.steps += steps
        return self.spikes.copy()
