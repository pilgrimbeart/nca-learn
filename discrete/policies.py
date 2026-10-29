"""Policies, not circuits: what the body allows, before any circuit is built (discrete/NOTEBOOK.md). Each policy sees
only what a brain sees (the eyes' pulses, the taste) and fires the thrusters by name of motor; the body is
creature.Life's, unchanged (or built differently: discrete/bodies.py). Judged as minimal/spec.py judges circuits
(efficiency, gain rate, food, stranding), the circuit's power taken as 0: in all food (judge, D1) or with poison
(judge_poison, D6).

A kind is the approach (straight, curve, counter, reflex, reflex_hold, hold_drive); options of any kind: a roam
(bored, roam, roam_rate, or every; until_seen: until the next sighting, giving up as learn_avoid does), learning the
bit (learn: toggle or trace, D6), avoiding the colour not followed (avoid: extra turns, or "drop" the hold), the
oracle (told from birth which sensor sees food: the ceiling, D8); kinds that tune one setting in the life (lockin,
tumble, homeo, D5).

    python -m discrete.policies [--seeds 32]
"""

from __future__ import annotations

import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from units import TICK  # noqa: E402


class Policy:
    """A brain made of a rule: pulses seen this tick (any sensor) -> motors fired. Periodic drives keep their own
    phase, started at random."""

    def __init__(self, seed, kind, **p):
        self.kind, self.p = kind, p
        self.rng = np.random.default_rng(seed + 77)
        self.seen = 0
        self.last = -1e9                                # when a pulse last came
        self.t = 0.0
        self.phase = {k: self.rng.random() for k in ("scan", "drive", "roam")}
        self.roam_until = -1.0
        self.trace = [0.0, 0.0]                         # learning: each sensor's recent pulses, fading over p["tau"]
        self.on = [True, True]                          # learning: which sensors may start the hold
        if p.get("latch"):                              # (one bit: one sensor on, at first by chance)
            self.on = [bool(self.rng.random() < 0.5)] * 2
            self.on[1] = not self.on[0]
        self.good = int(self.rng.integers(2))           # learning (toggle): the one sensor that may, at first by chance
        self.doubt = 0                                  # learning (toggle with n): poison since the last food
        self.doubted = 0.0
        self.tasted = 0.0
        # self-tuning (kinds "lockin", "tumble"): the log of one setting, p["knob"], moves in the life
        self.x = np.log(p[p["knob"]]) if "knob" in p else 0.0
        self.dir = 1.0                                  # tumble: which way it drifts
        self.fast = self.slow = 0.0                     # tumble: the food rate, recent and longer
        self.since = 0.0                                # tumble: time since it last turned
        self.knob_trace = []
        self.fed = 0.0                                  # homeostat: meals, fading over p["memory"]
        self.bad = 0                                    # learning (toggle, avoid): pulses of the sensor not followed
        self.sign = 1.0                                 # lock-in, dither "approach": this approach's wobble
        self.phase["drive1"] = self.rng.random()       # (drawn last: earlier policies' lives unchanged)

    def setting(self, name):
        """A setting, the tuned one at its present value (with lock-in, wobbling by a factor exp(+-wobble))."""
        p = self.p
        if p.get("knob") != name:
            return p[name]
        if self.kind == "homeo":                        # the more it has eaten lately, the lower (gain > 0)
            return float(p[name] * np.exp(-p["gain"] * (self.fed - p.get("target", 0.0))))
        if self.kind == "lockin":
            return float(np.exp(self.x + p["wobble"] * self.phase_sign()))
        return float(np.exp(self.x))

    def phase_sign(self):
        if self.p.get("dither") == "approach":          # each approach wobbles its own way, tossed at its start
            return self.sign
        return 1.0 if (self.t / self.p["period"] + self.phase["roam"]) % 1.0 < 0.5 else -1.0

    def stimulate(self, sensor, at):
        self.trace[sensor] += 1.0
        k = self.kind
        p = self.p
        if k == "lockin" and p.get("reward") == "pulse" and self.t - self.last < self.setting("hold"):
            lo, hi = np.log(p.get("lo", 1e-3)), np.log(p.get("hi", 1e3))   # a pulse while driving: the knob moves
            self.x = float(np.clip(self.x + p["rate"] * self.phase_sign(), lo, hi))  # the way it is wobbling
        if p.get("learn") == "toggle" and sensor != self.good:
            self.bad += 1                               # (avoid: the other colour turns it away)
            return
        if p.get("learn") == "trace" and not self.on[sensor]:
            return
        self.seen += 1

    def taste(self, value, at):
        self.tasted = value
        p, k = self.p, self.kind
        lo, hi = np.log(p.get("lo", 1e-3)), np.log(p.get("hi", 1e3))
        if k == "lockin" and value > 0 and p.get("reward", "meal") == "meal":   # a meal: the knob moves the way
                                                                                 # it is wobbling
            self.x = float(np.clip(self.x + p["rate"] * self.phase_sign(), lo, hi))
        if k == "homeo" and value > 0:
            self.fed += 1.0
        if k == "tumble" and value > 0:
            self.fast += 1.0 / p["fast"]
            self.slow += 1.0 / p["slow"]
        if p.get("learn") == "toggle":                  # poison: approach the other sensor's colour instead (after n
            blamed = p.get("blame") != "held" or self.t - self.last < p.get("hold", 0.0) + 2 * TICK
            if value < 0 and blamed:                    # poisons with no food between; blame "held": only those
                if "forget" in p:                       # eaten while approaching; forget: doubt fades over that long)
                    self.doubt *= float(np.exp(-(self.t - self.doubted) / p["forget"]))
                    self.doubted = self.t
                self.doubt += 1
                if self.doubt >= p.get("n", 1) - 0.25 * ("forget" in p):
                    self.good, self.doubt = 1 - self.good, 0
            elif value > 0:
                self.doubt = 0
        elif p.get("learn") == "trace" and max(self.trace) > 0 and (value < 0 or not p.get("poison_only")):      # the sensor that saw most just before: poison turns it off,
            s = int(np.argmax(self.trace))              # food on; poison also turns the other on, so that a mistake
            self.on[s] = value > 0                      # (a poison eaten unseen, blamed on the other eye) can't
            if value < 0 or p.get("latch"):             # leave both off for good; latch: one bit, exactly one on
                self.on[1 - s] = not self.on[s]

    def drive(self, sensor):
        return 1.0

    def _clock(self, name, rate):
        """Whether a periodic drive at `rate` per second ticks in this tick."""
        if rate <= 0:
            return 0
        self.phase[name] += rate * TICK
        n = int(self.phase[name])
        self.phase[name] -= n
        return n

    def step(self):
        p, seen = self.p, self.seen
        self.seen = 0
        self.t += TICK
        self.trace = [x * np.exp(-TICK / p.get("tau", 0.3)) for x in self.trace]
        self.fed *= np.exp(-TICK / p.get("memory", 10.0))
        tasted, self.tasted = self.tasted, 0.0
        if self.kind == "tumble":                       # drift; turn back when food comes slower than it did
            self.fast *= np.exp(-TICK / p["fast"])
            self.slow *= np.exp(-TICK / p["slow"])
            self.since += TICK
            lo, hi = np.log(p.get("lo", 1e-3)), np.log(p.get("hi", 1e3))
            self.x = float(np.clip(self.x + self.dir * p["rate"] * TICK, lo, hi))
            if (self.fast < self.slow * (1 - p.get("margin", 0.1)) and self.since > p["fast"]) or self.x in (lo, hi):
                self.dir, self.since = -self.dir, 0.0
        if "knob" in p and int(self.t / TICK) % 100 == 0:
            self.knob_trace.append(float(np.exp(self.x)))
        if tasted and p.get("on_taste") == "end":       # a meal: the block ahead is gone; stop driving
            self.last = -1e9
            seen = 0
        elif tasted and p.get("on_taste") == "hold":    # a meal: drive on, as if a pulse had come
            seen += 1
        bad, self.bad = self.bad, 0
        if bad and p.get("avoid"):                      # the colour not followed: turn away, stop roaming, drop the
            self.roam_until = min(self.roam_until, self.t)                  # hold
            self.last = -1e9
            seen = 0
        if seen and p.get("until_seen"):              # a roam that lasts until the next sighting (the circuit's run)
            self.roam_until = min(self.roam_until, self.t)
        if seen:
            if p.get("dither") == "approach" and self.t - self.last >= self.setting("hold"):   # a new approach:
                                                                                                  # toss its sign
                self.sign = 1.0 if self.rng.random() < 0.5 else -1.0
            self.last = self.t
        held = self.t - self.last < p.get("hold", 0.0)
        out = []
        k = self.kind
        if k == "straight":                             # both thrusters at one rate, eyes ignored
            out += [0, 1] * self._clock("drive", p["rate"])
        elif k == "curve":                              # two free-running clocks, one per thruster, eyes ignored
            out += [0] * self._clock("scan", p["a"]) + [1] * self._clock("drive", p["b"])
        elif k == "reflex_curve":                       # ... and each pulse fires both
            out += [0, 1] * seen + [0] * self._clock("scan", p["a"]) + [1] * self._clock("drive", p["b"])
        elif k == "counter":                            # a scanner fires one thruster; each pulse fires the other k
            out += [1] * seen * p.get("k", 1) + [0] * self._clock("scan", p["scan"])   # times: their turns cancel
        elif k == "reflex":                             # each pulse fires both; a scanner fires one at all times
            out += [0, 1] * seen + [0] * self._clock("scan", p["scan"])
        elif "bored" in p and self.roaming():           # (any kind below) after `bored` s with nothing, drive
            out += [0, 1] * self._clock("drive", p.get("roam_rate", p.get("drive", 0)))   # straight for `roam` s
        elif k == "reflex_hold":                        # ... the scanner silenced for a while after a pulse
            out += [0, 1] * seen * p.get("k", 1)
            if not held:
                out += [0] * self._clock("scan", p["scan"])
        elif k in ("hold_drive", "lockin", "tumble", "homeo"):   # after a pulse, both at a
            if self.t - self.last < self.setting("hold"):                             # drive rate for a while; else scan
                if "balance" in p:                      # motor 0 at drive x balance, motor 1 at drive / balance: the
                    d, k = self.setting("drive"), self.setting("balance")      # common rate fired together, the
                    m = 0 if k > 1 else 1                                       # excess on its own motor
                    out += [0, 1] * self._clock("drive", d * min(k, 1 / k))
                    out += [m] * self._clock("drive1", d * abs(k - 1 / k))
                else:
                    out += [0, 1] * self._clock("drive", self.setting("drive"))
            else:
                out += [0] * self._clock("scan", self.setting("scan"))
        if bad and p.get("avoid"):                      # (avoid "drop": only the hold dropped, as in the circuit)
            out += [0] * bad * (0 if p["avoid"] == "drop" else p["avoid"])
        return out

    def roaming(self):
        """Roam (p["bored"], p["roam"]): after `bored` s with no pulse (and none since the last roam), `roam` s."""
        p = self.p
        if p.get("every"):                              # (every: a roam every so many s, whatever is seen, as a free
            return (self.t / p["every"] + self.phase["roam"]) % 1.0 < p["roam"] / p["every"]   # oscillator gives)
        if self.t - self.last > p["bored"] and self.t > self.roam_until + p["bored"]:
            self.roam_until = self.t + p["roam"]
        return self.t < self.roam_until


def life(job):
    from creature import Life
    from minimal.spec import Lived, SPAN, thirds
    kind, p, seed, seconds, poison, body = (*job, None, None)[:6]
    lf = Life(seed, poison, brain=lambda s: Policy(s, kind, **p))
    if p.get("oracle") and poison:                      # the ceiling: told from birth which sensor sees food (no
        lf.brain.good = lf.sensor[next(c for c in lf.sensor if c != poison)]   # brain can know; learn "toggle" with
                                                                                # a large n keeps it)
    if body:                                            # a body built differently (discrete/bodies.py)
        from discrete.bodies import vary
        vary(lf, body)
    ticks = int(round(seconds / TICK))
    while lf.t < ticks:
        lf.step()
    l = Lived(thirds(lf.meals, lf.moving, ticks, poison))
    l.power, l.firings = 0.0, SPAN * len(lf.firings) / seconds
    return l


def judge(kind, p, seeds, seconds=100.0, ex=None, body=None):
    """All food; body: factors (discrete/bodies.py) for every life, or a function of the seed giving them."""
    from minimal.spec import efficiency, gain
    jobs = [(kind, p, s, seconds, None, body(s) if callable(body) else body) for s in seeds]
    lives = list(ex.map(life, jobs)) if ex else [life(j) for j in jobs]
    t = sum(t for l in lives for _, _, t in l)
    food = 10 * sum(a for l in lives for a, _, _ in l) / t
    stranded = np.mean([l[2][0] == 0 for l in lives])
    fir = np.mean([l.firings for l in lives])
    return dict(eff=efficiency(lives), gain=gain(lives), food=food, stranded=stranded, firings=fir)


def judge_poison(kind, p, seeds, seconds=100.0, ex=None):
    """Lives paired, red then blue as poison on each seed (a policy that ignores taste nets below 0), judged as
    minimal/spec.py judges circuits."""
    from minimal.spec import does_job, efficiency, gain
    jobs = [(kind, p, s, seconds, c) for s in seeds for c in ("red", "blue")]
    lives = list(ex.map(life, jobs)) if ex else [life(j) for j in jobs]
    t = sum(t for l in lives for _, _, t in l)
    lf, lp = sum(l[2][0] for l in lives), sum(l[2][1] for l in lives)
    return dict(eff=efficiency(lives), gain=gain(lives), food=10 * sum(a for l in lives for a, _, _ in l) / t,
                poison=10 * sum(b for l in lives for _, b, _ in l) / t, last=lf / max(lp, 1),
                stranded=float(np.mean([l[2][0] == 0 for l in lives])), job=does_job(lives))


if __name__ == "__main__":
    import argparse
    import itertools
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=32)
    a = ap.parse_args()
    seeds = range(1000, 1000 + a.seeds)
    grid = []
    for s, k in itertools.product((48, 64, 96), (1, 2)):
        grid.append(("counter", dict(scan=s, k=k)))
    for s, h in itertools.product((16, 32, 64, 96), (0.05, 0.1, 0.2)):
        grid.append(("hold_drive", dict(scan=s, drive=s, hold=h)))
    with ProcessPoolExecutor() as ex:
        for kind, p in grid:
            r = judge(kind, p, seeds, ex=ex)
            print(f"{kind:16s} {str(p):40s} eff {r['eff']:5.2f} gain {r['gain']:5.2f} food {r['food']:5.2f}"
                  f" stranded {r['stranded']:4.0%} firings {r['firings']:5.0f}", flush=True)
