"""Discrete circuits living closed loop in SPICE (discrete/NOTEBOOK.md): a netlist of common parts (resistors, capacitors,
diodes, bipolar transistors, FETs) on a battery, and the body (creature.Life, unchanged) running with ngspice tick by
tick, as minimal/spice_life.py runs the chip's circuits.

The interface, as for every brain (AGENTS.md), in a discrete technology:
- the battery: SUPPLY volts between `vdd` and ground; what it delivers is the circuit's power;
- each eye a photodiode from the supply into its sensor node (`s0`, `s1`), giving a pulse of EYE amps for PULSE at each
  of the body's stimuli; it can't lift its node above the supply (the photodiode's own limit, not a part);
- each motor (`m0`, `m1`) a thruster driver's Schmitt input (CMOS, drawing nothing, MOTOR_C of capacitance): a firing
  each time the node rises through 2/3 of the supply, re-armed once it falls below 1/3;
- the taste (my choice, to confirm): a circuit that names a taste node (`Netlist.taste`) gets, at each meal, a pulse
  of EYE amps for PULSE into it (+ food, - poison: pulled out), clamped a diode drop beyond either rail by the sensor's
  own diodes (not parts, as an eye's); a circuit that names none isn't wired to it.

Parts are real: each seed draws its own tolerances (TOL) for every resistor, capacitor and transistor, as a batch of
parts off the shelf would vary. Noise: none in SPICE (a discrete circuit's thermal noise is microvolts against swings of
volts); the body's pulses are random (Poisson, at random moments), and the tolerances differ seed by seed.

    python -m discrete.life CIRCUIT [--seeds 0:8] [--seconds 100] [--workers 4] [--set k=v ...]
"""

from __future__ import annotations

import ctypes as C
import os
import sys
import tempfile
import threading
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from minimal.spice_life import (LIB, NGROOT, BGRunning, Exit, GetISRC, GetSync, GetVSRC, SendChar,  # noqa: E402
                                SendData, SendInit, SendStat)
from units import MICRO, PICO, PULSE, TICK  # noqa: E402

SUPPLY = 3.0            # V: a lithium coin cell
EYE = 1 * MICRO         # A: an eye's photocurrent while it pulses (a small photodiode in daylight)
MOTOR_C = 10 * PICO     # F: a thruster driver's input
RISE, FALL = 2 / 3, 1 / 3   # a motor fires rising through RISE x the supply, and re-arms below FALL x it
STEP = TICK / 20        # s: SPICE's largest step in a life, 0.5 ms, with its error control tightened (ACCURACY)
ACCURACY = ".options trtol=1 reltol=1e-4"
        # ngspice's default error control let an oscillator run 15% slow at this step, and a circuit tuned there lost
        # the job; at finer steps the timing converged but a marginal roam still fired or not by the step's chance.
        # Tightened, every step from 0.5 ms to 16 us agrees (discrete/NOTEBOOK.md D7)

TOL = {"R": 0.01, "C": 0.05, "IS": 0.2, "BF": 0.25}
        # each part's spread (one standard deviation, relative): 1% resistors, 5% capacitors (a 10% part's), a
        # transistor's saturation current 20% (its VBE about 5 mV) and gain 25%

TRANSISTORS = {                                         # (kind, saturation current, gain, the rest)
    "NPN": ("NPN", 6.734e-15, 416.4, "XTI=3 EG=1.11 VAF=74.03 NE=1.259 ISE=6.734f IKF=66.78m XTB=1.5 BR=.7371 NC=2"
            " ISC=0 IKR=0 RC=1 CJC=3.638p MJC=.3085 VJC=.75 FC=.5 CJE=4.493p MJE=.2593 VJE=.75 TR=239.5n TF=301.2p"
            " ITF=.4 VTF=4 XTF=2 RB=10"),                                                         # 2N3904
    "PNP": ("PNP", 1.41e-15, 180.7, "XTI=3 EG=1.11 VAF=18.7 NE=1.5 ISE=0 IKF=80m XTB=1.5 BR=4.977 NC=2 ISC=0 IKR=0"
            " RC=2.5 CJC=9.728p MJC=.5776 VJC=.75 FC=.5 CJE=8.063p MJE=.3677 VJE=.75 TR=33.42n TF=179.3p ITF=.4"
            " VTF=4 XTF=6 RB=10"),                                                                # 2N3906
}
DIODE = "D(IS=5e-14 N=1.0 RS=5 CJO=2p M=0.33 TT=3u BV=85 IBV=1n)"
        # a low-leakage switching diode (BAS416 class: picoamps reversed; a 1N4148 leaks nanoamps, as much as
        # these circuits' currents)


class Netlist:
    """A circuit being written for one seed: parts with this seed's tolerances (rng None: nominal), counted."""

    def __init__(self, rng=None):
        self.rng, self.lines, self.models, self.count = rng, [], [], {"R": 0, "C": 0, "D": 0, "Q": 0}
        self.eye = ["s0", "s1"]         # the node each eye feeds (both may feed one: a wire, not a part)
        self.motor = ["m0", "m1"]       # the node each motor reads (both may read one)
        self.taste = None               # the node the taste feeds, if any

    def _vary(self, x, kind):
        return x if self.rng is None else x * float(np.exp(self.rng.normal(0.0, TOL[kind])))

    def R(self, a, b, ohms):
        self.count["R"] += 1
        self.lines.append(f"R{len(self.lines)} {a} {b} {self._vary(ohms, 'R'):.6g}")

    def C(self, a, b, farads):
        self.count["C"] += 1
        self.lines.append(f"C{len(self.lines)} {a} {b} {self._vary(farads, 'C'):.6g}")

    def D(self, anode, cathode):
        self.count["D"] += 1
        self.lines.append(f"D{len(self.lines)} {anode} {cathode} DMOD")

    def Q(self, kind, c, b, e):
        """A bipolar transistor, NPN (2N3904) or PNP (2N3906), with its own saturation current and gain."""
        self.count["Q"] += 1
        n = len(self.lines)
        pol, IS, BF, rest = TRANSISTORS[kind]
        self.models.append(f".model Q{n}M {pol}(IS={self._vary(IS, 'IS'):.6g} BF={self._vary(BF, 'BF'):.6g} {rest})")
        self.lines.append(f"Q{n} {c} {b} {e} Q{n}M")

    def parts(self) -> int:
        return sum(self.count.values())

    def text(self, supply=SUPPLY) -> list:
        return ([f"* discrete circuit, {self.parts()} parts {self.count}", f"VDD vdd 0 dc {supply:g}",
                 f"VEYE veye 0 dc {supply:g}", ".model DMOD " + DIODE, ".model DEYE D(IS=1e-14 N=1)"]
                + [f"I_eye{k} 0 {self.eye[k]} dc 0 external" for k in (0, 1)]
                + [f"D_eye{k} {self.eye[k]} veye DEYE" for k in (0, 1)]
                + [f"C_motor{k} {m} 0 {MOTOR_C:g}" for k, m in enumerate(dict.fromkeys(self.motor))]
                + ([f"I_taste 0 {self.taste} dc 0 external", f"D_taste_hi {self.taste} veye DEYE",
                    f"D_taste_lo 0 {self.taste} DEYE"] if self.taste else [])
                + self.models + self.lines + [ACCURACY])


class SpiceBrain:
    """The brain creature.Life talks to: stimulate and taste queue the next tick's pulses; step waits while ngspice
    runs the tick, then returns the motors that fired."""

    def __init__(self):
        self.base = 0.0
        self.queued = []
        self.spikes = None
        self.go, self.ready = threading.Event(), threading.Event()

    def stimulate(self, sensor, at):
        self.queued.append((sensor, self.base + at, self.base + at + PULSE))

    def taste(self, value, at):
        if value:
            self.queued.append((2 if value > 0 else 3, self.base + at, self.base + at + PULSE))

    def step(self):
        self.ready.set()
        self.go.wait()
        self.go.clear()
        self.base += TICK
        return [m for m in (0, 1) for _ in range(self.spikes[m])]

    def drive(self, sensor):
        return 1.0


def live(net: Netlist, seed: int, seconds: float, supply: float = SUPPLY, poison=None, probe=(), record=False,
         body=None, step: float = STEP) -> dict:
    """One life of a netlist, closed loop: meals, firings, when it first moved, mean power. probe: node names whose
    voltages to record at each tick's end; record: also each firing (tick, thruster) and what the eyes saw each tick
    (watching); body: a body built differently (discrete/bodies.py's factors)."""
    from creature import Life
    factors = body
    os.environ.setdefault("SPICE_LIB_DIR", os.path.join(NGROOT, "usr/share/ngspice"))
    ng = C.CDLL(LIB)
    lines = [f"discrete life, seed {seed}"] + net.text(supply)
    lines += [".save " + " ".join(f"v({m})" for m in dict.fromkeys(net.motor)) + " i(VDD) "
              + " ".join(f"v({p})" for p in probe), ".end"]
    brain = SpiceBrain()
    pulses = {0: [], 1: [], 2: [], 3: []}             # the eyes', then the taste's (food, poison)
    ticks = int(round(seconds / TICK))
    st = {"next": TICK, "idx": None, "armed": [True, True], "count": [0, 0], "t": 0.0, "energy": 0.0,
          "done": False, "out": [], "err": None, "trace": []}
    hi, lo = RISE * supply, FALL * supply

    def schedule():
        for k, a, b in brain.queued:
            pulses[k].append((a, b))
            ng.ngSpice_SetBkpt(C.c_double(a))
            ng.ngSpice_SetBkpt(C.c_double(b))
        brain.queued.clear()
        for k in pulses:                                # forget pulses long past
            pulses[k] = [p for p in pulses[k] if p[1] > st["t"] - TICK]
        ng.ngSpice_SetBkpt(C.c_double(st["next"]))

    @SendChar
    def on_char(s, i, u):
        s = s.decode(errors="replace")
        st["out"].append(s)
        if "rror" in s and "stderr" in s:
            st["err"] = s
        return 0

    @SendStat
    def on_stat(s, i, u):
        return 0

    @Exit
    def on_exit(status, unload, quit_, i, u):
        st["err"] = st["err"] or f"ngspice exited ({status})"
        return 0

    @SendData
    def on_data(vals, n, i, u):
        v = vals.contents
        if st["idx"] is None:
            nm = [v.vecsa[k].contents.name.decode().lower() for k in range(v.veccount)]
            find = lambda s: next((k for k, x in enumerate(nm) if x in (s, f"v({s})", s[2:-1] + "#branch")), None)
            st["idx"] = ([find(m) for m in net.motor], find("time"), find("i(vdd)"), [find(p) for p in probe])
        (k0, k1), kt, kd, kp = st["idx"]
        t = v.vecsa[kt].contents.creal
        st["energy"] += -supply * v.vecsa[kd].contents.creal * (t - st["t"])
        st["t"] = t
        for m, k in enumerate((k0, k1)):
            x = v.vecsa[k].contents.creal
            if st["armed"][m] and x > hi:
                st["count"][m] += 1
                st["armed"][m] = False
            elif x < lo:
                st["armed"][m] = True
        if t >= st["next"] - 1e-9 and not st["done"]:
            if probe:
                st["trace"].append([v.vecsa[k].contents.creal for k in kp])
            brain.spikes = st["count"][:]
            st["count"] = [0, 0]
            st["next"] += TICK
            brain.ready.clear()
            brain.go.set()
            brain.ready.wait()
            if not st["done"]:
                schedule()
        return 0

    @SendInit
    def on_init(p, i, u):
        return 0

    @BGRunning
    def on_bg(r, i, u):
        return 0

    @GetVSRC
    def on_vsrc(val, t, name, i, u):
        val[0] = 0.0
        return 0

    @GetISRC
    def on_isrc(val, t, name, i, u):
        name = name.decode().lower()
        if "taste" in name:
            val[0] = EYE * (sum(a <= t < b for a, b in pulses[2]) - sum(a <= t < b for a, b in pulses[3]))
        else:
            val[0] = EYE * sum(a <= t < b for a, b in pulses[int(name[-1])])
        return 0

    @GetSync
    def on_sync(t, dt, olddt, redo, i, loc, u):
        return 0

    keep = (on_char, on_stat, on_exit, on_data, on_init, on_bg, on_vsrc, on_isrc, on_sync)
    ng.ngSpice_Init(on_char, on_stat, on_exit, on_data, on_init, on_bg, None)
    ident = C.c_int(0)
    ng.ngSpice_Init_Sync(on_vsrc, on_isrc, on_sync, C.byref(ident), None)
    ng.ngSpice_Command(b"set ng_nomodcheck")
    arr = (C.c_char_p * (len(lines) + 1))(*[ln.encode() for ln in lines], None)
    result = {}

    seen = []                                           # watching: what the eyes saw each tick (if record)

    def body():
        try:
            lf = Life(seed, poison, brain=lambda s: brain)
            if factors:
                from discrete.bodies import vary
                vary(lf, factors)
            while lf.t < ticks:
                if record:
                    seen.append(sum(lf.body.sees().values()))
                lf.step()
            result.update(meals=lf.meals, firings=len(lf.firings), moving=lf.moving, fired=lf.firings,
                          seen=seen)
        except Exception as e:                          # noqa: BLE001
            result["error"] = repr(e)
        finally:
            st["done"] = True
            brain.ready.set()

    th = threading.Thread(target=body, daemon=True)
    with tempfile.TemporaryDirectory() as d:
        cwd = os.getcwd()
        os.chdir(d)
        try:
            th.start()
            brain.ready.wait()
            if ng.ngSpice_Circ(arr):
                raise RuntimeError("ngspice wouldn't load the circuit:\n" + "\n".join(st["out"][-30:]))
            schedule()
            t0 = time.time()
            ng.ngSpice_Command(f"tran {step / 4:g} {seconds:g} 0 {step:g} uic".encode())
            wall = time.time() - t0
        finally:
            for cmd in (b"destroy all", b"remcirc"):   # ngspice keeps every circuit and its results otherwise: a
                ng.ngSpice_Command(cmd)                 # worker grew by half a gigabyte in an hour
            os.chdir(cwd)
    th.join(5)
    del keep
    if "error" in result or "meals" not in result:
        raise RuntimeError(f"seed {seed}: {result.get('error')} {st['err']}\n" + "\n".join(st["out"][-20:]))
    return {"seed": seed, "meals": [(int(a), b) for a, b in result["meals"]], "firings": result["firings"],
            "moving": result["moving"], "power": st["energy"] / max(st["t"], 1e-12), "reached": st["t"],
            "wall": wall, "parts": net.parts(), "trace": st["trace"],
            **({"fired": result["fired"], "seen": result["seen"]} if record else {})}


def lived(r, seconds, poison=None):
    """A life's record as minimal.spec judges it (Lived)."""
    from minimal.spec import SPAN, Lived, thirds
    ticks = int(round(seconds / TICK))
    l = Lived(thirds(r["meals"], r["moving"], ticks, poison))
    l.power, l.firings, l.substrate = r["power"], SPAN * r["firings"] / seconds, "silicon"
    return l


def _one(a):
    name, params, seed, seconds = a
    from discrete.circuits import CIRCUITS
    build, supply = CIRCUITS[name]
    net = build(np.random.default_rng(seed + 5_000_011), **params)
    return live(net, seed, seconds, supply)


def judge(name, params, seeds, seconds=100.0, workers=4):
    """Lives of a circuit on seeds (each with its own parts): the league's measures, all food, and the lives."""
    from concurrent.futures import ProcessPoolExecutor
    from minimal.spec import efficiency, gain
    with ProcessPoolExecutor(workers) as ex:
        rs = list(ex.map(_one, [(name, params, s, seconds) for s in seeds]))
    lives = [lived(r, seconds) for r in rs]
    t = sum(t for l in lives for _, _, t in l)
    return dict(eff=efficiency(lives), gain=gain(lives), food=10 * sum(a for l in lives for a, _, _ in l) / t,
                stranded=float(np.mean([l[2][0] == 0 for l in lives])),
                firings=float(np.mean([l.firings for l in lives])),
                power=float(np.mean([r["power"] for r in rs])), parts=rs[0]["parts"],
                wall=float(np.mean([r["wall"] for r in rs]))), lives


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("circuit")
    ap.add_argument("--seeds", default="0:8")
    ap.add_argument("--seconds", type=float, default=100.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--set", nargs="*", default=[])
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.seeds.split(":"))
    params = {k: float(v) for k, v in (s.split("=") for s in a.set)}
    r, _ = judge(a.circuit, params, range(lo, hi), a.seconds, a.workers)
    print(f"{a.circuit} {params}: parts {r['parts']}  eff {r['eff']:.2f}  gain {r['gain']:.2f}  food {r['food']:.2f}"
          f"  stranded {r['stranded']:.0%}  firings {r['firings']:.0f}/10s  power {r['power'] * 1e9:.1f} nW"
          f"  ({r['wall']:.0f} s a life)")


def bench(net: Netlist, seconds: float, nodes, supply: float = SUPPLY, pulses=(), step: float = 2e-5):
    """A circuit alone on the bench (no body): a transient over `seconds`, the eyes pulsing at the given (eye, time)s
    (eye "food" or "poison": a taste); returns (time, {node: voltage}, mean power)."""
    os.environ.setdefault("SPICE_LIB_DIR", os.path.join(NGROOT, "usr/share/ngspice"))
    ng = C.CDLL(LIB)
    keep = []
    for f in (SendChar, SendStat):
        keep.append(f(lambda s, i, u: 0))
    keep.append(Exit(lambda *a: 0))
    ng.ngSpice_Init(keep[0], keep[1], keep[2], None, None, None, None)
    lines = [f"bench"] + net.text(supply)
    lines = [ln for ln in lines if not ln.startswith(("I_eye", "I_taste"))]
    for k, node in ((0, net.eye[0]), (1, net.eye[1]), ("food", net.taste), ("poison", net.taste)):
        ts = [t for e, t in pulses if e == k]
        if ts:
            pts = " ".join(f"{t:g} 0 {t + 1e-6:g} {EYE:g} {t + PULSE:g} {EYE:g} {t + PULSE + 1e-6:g} 0" for t in ts)
            a, b = ("0", node) if k != "poison" else (node, "0")
            lines.append(f"I_bench{k} {a} {b} pwl(0 0 {pts})")
    lines.append(".end")
    arr = (C.c_char_p * (len(lines) + 1))(*[ln.encode() for ln in lines], None)
    with tempfile.TemporaryDirectory() as d:
        ng.ngSpice_Circ(arr)
        ng.ngSpice_Command(f"tran {step:g} {seconds:g} 0 {step:g} uic".encode())
        out = os.path.join(d, "out.txt")
        ng.ngSpice_Command(f"wrdata {out} i(VDD) " .encode() + " ".join(f"v({n})" for n in nodes).encode())
        data = np.loadtxt(out)
        for cmd in (b"destroy all", b"remcirc"):
            ng.ngSpice_Command(cmd)
    t = data[:, 0]
    V = {n: data[:, 3 + 2 * k] for k, n in enumerate(nodes)}
    power = -supply * float(np.trapezoid(data[:, 1], t) / (t[-1] - t[0]))
    return t, V, power
