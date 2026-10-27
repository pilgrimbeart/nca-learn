"""A circuit as transistors (the user's question, 2026-10-25: are the amplifier symbols honest? draw it in conventional
parts, so that SPICE can repeat the findings): any spec as a flat ngspice netlist of SkyWater's open SKY130 process's
1.8 V core transistors (sky130_fd_pr__nfet_01v8, __pfet_01v8), resistors, capacitors and diodes, on the chip's
supply (units.SUPPLY). Ideal sources stand only where a chip has a bias generator (each bias current and offset, a
gate's reference, two cascode biases) and for the body's pulses; analogue ground (0 V) is one buffer for the chip,
whose net current is measured (VAGND).

Each part of the simulator's model (mixed_feedback.py) becomes the blocks chip.py describes, from chip.py's own
decisions (so SPICE measures what the simulator reckons):

  node        a capacitor to ground; a leak, a resistor to analogue ground (on a chip a pseudo-resistor: no process
              has gigaohm resistors); its bias, a current from a rail; where the body's pulses enter, two clamp diodes
              to the rails (elsewhere the amplifiers' outputs can't pass the rails)
  element     a differential pair of nMOS reading the node against its offset, its tail current |gain|:
                tanh     Mead's wide-range transconductance amplifier (the pair and three current mirrors), giving
                         I tanh(slope (Vx - offset)) both ways
                sigmoid  one branch of the pair, mirrored into the node (or mirrored twice, to sink from it)
              every current mirror and tail a wide-swing cascode (4 transistors): a plain mirror of nfet_01v8 is off by
              11% for every volt across it (its drain lowers its barrier), whatever its length
  slope       a pair's own slope is set by physics (chip.NATIVE, kappa / U_T: about 26 /V for one branch, 13 /V for
              tanh): a little shallower by resistors in the pair's sources (degeneration); much shallower by a divider;
              steeper by a preamplifier (a degenerated wide-range amplifier into a resistor)
  level       a pair works only for offsets inside chip.RANGE: beyond, a source follower shifts the input
  gate        the tail current made by a second, degenerated pair reading the gate node against half a typical
              voltage, whose one branch (0 to |gain|, linear over about 0 to V_TYP) is mirrored into the element's tail
  filter      a follower (so that it doesn't load the node it reads), then a resistor and a capacitor
  memory      a SONOS cell (SKY130's flash transistor, charge trapped in a nitride layer: its threshold is the stored value,
              held for years, read by the gates of the pairs that read it: in SPICE, a capacitor that only gates
              touch), written by tunnelling: each write element's current flows into a node held at analogue ground
              and measured (V*_w), and drives a high-voltage pulse driver whose duty sets the tunnelling (SKY130's
              cell: 10.5 V across for 2 ms moves the threshold across its 3.7 V window); the PDK models only the
              cell's two end states, not its writing, so in SPICE the tunnelling is a current-controlled source
              (B*_w) of the write's current into the cell (less the driver's threshold), and the driver (two high-voltage switches per write) and
              the charge pumps (program and erase supplies, once for the chip) are counted, not simulated. A
              capacitor written by transistors' drains instead leaked: 0.1 to 3 pA, a bit lost in seconds

Then each element is trimmed, as an analogue chip is after fabrication: its bias current, slope resistor, offset and
gate adjusted from sweeps in SPICE until it matches the model's formula where it is used. What the transistors can't
match is the point of building it (`--check`): the gate's corners are rounded, a degenerated slope depends on the
current through the pair, a preamplified one saturates sooner, outputs stop about 0.2 V short of the supply's rails.

    python -m minimal.spice SPEC.json [--seed N]      the netlist (SPEC.cir), the circuit as built for seed N
    python -m minimal.spice SPEC.json --check         each element's block against the model's formula

The SKY130 models: a sparse clone of github.com/google/skywater-pdk-libs-sky130_fd_pr (models/, cells/**/*.spice and
*.pm3), at $SKY130_FD_PR (default ~/.local/opt/sky130_fd_pr); ngspice 42 or later.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chip  # noqa: E402
from chip import AUX, NATIVE, VGS_N, VSG_P  # noqa: E402
from units import I_TYP, SUPPLY, U_T, V_TYP  # noqa: E402

PDK = os.environ.get("SKY130_FD_PR", os.path.expanduser("~/.local/opt/sky130_fd_pr"))
NGSPICE = os.environ.get("NGSPICE", "ngspice")
NFET, PFET = "sky130_fd_pr__nfet_01v8", "sky130_fd_pr__pfet_01v8"
W, L = 4, 4                 # um: every transistor
HALF = SUPPLY / 2           # V: the supply's rails, +-HALF
VCN = -HALF + VGS_N + 0.15  # V: the cascodes' biases (a quarter of a volt more than a transistor's gate-source voltage
VCP = HALF - VSG_P - 0.15   # at 10 nA, so the mirrors below stay saturated)
SHIFT = 0.3                 # V: about what a source follower shifts by (trimmed out)
GATE_HALF = V_TYP / 2       # V: the gate's pair reads the gate node against this
PRE_DEGEN = 4.0             # a preamplifier's slope cut by this, so that its output can swing far enough
DIVIDER = 10e12             # ohms: a divider's two resistors together (so that it doesn't load the node it reads)
DIVIDER_C = 1e-12           # F: its two capacitors together
FILTER_C = 5e-12            # F: a filter's capacitor
DIODE = ".model dclamp d(is=1e-15 n=1)"
CLAMP = HALF - U_T * np.log(3 * I_TYP / 1e-15)  # V: the clamp diodes' references, so that a node the body pulses (3
                            # typical currents) stops at the supply's rails, as the simulator's nodes do


def models() -> str:
    """The include lines for the two 5 V transistors, typical corner (a cut of SKY130's sky130.lib.spice tt section
    and all.spice's parameters: the whole library doesn't load in ngspice unpatched)."""
    head = open(os.path.join(PDK, "models", "all.spice")).read().split("* include all individual diode models")[0]
    head = head.replace('.include "parameters/', f'.include "{PDK}/models/parameters/')
    cells = [f'.include "{PDK}/cells/{d}/sky130_fd_pr__{d}__{c}.corner.spice"'
             for d in (NFET[14:], PFET[14:]) for c in ("tt", "mismatch")]
    return head + ".param mc_mm_switch=0 mc_pr_switch=0\n" + "\n".join(cells) + "\n"


def degeneration(ratio: float, amps: float) -> float:
    """The source resistors (each) that cut a pair's slope by ratio (> 1) at a tail current of amps: the pair's
    transconductance per transistor, g = kappa (I/2) / U_T = NATIVE amps / 2, is cut by 1 + g R."""
    return max(ratio - 1.0, 0.0) / (NATIVE * amps / 2.0)


class Net:
    """A flat netlist being written: transistors, resistors, capacitors, diodes and sources, counted."""

    def __init__(self):
        self.lines, self.count = [], {"T": 0, "R": 0, "C": 0, "D": 0, "sources": 0}

    def n(self, name, d, g, s):
        self.lines.append(f"X{name} {d} {g} {s} vss {NFET} W={W} L={L}")
        self.count["T"] += 1

    def p(self, name, d, g, s):
        self.lines.append(f"X{name} {d} {g} {s} vdd {PFET} W={W} L={L}")
        self.count["T"] += 1

    def r(self, name, a, b, ohms):
        self.lines.append(f"R{name} {a} {b} {ohms:.6g}")
        self.count["R"] += 1

    def c(self, name, a, b, farads):
        self.lines.append(f"C{name} {a} {b} {farads:.6g}")
        self.count["C"] += 1

    def d(self, name, a, k):
        self.lines.append(f"D{name} {a} {k} dclamp")
        self.count["D"] += 1

    def v(self, name, node, volts):
        """A bias voltage (a chip's bias generator)."""
        self.lines.append(f"V{name} {node} 0 {volts:.6g}")
        self.count["sources"] += 1

    def i(self, name, frm, to, amps):
        """A bias current (a chip's bias generator), from frm to to."""
        self.lines.append(f"I{name} {frm} {to} {amps:.6g}")
        self.count["sources"] += 1

    def comment(self, text):
        self.lines.append(f"* {text}")

    # blocks

    def mirror_n(self, k, inp, out):
        """A wide-swing cascode nMOS mirror: the current flowing into inp is sunk from out."""
        self.n(f"{k}_c1", inp, "vcn", f"{k}_s1")
        self.n(f"{k}_m1", f"{k}_s1", inp, "vss")
        self.n(f"{k}_c2", out, "vcn", f"{k}_s2")
        self.n(f"{k}_m2", f"{k}_s2", inp, "vss")

    def mirror_p(self, k, inp, out):
        """A wide-swing cascode pMOS mirror: the current drawn out of inp is sourced into out."""
        self.p(f"{k}_c1", inp, "vcp", f"{k}_s1")
        self.p(f"{k}_m1", f"{k}_s1", inp, "vdd")
        self.p(f"{k}_c2", out, "vcp", f"{k}_s2")
        self.p(f"{k}_m2", f"{k}_s2", inp, "vdd")

    def tail(self, k, amps):
        """A tail current of amps (a bias current, mirrored); returns its node."""
        self.i(f"{k}_ib", "vdd", f"{k}_bin", amps)
        self.mirror_n(f"{k}_t", f"{k}_bin", f"{k}_tail")
        return f"{k}_tail"

    def pair(self, k, plus, minus, tail, degen=0.0):
        """A differential pair of nMOS (sources joined at tail, through resistors of degen ohms each if any); returns its
        drains (plus's, minus's)."""
        sp, sm = (f"{k}_sp", f"{k}_sm") if degen else (tail, tail)
        self.n(f"{k}_p", f"{k}_dp", plus, sp)
        self.n(f"{k}_m", f"{k}_dm", minus, sm)
        if degen:
            self.r(f"{k}_sp", sp, tail, degen)
            self.r(f"{k}_sm", sm, tail, degen)
        return f"{k}_dp", f"{k}_dm"

    def wide(self, k, plus, minus, out, tail, degen=0.0):
        """Mead's wide-range transconductance amplifier: I tanh(...) into out, positive while plus is above minus."""
        dp, dm = self.pair(k, plus, minus, tail, degen)
        self.mirror_p(f"{k}a", dp, out)                 # plus's current, sourced into out
        self.mirror_p(f"{k}b", dm, f"{k}_mid")          # minus's, mirrored twice to sink it from out
        self.mirror_n(f"{k}c", f"{k}_mid", out)

    def follower(self, k, x, out):
        """A unity-gain follower (a wide-range amplifier fed back): out copies x without loading it."""
        self.wide(k, x, out, out, self.tail(k, AUX))

    def shifter(self, k, x, out, up: bool):
        """A source follower: out = x shifted down (an nMOS, its source pulled down by a mirrored bias) or up (a
        pMOS, its source pulled up) by about SHIFT."""
        if up:
            self.i(f"{k}_ib", f"{k}_bin", "vss", AUX)
            self.mirror_p(f"{k}_l", f"{k}_bin", out)
            self.p(f"{k}_f", "vss", x, out)
        else:
            self.i(f"{k}_ib", "vdd", f"{k}_bin", AUX)
            self.mirror_n(f"{k}_l", f"{k}_bin", out)
            self.n(f"{k}_f", "vdd", x, out)


TRIM = {"amp": 1.0, "slope": 1.0, "off": 0.0, "shift": SHIFT, "gate": 1.0}


def element(net: Net, j: int, names: list, el, link, trim: dict = TRIM, x: str | None = None, out: str | None = None,
            gate_on: str | None = None) -> list:
    """Element j as transistors: el = (gain, offset, slope, tau, sigmoid), link = (to, from, gate); trim: its bias
    current, slope and offset adjusted (trim()); x, out, gate_on: other nets to read, drive and gate it by (to test it
    alone). Returns where its stages start: [(net, the share of its input's voltage)]."""
    gain, offset, slope, tau, sigmoid = el
    to, frm, gate = (int(v) for v in link)
    k = f"e{j}"
    out, x = out or names[to], x or names[frm]
    kind = "sigmoid" if sigmoid > 0.5 else "tanh"
    net.comment(f"element {j}: {names[to]} <- {kind}({slope:.3g} ({names[frm]} - {offset:.3g} V)) x {gain:.3g} A"
                + (f", gated by {names[gate]}" if gate >= 0 else "")
                + (f", its input filtered over {tau:.3g} s" if tau > 0 else ""))
    a = abs(slope) / chip.native(kind == "sigmoid") * trim["slope"]    # > 1: a preamplifier; < 1: degeneration or a
    off = offset + trim["off"]                                          # divider
    ics = []                                            # (net, x's share): where a stage starts, from its input
    share, _, _, level = chip.blocks(offset, slope, tau, kind == "sigmoid", trim["slope"], trim["off"])
    if share < 1:                                       # a compensated divider towards the middle of the pair's range
        mid, ref = f"{k}_dv", f"{k}_dref"               # (resistors and capacitors in the same ratio, as a scope's
        net.v(f"{k}_dref", ref, chip.CENTRE)            # probe): loading nothing, the offset scaled with it
        net.r(f"{k}_d1", x, mid, DIVIDER * (1 - share))
        net.r(f"{k}_d2", mid, ref, DIVIDER * share)
        net.c(f"{k}_d1", x, mid, DIVIDER_C * share)
        net.c(f"{k}_d2", mid, ref, DIVIDER_C * (1 - share))
        ics.append((mid, share))
        x, a, off = mid, a / share, chip.divided(off, share)
    if tau > 0:                                         # a follower (so that the filter doesn't load), R and C
        net.follower(f"{k}f", x, f"{k}_buf")
        net.r(f"{k}_f", f"{k}_buf", f"{k}_x", tau / FILTER_C)
        net.c(f"{k}_f", f"{k}_x", "0", FILTER_C)
        ics.append((f"{k}_x", share))
        x = f"{k}_x"
    up, down = level > 0, level < 0
    ref = f"{k}_off"
    shift = trim.get("shift", SHIFT)
    net.v(f"{k}_off", ref, off + shift * up - shift * down)
    if up or down:                                      # into the pair's range
        net.shifter(f"{k}s", x, f"{k}_lv", up)
        net.shifted = x                                 # (what it shifts: shift_of measures across it)
        x = f"{k}_lv"
    I = abs(gain) * trim["amp"]
    if gate >= 0:                                       # the tail made by the gate's pair
        gp, gm = net.pair(f"{k}g", gate_on or names[gate], f"{k}_half", net.tail(f"{k}g", I),
                          degen=GATE_HALF / I * trim.get("gate", 1.0))
        net.lines.append(f"V{k}g_dm vdd {gm} 0")        # the other branch straight to the rail (a wire)
        net.v(f"{k}_half", f"{k}_half", GATE_HALF)
        net.mirror_p(f"{k}gm", gp, f"{k}_bin")
        net.mirror_n(f"{k}_t", f"{k}_bin", f"{k}_tail")
        tail = f"{k}_tail"
    else:
        tail = net.tail(k, I)
    degen = 0.0
    if a > 1:                                           # a preamplifier into a resistor to the offset: its gain,
        pre = NATIVE / 2 / PRE_DEGEN                    # AUX x RL x its own (degenerated) slope, multiplies the pair's
        net.wide(f"{k}p", x, ref, f"{k}_pre", net.tail(f"{k}p", AUX), degen=degeneration(PRE_DEGEN, AUX))
        net.r(f"{k}_pl", f"{k}_pre", ref, a / (AUX * pre))
        x = f"{k}_pre"
    elif a < 1:
        degen = degeneration(1 / a, I)
    plus, minus = (x, ref) if slope > 0 else (ref, x)   # a negative slope: the pair reads the other way round
    if kind == "tanh":
        net.wide(f"{k}m", *((plus, minus) if gain > 0 else (minus, plus)), out, tail, degen)
    else:
        dp, dm = net.pair(f"{k}m", plus, minus, tail, degen)
        net.lines.append(f"V{k}_dm vdd {dm} 0")         # the other branch straight to the rail (a wire)
        if gain > 0:
            net.mirror_p(f"{k}o", dp, out)
        else:
            net.mirror_p(f"{k}o", dp, f"{k}_mid")
            net.mirror_n(f"{k}q", f"{k}_mid", out)
    return ics


def build(spec: dict, seed: int | None = None, substrate: str = "silicon"):
    """(the simulator's circuit, its node names for SPICE) of spec, as designed (no mismatch) or as built for seed (the
    simulator's mismatch, mixed_feedback.Circuit._arrays), every node where it settles at birth."""
    import mixed_feedback as mf
    from minimal.spec import make
    c = make(spec, substrate)(0 if seed is None else seed).circuit
    keep = mf.MISMATCH
    if seed is None:
        mf.MISMATCH = 0.0
    try:
        c._ready()
    finally:
        mf.MISMATCH = keep
    return c, ["n_" + n.lower() for n in c.names]


def header(title: str) -> list:
    return [f"* {title}", models(), DIODE, f"VDD vdd 0 {HALF:g}", f"VSS vss 0 {-HALF:g}", f"VCN vcn 0 {VCN:g}",
            f"VCP vcp 0 {VCP:g}", "VAGND agnd 0 0", f"VCLH vclh 0 {CLAMP:.4g}", f"VCLL vcll 0 {-CLAMP:.4g}"]


def node(net: Net, nm: str, bias: float, leak: float, cap: float, pulsed: bool, memory: bool = False) -> None:
    """A node as parts: its capacitor; its leak, a resistor to analogue ground; its bias, a current from the rail it
    comes from; where the body's pulses enter, clamp diodes, to references that stop it at the supply's rails; a memory,
    a SONOS cell (2 transistors, counted: its stored value the capacitor's voltage here)."""
    net.c(nm, nm, "0", cap)
    if memory:
        net.comment(f"{nm}: a SONOS cell (2 transistors, counted)")
        net.count["T"] += 2
    if leak > 0:
        net.r(f"{nm}_leak", nm, "agnd", 1 / leak)
    if bias > 0:                                        # a bias current, mirrored from a rail
        net.i(f"{nm}_bias", f"{nm}_bin", "vss", bias)
        net.mirror_p(f"{nm}_b", f"{nm}_bin", nm)
    elif bias < 0:
        net.i(f"{nm}_bias", "vdd", f"{nm}_bin", -bias)
        net.mirror_n(f"{nm}_b", f"{nm}_bin", nm)
    if pulsed:
        net.d(f"{nm}_hi", nm, "vclh")
        net.d(f"{nm}_lo", "vcll", nm)


def write(net: Net, j: int, mem: str, full: float) -> str:
    """Element j writing the memory mem by tunnelling: its current into a node held at analogue ground (V*_w measures
    it), and the same current into the cell less the driver's threshold (chip.DEAD of its full current: B*_w, the
    high-voltage driver's tunnelling, two switches, counted). Returns the node the element drives."""
    w, d = f"e{j}_w", chip.DEAD * full
    net.lines += [f"Ve{j}_w {w} agnd 0",
                  f"Be{j}_w 0 {mem} I = (i(Ve{j}_w) > {d:.4g}) ? i(Ve{j}_w) - {d:.4g} : "
                  f"((i(Ve{j}_w) < {-d:.4g}) ? i(Ve{j}_w) + {d:.4g} : 0)"]
    net.count["T"] += 2
    return w


PUMPS = 2           # the program and erase supplies (charge pumps), once for a chip with a memory: counted as sources


def count(spec: dict) -> dict:
    """The parts spec takes as transistors (chip.py's blocks, as designed): transistors, resistors, capacitors, diodes
    and bias sources (each a bias generator's output)."""
    names = [f"n{i}" for i in range(len(spec["nodes"]))]
    net = Net()
    pulsed = set(spec["sensors"]) | {spec["taste"]}
    memory = [bool(n[7]) for n in spec["nodes"]]
    for i, (_, bias, R, C, _, _, _, mem) in enumerate(spec["nodes"]):
        node(net, names[i], bias, 0.0 if R is None else 1.0 / R, C, i in pulsed, bool(mem))
    for j, (to, frm, gate, gain, offset, slope, tau, sigmoid) in enumerate(spec["elements"]):
        element(net, j, names, (gain, offset, slope, tau, float(sigmoid)), (to, frm, gate),
                out=f"e{j}_w" if memory[to] else None)
        if memory[to]:
            write(net, j, names[to], abs(gain))
    net.count["sources"] += PUMPS * any(memory)
    return dict(net.count)


def run(text: str, workdir: str) -> str:
    open(os.path.join(workdir, "circuit.cir"), "w").write(text)
    open(os.path.join(workdir, ".spiceinit"), "w").write("set ngbehavior=hsa\nset ng_nomodcheck\n")
    r = subprocess.run([NGSPICE, "-b", "circuit.cir"], cwd=workdir, capture_output=True, text=True)
    if r.returncode or "rror" in r.stdout:
        raise RuntimeError(r.stdout[-3000:] + r.stderr[-3000:])
    return r.stdout


def sweep(c, names, j: int, trim: dict, workdir: str, what: str = "x"):
    """Element j alone, as the model's element would be measured: its input swept over where it turns, its gate fully
    open (1.5 V) and its output held at the voltage its node settles at (a source, whose current is the element's);
    or (what) its gate swept from -0.5 to 1.5 V, or its output from rail to rail, its input where it gives its full
    current. (what was swept, measured current, model's current), and the parts counted."""
    el, link = c.el_arr[:, j], c.link[:, j]
    gain, offset, slope, tau, sig = el
    net = Net()
    element(net, j, names, el, link, trim, x="x", out="y", gate_on="gon")
    held = float(np.clip(c.V[int(link[0])], -SUPPLY / 2 + 0.25, SUPPLY / 2 - 0.25))
    full = float(np.clip(offset + 6 / slope, -HALF, HALF))     # the input giving its full current
    src, lo, hi = {"x": ("Vx", max(offset - 4 / abs(slope), -HALF + 0.05), min(offset + 4 / abs(slope), HALF - 0.05)),
                   "gate": ("Vgon", -0.5 * V_TYP, 1.5 * V_TYP), "out": ("Vy", -SUPPLY / 2, SUPPLY / 2)}[what]
    text = "\n".join(header(f"element {j}") + [f"Vx x 0 {full:.4g}", f"Vy y 0 {held:.4g}", f"Vgon gon 0 {1.5 * V_TYP:g}"]
                     + net.lines + [".options gmin=1e-18 abstol=1e-16 reltol=1e-5", ".control", "set wr_singlescale",
                                    f"dc {src} {lo:.5g} {hi:.5g} {(hi - lo) / 100:.5g}", "wrdata dc.txt i(Vy)", "quit",
                                    ".endc", ".end"]) + "\n"
    run(text, workdir)
    data = np.loadtxt(os.path.join(workdir, "dc.txt"))
    xs, ys = data[:, 0], data[:, 1]
    f = (lambda z: 1 / (1 + np.exp(-z))) if sig > 0.5 else np.tanh
    if what == "x":
        model = gain * f(slope * (xs - offset))
    else:
        model = gain * f(slope * (full - offset)) * (np.clip(xs / V_TYP, 0, 1) if what == "gate" else 1.0)
    return xs, ys, model, net.count


def fit(xs, ys, gain, offset, slope, sig):
    """(amplitude, centre, slope) of a measured element's current, as the model would describe it: least squares
    (Gauss-Newton, from the model's own values)."""
    u = ys / gain
    f = (lambda z: 1 / (1 + np.exp(-z))) if sig > 0.5 else np.tanh
    p = np.array([1.0, offset, slope])
    for _ in range(30):
        z = p[2] * (xs - p[1])
        r = u - p[0] * f(z)
        d = f(z) * (1 - f(z)) if sig > 0.5 else 1 - np.tanh(z) ** 2
        J = np.stack([f(z), -p[0] * p[2] * d, p[0] * (xs - p[1]) * d], axis=1)
        step = np.linalg.lstsq(J, r, rcond=None)[0]
        p = p + np.clip(step, [-0.5, -1 / abs(p[2]), -abs(p[2]) / 2], [0.5, 1 / abs(p[2]), abs(p[2]) / 2])
    return p[0], p[1], abs(p[2])


def shift_of(c, names, j, trim, workdir):
    """What element j's level shifter shifts by at its offset (its body effect makes it more than SHIFT)."""
    el, link = c.el_arr[:, j], c.link[:, j]
    net = Net()
    element(net, j, names, el, link, trim, x="x", out="y", gate_on="gon")
    text = "\n".join(header(f"element {j}") + [f"Vx x 0 {el[1] + trim['off']:.5g}", "Vy y 0 0", f"Vgon gon 0 {1.5 * V_TYP:g}"]
                     + net.lines + [".options gmin=1e-18 abstol=1e-16", ".control", "op",
                                    f"print v({net.shifted})-v(e{j}_lv)", "quit", ".endc", ".end"]) + "\n"
    out = run(text, workdir)
    return abs(float(out.split("=")[-1].split()[0]))


def trim(spec: dict, seed: int | None = None, rounds: int = 5) -> list:
    """Each element's trim: its bias current, slope and offset adjusted from sweeps until it matches the model's
    amplitude, centre and slope (as a chip is trimmed)."""
    c, names = build(spec, seed)
    trims = []
    with tempfile.TemporaryDirectory() as d:
        for j in range(c.el_arr.shape[1]):
            gain, offset, slope, tau, sig = c.el_arr[:, j]
            t = dict(TRIM)
            for _ in range(rounds):
                if chip.blocks(offset, slope, tau, sig > 0.5, t["slope"], t["off"])[3]:     # (a level shifter only
                    t["shift"] = shift_of(c, names, j, t, d)                        # where the pair can't reach)
                if c.link[2, j] >= 0:                   # the gate: 0.25 to 0.75 of full over 0.25 to 0.75 V_TYP
                    xs, ys, model, _ = sweep(c, names, j, t, d, "gate")
                    full = np.max(np.abs(model))
                    rise = (np.interp(0.75 * V_TYP, xs, ys) - np.interp(0.25 * V_TYP, xs, ys)) / full * np.sign(gain) / 0.5
                    t["gate"] *= rise
                xs, ys, model, _ = sweep(c, names, j, t, d)
                A, centre, s = fit(xs, ys, gain, offset, slope, sig)
                if not (A > 0 and s > 0 and np.isfinite(centre)):
                    raise RuntimeError(f"element {j} can't be trimmed: amplitude {A}, slope {s}, centre {centre}")
                t["amp"] /= A
                t["off"] += offset - centre
                t["slope"] *= abs(slope) / s
            trims.append(t)
    return trims


def netlist(spec: dict, seed: int | None = None, trims: list | None = None, pulses=None, seconds: float = 1.0,
            probe: str = "probe.txt", title: str = "circuit") -> tuple:
    """(the netlist, the parts counted). pulses: [(node index, current, start, length)], the body's; probe: the file
    every node's voltage is written to, every 0.125 ms."""
    c, names = build(spec, seed)
    nodes, el, link, V = c.node_arr, c.el_arr, c.link, c.V
    trims = trims or [TRIM] * el.shape[1]
    net = Net()
    pulsed = set(spec["sensors"]) | {spec["taste"]}
    for i, nm in enumerate(names):
        net.comment(f"node {c.names[i]}" + (" (memory)" if nodes[5, i] else ""))
        node(net, nm, nodes[0, i], nodes[1, i], nodes[2, i], i in pulsed, bool(nodes[5, i]))
    ic = [f"v({nm})={V[i]:.6g}" for i, nm in enumerate(names)]
    for j in range(el.shape[1]):
        to = int(link[0, j])
        out = f"e{j}_w" if nodes[5, to] else None
        ic += [f"v({n})={chip.divided(V[link[1, j]], share):.6g}"
               for n, share in element(net, j, names, el[:, j], link[:, j], trims[j], out=out)]
        if out:
            write(net, j, names[to], abs(el[0, j]))
    net.count["sources"] += PUMPS * bool(nodes[5].any())
    title += f": {len(names)} nodes, {el.shape[1]} elements" + ("" if seed is None else f", as built for seed {seed}")
    lines = header(title) + net.lines
    if pulses:
        lines.append("* the body's pulses (the body, not the brain)")
        by = {}
        for i, amps, t0, length in pulses:              # each node's pulses, summed where they overlap
            by.setdefault(i, []).extend([(t0, amps), (t0 + length, -amps)])
        for i, edges in by.items():
            pts, level, last, edge = ["0 0"], 0.0, 0.0, 1e-6
            for te, step in sorted(edges):
                te = max(te, last + 2 * edge)           # (edges closer than this merge into one)
                pts += [f"{te:.9g} {level:.6g}", f"{te + edge:.9g} {level + step:.6g}"]
                level, last = level + step, te
            lines.append(f"I_body_{names[i]} 0 {names[i]} PWL({' '.join(pts)})")
    lines += [".ic " + " ".join(ic), ".options gmin=1e-18 abstol=1e-15 reltol=1e-4 vntol=1e-7 method=gear itl4=100",
              ".control", "set wr_singlescale", "set wr_vecnames", "option numdgt=7",
              f"tran 0.125m {seconds:g} 0 0.125m", "linearize",
              f"wrdata {probe} " + " ".join(f"v({nm})" for nm in names), "quit", ".endc", ".end"]
    return "\n".join(lines) + "\n", net.count


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(a.spec))["spec"]
    name = os.path.basename(a.spec)[:-5]
    trims = trim(spec, a.seed)
    if a.check:
        c, names = build(spec, a.seed)
        with tempfile.TemporaryDirectory() as d:
            for j, t in enumerate(trims):
                to, frm, gate = (int(v) for v in c.link[:, j])
                xs, ys, model, cnt = sweep(c, names, j, t, d)
                err = np.max(np.abs(ys - model)) / np.max(np.abs(model))
                line = (f"element {j}, {c.names[to]} <- {c.names[frm]}" + (f" gated by {c.names[gate]}" if gate >= 0
                                                                            else "")
                        + f": {cnt['T']} transistors, {cnt['R']} resistors, {cnt['C']} capacitors; trim"
                          f" {t['amp']:.2f} x bias, {t['slope']:.2f} x slope, {t['off'] * 1e3:+.0f} mV\n"
                          f"  input: worst error {err:.1%} of its full current")
                if gate >= 0:
                    xs, ys, model, _ = sweep(c, names, j, t, d, "gate")
                    e = np.abs(ys - model) / np.max(np.abs(model))
                    line += (f"; gate: worst {e.max():.0%} (at {xs[e.argmax()]:+.2f} V), at 0/0.25/0.5/0.75/1 V "
                             + "/".join(f"{np.interp(v * V_TYP, xs, ys) / np.max(np.abs(model)):+.2f}" for v in
                                        (0, 0.25, 0.5, 0.75, 1)) + " of full")
                xs, ys, model, _ = sweep(c, names, j, t, d, "out")
                ok = np.abs(ys - model) <= 0.05 * np.max(np.abs(model))
                line += (f"; output within 5% from {xs[ok].min():+.2f} to {xs[ok].max():+.2f} V" if ok.any()
                         else "; output never within 5%")
                print(line, flush=True)
    else:
        text, parts = netlist(spec, a.seed, trims, title=name)
        open(f"{name}.cir", "w").write(text)
        json.dump(trims, open(f"{name}.trims.json", "w"), indent=1)
        print(f"{name}.cir: {parts}")
