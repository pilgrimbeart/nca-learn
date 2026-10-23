"""Draws the designed circuit (brains/designed.py) as a circuit: python schematic.py writes
media/designed_circuit.svg, and media/designed_circuit.png for the live view's schematic button. Only for redrawing it,
so not in requirements.txt: pip install schemdraw cairosvg pillow.

Every input and output is a terminal on the brain's boundary: transconductance amplifiers (op-amp symbols), RC
filters, sources, numbered nodes. Learning is in the circuit too: each plastic synapse's bias current is set by a
capacitor holding p, charged or emptied while the one taste input is good or bad, as fast as its sensor's eligibility
allows. One side assignment shown (S0 -> M0, S1 -> M1 strong); the coin toss may choose otherwise. The layout is
drawn by hand: change it here when the brain changes; the values, in SI (units.py), are read from the brain's code."""
import pathlib
import schemdraw
import schemdraw.elements as elm

from brains.circuit import SIDE, STRONG, STIMULUS, TASTE
from brains.designed import CP, ELIGIBLE, HUSH, LEARN
from units import C_TYP, I_TYP, PULSE, R_TYP, T_TYP, si

schemdraw.use("svg")
d = schemdraw.Drawing(show=False)
d.config(unit=2, fontsize=10, lw=1.1)
FS = 9
LEFT, RIGHT, TOP, BOTTOM = -7.0, 95.0, 4.0, -80.0      # the brain's boundary: everything crossing it is a terminal


def text(p, s, halign="left", size=FS, valign="center"):
    d.add(elm.Label().at(p).label(s, fontsize=size, halign=halign, valign=valign))


SEGMENTS = []                                               # every wire drawn, to check none run on top of another
SHADE = "#e6e6e6"
TINTS = {"NEURON": "#dceefa", "SYNAPSE": "#fbecd0", "LEARNING": "#d6f0e7", "HUSH": "#f8dccb", "TASTE": "#f1dce8"}
                    # each kind of part a pale Okabe-Ito tint (sky blue, orange, bluish green, vermilion, reddish
                    # purple), and titled too, so the colour is never the only cue (the user is colour-blind)


class Part:
    """One part of the brain (a neuron, a synapse, a cell), shaded and titled with what it does. Drawing inside
    `with part:` adds to it; the box is fitted round its symbols and labels when `shade_parts` runs, leaving out
    control lines and anything on the boundary, within the limits given (wires running in from elsewhere)."""
    ALL = []

    def __init__(self, title, xlim=(-1e9, 1e9), top=1e9):
        self.title, self.xlim, self.top, self.items = title, xlim, top, []
        Part.ALL.append(self)

    def __enter__(self):
        self.start = len(d.elements)
        return self

    def __exit__(self, *exc):
        self.items += d.elements[self.start:]


def shade_parts():
    for p in Part.ALL:
        boxes = []
        for e in p.items:
            if getattr(e, "_userparams", {}).get("ls") == "--":
                continue
            b = e.get_bbox(transform=True, includetext=True)
            if b.xmin > LEFT + 0.01 and b.xmax < RIGHT - 0.01:
                boxes.append(b)
        x0 = max(min(b.xmin for b in boxes), p.xlim[0]) - 0.5
        x1 = min(max(b.xmax for b in boxes), p.xlim[1]) + 0.5
        y0, y1 = min(b.ymin for b in boxes) - 0.4, min(max(b.ymax for b in boxes), p.top) + 1.3
        tint = TINTS.get(p.title.split()[0].rstrip(":"), SHADE)
        d.add(elm.Rect((x0, y0), (x1, y1), fill=tint).color(tint).at((0, 0)).theta(0).zorder(0))
        text((x0 + 0.3, y1 - 0.55), p.title, size=FS + 2)


def wire(*pts):
    for a, b in zip(pts, pts[1:]):
        d.add(elm.Line().at(a).to(b))
        SEGMENTS.append((tuple(map(float, a)), tuple(map(float, b))))


def dashed(*pts):
    for a, b in zip(pts, pts[1:]):
        d.add(elm.Line().at(a).to(b).linestyle("--").linewidth(0.8))
        SEGMENTS.append((tuple(map(float, a)), tuple(map(float, b))))


def overlaps():
    """Pairs of wires that run along the same line for some length."""
    out = []
    for i, (a, b) in enumerate(SEGMENTS):
        for c, e in SEGMENTS[i + 1:]:
            for k in (0, 1):                                 # both vertical (k=0) or both horizontal (k=1)
                if abs(a[k] - b[k]) < 1e-6 and abs(c[k] - e[k]) < 1e-6 and abs(a[k] - c[k]) < 1e-6:
                    lo = max(min(a[1 - k], b[1 - k]), min(c[1 - k], e[1 - k]))
                    hi = min(max(a[1 - k], b[1 - k]), max(c[1 - k], e[1 - k]))
                    if hi - lo > 1e-6:
                        out.append(((a, b), (c, e)))
    return out


def dot(p):
    d.add(elm.Dot(radius=0.09).at(p))


def terminal(p, label, halign, valign="center"):
    """A terminal on the boundary: an open circle, named outside the box."""
    d.add(elm.Dot(radius=0.16, open=True).at(p))
    dx = {"left": 0.4, "right": -0.4, "center": 0}[halign]
    dy = {"bottom": 0.4, "top": -0.4, "center": 0}[valign]
    text((p[0] + dx, p[1] + dy), label, halign, FS + 1, valign)


def hang(p, element, label, length=2.0):
    """An element hanging down from p to ground, its value written to its right."""
    e = element().at(p).down(length)
    d.add(e)
    d.add(elm.Ground().at(e.end))
    text((p[0] + 0.35, p[1] - length / 2), label)


def battery_to_ground(p, label, length=1.4, right=False):
    d.add(elm.Battery().at(p).down(length))
    d.add(elm.Ground().at((p[0], p[1] - length)))
    text((p[0] + (0.4 if right else -0.4), p[1] - length / 2), label, "left" if right else "right")


def ota(cx, cy, plus_top, label, sub=None, left=False):
    """A transconductance amplifier pointing right (or left): output current I_b * tanh(V+ - V-). Returns its
    anchors."""
    o = elm.Opamp(leads=True, flip=plus_top != left)
    o = (o.left() if left else o.right()).at((cx, cy)).anchor("center")
    d.add(o)
    text((cx - 0.5, cy + 1.3), label, "center")
    if sub:
        text((cx - 0.5, cy - 1.35), sub, "center")
    return o.absanchors


def follower_integrator(cx, cy, src_x, node, tau):
    """A unity follower charging a capacitor: the node follows the input with time constant tau."""
    a = ota(cx, cy, True, "follower")
    plus, minus, out = a["in2"], a["in1"], a["out"]
    wire((src_x, cy + 0.62), plus)
    loop_y = cy - 1.4
    wire(out, (out[0] + 0.4, out[1]), (out[0] + 0.4, loop_y), (minus[0] - 0.5, loop_y), (minus[0] - 0.5, minus[1]),
         minus)
    n = (out[0] + 1.0, out[1])
    wire((out[0] + 0.4, out[1]), n)
    dot(n)
    text((n[0] + 0.15, n[1] + 0.4), node, size=FS + 1)
    hang(n, elm.Capacitor, f"τ = {si(tau, 's')}")
    return n


def neuron(ox, oy, name, nv, ns, sensor):
    """One excitable neuron: membrane node (capacitor, leak, bias, noise), a fast positive-feedback element and a slow
    negative-feedback element. A sensor also has its stimulus: a current switched in by the body's terminal."""
    with Part(f"NEURON {name}: " + (f"a sensor, spikes when it sees colour {sensor}" if sensor is not None else
                                     "a motor, each spike fires a thruster")) as part:
        return draw_neuron(ox, oy, name, nv, ns, sensor), part


def draw_neuron(ox, oy, name, nv, ns, sensor):
    right = ox + 25
    wire((ox, oy), (right, oy))
    dot((ox + 1.2, oy))
    text((ox + 1.2, oy + 0.45), f"N{nv}  V({name})", size=FS + 1)
    for x, el, lab in ((2.8, elm.Capacitor, f"C = {si(C_TYP, 'F')}"), (4.8, elm.Resistor, f"R = {si(2 * R_TYP, 'Ω')}"),
                       (6.8, elm.SourceI, f"bias\n{si(1.6 * I_TYP, 'A')} out"),
                       (9.2, elm.SourceSin, "noise\n(a substrate's)")):
        hang((ox + x, oy), el, lab)
        dot((ox + x, oy))
    if sensor is not None:                                   # the stimulus: 3.0 switched in for one tick
        d.add(elm.Switch().at((ox, oy - 2.2)).up(2.2))
        d.add(elm.SourceI().at((ox, oy - 4.6)).up(2.4))
        d.add(elm.Ground().at((ox, oy - 4.6)))
        text((ox + 0.45, oy - 3.4), si(STIMULUS, "A"))
        dashed((LEFT, oy - 1.1), (ox - 0.35, oy - 1.1))
        terminal((LEFT, oy - 1.1), f"in: sees colour {sensor}\n({si(STIMULUS, 'A')} for\n{si(PULSE, 's')})", "right")
    a = ota(ox + 13.2, oy - 3.2, True, "fast +: the spike's rise", f"I_b = {si(2 * I_TYP, 'A')}")
    plus, minus, out = a["in2"], a["in1"], a["out"]
    wire((ox + 10.8, oy), (ox + 10.8, plus[1]), plus)
    dot((ox + 10.8, oy))
    wire(minus, (ox + 11.1, minus[1]), (ox + 11.1, oy - 5.0))
    battery_to_ground((ox + 11.1, oy - 5.0), "−1.5 V")
    wire(out, (out[0] + 0.4, out[1]), (out[0] + 0.4, oy))
    dot((out[0] + 0.4, oy))
    dot((ox + 16.0, oy))                                     # slow negative feedback through the recovery node
    wire((ox + 16.0, oy), (ox + 16.0, oy - 3.2 + 0.62))
    vs = follower_integrator(ox + 18.0, oy - 3.2, ox + 16.0, f"N{ns}", 10 * T_TYP)
    a = ota(ox + 23.4, oy - 3.2, False, "slow −: recovery", f"I_b = {si(2 * I_TYP, 'A')}")
    plus, minus, out = a["in2"], a["in1"], a["out"]
    wire(vs, (vs[0] + 0.6, vs[1]), (vs[0] + 0.6, minus[1]), minus)
    wire(plus, (plus[0] - 0.3, plus[1]), (plus[0] - 0.3, oy - 6.0))
    battery_to_ground((plus[0] - 0.3, oy - 6.0), "−1.5 V")
    end = (out[0] + 0.4, oy)                                 # the membrane's right end
    wire(out, (end[0], out[1]), end)
    wire((right, oy), end)
    dot(end)
    return end


def synapse(x, y, src, dst_x, node, title, weight, label_below=False):
    """The presynaptic membrane, followed fast (tau 1.25 ms), into an amplifier against 0 V; its output current goes to
    the postsynaptic membrane. Returns the amplifier's anchors (its bias pins) and its Part."""
    part = Part(title, (x + 0.5, x + 11.0))
    with part:
        a = draw_synapse(x, y, src, dst_x, node, weight, label_below)
    return a, part


def draw_synapse(x, y, src, dst_x, node, weight, label_below):
    dot((src, y + 0.62))
    n = follower_integrator(x + 2.5, y, src, node, 0.5 * T_TYP)
    a = ota(x + 9.0, y, True, "" if label_below else "σ  (slope 5)")
    if label_below:
        text((x + 9.6, y - 1.3), "σ  (slope 5)")
    plus, minus, out = a["in2"], a["in1"], a["out"]
    wire(n, (n[0] + 0.9, n[1]), (n[0] + 0.9, plus[1]), plus)
    wire(minus, (minus[0] - 0.25, minus[1]), (minus[0] - 0.25, minus[1] - 0.6))
    d.add(elm.Ground().at((minus[0] - 0.25, minus[1] - 0.6)))
    text((out[0] + 1.6, out[1] + 0.45), weight, valign="bottom")
    wire(out, (dst_x, out[1]))
    return a


def bias_source(pin, up, label, control, ctl_y):
    """A voltage-controlled current source from an amplifier's bias pin (down to ground, or up then round to
    ground), setting its bias current I_b; control: the node whose voltage sets it, reached by a dashed line from
    (control, ctl_y). Returns nothing."""
    vx = pin[0]
    src = elm.SourceControlledI().at(pin)
    d.add(src.up(3.2) if up else src.down(3.2))
    end = (vx, pin[1] + (3.2 if up else -3.2))
    if up:
        wire(end, (vx, end[1] + 0.4), (vx + 0.8, end[1] + 0.4), (vx + 0.8, end[1] + 0.1))
        d.add(elm.Ground().at((vx + 0.8, end[1] + 0.1)))
    else:
        d.add(elm.Ground().at(end))
    mid = (pin[1] + end[1]) / 2
    text((vx + 1.4 if up else vx + 0.4, mid + (0.9 if up else -0.9)), label, size=FS)    # clear of the ground
    return mid


TASTE_Y, ROW = -51.0, {0: -54.0, 1: -56.0}                # the taste node's wire; each sensor's membrane, carried down
ROW_X = {0: 27.0, 1: 28.0}


def taste_node():
    """The one taste input: a current 3 nA x taste into the taste node (R 0.5 GOhm, C 2.5 pF), whose wire runs to every learning
    cell."""
    with Part("TASTE: one input for both learning cells", (-1e9, 6.5)):
        draw_taste(1.0)


def draw_taste(x):
    src = elm.SourceControlledI().at((x, TASTE_Y - 3.0)).up(3.0)
    d.add(src)
    d.add(elm.Ground().at((x, TASTE_Y - 3.0)))
    dashed((LEFT, TASTE_Y - 1.5), (x - 0.4, TASTE_Y - 1.5))
    text((x + 0.45, TASTE_Y - 2.4), f"{si(TASTE, 'A')}·taste")
    terminal((LEFT, TASTE_Y - 1.5), "in: taste\n+1 food, −1 poison,\nfor 1 tick when a block\ntouches the mouth; else 0",
             "right")
    wire((x, TASTE_Y), (LEFT_CELL[1] + 11.2, TASTE_Y))
    dot((x, TASTE_Y))
    text((x + 0.2, TASTE_Y + 0.45), "N17  taste", size=FS + 1)
    for dx, el, lab in ((3.0, elm.Capacitor, f"C = {si(C_TYP, 'F')}"), (5.0, elm.Resistor, f"R = {si(0.5 * R_TYP, 'Ω')}")):
        hang((x + dx, TASTE_Y), el, lab)
        dot((x + dx, TASTE_Y))


LEFT_CELL = {0: 31.0, 1: 63.0}


def cell(k, a, syn, enode, pnode):
    """Sensor k's learning cell. E: its eligibility node (C 25 pF, R 4 GOhm, clamped 0..1 V), charged by a spike of its own
    sensor and emptied by one of the other's. P: a capacitor holding p (no leak, clamped 0..1 V, 0.5 V at birth),
    charged while taste is good and discharged while it is bad, by two amplifiers whose bias currents E sets. P sets
    the plastic synapse's bias current. a: that synapse's amplifier."""
    with Part(f"LEARNING CELL {k}: sets p{k}, the weight of S{k} → M{1 - k}", top=-59.0):
        draw_cell(k, enode, pnode)
    pin = min(a["vd"], a["vs"], key=lambda q: q[1]) if k == 0 else max(a["vd"], a["vs"], key=lambda q: q[1])
    with syn:                                                # P sets the plastic synapse's bias current
        mid = bias_source(pin, k == 1, f"I_b = {si(STRONG, 'A')}·V({pnode.split()[-1]})/V\nthe synapse's weight", None,
                          None)
    px, py = LEFT_CELL[k] + 24.0, -74.0
    cx = px + 1.6 if k == 0 else 58.6
    dot((px, py + 1.4))
    if k == 0:
        dashed((px, py + 1.4), (cx, py + 1.4), (cx, mid), (pin[0] + 0.3, mid))
    else:
        dashed((px, py + 1.4), (px + 1.6, py + 1.4), (px + 1.6, -78.0), (cx, -78.0), (cx, mid), (pin[0] + 0.3, mid))


def draw_cell(k, enode, pnode):
    x0 = LEFT_CELL[k]
    # eligibility: own spike charges, the other's empties
    ys = (-61.0, -69.0)
    ex = x0 + 8.0
    for j, (src, sign, y) in enumerate(((k, "+", ys[0]), (1 - k, "−", ys[1]))):
        o = ota(x0 + 4.0, y, True, f"σ  {sign}10")
        text((x0 + 3.5, y - 2.5), "own spike: charges E" if j == 0 else "other's spike: empties E", "center", FS)
        plus, minus, out = o["in2"], o["in1"], o["out"]
        vx = x0 + 0.4 + 0.6 * src
        dot((vx, ROW[src]))
        wire((vx, ROW[src]), (vx, plus[1]), plus)
        wire(minus, (minus[0] - 0.25, minus[1]), (minus[0] - 0.25, minus[1] - 0.6))
        d.add(elm.Ground().at((minus[0] - 0.25, minus[1] - 0.6)))
        wire(out, (ex, out[1]))
    ey = -74.0
    wire((ex, ys[0]), (ex, ys[1]))
    wire((ex, ys[1]), (ex, ey))
    dot((ex, ys[1]))
    dot((ex, ey))
    text((ex + 0.2, ey + 0.45), enode, size=FS + 1)
    hang((ex, ey), elm.Capacitor, f"C = {si(10 * C_TYP, 'F')}")
    wire((ex, ey), (ex + 2.4, ey))
    hang((ex + 2.4, ey), elm.Resistor, f"R = {si(ELIGIBLE / (10 * C_TYP), 'Ω')}\nclamped 0..1 V")
    # p: taste good charges P, bad discharges it, each as fast as E allows
    gx, px = x0 + 17.0, x0 + 24.0
    tx = x0 + 11.2
    mids = []
    for j, (y, lab, sub, ref) in enumerate(((ys[0], "σ  good", "charges P while taste > 0.5", "0.5"),
                                            (ys[1], "σ  bad", "empties P while taste < −0.5", "−0.5"))):
        o = ota(gx, y, j == 0, lab, None)
        plus, minus, out = o["in2"], o["in1"], o["out"]
        tin = plus if j == 0 else minus
        ref_in = minus if j == 0 else plus
        dot((tx, TASTE_Y)) if j == 0 else None
        wire((tx, TASTE_Y), (tx, tin[1]), tin) if j == 0 else wire((tx, ys[0] + 0.62), (tx, tin[1]), tin)
        if j == 1:
            dot((tx, ys[0] + 0.62))
        bx = ref_in[0] - 1.1
        wire(ref_in, (bx, ref_in[1]), (bx, ref_in[1] - 0.2))
        battery_to_ground((bx, ref_in[1] - 0.2), ref, 0.8)
        wire(out, (px, out[1]))
        pin = min(o["vd"], o["vs"], key=lambda q: q[1])
        mid = bias_source(pin, False, "", None, None)
        dashed((ex + 1.4, mid), (pin[0] - 0.3, mid))
        mids.append(mid)
        text((pin[0] + 0.5, mid), f"I_b = {si(LEARN * CP / (1.3 * T_TYP), 'A')}·V({enode.split()[-1]})/V\n{sub}", size=FS)
    dashed((ex, ey + 1.2), (ex + 1.4, ey + 1.2), (ex + 1.4, mids[0]))   # E sets both sources' currents
    dot((ex, ey + 1.2))
    dot((ex + 1.4, mids[1]))
    wire((px, ys[0]), (px, ys[1]))
    py = -74.0
    wire((px, ys[1]), (px, py))
    dot((px, ys[1]))
    dot((px, py))
    text((px + 0.2, py + 0.45), pnode, size=FS + 1)
    hang((px, py), elm.Capacitor, f"C = {si(CP, 'F')}: holds p{k}\nclamped 0..1 V, 0.5 V at birth")
    text((x0 + 0.2, -77.6), f"E{k} holds how much more S{k} has spiked lately than S{1 - k}. A good taste raises p{k}, "
         f"a bad one lowers it, each as fast as E{k} allows.", size=FS)


def hush(k, x, y, s):
    """Sensor k's hush cell: its spike charges H (C 25 pF, R 4 GOhm, clamped 0..1 V) through a sigmoid; while H is above
    0.5 V a second sigmoid draws current out of the other sensor's membrane. Its first amplifier at (x, y); the cell
    runs right (s = 1) or left (s = -1). Returns that amplifier's anchors and the second's output."""
    a = ota(x, y, True, "σ  +10", left=s < 0)
    plus, minus, out = a["in2"], a["in1"], a["out"]
    g = minus[0] - 0.25 * s
    wire(minus, (g, minus[1]), (g, minus[1] - 0.6))
    d.add(elm.Ground().at((g, minus[1] - 0.6)))
    hx = out[0] + 1.6 * s                                    # the hush node
    wire(out, (hx, y))
    dot((hx, y))
    text((hx - 0.6 if s > 0 else hx - 1.0, y + 0.45), f"N{18 + k}  H{k}", size=FS + 1)
    hang((hx, y), elm.Capacitor, f"C = {si(10 * C_TYP, 'F')}")
    rx = hx + 1.6 * s
    wire((hx, y), (rx, y))
    hang((rx, y), elm.Resistor, f"R = {si(HUSH / (10 * C_TYP), 'Ω')}")
    b = ota(rx + 3.9 * s, y, False, "σ  −1.5  (slope 10)", left=s < 0)
    plus, minus, out = b["in2"], b["in1"], b["out"]
    jx = rx + 0.8 * s
    wire((rx, y), (jx, y), (jx, minus[1]), minus)
    bx = plus[0] - 0.25 * s
    wire(plus, (bx, plus[1]), (bx, plus[1] - 0.4))
    battery_to_ground((bx, plus[1] - 0.4), "0.5", 0.8, right=s < 0)
    return a, out


def hush_cells():
    """Each sensor hushes the other: S1's cell (above) feeds S0's membrane, S0's (below) feeds S1's."""
    with Part("HUSH CELL H1: S1 quiets S0", (14.1, 1e9)):
        a, out = hush(1, 15.2, -13.5, 1)
        text((14.3, -17.4), "S1's spike charges H1 (clamped 0..1 V);\nabove 0.5 V, H1 draws current out of S0",
             size=FS)
    plus = a["in2"]
    wire((12.5, -38.0), (12.5, plus[1]), plus)               # V(S1), up from S1's membrane
    dot((12.5, -38.0))
    wire(out, (26.2, out[1]), (26.2, 0.0))                   # into S0's membrane
    dot((26.2, 0.0))
    with Part("HUSH CELL H0: S0 quiets S1", (14.1, 1e9)):
        a, out = hush(0, 24.5, -23.5, -1)
        text((14.3, -27.9), "S0's spike charges H0 (clamped 0..1 V);\nabove 0.5 V, H0 draws current out of S1",
             size=FS)
    plus = a["in2"]
    wire((27.0, plus[1]), plus)                              # V(S0), from its wire to the synapses
    dot((27.0, plus[1]))
    wire(out, (13.6, out[1]), (13.6, -38.0))                 # into S1's membrane
    dot((13.6, -38.0))


def key(x, y):
    """The key: a small sample of each symbol, and what it means. (Samples are not wires: they skip the overlap check.)"""
    text((x, y), "KEY", size=FS + 2)
    rows = [
        (lambda p: elm.Opamp(leads=False, flip=True).right().at(p).anchor("in1").scale(0.55),
         "transconductance amplifier: output current I_b·tanh(V+ − V−), I_b its bias current;\n"
         "\"σ\": a sigmoid, an amplifier plus a constant current"),
        (lambda p: elm.Capacitor().right().at(p).length(1.6), "capacitor: a node's charge (with a follower before it: a low-pass filter, τ)"),
        (lambda p: elm.Resistor().right().at(p).length(1.6), "resistor: a node's leak"),
        (lambda p: elm.SourceI().right().at(p).length(1.6), "constant current source (a neuron's bias)"),
        (lambda p: elm.SourceControlledI().right().at(p).length(1.6),
         "controlled current source: its current is set by the voltage on its dashed line; the arrow is its direction"),
        (lambda p: elm.SourceSin().right().at(p).length(1.6), "noise source"),
        (lambda p: elm.Battery().right().at(p).length(1.6), "fixed voltage: a reference for an amplifier's input"),
        (lambda p: elm.Switch().right().at(p).length(1.6), "switch, closed by an input"),
        (lambda p: elm.Line().right().at(p).length(1.6), "wire: carries current"),
        (lambda p: elm.Line().right().at(p).length(1.6).linestyle("--").linewidth(0.8),
         "control line: sets a value, carries no current (round everything: the brain's boundary)"),
        (lambda p: elm.Dot(radius=0.09).at((p[0] + 0.8, p[1])),
         "junction: wires meeting at a dot are joined; wires crossing without one are not"),
        (lambda p: elm.Dot(radius=0.16, open=True).at((p[0] + 0.8, p[1])), "terminal: where the body connects"),
        (lambda p: elm.Ground().at((p[0] + 0.8, p[1] + 0.25)), "ground: 0 V"),
        (lambda p: elm.Rect((0, -0.4), (1.6, 0.4), fill=SHADE).color(SHADE).at(p).theta(0).zorder(0),
         "shaded box: one part of the brain, titled with what it does"),
    ]
    for i, (sample, meaning) in enumerate(rows):
        yy = y - 1.6 - i * 1.75 - (0.5 if i else 0.0)
        d.add(sample((x, yy)))
        text((x + 2.3, yy), meaning, size=FS)


s0, _ = neuron(0, 0, "S0", 1, 2, 0)
s1, _ = neuron(0, -38, "S1", 3, 4, 1)
MX = 62
m0 = neuron(MX, 0, "M0", 5, 6, None)
m1 = neuron(MX, -38, "M1", 7, 8, None)
SX, A0, A1 = 30.5, 27.0, 28.0
wire(s0, (A0, 0), (A0, -11 + 0.62))
wire((A0, -11 + 0.62), (A0, ROW[0]))
wire(s1, (A1, -38), (A1, -28 + 0.62))
wire((A1, -38), (A1, ROW[1]))
dot((A0, -11 + 0.62)); dot((A1, -38))
wire((A0, ROW[0]), (LEFT_CELL[1] + 0.4, ROW[0]))
wire((A1, ROW[1]), (LEFT_CELL[1] + 1.0, ROW[1]))
text((A0 - 0.3, ROW[0] - 0.1), "V(S0)", "right", FS); text((A1 - 1.3, ROW[1] - 0.1), "V(S1)", "right", FS)
synapse(SX, -4, A0, MX - 1.8, "N9", "SYNAPSE S0 → M0: fixed", f"weight {si(SIDE, 'A')}: relays every spike of S0 to M0")
a10, syn10 = synapse(SX, -11, A0, MX - 1.0, "N10", "SYNAPSE S0 → M1: learns",
                     f"weight {si(STRONG, 'A')}·p0: relays S0's spikes to M1 while p0 is high")
a11, syn11 = synapse(SX, -28, A1, MX - 1.8, "N11", "SYNAPSE S1 → M0: learns",
                     f"weight {si(STRONG, 'A')}·p1: relays S1's spikes to M0 while p1 is high", True)
synapse(SX, -35, A1, MX - 1.0, "N12", "SYNAPSE S1 → M1: fixed", f"weight {si(SIDE, 'A')}: relays every spike of S1 to M1")
taste_node()
hush_cells()
key(-5.0, -10.0)
cell(0, a10, syn10, "N13  E0", "N14  P0")
cell(1, a11, syn11, "N15  E1", "N16  P1")
wire((MX - 1.8, -28), (MX - 1.8, 0), (MX, 0))                       # into M0: S0 in full, S1 through p1
wire((MX - 1.0, -11), (MX - 1.0, -38), (MX, -38))                   # into M1: S0 through p0, S1 in full
for p in ((MX - 1.8, -4), (MX - 1.0, -35)):
    dot(p)
for ((rx, ry), part), k in ((m0, 0), (m1, 1)):                     # spike detectors: comparators with hysteresis
    with part:
        a = ota(rx + 3.4, ry - 2.2, True, "comparator")
        plus, minus, out = a["in2"], a["in1"], a["out"]
        wire((rx, ry), (rx + 0.7, ry), (rx + 0.7, plus[1]), plus)
        wire(minus, (minus[0] - 0.3, minus[1]), (minus[0] - 0.3, minus[1] - 0.6))
        d.add(elm.Ground().at((minus[0] - 0.3, minus[1] - 0.6)))
        text((out[0] + 0.4, out[1] - 0.5), "high above 0 V,\nlow below −1 V", valign="top")
    wire(out, (RIGHT, out[1]))
    terminal((RIGHT, out[1]), f"out: motor {k}\n(each rising edge\nfires its thruster)", "left")
dashed((LEFT, TOP), (RIGHT, TOP), (RIGHT, BOTTOM), (LEFT, BOTTOM), (LEFT, TOP))
text((LEFT + 0.3, TOP - 0.5), "the brain: everything inside this line; the body connects only at the terminals ○",
     valign="top")
text((LEFT, TOP + 4.6), "The designed circuit: four neurons (sensors S0, S1; motors M0, M1), four synapses (two fixed, "
     "two that learn), two hush cells by which each sensor quiets the other, two learning cells and the taste. Each "
     "shaded box is one of these parts, titled with what it does.", size=FS + 3)
text((LEFT, TOP + 3.5), "Each triangle is a transconductance amplifier, output current I_b·tanh(V+ − V−); followers "
     "with a capacitor are low-pass filters. Nodes N1–N19; ground is 0 V. Values in SI (units.py); a tick of the "
     "world is 10 ms.", size=FS + 1)
text((LEFT, TOP + 2.5), "Shown: S0 relays every spike to M0 and S1 to M1 (each sensor's side is a coin toss at "
     "birth). The body decides what each sensor sees, which thruster each motor fires, and the taste when a block "
     "touches the mouth: one input, saying nothing of which sensor saw it.", size=FS + 1)
shade_parts()
for x in (LEFT - 9.0, RIGHT + 8.0):                                  # room for the terminals' names
    d.add(elm.Line().at((x, 0)).to((x + 0.01, 0)).color("white"))
bad = overlaps()
assert not bad, bad
OUT = pathlib.Path(__file__).parent / "media"
d.save(str(OUT / "designed_circuit.svg"))
import cairosvg                                                      # noqa: E402
from PIL import Image                                                # noqa: E402
cairosvg.svg2png(url=str(OUT / "designed_circuit.svg"), write_to=str(OUT / "designed_circuit.png"), output_width=4800,
                 background_color="white")
Image.open(OUT / "designed_circuit.png").convert("RGB").save(OUT / "designed_circuit.png", optimize=True)
print("wrote", OUT / "designed_circuit.svg", "and", OUT / "designed_circuit.png")
