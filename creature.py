"""A new-born creature that learns which colour is food: a body in a world (world.py), and a brain (brains/). Life
joins them; measure compares brains on the same lives; watch shows a life.

    python creature.py                  # watch a life with the sheet brain (r: new life, d: damage the brain at the
                                        # mouse, b: the next brain, s: the designed circuit's schematic, space: pause,
                                        # up/down: speed, Esc: quit)
    python creature.py --measure 16     # 16 lives with learning and 16 without, for each brain: how soon it learns,
                                        # what it eats (--all-food: lives where both colours are food)
    python test_rules.py                # every rule keeps the golden rules
    python creature.py --record frames  # save a life's frames, headless, as PNGs (for a GIF)

A brain has two sensors and two motors, numbered 0 and 1, alike in all but number; it doesn't know what they are for.
The body gives them their meaning, by a wiring it draws at random each life: one sensor sees red, the other blue; one
motor fires the thruster at the tail's left corner, the other the one at its right. It stimulates a sensor when its
colour is seen, and fires a thruster for each time its motor fires. Its one other input is taste: a pulse, +1 for food
and -1 for poison, as soon as a block touches the mouth (otherwise nothing). Taste doesn't say which sensor saw the
block: the brain must work out what earned it. Nothing else goes in or out.

Brains: the sheet brain ("sheet", brains/sheet.py), a sheet of identical cells that builds itself, then learns; and
the circuit brains: "designed-circuit" (brains/designed.py), a small circuit of excitable neurons designed by hand;
"minimal-circuit" (brains/minimal.py), its neurons alone, driving at every block, with taste going nowhere (the
baseline for recruitment, RECRUITMENT.md); "adjusting-circuit" (brains/adjusting.py), each neuron adjusting its own
excitability from taste (rung 0); "knowing-circuit" (brains/knowing.py), the minimal circuit plus a taste neuron that
learns what predicts pain but has no outputs (recruitment's starting animal); "recruiting-circuit"
(brains/recruiting.py), the knowing circuit growing, in its life, the link that lets that knowledge act (rung 1);
"healing-circuit" (brains/healing.py), the same done by a generic recruit that knows nothing of the circuit, choosing
among actions on what it is attached to; "healing-cascade", where the first recruit can't help and the cure is
found by a second wave, one edge further.

In an all-food world (poison None) both colours are food, so there is nothing to learn: the control for recruitment,
which should then not happen.
"""

from __future__ import annotations

import argparse
import functools
import time

import numpy as np

from brains.adjusting import AdjustingBrain
from brains.sheet import SheetBrain
from brains.knowing import KnowingBrain
from brains.minimal import MinimalBrain
from brains.healing import HealingBrain
from brains.recruiting import RecruitingBrain
from brains.designed import DesignedBrain
from world import COLOURS, SENSE, THRUSTERS, WORLD, Body

BRAINS = {"sheet": SheetBrain, "designed-circuit": DesignedBrain, "minimal-circuit": MinimalBrain,
          "adjusting-circuit": AdjustingBrain, "knowing-circuit": KnowingBrain, "recruiting-circuit": RecruitingBrain,
          "healing-circuit": functools.partial(HealingBrain, listen="all", sign="inh", judge="share", tire=0.05),
          "healing-cascade": functools.partial(HealingBrain, menu="inputs", listen="all", sign="inh", cascade=True,
                                               trigger="root", judge="share", tire=0.05, starve=20000.0)}
FAST, SLOW = 10, 1  # watching: ticks per frame, slow while the brain wires itself and first drives the body
SLOWEST = 1 / 32    # watching: down halves the speed to this, a tick every 32 frames (about 1 a second)
SCHEMATIC = "media/designed_circuit.png"    # watching: the designed circuit (drawn by schematic.py)
SETTLE = 200        # watching: ticks after the creature starts moving before speeding up again
BLOCKS = 300        # watching: the height of the block view below (blocks.py)
LEARNED = 0.2       # measuring: a sensor has learned once its chance of firing both is this near right


class Life:
    """A body and a brain in a world. step() runs one tick. poison: the poison colour, or None (all food). brain: a
    name in BRAINS, or (for experiments) a function from the seed to a brain."""

    def __init__(self, seed: int = 0, poison: str | None = "red", learning: bool = True, brain: str = "sheet"):
        self.rng = np.random.default_rng(seed)                  # the world's: the same for every brain
        self.poison, self.learning = poison, learning
        self.brain = BRAINS[brain](seed) if isinstance(brain, str) else brain(seed)
        self.body = Body(self.rng)
        s, m = (0, 1)[:: self.rng.choice((1, -1))], (0, 1)[:: self.rng.choice((1, -1))]
        self.sensor = dict(zip(COLOURS, s))                     # the body's wiring: colour -> sensor,
        self.motor = dict(zip(THRUSTERS, m))                    # thruster -> motor
        self.t = 0
        self.meals, self.firings = [], []                       # (tick, colour), (tick, "left" or "right")
        self.yuck = -1e9                                        # when poison was last eaten
        self.moving = None                                      # when a thruster first fired

    def step(self) -> None:
        for c, seen in self.body.sees().items():                # each eye fires at random moments (Poisson), at
            for _ in range(self.rng.poisson(SENSE * seen)):     # a rate set by what it sees
                self.brain.stimulate(self.sensor[c], self.rng.random())
        motors = self.brain.step()
        fired = [f for f in THRUSTERS for _ in range(motors.count(self.motor[f]))]
        if fired and self.moving is None:
            self.moving = self.t
        for f in fired:
            self.body.fire(f)
            self.firings.append((self.t, f))
        taste = 0.0
        for c in self.body.move():                              # a meal: taste, good or bad
            self.meals.append((self.t, c))
            taste += -1.0 if c == self.poison else 1.0
            if c == self.poison:
                self.yuck = self.t
        if taste != 0.0:
            at = self.rng.random()                              # (drawn with learning off too: the same lives)
            if self.learning:                                   # one pulse, however many meals at once, at a moment
                self.brain.taste(min(max(taste, -1.0), 1.0), at)   # within the next tick
        self.t += 1

    def drive(self, colour: str) -> float:
        """Watching and measuring: the chance that this colour's sensor fires both motors."""
        return self.brain.drive(self.sensor[colour])


def one_life(job):
    """(brain, seed, poison, learning, ticks) -> per third of life after moving began, (poison eaten, food eaten,
    ticks); each sensor's chance of firing both at the end (poison's, food's; in an all-food life, red's, blue's); and
    how many ticks after moving began both sensors had learned (None: not in this life, or nothing to learn)."""
    brain, seed, poison, learning, ticks = job
    food = "blue" if poison == "red" else "red"
    life, learned = Life(seed, poison, learning, brain), None
    while life.t < ticks:
        life.step()
        if poison and learned is None and life.moving is not None and life.t % 50 == 0:
            if life.drive(poison) <= LEARNED and life.drive(food) >= 1 - LEARNED:
                learned = life.t - life.moving
    start = life.moving if life.moving is not None else ticks
    out = []
    for i in range(3):
        a, b = start + i * (ticks - start) / 3, start + (i + 1) * (ticks - start) / 3
        part = [c for m, c in life.meals if a <= m < b]
        out.append((sum(c == poison for c in part), sum(c != poison for c in part), b - a))
    return out, life.drive(poison or "red"), life.drive(food), learned


def measure(lives: int, ticks: int = 10000, brains=tuple(BRAINS), all_food: bool = False) -> None:
    """Each brain on the same lives (the same worlds and wirings): half with red as poison, half blue; with learning
    and without. Three scores: how soon the sensors learn, food minus poison eaten per 1,000 ticks, and food eaten
    for each poison. all_food: lives where both colours are food instead (food eaten per 1,000 ticks)."""
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    for brain in brains:
        for learning in ((True,) if all_food else (True, False)):
            jobs = [(brain, i // 2, None if all_food else COLOURS[i % 2], learning, ticks) for i in range(lives)]
            with ProcessPoolExecutor(mp_context=multiprocessing.get_context("spawn")) as pool:
                results = list(pool.map(one_life, jobs))
            thirds = [[sum(r[0][i][k] for r in results) for k in range(3)] for i in range(3)]
            if all_food:
                eaten = "  ".join(f"{1000 * f / max(1, t):5.2f}" for _, f, t in thirds)
                print(f"{brain}, all food: food per 1,000 ticks in each third of life: {eaten};  firing both at the"
                      f" end: red {np.mean([r[1] for r in results]):.2f}, blue {np.mean([r[2] for r in results]):.2f}")
                continue
            net = "  ".join(f"{1000 * (f - p) / max(1, t):+5.2f}" for p, f, t in thirds)
            ratio = "  ".join(f"{f / p:4.1f}" if p else f"{f}:0" for p, f, _ in thirds)
            done = sorted(r[3] for r in results if r[3] is not None)
            when = (f"{len(done)} of {len(results)} lives, median {done[len(done) // 2]} ticks after moving"
                    if done else f"0 of {len(results)} lives")
            meals = 1000 * sum(p + f for p, f, _ in thirds) / max(1, sum(t for _, _, t in thirds))
            print(f"{brain}, learning {'on ' if learning else 'off'}: net food per 1,000 ticks in each third of life:"
                  f" {net} (food:poison {ratio});  meals per 1,000 ticks {meals:.2f};  learned in {when};"
                  f"  firing both at the end: poison"
                  f" {np.mean([r[1] for r in results]):.2f}, food {np.mean([r[2] for r in results]):.2f}")


def watch(seed: int = 0, brain: str = "sheet", record: str | None = None, until: int = 10000,
          all_food: bool = False) -> None:
    """A life, live. Left, the brain's own panel, in greys. Right, the world: blocks lettered R (dark) and B (light),
    the creature a triangle with its point marked, and what its eyes see. It runs FAST ticks a frame, but SLOW while the
    brain wires itself and until a little after the creature starts moving; up and down take over the speed (down, past
    a tick a frame, waits 2, 4 ... 32 frames between ticks, so single spikes can be followed). Buttons
    below: switch brain (a new world, the same seed), and with the designed circuit, its schematic (the life waits
    while it is open). With record, no window: every frame is saved there as a PNG, until the given tick. all_food:
    both colours are food."""
    import os
    import pathlib
    from world import EAT, RAYS, REACH
    if record:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.makedirs(record, exist_ok=True)
    import pygame
    pygame.init()
    side = wpx = 490
    base = max(side, wpx)
    from blocks import BlockView, NodeView
    screen = pygame.display.set_mode((side + 12 + wpx, base + 108 + BLOCKS))
    view = None                                                     # the block view of a circuit brain
    pygame.display.set_caption("a brain learns which colour is food")
    font, small = pygame.font.SysFont(None, 22), pygame.font.SysFont(None, 18)
    per_frame, auto, paused, clock = FAST, True, False, pygame.time.Clock()   # auto: speed set by the stage
    owed = 0.0                                                      # ticks owed, below a tick a frame
    poison = None if all_food else COLOURS[seed % 2]
    life = Life(seed, poison, brain=brain)
    to_px = lambda p: (side + 12 + int(p[0] / WORLD * wpx), int((WORLD - p[1]) / WORLD * wpx))
    viewer = None                                                   # the schematic, while it is open

    def speed():
        """The speed, as shown."""
        if per_frame >= 1:
            return f"{per_frame:g} tick{'s' if per_frame > 1 else ''} per frame"
        return f"{round(1 / per_frame)} frames per tick"

    def buttons():
        """The buttons below, as (key, label, rect)."""
        names = list(BRAINS)
        other = names[(names.index(brain) + 1) % len(names)]
        out, x = [], 6
        for key, label in (("b", f"brain: {brain}   switch to {other}  (b)"),) + \
                          ((("s", "schematic  (s)"),) if brain == "designed-circuit" else ()):
            w = font.size(label)[0] + 20
            out.append((key, label, pygame.Rect(x, base + 74, w, 28)))
            x += w + 10
        return out

    def press(key):
        nonlocal brain, life, auto, viewer
        if key == "b":                                              # another brain, in a new world
            names = list(BRAINS)
            brain = names[(names.index(brain) + 1) % len(names)]
            life, auto, viewer = Life(seed, poison, brain=brain), True, None
        elif key == "s" and brain == "designed-circuit":
            viewer = SchematicViewer(pygame, screen, pathlib.Path(__file__).parent / SCHEMATIC, font)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if viewer is not None:                                  # the schematic has the mouse and keys
                if not viewer.handle(event):
                    viewer = None
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for key, _, rect in buttons():
                    if rect.collidepoint(event.pos):
                        press(key)
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_b, pygame.K_s):
                press("b" if event.key == pygame.K_b else "s")
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_UP:
                    per_frame, auto = per_frame * 2, False
                elif event.key == pygame.K_DOWN:
                    per_frame, auto = per_frame // 2 if per_frame > 1 else max(SLOWEST, per_frame / 2), False
                elif event.key == pygame.K_r:
                    seed += 1
                    poison = None if all_food else COLOURS[seed % 2]
                    life = Life(seed, poison, brain=brain)
                    auto = True
                elif event.key == pygame.K_d and hasattr(life.brain, "damage_at"):    # damage, at the mouse
                    mx, my = pygame.mouse.get_pos()
                    inside = 0 <= mx < side and 0 <= my < side
                    life.brain.damage_at(mx / side if inside else 0.5, my / side if inside else 0.5)
        if auto:
            settling = life.moving is None or life.t - life.moving < SETTLE
            per_frame = SLOW if life.brain.built() and settling else FAST
        if viewer is not None:
            viewer.draw()
            pygame.display.flip()
            clock.tick(30)
            continue
        if not paused:
            started = time.time()
            owed += per_frame
            ticks = int(owed)
            owed -= ticks
            for i in range(ticks):
                life.step()
                if not record and time.time() - started > 0.2:
                    break
        screen.fill((0, 0, 0))
        yuck = life.t - life.yuck < 60
        sensors = [next(f"{c} {life.drive(c):.2f}" for c in COLOURS if life.sensor[c] == k) for k in (0, 1)]
        motors = [next(f for f in THRUSTERS if life.motor[f] == k) for k in (0, 1)]
        life.brain.draw(screen, side, font, sensors, motors, life.sensor[poison] if yuck else None)
        pygame.draw.rect(screen, (25, 25, 25), (side + 12, 0, wpx, wpx))
        body = life.body
        f, h = body.forward(), body.head()
        r = np.array([f[1], -f[0]])                                 # the creature's right
        beam = pygame.Surface((wpx, wpx), pygame.SRCALPHA)
        across, far, _ = body.look()
        half_ray = EAT / RAYS                           # what the eyes see: each ray, fading as a block there would
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
        for (x, y), k in zip(body.xy, body.kind):
            c = COLOURS[k]
            px = to_px((x, y))
            pygame.draw.rect(screen, (90, 90, 90) if c == "red" else (210, 210, 210), (px[0] - 8, px[1] - 8, 16, 16))
            screen.blit(small.render(c[0].upper(), True, (255, 255, 255) if c == "red" else (0, 0, 0)), (px[0] - 4, px[1] - 6))
        corners = body.corners()
        pygame.draw.polygon(screen, (255, 255, 255) if yuck else (160, 160, 160), [to_px(p) for p in corners], 5 if yuck else 2)
        pygame.draw.circle(screen, (255, 255, 255), to_px(body.head()), 4)
        recent = {k for when, k in life.firings[-4:] if life.t - when < 6}
        for k, corner in zip(("left", "right"), corners[1:]):   # a ring at the corner of a thruster firing
            if k in recent:
                pygame.draw.circle(screen, (255, 255, 255), to_px(corner), 6, 2)
        if yuck:
            px = to_px(body.pos)
            screen.blit(font.render("yuck!", True, (0, 0, 0), (255, 255, 255)), (px[0] + 14, px[1] - 28))
        stage = "moving and learning" if life.moving is not None else life.brain.stage()
        eaten = {c: sum(1 for _, m in life.meals if m == c) for c in COLOURS}
        lines = (f"tick {life.t:6d}   brain: {brain}   stage: {stage}   poison: {poison or 'none (all food)'}   eaten: red {eaten['red']},"
                 f" blue {eaten['blue']}",
                 "recent meals: " + " ".join(m[0].upper() for _, m in life.meals[-14:]),
                 f"{speed()}   r new life   d damage (at the mouse)   space pause   up/down{'' if auto else ' (r: auto)'}   Esc")
        for i, line in enumerate(lines):
            screen.blit(font.render(line, True, (255, 255, 255)), (6, base + 6 + 22 * i))
        hover = pygame.mouse.get_pos()
        for _, label, rect in buttons():
            pygame.draw.rect(screen, (90, 90, 90) if rect.collidepoint(hover) else (50, 50, 50), rect, border_radius=4)
            pygame.draw.rect(screen, (200, 200, 200), rect, 1, border_radius=4)
            screen.blit(font.render(label, True, (255, 255, 255)), (rect.x + 10, rect.y + 6))
        strip = pygame.Rect(0, base + 108, side + 12 + wpx, BLOCKS)     # below: the brain as blocks
        if hasattr(life.brain, "circuit"):
            if view is None or view.brain is not life.brain:
                view = (NodeView if getattr(life.brain, "level0", False) else BlockView)(life.brain)
            view.draw(screen, strip, life, font, small)
        else:
            pygame.draw.rect(screen, (18, 18, 18), strip)
            screen.blit(font.render("block view: for the circuit brains (b to switch)", True, (120, 120, 120)),
                        (8, base + 112))
        pygame.display.flip()
        if record:
            pygame.image.save(screen, os.path.join(record, f"{life.t:06d}.png"))
            if life.t >= until:
                pygame.quit()
                return
            continue
        clock.tick(30)


class SchematicViewer:
    """Watching: an image over the whole window. The wheel zooms at the mouse, dragging pans; Esc, or close, shuts it."""
    BAR = 30

    def __init__(self, pygame, screen, path, font):
        self.pg, self.screen, self.font = pygame, screen, font
        self.image = pygame.image.load(str(path)).convert()
        w, h = screen.get_size()
        iw, ih = self.image.get_size()
        self.fit = min(w / iw, (h - self.BAR) / ih)
        self.zoom, self.ox, self.oy = self.fit, 0.0, 0.0            # screen pixels per image pixel; image at top left
        self.drag = None
        self.close = pygame.Rect(w - 110, 2, 104, self.BAR - 4)
        self._clamp()

    def _clamp(self):
        w, h = self.screen.get_size()
        iw, ih = self.image.get_size()
        vw, vh = w / self.zoom, (h - self.BAR) / self.zoom          # the view, in image pixels
        self.ox = min(max(self.ox, 0.0), max(iw - vw, 0.0)) if vw < iw else (iw - vw) / 2
        self.oy = min(max(self.oy, 0.0), max(ih - vh, 0.0)) if vh < ih else (ih - vh) / 2

    def handle(self, event) -> bool:
        """Takes an event; False once it is closed."""
        pg = self.pg
        if event.type == pg.KEYDOWN and event.key in (pg.K_ESCAPE, pg.K_s):
            return False
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.close.collidepoint(event.pos):
                return False
            self.drag = (event.pos, self.ox, self.oy)
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.drag = None
        elif event.type == pg.MOUSEMOTION and self.drag:
            (x0, y0), ox, oy = self.drag
            self.ox, self.oy = ox - (event.pos[0] - x0) / self.zoom, oy - (event.pos[1] - y0) / self.zoom
            self._clamp()
        elif event.type == pg.MOUSEWHEEL:                           # zoom, keeping the point under the mouse still
            mx, my = pg.mouse.get_pos()
            my -= self.BAR
            ix, iy = self.ox + mx / self.zoom, self.oy + my / self.zoom
            self.zoom = min(max(self.zoom * 1.25 ** event.y, self.fit), 1.0)
            self.ox, self.oy = ix - mx / self.zoom, iy - my / self.zoom
            self._clamp()
        return True

    def draw(self) -> None:
        pg, screen = self.pg, self.screen
        w, h = screen.get_size()
        iw, ih = self.image.get_size()
        screen.fill((235, 235, 235))
        x0, y0 = max(int(self.ox), 0), max(int(self.oy), 0)        # the part of the image in view, scaled alone
        x1 = min(int(self.ox + w / self.zoom) + 1, iw)
        y1 = min(int(self.oy + (h - self.BAR) / self.zoom) + 1, ih)
        if x1 > x0 and y1 > y0:
            part = self.image.subsurface((x0, y0, x1 - x0, y1 - y0))
            size = (max(1, round((x1 - x0) * self.zoom)), max(1, round((y1 - y0) * self.zoom)))
            screen.blit(pg.transform.smoothscale(part, size),
                        (round((x0 - self.ox) * self.zoom), self.BAR + round((y0 - self.oy) * self.zoom)))
        pg.draw.rect(screen, (40, 40, 40), (0, 0, w, self.BAR))
        screen.blit(self.font.render("the designed circuit   wheel: zoom   drag: pan", True, (255, 255, 255)),
                    (8, 7))
        hover = self.close.collidepoint(pg.mouse.get_pos())
        pg.draw.rect(screen, (90, 90, 90) if hover else (60, 60, 60), self.close, border_radius=4)
        pg.draw.rect(screen, (200, 200, 200), self.close, 1, border_radius=4)
        screen.blit(self.font.render("close (Esc)", True, (255, 255, 255)), (self.close.x + 10, self.close.y + 5))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--brain", default="sheet", help="the brain to watch or record: one of BRAINS, or a --spec")
    parser.add_argument("--spec", nargs="+", default=[], metavar="RESULTS",
                        help="also offer these circuits of the minimal search (minimal/results/*.json), named by file")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--measure", type=int, metavar="LIVES", help="measure every brain over this many lives (headless)")
    parser.add_argument("--ticks", type=int, default=10000, help="ticks per life when measuring or recording")
    parser.add_argument("--record", metavar="DIR", help="save a life's frames to DIR as PNGs, headless")
    parser.add_argument("--brains", nargs="+", default=None,
                        help="the brains to measure")
    parser.add_argument("--all-food", action="store_true", help="both colours are food (nothing to learn)")
    args = parser.parse_args()
    for path in args.spec:                                  # a minimal-search circuit, as a brain like any other
        import json
        import os
        from minimal.spec import make
        BRAINS[os.path.basename(path)[:-5]] = make(json.load(open(path))["spec"])
    args.brains = args.brains or list(BRAINS)
    for b in [args.brain, *args.brains]:
        if b not in BRAINS:
            parser.error(f"{b}: not a brain (one of {', '.join(BRAINS)})")
    if args.measure:
        measure(args.measure, args.ticks, args.brains, args.all_food)
    else:
        watch(args.seed, args.brain, args.record, args.ticks, args.all_food)
