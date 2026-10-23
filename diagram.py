"""Draws what runs inside one cell, as a block diagram: python diagram.py writes media/cell.svg (shown in the README).

The rule's numbers, layers and stages, with what each reads from its neighbours' means and the body on the left, and
what it shows its neighbours and gives the body on the right. Colour-blind-safe colours (Okabe-Ito), each kind also
told apart by line weight or dash, never by colour alone: a shared number blue and thin, the body vermilion and thick,
a value kept inside the cell bluish green and dashed. The text is written by hand from rules/*.py, so redraw it when a
rule changes.
"""

from html import escape
import pathlib

OUT = pathlib.Path(__file__).parent / "media" / "cell.svg"
W = 1500
LX, LW = 16, 220                 # the left column: from neighbours and the body
RX, RW = 1264, 220               # the right column: shown to neighbours, and given to the body
CX0, CX1 = 290, 1210             # the cell
KX0, KX1 = 306, 1194             # the rule's layers
SX0, SX1 = 322, 1178             # their stages
LINK = 40                        # where the arrows between stages run, from SX0
STYLE = """
.bg { fill: #ffffff; }
.cell { fill: #ffffff; stroke: #1b1c1d; stroke-width: 2.2; }
.con { fill: #e8f3fa; stroke: #56b4e9; stroke-width: 1; }
.sub, .nbox { fill: #ffffff; stroke: #1b1c1d; stroke-width: 1; }
.bodybox { fill: #2a2c2e; stroke: #2a2c2e; }
.a-sig { stroke: #0072b2; stroke-width: 1.4; }
.a-body { stroke: #d55e00; stroke-width: 3; }
.a-int { stroke: #009e73; stroke-width: 1.4; stroke-dasharray: 4 3; }
.ahf { fill: #0072b2; }
.ahb { fill: #d55e00; }
.ahm { fill: #009e73; }
text { fill: #1b1c1d; font-family: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif; }
.colh { font-size: 13px; font-weight: 600; letter-spacing: 0.1em; }
.colhs, .hd, .io, .lab, .nts { fill: #5e6163; }
.colhs { font-size: 12px; }
.hd { font-size: 12.5px; }
.ct { font-size: 14.5px; font-weight: 600; }
.bt { font-size: 13px; font-weight: 600; }
.lab { font-size: 11px; font-style: italic; }
.nts, .bodyts { font-size: 11.5px; }
.io, .eq, .eqs, .nt, .bodyt { font-family: "IBM Plex Mono", Menlo, Consolas, "DejaVu Sans Mono", monospace; }
.io, .eq { font-size: 11.5px; }
.eqs { font-size: 11px; }
.nt, .bodyt { font-size: 12.5px; font-weight: 500; }
.bodyt, .bodyts { fill: #f6f6f5; }
"""
svg = []


def rect(x, y, w, h, cls, rx=4):
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" class="{cls}"/>')


def text(x, y, s, cls, anchor="start"):
    svg.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{escape(s)}</text>')


def arrow(x1, y1, x2, y2, kind="sig"):
    """kind: sig (a shared number), body (to or from the body), int (kept inside the cell, between stages)."""
    marker = {"sig": "ah", "body": "ahb", "int": "ahm"}[kind]
    svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="a-{kind}" marker-end="url(#{marker})"/>')


def link(y0, y1, label):
    """A value passed down from one stage to the next, inside the cell."""
    arrow(SX0 + LINK, y0 + 1, SX0 + LINK, y1 - 1, "int")
    text(SX0 + LINK + 12, y0 + 12, label, "lab")


def stage(x, y, w, h, title, io, lines, small=False):
    rect(x, y, w, h, "sub")
    text(x + 12, y + 19, title, "bt")
    if io:
        text(x + w - 12, y + 19, io, "io", "end")
    for i, s in enumerate(lines):
        assert len(s) <= (29 if small else 120), s                  # it must fit its box
        text(x + 12, y + 38 + 15 * i, s, "eqs" if small else "eq")


def layer(y, h, title, sub):
    rect(KX0, y, KX1 - KX0, h, "con", 6)
    text(KX0 + 14, y + 21, title, "ct")
    text(KX1 - 14, y + 21, sub, "io", "end")


def side(x, y, h, title, sub=None, body=False):
    """A box in the left or right column: a shared number (outlined) or the body (filled)."""
    rect(x, y, LW, h, "bodybox" if body else "nbox")
    cls = "bodyt" if body else "nt"
    text(x + 12, y + (18 if sub else h / 2 + 4.5), title, cls)
    if sub:
        text(x + 12, y + 34, sub, cls + "s")


# column heads
text(LX, 26, "FROM NEIGHBOURS", "colh")
text(LX, 44, "mean over neighbours of what", "colhs")
text(LX, 58, "each shows: clip(v, −1, 1) + N(0, 0.01)", "colhs")
text(CX0, 26, "ONE CELL", "colh")
text(CX0, 44, "brain.update(me, mean, count, inp, out): 85 numbers kept, 28 of them shown", "colhs")
text(RX, 26, "OUT", "colh")
text(RX, 44, "what the cell shows its", "colhs")
text(RX, 58, "neighbours, and gives the body", "colhs")
text(KX0, 96, "Updates at random (in the creature, with chance 0.9 a step, 400 steps a second: never in lockstep); then every kept number gets "
     "noise N(0, 0.001),", "hd")
text(KX0, 113, "and whole numbers are re-rounded at its next update. Order inside:  organs  →  choose and learn  →  "
     "channel 1  →  channel 2.", "hd")
side(LX, 84, 40, "count", "3 corner · 5 edge · 8 inside")
arrow(LX + LW, 104, CX0, 104)

# organs
OY, RH, RG = 135, 80, 16
organs = [
    ("1  The race · one corner keeps beating: the organiser", "reads w, w2 · writes w, w2", [
        "excitable: fire → state = 12; excited while state > 10 (2 updates), then resting 10",
        "fire if resting and a neighbour shows the next beat: phase = (par + 1) mod 3, read from w, w2 as +−, −+, ++",
        "a corner (count = 3) is a pacemaker with its own period, 30–90; reached by another's wave, it stands down for good",
    ], ("w, w2", "beat waves (2)"), ("w, w2", "beat phase, while excited"), "standing, fire"),
    ("2  Handedness · which edge is which", "reads hand · writes hand", [
        "z = count · (mean_hand + 1): a standing corner adds 2, a stood-down one 1.75, a coin 1.5 or 0.5",
        "the organiser's two edge neighbours each show a coin ±0.5, and toss again while the other's is the same",
        "the one on +0.5 starts the edge that becomes y = −1 (yl); the one on −0.5 the one that becomes x = −1 (xl)",
    ], ("hand", "corners and coins (1)"), ("hand", "1 / 0.75 corner, ±0.5 coin"), "role, fire (the organiser's beat)"),
    ("3  Edge labels · each edge learns −1 or +1", "reads xl, yl · writes xl, yl", [
        "each organiser beat starts a label pulse along both its edges; edge cells relay it (show 3, rest 8): one way",
        "half strength beside a corner (corners take it, edges don't); a corner on −1 starts +1 on its other axis",
        "hold lx, ly once two pulses in a row agree; forget a label after 6 organiser beats with none",
    ], ("xl, yl", "label pulses (2)"), ("xl, yl", "a label pulse passing"), "hx, hy (held labels)"),
    ("4  Coordinates · x and y from −1 to 1", "reads x, y · writes x, y", [
        "x = lx if labelled, else clip(mean_x + β · (x − x_prev), −1, 1);   β = 0.9 while drifting, else 0   (y alike)",
        "xs ← xs + (x − xs) / 50;     xss ← xss + (x − xss) / 150",
        "still = |xs − xss| < 0.03 and |ys − yss| < 0.03",
    ], ("x, y", "neighbours' places (2)"), ("x, y", "my place"), "xs, still, which edge"),
    ("5  Naming · S1, S2, M1, M2, T", "reads mark · writes mark", [
        "mark: on the y = 1 and y = −1 edges where |xs| < 0.125 (a 0.05 margin, so it doesn't flicker)",
        "place: past either end of the mark: a sensor on y = 1, an actuator on y = −1 (1 if xs < 0, else 2); on it, on y = 1: T",
        "name = place once held 300 updates, still, with no named neighbour; kept while |xs − its x| < 0.15",
    ], ("mark", "marks, named cells (1)"), None, None),
]
OH = 36 + len(organs) * (RH + RG) - RG + 14
layer(OY, OH, "organs.update · where am I, and what am I called", "rules/organs.py")
for i, (title, io, lines, inp, out, passes) in enumerate(organs):
    y = OY + 36 + i * (RH + RG)
    stage(SX0, y, SX1 - SX0, RH, title, io, lines)
    c = y + RH / 2
    side(LX, c - 22, 44, *inp)
    arrow(LX + LW, c, SX0, c)
    if out:
        side(RX, c - 22, 44, *out)
        arrow(SX1, c, RX, c)
    else:                                                       # naming: a shared mark, and the name the body uses
        side(RX, c - 38, 34, "mark  ·  ±1, or 0 once named")
        arrow(SX1, c - 21, RX, c - 21)
        side(RX, c + 4, 34, "name  →  body", body=True)
        arrow(SX1, c + 21, RX, c + 21, "body")
        text(RX + 12, c + 52, "finds S1, S2, M1, M2, T by name", "colhs")
    if passes:
        link(y + RH, y + RH + RG, passes)

# brain
BY = OY + OH + 20
link(OY + OH, BY, "name (am I S1 or S2?)")
brain = [
    ("Choose", "body: stimulus", [
        "on a stimulus, or by itself with chance 0.01:  fire both channels with chance p / 20, else one: my side",
        "my side: channel 1 or 2, by a coin toss when I took my name;   p in twentieths, born 10 (1/2)",
    ], ("stimulus", "my colour is in view"), None),
    ("Taste · in T cells", "body: taste · writes taste", [
        "given taste ±1: show its sign on taste for 3 updates;   it never says which sensor it is about",
    ], ("taste ±1", "food or poison, at the mouth"), ("taste", "±1 while showing a taste")),
    ("Ping · in sensors and T cells", "reads ping · writes ping", [
        "a stimulated sensor shows ping for 2 updates, then rests 4;  a T cell seeing one does the same: a one-way wave",
        "a sensor that sees a ping while not resting forgets its stimulus (since ← 99): only the last one stimulated learns",
    ], ("ping", "a neighbour's ping (1)"), ("ping", "1 while pinging")),
    ("Learn · in sensors", "reads taste", [
        "taste begins beside me, and since ≤ 15 updates:  p ← round( p + 0.5 · (20 − p if good, else −p) )",
        "three factors: my own recent input, the taste, and no newer stimulus of the other sensor",
    ], ("taste", "a T cell's taste (1)"), None),
]
BRH = 64
BH = 36 + len(brain) * (BRH + RG) - RG + 14
layer(BY, BH, "brain · choose, taste and learn (only in sensors and T cells; shares taste, ping)", "rules/brain.py")
for i, (title, io, lines, inp, out) in enumerate(brain):
    y = BY + 36 + i * (BRH + RG)
    stage(SX0, y, SX1 - SX0, BRH, title, io, lines)
    c = y + BRH / 2
    body = inp[0] in ("stimulus", "taste ±1")
    side(LX, c - 22, 44, *inp, body=body)
    arrow(LX + LW, c, SX0, c, "body" if body else "sig")
    if out:
        side(RX, c - 22, 44, *out)
        arrow(SX1, c, RX, c)

# wiring: channel 1 in full, channel 2 the same
AY = BY + BH + 20
link(BY + BH, AY, "send_1, name")
layer(AY, 212, "wiring.stage, channel 1 · paths from S1 and S2 to M1", "rules/wiring.py, see.py")
sw = (SX1 - SX0 - 3 * 14) / 4
wiring = [
    ("Distance field", "f0–f4", [
        "sink (named M1): r = 0",
        "else r = (lowest + 1) mod 5",
        "  lowest: the neighbour",
        "  residue after the gap",
        "take after 3 agreeing reads",
        "would rise → let go, rest 6",
        "show f_r = +1, others −1",
    ]),
    ("Path sensing", "p0–p2", [
        "u_j = count · (mean_pj + 1)",
        "(nearer, level, farther)",
        "    = M_r⁻¹ · u",
        "split each into tips 1.2,",
        "  pulses 0.4, paths 2",
        "  (at most 2 cells)",
    ]),
    ("Growth", "offer", [
        "source: on once r held 20",
        "below a tip: raise a hand,",
        "  chance 0.5 (0.02 if",
        "  another path above)",
        "tip: one hand twice → go",
        "3 reads of go → join",
        "none farther, twice → leave",
    ]),
    ("Pulse", "p0–p2", [
        "on, timer 0, and send (S1,S2)",
        "  or a pulse farther →",
        "  timer = 6 on + 7 rest",
        "sink: fired += 1",
        "show p = −1 + k · CODE[r]",
        "  k: pulse 0.4, tip 1.2,",
        "     path 2, off 0",
    ]),
]
SY, SH = AY + 36, 160
for i, (title, io, lines) in enumerate(wiring):
    x = SX0 + i * (sw + 14)
    stage(x, SY, sw, SH, title, io, lines, small=True)
    if i < len(wiring) - 1:
        arrow(x + sw + 1, SY + SH / 2, x + sw + 13, SY + SH / 2, "int")
c = SY + SH / 2
side(LX, c - 40, 52, "channel 1 (9)", "f0–f4 · p0–p2 · offer")
arrow(LX + LW, c - 14, SX0, c - 14)
side(RX, c - 40, 52, "channel 1 (9)", "f0–f4 · p0–p2 · offer")
arrow(SX1, c - 14, RX, c - 14)
side(RX, c + 22, 38, "fired_1  →  its thruster", body=True)
arrow(SX1, c + 41, RX, c + 41, "body")
VY = AY + 212 + 20
link(AY + 212, VY, "send_2 (from the brain), name")
layer(VY, 86, "wiring.stage, channel 2 · paths from S1 and S2 to M2", "the same four stages")
for i, (title, io, _) in enumerate(wiring):
    x = SX0 + i * (sw + 14)
    rect(x, VY + 34, sw, 38, "sub")
    text(x + 12, VY + 57, title, "bt")
    text(x + sw - 12, VY + 57, io, "io", "end")
    if i < len(wiring) - 1:
        arrow(x + sw + 1, VY + 53, x + sw + 13, VY + 53, "int")
side(LX, VY + 31, 44, "channel 2 (9)", "f0–f4 · p0–p2 · offer")
arrow(LX + LW, VY + 53, SX0, VY + 53)
side(RX, VY + 12, 44, "channel 2 (9)", "f0–f4 · p0–p2 · offer")
arrow(SX1, VY + 44, RX, VY + 44)
side(RX, VY + 60, 36, "fired_2  →  its thruster", body=True)
arrow(SX1, VY + 66, RX, VY + 66, "body")

# the cell's outline, behind everything, and the legend below it
bottom = VY + 86 + 16
svg.insert(0, f'<rect x="{CX0}" y="72" width="{CX1 - CX0}" height="{bottom - 72}" rx="10" class="cell"/>')
ly = bottom + 34
rect(LX, ly - 12, 16, 12, "nbox", 2)
arrow(LX + 22, ly - 6, LX + 50, ly - 6)
text(LX + 60, ly - 2, "a shared number: read as the neighbours' mean, shown clipped to −1..1 with 1% noise", "colhs")
rect(LX + 620, ly - 12, 16, 12, "bodybox", 2)
arrow(LX + 642, ly - 6, LX + 670, ly - 6, "body")
text(LX + 680, ly - 2, "the body (creature.py): given to, or taken from, a cell by its name", "colhs")
arrow(LX + 1120, ly - 6, LX + 1150, ly - 6, "int")
text(LX + 1160, ly - 2, "kept inside the cell, passed on", "colhs")
H = ly + 16

markers = "".join(
    f'<marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="{size}" markerHeight="{size}" '
    f'markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="{cls}"/></marker>'
    for name, size, cls in (("ah", 9, "ahf"), ("ahb", 13, "ahb"), ("ahm", 8, "ahm")))
OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
               f'aria-labelledby="t"><title id="t">What runs inside one cell</title><style>{STYLE}</style>'
               f'<defs>{markers}</defs><rect width="{W}" height="{H}" class="bg"/>' + "".join(svg) + "</svg>\n")
print(f"wrote {OUT}")
