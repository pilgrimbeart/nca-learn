"""Draws a circuit of the minimal search from its spec, so any design can be drawn and redrawn when it changes:
python -m minimal.draw RESULTS.json [...] writes media/NAME.svg, two drawings of the same circuit, one above the other.

The signal-flow graph (above): each circle is a state, a voltage held by a capacitor (a memory node, a floating gate,
a square), with its capacitor, its leak (a resistor to its rest voltage) and any clamp written beside it; each arrow
is an active device, an amplifier reading the voltage at its tail and pushing a current into the capacitor at its
head, labelled with its current (gain), what it reads (tanh or sigmoid, slope and offset) and its input filter's time
constant; an arrow into its own node is a loop; a gated amplifier has a dotted line from its gate node. It shows who
drives whom, and the loops.

The schematic (below): every part, as it would be built, laid out as a crossbar so that any design draws the same
way. Each net is a horizontal wire, its capacitor, leak resistor and rest voltage hanging to ground at its left end;
each element is an amplifier symbol in a column of its own below the nets, wired up from the net it reads and back to
the net it drives, with a series transistor fed from its gate net if gated and a resistor and capacitor on its input
if filtered; a dot marks a joint, and wires crossing without one don't connect. The body's eyes and taste come in as
current sources on the left, the thrusters go out on the right. Its parts can be counted on the page.

Values in SI (units.py). Colour-blind-safe (Okabe-Ito), and never colour alone (the user is colour-blind): a current
in blue and solid, a current out vermilion and dashed, a gate orange, a memory node sky blue. Layout of both: sensors
and taste first, motors last, the rest between, in the order the spec lists them.
"""

from __future__ import annotations

import json
import math
import os
import sys
from html import escape

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from minimal.spec import parts  # noqa: E402
from units import si  # noqa: E402

W, H, R = 1500, 800, 26
INK, MID, BG = "#111", "#555", "#fff"
EXCITE, INHIBIT, GATE, MEMORY, NODE = "#0072B2", "#D55E00", "#E69F00", "#56B4E9", "#F2F2F2"   # Okabe-Ito


def layout(spec: dict) -> dict:
    """Each node's (x, y): sensors and taste in the left column, motors in the right, the rest in columns between."""
    n = len(spec["nodes"])
    left = [*spec["sensors"], spec["taste"]]
    right = [m for m in dict.fromkeys(spec["motors"]) if m not in left]
    middle = [i for i in range(n) if i not in left and i not in right]
    cols = [left] + [middle[k::2] for k in range(2) if middle[k::2]] + [right]
    pos = {}
    for c, col in enumerate(cols):
        x = 200 + c * (W - 560) / max(1, len(cols) - 1)
        for k, i in enumerate(col):
            pos[i] = (x, 130 + (k + 0.5) * (H - 220) / len(col))
    return pos


def node_label(nd) -> str:
    name, bias, R_, C, lo, hi, start, memory = nd
    out = [f"C {si(C, 'F')}"]
    if R_ is not None:
        out.append(f"R {si(R_, 'Ω')} to {bias * R_:+.2f} V")
    elif bias:
        out.append(f"{si(bias, 'A')} in")
    if lo is not None or hi is not None:
        out.append(f"clamped {lo if lo is not None else '-'}..{hi if hi is not None else '-'} V")
    if start is not None:
        out.append(f"born at {start:.2f} V")
    return out


def element_label(e) -> str:
    _, _, _, gain, offset, slope, tau, sigmoid = e
    f = "σ" if sigmoid else "tanh"
    text = f"{si(gain, 'A')} {f}({slope:.3g}(V {'-' if offset >= 0 else '+'} {abs(offset):.2f}))"
    return text + (f", τ {si(tau, 's')}" if tau > 0 else "")


def order(spec: dict) -> list:
    """The nodes in drawing order: sensors and taste, the rest as the spec lists them, motors last."""
    left = [*spec["sensors"], spec["taste"]]
    right = [m for m in dict.fromkeys(spec["motors"]) if m not in left]
    return left + [i for i in range(len(spec["nodes"])) if i not in left and i not in right] + right


def graph(spec: dict, y0: float) -> list:
    """The signal-flow graph, its top at y0: (SVG elements)."""
    pos = {i: (x, y + y0) for i, (x, y) in layout(spec).items()}
    names = [nd[0] for nd in spec["nodes"]]
    out = []
    pairs = {}
    for e in spec["elements"]:
        pairs[(e[1], e[0])] = pairs.get((e[1], e[0]), 0) + 1
    seen = {}
    for e in spec["elements"]:
        to, frm, gate = e[0], e[1], e[2]
        kind, colour = ("out", INHIBIT) if e[3] < 0 else ("in", EXCITE)
        style = f'stroke="{colour}" stroke-width="1.8"' + (' stroke-dasharray="7,5"' if e[3] < 0 else "")
        k = seen[(frm, to)] = seen.get((frm, to), 0) + 1
        (x0, ya), (x1, yb) = pos[frm], pos[to]
        anchor = "start"
        if frm == to:                                   # loops on the node's outer side, one above another
            s_ = 1 if frm in (*spec["sensors"], spec["taste"]) else -1   # (away from its terminal: left of a motor)
            cy = ya - 18 + 36 * (k - 1)
            out.append(f'<path d="M{x0 + s_ * 20},{cy - 8} C{x0 + s_ * 75},{cy - 30} {x0 + s_ * 75},{cy + 14} '
                       f'{x0 + s_ * 22},{cy + 6}" fill="none" {style} marker-end="url(#{kind})"/>')
            mx, my = x0 + s_ * 62, cy - 8
            lx, ly, anchor = x0 + s_ * 80, cy - 2, "start" if s_ > 0 else "end"
        else:
            dx, dy = x1 - x0, yb - ya
            d = math.hypot(dx, dy)
            ux, uy = dx / d, dy / d
            bend = (k - (pairs[(frm, to)] + 1) / 2) * 60 + (30 if (to, frm) in pairs else 0)
            sx, sy, ex, ey = x0 + ux * R, ya + uy * R, x1 - ux * (R + 4), yb - uy * (R + 4)
            mx, my = (sx + ex) / 2 - uy * bend, (sy + ey) / 2 + ux * bend
            out.append(f'<path d="M{sx:.0f},{sy:.0f} Q{mx:.0f},{my:.0f} {ex:.0f},{ey:.0f}" fill="none" '
                       f'{style} marker-end="url(#{kind})"/>')
            mx, my = (sx + 2 * mx + ex) / 4, (sy + 2 * my + ey) / 4
            side = 1 if bend >= 0 else -1               # (the label on the outside of its curve)
            lx, ly = mx - uy * 14 * side, my + ux * 14 * side + 4
            anchor = "middle"
        if gate >= 0:                                   # the gate: a dotted line to the arrow's middle
            gx, gy = pos[gate]
            out.append(f'<line x1="{gx:.0f}" y1="{gy:.0f}" x2="{mx:.0f}" y2="{my:.0f}" stroke="{GATE}" '
                       f'stroke-width="2" stroke-dasharray="2,4" stroke-linecap="round"/><circle cx="{mx:.0f}" '
                       f'cy="{my:.0f}" r="4" fill="{GATE}"/>')
        label = element_label(e) + (f" × V({names[gate]})" if gate >= 0 else "")
        for paint in (f'fill="{BG}" stroke="{BG}" stroke-width="3"', f'fill="{colour}"'):   # a halo, then the text
            out.append(f'<text x="{lx:.0f}" y="{ly:.0f}" font-size="10.5" text-anchor="{anchor}" {paint}>'
                       f'{escape(label)}</text>')
    for i, nd in enumerate(spec["nodes"]):
        x, y = pos[i]
        if nd[7]:
            out.append(f'<rect x="{x - R}" y="{y - R}" width="{2 * R}" height="{2 * R}" fill="{MEMORY}" '
                       f'stroke="{INK}" stroke-width="2"/>')
        else:
            out.append(f'<circle cx="{x}" cy="{y}" r="{R}" fill="{NODE}" stroke="{INK}" stroke-width="2"/>')
        out.append(f'<text x="{x}" y="{y + 5}" font-size="15" text-anchor="middle" fill="{INK}">{escape(nd[0])}</text>')
        for k, line in enumerate(node_label(nd)):
            out.append(f'<text x="{x}" y="{y + R + 15 + 13 * k}" font-size="10.5" text-anchor="middle" '
                       f'fill="{INK}">{escape(line)}</text>')
    for i, text, side in terminals(spec):
        x, y = pos[i]
        bx = 20 if side < 0 else W - 140
        out.append(f'<rect x="{bx}" y="{y - 12}" width="120" height="24" fill="{BG}" stroke="{MID}"/>'
                   f'<text x="{bx + 60}" y="{y + 4}" font-size="12" text-anchor="middle" fill="{INK}">{escape(text)}</text>'
                   f'<line x1="{bx + 120 if side < 0 else bx}" y1="{y}" x2="{x + side * R}" y2="{y}" stroke="{MID}"/>')
    out.append(f'<text x="20" y="{y0 + H - 16}" font-size="12" fill="{MID}">circle: a state, a voltage held by a '
               'capacitor; square: a memory node (a floating gate); arrow: an amplifier, reading the voltage at its '
               'tail and pushing a current into the capacitor at its head (blue solid: in, vermilion dashed: out); '
               'orange dotted: its gate</text>')
    return out


def terminals(spec: dict) -> list:
    """The body's terminals: (node, label, side: -1 left, +1 right)."""
    return [(spec["sensors"][0], "eye (a colour)", -1), (spec["sensors"][1], "eye (the other)", -1),
            (spec["taste"], "taste (±1)", -1)] + [(m, f"thruster {k}", 1) for k, m in enumerate(spec["motors"])]


RS, CW, LX = 100, 150, 560      # the schematic: the spacing of its nets and its columns, and where the nets begin


def ground(x: float, y: float) -> str:
    return (f'<line x1="{x - 9}" y1="{y}" x2="{x + 9}" y2="{y}" stroke="{INK}" stroke-width="1.5"/>'
            f'<line x1="{x - 5}" y1="{y + 4}" x2="{x + 5}" y2="{y + 4}" stroke="{INK}" stroke-width="1.5"/>'
            f'<line x1="{x - 2}" y1="{y + 8}" x2="{x + 2}" y2="{y + 8}" stroke="{INK}" stroke-width="1.5"/>')


def capacitor(x: float, y: float, colour: str = INK, fill: str = "none") -> str:
    """A capacitor hanging down from (x, y) to ground (its top plate at y + 14)."""
    return (f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + 14}" stroke="{INK}"/>'
            + (f'<rect x="{x - 15}" y="{y + 10}" width="30" height="12" fill="{fill}" stroke="none"/>' if fill != "none" else "")
            + f'<line x1="{x - 11}" y1="{y + 14}" x2="{x + 11}" y2="{y + 14}" stroke="{colour}" stroke-width="2.5"/>'
            f'<line x1="{x - 11}" y1="{y + 19}" x2="{x + 11}" y2="{y + 19}" stroke="{colour}" stroke-width="2.5"/>'
            f'<line x1="{x}" y1="{y + 19}" x2="{x}" y2="{y + 32}" stroke="{INK}"/>' + ground(x, y + 32))


def resistor(x0: float, y0: float, x1: float, y1: float) -> str:
    """A zigzag resistor from (x0, y0) to (x1, y1), straight or upright."""
    n, pts = 6, []
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    for k in range(n + 1):
        t = 0.2 + 0.6 * k / n
        w = 0 if k in (0, n) else (5 if k % 2 else -5)
        pts.append((x0 + ux * L * t - uy * w, y0 + uy * L * t + ux * w))
    path = f"M{x0},{y0} L{pts[0][0]:.1f},{pts[0][1]:.1f} " + " ".join(f"L{a:.1f},{b:.1f}" for a, b in pts[1:])
    return f'<path d="{path} L{x1},{y1}" fill="none" stroke="{INK}" stroke-width="1.4"/>'


def text(x, y, s, size=10.5, colour=INK, anchor="start", weight="normal") -> str:
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" text-anchor="{anchor}" fill="{colour}" '
            f'font-weight="{weight}">{escape(s)}</text>')


def dot(x, y) -> str:
    return f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3.5" fill="{INK}"/>'


def schematic(spec: dict, y0: float) -> tuple:
    """The component schematic, its top at y0: (SVG elements, its width, its height)."""
    names = [nd[0] for nd in spec["nodes"]]
    rows = order(spec)
    ny = {i: y0 + 90 + k * RS for k, i in enumerate(rows)}
    els = spec["elements"]
    xr = LX + 40 + len(els) * CW                        # where the nets end
    yb = ny[rows[-1]] + 150                             # the amplifiers' band
    out = []
    for i in rows:                                      # the nets, with each one's parts at its left end
        nd, y = spec["nodes"][i], ny[i]
        name, bias, R_, C, lo, hi, start, memory = nd
        out.append(f'<line x1="{LX - 200}" y1="{y}" x2="{xr}" y2="{y}" stroke="{INK}" stroke-width="1.6"/>')
        out.append(text(LX - 200, y - 8, name, 14, INK, weight="bold"))
        cx = LX - 40
        out.append(dot(cx, y) + capacitor(cx, y, MEMORY if memory else INK, "#d8eefa" if memory else "none"))
        out.append(text(cx + 15, y + 24, si(C, "F") + ("  floating gate" if memory else "")))
        if R_ is not None:                              # the leak: a resistor to its rest voltage
            rx = LX - 120
            out.append(dot(rx, y) + resistor(rx, y, rx, y + 38))
            out.append(f'<line x1="{rx - 8}" y1="{y + 42}" x2="{rx + 8}" y2="{y + 42}" stroke="{INK}" stroke-width="2.5"/>'
                       f'<line x1="{rx - 4}" y1="{y + 47}" x2="{rx + 4}" y2="{y + 47}" stroke="{INK}" stroke-width="1.5"/>')
            out.append(text(rx + 9, y + 26, si(R_, "Ω")) + text(rx + 9, y + 49, f"rest {bias * R_:+.2f} V", 9.5, MID))
        elif bias:
            out.append(text(LX - 140, y + 24, f"{si(bias, 'A')} in", 9.5, MID))
        if lo is not None or hi is not None:
            out.append(text(LX - 200, y + 40, f"clamped {lo}..{hi} V (2 diodes)", 9.5, MID))
        if start is not None:
            out.append(text(LX - 200, y + 12, f"born at {start:.2f} V", 9.5, MID))
    for i, label, side in terminals(spec):              # the body
        y = ny[i]
        if side < 0:                                    # a current source into the net
            x = LX - 250
            out.append(f'<line x1="{x}" y1="{y}" x2="{LX - 200}" y2="{y}" stroke="{INK}"/>'
                       f'<circle cx="{x - 14}" cy="{y}" r="12" fill="{BG}" stroke="{INK}"/>'
                       f'<line x1="{x - 21}" y1="{y}" x2="{x - 7}" y2="{y}" stroke="{INK}" marker-end="url(#ink)"/>'
                       + text(x - 32, y + 4, f"{label}: current pulses", 11, INK, "end"))
        else:
            out.append(f'<rect x="{xr + 20}" y="{y - 12}" width="150" height="24" fill="{BG}" stroke="{MID}"/>'
                       f'<line x1="{xr}" y1="{y}" x2="{xr + 20}" y2="{y}" stroke="{INK}"/>'
                       + text(xr + 95, y + 4, f"{label}: its spikes", 11, INK, "middle"))
    for j, e in enumerate(els):                         # the amplifiers, a column each
        to, frm, gate, gain, offset, slope, tau, sigmoid = e
        colour = INHIBIT if gain < 0 else EXCITE
        x = LX + 40 + j * CW
        xin, xa, xt, xout, xg = x, x + 34, x + 92, x + 112, x + 128
        y_in, y_ref = yb - 12, yb + 12
        out.append(dot(xin, ny[frm]) + f'<line x1="{xin}" y1="{ny[frm]}" x2="{xin}" y2="{y_in}" stroke="{INK}"/>')
        if tau > 0:                                     # the input filter: a resistor in series, a capacitor down
            out.append(resistor(xin, y_in, xa, y_in).replace(f'M{xin},{y_in}', f'M{xin},{y_in}'))
            out.append(dot(xa - 8, y_in) + f'<line x1="{xa - 8}" y1="{y_in}" x2="{xa - 8}" y2="{y_in + 4}" stroke="{INK}"/>')
            out.append(text(xin - 4, y_in - 36, f"τ {si(tau, 's')}", 9.5, MID))
            out.append(f'<line x1="{xa - 18}" y1="{yb + 40}" x2="{xa + 2}" y2="{yb + 40}" stroke="{INK}" stroke-width="2.5"/>'
                       f'<line x1="{xa - 18}" y1="{yb + 45}" x2="{xa + 2}" y2="{yb + 45}" stroke="{INK}" stroke-width="2.5"/>'
                       f'<line x1="{xa - 8}" y1="{yb + 45}" x2="{xa - 8}" y2="{yb + 56}" stroke="{INK}"/>'
                       + ground(xa - 8, yb + 56)
                       + f'<line x1="{xa - 8}" y1="{y_in}" x2="{xa - 8}" y2="{yb + 40}" stroke="{INK}" stroke-dasharray="1,0"/>')
        else:
            out.append(f'<line x1="{xin}" y1="{y_in}" x2="{xa}" y2="{y_in}" stroke="{INK}"/>')
        dash = ' stroke-dasharray="5,3"' if gain < 0 else ""
        out.append(f'<path d="M{xa},{yb - 28} L{xt},{yb} L{xa},{yb + 28} Z" fill="#eef6fb" stroke="{colour}" '
                   f'stroke-width="2"{dash}/>' + text(xa + 4, y_in + 4, "+", 12) + text(xa + 4, y_ref + 4, "−", 12))
        out.append(f'<line x1="{xa - 10}" y1="{y_ref}" x2="{xa}" y2="{y_ref}" stroke="{INK}"/>'
                   + text(xa - 4, y_ref + 16, f"{offset:+.2f} V", 9.5, MID, "end"))
        out.append(f'<line x1="{xt}" y1="{yb}" x2="{xout}" y2="{yb}" stroke="{INK}"/>'
                   f'<line x1="{xout}" y1="{yb}" x2="{xout}" y2="{ny[to]}" stroke="{colour}" stroke-width="1.6"{dash}/>'
                   + dot(xout, ny[to]))
        out.append(text(xa, yb + 84, f"{si(gain, 'A')}", 11, colour, weight="bold")
                   + text(xa, yb + 98, f"{'σ' if sigmoid else 'tanh'}, {slope:.3g} per V", 10, colour)
                   + text(xa, yb + 111, f"{names[frm]} → {names[to]}", 10, MID))
        if gate >= 0:                                   # the gate: a transistor in the amplifier's tail
            gx, gy = (xa + xt) / 2 - 8, yb + 22
            out.append(f'<line x1="{gx}" y1="{gy - 6}" x2="{gx}" y2="{yb + 40}" stroke="{INK}"/>'
                       f'<rect x="{gx - 7}" y="{yb + 40}" width="14" height="14" fill="{BG}" stroke="{GATE}" stroke-width="2"/>'
                       f'<line x1="{gx + 7}" y1="{yb + 47}" x2="{xg}" y2="{yb + 47}" stroke="{GATE}" stroke-width="1.6"/>'
                       f'<line x1="{xg}" y1="{yb + 47}" x2="{xg}" y2="{ny[gate]}" stroke="{GATE}" stroke-width="1.6"/>'
                       + dot(xg, ny[gate]) + text(gx + 10, yb + 68, f"× V({names[gate]})", 9.5, GATE))
    p = parts(spec)
    out.append(text(20, y0 + 30, f"The schematic: every part ({p['C']} capacitors, {p['R']} resistors, {p['D']} diodes, "
                    f"{p['T']} transistors: {p['total']} parts)", 18, INK))
    out.append(text(20, y0 + 52, "each net a wire, its capacitor, leak and rest voltage at its left; each amplifier a "
                    "column below, wired up from the net it reads (+) and back to the net it drives; a dot is a joint, "
                    "wires crossing without one don't connect; a gate: a transistor in the amplifier's tail (orange)",
                    11.5, MID))
    return out, xr + 190, yb + 135 - y0


def svg(name: str, spec: dict, note: str = "") -> str:
    sch, sw, sh = schematic(spec, H + 20)
    width, height = max(W, sw), H + 20 + sh
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
           f'font-family="Helvetica, Arial, sans-serif">',
           f'<rect width="{width}" height="{height}" fill="{BG}"/>',
           "<defs>" + "".join(f'<marker id="{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                              f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/>'
                              '</marker>' for k, c in (("in", EXCITE), ("out", INHIBIT), ("ink", INK))) + "</defs>",
           f'<text x="20" y="34" font-size="22" fill="{INK}">{escape(name)}: {parts(spec)["total"]} parts '
           f'({len(spec["nodes"])} nodes, {len(spec["elements"])} elements). The signal-flow graph: who drives whom</text>',
           f'<text x="20" y="58" font-size="13" fill="{MID}">{escape(note)}</text>']
    out += graph(spec, 0)
    out.append(f'<line x1="20" y1="{H + 6}" x2="{width - 20}" y2="{H + 6}" stroke="{MID}" stroke-dasharray="3,4"/>')
    out += sch
    return "\n".join(out + ["</svg>"]) + "\n"


if __name__ == "__main__":
    for path in sys.argv[1:]:
        name = os.path.basename(path)[:-5]
        r = json.load(open(path))
        out = os.path.join(os.path.dirname(__file__), "..", "media", f"{name}.svg")
        from minimal.spec import load
        open(out, "w").write(svg(name, load(path), r.get("note", "")))
        print("wrote", os.path.normpath(out))
