"""Draws a circuit of the minimal search as a diagram, from its spec, so any design can be drawn and redrawn when it
changes: python -m minimal.draw RESULTS.json [...] writes media/NAME.svg.

Nodes are circles (a memory node a square), each with its capacitor, its leak (a resistor to its rest voltage) and
any clamp written beside it, in SI (units.py). Elements are arrows from the node they read to the node they feed, each
labelled with its current (gain), what it reads (tanh or sigmoid, slope and offset) and its filter's time constant; an
arrow into its own node is a loop. A gated element has a dotted line from its gate node to the middle of its arrow.
Colour-blind-safe (Okabe-Ito), and never colour alone (the user is colour-blind): a current in is blue and solid, a
current out vermilion and dashed, a gate orange and dotted, a memory node a sky-blue square. The body's terminals
(eyes, taste, thrusters) are boxes at the edges. Layout: sensors and taste on the left, motors on the right, the rest
between, in the order the spec lists them.
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


def svg(name: str, spec: dict, note: str = "") -> str:
    pos = layout(spec)
    names = [nd[0] for nd in spec["nodes"]]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="Helvetica, Arial, sans-serif">',
           f'<rect width="{W}" height="{H}" fill="{BG}"/>',
           "<defs>" + "".join(f'<marker id="{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                              f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/>'
                              '</marker>' for k, c in (("in", EXCITE), ("out", INHIBIT))) + "</defs>",
           f'<text x="20" y="34" font-size="22" fill="{INK}">{escape(name)}: {parts(spec)["total"]} parts '
           f'({len(spec["nodes"])} nodes, {len(spec["elements"])} elements)</text>',
           f'<text x="20" y="58" font-size="13" fill="{MID}">{escape(note)}</text>']
    pairs = {}
    for e in spec["elements"]:
        pairs[(e[1], e[0])] = pairs.get((e[1], e[0]), 0) + 1
    seen = {}
    for e in spec["elements"]:
        to, frm, gate = e[0], e[1], e[2]
        kind, colour = ("out", INHIBIT) if e[3] < 0 else ("in", EXCITE)
        style = f'stroke="{colour}" stroke-width="1.8"' + (' stroke-dasharray="7,5"' if e[3] < 0 else "")
        k = seen[(frm, to)] = seen.get((frm, to), 0) + 1
        (x0, y0), (x1, y1) = pos[frm], pos[to]
        anchor = "start"
        if frm == to:                                   # loops on the node's outer side, one above another
            s = 1 if frm in (*spec["sensors"], spec["taste"]) else -1   # (away from its terminal: left of a motor)
            cy = y0 - 18 + 36 * (k - 1)
            out.append(f'<path d="M{x0 + s * 20},{cy - 8} C{x0 + s * 75},{cy - 30} {x0 + s * 75},{cy + 14} '
                       f'{x0 + s * 22},{cy + 6}" fill="none" {style} marker-end="url(#{kind})"/>')
            mx, my = x0 + s * 62, cy - 8
            lx, ly, anchor = x0 + s * 80, cy - 2, "start" if s > 0 else "end"
        else:
            dx, dy = x1 - x0, y1 - y0
            d = math.hypot(dx, dy)
            ux, uy = dx / d, dy / d
            bend = (k - (pairs[(frm, to)] + 1) / 2) * 60 + (30 if (to, frm) in pairs else 0)
            sx, sy, ex, ey = x0 + ux * R, y0 + uy * R, x1 - ux * (R + 4), y1 - uy * (R + 4)
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
        out.append(f'<text x="{lx:.0f}" y="{ly:.0f}" font-size="10.5" text-anchor="{anchor}" fill="{colour}" '
                   f'stroke="{BG}" stroke-width="3" paint-order="stroke">{escape(label)}</text>')
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
    terminals = [(spec["sensors"][0], "eye (a colour)", -1), (spec["sensors"][1], "eye (the other)", -1),
                 (spec["taste"], "taste (±1)", -1)] + [(m, f"thruster {k}", 1) for k, m in enumerate(spec["motors"])]
    for i, text, side in terminals:
        x, y = pos[i]
        bx = 20 if side < 0 else W - 140
        out.append(f'<rect x="{bx}" y="{y - 12}" width="120" height="24" fill="{BG}" stroke="{MID}"/>'
                   f'<text x="{bx + 60}" y="{y + 4}" font-size="12" text-anchor="middle" fill="{INK}">{escape(text)}</text>'
                   f'<line x1="{bx + 120 if side < 0 else bx}" y1="{y}" x2="{x - side * R}" y2="{y}" stroke="{MID}"/>')
    out.append(f'<text x="20" y="{H - 16}" font-size="12" fill="{MID}">circle: a node (a capacitor); square: a memory '
               'node (a floating gate); blue solid arrow: a current in; vermilion dashed: a current out; orange dotted: '
               'a gate, multiplying the current by its node\'s voltage (0..1 V); values in SI (units.py)</text>')
    return "\n".join(out + ["</svg>"]) + "\n"


if __name__ == "__main__":
    for path in sys.argv[1:]:
        name = os.path.basename(path)[:-5]
        r = json.load(open(path))
        out = os.path.join(os.path.dirname(__file__), "..", "media", f"{name}.svg")
        open(out, "w").write(svg(name, r["spec"], r.get("note", "")))
        print("wrote", os.path.normpath(out))
