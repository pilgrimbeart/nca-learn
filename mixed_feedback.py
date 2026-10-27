"""Mixed-feedback circuits, after Ribar and Sepulchre, "Neuromorphic Control" (2021): every circuit is nodes and one
kind of element. Everything is in SI units (units.py, where the axioms behind every number below are).

  A node is a capacitor: C dV/dt = (bias - V / R) + (the currents of the elements into it) + (the pulses into it),
  where bias - V / R is its leak, a resistor to its rest voltage bias x R (with no leak, bias is a steady current); it
  may be clamped between two voltages (diodes to two rails). An element puts a current into one node,
  gain x f(slope x (Vx - offset)), from a node's voltage Vx (its own: an ion channel; another's: a synapse), low-pass
  filtered with time constant tau (0: at once). f is tanh (an ion channel) or the logistic sigmoid (a synapse). An
  element may be gated by a third node: its current is then also multiplied by that node's voltage over the circuit's
  typical voltage, clipped to 0..1 (an amplifier whose bias current a voltage sets). Its sign sets the feedback: an element on its own node with
  positive gain is positive feedback (it makes the node switch), with negative gain negative feedback (it restores
  it); the timescales at which each acts set the behaviour (an excitable neuron: fast positive feedback, slow
  negative). A memory node (a floating gate or memristor, or a synapse's weight) has no leak and no membrane.

Noise and mismatch are built in here, where no circuit, brain or search can turn them off (the user's decision,
2026-10-20; the reasoning in NOTEBOOK.md, Noise as biology makes it). The noise is a substrate's, one of SUBSTRATES
(the user's decision, 2026-10-22: judged in silicon, in biology and at twice biology's noise), each derived from the
physics of what carries its currents (units.py):

  Shot noise: every current is carried by discrete events (channels opening, vesicles released, electrons crossing a
  transistor's barrier), so each device's current I carries noise of variance q x |I| per second, q the charge one
  event carries: about 78,000 electrons' worth in biology (Q_BIO, calibrated), one electron in silicon. It is summed
  over every device on a node, gross, not net (two big currents that cancel still flicker), the body's pulses
  included. Raising a node's currents to drown its noise works only as the square root, and costs power in proportion.
  Resting noise, which a node has even when no net current flows: in biology, membrane noise (a node's capacitance is
  membrane area, and area holds channels that flicker at rest: the shot noise of a resting current J_REST per farad,
  so every node but a memory adds variance Q_BIO x J_REST x C per second; a node scaled up k times, capacitance and
  currents together, the same behaviour, is quieter only by sqrt(k), for k times the power and area); in silicon, the
  thermal noise of a node's leak (variance 2 k T / R per second), a capacitor's own being negligible.
  A memory node gets only its writers' shot noise: perfectly still while nothing writes it; written, rough by the
  charge moved (variance in proportion to what is written: a weight built of discrete steps).
  Biology's two numbers scale with a circuit's typical voltage (units.V_CAL), so that a circuit scaled to another
  supply, voltages and currents together, is as noisy beside its signals; silicon's are physics, and don't.
  Both are rates per second, so the integration step doesn't change them (Euler-Maruyama, noise scaled by sqrt(DT)).
  Biology's two numbers are calibrated together: the standard neuron (neuron(), at rest, its parts as designed) fires
  on its own about twice a second, as cortical neurons at rest do (mismatched, some fire more, and some oscillate), its membrane fluctuating by about 10-25% of the way from rest to
  threshold, as awake cortex does; each gives about half its noise. Silicon, at these currents, is about 280 times
  quieter in amplitude: far below biology, so a design that needs noise to work fails there.
  Mismatch: no two parts are alike (analogue silicon differs by 10% or more; identified neurons of one type by 2-5
  times, held in shape by homeostasis these circuits lack). Every node's bias, leak and capacitance and every
  element's gain, slope and time constant is off by about MISMATCH of itself, and every offset by about MISMATCH
  typical voltages, drawn once for each part from the circuit's seed when the integration's arrays are built (also for parts
  grown in a life, or changed by growth), so no design can lean on a knife-edge or an exact cancellation.
  Pulses: the body's inputs are charges at moments it gives, anywhere within a tick (pulse()), spread over the steps
  they overlap; never on tick boundaries, which would let a circuit lock to the tick (lockstep).

Time is in seconds, integrated in steps of DT, compiled: one call runs many steps. A node spikes when its voltage
rises through SPIKE, and can spike again once it has fallen a typical voltage below it.
"""

from __future__ import annotations

import numpy as np
from numba import njit

import chip
from units import C_TYP, DT, J_REST, K_B, LOUDER, MISMATCH, PULSE, Q_BIO, Q_SI, R_TYP, SUPPLY, T, T_TYP, V_CAL, V_TYP

SPIKE = 0.0                 # V: a node spikes rising through this; it can spike again once below -1 typical voltage
SETTLE = 0.5                # s a new circuit runs without noise, to settle at rest
SUBSTRATES = {              # name: (the charge one event of shot noise carries, a node's resting noise per second from
                            # its capacitance, its leak's conductance and whether it is a memory), at a circuit's typical
                            # voltage v (biology's scaled with it: units.V_CAL; silicon's is physics)
    "silicon": (lambda v: Q_SI, lambda cap, leak, memory, v: 0.0 if memory else 2 * K_B * T * leak),
    "biology": (lambda v: Q_BIO * v / V_CAL, lambda cap, leak, memory, v: 0.0 if memory else
                Q_BIO * J_REST * cap * (v / V_CAL) ** 2),
    "biology x2": (lambda v: LOUDER ** 2 * Q_BIO * v / V_CAL, lambda cap, leak, memory, v: 0.0 if memory else
                   LOUDER ** 2 * Q_BIO * J_REST * cap * (v / V_CAL) ** 2),
}
HALF = SUPPLY / 2           # V: the supply's rails, +-HALF about analogue ground (chip.py: power is what they deliver)


@njit(cache=True)
def _fade(d, knee):
    """How much of an output's current is left d volts from the rail it comes from (chip.KNEE_P, KNEE_N; knee 0: all)."""
    if knee <= 0.0:
        return 1.0
    return 1.0 - np.exp(-max(d, 0.0) / knee)


@njit(cache=True)
def _step(V, Vx, armed, spikes, vmax, drive, node, el, link, z, q, rest, dt, dV, gross, cfg):
    """One integration step, shared by every simulation of a circuit (here and minimal/fastlife.py), so the noise
    can't be left out of one. node: each node's (bias, leak, cap, lo, hi, memory); el: each element's (gain, offset,
    slope, tau, sigmoid); link: each element's (to, from, gate); drive: each node's pulse current in this step; z: a
    standard normal draw for each node; q, rest: the substrate's charge per event of shot noise and each node's resting
    noise per second (SUBSTRATES); cfg: the circuit's (volt, still, half, kp, kn, dead) (Circuit.cfg): volt its typical
    voltage (a gate is open at it, a spike resets below minus it); still its static power (chip.still); half its
    supply's rails, +-half; kp, kn how an output's current
    fades near the rail it comes from (chip.KNEE_P, KNEE_N: a bias or an element sourcing from +half through pMOS,
    sinking to -half through nMOS; 0: not at all); dead the share of a write's full current below which a memory's
    driver doesn't fire (chip.DEAD; 0: none). Returns the power the supply delivers (chip.py): still; a bias from
    its rail, |I| x (half -+ V); a leak through its resistor to analogue ground, V^2 x leak, and the ground's net current
    to a rail; an element's current into a node from +half or out of it to -half, and its pair and mirrors' currents
    that depend on its input or gate, across the supply (a capacitor gives back what it stores)."""
    n, m = V.shape[0], link.shape[1]
    bias, leak, cap, lo, hi, memory = node[0], node[1], node[2], node[3], node[4], node[5]
    gain, offset, slope, tau, sig = el[0], el[1], el[2], el[3], el[4]
    to, frm, gate = link[0], link[1], link[2]
    volt, still, half, kp, kn, dead = cfg[0], cfg[1], cfg[2], cfg[3], cfg[4], cfg[5]
    power, ground, supply = still, 0.0, 2.0 * half
    for e in range(m):                                  # each element's input, filtered
        if tau[e] > 0.0:
            Vx[e] = Vx[e] + dt * (V[frm[e]] - Vx[e]) / tau[e]
        else:
            Vx[e] = V[frm[e]]
    for i in range(n):
        b = bias[i] * (_fade(half - V[i], kp) if bias[i] > 0.0 else _fade(V[i] + half, kn))
        I = b - leak[i] * V[i]                          # the leak (or, with none, a steady current)
        dV[i] = I + drive[i]
        gross[i] = abs(I) + abs(drive[i])
        power += abs(b) * max(half - V[i] if b > 0.0 else V[i] + half, 0.0)
        power += leak[i] * V[i] * V[i]
        ground += leak[i] * V[i]
    for e in range(m):                                  # each element's current, in order
        x = slope[e] * (Vx[e] - offset[e])
        f = 1.0 / (1.0 + np.exp(-x)) if sig[e] > 0.5 else np.tanh(x)
        full = abs(gain[e])                             # the pair's tail current
        if gate[e] >= 0:
            g = min(max(V[gate[e]] / volt, 0.0), 1.0)
            f = f * g
            full = full * g
            power += 2.0 * full * supply                # the pair and its tail's reference, as the gate opens
        k = to[e]
        vo = 0.0 if memory[k] > 0.0 else V[k]           # (a memory is written by tunnelling: the write's output sits
        fu, fd = _fade(half - vo, kp), _fade(vo + half, kn)     # at analogue ground, chip.py)
        if sig[e] > 0.5:
            I = gain[e] * f * (fu if gain[e] > 0.0 else fd)
            if gain[e] < 0.0:
                power += abs(gain[e] * f) * supply      # the second mirror, to sink
        else:                                           # a tanh: its branches, (1 +- w) / 2 of the tail, one sourced,
            w = gain[e] * f / full if full > 0.0 else 0.0   # the other sunk, each fading near its rail
            src, snk = full * (1.0 + w) / 2 * fu, full * (1.0 - w) / 2 * fd
            I = src - snk
            power += (full * (1.0 - w) / 2 + min(src, snk)) * supply    # the sunk branch's mirror, and what cancels
        if memory[k] > 0.0:                             # a memory: tunnelling only above the driver's threshold
            I = np.sign(I) * max(abs(I) - dead * abs(gain[e]), 0.0)
        dV[k] += I
        gross[k] += abs(I)
        power += abs(I) * max(half - vo if I > 0.0 else vo + half, 0.0)
    for i in range(n):
        var = (q * gross[i] + rest[i]) * dt               # the charge's variance over the step
        v = V[i] + (dt * dV[i] + np.sqrt(var) * z[i]) / cap[i]
        V[i] = min(max(v, lo[i]), hi[i])
        vmax[i] = max(vmax[i], V[i])
        up = armed[i] and V[i] > SPIKE
        spikes[i] += up
        armed[i] = (armed[i] and not up) or V[i] < -volt
    return power + abs(ground) * half


@njit(cache=True)
def _run(V, Vx, armed, spikes, vmax, drive, node, el, link, z, q, rest, dt, steps, cfg):
    """steps integration steps (_step); drive and z: (steps, nodes). Returns the power summed over the steps."""
    n = V.shape[0]
    dV, gross = np.empty(n), np.empty(n)
    power = 0.0
    for k in range(steps):
        power += _step(V, Vx, armed, spikes, vmax, drive[k], node, el, link, z[k], q, rest, dt, dV, gross, cfg)
    return power


@njit(cache=True)
def _settle(V, Vx, node, el, link, dt, steps, fixed, born, cfg):
    """Birth: steps without noise, pulses or spikes counted, the fixed nodes put back to born after every step."""
    n = V.shape[0]
    dV, gross, zero = np.empty(n), np.empty(n), np.zeros(n)
    armed, spikes, vmax = np.zeros(n, dtype=np.bool_), np.zeros(n, dtype=np.int64), np.zeros(n)
    for k in range(steps):
        _step(V, Vx, armed, spikes, vmax, zero, node, el, link, zero, 0.0, zero, dt, dV, gross, cfg)
        for i in range(n):
            if fixed[i]:
                V[i] = born[i]


@njit(cache=True)
def _pulse(drive, node, current, at, length, dt):
    """Adds a pulse of current into node, from `at` to `at + length` (seconds from drive's first step), to
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
    substrate: whose noise, one of SUBSTRATES. volt: its typical voltage (units.V_TYP; the recruitment line's
    circuits, drawn before the supply was fixed, at 1 V: brains/circuit.py), which offsets' mismatch, a gate's opening,
    a spike's reset and biology's noise scale with. on_chip: on the chip's supply (units.SUPPLY), its outputs fading
    near the rails (chip.KNEE_P, KNEE_N); else (the recruitment line, not yet built in transistors) its power reckoned
    against rails at 3 typical voltages, and no output fades."""

    def __init__(self, seed: int = 0, streams: bool = False, substrate: str = "biology", volt: float = V_TYP,
                 on_chip: bool = True):
        assert substrate in SUBSTRATES, f"the noise is a substrate's, one of {tuple(SUBSTRATES)}, never turned off"
        self.rng, self.substrate, self.seed, self.streams = np.random.default_rng(seed), substrate, seed, streams
        self.volt, self.on_chip = volt, on_chip
        self.q = SUBSTRATES[substrate][0](volt)
        self.nodes, self.elements, self.names, self.start = [], [], [], []
        self.node_rng = []
        self.V = None
        self.drive = np.zeros((0, 0))                   # pulses to come: (steps, nodes)
        self.power_sum, self.steps = 0.0, 0             # watching: the devices' power summed over the steps, and how many

    def node(self, name: str, bias: float = 0.0, R: float | None = 2 * R_TYP, C: float = C_TYP, lo: float = -np.inf,
             hi: float = np.inf, start: float | None = None, memory: bool = False) -> int:
        """A node: bias in A, R in ohms (None: no leak), C in F, lo, hi and start in V. start: its voltage at birth (else
        where it settles at rest). memory: a memory node (no leak, no membrane: noisy only when written)."""
        assert not memory or R is None, "a memory node has no leak"
        self.nodes.append((bias, 0.0 if R is None else 1.0 / R, C, lo, hi, float(memory)))
        self.names.append(name)
        self.start.append(start)
        if self.streams:
            self.node_rng.append(np.random.default_rng([self.seed, len(self.names) - 1]))
        return len(self.names) - 1

    def element(self, to: int, frm: int, gain: float, offset: float, tau: float = 0.0, slope: float = 1.0,
                sigmoid: bool = False, gate: int = -1) -> int:
        """An element: gain in A, offset in V, tau in s (0: unfiltered), slope per volt. A gate opens from 0 to volt."""
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
        """The arrays the integration runs on: every part as built, mismatched (MISMATCH), each by draws of its own;
        and each node's resting noise in this substrate, from its parts as mismatched."""
        node = np.array(self.nodes, dtype=float).T.copy()
        for i in range(node.shape[1]):
            d = np.random.default_rng([self.seed, 7, i]).standard_normal(3)
            node[:3, i] *= 1.0 + MISMATCH * d                   # bias, leak, capacitance
        el = np.array([e for e, _ in self.elements], dtype=float).reshape(-1, 5).T.copy()
        for j in range(el.shape[1]):
            d = np.random.default_rng([self.seed, 8, j]).standard_normal(4)
            el[0, j] *= 1.0 + MISMATCH * d[0]                   # gain
            el[1, j] += MISMATCH * d[1] * self.volt             # offset (typical voltages)
            el[2, j] *= 1.0 + MISMATCH * d[2]                   # slope
            el[3, j] *= 1.0 + MISMATCH * d[3]                   # time constant
        self.node_arr, self.el_arr = node, el
        self.link = np.array([l for _, l in self.elements], dtype=np.int64).reshape(-1, 3).T.copy()
        rest = SUBSTRATES[self.substrate][1]
        self.rest = np.array([rest(node[2, i], node[1, i], node[5, i] > 0, self.volt) for i in range(node.shape[1])])
        half = HALF if self.on_chip else 3 * self.volt
        self.still = chip.still(node, el, self.link, 2 * half)
        self.cfg = np.array([self.volt, self.still, half, chip.KNEE_P * self.on_chip, chip.KNEE_N * self.on_chip,
                             chip.DEAD * self.on_chip])

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

    def unit(self) -> float:
        """A typical current at this circuit's typical voltage (A): it moves a typical capacitor that far in a typical
        time."""
        return C_TYP * self.volt / T_TYP

    def neuron(self, name: str, bias: float | None = None, tau: float = 10 * T_TYP, strength: float | None = None) -> int:
        """An excitable neuron: fast positive feedback (it fires), slow negative feedback (it recovers, over tau). At
        rest below its threshold, a pulse above it gives one spike; noise gives the odd spike of its own. bias,
        strength: by default -1.6 and 2 typical currents (unit)."""
        bias = -1.6 * self.unit() if bias is None else bias
        strength = 2 * self.unit() if strength is None else strength
        n = self.node(name, bias)
        self.element(n, n, strength, -1.5 * self.volt, slope=1.0 / self.volt)   # fast: positive feedback, all-or-none
        self.element(n, n, -strength, -1.5 * self.volt, tau=tau, slope=1.0 / self.volt)  # slow: negative, recovery
        return n

    def synapse(self, to: int, frm: int, weight: float, tau: float = 0.5 * T_TYP, slope: float | None = None) -> int:
        """A current (weight, in A) into `to` while `frm` spikes (excitatory if weight > 0); slope by default 5 per
        typical voltage."""
        slope = 5.0 / self.volt if slope is None else slope
        return self.element(to, frm, weight, SPIKE, tau=tau, slope=slope, sigmoid=True)

    def _ready(self):
        """Once built: the arrays the integration runs on, and every node settled at rest."""
        if self.V is not None:
            return
        self._arrays()
        n = len(self.names)
        fixed = np.array([v is not None for v in self.start])
        self.V = np.array([-3 * self.volt if v is None else v for v in self.start])
        self.V = np.minimum(np.maximum(self.V, self.node_arr[3]), self.node_arr[4])
        self.Vx = self.V[self.link[1]].copy()
        _settle(self.V, self.Vx, self.node_arr, self.el_arr, self.link, DT, int(round(SETTLE / DT)), fixed,
                self.V.copy(), self.cfg)
        self.armed = np.ones(n, dtype=np.bool_)
        self.spikes = np.zeros(n, dtype=np.int64)
        self.vmax = np.full(n, -np.inf)
        self.drive = np.zeros((self.drive.shape[0], n))

    def pulse(self, node: int, current: float, at: float, length: float = PULSE) -> None:
        """A pulse of current (A) into node, starting `at` seconds after the next run() begins (any time, not a whole
        number of steps), lasting `length` seconds; it may run on into later runs."""
        self._ready()
        need = int(np.ceil((at + length) / DT)) + 1
        if need > len(self.drive):
            self.drive = np.concatenate([self.drive, np.zeros((need - len(self.drive), len(self.names)))])
        _pulse(self.drive, node, current, at, length, DT)

    def run(self, seconds: float) -> np.ndarray:
        """Runs for this long (a whole number of steps), with the pulses given (pulse()); how many times each node
        spiked. Afterwards vmax holds each node's highest voltage over the run, and last_charge the charge (C) the
        pulses brought into each node."""
        self._ready()
        steps = int(round(seconds / DT))
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
        self.power_sum += _run(self.V, self.Vx, self.armed, self.spikes, self.vmax, np.ascontiguousarray(drive),
                               self.node_arr, self.el_arr, self.link, z, self.q, self.rest, DT, steps, self.cfg)
        self.steps += steps
        return self.spikes.copy()

    def power(self) -> float:
        """Watching: the devices' mean power (W) so far."""
        return self.power_sum / max(self.steps, 1)
