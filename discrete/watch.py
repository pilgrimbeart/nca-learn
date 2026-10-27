"""Watching a discrete circuit live (discrete/NOTEBOOK.md): creature.py's live view, all food, with the brain a netlist
running in ngspice tick by tick beside the body, as discrete/life.py runs it, but with ngspice in its own background
thread so that the window keeps the main one. The left panel shows the schematic (discrete/draw.py) and each node's
voltage over the last moments, the min and max of each short bin, so that a motor's brief dip at a beat shows.

    python -m discrete.watch [--seed 0] [--circuit hold_drive straight] [--poison] [--record DIR --until S]

--poison: one colour poison (as creature.py's lives), for a circuit that learns (learn_hold); --record: no window,
every frame saved there as a PNG. b switches circuit (a new world, the same seed), r a new life; the rest as creature.py's live view. Each circuit runs
with its seed's own part tolerances, as in a judged life.
"""

from __future__ import annotations

import ctypes as C
import json
import os
import sys
import threading
import time
from collections import deque

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from discrete.life import EYE, FALL, RISE, STEP, SUPPLY  # noqa: E402
from minimal.spice_life import (LIB, NGROOT, BGRunning, Exit, GetISRC, GetSync, GetVSRC, SendChar,  # noqa: E402
                                SendData, SendInit, SendStat)
from units import PULSE, TICK  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = 0.5e-3            # s: a trace keeps each node's min and max over this long ...
WINDOW = 0.5            # s: ... for this long back
SECONDS = 3600.0        # s: how long ngspice is told to run (a life watched is stopped long before)

SHOWN = {               # circuit: (results file, schematic or None, [(node, label, colour, volts shown)])
    "hold_drive": ("hold_drive_screened.json", "hold_drive_14.png",
                   [("h", "h  hold", (86, 180, 233), 3.0), ("a", "a  timing", (230, 159, 0), 1.2),
                    ("m0", "m0  motor A (scan)", (44, 193, 151), 3.0), ("m1", "m1  motor B (drive)", (224, 141, 192), 3.0)]),
    "straight": ("straight_tuned.json", None,
                 [("a", "a  timing", (230, 159, 0), 1.2), ("b", "b  beat", (230, 159, 0), 1.2),
                  ("m", "m  both motors", (44, 193, 151), 3.0)]),
    "learn_hold": ("learn_hold_tuned.json", "learn_hold.png",
                   [("h", "h  hold", (86, 180, 233), 3.0), ("c0", "c0  the bit (high: eye 0 shorted)", (230, 159, 0), 3.0),
                    ("q", "q  doubt (taste)", (204, 121, 167), 3.0), ("m1", "m1  motor B (drive)", (224, 141, 192), 3.0)]),
    "learn_avoid": ("learn_avoid_tuned.json", "learn_avoid.png",
                    [("h", "h  hold", (86, 180, 233), 3.0), ("c0", "c0  the bit (high: eye 0 shorted)", (230, 159, 0), 3.0),
                     ("u", "u  giving up (low: drive on)", (240, 228, 66), 3.0),
                     ("m1", "m1  motor B (drive)", (224, 141, 192), 3.0)]),
}

_current = None         # the brain ngspice is running now: one circuit at a time in a process
_keep = []              # every callback handed to ngspice, kept alive


class LiveSpice:
    """The brain creature.Life talks to (as discrete/life.py's SpiceBrain), with ngspice in its background thread:
    step lets ngspice run to the tick's end and returns the motors that fired there."""

    def __init__(self, name: str, seed: int):
        from discrete.circuits import CIRCUITS
        global _current
        if _current is not None:
            _current.stop()
        results, picture, self.nodes = SHOWN[name]
        path = os.path.join(HERE, "results", results)
        params = json.load(open(path))["best"] if os.path.exists(path) else {}     # (untuned: the builder's values)
        build, self.supply = CIRCUITS[name]
        self.net = build(np.random.default_rng(seed + 5_000_011), **params)    # this seed's parts, as when judged
        self.name, self.seed = name, seed
        self.picture = os.path.join(HERE, "..", "media", picture) if picture else None
        self.image = None
        self.base, self.queued, self.pulses = 0.0, [], {0: [], 1: [], 2: [], 3: []}   # eyes, taste (food, poison)
        self.spikes = [0, 0]
        self.go, self.ready = threading.Event(), threading.Event()
        self.started = self.done = False
        self.st = {"next": TICK, "idx": None, "armed": [True, True], "count": [0, 0], "t": 0.0, "energy": 0.0,
                   "out": []}
        self.bins = {n: deque(maxlen=int(WINDOW / BIN)) for n, *_ in self.nodes}
        self.acc = {n: None for n, *_ in self.nodes}
        self.bin_end = BIN
        self.firings = [0, 0]
        _current = self

    # the brain's interface
    def stimulate(self, sensor, at):
        self.queued.append((sensor, self.base + at, self.base + at + PULSE))

    def taste(self, value, at):
        if value:
            self.queued.append((2 if value > 0 else 3, self.base + at, self.base + at + PULSE))

    def step(self):
        if not self.started:
            self.start()
        self.ready.set()
        self.go.wait()
        self.go.clear()
        self.base += TICK
        return [m for m in (0, 1) for _ in range(self.spikes[m])]

    def drive(self, sensor):
        return 1.0

    def built(self):
        return True

    def stage(self):
        return "scanning"

    # ngspice
    def schedule(self):
        for k, a, b in self.queued:
            self.pulses[k].append((a, b))
            self.ng.ngSpice_SetBkpt(C.c_double(a))
            self.ng.ngSpice_SetBkpt(C.c_double(b))
        self.queued.clear()
        for k in self.pulses:
            self.pulses[k] = [p for p in self.pulses[k] if p[1] > self.st["t"] - TICK]
        self.ng.ngSpice_SetBkpt(C.c_double(self.st["next"]))

    def start(self):
        os.environ.setdefault("SPICE_LIB_DIR", os.path.join(NGROOT, "usr/share/ngspice"))
        ng = self.ng = C.CDLL(LIB)
        st, net, supply = self.st, self.net, self.supply
        hi, lo = RISE * supply, FALL * supply
        motors = list(dict.fromkeys(net.motor))
        shown = [n for n, *_ in self.nodes]

        @SendChar
        def on_char(s, i, u):
            st["out"].append(s.decode(errors="replace"))
            return 0

        @SendStat
        def on_stat(s, i, u):
            return 0

        @Exit
        def on_exit(status, unload, quit_, i, u):
            return 0

        @SendData
        def on_data(vals, n, i, u):
            if self.done:
                return 0
            v = vals.contents
            if st["idx"] is None:
                nm = [v.vecsa[k].contents.name.decode().lower() for k in range(v.veccount)]
                find = lambda s: next((k for k, x in enumerate(nm) if x in (s, f"v({s})", s[2:-1] + "#branch")), None)
                st["idx"] = ([find(m) for m in net.motor], find("time"), find("i(vdd)"), [find(p) for p in shown])
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
            while t >= self.bin_end:                    # the traces: each node's min and max over a bin
                for name in shown:
                    if self.acc[name] is not None:
                        self.bins[name].append(self.acc[name])
                        self.acc[name] = None
                self.bin_end += BIN
            for name, k in zip(shown, kp):
                x = v.vecsa[k].contents.creal
                a = self.acc[name]
                self.acc[name] = (x, x) if a is None else (min(a[0], x), max(a[1], x))
            if t >= st["next"] - 1e-9:
                self.spikes = st["count"][:]
                self.firings = [a + b for a, b in zip(self.firings, self.spikes)]
                st["count"] = [0, 0]
                st["next"] += TICK
                self.ready.clear()
                self.go.set()
                self.ready.wait()
                if not self.done:
                    self.schedule()
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
            on = lambda k: sum(a <= t < b for a, b in self.pulses[k])
            val[0] = EYE * (on(2) - on(3) if "taste" in name else on(int(name[-1])))
            return 0

        @GetSync
        def on_sync(t, dt, olddt, redo, i, loc, u):
            return 0

        _keep.append((on_char, on_stat, on_exit, on_data, on_init, on_bg, on_vsrc, on_isrc, on_sync))
        ng.ngSpice_Init(on_char, on_stat, on_exit, on_data, on_init, on_bg, None)
        ident = C.c_int(0)
        ng.ngSpice_Init_Sync(on_vsrc, on_isrc, on_sync, C.byref(ident), None)
        ng.ngSpice_Command(b"set ng_nomodcheck")
        lines = [f"discrete watch, seed {self.seed}"] + net.text(supply)
        lines += [".save " + " ".join(f"v({m})" for m in motors) + " i(VDD) "
                  + " ".join(f"v({p})" for p in shown if p not in motors),
                  f".tran {STEP / 4:g} {SECONDS:g} 0 {STEP:g} uic", ".end"]
        arr = (C.c_char_p * (len(lines) + 1))(*[ln.encode() for ln in lines], None)
        if ng.ngSpice_Circ(arr):
            raise RuntimeError("ngspice wouldn't load the circuit:\n" + "".join(st["out"][-30:]))
        self.schedule()
        self.started = True
        ng.ngSpice_Command(b"bg_run")

    def stop(self):
        """Halt ngspice and unload the circuit (a new life, or another circuit, is starting)."""
        if not self.started or self.done:
            self.done = True
            return
        self.done = True
        self.ready.set()
        self.ng.ngSpice_Command(b"bg_halt")
        t0 = time.time()
        while self.ng.ngSpice_running() and time.time() - t0 < 5:
            time.sleep(0.01)
        for cmd in (b"destroy all", b"remcirc"):
            self.ng.ngSpice_Command(cmd)

    # watching
    def draw(self, screen, side: int, font, sensors: list, motors: list, lit) -> None:
        """The schematic above (if drawn), each shown node's voltage over the last WINDOW below: min to max of each
        bin, a dashed line at the motors' threshold; power and firing rates."""
        import pygame
        screen.fill((20, 24, 28))
        top = 0
        if self.picture:
            if self.image is None or self.image[0] != side:
                img = pygame.image.load(self.picture)
                w, h = img.get_size()
                self.image = (side, pygame.transform.smoothscale(img, (side, int(side * h / w))))
            screen.blit(self.image[1], (0, 0))
            top = self.image[1].get_height() + 4
        t = self.st["t"]
        power = self.st["energy"] / max(t, 1e-9)
        info = (f"{self.name}: {self.net.parts()} parts   {power * 1e9:.0f} nW   SPICE t {t:.2f} s   "
                f"firings A {self.firings[0]}, B {self.firings[1]}")
        screen.blit(font.render(info, True, (230, 230, 230)), (6, top))
        top += 22
        rows = self.nodes
        h = (side - top) // len(rows)
        n = int(WINDOW / BIN)
        for i, (node, label, colour, vmax) in enumerate(rows):
            y0 = top + i * h
            pygame.draw.rect(screen, (32, 37, 42), (0, y0 + 2, side, h - 4))
            Y = lambda v: y0 + h - 4 - int(min(max(v, 0.0), vmax) / vmax * (h - 10))
            if vmax > 2:
                for x in range(0, side, 8):             # the motors' threshold, 2 V: dashed
                    pygame.draw.line(screen, (110, 110, 110), (x, Y(RISE * self.supply)),
                                     (x + 3, Y(RISE * self.supply)))
            bins = list(self.bins[node])
            for k, (a, b) in enumerate(bins):
                x = side - (len(bins) - k) * side // n
                pygame.draw.line(screen, colour, (x, Y(a)), (x, Y(b)), 2 if side > n else 1)
            screen.blit(font.render(f"{label}  (0-{vmax:g} V)", True, colour, (32, 37, 42)), (6, y0 + 4))
        screen.blit(font.render(f"last {WINDOW:g} s", True, (150, 150, 150)), (side - 80, side - 20))


def main():
    import argparse
    import creature
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--circuit", nargs="+", default=["hold_drive", "straight"], choices=list(SHOWN))
    ap.add_argument("--poison", action="store_true")
    ap.add_argument("--record", default=None)
    ap.add_argument("--until", type=float, default=100.0)
    a = ap.parse_args()
    creature.BRAINS.clear()                             # only the discrete circuits, b switching among them
    for name in a.circuit:
        dict.__setitem__(creature.BRAINS, name, lambda seed, name=name: LiveSpice(name, seed))
    try:
        creature.watch(a.seed, a.circuit[0], record=a.record, until=a.until, all_food=not a.poison)
    finally:
        if _current is not None:
            _current.stop()


if __name__ == "__main__":
    main()
