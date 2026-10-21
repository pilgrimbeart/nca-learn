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
"baseline-circuit" (brains/baseline.py), its neurons alone, driving at every block, with taste going nowhere (the
baseline for recruitment, RECRUITMENT.md); "adjusting-circuit" (brains/adjusting.py), each neuron adjusting its own
excitability from taste (rung 0); "knowing-circuit" (brains/knowing.py), the baseline circuit plus a taste neuron that
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
import os
import functools
import time

import numpy as np

from world import COLOURS, SENSE, THRUSTERS, WORLD, Body


class Brains(dict):
    """The brains by name, each imported when first asked for: importing a brain compiles it (numba: about 15 s the
    first time after its code changes, then from the cache), which only the brains in use should pay for, and the
    live view only once its window can say so. A value is (module, class, keywords) until then."""

    def __getitem__(self, name):
        v = dict.__getitem__(self, name)
        if isinstance(v, tuple):
            import importlib
            module, cls, kw = v
            v = getattr(importlib.import_module(module), cls)
            v = functools.partial(v, **kw) if kw else v
            dict.__setitem__(self, name, v)
        return v


BRAINS = Brains({
    "sheet": ("brains.sheet", "SheetBrain", {}), "designed-circuit": ("brains.designed", "DesignedBrain", {}),
    "baseline-circuit": ("brains.baseline", "BaselineBrain", {}),
    "adjusting-circuit": ("brains.adjusting", "AdjustingBrain", {}),
    "knowing-circuit": ("brains.knowing", "KnowingBrain", {}),
    "recruiting-circuit": ("brains.recruiting", "RecruitingBrain", {}),
    "healing-circuit": ("brains.healing", "HealingBrain", dict(listen="all", sign="inh", judge="share", tire=0.05)),
    "healing-cascade": ("brains.healing", "HealingBrain", dict(menu="inputs", listen="all", sign="inh", cascade=True,
                                                               trigger="root", judge="share", tire=0.05,
                                                               starve=20000.0))})
FAST, SLOW = 10, 1  # watching: ticks per frame, slow while the brain wires itself and first drives the body
SLOWEST = 1 / 32    # watching: down halves the speed to this, a tick every 32 frames (about 1 a second)
SCHEMATIC = "media/designed_circuit.png"    # watching: the designed circuit (drawn by schematic.py)
SETTLE = 200        # watching: ticks after the creature starts moving before speeding up again
BLOCKS = 300        # watching: the height of the block view below (blocks.py), in the window as it opens
TEXT = 108          # watching: the height of the lines and buttons between the panels and the block view
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
    a tick a frame, waits 2, 4 ... 32 frames between ticks, so single spikes can be followed). The window can be
    resized (or maximised): the panels stay square, centred, in the proportions it opens with. Buttons
    below: switch brain (a new world, the same seed), the rules the simulation enforces (i), and with the designed
    circuit, its schematic (the life waits while either is open). With record, no window: every frame is saved there as a PNG, until the given tick. all_food:
    both colours are food."""
    import os
    import pathlib
    from world import EAT, RAYS, REACH
    if record:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.makedirs(record, exist_ok=True)
    import pygame
    pygame.init()
    from blocks import BlockView, NodeView
    OPEN = 490                                                      # the panels' side as the window opens
    screen = pygame.display.set_mode((2 * OPEN + 12, OPEN + TEXT + BLOCKS), 0 if record else pygame.RESIZABLE)

    def layout():
        """The two square panels' side and the left one's x, from the window's present size."""
        w, h = screen.get_size()
        side = max(100, min((w - 12) // 2, (h - TEXT) * OPEN // (OPEN + BLOCKS)))
        return side, max(0, (w - 2 * side - 12) // 2)
    side, x0 = layout()
    view = None                                                     # the block view of a circuit brain
    pygame.display.set_caption("a brain learns which colour is food")
    font, small = pygame.font.SysFont(None, 22), pygame.font.SysFont(None, 18)
    per_frame, auto, paused, clock = FAST, True, False, pygame.time.Clock()   # auto: speed set by the stage
    owed = 0.0                                                      # ticks owed, below a tick a frame
    poison = None if all_food else COLOURS[seed % 2]

    def wait_note():
        """While a brain is first loaded: numba may be compiling it (only after its code has changed)."""
        screen.fill((0, 0, 0))
        w, h = screen.get_size()
        for i, line in enumerate((f"Please wait while numba compiles the {brain} brain ...",
                                  "(only after its code has changed: about 15 to 30 s; otherwise a moment)")):
            text = (font if i == 0 else small).render(line, True, (255, 255, 255) if i == 0 else (170, 170, 170))
            screen.blit(text, ((w - text.get_width()) // 2, h // 2 - 20 + 30 * i))
        pygame.display.flip()
        pygame.event.pump()

    wait_note()
    life = Life(seed, poison, brain=brain)
    to_px = lambda p: (x0 + side + 12 + int(p[0] / WORLD * side), int((WORLD - p[1]) / WORLD * side))
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
        for key, label in (("b", f"brain: {brain}   switch to {other}  (b)"), ("i", "rules  (i)")) + \
                          ((("s", "schematic  (s)"),) if brain == "designed-circuit" else ()):
            w = font.size(label)[0] + 20
            out.append((key, label, pygame.Rect(x, side + 74, w, 28)))
            x += w + 10
        return out

    def press(key):
        nonlocal brain, life, auto, viewer
        if key == "b":                                              # another brain, in a new world
            names = list(BRAINS)
            brain = names[(names.index(brain) + 1) % len(names)]
            wait_note()
            life, auto, viewer = Life(seed, poison, brain=brain), True, None
        elif key == "s" and brain == "designed-circuit":
            viewer = SchematicViewer(pygame, screen, pathlib.Path(__file__).parent / SCHEMATIC, font)
        elif key == "i":
            viewer = RulesViewer(pygame, font, small)

    while True:
        screen = pygame.display.get_surface()                       # (resized with the window)
        side, x0 = layout()
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
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_b, pygame.K_s, pygame.K_i):
                press({pygame.K_b: "b", pygame.K_s: "s", pygame.K_i: "i"}[event.key])
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
                    mx -= x0
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
        life.brain.draw(screen.subsurface((x0, 0, side, side)), side, font, sensors, motors,
                        life.sensor[poison] if yuck else None)
        pygame.draw.rect(screen, (25, 25, 25), (x0 + side + 12, 0, side, side))
        body = life.body
        f, h = body.forward(), body.head()
        r = np.array([f[1], -f[0]])                                 # the creature's right
        beam = pygame.Surface((side, side), pygame.SRCALPHA)
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
                        pygame.draw.polygon(beam, (255, 255, 255, alpha), [(x - x0 - side - 12, y) for x, y in pts])
        screen.blit(beam, (x0 + side + 12, 0))
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
            screen.blit(font.render(line, True, (255, 255, 255)), (6, side + 6 + 22 * i))
        hover = pygame.mouse.get_pos()
        for _, label, rect in buttons():
            pygame.draw.rect(screen, (90, 90, 90) if rect.collidepoint(hover) else (50, 50, 50), rect, border_radius=4)
            pygame.draw.rect(screen, (200, 200, 200), rect, 1, border_radius=4)
            screen.blit(font.render(label, True, (255, 255, 255)), (rect.x + 10, rect.y + 6))
        strip = pygame.Rect(0, side + TEXT, screen.get_width(), max(0, screen.get_height() - side - TEXT))   # below:
                                                                                        # the brain as blocks
        if hasattr(life.brain, "circuit"):
            if view is None or view.brain is not life.brain:
                view = (NodeView if getattr(life.brain, "level0", False) else BlockView)(life.brain)
            view.draw(screen, strip, life, font, small)
        else:
            pygame.draw.rect(screen, (18, 18, 18), strip)
            screen.blit(font.render("block view: for the circuit brains (b to switch)", True, (120, 120, 120)),
                        (8, side + TEXT + 4))
        pygame.display.flip()
        if record:
            pygame.image.save(screen, os.path.join(record, f"{life.t:06d}.png"))
            if life.t >= until:
                pygame.quit()
                return
            continue
        clock.tick(30)


def rules() -> list:
    """Watching: the rules the simulation enforces, as (depth, text): 0 a heading, 1 a point, 2 a point under it. The
    numbers are read from the code, so the list can't drift from what is enforced."""
    import mixed_feedback as mf
    import sheet
    import world
    from brains import circuit
    from minimal import spec
    noisy = f"{mf.NOISY[0]:g} to {mf.NOISY[1]:g}"
    return [
        (0, "The body and the brain"),
        (1, "A brain meets the body only through two sensors, two motors and one taste: nothing else passes either way."),
        (1, f"Each eye fires at random moments (a Poisson process), up to {world.SENSE:g} times a tick for its colour"
            f" seen close up, half as often at {world.REACH:g} units, nothing beyond {world.RANGE:g}; it says how much"
            " of its colour is ahead, never where."),
        (1, "The taste is +1 (food) or -1 (poison) for one tick when a block touches the mouth, else 0, and never says"
            " which sensor it is about."),
        (1, "Which colour feeds which sensor, and which motor drives which thruster, is drawn at random for each life:"
            " no brain can be built knowing it."),
        (1, "A thruster fires once for each spike of its motor; a motor spikes when its voltage rises through"
            f" {mf.SPIKE:g} V, and can spike again only once it has fallen below {mf.RESET:g} V."),
        (1, "The body must never become part of the solution: it does no job a brain could do (credit, timing,"
            " filtering, choosing what learns)."),
        (0, "The circuit simulator (every circuit brain)"),
        (1, "Everything that affects behaviour is explicit circuit: nodes (capacitors, with any leak) and elements (a"
            " current from a node's voltage, possibly filtered and gated); no program beside it."),
        (1, f"Continuous time, integrated in steps of {mf.DT:g} tick; the body's pulses arrive anywhere within a tick,"
            " never on tick boundaries, so nothing can lock to the clock."),
        (1, f"Shot noise on every device's current (variance {mf.SHOT:g} x its current per tick), summed gross, not"
            " net: two currents that cancel still flicker."),
        (1, f"Membrane noise on every node in proportion to its capacitance (variance {mf.MEMBRANE:g} x C per tick); none on a"
            " memory node, whose only noise is its writes'."),
        (1, f"Mismatch: every part off by about {mf.MISMATCH:.0%} of itself at birth, drawn once per circuit."),
        (1, f"The noise can be scaled only within {noisy} of its usual level, never turned off or dodged."),
        (1, "A result must hold at a finer step and on fresh seeds."),
        (0, "The minimal circuit search: what a circuit may be"),
        (1, f"Within the supply: every node within +-{mf.RAIL:g} V; a clamp inside the rails is a part."),
        (1, f"Not faster than the step: nothing may move a node more than {spec.SLEW:g} V per circuit tick, and a"
            f" device fed back to itself acts no faster than {spec.LOOP:g} per circuit tick."),
        (1, "An illegal circuit can't be built or lived (minimal/spec.py, check)."),
        (1, "Sepulchre's rules, when a circuit declares them: every node leaks except memory nodes, no clamps; gates"
            " and memory nodes (floating gates) allowed, as Sepulchre is silent on learning and storage."),
        (0, "Judging: seeds and lives"),
        (1, "A seed is a world: where the blocks are, where the creature starts, which colour is poison, the circuit's"
            " noise and mismatch. The same seed gives the same life."),
        (1, "Each seed is lived twice, red then blue as poison, so a circuit that ignores taste scores below 0."),
        (1, "Searches choose on seeds of their own, fresh each generation: the polish from 10,000, pruning"
            " 15,000-15,031, the open search from 20,000."),
        (1, "Held out: seeds 100-163 judge what a search produced and are never used to choose."),
        (1, "Headline claims are confirmed once on seeds 500-563, never used before, then retired."),
        (1, "Judged at the usual noise; an experiment may judge across half, usual and double, the worst level"
            " counting."),
        (0, "Judging: the job and the score"),
        (1, f"The job: at least {spec.JOB[0]:g} food per 1,000 ticks; food:poison at least {spec.JOB[1]:g} over the"
            f" last third of a 10,000-tick life; at most {spec.JOB[2]:.0%} of lives stranded (no food in their last"
            " third)."),
        (1, f"The score, per 1,000 ticks: food, less {spec.COST:g} x poison, less {spec.COST:g} x the food each third"
            f" of each life falls short of {spec.NEED:g}, less moving and thinking."),
        (2, f"Moving: a thruster firing costs {spec.THRUST:g} of a meal."),
        (2, f"Thinking: {spec.ENERGY:g} of a meal per unit of the circuit's power per 1,000 ticks (about a hundredth"
            " of moving)."),
        (2, f"Resting: the {spec.NEED:g} meal per 1,000 ticks every creature needs, counted in efficiency."),
        (0, "Judging: what is measured"),
        (1, "Parts: capacitors, resistors, diodes and transistors."),
        (1, f"Area, by analogy with analogue chips, in unit transistors: an element {spec.AREA['element']}, a gate"
            f" {spec.AREA['gate']} more, a leak {spec.AREA['leak']}, a capacitor {spec.AREA['capacitor']} per unit;"
            " shown, not ranked on."),
        (1, "Efficiency: meals eaten per meal spent (resting, moving, thinking). Thrift: food per 1,000 firings."
            " Speed: food per 1,000 ticks."),
        (1, "Simplicity and efficiency are kept apart, never traded."),
        (1, "Confidence: every measure with its 95% interval; two designs compared paired, on the same seeds, and"
            " one is above the other only if the interval of the difference excludes 0. Otherwise: tied."),
        (0, "The sheet brain"),
        (1, "Identical cells running one local rule; a cell sees only its own numbers, its neighbours' mean of each"
            " shared number, and how many neighbours it has."),
        (1, f"Shared numbers are clipped to -1..1 and shown with noise {sheet.SHOW:g}; kept numbers get noise"
            f" {sheet.NOISE:g} at every update; cells update at random, never all at once."),
        (1, "No hidden size, no magic knowledge: a path finds its target by a signal the target itself sends."),
    ]


def rules_text() -> str:
    """The rules (rules()) as plain text, Markdown-style, to copy or keep (python creature.py --rules)."""
    out = ["# What the simulation enforces"]
    for depth, text in rules():
        out.append(f"\n## {text}\n" if depth == 0 else ("- " if depth == 1 else "  - ") + text)
    return "\n".join(out) + "\n"


def _wsl() -> bool:
    import platform
    return "microsoft" in platform.release().lower()


def copy_text(pygame, text: str) -> bool:
    """Put text on the clipboard: Windows' (clip.exe) under WSL, else SDL's; True if it got there."""
    import subprocess
    if _wsl():
        try:
            subprocess.run(["clip.exe"], input=text.encode("utf-16"), check=True, timeout=10)
            return True
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        pygame.scrap.init()
        pygame.scrap.put(pygame.SCRAP_TEXT, text.encode())
        return True
    except Exception:                                  # (no clipboard this pygame can reach)
        return False


def open_text(text: str, name: str = "nca-learn-rules.txt") -> str:
    """Write text to a file and open it in the system's viewer (Notepad under WSL), where any of it can be selected;
    returns the file's path."""
    import subprocess
    import tempfile
    path = os.path.join(tempfile.gettempdir(), name)
    with open(path, "w") as f:
        f.write(text)
    try:
        if _wsl():
            win = subprocess.run(["wslpath", "-w", path], capture_output=True, text=True, timeout=10).stdout.strip()
            subprocess.Popen(["explorer.exe", win])
        else:
            subprocess.Popen(["xdg-open", path])
    except OSError:
        pass
    return path


class RulesViewer:
    """Watching: the rules the simulation enforces (rules()), over the whole window. The wheel or up and down scroll;
    copy all puts them on the clipboard as text, open as text opens them in a text viewer; Esc, i or close shuts it."""
    BAR = 30

    def __init__(self, pygame, font, small):
        self.pg, self.font, self.small = pygame, font, small
        self.items, self.top = rules(), 0
        self.said, self.said_at = "", 0.0              # what the last button did, shown for a few seconds

    @property
    def close(self):
        return self.pg.Rect(self.pg.display.get_surface().get_width() - 110, 2, 104, self.BAR - 4)

    @property
    def copy(self):
        return self.pg.Rect(self.close.x - 110, 2, 100, self.BAR - 4)

    @property
    def opened(self):
        return self.pg.Rect(self.copy.x - 130, 2, 120, self.BAR - 4)

    def handle(self, event) -> bool:
        """Takes an event; False once it is closed."""
        pg = self.pg
        if event.type == pg.KEYDOWN and event.key in (pg.K_ESCAPE, pg.K_i):
            return False
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1 and self.close.collidepoint(event.pos):
            return False
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1 and self.copy.collidepoint(event.pos):
            ok = copy_text(pg, rules_text())
            self.said = "copied to the clipboard" if ok else "no clipboard reachable: try open as text"
            self.said_at = time.time()
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1 and self.opened.collidepoint(event.pos):
            self.said, self.said_at = f"opened {open_text(rules_text())}", time.time()
        if event.type == pg.MOUSEWHEEL:
            self.top = max(0, self.top - 3 * event.y)
        elif event.type == pg.KEYDOWN and event.key in (pg.K_UP, pg.K_DOWN, pg.K_PAGEUP, pg.K_PAGEDOWN):
            step = {pg.K_UP: -1, pg.K_DOWN: 1, pg.K_PAGEUP: -15, pg.K_PAGEDOWN: 15}[event.key]
            self.top = max(0, self.top + step)
        return True

    def lines(self, width):
        """The rules wrapped to the width: (depth, first line of its item, text)."""
        out = []
        for depth, text in self.items:
            f = self.font if depth == 0 else self.small
            indent = (0, 22, 44)[depth]
            words, line = text.split(), ""
            first = True
            for w in words:
                if line and f.size(line + " " + w)[0] > width - indent - 40:
                    out.append((depth, first, line))
                    line, first = w, False
                else:
                    line = f"{line} {w}" if line else w
            out.append((depth, first, line))
        return out

    def draw(self) -> None:
        pg = self.pg
        screen = pg.display.get_surface()
        w, h = screen.get_size()
        screen.fill((24, 24, 24))
        lines = self.lines(w)
        self.top = min(self.top, max(0, len(lines) - 5))
        y = self.BAR + 10
        for depth, first, text in lines[self.top:]:
            if y > h - 20:
                break
            if depth == 0:
                y += 8
                screen.blit(self.font.render(text, True, (255, 255, 255)), (16, y))
                pg.draw.line(screen, (120, 120, 120), (16, y + 21), (w - 16, y + 21), 1)    # headings underlined
                y += 28
                continue
            x = 16 + (22, 44)[depth - 1]
            if first:
                mark = (x - 12, y + 7)
                if depth == 1:
                    pg.draw.circle(screen, (220, 220, 220), mark, 3)             # a point: a dot
                else:
                    pg.draw.line(screen, (220, 220, 220), (mark[0] - 3, mark[1]), (mark[0] + 3, mark[1]), 2)   # under it: a dash
            screen.blit(self.small.render(text, True, (230, 230, 230)), (x, y))
            y += 19
        pg.draw.rect(screen, (40, 40, 40), (0, 0, w, self.BAR))
        title = "what the simulation enforces   wheel or up/down: scroll"
        if self.said and time.time() - self.said_at < 6:
            title = self.said
        screen.blit(self.font.render(title, True, (255, 255, 255)), (8, 7))
        for rect, label in ((self.opened, "open as text"), (self.copy, "copy all"), (self.close, "close (Esc)")):
            hover = rect.collidepoint(pg.mouse.get_pos())
            pg.draw.rect(screen, (90, 90, 90) if hover else (60, 60, 60), rect, border_radius=4)
            pg.draw.rect(screen, (200, 200, 200), rect, 1, border_radius=4)
            screen.blit(self.font.render(label, True, (255, 255, 255)), (rect.x + 10, rect.y + 5))


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
        self._clamp()

    @property
    def close(self):
        return self.pg.Rect(self.screen.get_width() - 110, 2, 104, self.BAR - 4)

    def _clamp(self):
        self.screen = self.pg.display.get_surface()                 # (resized with the window)
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
        self.screen = self.pg.display.get_surface()                 # (resized with the window)
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
    parser.add_argument("--rules", action="store_true", help="print the rules the simulation enforces, as text")
    args = parser.parse_args()
    if args.rules:
        print(rules_text(), end="")
        raise SystemExit
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
