"""The discrete circuits drawn by hand as SVG (discrete/NOTEBOOK.md): hold and drive (discrete/circuits.py, 14 parts,
D3) with its screened values, media/hold_drive_14.svg; the learning circuit (49 parts, D6), media/learn_hold.svg; and
the learning circuit that gives up and avoids (46 parts, D8, D9), media/learn_avoid.svg; each also as a PNG on a dark
ground for the live view (discrete/watch.py). Okabe-Ito colours, each block also outlined and named (the user is
colour-blind). Redraw them when a circuit changes.

    python -m discrete.draw
"""
import json
import os
import numpy as np

BLK = {"eye": "var(--c-eye)", "osc": "var(--c-osc)", "ma": "var(--c-ma)", "mb": "var(--c-mb)", "if": "var(--c-if)",
       "bit": "var(--c-bit)", "doubt": "var(--c-doubt)", "roam": "var(--c-roam)"}
out = []


def L(*pts, c="var(--ink)", w=2, dash=None):
    d = " ".join(f"{x},{y}" for x, y in pts)
    out.append(f'<polyline points="{d}" fill="none" stroke="{c}" stroke-width="{w}"'
               + (f' stroke-dasharray="{dash}"' if dash else "") + ' stroke-linejoin="round"/>')


def dot(x, y):
    out.append(f'<circle cx="{x}" cy="{y}" r="4" fill="var(--ink)"/>')


def T(x, y, s, cls="lbl", anchor="start"):
    out.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{s}</text>')


def label(x, y, ref, val, c, anchor="start"):
    T(x, y, ref, "ref", anchor)
    out.append(f'<text x="{x}" y="{y + 16}" class="val" text-anchor="{anchor}" fill="{c}">{val}</text>')


def vdd(x, y):           # local supply: a bar with +3 V above; lead from (x,y) down
    L((x - 12, y), (x + 12, y), w=2.5)
    T(x, y - 7, "+3 V", "sup", "middle")


def gnd(x, y):           # local ground below (x, y)
    L((x, y), (x, y + 8))
    for k, h in enumerate((14, 9, 4)):
        L((x - h, y + 8 + 5 * k), (x + h, y + 8 + 5 * k))


def res(x, y0, y1, c):   # vertical resistor from y0 to y1, zigzag body of 44 px in the middle
    m = (y0 + y1) / 2
    a, b = m - 22, m + 22
    L((x, y0), (x, a))
    zz = [(x, a)] + [(x + (8 if k % 2 == 0 else -8), a + 44 * (k + 0.5) / 6) for k in range(6)] + [(x, b)]
    L(*zz, c=c, w=2.5)
    L((x, b), (x, y1))


def resh(x0, x1, y, c):  # horizontal resistor from x0 to x1
    m = (x0 + x1) / 2
    a, b = m - 22, m + 22
    L((x0, y), (a, y))
    zz = [(a, y)] + [(a + 44 * (k + 0.5) / 6, y + (8 if k % 2 == 0 else -8)) for k in range(6)] + [(b, y)]
    L(*zz, c=c, w=2.5)
    L((b, y), (x1, y))


def diode(x, y0, y1, c):  # vertical diode, anode at y0, cathode at y1 (current flows from y0 to y1)
    m = (y0 + y1) / 2
    s = 1 if y1 > y0 else -1
    L((x, y0), (x, m - 9 * s)); L((x, m + 9 * s), (x, y1))
    out.append(f'<polygon points="{x - 10},{m - 9 * s} {x + 10},{m - 9 * s} {x},{m + 9 * s}" fill="none" stroke="{c}"'
               f' stroke-width="2"/>')
    L((x - 11, m + 9 * s), (x + 11, m + 9 * s), c=c, w=2.5)


def cap(x, y0, y1, c):
    m = (y0 + y1) / 2
    L((x, y0), (x, m - 5))
    L((x, m + 5), (x, y1))
    L((x - 15, m - 5), (x + 15, m - 5), c=c, w=3)
    L((x - 15, m + 5), (x + 15, m + 5), c=c, w=3)


def arrow(x0, y0, x1, y1, c):  # filled arrowhead at (x1, y1) pointing from (x0, y0)
    v = np.array([x1 - x0, y1 - y0], float); v /= np.hypot(*v); n = np.array([-v[1], v[0]])
    p = np.array([x1, y1]); a = p - 9 * v + 4.5 * n; b = p - 9 * v - 4.5 * n
    out.append(f'<polygon points="{p[0]},{p[1]} {a[0]},{a[1]} {b[0]},{b[1]}" fill="{c}"/>')


def bjt(bx, cy, kind, c, mirror=False, top="c"):
    """Base terminal at (bx, cy); bar 20 px in; the top/bottom leads end 40 px in, 25 px up/down. Returns
    (top end, bottom end). top: which terminal is on top ('c' or 'e')."""
    s = -1 if mirror else 1
    bar = bx + 20 * s
    end = bx + 40 * s
    out.append(f'<circle cx="{bx + 26 * s}" cy="{cy}" r="21" fill="none" stroke="{c}" stroke-width="1.5"/>')
    L((bx, cy), (bar, cy))
    L((bar, cy - 12), (bar, cy + 12), w=3.5)
    t, b = (end, cy - 25), (end, cy + 25)
    L((bar, cy - 6), t)
    L((bar, cy + 6), b)
    e0, e1 = ((bar, cy - 6), t) if top == "e" else ((bar, cy + 6), b)
    if kind == "NPN":
        arrow(*e0, *e1, "var(--ink)")
    else:
        m = ((e0[0] + e1[0]) / 2, (e0[1] + e1[1]) / 2)
        arrow(*e1, *m, "var(--ink)")
    return t, b


def photodiode(x, y0, y1):  # cathode up: current flows down into the node
    m = (y0 + y1) / 2
    c = BLK["if"]
    L((x, y0), (x, m - 9)); L((x, m + 9), (x, y1))
    out.append(f'<polygon points="{x},{m - 9} {x - 10},{m + 9} {x + 10},{m + 9}" fill="none" stroke="{c}" stroke-width="2"/>')
    L((x - 11, m - 9), (x + 11, m - 9), c=c, w=2.5)
    for k in (0, 12):
        L((x - 34, m - 22 + k), (x - 16, m - 10 + k), c=c, w=1.5)
        arrow(x - 34, m - 22 + k, x - 15, m - 9 + k, c)


def schmitt(x, y, name):
    c = BLK["if"]
    out.append(f'<polygon points="{x},{y - 18} {x + 34},{y} {x},{y + 18}" fill="var(--bg)" stroke="{c}" stroke-width="2" stroke-dasharray="4 3"/>')
    L((x + 5, y + 5), (x + 13, y + 5), (x + 13, y - 5), (x + 19, y - 5), c=c, w=1.3)
    L((x + 9, y + 5), (x + 9, y - 5), (x + 15, y - 5), c=c, w=1.3)
    L((x + 34, y), (x + 50, y), c=c, dash="4 3")
    T(x + 54, y + 5, f"thruster {name}", "ifl")


def box(x, y, w, h, name, c):
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{c}" fill-opacity="0.06" stroke="{c}"'
               f' stroke-width="1.5" stroke-dasharray="7 5"/>')
    T(x + 10, y + 20, name, "blk")


HERE = os.path.dirname(os.path.abspath(__file__))


def eng(v, u):
    for f, p in ((1e9, "G"), (1e6, "M"), (1e3, "k"), (1, ""), (1e-9, "n"), (1e-12, "p")):
        if abs(v) >= f:
            x = v / f
            return f"{x:.3g} {p}{u}".replace(" ", " ")
    return f"{v:g}{u}"


def hold_drive():
    P = json.load(open(os.path.join(HERE, "results", "hold_drive_screened.json")))["best"]
    # blocks
    box(30, 30, 345, 400, "eyes and hold", BLK["eye"])
    box(390, 30, 320, 520, "oscillator (a PUT from two transistors)", BLK["osc"])
    box(720, 135, 160, 300, "motor A: scan", BLK["ma"])
    box(890, 30, 235, 405, "motor B: drive", BLK["mb"])
    # eyes: photodiodes from the supply into e (uncounted, part of the body)
    for x, nm in ((70, "left"), (140, "right")):
        vdd(x, 110)
        photodiode(x, 110, 190)
        T(x + 14, 160, nm, "ifl")
    L((70, 190), (70, 235), (140, 235)); L((140, 190), (140, 235), (195, 235)); dot(140, 235)
    T(80, 255, "e", "node")
    # Q0: emitter follower
    t, b = bjt(195, 235, "NPN", BLK["eye"])
    vdd(t[0], 175); L((t[0], 175), t)
    label(250, 222, "Q0", "2N3904", BLK["eye"])
    # h node, C1
    L(b, (235, 300), (300, 300)); dot(235, 300)
    cap(235, 300, 370, BLK["eye"]); gnd(235, 370)
    label(255, 342, "C1", eng(P["ch"], "F"), BLK["eye"])
    L((300, 300), (300, 80), (1040, 80)); dot(300, 300)
    T(310, 296, "h", "node"); T(310, 70, "h (the hold)", "node")
    # oscillator
    dot(450, 80)
    res(450, 80, 280, BLK["osc"]); label(466, 176, "R9 (rf)", eng(P["rf"], "Ω"), BLK["osc"])
    vdd(540, 130); res(540, 130, 280, BLK["osc"]); label(556, 200, "R2 (rt)", eng(P["rt"], "Ω"), BLK["osc"])
    L((450, 280), (540, 280)); dot(540, 280)
    T(460, 298, "a", "node")
    cap(540, 280, 400, BLK["osc"]); gnd(540, 400)
    label(480, 350, "C3 (ct)", eng(P["ct"], "F"), BLK["osc"], "end")
    L((540, 280), (590, 280), (590, 290))
    # Q6 PNP, base on the right, emitter on top
    t, b = bjt(630, 315, "PNP", BLK["osc"], mirror=True, top="e")
    L((590, 290), t)
    label(582, 372, "Q6", "2N3906", BLK["osc"], "end")
    # g
    L((630, 315), (660, 315)); dot(660, 315)
    vdd(660, 130); res(660, 130, 315, BLK["osc"]); label(648, 250, "R4", eng(P["rg1"], "Ω"), BLK["osc"], "end")
    res(660, 315, 400, BLK["osc"]); gnd(660, 400); label(648, 352, "R5", eng(P["rg2"], "Ω"), BLK["osc"], "end")
    T(640, 308, "g", "node")
    # b bus from Q6's collector
    L(b, (590, 470)); dot(590, 470)
    T(578, 466, "b", "node", "end")
    L((590, 470), (610, 470))
    t7, b7 = bjt(610, 470, "NPN", BLK["osc"])
    L(t7, (650, 440), (685, 440), (685, 315), (660, 315))
    gnd(*b7)
    label(668, 488, "Q7", "2N3904", BLK["osc"])
    # R8 shunt from b
    L((590, 470), (545, 470)); dot(545, 470)
    res(545, 470, 520, BLK["osc"])
    gnd(545, 520)
    label(530, 486, "R8 (rsh)", eng(P["rsh"], "Ω"), BLK["osc"], "end")
    # b to the motor buffers, along the bottom
    L((590, 470), (590, 570), (900, 570), (900, 360), (920, 360))
    L((740, 570), (740, 360), (760, 360)); dot(740, 570)
    T(745, 590, "b: every beat of the oscillator", "node")
    # motor A
    vdd(800, 175); res(800, 175, 290, BLK["ma"]); label(812, 225, "R11", eng(P["rp"], "Ω"), BLK["ma"])
    t, b = bjt(760, 360, "NPN", BLK["ma"])
    L(t, (800, 290)); dot(800, 290); gnd(*b)
    label(812, 340, "Q10", "2N3904", BLK["ma"])
    L((800, 290), (840, 290)); T(806, 282, "m0", "node")
    schmitt(840, 290, "A")
    # motor B
    dot(960, 80)
    res(960, 80, 290, BLK["mb"]); label(972, 180, "R13", eng(P["rp"], "Ω"), BLK["mb"])
    t, b = bjt(920, 360, "NPN", BLK["mb"])
    L(t, (960, 290)); dot(960, 290); gnd(*b)
    label(972, 340, "Q12", "2N3904", BLK["mb"])
    L((960, 290), (1000, 290)); T(966, 282, "m1", "node")
    schmitt(1000, 290, "B")



CSS = (".ref{font:600 13px sans-serif;fill:var(--ink)}.val{font:12px monospace}.node{font:italic 600 13px serif;"
       "fill:var(--mute)}.sup{font:10px sans-serif;fill:var(--mute)}.blk{font:600 12px sans-serif;fill:var(--ink)}"
       ".ifl{font:11px sans-serif;fill:var(--c-if)}")
DARK = {"--ink": "#e3e7ea", "--mute": "#9aa5ae", "--bg": "#14181c", "--c-eye": "#56B4E9", "--c-osc": "#E69F00",
        "--c-ma": "#2CC197", "--c-mb": "#E08DC0", "--c-if": "#7b858d", "--c-bit": "#F07B3F", "--c-doubt": "#CC79A7",
        "--c-roam": "#F0E442"}
LIGHT = {"--ink": "#1d2328", "--mute": "#5b6670", "--bg": "#ffffff", "--c-eye": "#0072B2", "--c-osc": "#C98500",
         "--c-ma": "#007A5A", "--c-mb": "#B5508F", "--c-if": "#8a949c", "--c-bit": "#D55E00", "--c-doubt": "#9B4F86",
         "--c-roam": "#8C7A00"}
def learn(avoid=False):
    """learn_hold, or (avoid) learn_avoid: the roam replaced by giving up and avoiding."""
    import inspect
    from discrete.circuits import learn_avoid, learn_hold
    P = {}
    for build in (learn_hold, learn_avoid) if avoid else (learn_hold,):
        P.update({k: p.default for k, p in inspect.signature(build).parameters.items() if k != "kw"})
    G, B, D, O, R = BLK["eye"], BLK["bit"], BLK["doubt"], BLK["osc"], BLK["roam"]
    box(20, 20, 410, 485, "eyes and the gate", G)
    box(440, 20, 420, 485, "the bit: a toggle latch", B)
    box(20, 515, 840, 425, "the doubt: two poisons in quick succession", D)
    box(870, 20, 840, 545, "hold and drive (hold12): scan, and drive while the hold is up", O)
    box(870, 575, 840, 365, "giving up, and turning from poison ahead" if avoid else
        "the roam: a phantom pulse every few seconds", R)
    # the hold bus
    L((190, 80), (1480, 80)); T(600, 72, "h (the hold)", "node")
    # eyes, each gated by a Darlington shunt fed from the latch
    for x0, nm, c, ybus, k in ((140, "left", "c0", 470, 0), (330, "right", "c1", 485, 1)):
        vdd(x0, 105)
        photodiode(x0, 105, 175)
        T(x0 + 12, 130, f"eye {k}", "ifl")
        L((x0, 175), (x0, 210)); dot(x0, 200)
        T(x0 + 6, 196, f"s{k}", "node")
        L((x0, 200), (x0 + 50, 200)); diode(x0 + 50, 200, 80, G); dot(x0 + 50, 80)
        tq, bq = bjt(x0 - 40, 300, "NPN", G)            # the shunt: collector at s, emitter to ground
        L((x0, 210), tq)
        if avoid:                                       # (its emitter to k: the current it sinks empties the hold)
            L(bq, (bq[0], bq[1] + 14)); dot(bq[0], bq[1] + 14); T(bq[0] + 6, bq[1] + 20, "k", "node")
        else:
            gnd(*bq)
        td, bd = bjt(x0 - 80, 250, "NPN", G)            # its driver (Darlington)
        L(td, (x0 - 40, 210), (x0, 210)); dot(x0, 210)
        L(bd, (x0 - 40, 300))
        L((x0 - 80, 250), (x0 - 80, 330)); res(x0 - 80, 330, 440, G)
        label(x0 - 72, 395, "rk", eng(P["rk"], "Ω"), G)
        L((x0 - 80, 440), (x0 - 80, ybus), (455 if k == 0 else 470, ybus))
        T(x0 - 76, ybus - 4, f"from {c}", "node")
        if k == 0:
            label(x0 + 18, 330, "2 x 2N3904", "", G)
    # the latch: QL0 (collector c0, base on its right), QL1 (collector c1, base on its left)
    for x, nm in ((560, "c0"), (730, "c1")):
        vdd(x, 120); res(x, 120, 200, B); label(x + 12, 165, "rl", eng(P["rl"], "Ω"), B)
        L((x, 200), (x, 305))
        T(x + 6, 222 if x == 730 else 222, nm, "node")
    t0, b0 = bjt(600, 330, "NPN", B, mirror=True); gnd(*b0)
    t1, b1 = bjt(690, 330, "NPN", B); gnd(*b1)
    label(700, 405, "2 x 2N3904", "", B)
    # cross-coupling: c0 -> b1, c1 -> b0
    dot(560, 250); resh(560, 660, 250, B); L((660, 250), (690, 250), (690, 330))
    label(610, 222, "rx", eng(P["rx"], "Ω"), B, "middle")
    dot(730, 280); resh(730, 640, 280, B); L((640, 280), (620, 280), (620, 330), (600, 330))
    label(745, 300, "rx", eng(P["rx"], "Ω"), B)
    # the c0, c1 buses from the gate
    L((455, 470), (455, 215), (560, 215)); dot(560, 215)
    L((470, 485), (845, 485), (845, 215), (730, 215)); dot(730, 215)
    # steering: j0 from c0 by rs, the diode from b0, the capacitor from w
    dot(560, 235); L((560, 235), (500, 235)); res(500, 235, 360, B); L((500, 360), (500, 430))
    label(484, 300, "rs", eng(1e9, "Ω"), B, "end")
    dot(620, 330); diode(620, 330, 430, B); L((620, 430), (500, 430)); dot(500, 430); T(506, 424, "j0", "node")
    cap(500, 430, 465, B); L((500, 465), (500, 500))
    dot(730, 265); L((730, 265), (800, 265)); res(800, 265, 380, B); L((800, 380), (800, 430))
    label(812, 330, "rs", eng(1e9, "Ω"), B)
    dot(670, 330); L((690, 330), (670, 330)); diode(670, 330, 430, B); L((670, 430), (800, 430)); dot(800, 430)
    T(806, 424, "j1", "node")
    cap(800, 430, 465, B); L((800, 465), (800, 500))
    label(512, 462, "cs", eng(P["cs"], "F"), B)
    L((500, 500), (800, 500)); T(700, 496, "w", "node")
    # the doubt: the taste into q
    c = BLK["if"]
    out.append(f'<circle cx="80" cy="680" r="18" fill="none" stroke="{c}" stroke-width="2" stroke-dasharray="4 3"/>')
    arrow(80, 694, 80, 668, c); L((80, 662), (80, 620), (380, 620)); L((80, 698), (80, 720)); gnd(80, 720)
    T(104, 676, "taste: + food,", "ifl"); T(104, 690, "- poison", "ifl")
    T(200, 612, "q", "node")
    dot(170, 620); cap(170, 620, 760, D); gnd(170, 760); label(186, 700, "cq", eng(P["cq"], "F"), D)
    dot(250, 620); vdd(250, 560); res(250, 560, 620, D); label(262, 588, "rq", eng(P["rq"], "Ω"), D)
    resh(300, 420, 620, D); label(360, 645, "rq1", eng(P["rq1"], "Ω"), D, "middle")
    tc1, bc1 = bjt(420, 620, "NPN", D); gnd(*bc1)
    vdd(460, 550); res(460, 550, 595, D); L((460, 595), tc1); label(472, 568, "rw1", eng(P["rw1"], "Ω"), D)
    dot(460, 595); L((460, 595), (520, 595), (520, 680), (540, 680)); T(526, 612, "w1", "node")
    tc2, bc2 = bjt(540, 680, "NPN", D); gnd(*bc2)
    vdd(640, 560); res(640, 560, 640, D); label(652, 598, "rw", eng(P["rw"], "Ω"), D)
    L(tc2, (580, 645), (640, 645), (640, 640)); dot(640, 645)
    L((640, 645), (700, 645), (700, 500)); dot(700, 500)
    label(600, 730, "2 x 2N3904", "", D)
    T(40, 900, "each poison pulls q down ~0.8 V; it recovers through rq over ~1.5 s; food lifts it. Below ~0.65 V, the", "ifl")
    T(40, 918, "first transistor lets go, the second pulls w down: a falling edge that flips the latch.", "ifl")
    # hold and drive (hold12)
    dot(930, 80); cap(930, 80, 200, O); gnd(930, 200); label(946, 145, "ch", eng(P["ch"], "F"), O)
    vdd(1060, 130); res(1060, 130, 280, O); label(1076, 200, "rt", eng(P["rt"], "Ω"), O)
    T(1040, 298, "a", "node")
    cap(1060, 280, 400, O); gnd(1060, 400); label(1048, 350, "ct", eng(P["ct"], "F"), O, "end")
    L((1060, 280), (1110, 280), (1110, 290))
    t, b = bjt(1150, 315, "PNP", O, mirror=True, top="e"); L((1110, 290), t)
    L((1150, 315), (1180, 315)); dot(1180, 315); T(1160, 308, "g", "node")
    vdd(1180, 130); res(1180, 130, 315, O); label(1192, 230, "rg1", eng(P["rg1"], "Ω"), O)
    res(1180, 315, 400, O); gnd(1180, 400); label(1192, 360, "rg2", eng(P["rg2"], "Ω"), O)
    L(b, (1110, 470)); dot(1110, 470); T(1098, 466, "b", "node", "end")
    L((1110, 470), (1130, 470))
    t7, b7 = bjt(1130, 470, "NPN", O); L(t7, (1170, 440), (1205, 440), (1205, 315), (1180, 315)); gnd(*b7)
    L((1110, 470), (1065, 470)); dot(1065, 470); res(1065, 470, 515, O); gnd(1065, 515)
    label(1050, 496, "rsh", eng(P["rsh"], "Ω"), O, "end")
    label(1215, 470, "2N3906, 2N3904", "", O)
    L((1110, 470), (1110, 550), (1420, 550), (1420, 360), (1440, 360))
    L((1260, 550), (1260, 360), (1280, 360)); dot(1260, 550)
    vdd(1320, 175); res(1320, 175, 290, BLK["ma"]); label(1332, 225, "rp", eng(P["rp"], "Ω"), BLK["ma"])
    t, b = bjt(1280, 360, "NPN", BLK["ma"]); L(t, (1320, 290)); dot(1320, 290); gnd(*b)
    L((1320, 290), (1360, 290)); T(1326, 282, "m0", "node"); schmitt(1360, 290, "A")
    dot(1480, 80); res(1480, 80, 290, BLK["mb"]); label(1492, 180, "rb", eng(P["rb"], "Ω"), BLK["mb"])
    t, b = bjt(1440, 360, "NPN", BLK["mb"]); L(t, (1480, 290)); dot(1480, 290); gnd(*b)
    L((1480, 290), (1520, 290)); T(1486, 282, "m1", "node"); schmitt(1520, 290, "B")
    if avoid:
        _give_up(P, R, G)
        return
    # the roam
    vdd(950, 615); res(950, 615, 720, R); label(962, 670, "rt2", eng(P["rt2"], "Ω"), R)
    dot(950, 720); T(930, 716, "a2", "node", "end")
    cap(950, 720, 820, R); gnd(950, 820); label(938, 775, "ct2", eng(P["ct2"], "F"), R, "end")
    L((950, 720), (1000, 720), (1000, 730))
    t, b = bjt(1040, 755, "PNP", R, mirror=True, top="e"); L((1000, 730), t)
    L((1040, 755), (1070, 755)); dot(1070, 755); T(1078, 750, "g2", "node")
    vdd(1070, 615); res(1070, 615, 755, R); label(1082, 690, "rg3", eng(P["rg3"], "Ω"), R)
    res(1070, 755, 860, R); gnd(1070, 860); label(1082, 815, "rg4", eng(P["rg4"], "Ω"), R)
    L(b, (1000, 840)); dot(1000, 840)
    t7, b7 = bjt(1000, 840, "NPN", R); L(t7, (1040, 800), (1110, 800), (1110, 755), (1070, 755)); dot(1110, 800)
    gnd(*b7)
    L((1000, 840), (930, 840)); res(930, 840, 895, R); gnd(930, 895)
    label(918, 872, "rsh2", eng(P["rsh2"], "Ω"), R, "end")
    vdd(1250, 615); res(1250, 615, 700, R); label(1262, 660, "rbe", eng(P["rbe"], "Ω"), R)
    dot(1250, 700); res(1250, 700, 800, R); L((1250, 800), (1110, 800)); label(1262, 755, "rbg", eng(P["rbg"], "Ω"), R)
    L((1250, 700), (1290, 700))
    t, b = bjt(1290, 700, "PNP", R, top="e"); vdd(t[0], 650); L((t[0], 650), t)
    L(b, (t[0], 900), (1700, 900), (1700, 80), (1480, 80)); T(1420, 892, "to h: a phantom pulse", "node")
    label(1360, 690, "2N3906", "", R)
    label(1120, 860, "2N3906, 2N3904", "", R)


def _give_up(P, R, G):
    """learn_avoid's lower right: the followers from the eyes onto u, its leak, the PNP that feeds the hold once u has
    sagged; and k, the shunts' emitters, on the NPN that empties the hold."""
    for x, s in ((940, "s0"), (1060, "s1")):           # followers: collector at the supply, emitter onto u
        t, b = bjt(x, 680, "NPN", R); vdd(t[0], 630); L((t[0], 630), t)
        L((x - 30, 680), (x, 680)); T(x - 34, 676, s, "node", "end")
        L(b, (b[0], 800))
    L((980, 800), (1260, 800)); dot(1100, 800); T(986, 794, "u", "node")
    label(900, 860, "2 x 2N3904", "", R)
    dot(1140, 800); cap(1140, 800, 880, R); gnd(1140, 880); label(1152, 845, "cu", eng(P["cu"], "F"), R)
    dot(1200, 800); res(1200, 800, 880, R); gnd(1200, 880); label(1212, 845, "ru", eng(P["ru"], "Ω"), R)
    L((1260, 800), (1260, 700), (1300, 700))
    t, b = bjt(1300, 700, "PNP", R, top="e"); vdd(t[0], 650); L((t[0], 650), t)
    L(b, (t[0], 900), (1700, 900), (1700, 80), (1480, 80)); T(1350, 892, "to h: drive on", "node")
    label(1370, 690, "2N3906", "", R)
    dot(1480, 780); T(1468, 774, "k", "node", "end")
    res(1480, 780, 880, G); gnd(1480, 880); label(1468, 835, "rd", eng(P["rd"], "Ω"), G, "end")
    L((1480, 780), (1560, 780))
    t, b = bjt(1560, 780, "NPN", G); gnd(*b); L(t, (t[0], 720), (1700, 720)); dot(1700, 720)
    label(1610, 800, "2N3904", "", G)
    T(890, 925, "u sags once the free eye has seen nothing for a few seconds: the PNP feeds the hold, both thrusters "
      "drive straight.", "ifl")
    T(1490, 690, "the silenced eye's current", "ifl"); T(1490, 704, "empties the hold: turn", "ifl")


DRAWINGS = {"hold_drive_14": (hold_drive, (0, 0, 1150, 610)), "learn_hold": (learn, (0, 0, 1720, 950)),
            "learn_avoid": (lambda: learn(avoid=True), (0, 0, 1720, 950))}


def svg(name, colours):
    draw, view = DRAWINGS[name]
    out.clear()
    draw()
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{" ".join(map(str, view))}"><style>{CSS}</style>'
         f'<rect x="0" y="0" width="{view[2]}" height="{view[3]}" fill="var(--bg)"/>{"".join(out)}</svg>')
    for k, v in colours.items():                    # resolved: cairosvg doesn't do CSS variables
        s = s.replace(f"var({k})", v)
    return s


if __name__ == "__main__":
    import cairosvg
    media = os.path.join(HERE, "..", "media")
    for name, (_, view) in DRAWINGS.items():
        open(os.path.join(media, f"{name}.svg"), "w").write(svg(name, LIGHT))
        cairosvg.svg2png(bytestring=svg(name, DARK).encode(), write_to=os.path.join(media, f"{name}.png"),
                         output_width=2 * view[2])
        print(f"wrote media/{name}.svg and .png")
