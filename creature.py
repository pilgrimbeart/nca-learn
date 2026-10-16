"""A new-born creature whose brain builds itself, then learns which colour is food. The body, the world and the views;
everything the brain's cells are and do is in rules/brain.py (on rules/wiring.py, on rules/organs.py), run by sheet.py,
where each cell sees only its own numbers and the mean of each shared number over its neighbours.

    python creature.py                  # watch a life (r: new life, d: damage the brain at the mouse, space: pause,
                                        # up/down: speed, Esc: quit)
    python creature.py --measure 16     # 16 lives with learning and 16 without: how soon it learns, what it eats
    python test_rules.py                # every rule keeps the golden rules
    python creature.py --record frames  # save a life's frames, headless, as PNGs (for a GIF)

The brain names two sensors (S1, S2) and two actuators (M1, M2), alike in all but name; nothing in a cell knows what
they are for. The body gives them their meaning, by a wiring it draws at random each life: one sensor sees red, the
other blue; one actuator's pulses fire the thruster at the tail's left corner, the other's the one at its right. It
touches the brain only at cells by the names they took, cell by cell: it stimulates a sensor when its colour is seen,
gives that sensor the reward when a block of its colour touches the mouth, and fires a thruster for each pulse
arriving at its actuator. Nothing else goes in or out, and the body keeps nothing of the brain's.

The body: a square. Both thrusters push it forward; one alone also turns it, away from its own side, so the creature
veers; both at once drive it straight ahead. Its eyes at the head look along parallel rays across the corridor its
mouth will sweep, up to RANGE; each ray stops at the first block it meets, so a near block hides what is behind it. A
block counts less the farther off it is, and each eye sees only its own colour. A block the head moves into is
eaten, and its colour's sensor gets the reward at once: +1, or -1 if it was poison. The world: a torus
of red and blue blocks; an eaten block reappears elsewhere.
"""

from __future__ import annotations

import argparse
import math
import time

import numpy as np

import sheet
from rules import brain, wiring

SIZE = 49           # the brain: SIZE x SIZE cells
UPDATE = 0.9        # the chance a brain cell updates in a tick (never all at once)
BODY = 4.0          # the body's side, in world units
WORLD = 60.0        # the world's side (a torus)
BLOCKS = 18         # blocks of each colour
EAT = 1.0           # a block this near the front edge (the mouth: the whole head end) is eaten
SENSE = 0.21        # stimuli per tick to a sensor that sees its colour at full strength
REACH = 5.0         # a block this far off counts half as much as one at the eyes
RANGE = 15.0        # how far the eyes see
RAYS = 25           # the eyes' rays, side by side across the corridor ahead: each stops at the first block it meets
BLOCK = 1.0         # a block's radius (what it hides behind it)
PUSH = 0.5          # a thruster firing adds this much forward speed ...
TURN = 0.08         # ... and this much turning speed, away from its side (radians per tick): both at once go straight
DRAG = 0.2          # speed and turning fade at this rate
DAMAGE = 7          # watching: the radius of the disc of cells d replaces with new-born ones
BAND = 4            # watching: the faint checkerboard's squares, in cells
FAST, SLOW = 10, 1  # watching: ticks per frame, slow while the paths grow and pulses first run down them
SETTLE = 200        # watching: ticks after the creature starts moving before speeding up again
COLOURS = ("red", "blue")
THRUSTERS = ("left", "right")                           # at the tail's two corners, both pushing forward
NAME = {"S1": 1, "S2": 2, "M1": 3, "M2": 4}             # the names cells give themselves


class Body:
    """Where the creature is and how it moves; the world's blocks."""

    def __init__(self, rng):
        self.rng = rng
        self.pos = np.array([WORLD / 2, WORLD / 2])
        self.heading = rng.uniform(0, 2 * math.pi)
        self.speed, self.spin = np.zeros(2), 0.0
        self.blocks = [[*self.somewhere(), c] for c in COLOURS for _ in range(BLOCKS)]

    def somewhere(self):
        while True:
            p = self.rng.uniform(0, WORLD, 2)
            if np.linalg.norm(self.wrap(p - self.pos)) > 3 * EAT + BODY:
                return p

    @staticmethod
    def wrap(d):
        return (d + WORLD / 2) % WORLD - WORLD / 2

    def forward(self):
        return np.array([math.cos(self.heading), math.sin(self.heading)])

    def head(self):
        return self.pos + self.forward() * BODY / 2

    def look(self) -> tuple:
        """The eyes' rays, parallel, across the corridor its mouth will sweep: for each, its offset across, how far it
        goes (to the first block it meets, or RANGE), and that block's colour (or None)."""
        f, h = self.forward(), self.head()
        side, w = np.array([f[1], -f[0]]), BODY / 2 + EAT / 2
        across = -w + (np.arange(RAYS) + 0.5) * 2 * w / RAYS
        far, colour = np.full(RAYS, RANGE), [None] * RAYS
        for x, y, c in self.blocks:
            d = self.wrap(np.array([x, y]) - h)
            ahead, off = d @ f, d @ side
            if ahead <= -BLOCK or ahead - BLOCK >= RANGE or abs(off) >= w + BLOCK:
                continue
            gap = BLOCK ** 2 - (across - off) ** 2
            for k in np.nonzero(gap > 0)[0]:
                hit = max(0.0, ahead - np.sqrt(gap[k]))
                if hit < far[k]:
                    far[k], colour[k] = hit, c
        return across, far, colour

    def sees(self) -> dict:
        """How strongly each colour is seen, at most 1: a block wholly in view counts 1 / (1 + (distance / REACH)^2),
        less if part of it is hidden or out of the corridor."""
        _, far, colour = self.look()
        share = (2 * (BODY / 2 + EAT / 2) / RAYS) / (2 * BLOCK)     # one ray's share of a block's width
        seen = {c: 0.0 for c in COLOURS}
        for d, c in zip(far, colour):
            if c is not None:
                seen[c] += share / (1 + (d / REACH) ** 2)
        return {c: min(1.0, v) for c, v in seen.items()}

    def fire(self, thruster: str) -> None:
        self.speed += PUSH * self.forward()
        self.spin += TURN if thruster == "right" else -TURN    # the left one turns it right, and the right one left

    def move(self) -> list:
        """Moves on a tick; returns the colours of blocks eaten (each reappears elsewhere)."""
        self.pos = (self.pos + self.speed) % WORLD
        self.heading += self.spin
        self.speed *= math.exp(-DRAG)
        self.spin *= math.exp(-DRAG)
        eaten, f = [], self.forward()
        if self.speed @ f <= 0:                             # it only eats what it moves forward into
            return eaten
        for b in self.blocks:
            d = self.wrap(np.array(b[:2]) - self.pos)
            if 0 < d @ f < BODY / 2 + EAT and abs(d @ np.array([f[1], -f[0]])) < BODY / 2 + EAT / 2:
                eaten.append(b[2])
                b[0], b[1] = self.somewhere()
        return eaten


class Life:
    """A brain and a body in a world. step() runs one tick."""

    def __init__(self, seed: int = 0, poison: str = "red", learning: bool = True):
        self.rng = np.random.default_rng(seed)
        self.poison, self.learning = poison, learning
        self.brain = sheet.Sheet(brain, SIZE, seed, update=UPDATE)
        self.body = Body(self.rng)
        s, m = ("S1", "S2")[:: self.rng.choice((1, -1))], ("M1", "M2")[:: self.rng.choice((1, -1))]
        self.organ = dict(zip(COLOURS + THRUSTERS, s + m))  # the body's wiring: colour -> sensor, thruster -> actuator
        self.t = 0
        self.meals, self.firings = [], []                   # (tick, colour), (tick, "left" or "right")
        self.yuck = -1e9                                    # when poison was last eaten
        self.moving = None                                  # when the first pulse reached a thruster

    def named(self, organ: str) -> np.ndarray:
        """The cells named as this organ (a cell's own name, or what the body wired to a colour or thruster)."""
        return self.brain.cells("name", NAME[self.organ.get(organ, organ)])

    def step(self) -> None:
        for c, seen in self.body.sees().items():            # sensors fire at what they see
            if self.rng.random() < SENSE * seen:
                self.brain.give(self.named(c), "stimulus")
        self.brain.step(1)
        fired = [f for f in THRUSTERS
                 for _ in range(int(self.brain.take(self.named(f), f"fired_{self.organ[f][1]}").sum()))]
        if fired and self.moving is None:
            self.moving = self.t
        for f in fired:
            self.body.fire(f)
            self.firings.append((self.t, f))
        for c in self.body.move():                          # a meal: its colour's sensor gets the reward
            self.meals.append((self.t, c))
            if self.learning:
                self.brain.give(self.named(c), "reward", -1.0 if c == self.poison else 1.0)
            if c == self.poison:
                self.yuck = self.t
        self.t += 1

    def drive(self, colour: str) -> float:
        """The chance that this colour's sensor fires both thrusters (watching only)."""
        p = self.brain.get(self.named(colour), "p")
        return min(max(float(p.mean()) / brain.STEPS, 0.0), 1.0) if p.size else 0.5


LEARNED = 0.2       # measuring: a sensor has learned once its chance of firing both is this near right


def one_life(job):
    """(seed, poison, learning, ticks) -> per third of life after moving began, (poison eaten, food eaten, ticks);
    each sensor's chance of firing both at the end; and how many ticks after moving began both sensors had learned
    (None: not in this life)."""
    seed, poison, learning, ticks = job
    food = "blue" if poison == "red" else "red"
    life, learned = Life(seed, poison, learning), None
    while life.t < ticks:
        life.step()
        if learned is None and life.moving is not None and life.t % 50 == 0:
            if life.drive(poison) <= LEARNED and life.drive(food) >= 1 - LEARNED:
                learned = life.t - life.moving
    start = life.moving or ticks
    out = []
    for i in range(3):
        a, b = start + i * (ticks - start) / 3, start + (i + 1) * (ticks - start) / 3
        part = [c for m, c in life.meals if a <= m < b]
        out.append((sum(c == poison for c in part), sum(c != poison for c in part), b - a))
    return out, life.drive(poison), life.drive(food), learned


def measure(lives: int, ticks: int = 8000) -> None:
    """Half the lives with red as poison, half blue; with learning and without. Two scores, both per unit of time:
    how soon the sensors learn (the rules), and food minus poison eaten per 1,000 ticks (the sheet and the body)."""
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    for learning in (True, False):
        jobs = [(i // 2, COLOURS[i % 2], learning, ticks) for i in range(lives)]
        with ProcessPoolExecutor(mp_context=multiprocessing.get_context("spawn")) as pool:
            results = list(pool.map(one_life, jobs))
        thirds = [[sum(r[0][i][k] for r in results) for k in range(3)] for i in range(3)]
        net = "  ".join(f"{1000 * (f - p) / max(1, t):+5.2f}" for p, f, t in thirds)
        share = "  ".join(f"{100 * p / max(1, p + f):3.0f}%" for p, f, _ in thirds)
        done = sorted(r[3] for r in results if r[3] is not None)
        when = (f"{len(done)} of {len(results)} lives, median {done[len(done) // 2]} ticks after moving"
                if done else f"0 of {len(results)} lives")
        print(f"learning {'on ' if learning else 'off'}: net food per 1,000 ticks in each third of life: {net}"
              f" (poison's share {share});  learned in {when};  firing both at the end: poison"
              f" {np.mean([r[1] for r in results]):.2f}, food {np.mean([r[2] for r in results]):.2f}")


def watch(seed: int = 0, record: str | None = None, until: int = 8000) -> None:
    """A life, live. Left, the brain, in greys: the cells' coordinates (x and y, each running -1 to 1 across the
    sheet) as a faint checkerboard; paths to M1 light grey and to M2 mid grey, pulses white, organs labelled beside
    their cells with their own names and, after them, what the body wired them to (the sensors with their chance of
    firing both thrusters). Right, the world: blocks lettered R (dark) and B (light), the creature a square with its
    head marked, and what its eyes see.
    It runs FAST ticks a frame, but SLOW while the paths grow and until a little after the creature starts moving, so
    the pulses can be seen; up and down take over the speed. With record, no window: every frame is saved there as a
    PNG, until the given tick."""
    import os
    if record:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.makedirs(record, exist_ok=True)
    import pygame
    pygame.init()
    scale = max(1, 490 // SIZE)
    side, wpx = SIZE * scale, 490
    screen = pygame.display.set_mode((side + 12 + wpx, max(side, wpx) + 72))
    pygame.display.set_caption("a brain builds itself, then learns which colour is food")
    font, small = pygame.font.SysFont(None, 22), pygame.font.SysFont(None, 18)
    per_frame, auto, paused, clock = FAST, True, False, pygame.time.Clock()   # auto: speed set by the stage
    poison = COLOURS[seed % 2]
    life = Life(seed, poison)
    to_px = lambda p: (side + 12 + int(p[0] / WORLD * wpx), int((WORLD - p[1]) / WORLD * wpx))
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_UP:
                    per_frame, auto = per_frame * 2, False
                elif event.key == pygame.K_DOWN:
                    per_frame, auto = max(1, per_frame // 2), False
                elif event.key == pygame.K_r:
                    seed += 1
                    poison = COLOURS[seed % 2]
                    life = Life(seed, poison)
                    auto = True
                elif event.key == pygame.K_d:                       # damage: new-born cells in a disc at the mouse
                    mx, my = pygame.mouse.get_pos()
                    if not (0 <= mx < side and 0 <= my < side):
                        mx, my = side // 2, side // 2
                    rows, cols = np.mgrid[0:SIZE, 0:SIZE]
                    life.brain.damage((rows - my / scale) ** 2 + (cols - mx / scale) ** 2 < DAMAGE ** 2)
        named = set(np.unique(np.round(life.brain.view("name"))).astype(int)) - {0}
        growing = len(named) == 4 and (life.moving is None or life.t - life.moving < SETTLE)
        if auto:
            per_frame = SLOW if growing else FAST
        if not paused:
            started = time.time()
            for i in range(per_frame):
                life.step()
                if not record and time.time() - started > 0.2:
                    break
        screen.fill((0, 0, 0))
        view = life.brain.view
        cols = np.floor((view("x") + 1) / 2 * (SIZE - 1) / BAND + 0.5)     # the cells' coordinates, in bands of cells
        rows = np.floor((view("y") + 1) / 2 * (SIZE - 1) / BAND + 0.5)
        shade = 0.06 + 0.08 * ((cols + rows) % 2)
        names = np.round(view("name"))
        for c, level in (("2", 0.45), ("1", 0.75)):
            on = view(f"on_{c}") > 0.5
            shade = np.where(on, np.maximum(shade, level), shade)
            shade = np.where(on & (np.round(view(f"timer_{c}")) > wiring.REST), 1.0, shade)
        rgb = np.stack([shade] * 3, axis=-1)
        rgb = (255 * rgb).astype(np.uint8).transpose(1, 0, 2).repeat(scale, 0).repeat(scale, 1)
        screen.blit(pygame.surfarray.make_surface(rgb), (0, 0))
        yuck = life.t - life.yuck < 60
        for k in np.unique(names[names > 0]):
            cells = np.argwhere(names == k)
            own = next(n for n, v in NAME.items() if v == k)
            role = next(o for o, n in life.organ.items() if n == own)        # what the body wired it to
            for r, c in cells:
                label_text = f"{own} {role}" + (f" {life.drive(role):.2f}" if role in COLOURS else "")
                lit = yuck and role == poison
                label = font.render(label_text, True, (0, 0, 0) if lit else (255, 255, 255),
                                    (255, 255, 255) if lit else (60, 60, 60))
                w, h = label.get_size()                                 # beside the cell, inside the sheet
                px = c * scale + scale + 3 if c == 0 else c * scale - w - 3 if c == SIZE - 1 else c * scale - w // 2
                py = r * scale + scale + 3 if r == 0 else r * scale - h - 3 if r == SIZE - 1 else r * scale - h // 2
                if k % 2 == 0 and r in (0, SIZE - 1):              # the pair sit close on one edge: stagger them
                    py += h if r == 0 else -h
                screen.blit(label, (min(max(0, px), side - w), min(max(0, py), side - h)))
        pygame.draw.rect(screen, (25, 25, 25), (side + 12, 0, wpx, wpx))
        body = life.body
        f, h, half = body.forward(), body.head(), BODY / 2
        r = np.array([f[1], -f[0]])                                 # the creature's right
        beam = pygame.Surface((wpx, wpx), pygame.SRCALPHA)
        across, far, _ = body.look()
        half_ray = (BODY / 2 + EAT / 2) / RAYS          # what the eyes see: each ray, fading as a block there would
        for o, length in zip(across, far):              # count less, up to the first block it meets
            for k in range(int(np.ceil(length))):
                a, b = h + k * f + o * r, h + min(k + 1, length) * f + o * r
                alpha = int(90 / (1 + ((k + 0.5) / REACH) ** 2))
                for ox in (-WORLD, 0, WORLD):                   # the world is a torus: draw the wrapped copies too
                    for oy in (-WORLD, 0, WORLD):
                        q = np.array([ox, oy])
                        pts = [to_px(p + q + s * half_ray * r) for p, s in ((a, 1), (b, 1), (b, -1), (a, -1))]
                        pygame.draw.polygon(beam, (255, 255, 255, alpha), [(x - side - 12, y) for x, y in pts])
        screen.blit(beam, (side + 12, 0))
        for x, y, c in body.blocks:
            px = to_px((x, y))
            pygame.draw.rect(screen, (90, 90, 90) if c == "red" else (210, 210, 210), (px[0] - 8, px[1] - 8, 16, 16))
            screen.blit(small.render(c[0].upper(), True, (255, 255, 255) if c == "red" else (0, 0, 0)), (px[0] - 4, px[1] - 6))
        corners = [body.pos + half * (f + r), body.pos + half * (f - r), body.pos + half * (-f - r), body.pos + half * (-f + r)]
        pygame.draw.polygon(screen, (255, 255, 255) if yuck else (160, 160, 160), [to_px(p) for p in corners], 5 if yuck else 2)
        pygame.draw.circle(screen, (255, 255, 255), to_px(body.head()), 4)
        recent = {k for when, k in life.firings[-4:] if life.t - when < 6}
        for k, sign in (("left", -1), ("right", 1)):              # a ring at the corner of a thruster firing
            if k in recent:
                pygame.draw.circle(screen, (255, 255, 255), to_px(body.pos - half * f + sign * half * r), 6, 2)
        if yuck:
            px = to_px(body.pos)
            screen.blit(font.render("yuck!", True, (0, 0, 0), (255, 255, 255)), (px[0] + 14, px[1] - 28))
        stage = ("where am I" if len(named) < 4 else "wiring" if life.moving is None else "moving and learning")
        eaten = {c: sum(1 for _, m in life.meals if m == c) for c in COLOURS}
        base = max(side, wpx)
        lines = (f"tick {life.t:6d}   stage: {stage}   poison: {poison}   eaten: red {eaten['red']}, blue {eaten['blue']}",
                 "recent meals: " + " ".join(m[0].upper() for _, m in life.meals[-14:]),
                 f"{per_frame} ticks per frame   r new life   d damage (at the mouse)   space pause   up/down{'' if auto else ' (r: auto)'}   Esc")
        for i, line in enumerate(lines):
            screen.blit(font.render(line, True, (255, 255, 255)), (6, base + 6 + 22 * i))
        pygame.display.flip()
        if record:
            pygame.image.save(screen, os.path.join(record, f"{life.t:06d}.png"))
            if life.t >= until:
                pygame.quit()
                return
            continue
        clock.tick(30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--measure", type=int, metavar="LIVES", help="measure over this many lives (headless)")
    parser.add_argument("--ticks", type=int, default=8000, help="ticks per life when measuring or recording")
    parser.add_argument("--record", metavar="DIR", help="save a life's frames to DIR as PNGs, headless")
    args = parser.parse_args()
    if args.measure:
        measure(args.measure, args.ticks)
    else:
        watch(args.seed, args.record, args.ticks)
