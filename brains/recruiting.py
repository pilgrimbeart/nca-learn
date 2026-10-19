"""The recruiting circuit: the knowing circuit (brains/knowing.py), which may know what predicts pain but can't act on
it, plus the machinery to grow, in its life, the link that lets that knowledge change what the creature does (rung 1,
RECRUITMENT.md). All circuit, except growth itself, the one declared primitive: a new unit appears when a sprout
node's voltage passes GROW, attached where that sprout is.

  Frustration F, at the taste neuron: a slow node charged at a bad taste while the taste neuron had fired just before
  it ("I predicted this pain, and it came anyway"), through an amplifier from the taste node gated by T's
  eligibility E_T, charged by T's spikes. (T's innate answer to the taste itself comes too late to count: only
  anticipation does; E2.) F fades over FRUSTRATION ticks.
  Help, routed back along T's input synapses: for each sensor s a node h_s, charged while F is high through an
  amplifier gated by W_s, the strength of s's synapse onto T, so the sensor whose activity predicted the pain hears
  most. (route=False: gated by nothing, so both sensors hear alike: an ablation.)
  Sprouts: each of a sensor's output synapses has a sprout node, charged while its sensor's help is high. The sprouts
  of one sensor inhibit each other, so one wins (compete=False: they don't: an ablation). A synapse that carries help
  back (onto T) doesn't sprout.
  Growth (the primitive): when a sprout passes GROW its synapse is split by a bridge: a neuron relaying the sensor's
  spikes on to the motor, held down (a hold node, fading over HOLD ticks) while that sensor's own spikes come with a
  strong synapse onto T, "my activity predicts pain". So when the poison sensor fires it drives only its other motor,
  and the creature veers. Everything the bridge connects to is on the synapses of the sensor it grew from, so the
  growth rule needs to know nothing else (E7; hold="T", E1-E6's version, charged the hold by T's spikes instead, so
  growth had to know T, and the creature veered at T's false alarms too: 0.11 net food per 1,000 ticks worse). A
  bridge passes the signal unchanged until it is held: inserting it changes nothing by itself.
  Found by experiment (experiments/NOTEBOOK.md), and on by default: sharp, help only to a sensor that predicts pain
  (its synapse onto T past 1/2) and only while frustrated (a flag node, F past 1/2), a logical AND rather than help in
  proportion to W; once, a bridge brings a memory node that keeps its neuron's other sprouts down: one bridge per
  neuron. (sharp=False gives help in proportion to W, and once=False lets a neuron sprout again: E3's design.)
  Slow nodes are quiet nodes: every node gets the same noise current, so a node integrating over tau circuit ticks
  with capacitance C wanders by about NOISE x sqrt(tau / 2) / C; each slow node's C is chosen to keep that near QUIET
  (C grows as the square root of its time), its R to give its time, and the gains into it scaled with C to give its
  rates.
"""

from __future__ import annotations

import numpy as np

from brains.knowing import KnowingBrain
from brains.circuit import INHIBIT, SIDE, SPEED
from mixed_feedback import Circuit

GUARD = 0.0         # a slow element by which T's spikes could reach E_T (circuit ticks), to keep T's innate answer
                    # to a taste out of F: unneeded (E2: that answer comes too late to count anyway), and a cost
FRUSTRATION = 3000.0    # ticks over which frustration fades
FRUSTRATE = 0.5     # how far one anticipated pain raises F (0..1), with T fully eligible: F settles near rate x this x
                    # FRUSTRATION x eligibility, above 1/2 at the knowing circuit's rate of poison meals and below it
                    # once a bridge cuts that rate (E2; 0.5 rather than 0.3 brings growth earlier: E5b, confirmed in E6)
HELP = 100.0        # ticks over which a sensor's help fades
HELP_RATE = 0.005   # how fast a sensor's help rises while F is high (at W = 1), per circuit tick
SPROUT = 200.0      # ticks over which a sprout fades
SPROUT_RATE = 0.005  # how fast a sprout rises while its sensor's help is high, per circuit tick
RIVAL = 0.02        # how fast a sprout that is ahead empties its rivals, per circuit tick
ELIGIBLE_T = 10.0   # ticks over which the taste neuron's eligibility fades
GROW = 0.6          # a sprout this high grows its bridge (the growth primitive; E5b, E6)
HOLD = 10.0         # ticks over which a bridge stays held down after the taste neuron fires
QUIET = 0.02        # how far noise may move a slow node (voltage, steady state)
PAINFUL = -0.8      # the taste node below this is a bad taste, for frustration (a bad taste takes it to about -1.3;
                    # its own noise, about 0.1, mustn't reach it, or F integrates the leaks over thousands of ticks)


class RecruitingBrain(KnowingBrain):
    def __init__(self, seed: int, grow: bool = True, route: bool = True, compete: bool = True,
                 guard: float = GUARD, grow_at: float = GROW, learn: bool = True, frustrate: float = FRUSTRATE,
                 sharp: bool = True, once: bool = True, hold: str = "sensor"):
        self.grow_on, self.route, self.compete, self.guard, self.grow_at = grow, route, compete, guard, grow_at
        self.frustrate, self.sharp, self.once, self.hold_from = frustrate, sharp, once, hold
        if not learn:
            self.learning_step = 0.0                    # an experiment: T can't learn what predicts pain
        self.bridges, self.t = [], 0                    # measuring: (tick, sensor, motor) of each bridge grown
        super().__init__(seed)

    @staticmethod
    def slow(c: Circuit, name: str, ticks: float) -> tuple:
        """A quiet slow node fading over this many world ticks, 0..1: (node, its capacitance)."""
        tau = ticks * SPEED                             # in circuit ticks
        C = c.noise * np.sqrt(tau / 2.0) / QUIET
        return c.node(name, R=tau / C, C=C, lo=0.0, hi=1.0), C

    def build(self, c: Circuit) -> None:
        super().build(c)
        self.E_T, C = self.slow(c, "E_T", ELIGIBLE_T)
        c.element(self.E_T, self.T, 1.0 * C, 0.0, tau=self.guard, slope=5.0, sigmoid=True)    # T's spike charges it
        self.F, C = self.slow(c, "F", FRUSTRATION)
        c.element(self.F, self.taste_node, self.frustrate * C / 1.3, PAINFUL, slope=-20.0, sigmoid=True,
                  gate=self.E_T)
        self.help, self.sprout = {}, {}
        if self.sharp:                                  # a flag: F past 0.5, frustrated
            self.frustrated, C = self.slow(c, "frustrated", 2.0)
            c.element(self.frustrated, self.F, 1.0 * C, 0.5, slope=20.0, sigmoid=True)
        for s in self.sensors:
            h, C = self.slow(c, f"h{c.names[s]}", HELP)
            if self.sharp:                              # help iff this sensor predicts pain (W past 1/2) and frustrated
                c.element(h, self.W[s], HELP_RATE * C, 0.5, slope=20.0, sigmoid=True, gate=self.frustrated)
            else:                                       # help in proportion to W, while F is past 0.5
                c.element(h, self.F, HELP_RATE * C, 0.5, slope=20.0, sigmoid=True,
                          gate=self.W[s] if self.route else -1)
            self.help[s] = h
            for m in self.motors:                       # the synapse onto T carries the help back: no sprout
                x, C = self.slow(c, f"x{c.names[s]}{c.names[m]}", SPROUT)
                c.element(x, h, SPROUT_RATE * C, 0.5, slope=20.0, sigmoid=True)
                self.sprout[(s, m)] = (x, C)
            if self.compete:
                (xa, Ca), (xb, Cb) = [self.sprout[(s, m)] for m in self.motors]
                c.element(xa, xb, -RIVAL * Ca, 0.4, slope=20.0, sigmoid=True)
                c.element(xb, xa, -RIVAL * Cb, 0.4, slope=20.0, sigmoid=True)
        self.sprout = {k: x for k, (x, _) in self.sprout.items()}
        self.grown = set()

    def step(self) -> list:
        spikes = self._tick()
        self.t += 1
        if self.grow_on:                                # growth: the one primitive beside the circuit
            for (s, m), x in self.sprout.items():
                if (s, m) not in self.grown and self.circuit.V[x] > self.grow_at:
                    self.insert_bridge(s, m)
        return self._motors(spikes)

    def insert_bridge(self, s: int, m: int) -> None:
        """Split the synapse from sensor s to motor m with a bridge (see above). The growth primitive calls this; so
        may an experimenter (an oracle placing a bridge by hand)."""
        c = self.circuit
        tag = f"{c.names[s]}{c.names[m]}"
        bridge = c.neuron(f"B{tag}")
        hold = c.node(f"H{tag}", R=HOLD * SPEED / 10.0, C=10.0, lo=0.0, hi=1.0)
        c.redirect(self.syn[(s, m)], bridge)                        # the sensor now drives the bridge ...
        self.syn[(s, m)] = c.synapse(m, bridge, SIDE)               # ... which drives the motor
        if self.hold_from == "sensor":                  # local: the sensor's spike, gated by its synapse onto T ...
            c.element(hold, s, 10.0, 0.0, slope=5.0, sigmoid=True, gate=self.W[s])
        else:                                           # ... or T's spike (the growth rule must know T) ...
            c.element(hold, self.T, 10.0, 0.0, slope=5.0, sigmoid=True)
        c.element(bridge, hold, -INHIBIT, 0.5, slope=10.0, sigmoid=True)    # ... which holds the bridge down
        if self.once:                                   # a sprouted neuron is changed: its other sprouts stay down
            done = c.node(f"D{tag}", R=None, lo=0.0, hi=1.0, start=1.0, memory=True)
            for (s2, m2), x in self.sprout.items():
                if s2 == s and m2 != m:
                    c.element(x, done, -1.0 * c.nodes[x][2], 0.5, slope=20.0, sigmoid=True)
        c.grow()
        self.inject = np.concatenate([self.inject, np.zeros(len(c.names) - len(self.inject))])
        self.grown.add((s, m))
        self.bridges.append((self.t, s, m))

    def block_hints(self) -> dict:
        """Watching (blocks.py): where each sprout belongs: on the synapse it may split, or by the bridge it grew."""
        out = {}
        for (s, m), x in self.sprout.items():
            out[x] = ("arrow", (s, m)) if (s, m) not in self.grown else ("near", self._bridge_of(s, m))
        return out

    def _bridge_of(self, s: int, m: int) -> int:
        return self.circuit.names.index(f"B{self.circuit.names[s]}{self.circuit.names[m]}")

    def shown(self) -> list:
        return [("T taste", self.T)] + [(f"bridge {self.circuit.names[s]}-{self.circuit.names[m]}", n)
                                        for (_, s, m), n in zip(self.bridges, self._bridge_nodes())]

    def _bridge_nodes(self) -> list:
        return [self.circuit.names.index(f"B{self.circuit.names[s]}{self.circuit.names[m]}")
                for _, s, m in self.bridges]
