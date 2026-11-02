# nca-learn: a brain that grows itself and learns

Can a brain grow itself, emergently, and be useful? Grown, here, means built by local rules alone: nothing places
its parts, no unit sees the whole, and no god decides. Useful means capable of learning one bit of information during
its lifetime: here, which of two colours is food and which is poison.

**The sheet brain** builds itself before it acts. A sheet of identical cells, each running one local rule and seeing
nothing of its neighbours but the average of each number they share, works out where each cell is, grows organs and
wires them, like the "lizard" of [Growing Neural Cellular Automata](https://distill.pub/2020/growing-ca/) (Mordvintsev
et al., Distill 2020), but growing a nervous system instead of a picture. Then the creature it drives learns.

This repository is a small, self-contained demo of that one brain. (The wider exploration it started carries on in
[simple_learner](https://github.com/pilgrimbeart/simple_learner).)

![A life with the sheet brain: the brain (left) builds a coordinate frame, names its organs and grows its wiring,
then the creature (right) learns which colour is food](media/life.gif)

## What we've learned

The findings that changed the direction of the work, each told in full in the notebook.

- **The body must never do the brain's job.** Early on the body was changed to give food or poison only to the
  sensor whose colour was eaten. It looked like a simplification, since four mechanisms in the brain could go, but
  those mechanisms were the brain working out which sensor a taste was about (credit assignment), the hardest part
  of the task. The body was doing it instead. So whenever a change to the body lets the brain drop machinery, we ask
  where that machinery's job went (`NOTEBOOK.md`, Lessons).
- **Rules kept only in prose drift, so the code enforces them.** The sheet brain's central rule is that a cell sees
  only the average of what its neighbours show. Earlier experiments quietly broke it (reading one neighbour on its
  own), and nothing stopped them. Now the rule is built into the engine's structure and tested, so breaking it fails
  loudly (`NOTEBOOK.md`, Lessons).
- **Find what the body allows before blaming the brain.** A scripted policy that is told the answer from birth and
  sees only what a brain would see shows the best any brain could do with that body. This showed that an early square
  body, not the brain, capped every brain (`NOTEBOOK.md`, The body).
- **Real units show what abstract ones hide.** Written in seconds and metres, every number has a meaning and a quick
  sanity check: a tick of 10 ms makes a reaction in 2 to 4 ticks an insect's (`NOTEBOOK.md`, Lessons; `units.py`).

## The ground rules

The brain keeps the ground rules set out in `AGENTS.md`: the body talks to the brain only through two sensors, two
motors and one taste that never says which sensor it is about, and never does the brain's work (credit assignment,
timing, filtering); nor does the simulator, so there is no clock or lockstep and noise is everywhere; and everything is
local, with no god.

## The creature and its world

A disc whose front point is the mouth, with eyes looking ahead (one sensor for each colour) and a forward thruster on
each side of its rear rim: both thrusters together drive it straight ahead, one alone makes it veer. (It was a triangle
until 2026-10-31; the disc keeps the mouth where the point was, so every life is unchanged.) Red and blue blocks lie
about the world; one colour is poison, alternating from life to life. A brain fires its two motors and is told only what
its sensors see and the taste. In *all-food lives* both colours are food, so there is nothing to learn: the control for
anything that should happen only when there is.

## Quick start

Needs Python 3.10 or later.

```bash
git clone https://github.com/pilgrimbeart/nca-learn.git
cd nca-learn
python3 -m venv .venv              # Windows: python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python creature.py                 # watch a life
```

Once the environment is active, `python` is its Python. In a new terminal, activate it again first. On Ubuntu, if
`python3 -m venv` says ensurepip is missing: `sudo apt install python3-venv`.

The first run after the brain's code changes pauses for 15-30 s while numba compiles it (the window says so); after
that it starts in about a second, from numba's cache.

In the live view:

| key | |
|---|---|
| `r` | a new life (a new seed, a new wiring; poison alternates red and blue) |
| `d` | damage the sheet: replace a disc of cells under the mouse with new-born ones |
| `i` | the rules the simulation enforces: the interface, the sheet's rules, seeds (wheel or up/down: scroll; numbers read from the code; "copy all" puts them on the clipboard as text, "open as text" opens them in a text viewer; `python creature.py --rules` prints them) |
| space | pause |
| up / down | faster / slower; below a tick a frame, down waits 2, 4 ... 32 frames per tick |
| `a` | automatic speed again (slow while the sheet wires itself and first moves, fast otherwise) |
| Esc | quit |

### What you're seeing

- **Left, the brain** (49 × 49 cells):
  - a faint **checkerboard**: the coordinates each cell has worked out for itself (x and y, each running from -1 to
    1 across the sheet), in squares of about 4 cells;
  - its organs, labelled with the names they gave themselves, **S1** and **S2** (the sensors, on one edge), between
    them **T** (taste: white while it shows a taste), and **M1** and **M2** (the actuators, its motors, on the
    opposite edge), and then with what the body wired them to this life: **red** or **blue** (the sensor that sees
    that colour, with its chance of firing both thrusters, which it has learned) and **left** or **right** (the
    thruster it drives);
  - **paths**: sky blue from the sensors to M1, orange to M2; **pulses** running down them, white.
- **Right, the world:** red blocks and blue blocks, lettered R and B, and the creature, a disc with its mouth marked
  by a dot on the rim the way it faces, its thrusters small squares on the rear rim, and what its eyes see: a pale
  beam ahead, the corridor its mouth will sweep, fading with distance, each of its rays stopping at the first block it
  meets (so a near block casts a shadow). A ring round a thruster shows it firing. "yuck!" is a poison meal.
- **Below:** the tick, the stage of life, which colour is poison this life, and the recent meals; and a button for
  `i` (above). The life waits while the rules are open. The window can be resized or maximised: the panels stay
  square, centred.

The view runs at 10 ticks a frame, but slows to 1 while the paths grow and until a little after the creature starts
moving, so the pulses can be seen running down them. A life goes: "where am I" (to about 4.5 s), "wiring", then
"moving and learning". Within a few tens of seconds the poison sensor's chance of firing both falls towards 0, and
the food sensor's rises towards 1.

## The sheet brain

A sheet of identical cells, each born the same bar random noise, each running one local rule. Like the lizard, it
builds something from nothing and repairs itself when damaged: cells work out where they are, differentiate, wire
sensors to thrusters, and then drive a creature that learns, within its own lifetime, which colour is food. Nothing in
the cells is told which colour is poison, where it is in the sheet, or how big the sheet is. The brain grows two
sensors and two actuators and wires each sensor to both actuators; the rule a cell runs is unchanged if the two
sensors, or the two actuators, are swapped. What a sensor learns is only whether to fire both thrusters at what it
senses (the creature drives straight at it) or one (it veers).

### Its rules can't be broken by accident

The ground rules (above) are built into the code:

- **`sheet.py` is the only code that knows there is a grid.** A rule (`rules/*.py`) declares its numbers, which of
  them its neighbours can see, and what every cell is born with, and one compiled function
  `update(me, mean, count, inp, out)`. It is given its own numbers, its neighbours' **mean** of each shared number,
  how many neighbours it has, and what the body delivered: nothing else. Not its position, the size, a clock, or any
  neighbour on its own.
- **A rule never holds a view into the sheet.** The engine copies a cell's numbers and its neighbours' means into the
  rule's own small arrays, and `test_rules.py` runs every rule with array bounds checked, so an index past the end
  can't reach another cell's numbers.
- **The engine does the rest.** The sheet runs in steps, 400 a second (4 to each tick of the world); at each step each cell updates
  with some chance, never all at once. Every number a cell keeps gets a little noise at every update. What it shows
  its neighbours is cruder: every shared number is clipped to -1..1 and shown with noise of 1%, drawn afresh every
  step. So a shared number can't carry much: no encoding can squeeze information below the noise or spread it over
  orders of magnitude. Every cell is born from one birth vector, identical bar declared noise.
- **The body touches the brain only at cells, by the names they gave themselves:** `cells()`, `give()`, `get()`,
  `take()`. Only the cells named S1 and S2 get a stimulus, and only the cells named T get taste (+1 food, -1 poison,
  at the tick a block touches the mouth: it never says which sensor it is about); only M1 and M2 are read. Watching uses
  `view()`; the experimenter's `damage()` replaces cells with new-born ones. `test_rules.py` checks every rule's
  imports, signature and birth, and that no body code reaches inside.
- Numba-compiled: about 330,000 cell-updates a second on one core for the whole brain (about 150 steps, so 0.37 s
  of the world, a second at 49 × 49).

### What a cell can read from averages

Each shared number is between -1 and 1, with noise of 1%, and a cell sees only its neighbours' mean of it. A
neighbour moves that mean by at most 2 / (the cell's number of neighbours), so what a cell reads is the sum over its
neighbours, with noise of about 0.03.

- **Flags.** A number shown as +1 or -1: the sum counts the neighbours showing +1, exactly.
- **A few levels.** A number shown at a few well-spaced strengths: the sum says how many neighbours show each, as long
  as every mix that can occur sums to something clearly different (`rules/see.py` chooses the strengths so).
- **Gradients.** A smooth number many neighbours share: if each cell takes its neighbours' mean, with a few cells
  held fixed, the sheet settles into a smooth field, and the mean reads it closely. That is how cells learn where
  they are.
- **Waves.** An excitable flag (excited for a moment, then resting): a cell that sees an excited neighbour is excited
  in turn, so a wave runs outwards from wherever it starts, and dies at the edges and where waves meet.
- **Not the smallest.** A mean can't give the smallest of the neighbours' numbers (an earlier version cheated the
  noise rule to get it: `NOTEBOOK.md`). Distances are counted mod 5 instead (below).
- **Whole numbers.** What a cell keeps to itself is not limited: it keeps counts and timers as whole numbers,
  re-rounded at each update so its own small noise can't move them.

### What happens in a life

The rules are layered: `rules/brain.py` runs `rules/wiring.py`, which runs `rules/organs.py`; `rules/see.py` holds
what they share.

1. **Where am I** (`rules/organs.py`).
   - **The race.** The four corners know they are corners: they have three neighbours. Each beats like a pacemaker,
     sending waves across the sheet, each at its own random pace. A corner reached by another's wave before its own
     beat stands down for good, so the fastest is left: the organiser. It keeps beating. It organises the sheet's
     coordinates, and is not an organ. Each beat carries its number mod 3, and a cell takes only the next beat after
     the last it took, so no wave can circle back (as damage would otherwise make it).
   - **Handedness.** The organiser's two edge neighbours toss coins until they differ: the one with heads is on the
     edge that will be y = -1.
   - **Edge labels.** At each of the organiser's beats those two start a label pulse along their edges: "y = -1" and
     "x = -1". Each corner at the far end of an edge starts the opposite label (+1) along its other edge. A label
     stops at a corner instead of leaking round it, and a cell forgets a label after six of the organiser's beats
     with no pulse to renew it, so if the winner changes, the labels follow it. (Not three: a cell that misses one
     beat refuses the next two as out of turn.)
   - **Coordinates.** Labelled edges hold x (or y) at their label; every other cell takes the mean of its neighbours'.
     So x runs straight from -1 to 1 across the sheet, and y too: a gradient, read well from averages. While a cell's
     place still drifts it carries on part of its last move (momentum), which speeds the settling.
   - **Organs.** Once its place has stopped drifting, a cell either side of the middle of the y = 1 edge (x = -1/8
     and +1/8) names itself a sensor, S1 or S2, and likewise on the y = -1 edge an actuator, M1 or M2: 1 on the
     x < 0 side. Both of a kind are placed by one rule. The marked cells between the sensors name themselves T, the
     taste organ, so each sensor has a T cell beside it (and if the mark's end drifts after a sensor is named, the
     cell between takes T too). A name is taken after holding its place for 300 updates, and then kept: a named cell
     shows that it is named, so no neighbour takes the name too.
2. **Wiring** (`rules/wiring.py`).
   - **Signals from the sinks.** Once M1 and M2 have named themselves, each sends out a distance field: it shows 0,
     and every other cell one more than the nearest of its neighbours, counted mod 5 (shown on five flags). A
     cell's neighbours are one step nearer, level or one step farther, three residues of the five in a row, so the
     lowest is the one after the gap. Nothing in the wiring knows where M1 and M2 are: the paths follow the fields, so
     if one named itself somewhere else, the paths would grow there.
   - **Path cells** show their residue as a pattern on three flags, at a strength that says if they are a tip or
     carry a pulse, so every cell knows what path cells are one step nearer, level and one step farther.
   - **Growth.** Each sensor starts a path down each field once its distance has held still. The end of a path (a tip)
     shows itself; the cells one step nearer raise hands at random, and the tip says "go" only while it sees exactly
     one hand; that cell joins. So a path grows one cell at a time, downhill, until it reaches its actuator, and a tip
     never takes two. A cell that would also give another path a second way on rarely raises its hand.
   - **Fading.** A path cell with no path cell one step farther leaves, so a path cut off from its source fades and
     its source grows a new one.
   - **Pulses.** A pulse runs down a path, from a cell to its neighbour one step nearer, and the actuator counts
     the pulses it takes: the body fires the thruster it wired to that actuator.
3. **Choosing** (`rules/brain.py`). A sensor fires when the body stimulates it (its colour is in view), and now and
   then by itself. Each time, it sends a pulse to both actuators with chance p, otherwise to one: always the same one,
   its side, chosen by a coin toss. Both thrusters fire forward, one from each corner of the tail: both together drive
   the creature straight ahead, one alone makes it veer. Born p = 1/2.
4. **Learning, in the sensors** (`rules/brain.py`). When a block touches the mouth it is eaten, and the T cells get
   the taste: +1 for food, -1 for poison, nothing about which sensor saw it. Each shows its sign for 3 updates. A
   sensor that sees taste begin beside it, and was stimulated within the last 15 updates, moves p half the way
   towards 1 (good) or 0 (bad). Three factors: the sensor's own recent input, the taste, and that the other sensor has
   not been stimulated since. For that last one, a stimulated sensor shows a ping, which the T cells relay as a
   one-way wave to the other sensor, and that sensor forgets its stimulus. So the brain, not the body, works out which
   sensor a taste is about. All other cells only build and carry: frame, paths, pulses.

No stage waits a fixed time: each starts when the one before has produced what it needs.

### The numbers a cell shares

28, each between -1 and 1 and seen only as averages over the neighbours, most of them in effect flags. The lizard
used 16, but not like for like: its cells saw each one through Sobel filters, which weight neighbours by where they
are, so they saw direction for free, in full-precision numbers with no noise on what neighbours show. Ours see no
direction at all, only means, so they build it from signals: the coordinates and the distance fields are most of the
28.
- where am I: 8 (the race's wave on two flags, hand, two edge labels, x, y, and the mark that places the organs);
- wiring: 9 for each of the two channels (five for the distance, three for the path, one for offers);
- learning: 2 (taste, shown by the T cells; ping, the wave that tells a sensor the other was stimulated since).

### Result

Three scores: how soon the sensors learn (set by the rules), and how much more food than poison the creature then
eats per 10 s and how many food blocks for each poison (set by the brain's behaviour and the body). 32 lives of
100 s with learning and 32 without, half with red as poison and half blue, each with its own random wiring
(`python creature.py --measure 32`). "Learned": both sensors' chance of firing both thrusters within 0.2 of right
(poison's at most 0.2, food's at least 0.8), counted from when the creature starts moving.

|  | learned | food minus poison per 10 s, by third of life after moving | food:poison, by third | firing both at the end |
|---|---|---|---|---|
| learning on | 24 of 32 lives, median 50 s | +0.25, +0.53, +0.89 | 1.5, 2.0, 3.0 | poison's sensor 0.17, food's 0.91 |
| learning off | none | 0, 0, 0 | 1.0 | both 0.50 |

Lives learn from taste alone: the brain works out which sensor a taste is about. An earlier version had the body hand
the taste to the eaten colour's sensor, which did that work for it (withdrawn: see `NOTEBOOK.md`). Now a taste after
both colours were seen at once is sometimes credited to the wrong sensor, so p wanders a little near its target.
Learning is slow because meals are few, about 1.5 per 10 s: in 8 lives of 32 the sensors had not both come
right by 100 s. With p set perfect from birth by hand the creature eats 3.6, 2.7 and 4.8 food for each poison
by thirds (32 lives): the limit of this body with a brain this slow (earlier bodies capped it lower: `NOTEBOOK.md`).
Once learned, the thirds differ much by noise: poison meals are few, and even 32 lives are few for this score.

### Damage

Press `d` in the live view to replace a disc of cells under the mouse with new-born ones, as with the lizard. A band 7
rows deep across the middle (6 lives of 6): the new cells relearn x and y within 90-180 steps, names are kept (or
retaken, where the band took one), and paths cut off from their source fade and regrow, so every route carries pulses
again (measured with an earlier version of the organs). Damage the organiser's corner (a disc of radius 4, 6 lives
of 6): it takes up beating again, at the same corner; but if its two coin-tossed neighbours went too, the toss can come
out the other way, and the sensors swap names, so each now gets the other colour and what each learned is about the
wrong one. Damage a sensor and a new cell takes the name, but what the old one had learned is gone.

### Not yet

- Odd sizes only, and tested at 49 × 49: on an even sheet the middle of an edge falls between two cells.
- Slow learning and the odd taste credited to the wrong sensor (Result, above).
- In about 1 sheet in 32, two cells take the same actuator name (M1).
- The coordinates take about 1,500 steps to settle (they are averages, and averages spread slowly).
- 28 shared numbers: fewer would be better, though the lizard's 16 also carried direction, which ours must build.
- Every life starts from scratch: the brain builds itself again (about 2,500 steps, 6 s, before the creature
  moves), and the sensors learn again.

### Inside one cell

Everything a cell does, as a block diagram: the rule's three layers and their stages, with what each reads from its
neighbours' means and the body on the left, and what it shows its neighbours and gives the body on the right.

![What runs inside one cell: organs (the race, handedness, edge labels, coordinates, naming), the brain (choose,
taste, ping and learn, in sensors and T cells) and the wiring for each of the two channels](media/cell.svg)

## Next

The open questions, most valuable first, are in [`QUESTIONS.md`](QUESTIONS.md).

## Terms

- **Real units**: everything in SI, every number that can be derived derived from a few axioms (`units.py`).
- **Tick**: the body's step, 10 ms: the eyes look, the thrusters fire and the body moves once a tick (a reaction in 2
  to 4 ticks is an insect's). The sheet takes 4 steps a tick. The live view shows real time at about 3 ticks a frame
  (it says how fast it runs against real time).
- **All-food lives**: both colours food, so there is nothing to learn: the control for anything that should happen
  only when there is something to learn.

## Other commands

```bash
python creature.py --seed 3         # a particular life
python creature.py --measure 32     # 32 lives with learning and 32 without, headless (--all-food: both colours food)
python test_rules.py                # check every sheet rule keeps the sheet brain's rules
python test_world.py                # check the compiled eyes and mouth against plain numpy versions
python watch.py organs              # one stage of the sheet brain on its own (organs, wiring; --show picks the numbers)
python measure_organs.py            # when the coordinates and names come right, life by life
python measure_wiring.py            # pulses sent from S1 and S2: how many arrive, and how soon
python diagram.py                   # redraw media/cell.svg, what runs inside one cell
python creature.py --record frames  # save a life's frames as PNGs, headless (media/life.gif: --seed 0 --seconds 100,
                                    # 180 frames taken evenly by tick)
```

## Files

| | |
|---|---|
| `creature.py` | a life (a body, a brain and the body's wiring), the live view, and the measurement |
| `world.py` | the world and the body: blocks, eyes, thrusters, mouth |
| `units.py` | the axioms: units and the tick |
| `brains/sheet.py` | the sheet brain: the sheet, by the names its cells took |
| `sheet.py` | the engine: the only code that knows the grid |
| `rules/organs.py` | where am I: the race, handedness, edge labels, coordinates, names |
| `rules/wiring.py` | growing paths and running pulses, built on `rules/organs.py` |
| `rules/brain.py` | choosing and learning, built on `rules/wiring.py` |
| `rules/see.py` | what cells read from averages, and the distance field and path signs the rules share |
| `rules/interface.py` | the signature every rule's compiled update has (so numba can cache the sheet) |
| `test_rules.py` | checks every sheet rule and every body file keep the rules |
| `test_world.py` | checks the compiled eyes and mouth (`world.py`) against plain numpy versions |
| `watch.py`, `measure_organs.py`, `measure_wiring.py` | each stage on its own, live or measured |
| `diagram.py` | draws `media/cell.svg`, the diagram above (by hand from the rules: redraw it when one changes) |
| `AGENTS.md` | the rules, for agents and people: principles, honesty, the brain's constraints, how to work here |
| `QUESTIONS.md` | the open questions, most valuable first: parked mid-quest, removed when answered |
| `NOTEBOOK.md` | the lab notebook of the sheet brain and the body: what was tried, what failed and why |

## Licence

MIT: see `LICENSE`.
