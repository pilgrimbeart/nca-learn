"""Draws a circuit as transistors (the user's request, 2026-10-25), from the very netlist minimal/spice.py writes for
SPICE: a top sheet (each node's capacitor, leak and bias, the inputs' clamps, the supplies and cascode biases)
and a sheet per element, every transistor, resistor, capacitor and source in conventional symbols, nothing drawn as an
amplifier or a box.

Within a sheet every connection is a wire (a dot joins wires; wires crossing without one don't connect). Between
blocks, and between sheets, a net is joined by its label: a pointed label (blue) is a node of the top sheet, a plain
one a net of this sheet alone. A transistor's body is tied to its rail (nMOS to vss, pMOS to vdd), as is
usual. Dashed boxes only group a block's parts and name them by the netlist's prefix.

Each sheet is checked against the netlist before it is written: the drawing's connections (wires, joints, labels,
rails) must be exactly the netlist's, every device drawn once, no wire left dangling, or nothing is written.

    python -m minimal.sheets SPEC.json [--trims TRIMS.json] [--out DIR]    DIR/top.svg, DIR/e0.svg, ...
"""

from __future__ import annotations

import json
import os
import re
import sys
from html import escape

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from minimal import spice  # noqa: E402
from units import si  # noqa: E402

INK, BG = "#111", "#fff"
NODE, BOX, BODY = "#0072B2", "#56B4E9", "#D55E00"      # Okabe-Ito: a node's label, a block's box, the body's source
FONT = "font-family=\"Helvetica, Arial, sans-serif\""
LOCAL = {"off": "offset", "half": "half", "bin": "bias in", "pre": "pre", "dv": "divided", "buf": "buffer",
         "x": "filtered", "lv": "shifted", "rest": "rest"}


class Tf:
    """A placement: local (x, y) to the sheet's, shifted and flipped."""

    def __init__(self, ox=0.0, oy=0.0, fx=1, fy=1):
        self.ox, self.oy, self.fx, self.fy = ox, oy, fx, fy

    def __call__(self, x, y):
        return (self.ox + self.fx * x, self.oy + self.fy * y)

    def v(self, dx, dy):
        return (self.fx * dx, self.fy * dy)


def parse(text: str) -> dict:
    """The netlist's devices by sheet: {"top" or element j: {name: (letter, kind, nets, value)}}."""
    out, sheet = {"top": {}}, "top"
    for line in text.splitlines():
        if line.startswith("* element "):
            sheet = int(line.split()[2].rstrip(":"))
            out[sheet] = {}
        elif line.startswith("* node"):
            sheet = "top"
        elif line[:1] in "XRCDVIB" and len(line.split()) >= 3:
            w = line.split()
            if w[0][0] == "B":                          # a memory's tunnelling (spice.write)
                out[sheet][w[0]] = ("B", "B", w[1:3], None)
            elif w[0][0] == "X":
                out[sheet][w[0]] = ("X", "n" if w[5] == spice.NFET else "p", w[1:4], None)
            elif w[0][0] == "D":
                out[sheet][w[0]] = ("D", "D", w[1:3], None)
            else:
                out[sheet][w[0]] = (w[0][0], w[0][0], w[1:3], float(w[3]))
    return out


class Draw:
    """A sheet being drawn: devices by their terminals' points, wires, labels and rails; checked against its netlist."""

    def __init__(self, devs: dict, names: list):
        self.devs, self.names = devs, names
        self.placed, self.extra = {}, {}            # name: {terminal: point}; extra: drawn, not in the netlist
        self.wires, self.flags, self.rails, self.texts, self.boxes = [], [], [], [], []

    # placing

    def mos(self, name, d, g, s):
        self.placed[name] = {"d": P(d), "g": P(g), "s": P(s)}

    def two(self, name, a, b):
        """R, C (a, b), V (+, -), I (from, to: the current flows through it into to), D (anode, cathode)."""
        self.placed[name] = {"a": P(a), "b": P(b)}

    def wire(self, *pts):
        for p, q in zip(pts, pts[1:]):
            self.wires.append((P(p), P(q)))

    def net_of(self, name, term):
        letter, kind, nets, _ = self.devs[name]
        return nets[{"d": 0, "g": 1, "s": 2, "a": 0, "b": 1}[term]]

    def flag(self, pt, net, d):
        self.flags.append((P(pt), net, d))

    def flag_at(self, name, term, d, length=20):
        """A label on a device's terminal, with its netlist net."""
        p = self.placed[name][term]
        q = (p[0] + d[0] * length, p[1] + d[1] * length)
        self.wire(p, q)
        self.flag(q, self.net_of(name, term), d)

    def rail(self, pt, net, d=(0, -1)):
        self.rails.append((P(pt), net, d))

    def text(self, pt, s, size=10, anchor="start", colour=INK, weight="normal"):
        self.texts.append((P(pt), s, size, anchor, colour, weight))

    # layout

    def bbox(self):
        xs, ys = [], []
        for k, t in list(self.placed.items()) + list(self.extra.items()):
            for x, y in t.values():
                xs += [x - 26, x + 26]
                ys += [y, y]
            if "a" in t:                                # a two-terminal part's value, beside or above it
                (ax, ay), (bx, by) = t["a"], t["b"]
                if ax == bx:
                    xs.append(ax + 80 + 40 * (k in self.extra))
                else:
                    ys.append(min(ay, by) - 26)
        for p, q in self.wires:
            xs += [p[0], q[0]]
            ys += [p[1], q[1]]
        for (x, y), net, d in self.flags:
            w = 12 + 7 * len(self.label(net))
            xs += [x + d[0] * (w + 8), x - 8, x + 8]
            ys += [y + d[1] * 24 - 9, y + 9]
        for (x, y), net, d in self.rails:
            xs += [x - 14, x + 14]
            ys += [y + d[1] * 24 - 6, y + 6]
        for (x, y), s, size, anchor, *_ in self.texts:
            w = 0.55 * size * len(s)
            x0 = x - (w if anchor == "end" else w / 2 if anchor == "middle" else 0)
            xs += [x0, x0 + w]
            ys += [y - size, y + 3]
        return min(xs), min(ys), max(xs), max(ys)

    def absorb(self, other: "Draw", dx, dy, caption=None):
        f = lambda p: P((p[0] + dx, p[1] + dy))
        for k, t in other.placed.items():
            self.placed[k] = {n: f(p) for n, p in t.items()}
        self.extra.update({k: {n: f(p) for n, p in t.items()} for k, t in other.extra.items()})
        self.wires += [(f(p), f(q)) for p, q in other.wires]
        self.flags += [(f(p), n, d) for p, n, d in other.flags]
        self.rails += [(f(p), n, d) for p, n, d in other.rails]
        self.texts += [(f(p), *rest) for p, *rest in other.texts]
        if caption is not None:
            x0, y0, x1, y1 = other.bbox()
            self.boxes.append((x0 + dx - 10, y0 + dy - 10, x1 + dx + 10, y1 + dy + 10, caption))

    # checking

    def check(self):
        """The drawing's connections against the netlist's; raises if they differ."""
        alias = {n: n for d in self.devs.values() for n in d[2]}

        def root(n):
            while alias.setdefault(n, n) != n:
                n = alias[n]
            return n
        wires = {k for k, d in self.devs.items() if d[0] == "V" and d[3] == 0}    # a 0 V source is a wire
        alias[root("agnd")] = root("0")                 # (analogue ground is ground, through VAGND)
        for k in wires:
            a, b = self.devs[k][2]
            alias[root(a)] = root(b)
        want = set(self.devs) - wires
        if set(self.placed) != want:
            raise ValueError(f"drawn but not in the netlist: {sorted(set(self.placed) - want)}; in the netlist but "
                             f"not drawn: {sorted(want - set(self.placed))}")
        pts = {}
        for p, q in self.wires:
            pts.setdefault(p, []), pts.setdefault(q, [])
        for t in list(self.placed.values()) + list(self.extra.values()):
            for p in t.values():
                pts.setdefault(p, [])
        for p, n, _ in self.flags + self.rails:
            pts.setdefault(p, [])
        up = {p: p for p in pts}

        def find(p):
            while up[p] != p:
                up[p] = up[up[p]]
                p = up[p]
            return p

        def join(a, b):
            up[find(a)] = find(b)
        for p, q in self.wires:
            join(p, q)
            for r in pts:
                if on(r, p, q):
                    join(r, p)
        named = {}
        for p, n, _ in self.flags + self.rails:
            n = root(n)
            if n in named:
                join(p, named[n])
            named[n] = p
        groups = {}
        for k, t in self.placed.items():
            for term, p in t.items():
                groups.setdefault(find(p), set()).add(root(self.net_of(k, term)))
        for p, n, _ in self.flags + self.rails:
            groups.setdefault(find(p), set()).add(root(n))
        seen = {}
        for g, nets in groups.items():
            if len(nets) != 1:
                raise ValueError(f"one drawn net joins netlist nets {sorted(nets)}")
            n = nets.pop()
            if n in seen:
                raise ValueError(f"netlist net {n} drawn as two unconnected pieces")
            seen[n] = g
        for p in pts:                               # every wire's end meets something
            if any(p in w for w in self.wires) and self.degree(p) < 2:
                raise ValueError(f"a wire ends in the air at {p}")

    def degree(self, p):
        n = sum((p == a) + (p == b) + 2 * on(p, a, b, strict=True) for a, b in self.wires)
        n += sum(p == q for t in list(self.placed.values()) + list(self.extra.values()) for q in t.values())
        return n + sum(p == q for q, *_ in self.flags + self.rails)

    def label(self, net):
        if net.startswith("n_"):
            return self.names[["n_" + n.lower() for n in self.names].index(net)]
        m = re.match(r"e\d+_(\w+)$", net) or re.match(r"n_\w+_(rest)$", net)
        return LOCAL.get(m.group(1), net) if m else net

    # drawing

    def svg(self, title, lines, notes) -> str:
        x0, y0, x1, y1 = self.bbox()
        for b in self.boxes:
            x0, y0, x1, y1 = min(x0, b[0]), min(y0, b[1] - 16), max(x1, b[2], b[0] + 6.6 * len(b[4])), max(y1, b[3])
        pad, head = 30, 34 + 16 * len(lines)
        foot = 16 * len(notes) + 20
        W, H = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad + head + foot
        dx, dy = pad - x0, pad + head - y0
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" '
             f'height="{H:.0f}" {FONT}>', f'<rect width="100%" height="100%" fill="{BG}"/>',
             f'<g transform="translate({dx:.0f},{dy:.0f})" stroke-linecap="round" fill="none">']
        for bx0, by0, bx1, by1, cap in self.boxes:
            o.append(f'<rect x="{bx0:.0f}" y="{by0:.0f}" width="{bx1 - bx0:.0f}" height="{by1 - by0:.0f}" rx="6" '
                     f'stroke="{BOX}" stroke-width="1.5" stroke-dasharray="6,4"/>')
            o.append(txt(bx0 + 4, by0 - 5, cap, 11, colour="#005a8c", weight="bold"))
        for p, q in self.wires:
            o.append(line(p, q))
        for k, t in self.placed.items():
            o.append(self.symbol(k, t))
        for k, t in self.extra.items():
            o.append(self.symbol(k, t, extra=True))
        for p, n, d in self.rails:
            o.append(rail(p, n, d))
        for p, n, d in self.flags:
            o.append(flag(p, self.label(n), d, n.startswith("n_") and not n.endswith("_rest")))
        dots = {p for p in {q for w in self.wires for q in w} | {q for t in self.placed.values() for q in t.values()}
                if self.degree(p) >= 3}
        for x, y in sorted(dots):
            o.append(f'<circle cx="{x}" cy="{y}" r="3.2" fill="{INK}" stroke="none"/>')
        for p, s, size, anchor, colour, weight in self.texts:
            o.append(txt(*p, s, size, anchor, colour, weight))
        o.append("</g>")
        o.append(txt(pad, 26, title, 17, weight="bold"))
        for k, s in enumerate(lines):
            o.append(txt(pad, 46 + 16 * k, s, 12))
        for k, s in enumerate(notes):
            o.append(txt(pad, H - foot + 14 + 16 * k, s, 11))
        o.append("</svg>")
        return "\n".join(o)

    def symbol(self, name, t, extra=False) -> str:
        if extra:
            letter, value = "I", None
        else:
            letter, kind, nets, value = self.devs[name]
        if letter == "X":
            return mos(t["d"], t["g"], t["s"], kind)
        a, b = t["a"], t["b"]
        return {"R": resistor, "C": capacitor, "V": vsource, "I": isource, "D": diode, "B": tunnel}[letter](a, b, value,
                                                                                                    extra)


def P(p):
    return (round(float(p[0]), 2), round(float(p[1]), 2))


def on(r, a, b, strict=False):
    """r on the segment a-b (strict: not at its ends)."""
    if strict and r in (a, b):
        return False
    if a[0] == b[0] == r[0]:
        return min(a[1], b[1]) <= r[1] <= max(a[1], b[1])
    if a[1] == b[1] == r[1]:
        return min(a[0], b[0]) <= r[0] <= max(a[0], b[0])
    return False


# symbols

def line(p, q, w=1.5, colour=INK):
    return f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}" stroke="{colour}" stroke-width="{w}"/>'


def poly(pts, w=1.5, colour=INK, fill="none"):
    return (f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" stroke="{colour}" '
            f'stroke-width="{w}" fill="{fill}"/>')


def txt(x, y, s, size=10, anchor="start", colour=INK, weight="normal"):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" text-anchor="{anchor}" fill="{colour}" stroke="none" '
            f'font-weight="{weight}">{escape(s)}</text>')


def mos(d, g, s, kind):
    """A MOSFET, its channel vertical between drain and source, its gate to one side: nMOS an arrow out of the
    source; pMOS an arrow into it and a bubble on the gate."""
    side = 1 if g[0] > d[0] else -1
    ym = (d[1] + s[1]) / 2
    ds = 1 if s[1] > d[1] else -1
    xc, xp = d[0] + side * 16, d[0] + side * 22
    o = [poly([d, (d[0], ym - ds * 12), (xc, ym - ds * 12)]), poly([s, (s[0], ym + ds * 12), (xc, ym + ds * 12)]),
         line((xc, ym - 17), (xc, ym + 17), 2.6), line((xp, ym - 13), (xp, ym + 13), 2)]
    if kind == "p":
        o.append(f'<circle cx="{xp + side * 4.5}" cy="{ym}" r="4" stroke="{INK}" stroke-width="1.4" fill="{BG}"/>')
        o.append(line((xp + side * 9, ym), g))
    else:
        o.append(line((xp, ym), g))
    ya, xm = ym + ds * 12, (d[0] + xc) / 2
    tip, back = (xm - side * 5, xm + side * 3) if kind == "n" else (xm + side * 5, xm - side * 3)
    o.append(poly([(tip, ya), (back, ya - 4), (back, ya + 4), (tip, ya)], 1, fill=INK))
    return "".join(o)


def along(a, b):
    """(unit vector along a-b, its normal, length)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = (dx * dx + dy * dy) ** 0.5
    return (dx / n, dy / n), (-dy / n, dx / n), n


def value_text(a, b, s, colour=INK):
    (ux, uy), _, n = along(a, b)
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    if abs(ux) < 0.5:                               # vertical: to the right
        return txt(mx + 18, my + 4, s, 10, colour=colour)
    return txt(mx, my - 14, s, 10, "middle", colour=colour)


def resistor(a, b, ohms, extra=False):
    (ux, uy), (nx, ny), n = along(a, b)
    m0, m1 = n / 2 - 20, n / 2 + 20
    pts = [a, (a[0] + ux * m0, a[1] + uy * m0)]
    for k in range(1, 8):
        t = m0 + k * 40 / 8
        s = (1 if k % 2 else -1) * 7 if k < 8 else 0
        pts.append((a[0] + ux * t + nx * s, a[1] + uy * t + ny * s))
    pts += [(a[0] + ux * m1, a[1] + uy * m1), b]
    return poly(pts) + value_text(a, b, si(ohms, "Ω"))


def capacitor(a, b, farads, extra=False):
    (ux, uy), (nx, ny), n = along(a, b)
    c = (a[0] + ux * n / 2, a[1] + uy * n / 2)
    p1, p2 = (c[0] - ux * 4, c[1] - uy * 4), (c[0] + ux * 4, c[1] + uy * 4)
    o = [line(a, p1), line(p2, b)]
    for p in (p1, p2):
        o.append(line((p[0] - nx * 12, p[1] - ny * 12), (p[0] + nx * 12, p[1] + ny * 12), 2.4))
    return "".join(o) + value_text(a, b, si(farads, "F"))


def circle_source(a, b):
    (ux, uy), _, n = along(a, b)
    c = (a[0] + ux * n / 2, a[1] + uy * n / 2)
    return c, (ux, uy), [line(a, (c[0] - ux * 14, c[1] - uy * 14)), line((c[0] + ux * 14, c[1] + uy * 14), b),
                         f'<circle cx="{c[0]}" cy="{c[1]}" r="14" stroke="{INK}" stroke-width="1.5" fill="{BG}"/>']


def vsource(a, b, volts, extra=False):
    c, (ux, uy), o = circle_source(a, b)
    o.append(txt(c[0] - ux * 6, c[1] - uy * 6 + 4, "+", 11, "middle"))
    o.append(txt(c[0] + ux * 6, c[1] + uy * 6 + 4, "−", 11, "middle"))
    return "".join(o) + value_text(a, b, f"{volts:+.4g} V")


def isource(a, b, amps, extra=False):
    colour = BODY if extra else INK
    c, (ux, uy), o = circle_source(a, b)
    o.append(f'<line x1="{c[0] - ux * 8}" y1="{c[1] - uy * 8}" x2="{c[0] + ux * 5}" y2="{c[1] + uy * 5}" '
             f'stroke="{colour}" stroke-width="1.6"/>')
    nx, ny = -uy, ux
    tip = (c[0] + ux * 9, c[1] + uy * 9)
    o.append(poly([tip, (tip[0] - ux * 6 + nx * 4, tip[1] - uy * 6 + ny * 4),
                   (tip[0] - ux * 6 - nx * 4, tip[1] - uy * 6 - ny * 4), tip], 1, colour, colour))
    return "".join(o) + value_text(a, b, "the body's pulses" if extra else si(amps, "A"), colour)


def tunnel(a, b, value=None, extra=False):
    """A memory's tunnelling, a current source the write controls: a diamond with an arrow."""
    (ux, uy), _, n = along(a, b)
    c = (a[0] + ux * n / 2, a[1] + uy * n / 2)
    nx, ny = -uy, ux
    pts = [(c[0] - ux * 15, c[1] - uy * 15), (c[0] + nx * 15, c[1] + ny * 15), (c[0] + ux * 15, c[1] + uy * 15),
           (c[0] - nx * 15, c[1] - ny * 15)]
    o = [line(a, pts[0]), line(pts[2], b), poly(pts + [pts[0]], 1.5, INK, BG)]
    o.append(line((c[0] - ux * 8, c[1] - uy * 8), (c[0] + ux * 5, c[1] + uy * 5), 1.6))
    tip = (c[0] + ux * 9, c[1] + uy * 9)
    o.append(poly([tip, (tip[0] - ux * 6 + nx * 4, tip[1] - uy * 6 + ny * 4),
                   (tip[0] - ux * 6 - nx * 4, tip[1] - uy * 6 - ny * 4), tip], 1, INK, INK))
    return "".join(o) + value_text(a, b, "tunnelling")


def diode(a, b, value=None, extra=False):
    (ux, uy), (nx, ny), n = along(a, b)
    c = (a[0] + ux * n / 2, a[1] + uy * n / 2)
    t0, t1 = (c[0] - ux * 8, c[1] - uy * 8), (c[0] + ux * 8, c[1] + uy * 8)
    return (line(a, t0) + line(t1, b) + poly([(t0[0] + nx * 9, t0[1] + ny * 9), (t0[0] - nx * 9, t0[1] - ny * 9),
                                               t1, (t0[0] + nx * 9, t0[1] + ny * 9)], 1.5, fill=INK)
            + line((t1[0] + nx * 9, t1[1] + ny * 9), (t1[0] - nx * 9, t1[1] - ny * 9), 2))


def rail(p, net, d):
    """vdd: a bar, labelled; vss: a bar and an open triangle, labelled; ground (0 V): three bars."""
    x, y = p
    q = (x + d[0] * 12, y + d[1] * 12)
    o = [line(p, q)]
    if net in ("0", "agnd"):
        for k, w in enumerate((10, 6, 2)):
            o.append(line((q[0] - w, q[1] + d[1] * 4 * k), (q[0] + w, q[1] + d[1] * 4 * k), 1.6))
        if net == "agnd":
            o.append(txt(q[0] + 13, q[1] + 3 + d[1] * 3, "agnd", 9))
        return "".join(o)
    o.append(line((q[0] - 10, q[1]), (q[0] + 10, q[1]), 2.2))
    if net == "vss":
        o.append(poly([(q[0] - 6, q[1]), (q[0] + 6, q[1]), (q[0], q[1] + d[1] * 8), (q[0] - 6, q[1])], 1.3))
    o.append(txt(q[0] + 13, q[1] + 3 + d[1] * 3, {"vdd": f"vdd +{spice.HALF:g} V", "vss": f"vss −{spice.HALF:g} V"}.get(net, net), 9))
    return "".join(o)


def flag(p, s, d, node):
    """A net's label, at the end of a wire: a node's pointed and blue, a local net's plain."""
    x, y = p
    w = 10 + 7 * len(s)
    if d[1]:                                        # up or down: the label above or below
        cy = y + d[1] * 13
        if node:
            pts = [(x, y), (x + w / 2, cy - d[1] * 4), (x + w / 2, cy + d[1] * 9), (x - w / 2, cy + d[1] * 9),
                   (x - w / 2, cy - d[1] * 4), (x, y)]
            return poly(pts, 1.4, NODE, "#cfe8f6") + txt(x, cy + d[1] * 2 + 4, s, 11, "middle", weight="bold")
        return txt(x, y + d[1] * 6 + (8 if d[1] > 0 else -2), s, 10, "middle", colour="#333")
    if node:
        pts = [(x, y), (x + d[0] * 8, y - 9), (x + d[0] * (w + 8), y - 9), (x + d[0] * (w + 8), y + 9),
               (x + d[0] * 8, y + 9), (x, y)]
        return poly(pts, 1.4, NODE, "#cfe8f6") + txt(x + d[0] * (w / 2 + 8), y + 4, s, 11, "middle", weight="bold")
    return txt(x + d[0] * 4, y + 4, s, 10, "start" if d[0] > 0 else "end", colour="#333")


# blocks, as spice.Net builds them

def mirror(dr: Draw, k, t: Tf, w=100):
    """A wide-swing cascode mirror k (spice.Net.mirror_n / mirror_p), drawn in local units as a pMOS one: the rail at
    y 0, the input at (0, 120), the output at (w, 120); t places it (flipped, for an nMOS one)."""
    dr.mos(f"X{k}_m1", t(0, 60), t(40, 30), t(0, 0))
    dr.mos(f"X{k}_c1", t(0, 120), t(-40, 90), t(0, 60))
    dr.mos(f"X{k}_m2", t(w, 60), t(w - 40, 30), t(w, 0))
    dr.mos(f"X{k}_c2", t(w, 120), t(w + 40, 90), t(w, 60))
    dr.wire(t(0, 0), t(w, 0))
    dr.rail(t(w / 2, 0), dr.net_of(f"X{k}_m1", "s"), t.v(0, -1))
    dr.wire(t(40, 30), t(w - 40, 30))
    dr.wire(t(50, 30), t(50, 120), t(0, 120))
    dr.flag_at(f"X{k}_c1", "g", t.v(-1, 0))
    dr.flag_at(f"X{k}_c2", "g", t.v(1, 0))
    return t(0, 120), t(w, 120)


def pair(dr: Draw, k, w, degen):
    """A differential pair k (plus at x 0, minus at x w, drains at y 0), its sources joined at y 120."""
    dr.mos(f"X{k}_p", (0, 0), (-40, 30), (0, 60))
    dr.mos(f"X{k}_m", (w, 0), (w + 40, 30), (w, 60))
    if degen:
        dr.two(f"R{k}_sp", (0, 60), (0, 120))
        dr.two(f"R{k}_sm", (w, 60), (w, 120))
    else:
        dr.wire((0, 60), (0, 120))
        dr.wire((w, 60), (w, 120))
    dr.wire((0, 120), (w, 120))


def tail(dr: Draw, k, cx, jy, gated):
    """The tail k (spice.Net.tail: a bias current, mirrored; or, gated, the gate's current mirrored) under a pair whose
    sources join at (cx, jy)."""
    dr.wire((cx, jy), (cx, jy + 160))
    inp, _ = mirror(dr, f"{k}_t", Tf(cx - 100, jy + 280, 1, -1))
    if gated:
        dr.flag_at(f"X{k}_t_c1", "d", (0, -1), 30)
    else:
        dr.two(f"I{k}_ib", (cx - 100, jy + 50), inp)
        dr.rail((cx - 100, jy + 50), "vdd")


def wide(dr: Draw, k, tk, gated=False, degen=False):
    """Mead's wide-range transconductance amplifier k (spice.Net.wide) with its tail tk: the pair, two pMOS mirrors
    above it, an nMOS mirror between them turning the minus side's current round."""
    pair(dr, k, 400, degen)
    mirror(dr, f"{k}a", Tf(0, -180))
    mirror(dr, f"{k}b", Tf(400, -180, -1, 1))
    mirror(dr, f"{k}c", Tf(300, 80, -1, -1), 200)
    dr.wire((0, -60), (0, 0))
    dr.wire((400, -60), (400, 0))
    dr.wire((100, -60), (100, -40))
    dr.wire((300, -60), (300, -40))
    dr.wire((100, -50), (130, -50))
    dr.flag((130, -50), dr.net_of(f"X{k}a_c2", "d"), (1, 0))
    dr.flag_at(f"X{k}_p", "g", (-1, 0))
    dr.flag_at(f"X{k}_m", "g", (1, 0))
    tail(dr, tk, 200, 120, gated)


def branch(dr: Draw, k, ko, kq, tk, gated=False, degen=False, half=None):
    """One branch of a pair k (its other drain wired to vdd), mirrored by ko into the output, or by ko then kq to sink
    from it; its tail tk; half: a reference source wired to the minus input (the gate's)."""
    w = 360
    pair(dr, k, w, degen)
    dr.wire((w, 0), (w, -40))
    dr.rail((w, -40), "vdd")
    mirror(dr, ko, Tf(0, -180))
    dr.wire((0, -60), (0, 0))
    if kq is None:
        dr.wire((100, -60), (100, -30))
        dr.flag((100, -30), dr.net_of(f"X{ko}_c2", "d"), (0, 1))
    else:
        mirror(dr, kq, Tf(100, 80, 1, -1))
        dr.wire((100, -60), (100, -40))
        dr.wire((200, -40), (200, -55), (250, -55))
        dr.flag((250, -55), dr.net_of(f"X{kq}_c2", "d"), (1, 0))
    dr.flag_at(f"X{k}_p", "g", (-1, 0))
    if half:
        dr.wire((w + 40, 30), (w + 90, 30))
        dr.two(half, (w + 90, 30), (w + 90, 120))
        dr.rail((w + 90, 120), "0", (0, 1))
    else:
        dr.flag_at(f"X{k}_m", "g", (1, 0))
    tail(dr, tk, w / 2, 120, gated)


def divider(dr: Draw, k):
    dr.two(f"R{k}_d1", (0, 0), (0, 100))
    dr.two(f"C{k}_d1", (90, 0), (90, 100))
    dr.two(f"R{k}_d2", (0, 100), (0, 200))
    dr.two(f"C{k}_d2", (90, 100), (90, 200))
    dr.wire((0, 0), (90, 0))
    dr.wire((0, 100), (90, 100))
    dr.wire((0, 200), (90, 200))
    dr.wire((45, 200), (45, 230))
    dr.two(f"V{k}_dref", (45, 230), (45, 330))                   # towards the middle of the pair's range
    dr.rail((45, 330), "0", (0, 1))
    dr.flag_at(f"R{k}_d1", "a", (0, -1))
    dr.wire((90, 100), (130, 100))
    dr.flag((130, 100), dr.net_of(f"R{k}_d1", "b"), (1, 0))


def filt(dr: Draw, k):
    dr.two(f"R{k}_f", (0, 0), (120, 0))
    dr.two(f"C{k}_f", (120, 0), (120, 90))
    dr.rail((120, 90), "0", (0, 1))
    dr.flag((0, 0), dr.net_of(f"R{k}_f", "a"), (-1, 0))
    dr.wire((120, 0), (160, 0))
    dr.flag((160, 0), dr.net_of(f"R{k}_f", "b"), (1, 0))


def shifter(dr: Draw, k, up):
    """A source follower k (spice.Net.shifter); drawn for one shifting down (nMOS), flipped for up (pMOS)."""
    t = Tf(0, 0, 1, -1 if up else 1)
    w = 160
    mirror(dr, f"{k}_l", Tf(0, t(0, 120)[1], 1, -t.fy), w)
    dr.two(f"I{k}_ib", t(0, -110), t(0, 0)) if not up else dr.two(f"I{k}_ib", t(0, 0), t(0, -110))
    dr.rail(t(0, -110), "vss" if up else "vdd", t.v(0, -1))
    dr.mos(f"X{k}_f", t(w, -90), t(w - 40, -60), t(w, -30))
    dr.rail(t(w, -90), "vss" if up else "vdd", t.v(0, -1))
    dr.wire(t(w, -30), t(w, 0))
    dr.wire(t(w, -15), t(w + 40, -15))
    dr.flag(t(w + 40, -15), dr.net_of(f"X{k}_f", "s"), (1, 0))
    dr.flag_at(f"X{k}_f", "g", (-1, 0))


def write(dr: Draw, k):
    """A memory written by tunnelling (spice.write): the write's output held at analogue ground, its current, less the
    driver's threshold, tunnelling into the cell."""
    dr.two(f"B{k}_w", (0, 100), (0, 0))
    dr.rail((0, 100), "0", (0, 1))
    dr.flag_at(f"B{k}_w", "b", (0, -1))
    dr.text((30, 40), f"{k}_w: the write's output, held at agnd", 10)
    dr.text((30, 54), "(its current measured by a 0 V source)", 10)


def bias(dr: Draw, n, positive):
    """A node's bias (spice.node): a reference current mirrored from vdd into the node, or from it to vss."""
    t = Tf(0, 0, 1, 1 if positive else -1)
    i_pt, o_pt = mirror(dr, f"{n}_b", t, 100)
    end = t(0, 230)
    if positive:
        dr.two(f"I{n}_bias", i_pt, end)
        dr.rail(end, "vss", t.v(0, 1))
    else:
        dr.two(f"I{n}_bias", end, i_pt)
        dr.rail(end, "vdd", t.v(0, 1))
    dr.wire(o_pt, t(100, 190))
    dr.flag(t(100, 190), n, t.v(0, 1))


def offset(dr: Draw, k, rl):
    """The offset's bias source; rl: a preamplifier's load resistor from its output to the offset."""
    dr.two(f"V{k}_off", (0, 0), (0, 100))
    dr.rail((0, 100), "0", (0, 1))
    dr.wire((0, 0), (-30, 0))
    dr.flag((-30, 0), dr.net_of(f"V{k}_off", "a"), (-1, 0))
    if rl:
        dr.two(f"R{k}_pl", (90, -100), (90, 0))
        dr.wire((0, 0), (90, 0))
        dr.flag_at(f"R{k}_pl", "a", (0, -1))


# sheets

def element_sheet(devs, names, c, j, text_head) -> tuple:
    gain, off, slope, tau, sig = c.el_arr[:, j]
    to, frm, gate = (int(v) for v in c.link[:, j])
    k = f"e{j}"
    has = lambda n: n in devs
    gated = gate >= 0
    blocks = []

    def block(fn, caption, *a, **kw):
        d = Draw(devs, names)
        fn(d, *a, **kw)
        blocks.append((d, caption))

    if has(f"R{k}_d1"):
        share = devs[f"R{k}_d2"][3] / spice.DIVIDER
        block(divider, f"divider ×{share:.3g} ({k}_d): {names[frm]} into the pair's range", k)
    if has(f"R{k}_f"):
        block(wide, f"follower ({k}f): the filter mustn't load its input", f"{k}f", f"{k}f")
        block(filt, f"filter ({k}_f): τ {si(tau, 's')}", k)
    if has(f"X{k}s_f"):
        up = devs[f"X{k}s_f"][1] == "p"
        block(shifter, f"level shifter ({k}s): {'up' if up else 'down'}", f"{k}s", up)
    pre = has(f"R{k}_pl")
    if pre:
        block(wide, f"preamplifier ({k}p): degenerated, into its load", f"{k}p", f"{k}p", degen=True)
    block(offset, f"offset ({k}_off)" + (" and load" if pre else ""), k, pre)
    if gated:
        block(branch, f"gate ({k}g): a tail of 0 to its full current as {names[gate]} goes 0 to {spice.V_TYP:g} V",
              f"{k}g", f"{k}gm", None, f"{k}g", degen=True, half=f"V{k}_half")
    degen = has(f"R{k}m_sp")
    if sig < 0.5:
        block(wide, f"output ({k}m): tanh, into {names[to]}", f"{k}m", k, gated, degen)
    else:
        block(branch, f"output ({k}m): sigmoid, {'sourced into' if gain > 0 else 'sunk from'} {names[to]}",
              f"{k}m", f"{k}o", None if gain > 0 else f"{k}q", k, gated, degen)
    if has(f"B{k}_w"):
        block(write, f"write ({k}_w): by tunnelling into {names[to]}, a SONOS cell", k)
    return blocks


def place(sheet: Draw, blocks, x=0.0, y=0.0, gap=70):
    """Blocks in a row, their tops aligned."""
    for d, cap in blocks:
        bx0, by0, bx1, by1 = d.bbox()
        sheet.absorb(d, x - bx0, y - by0, cap)
        x += max(bx1 - bx0, 6.2 * len(cap) - 12) + gap     # (room for its caption)


def top_sheet(devs, names, c, spec, uses) -> Draw:
    dr = Draw(devs, names)
    nets = ["n_" + n.lower() for n in names]
    inputs = set(spec["sensors"]) | {spec["taste"]}
    x = row = 0
    for i, n in enumerate(nets):
        d = Draw(devs, names)
        d.wire((-40, 0), (0, 0))
        d.flag((-40, 0), n, (-1, 0))
        cols = [f"C{n}"] + ([f"R{n}_leak"] if f"R{n}_leak" in devs else []) + \
               ([f"D{n}_lo", "body"] if i in inputs else [])
        xs = [70 * k for k in range(len(cols))]
        for cx, col in zip(xs, cols):
            if col.startswith("C"):
                d.two(col, (cx, 0), (cx, 90))
                d.rail((cx, 90), "0", (0, 1))
            elif col.startswith("R"):
                d.two(col, (cx, 0), (cx, 90))
                d.rail((cx, 90), "agnd", (0, 1))
            elif col.startswith("D"):
                d.two(col, (cx, 90), (cx, 0))
                d.wire((cx, 90), (cx, 110))
                d.flag((cx, 110), "vcll", (0, 1))
            else:
                d.extra[f"body_{n}"] = {"a": P((cx, 90)), "b": P((cx, 0))}
                d.rail((cx, 90), "0", (0, 1))
        if i in inputs:
            d.two(f"D{n}_hi", (35, 0), (35, -70))
            d.wire((35, -70), (35, -90))
            d.flag((35, -90), "vclh", (0, -1))
        d.wire((0, 0), (xs[-1], 0))
        memory = c.node_arr[5, i] > 0
        cap = f"node {names[i]}" + (": memory, no leak (a floating gate)" if memory else "")
        y = d.bbox()[3] + 22
        for s in uses[i]:
            d.text((-60, y), s, 10)
            y += 14
        if i == 4:                                  # the rest in a second row
            x, row = 0, dr.bbox()[3] + 60
        place(dr, [(d, cap)], x, row)
        x = dr.boxes[-1][2] + 70
        if f"I{n}_bias" in devs:                    # its bias, mirrored from a rail
            b = Draw(devs, names)
            bias(b, n, c.node_arr[0, i] > 0)
            place(dr, [(b, f"bias of {names[i]}")], x, row)
            x = dr.boxes[-1][2] + 70
    d = Draw(devs, names)
    for k, (v, net) in enumerate((("VDD", "vdd"), ("VSS", "vss"), ("VCN", "vcn"), ("VCP", "vcp"), ("VCLH", "vclh"),
                                  ("VCLL", "vcll"))):
        d.two(v, (110 * k, 0), (110 * k, 100))
        d.rail((110 * k, 100), "0", (0, 1))
        if net in ("vdd", "vss"):
            d.rail((110 * k, 0), net)
        else:
            d.wire((110 * k, 0), (110 * k, -30))
            d.flag((110 * k, -30), net, (0, -1))
    d.text((0, 140), "agnd: analogue ground, one buffer for the chip (in SPICE, ground through a 0 V source", 10)
    d.text((0, 154), "that measures its current)", 10)
    place(dr, [(d, "supplies, cascode biases, clamp references")], x, row)
    return dr


def draw(spec: dict, trims: list, out: str, name: str) -> list:
    c, names = spice.build(spec)
    text, count = spice.netlist(spec, None, trims, title=name)
    sheets = parse(text)
    uses = [[] for _ in c.names]
    for j in range(c.el_arr.shape[1]):
        to, frm, gate = (int(v) for v in c.link[:, j])
        uses[frm].append(f"read by e{j}")
        uses[to].append(f"driven by e{j}")
        if gate >= 0:
            uses[gate].append(f"gates e{j}")
    os.makedirs(out, exist_ok=True)
    notes = [f"Transistors: SKY130 core (nfet_01v8, pfet_01v8), W/L {spice.W}/{spice.L} µm; nMOS bodies to vss "
             f"(−{spice.HALF:g} V), pMOS bodies to vdd (+{spice.HALF:g} V). A memory is a SONOS cell, written by tunnelling.",
             "A dot joins wires; wires crossing without one don't connect. A pointed blue label is a node of the top "
             "sheet; a plain label joins within this sheet.",
             "Drawn from the netlist minimal/spice.py writes for SPICE, and checked against it: every connection here "
             "is the netlist's, and only those."]
    files = []
    top = top_sheet(sheets["top"], c.names, c, spec, uses)
    top.check()
    nn = {k: sum(1 for d in sheets["top"].values() if d[0] == k) for k in "RCDVI"}
    files.append(("top", top.svg(f"{name}: top sheet, the nodes",
                                 [f"{len(names)} nodes: each a capacitor to ground, a leak (a resistor to analogue ground), "
                                  f"its bias (a current from a rail), the inputs' clamp diodes; the supplies and cascode"
                                  f" biases.",
                                  f"This sheet: {nn['C']} capacitors, {nn['R']} resistors, {nn['D']} diodes, "
                                  f"{nn['V'] + nn['I']} sources. Whole circuit: {count['T']} transistors, "
                                  f"{count['R']} resistors, {count['C']} capacitors, {count['D']} diodes, "
                                  f"{count['sources']} sources."],
                                 notes[1:] + ["The body's pulses (vermilion) enter at the sensors and taste; they are "
                                              "the body, not the circuit."])))
    for j in range(c.el_arr.shape[1]):
        devs = sheets[j]
        blocks = element_sheet(devs, c.names, c, j, None)
        dr = Draw(devs, c.names)
        place(dr, blocks)
        dr.check()
        gain, off, slope, tau, sig = c.el_arr[:, j]
        to, frm, gate = (int(v) for v in c.link[:, j])
        f = "σ" if sig > 0.5 else "tanh"
        head = (f"{c.names[to]} ← {si(gain, 'A')} × {f}({slope:.3g} ({c.names[frm]} {'−' if off >= 0 else '+'} "
                f"{abs(off):.3g} V))" + (f", gated by {c.names[gate]}" if gate >= 0 else "")
                + (f", its input filtered over {si(tau, 's')}" if tau > 0 else ""))
        cnt = {k: sum(1 for d in devs.values() if d[0] == k) for k in "XRCVI"}
        wires = sum(1 for d in devs.values() if d[0] == "V" and d[3] == 0)
        files.append((f"e{j}", dr.svg(f"{name}: element {j}", [head, f"{cnt['X']} transistors, {cnt['R']} resistors, "
                                      f"{cnt['C']} capacitors, {cnt['V'] - wires + cnt['I']} bias sources"], notes)))
    for n, s in files:
        open(os.path.join(out, f"{n}.svg"), "w").write(s)
    return [n for n, _ in files]


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--trims")
    ap.add_argument("--out")
    a = ap.parse_args()
    from minimal.spec import load
    spec = load(a.spec)
    name = os.path.basename(a.spec)[:-5]
    trims = json.load(open(a.trims)) if a.trims else spice.trim(spec)
    out = a.out or os.path.join(os.path.dirname(__file__), "..", "media", f"{name}_transistors")
    print(", ".join(draw(spec, trims, out, name)), "written to", out)
