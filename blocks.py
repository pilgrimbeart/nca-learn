"""The block view: a circuit brain at level 1, its motifs as blocks, found from the netlist and drawn live, in greys.
Watching only: it reads the circuit and never writes it.

  Neurons (a node with its own feedback elements) are circles: their brightness is their voltage, and they flash
  white when they spike. Synapses (an element from one neuron to another) are arrows, solid if excitatory and dashed
  if inhibitory, as thick as their recent current. Every other node is a meter (a bar, 0..1 of its range), hung where
  it belongs: on the arrow it gates (a learned synapse's strength), or by the neuron it acts on, or the one that
  drives it; a brain may say where some belong (block_hints). Links through such nodes are drawn too: a thin line
  from the neuron driving a node to its meter, and from a meter to the neuron it acts on (a bar at the end if it
  inhibits); faint dots where one node drives or gates another. The body's contacts sit at the edges: the eyes on the
  left (lit while their colour is seen), the thrusters on the right (lit when they fire), the taste below its neuron
  (+ or - when a meal is tasted). A unit grown in the life (a bridge) is a new circle on the arrow it split, outlined
  for a while after it grows. Layout: sensors left, motors right, a neuron between others where it connects them,
  one with inputs only below.
"""

from __future__ import annotations

import numpy as np

from units import I_TYP

SPIKE_FLASH = 3     # ticks (units.TICK) a spike keeps a neuron white, so it can be seen (watching, not time)
TASTE_SHOW = 30     # ticks a taste stays marked
NEW = 300           # ticks a grown unit stays outlined
SMOOTH = 0.8        # how much of an arrow's drawn current carries over from one frame to the next
GAP = 30            # pixels between neighbouring meters
LEGEND = ("E eligibility  W, P learned strength  H hold/hush  h help  x sprout  F frustration  D grown  |  "
          "arrows: solid excites, dashed inhibits, thick = current")
WHITE, LIGHT, MID, DARK, INK = (255, 255, 255), (190, 190, 190), (120, 120, 120), (55, 55, 55), (30, 30, 30)


def shade(x):
    g = int(40 + 215 * min(max(x, 0.0), 1.0))
    return (g, g, g)


class BlockView:
    def __init__(self, brain):
        self.brain = brain
        self.current = {}                               # element -> smoothed current, for arrow thickness
        self.last_spike = {}                            # neuron -> tick
        self.last_taste = (-10 ** 9, 0.0)

    # structure, found from the netlist
    def structure(self):
        c, b = self.brain.circuit, self.brain
        own = {}
        for e, (_, (to, frm, gate)) in enumerate(c.elements):
            if to == frm:
                own[to] = own.get(to, 0) + 1
        neurons = [n for n, k in own.items() if k >= 2]
        nset = set(neurons)
        arrows = [(e, frm, to, gate) for e, (_, (to, frm, gate)) in enumerate(c.elements)
                  if to in nset and frm in nset and to != frm]
        hints = b.block_hints() if hasattr(b, "block_hints") else {}
        inputs = {b.taste_node}
        place = {}                                      # state node -> ("arrow", element) or ("near", neuron)
        for node, (kind, where) in hints.items():
            if kind == "arrow":
                e = next((e for e, f, t, _ in arrows if (f, t) == where), None)
                place[node] = ("arrow", e) if e is not None else ("near", where[0])
            else:
                place[node] = ("near", where)
        for e, f, t, g in arrows:                       # a node gating a synapse: its strength, on the arrow
            if g >= 0 and g not in place and g not in nset:
                place[g] = ("arrow", e)
        state = [n for n in range(len(c.names)) if n not in nset and n not in inputs]
        for _ in range(4):                              # the rest: by the neuron it acts on, or the one driving it
            for n in state:
                if n in place:
                    continue
                into = [t for _, (t, f, _) in c.elements if f == n and t in nset]
                strongest = sorted(c.elements, key=lambda el: -el[0][0])     # the strongest charger first
                drv = [f for (g, *_), (t, f, _) in strongest if t == n and f in nset and g > 0]
                via = [p for _, (t, f, g) in c.elements if t == n for p in (f, g) if p in place]
                if into:
                    place[n] = ("near", into[0])
                elif drv:
                    place[n] = ("near", drv[0])
                elif via:
                    kind, where = place[via[0]]
                    place[n] = (kind, where)
        return neurons, arrows, place

    def layout(self, neurons, arrows):
        b = self.brain
        pos = {}
        for i, s in enumerate(b.sensors):
            pos[s] = (0.16, 0.22 + 0.42 * i)
        for i, m in enumerate(b.motors):
            pos[m] = (0.84, 0.22 + 0.42 * i)
        rest = [n for n in neurons if n not in pos]
        for _ in range(3):
            for n in rest:
                pre = [pos[f] for _, f, t, _ in arrows if t == n and f in pos]
                post = [pos[t] for _, f, t, _ in arrows if f == n and t in pos]
                if pre and post:                        # between what it connects (a bridge on a split synapse)
                    x = (np.mean([p[0] for p in pre]) + np.mean([p[0] for p in post])) / 2
                    y = (np.mean([p[1] for p in pre]) + np.mean([p[1] for p in post])) / 2 - 0.08
                    pos[n] = (x, y)
                elif pre and n not in pos:              # inputs only (the taste neuron): below, in the middle
                    pos[n] = (0.5, 0.86)
        for n in rest:
            pos.setdefault(n, (0.5, 0.5))
        return pos

    # drawing
    def draw(self, screen, rect, life, font, small):
        import pygame
        b, c = self.brain, self.brain.circuit
        pygame.draw.rect(screen, (18, 18, 18), rect)
        if c.V is None:
            return
        neurons, arrows, place = self.structure()
        pos = self.layout(neurons, arrows)
        X = lambda p: (int(rect.x + p[0] * rect.w), int(rect.y + p[1] * rect.h))
        spikes = b.history[-1][1] if b.history else np.zeros(len(c.V), dtype=int)
        for n in neurons:
            if n < len(spikes) and spikes[n] > 0:
                self.last_spike[n] = life.t
        inj = getattr(b, "last_inject", None)
        if inj is not None and inj[b.taste_node] != 0:
            self.last_taste = (life.t, float(np.sign(inj[b.taste_node])))
        R = max(10, rect.h // 16)
        # arrows: thickness from the element's present current, smoothed
        gain, offset, slope, _, sig = c.el_arr
        for e, f, t, g in arrows:
            x = slope[e] * (c.Vx[e] - offset[e])
            out = 1.0 / (1.0 + np.exp(-x)) if sig[e] > 0.5 else np.tanh(x)
            if g >= 0:
                out *= min(max(c.V[g], 0.0), 1.0)
            self.current[e] = SMOOTH * self.current.get(e, 0.0) + (1 - SMOOTH) * abs(out)
            a, z = np.array(X(pos[f]), float), np.array(X(pos[t]), float)
            d = z - a
            d /= max(np.linalg.norm(d), 1.0)
            a2, z2 = a + d * R, z - d * (R + 4)
            width = 2 + int(7 * min(self.current[e] * 3, 1.0))
            colour = LIGHT if self.current[e] > 0.05 else MID
            if gain[e] >= 0:
                pygame.draw.line(screen, colour, a2, z2, width)
                tip = [z2, z2 - d * 10 + np.array([-d[1], d[0]]) * 6, z2 - d * 10 - np.array([-d[1], d[0]]) * 6]
                pygame.draw.polygon(screen, colour, tip)
            else:                                       # inhibitory: dashed, ending in a bar
                for k in range(0, int(np.linalg.norm(z2 - a2)), 12):
                    pygame.draw.line(screen, colour, a2 + d * k, a2 + d * min(k + 6, np.linalg.norm(z2 - a2)), width)
                bar = np.array([-d[1], d[0]]) * 8
                pygame.draw.line(screen, colour, z2 - bar, z2 + bar, 3)
        # meters, on arrows and by neurons: where each goes
        by_neuron, by_arrow = {}, {}
        for n, (kind, where) in place.items():
            if kind != "hide":                          # (a brain may hide machinery too fine to show)
                (by_arrow if kind == "arrow" else by_neuron).setdefault(where, []).append(n)
        e_of = {e: (f, t) for e, f, t, _ in arrows}
        at = {}                                         # meter -> (its top-left corner, its index in its row)
        for e, nodes in by_arrow.items():
            if e not in e_of:
                continue
            f, t = e_of[e]
            a, z = np.array(X(pos[f]), float), np.array(X(pos[t]), float)
            p = a + (z - a) * (0.3 + 0.18 * (e % 2))          # staggered, so crossing arrows' meters don't collide
            for k, n in enumerate(nodes):
                at[n] = ((int(p[0]) + GAP * k - 6, int(p[1]) - 34), k)
        for nrn, nodes in by_neuron.items():
            if nrn not in pos:
                continue
            p = X(pos[nrn])
            for k, n in enumerate(nodes):
                at[n] = ((p[0] + R + 8 + GAP * k, p[1] - 14), k)
        # links through state nodes: from the neuron driving a node to its meter, from a meter to the neuron it acts
        # on (ending in a bar if it inhibits), and faintly between meters (one node driving or gating another)
        mid = lambda n: np.array((at[n][0][0] + 5, at[n][0][1] + 14), float)
        nset = set(neurons)
        for e, (_, (t, f, g)) in enumerate(c.elements):
            if t == f or (t in nset and f in nset):
                continue
            x = slope[e] * (c.Vx[e] - offset[e])
            out = 1.0 / (1.0 + np.exp(-x)) if sig[e] > 0.5 else np.tanh(x)
            out *= min(max(c.V[g], 0.0), 1.0) if g >= 0 else 1.0
            self.current[e] = SMOOTH * self.current.get(e, 0.0) + (1 - SMOOTH) * abs(out)
            w = 1 + int(3 * min(self.current[e] * 3, 1.0))
            ends = []
            if f in nset and t in at:
                ends.append((np.array(X(pos[f]), float), mid(t), R, 6, False))
            elif f in at and t in nset:
                ends.append((mid(f), np.array(X(pos[t]), float), 6, R + 3, True))
            elif f in at and t in at:
                ends.append((mid(f), mid(t), 6, 6, None))
            if g >= 0 and g in at and t in at and g != t:
                ends.append((mid(g), mid(t), 6, 6, None))
            for a, z, ra, rz, into in ends:
                d = z - a
                L = np.linalg.norm(d)
                if L < 1:
                    continue
                d /= L
                a2, z2 = a + d * ra, z - d * rz
                if into is None:                        # between meters: faint and dotted
                    for k in range(0, int(L - ra - rz), 8):
                        pygame.draw.line(screen, DARK, a2 + d * k, a2 + d * min(k + 3, L - ra - rz), 1)
                    continue
                colour = LIGHT if self.current[e] > 0.05 else MID
                if gain[e] >= 0:
                    pygame.draw.line(screen, colour, a2, z2, w)
                else:
                    for k in range(0, int(L - ra - rz), 10):
                        pygame.draw.line(screen, colour, a2 + d * k, a2 + d * min(k + 5, L - ra - rz), w)
                if into and gain[e] < 0:
                    bar = np.array([-d[1], d[0]]) * 7
                    pygame.draw.line(screen, colour, z2 - bar, z2 + bar, 3)
        for n, (corner, k) in at.items():
            self.meter(screen, small, corner, n, k)
        # neurons
        grown = {b._bridge_of(s, m): t for t, s, m in getattr(b, "bridges", [])} if hasattr(b, "_bridge_of") else {}
        for n in neurons:
            p = X(pos[n])
            flash = life.t - self.last_spike.get(n, -10 ** 9) < SPIKE_FLASH
            pygame.draw.circle(screen, WHITE if flash else shade((c.V[n] + 5.0) / 6.0), p, R)
            new = n in grown and life.t - grown[n] < NEW
            pygame.draw.circle(screen, WHITE, p, R + (5 if new else 1), 3 if new else 1)
            label = small.render(c.names[n] + ("  grown" if new else ""), True, LIGHT)
            screen.blit(label, (p[0] - label.get_width() // 2, p[1] - R - 16))
        self.contacts(screen, rect, life, small, pos, R, inj, getattr(b, "T", None))
        screen.blit(font.render("block view (level 1): neurons, synapses, and the states they hold", True, MID),
                    (rect.x + 8, rect.y + 4))
        screen.blit(small.render(LEGEND, True, MID), (rect.x + 8, rect.bottom - 16))

    def contacts(self, screen, rect, life, small, pos, R, inj, T):
        """The body's contacts at the edges: the eyes (lit while their colour is seen), the thrusters (lit when they
        fire), the taste (+ or - when a meal is tasted), wired to T if it is drawn."""
        import pygame
        b, c = self.brain, self.brain.circuit
        X = lambda p: (int(rect.x + p[0] * rect.w), int(rect.y + p[1] * rect.h))
        names = {}
        for colour, k in life.sensor.items():
            names[b.sensors[k]] = f"{colour} eye"
        for thruster, k in life.motor.items():
            names[b.motors[k]] = f"{thruster} thruster"
        stim = inj if inj is not None else np.zeros(len(c.V))
        for s in b.sensors:
            p = X(pos[s])
            box = pygame.Rect(rect.x + 4, p[1] - 10, 62, 20)
            on = stim[s] > 0
            pygame.draw.rect(screen, WHITE if on else DARK, box, 0 if on else 1)
            screen.blit(small.render(names.get(s, ""), True, INK if on else LIGHT), (box.x + 4, box.y + 3))
            pygame.draw.line(screen, MID, (box.right, p[1]), (p[0] - R, p[1]), 1)
        for m in b.motors:
            p = X(pos[m])
            box = pygame.Rect(rect.right - 92, p[1] - 10, 88, 20)
            on = life.t - self.last_spike.get(m, -10 ** 9) < SPIKE_FLASH
            pygame.draw.rect(screen, WHITE if on else DARK, box, 0 if on else 1)
            screen.blit(small.render(names.get(m, ""), True, INK if on else LIGHT), (box.x + 4, box.y + 3))
            pygame.draw.line(screen, MID, (p[0] + R, p[1]), (box.x, p[1]), 1)
        tp = X(pos[T]) if T in pos else X((0.5, 0.86))
        box = pygame.Rect(tp[0] - 150, tp[1] - 10, 70, 20)
        recent = life.t - self.last_taste[0] < TASTE_SHOW
        mark = ("taste +" if self.last_taste[1] > 0 else "taste -") if recent else "taste"
        pygame.draw.rect(screen, WHITE if recent else DARK, box, 0 if recent else 1)
        screen.blit(small.render(mark, True, INK if recent else LIGHT), (box.x + 4, box.y + 3))
        if T in pos:
            pygame.draw.line(screen, MID, (box.right, tp[1]), (tp[0] - R, tp[1]), 1)

    def meter(self, screen, small, at, n, k=0):
        """A node's level as a bar (0..1 of its range, or of -1..1 if it has none), labelled with its name."""
        import pygame
        c = self.brain.circuit
        lo, hi = c.node_arr[3][n], c.node_arr[4][n]
        lo, hi = (lo, hi) if np.isfinite(lo) and np.isfinite(hi) else (-1.5, 1.5)
        v = (c.V[n] - lo) / max(hi - lo, 1e-9)
        bar = pygame.Rect(at[0], at[1], 9, 28)
        pygame.draw.rect(screen, DARK, bar)
        fill = int(28 * min(max(v, 0.0), 1.0))
        pygame.draw.rect(screen, LIGHT, (bar.x, bar.bottom - fill, 9, fill))
        pygame.draw.rect(screen, MID, bar, 1)
        label = small.render(c.names[n], True, MID)              # labels alternate below and above, so they don't
        screen.blit(label, (at[0] + 5 - label.get_width() // 2, at[1] + 30 if k % 2 == 0 else at[1] - 14))  # collide


class NodeView(BlockView):
    """The node view, for a circuit with no neurons to find (the minimal search's): level 0, every node and element.
    A node is a circle (a memory node a square), its brightness its voltage between the rails, white when it spikes;
    an element is an arrow from the node it reads to the node it feeds, solid if it excites and dashed if it
    inhibits, as thick as its recent current, with a dotted line from the node that gates it; an element on its own
    node is a loop, marked + or -. The body's contacts as in the block view."""

    def layout(self):
        b, n = self.brain, len(self.brain.circuit.names)
        pos = {}
        for i, s in enumerate(b.sensors):
            pos[s] = (0.16, 0.22 + 0.42 * i)
        for i, m in enumerate(b.motors):
            pos.setdefault(m, (0.84, 0.22 + 0.42 * i))
        pos.setdefault(b.taste_node, (0.34, 0.84))
        rest = [k for k in range(n) if k not in pos]
        for i, k in enumerate(rest):
            pos[k] = (0.52 + 0.12 * (i // 2), 0.43 + 0.3 * (i % 2))
        return pos

    def draw(self, screen, rect, life, font, small):
        import pygame
        b, c = self.brain, self.brain.circuit
        pygame.draw.rect(screen, (18, 18, 18), rect)
        if c.V is None:
            return
        pos = self.layout()
        X = lambda p: np.array((rect.x + p[0] * rect.w, rect.y + p[1] * rect.h))
        spikes = b.history[-1][1] if b.history else np.zeros(len(c.V), dtype=int)
        for n in range(len(c.V)):
            if n < len(spikes) and spikes[n] > 0:
                self.last_spike[n] = life.t
        inj = getattr(b, "last_inject", None)
        if inj is not None and inj[b.taste_node] != 0:
            self.last_taste = (life.t, float(np.sign(inj[b.taste_node])))
        R = max(10, rect.h // 18)
        gain, offset, slope, _, sig = c.el_arr
        loops = {}
        for e, (_, (t, f, g)) in enumerate(c.elements):
            x = slope[e] * (c.Vx[e] - offset[e])
            out = 1.0 / (1.0 + np.exp(-x)) if sig[e] > 0.5 else np.tanh(x)
            if g >= 0:
                out *= min(max(c.V[g], 0.0), 1.0)
            self.current[e] = SMOOTH * self.current.get(e, 0.0) + (1 - SMOOTH) * abs(gain[e] * out) / I_TYP   # nA
            width = 1 + int(6 * min(self.current[e] / 3, 1.0))
            colour = LIGHT if self.current[e] > 0.05 else MID
            if t == f:                                  # its own node: a loop above it, marked + or -
                k = loops.get(t, 0)
                loops[t] = k + 1
                centre = X(pos[t]) + np.array((-R + 2 * R * k, -R * 1.6))
                pygame.draw.circle(screen, colour, centre.astype(int), int(R * 0.7), width)
                mark = small.render("+" if gain[e] >= 0 else "-", True, LIGHT)
                screen.blit(mark, (centre[0] - 3, centre[1] - R * 0.7 - 14))
                continue
            a, z = X(pos[f]), X(pos[t])
            d = z - a
            L = max(np.linalg.norm(d), 1.0)
            d /= L
            a2, z2 = a + d * (R + 2), z - d * (R + 4)
            if gain[e] >= 0:
                pygame.draw.line(screen, colour, a2, z2, width)
                side = np.array([-d[1], d[0]]) * 6
                pygame.draw.polygon(screen, colour, [z2, z2 - d * 10 + side, z2 - d * 10 - side])
            else:
                span = np.linalg.norm(z2 - a2)
                for k in range(0, int(span), 12):
                    pygame.draw.line(screen, colour, a2 + d * k, a2 + d * min(k + 6, span), width)
                bar = np.array([-d[1], d[0]]) * 8
                pygame.draw.line(screen, colour, z2 - bar, z2 + bar, 3)
            if g >= 0:                                  # the gate: dotted, from its node to the arrow's middle
                gm, mid = X(pos[g]), (a2 + z2) / 2
                dg = mid - gm
                Lg = max(np.linalg.norm(dg), 1.0)
                dg /= Lg
                for k in range(int(R), int(Lg), 7):
                    pygame.draw.circle(screen, MID, (gm + dg * k).astype(int), 1)
                pygame.draw.circle(screen, MID, mid.astype(int), 3)
        for n in range(len(c.V)):
            p = X(pos[n]).astype(int)
            flash = life.t - self.last_spike.get(n, -10 ** 9) < SPIKE_FLASH
            fill = WHITE if flash else shade((c.V[n] + 3.0) / 6.0)
            if c.node_arr[5][n] > 0.5:                  # a memory: a square
                box = pygame.Rect(p[0] - R, p[1] - R, 2 * R, 2 * R)
                pygame.draw.rect(screen, fill, box)
                pygame.draw.rect(screen, WHITE, box, 1)
            else:
                pygame.draw.circle(screen, fill, p, R)
                pygame.draw.circle(screen, WHITE, p, R, 1)
            label = small.render(c.names[n], True, LIGHT)
            screen.blit(label, (p[0] + R + 4, p[1] + R - 6))
        self.contacts(screen, rect, life, small, {k: tuple(v) for k, v in pos.items()}, R, inj, b.taste_node)
        screen.blit(font.render("node view (level 0): every node and element", True, MID), (rect.x + 8, rect.y + 4))
        screen.blit(small.render("circle node, square memory, brightness = voltage, white = spike  |  arrows: solid "
                                 "excites, dashed inhibits, thick = current, dotted = gate, loop = own feedback",
                                 True, MID), (rect.x + 8, rect.bottom - 16))
