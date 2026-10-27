"""Closed loop in SPICE (the user's request, 2026-10-25: is the simulator accurate enough to trust the findings?): a
circuit as transistors (minimal/spice.py's netlist, as built for the seed and trimmed) lives real lives, the body
(creature.Life) and ngspice running together, tick by tick. ngspice runs as a library (libngspice, through ctypes);
the body's pulses enter by external current sources, whose value ngspice asks for at each time point; at each tick's
end (a breakpoint, so a time point falls on it) the body takes the motors' spikes over the tick, moves, eats, and
gives the next tick's pulses (each pulse's edges breakpoints too). The body runs in its own thread, waiting in
brain.step() while ngspice runs the tick, so that creature.Life lives it unchanged.

What SPICE adds: the transistors' own behaviour (slopes, rounded gates, outputs near the rails, leakage, the memory
node's drift). What it leaves out: noise (no transient noise; the circuit is as built, with the simulator's mismatch
for the seed, then trimmed); SKY130's own mismatch. Power is what the supply delivers (its two rails, and
analogue ground's net current to a rail).

    python -m minimal.spice_life SPEC.json [--seeds 100:116] [--seconds 100] [--workers 4]

writes minimal/results/spice_life_NAME_SUPPLYV.json: each life lived in SPICE and in the simulator (silicon) on the same
seed, paired.
"""

from __future__ import annotations

import ctypes as C
import json
import os
import sys
import tempfile
import threading
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from minimal import spice  # noqa: E402
from units import I_TYP, PULSE, TICK  # noqa: E402

NGROOT = os.path.expanduser(os.environ.get("NGSPICE_ROOT", "~/.local/opt/ngspice/root"))
LIB = os.path.join(NGROOT, "usr/lib/x86_64-linux-gnu/libngspice.so.0")


class VecValues(C.Structure):
    _fields_ = [("name", C.c_char_p), ("creal", C.c_double), ("cimag", C.c_double), ("is_scale", C.c_bool),
                ("is_complex", C.c_bool)]


class VecValuesAll(C.Structure):
    _fields_ = [("veccount", C.c_int), ("vecindex", C.c_int), ("vecsa", C.POINTER(C.POINTER(VecValues)))]


SendChar = C.CFUNCTYPE(C.c_int, C.c_char_p, C.c_int, C.c_void_p)
SendStat = C.CFUNCTYPE(C.c_int, C.c_char_p, C.c_int, C.c_void_p)
Exit = C.CFUNCTYPE(C.c_int, C.c_int, C.c_bool, C.c_bool, C.c_int, C.c_void_p)
SendData = C.CFUNCTYPE(C.c_int, C.POINTER(VecValuesAll), C.c_int, C.c_int, C.c_void_p)
SendInit = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_int, C.c_void_p)
BGRunning = C.CFUNCTYPE(C.c_int, C.c_bool, C.c_int, C.c_void_p)
GetVSRC = C.CFUNCTYPE(C.c_int, C.POINTER(C.c_double), C.c_double, C.c_char_p, C.c_int, C.c_void_p)
GetISRC = C.CFUNCTYPE(C.c_int, C.POINTER(C.c_double), C.c_double, C.c_char_p, C.c_int, C.c_void_p)
GetSync = C.CFUNCTYPE(C.c_int, C.c_double, C.POINTER(C.c_double), C.c_double, C.c_int, C.c_int, C.c_int, C.c_void_p)


class SpiceBrain:
    """The brain creature.Life talks to: stimulate and taste queue pulses for the next tick; step waits while ngspice
    runs the tick, then returns the motors that fired."""

    def __init__(self, sensors, motors, taste_node):
        self.sensors, self.motors, self.taste_node = sensors, motors, taste_node
        self.base = 0.0                                 # when the next tick starts
        self.queued = []                                # (node, amps, start, end)
        self.spikes = None
        self.go, self.ready = threading.Event(), threading.Event()

    def stimulate(self, sensor, at):
        from brains.circuit import PULSES
        self.queued.append((self.sensors[sensor], PULSES * I_TYP, self.base + at, self.base + at + PULSE))

    def taste(self, value, at):
        from brains.circuit import PULSES
        self.queued.append((self.taste_node, PULSES * I_TYP * value, self.base + at, self.base + at + PULSE))

    def step(self):
        self.ready.set()                                # the tick's pulses are queued: ngspice may run it
        self.go.wait()
        self.go.clear()
        self.base += TICK
        return [m for m, n in enumerate(self.spikes) for _ in range(n)]

    def drive(self, sensor):
        return 1.0


def live(spec: dict, seed: int, poison: str, seconds: float, trims=None) -> dict:
    """One life of spec as transistors, closed loop: meals, firings, when it first moved, power, spikes per motor."""
    from creature import Life
    from mixed_feedback import SPIKE
    from units import V_TYP
    os.environ.setdefault("SPICE_LIB_DIR", os.path.join(NGROOT, "usr/share/ngspice"))
    ng = C.CDLL(LIB)
    trims = trims or spice.trim(spec, seed)
    c, names = spice.build(spec, seed)
    text, count = spice.netlist(spec, seed, trims, title=f"closed loop, seed {seed}")
    text = text.split(".control")[0]
    inputs = sorted(set(spec["sensors"]) | {spec["taste"]})
    src = {f"i_body_{names[i]}": i for i in inputs}
    lines = text.splitlines()[:-1] if text.rstrip().endswith(".end") else text.splitlines()
    lines += [f"I_body_{names[i]} 0 {names[i]} dc 0 external" for i in inputs]
    lines += [".save " + " ".join(f"v({n})" for n in names) + " i(VDD) i(VSS) i(VAGND)", ".end"]

    brain = SpiceBrain(list(spec["sensors"]), list(spec["motors"]), spec["taste"])
    pulses = {i: [] for i in inputs}
    ticks = int(round(seconds / TICK))
    st = {"next": TICK, "idx": None, "armed": [True, True], "count": [0, 0], "t": 0.0, "energy": 0.0,
          "done": False, "out": [], "err": None, "V": None}
    motors = [names[m] for m in spec["motors"]]

    def schedule():
        for node, amps, a, b in brain.queued:
            pulses[node].append((a, b, amps))
            ng.ngSpice_SetBkpt(C.c_double(a))
            ng.ngSpice_SetBkpt(C.c_double(b))
        brain.queued.clear()
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
        if st["idx"] is None:                           # the vectors' places, the first time
            nm = [v.vecsa[k].contents.name.decode().lower() for k in range(v.veccount)]
            alias = lambda s: (s, f"v({s})", s[2:-1] + "#branch" if s.startswith("i(") else s)
            find = lambda s: next((k for k, x in enumerate(nm) if x in alias(s)), None)
            st["idx"] = ([find(m) for m in motors], find("time"), find("i(vdd)"), find("i(vss)"), find("i(vagnd)"))
            if None in st["idx"][0] or None in st["idx"][1:]:
                st["err"] = f"vectors not found among {nm}"
                raise SystemExit
        (k0, k1), kt, kd, ks, kg = st["idx"]
        t = v.vecsa[kt].contents.creal
        p = spice.HALF * (-v.vecsa[kd].contents.creal + v.vecsa[ks].contents.creal + abs(v.vecsa[kg].contents.creal))
        st["energy"] += p * (t - st["t"])
        st["t"] = t
        for m, k in enumerate((k0, k1)):
            x = v.vecsa[k].contents.creal
            if st["armed"][m] and x > SPIKE:
                st["count"][m] += 1
                st["armed"][m] = False
            elif x < -V_TYP:
                st["armed"][m] = True
        if t >= st["next"] - 1e-9 and not st["done"]:   # a tick's end: the body's turn
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
        node = src.get(name.decode().lower())
        x = 0.0
        if node is not None:
            for a, b, amps in pulses[node]:
                if a <= t < b:
                    x += amps
        val[0] = x                                      # (into the node: the source runs from ground to it)
        return 0

    @GetSync
    def on_sync(t, dt, olddt, redo, i, loc, u):
        return 0

    keep = (on_char, on_stat, on_exit, on_data, on_init, on_bg, on_vsrc, on_isrc, on_sync)
    ng.ngSpice_Init(on_char, on_stat, on_exit, on_data, on_init, on_bg, None)
    ident = C.c_int(0)
    ng.ngSpice_Init_Sync(on_vsrc, on_isrc, on_sync, C.byref(ident), None)
    for cmd in ("set ngbehavior=hsa", "set ng_nomodcheck"):
        ng.ngSpice_Command(cmd.encode())
    arr = (C.c_char_p * (len(lines) + 1))(*[ln.encode() for ln in lines], None)

    result = {}

    def body():
        try:
            lf = Life(seed, poison, brain=lambda s: brain)
            while lf.t < ticks:
                lf.step()
            result.update(meals=lf.meals, firings=len(lf.firings), moving=lf.moving)
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
            brain.ready.wait()                          # tick 0's pulses
            if ng.ngSpice_Circ(arr):
                raise RuntimeError("ngspice wouldn't load the circuit:\n" + "\n".join(st["out"][-30:]))
            schedule()
            t0 = time.time()
            ng.ngSpice_Command(f"tran {TICK / 80:g} {seconds:g} 0 {TICK / 80:g}".encode())
            wall = time.time() - t0
        finally:
            os.chdir(cwd)
    th.join(5)
    del keep
    if "error" in result or "meals" not in result:
        raise RuntimeError(f"seed {seed} {poison}: {result.get('error')} {st['err']}\n" + "\n".join(st["out"][-20:]))
    return {"seed": seed, "poison": poison, "meals": [(int(a), b) for a, b in result["meals"]],
            "firings": result["firings"], "moving": result["moving"], "power": st["energy"] / max(st["t"], 1e-12),
            "reached": st["t"], "wall": wall, "parts": count}


def simulated(spec, seed, poison, seconds) -> dict:
    """The same life in the simulator (silicon, as built for the seed)."""
    from creature import Life
    from minimal.spec import make
    lf = Life(seed, poison, brain=make(spec, "silicon"))
    while lf.t < int(round(seconds / TICK)):
        lf.step()
    return {"seed": seed, "poison": poison, "meals": [(int(a), b) for a, b in lf.meals], "firings": len(lf.firings),
            "moving": lf.moving, "power": lf.brain.circuit.power()}


def job(a):
    spec, seed, seconds = a
    trims = spice.trim(spec, seed)
    out = []
    for poison in ("red", "blue"):
        out.append(("spice", live(spec, seed, poison, seconds, trims)))
        out.append(("sim", simulated(spec, seed, poison, seconds)))
    return out


def lived(r, seconds):
    """A life's record as minimal.spec judges it (Lived)."""
    from minimal.spec import SPAN, Lived, thirds
    ticks = int(round(seconds / TICK))
    l = Lived(thirds(r["meals"], r["moving"], ticks, r["poison"]))
    l.power, l.firings, l.substrate = r["power"], SPAN * r["firings"] / seconds, "silicon"
    return l


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--seeds", default="100:116")
    ap.add_argument("--seconds", type=float, default=100.0)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    from minimal.spec import load
    from units import SUPPLY
    spec = load(a.spec)
    name = f"{os.path.basename(a.spec)[:-5]}_{SUPPLY:g}V"
    lo, hi = (int(x) for x in a.seeds.split(":"))
    path = os.path.join(os.path.dirname(__file__), "results", f"spice_life_{name}.json")
    done = json.load(open(path)) if os.path.exists(path) else {"spice": [], "sim": []}
    have = {r["seed"] for r in done["spice"]}
    seeds = [s for s in range(lo, hi) if s not in have]
    with ProcessPoolExecutor(a.workers) as ex:
        for res in ex.map(job, [(spec, s, a.seconds) for s in seeds]):
            for kind, r in res:
                done[kind].append(r)
                print(f"{kind:5s} seed {r['seed']} {r['poison']:4s}: food {sum(c != r['poison'] for _, c in r['meals'])}"
                      f", poison {sum(c == r['poison'] for _, c in r['meals'])}, firings {r['firings']}"
                      + (f", {r['wall']:.0f} s" if kind == "spice" else ""), flush=True)
            json.dump(done, open(path, "w"))
