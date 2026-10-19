"""The healing circuit: rung 1 again, with nothing placed for the job (RECRUITMENT.md; experiments/NOTEBOOK.md, H
series). The knowing circuit (its taste neuron T learns what predicts pain but has no outputs) plus a generic way of
recruiting: when a unit is frustrated, a generic recruit grows beside it, attached to it and to every neuron within
one edge of it, and learns for itself which of its possible actions stops the pain. Neither the recruit nor the
growth rule knows what any neuron is or does. All circuit, except growth itself (the one declared primitive).

  Frustration, generic: a unit that can be frustrated has F, a slow level charged by anticipated pain (pain while the
  unit had fired just before: its prediction didn't prevent it), and O, a fast "ouch" pulse at every pain at all.
  Only T receives pain from the body, so only T can be frustrated at first. F triggers recruitment; O is what recruits
  learn from (learning from anticipated pain only would let a recruit "win" by silencing the anticipation instead of
  preventing the pain: wireheading; ouch="anticipated" tries it).
  Growth (the primitive): a unit whose F is past 1/2, with no recruit yet, gets one. A wave-1 recruit attaches to its
  parent and to every neuron within one edge of it; a recruit of a recruit attaches to its parent and to every neuron
  within one edge of anything its parent was attached to, so inflammation spreads one edge per failed wave.
  The recruit: a neuron R; a hold node (R's spikes keep its action on for about HOLD ticks); listening synapses, one
  from each attached neuron, their strengths memory nodes; and a menu of acting options, each enabled by a node of its
  own: inhibit or excite an attached neuron, or turn down one of its ungated output synapses (a gate node that rests
  open and that R's hold closes).
  Listening (listen): "pain", each strength rises when its neuron fired just before an ouch and falls when it fired
  just before a yum (the motif's pulse at every good taste: the same news T itself gets), so R comes to fire at what
  predicts pain; "all", every strength fixed full; "none".
  Choosing (select): "wsls", win-stay, lose-shift: the options' enable nodes rise from nothing, latch, and hold each
  other down (so one wins, by noise), and each has a fatigue node, charged by pain that follows R's action while the
  option is on and eased by a good taste that follows it; a tired option is knocked out and kept out while its fatigue
  fades, and another wins. "all", every option on at once;
  "random", one option fixed at recruitment (noise chooses). "reinforce", graded: every option partly on, its
  strength a memory node jittered up and down by two noise nodes (exploration from the circuit's own noise); a good
  taste after R acts moves each strength the way its jitter went at that moment, a pain the other way (reward-modulated
  perturbation: REINFORCE, node perturbation), so options can blend rather than one winning.
  Early and shadow (the user's idea, against learning from scratch late): grow_at, the frustration at which a recruit
  grows (1/2 by default; lower recruits early); shadow, an early recruit learns what to listen to but acts (and counts
  as having acted, for blaming its options) only while its parent's "frustrated" flag is on (F past 1/2: shadow="flag",
  which withdraws the recruit whenever its help has calmed the parent), or from the first time it comes on
  (shadow="latch": a memory node, commissioned, charged by the flag and never discharged). Inherit
  (listen="inherit"): where the parent already holds a learned memory on its synapse from an attached neuron (T's
  learned strengths from the eyes), the recruit's listening synapse from that neuron is gated by the same memory: it
  starts out knowing what its parent knows; other inputs learn as under "pain".
  Judge (judge): "rate", tiredness fades over REST_TIRED ticks, so it follows the rate of pains (less good tastes) after
  acting, and an option that stops the creature looks like a cure; "share", while the option is on it hardly fades and a
  good taste eases it by GOOD_STEP of a pain's step, so it follows the share of bad tastes after acting; while off it
  fades over about REST_TIRED ticks (an off node, held down by the enable, gates its rest).
  Menu "inputs": as "synapses", but the ungated synapses arriving at attached neurons (a recruit turns down its
  neighbours' inputs): wave 1, on T and the eyes, finds none (T's are learned memories, the eyes have no inputs);
  only a wave that reaches the motors can turn down an eye's synapse to a motor.
  Retire (retire): a recruit acts only while a working node is up; a memory node, retired, charged when its own
  frustration passes the growing threshold, holds working down for good: a recruit that failed hands over and stands
  down (its listening stays, so the next wave can still attach to it). Starve (starve): with judge="share", tiredness
  also creeps up while an option is on, so an option followed by no tastes at all (a freeze) is knocked out.
  Power: the latch, rivalry and knock-out elements are gated by their own source, so they draw current only while it
  is up (ungated, pairwise rivalry was most of a recruit's power).
  Cascade (cascade): a recruit that hasn't helped is frustrated itself, and so may recruit in turn: by default
  (trigger="persist") when its parent is still frustrated about PERSIST ticks after it came (a slow node filling while
  the parent's F is past 1/2, fading when it isn't): "if it can't reduce frustration, it emits frustration";
  trigger="root": the same, but filled while the first frustrated unit's flag is on (T's), for every wave, so a cure
  anywhere stops every wave's frustration at once (a parent's own frustration fades slowly and outlasts a cure);
  trigger="idle": pain while it is idle (an idle node, held down while any option is on: so once every option has
  been tried and knocked out).
"""

from __future__ import annotations

import numpy as np

from brains.circuit import INHIBIT, SPEED, STRONG
from brains.knowing import KnowingBrain
from brains.recruiting import PAINFUL, QUIET, RecruitingBrain
from mixed_feedback import Circuit

FRUSTRATION = 3000.0    # ticks over which frustration fades
FRUSTRATE = 0.5     # how far one anticipated pain raises F, with the unit fully eligible
OUCH = 1.0          # ticks over which an ouch pulse fades (above half for about 3 circuit ticks)
OUCH_ABOVE = 4.5    # circuit ticks an ouch pulse stays above half (measured), to scale what it drives
ELIGIBLE = 10.0     # ticks over which an eligibility fades
HOLD = 10.0         # ticks a recruit's action lasts after it fires
LISTEN_STEP = 0.2   # how far an ouch raises (a yum lowers) a listening strength while its neuron is fully eligible
LISTEN_DECAY = 0.00005  # and how fast it sinks while its neuron is eligible, per circuit tick: an input as often before
                        # good tastes as bad would otherwise wander between its bounds; with this it goes to 0
EXCITE = 1.5        # an exciting action's current
TIRE = 0.15         # how far a pain after acting tires the option that's on (and a good taste after acting rests it)
REST_TIRED = 10000.0    # ticks over which tiredness fades: an option is knocked out if pains follow its action at more
                        # than about TIRED / (TIRE x REST_TIRED) per tick of acting (about 1 in 3,000), between the
                        # untreated rate and a good option's
TIRED = 0.5         # an option this tired is knocked out
STARVE = 40000.0    # starve: an option on this long with no good tastes at all is knocked out (eased by good tastes, so
                    # one followed by fewer than about 1 good taste per STARVE x GOOD_STEP x TIRE / TIRED ticks tires)
REST_SHARE = 100000.0   # judge="share": while its option is on, tiredness hardly fades, so it is moved by tastes, not
GOOD_STEP = 0.5         # time, and follows the share of bad tastes after acting: a good taste eases it by half a pain's
                        # step, so an option followed by more than 1 bad taste in 3 tires, one followed by fewer rests
                        # (doing less changes nothing); while off, it fades over about REST_TIRED ticks
GROW_F = 0.5        # frustration past this grows a recruit
PERSIST = 10000.0   # cascade: ticks of its parent staying frustrated before a recruit is frustrated itself
IDLE_RISE = 500.0   # ticks over which a recruit's idleness builds while no option is on (trigger="idle")
EXHAUSTED = 0.15    # how far a pain while idle raises a recruit's own frustration (sustained exhaustion, not one pain)
REINFORCE_START = 0.2   # select="reinforce": each option's strength at birth ...
REINFORCE_RATE = 0.3    # ... how far an outcome moves it, at full jitter ...
JITTER_TAU, JITTER_C = 10.0, 3.0   # ... and its jitter: noise nodes fading over this many ticks, capacitance chosen so
                                   # they wander by about 0.3 (0.2 x sqrt(tau / 2) / C)


class HealingBrain(KnowingBrain):
    def __init__(self, seed: int, listen: str = "pain", menu: str = "synapses", sign: str = "both",
                 select: str = "wsls", cascade: bool = False, ouch: str = "all", grow: bool = True,
                 tire: float = TIRE, waves: int = 3, trigger: str = "persist", grow_at: float = GROW_F,
                 shadow: str = "", judge: str = "rate", hold: float = HOLD, retire: bool = False,
                 starve: bool | float = False, persist: float = PERSIST):
        self.listen, self.menu, self.sign, self.select, self.cascade = listen, menu, sign, select, cascade
        self.trigger, self.grow_at, self.shadow, self.judge, self.hold = trigger, grow_at, shadow, judge, hold
        self.retire, self.starve, self.persist = retire, starve, persist
        self.ouch_kind, self.grow_on, self.tire, self.waves = ouch, grow, tire, waves
        self.recruits, self.t = [], 0                   # measuring: each recruit's record
        super().__init__(seed)

    slow = staticmethod(RecruitingBrain.slow)

    def build(self, c: Circuit) -> None:
        super().build(c)
        # T's frustration motif: its eligibility, F (anticipated pain), O (every pain), recruited flag
        E_T, C = self.slow(c, "E_T", ELIGIBLE)
        c.element(E_T, self.T, 1.0 * C, 0.0, slope=5.0, sigmoid=True)
        F, C = self.slow(c, "F_T", FRUSTRATION)
        c.element(F, self.taste_node, FRUSTRATE * C / 1.3, PAINFUL, slope=-20.0, sigmoid=True, gate=E_T)
        O, C = self.slow(c, "O_T", OUCH)
        c.element(O, self.taste_node, 2.0 * C / 1.3, PAINFUL, slope=-20.0, sigmoid=True,
                  gate=E_T if self.ouch_kind == "anticipated" else -1)
        Y, C = self.slow(c, "Y_T", OUCH)                # yum: a pulse at every good taste
        c.element(Y, self.taste_node, 2.0 * C / 1.3, -PAINFUL, slope=20.0, sigmoid=True)
        flag, C = self.slow(c, "frustrated_T", 2.0)     # a flag: F past 1/2
        c.element(flag, F, 1.0 * C, GROW_F, slope=20.0, sigmoid=True)
        self.frust = {self.T: {"F": F, "O": O, "Y": Y, "flag": flag, "att": [self.T], "wave": 0}}
        self.done = set()                               # units that have recruited

    # growth: the one primitive beside the circuit
    def step(self) -> list:
        spikes = self._tick()
        self.t += 1
        if self.grow_on:
            for u, fr in list(self.frust.items()):
                if u not in self.done and fr["wave"] < self.waves and self.circuit.V[fr["F"]] > self.grow_at:
                    self.recruit(u)
        for r in self.recruits:                         # measuring only: when each recruit's choice changes
            if r["enable"]:
                lv = self.circuit.V[r["enable"]]
                k = int(np.argmax(lv)) if lv.max() > 0.5 else -1
                if k != r["now"]:
                    r["now"], r["switches"] = k, r["switches"] + 1
                    r["since"] = self.t
        return self._motors(spikes)

    def neurons(self) -> list:
        c = self.circuit
        own = {}
        for _, (to, frm, _) in c.elements:
            if to == frm:
                own[to] = own.get(to, 0) + 1
        return [n for n, k in own.items() if k >= 2]

    def neighbours(self, units) -> set:
        """Neurons within one edge (a synapse either way) of any of these units."""
        c, nset = self.circuit, set(self.neurons())
        out = set()
        for _, (to, frm, _) in c.elements:
            if to in nset and frm in nset and to != frm:
                if frm in units:
                    out.add(to)
                if to in units:
                    out.add(frm)
        return out

    def recruit(self, u: int) -> None:
        c, fr = self.circuit, self.frust[u]
        self.done.add(u)
        att = sorted({u} | self.neighbours(set(fr["att"])))
        i = len(self.recruits)
        R = c.neuron(f"R{i}")
        act = -1                                        # shadow: act (and count as having acted) only once frustrated
        if self.retire:                                 # retire: act only while working, until the recruit has failed
            act = c.node(f"working{i}", bias=1.0, R=1.0, C=1.0, lo=0.0, hi=1.0, start=1.0)
            retired = c.node(f"retired{i}", R=None, lo=0.0, hi=1.0, start=0.0, memory=True)
            c.element(act, retired, -3.0, 0.5, slope=12.0, sigmoid=True)
        if self.shadow == "flag":                       # while the parent's flag is on
            act = fr.get("flag", -1)
        elif self.shadow == "latch":                    # from the first time the flag comes on: commissioned for good
            act = c.node(f"commissioned{i}", R=None, lo=0.0, hi=1.0, start=0.0, memory=True)
            c.element(act, fr["flag"], 0.05, 0.5, slope=20.0, sigmoid=True)
        E_R, C_E = self.slow(c, f"E_R{i}", ELIGIBLE)
        c.element(E_R, R, 1.0 * C_E, 0.0, slope=5.0, sigmoid=True, gate=act)
        H = c.node(f"H_R{i}", R=self.hold * SPEED / 10.0, C=10.0, lo=0.0, hi=1.0)
        c.element(H, R, 10.0, 0.0, slope=5.0, sigmoid=True, gate=act)
        pain_after, C_P = self.slow(c, f"P_R{i}", OUCH)          # pain that follows my action
        c.element(pain_after, fr["O"], 2.0 * C_P, 0.5, slope=10.0, sigmoid=True, gate=E_R)
        good_after, C_G = self.slow(c, f"G_R{i}", OUCH)          # a good taste that follows my action
        c.element(good_after, fr["Y"], 2.0 * C_G, 0.5, slope=10.0, sigmoid=True, gate=E_R)
        # listening
        listen = {}
        learned = {f: g for _, (to, f, g) in c.elements if to == u and g >= 0 and c.nodes[g][5] > 0}  # parent's memories
        if self.listen != "none":
            for x in att:
                if self.listen == "inherit" and x in learned:   # what the parent learned of x, shared
                    w = learned[x]
                    c.element(R, x, STRONG, 0.0, tau=0.5, slope=5.0, sigmoid=True, gate=w)
                    listen[x] = w
                    continue
                w = c.node(f"w{i}_{c.names[x]}", R=None, lo=0.0, hi=1.0,
                           start=1.0 if self.listen == "all" else 0.0, memory=True)
                c.element(R, x, STRONG, 0.0, tau=0.5, slope=5.0, sigmoid=True, gate=w)     # x -> R, its strength w
                if self.listen in ("pain", "inherit"):
                    e, C = self.slow(c, f"e{i}_{c.names[x]}", ELIGIBLE)
                    c.element(e, x, 1.0 * C, 0.0, slope=5.0, sigmoid=True)
                    c.element(w, fr["O"], LISTEN_STEP / OUCH_ABOVE, 0.5, slope=10.0, sigmoid=True, gate=e)  # ouch
                    c.element(w, fr["Y"], -LISTEN_STEP / OUCH_ABOVE, 0.5, slope=10.0, sigmoid=True, gate=e)  # yum
                    c.element(w, e, -LISTEN_DECAY, 0.5, slope=10.0, sigmoid=True)                    # slight decay
                listen[x] = w
        # the menu of actions
        options = []
        nset = set(self.neurons())
        for x in att:
            if "inh" in self.sign or self.sign == "both":
                options.append(("inhibit", x))
            if "exc" in self.sign or self.sign == "both":
                options.append(("excite", x))
        if self.menu in ("synapses", "inputs"):         # synapses leaving (or, "inputs", arriving at) attached neurons
            for e, (_, (to, frm, gate)) in enumerate(c.elements):
                mine = frm in att and to in nset if self.menu == "synapses" else to in att and frm in nset
                if mine and to != frm and R not in (to, frm) and (gate == -1 or c.names[gate].startswith("Q")):
                    options.append(("gate", e))
        enable, strength = [], []
        for k, (kind, target) in enumerate(options):
            if self.select == "random":
                en = c.node(f"en{i}_{k}", R=None, lo=0.0, hi=1.0, start=0.0, memory=True)
            elif self.select == "reinforce":            # graded: a learned strength, jittered by two noise nodes
                a = c.node(f"a{i}_{k}", R=None, lo=0.0, hi=1.0, start=REINFORCE_START, memory=True)
                up = c.node(f"xi{i}_{k}+", R=JITTER_TAU * SPEED / JITTER_C, C=JITTER_C, lo=0.0, hi=1.0, start=0.0)
                down = c.node(f"xi{i}_{k}-", R=JITTER_TAU * SPEED / JITTER_C, C=JITTER_C, lo=0.0, hi=1.0, start=0.0)
                en = c.node(f"en{i}_{k}", R=0.5, C=1.0, lo=0.0, hi=1.0, start=0.0)     # (follows a + up - down)
                for src, sign in ((a, 1.0), (up, 1.0), (down, -1.0)):
                    c.element(en, src, 2.0 * sign, -10.0, slope=1.0, sigmoid=True, gate=src)   # a current of 2 x src
                for outcome, good in ((good_after, 1.0), (pain_after, -1.0)):
                    for jit, sign in ((up, 1.0), (down, -1.0)):   # move the strength the way the jitter went, or back
                        c.element(a, outcome, good * sign * REINFORCE_RATE / OUCH_ABOVE, 0.5, slope=10.0, sigmoid=True,
                                  gate=jit)
                strength.append(a)
            else:
                en, C = self.slow(c, f"en{i}_{k}", 20.0)
            enable.append(en)
            if kind == "inhibit":
                c.element(target, H, -INHIBIT, 0.5, slope=10.0, sigmoid=True, gate=en)
            elif kind == "excite":
                c.element(target, H, EXCITE, 0.5, slope=10.0, sigmoid=True, gate=en)
            else:                                       # turn the synapse down through a gate that rests open
                _, (to, frm, gate) = c.elements[target]
                if gate == -1:
                    gate = c.node(f"Q{c.names[frm]}{c.names[to]}", bias=1.0, R=1.0, C=1.0, lo=0.0, hi=1.0, start=1.0)
                    c.regate(target, gate)
                c.element(gate, H, -3.0, 0.5, slope=10.0, sigmoid=True, gate=en)
        if self.select == "all":
            for en in enable:
                c.nodes[en] = c.nodes[en][:1] + (0.0,) + c.nodes[en][2:]    # (a full, unleaking enable)
                c.start[en] = 1.0
        elif self.select == "random" and enable:
            c.start[enable[int(c.rng.integers(len(enable)))]] = 1.0
        elif self.select == "wsls" and enable:
            tired = []
            for k, en in enumerate(enable):
                Cn = c.nodes[en][2]
                c.start[en] = 0.0                                                    # all rise from nothing ...
                c.element(en, en, 0.15 * Cn, 0.5, slope=12.0, sigmoid=True, gate=en)  # ... the first past 1/2 latches
                c.nodes[en] = (0.008 * Cn,) + c.nodes[en][1:]           # a slow rise (to about 0.64) until one wins
                share = self.judge == "share"
                f, Cf = self.slow(c, f"tired{i}_{k}", REST_SHARE if share else REST_TIRED)
                sl = 30.0 if share else 10.0                # (steep: at 10 the resting tails, unequal now, add up to a
                c.element(f, pain_after, self.tire * Cf / OUCH_ABOVE, 0.5, slope=sl, sigmoid=True, gate=en)  # rise)
                c.element(f, good_after, -(GOOD_STEP if share else 1.0) * self.tire * Cf / OUCH_ABOVE, 0.5,
                          slope=sl, sigmoid=True, gate=en)
                if share:                                   # it rests only while off: an off node, held down by en
                    off = c.node(f"off{i}_{k}", bias=1.0, R=1.0, C=1.0, lo=0.0, hi=1.0, start=1.0)
                    c.element(off, en, -3.0, 0.5, slope=12.0, sigmoid=True)
                    c.element(f, f, -Cf / (REST_TIRED * SPEED), 0.0, slope=1.0, gate=off)   # (about f / REST_TIRED)
                c.element(en, f, -0.5 * Cn, TIRED, slope=20.0, sigmoid=True, gate=f)  # tired: knocked out
                if self.starve:                             # no news is bad news: a slow rise while on
                    ticks = STARVE if self.starve is True else self.starve
                    c.element(f, en, TIRED * Cf / (ticks * SPEED), 0.5, slope=20.0, sigmoid=True, gate=en)
                tired.append(f)
            for a in enable:                            # and holds the others down (pairwise: a shared inhibitor can't
                for b in enable:                        # tell one option on from ten, and all latched together)
                    if a != b:
                        c.element(a, b, -0.3 * c.nodes[a][2], 0.5, slope=20.0, sigmoid=True, gate=b)
                        # (steep: at slope 12 the tails of a dozen resting rivals outweighed the rise, and none won)
        # the recruit's own frustration, for a cascade: its parent still frustrated long after it came ("persist"), or
        # pain while it is idle, every option tried and knocked out ("idle")
        if self.cascade and self.trigger in ("persist", "root"):
            F_R, C = self.slow(c, f"F_R{i}", self.persist)
            src = fr["flag"] if self.trigger == "root" else fr["F"]   # root: the first frustrated unit's own flag
            c.element(F_R, src, C / (self.persist * SPEED), 0.5, slope=12.0, sigmoid=True)   # fills over persist ticks
            if self.retire:                             # and when it is frustrated enough to recruit, it stands down
                c.element(retired, F_R, 0.05, GROW_F, slope=20.0, sigmoid=True)
            self.frust[R] = {"F": F_R, "O": fr["O"], "Y": fr["Y"], "flag": fr.get("flag", -1), "att": att,
                             "wave": fr["wave"] + 1}
        elif self.cascade:
            idle, C_i = self.slow(c, f"idle{i}", IDLE_RISE)      # rises slowly (a newborn recruit isn't exhausted) ...
            c.nodes[idle] = (c.nodes[idle][1],) + c.nodes[idle][1:]  # (a bias equal to its leak: it rests at 1)
            c.start[idle] = 0.0
            for en in enable:                                        # ... and any option on holds it down
                c.element(idle, en, -3.0 * C_i, 0.5, slope=12.0, sigmoid=True)
            F_R, C = self.slow(c, f"F_R{i}", FRUSTRATION)
            c.element(F_R, fr["O"], EXHAUSTED * C / OUCH_ABOVE, 0.5, slope=10.0, sigmoid=True, gate=idle)
            self.frust[R] = {"F": F_R, "O": fr["O"], "Y": fr["Y"], "flag": fr.get("flag", -1), "att": att,
                             "wave": fr["wave"] + 1}
        c.grow()
        self.inject = np.concatenate([self.inject, np.zeros(len(c.names) - len(self.inject))])
        self.recruits.append({"tick": self.t, "parent": u, "R": R, "att": att, "listen": listen,
                              "options": options, "enable": strength or enable, "wave": fr["wave"] + 1,
                              "now": -1, "switches": 0, "since": self.t})

    def block_hints(self) -> dict:
        """Watching (blocks.py): each option's enable, tiredness and rest are too many to draw; the chosen action shows
        as its link."""
        c = self.circuit
        return {n: ("hide", None) for n, name in enumerate(c.names)
                if name.startswith(("en", "tired", "off", "xi", "a")) and name[-1].isdigit() or name.endswith(("+", "-"))}

    def report(self) -> list:
        """Measuring: each recruit, its listening strengths and which option is on (or most on)."""
        V, out = self.circuit.V, []
        for r in self.recruits:
            on = [float(V[e]) for e in r["enable"]]
            k = int(np.argmax(on)) if on else None
            out.append({"tick": r["tick"], "wave": r["wave"], "parent": r["parent"], "att": r["att"],
                        "switches": r["switches"], "since": r["since"],
                        "listen": {x: float(V[w]) for x, w in r["listen"].items()},
                        "on": None if k is None or on[k] < 0.5 else r["options"][k], "options": r["options"],
                        "levels": on})
        return out

    def shown(self) -> list:
        return [("T taste", self.T)] + [(f"recruit R{i}", r["R"]) for i, r in enumerate(self.recruits)]
