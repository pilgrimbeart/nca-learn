# nca-learn: a brain that builds itself then learns

Is it possible to design a self-constructing neural network that is useful?

Here we define "useful" as "capable of learning 1 bit of information during its lifetime". 

A sheet of identical cells, each born the same bar random noise, each running one local rule, and each seeing
nothing of its neighbours but the **average** of each number they share. Like the "lizard" of
[Growing Neural Cellular Automata](https://distill.pub/2020/growing-ca/) (Mordvintsev et al., Distill 2020), it
builds something from nothing and repairs itself when damaged. But instead of growing a picture, it grows a nervous
system: cells work out where they are, differentiate, wire sensors to thrusters, and then drive a creature 
that learns, within its own lifetime, which of two colours is food.

![A life: the brain (left) builds a coordinate frame, names its organs and grows its wiring, then the creature
(right) learns which colour is food](media/life.gif)

Nothing in the cells is told which colour is poison, where it is in the sheet, or how big the sheet is. No clock, no
global signal, no lockstep: cells update at random, with noise in every number. And the body never does the brain's
work: when a block touches the mouth, it gives one taste, +1 for food or -1 for poison, without saying which sensor
saw that block. The brain works out for itself what earned the taste.

Nor does any cell know what the organs are for. The brain grows two sensors and two actuators, the two of each kind
alike in everything but name, and wires each sensor to both actuators. Only the body (a triangle, its point the mouth)
knows that one sensor sees red and the other blue, and that the actuators drive thrusters at the left and right
corners of its tail, and it draws that wiring at random each life. The rule a cell runs is unchanged if the two
sensors, or the two actuators, are swapped. What a sensor learns is only whether to fire both thrusters at what it
senses (the creature drives straight at it) or one (it veers): approaching and avoiding are behaviour, not concepts in
the cells.

## Quick start

Needs Python 3.10 or later.

```bash
git clone https://github.com/pilgrimbeart/nca-learn.git
cd nca-learn
python3 -m venv .venv              # Windows: python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python creature.py                 # watch a life (the grown brain; --brain mixed-signal for the other)
```

Once the environment is active, `python` is its Python. In a new terminal, activate it again first. On Ubuntu, if
`python3 -m venv` says ensurepip is missing: `sudo apt install python3-venv`.

Each run starts with a pause of a few seconds while numba compiles the rules.

In the live view:

| key | |
|---|---|
| `r` | a new life (a new seed, a new wiring; poison alternates red and blue) |
| `d` | damage the brain: replace a disc of cells under the mouse with new-born ones |
| `b` | switch brain (grown or mixed signal), in a new world with the same seed |
| `s` | the mixed-signal brain's schematic (wheel: zoom, drag: pan, Esc: close) |
| space | pause |
| up / down | faster / slower (takes over from the automatic speed; `r` hands it back) |
| Esc | quit |

### What you're seeing

- **Left, the brain** (49 × 49 cells), in greys:
  - a faint **checkerboard**: the coordinates each cell has worked out for itself (x and y, each running from -1 to
    1 across the sheet), in squares of about 4 cells;
  - its organs, labelled with the names they gave themselves, **S1** and **S2** (the sensors, on one edge), between
    them **T** (taste: white while it shows a taste), and **M1** and **M2** (the actuators, on the opposite edge),
    and then with what the body wired them to this life: **red** or **blue** (the sensor that sees that colour,
    with its chance of firing both thrusters, which it has learned) and **left** or **right** (the thruster it
    drives);
  - **paths**: light grey from the sensors to M1, mid grey to M2; **pulses** running down them, white.
- **Right, the world:** red blocks (dark, lettered R) and blue blocks (light, lettered B), and the creature, a
  triangle pointing the way it faces, its point (the mouth) marked, and what its eyes see: a pale beam ahead, the
  corridor its mouth will sweep, fading with distance, each of its rays stopping at the first block it meets (so a
  near block casts a shadow). A ring at a corner of the tail shows that thruster firing. "yuck!" is a poison meal.
- **Below:** the tick, the stage of life, which colour is poison this life, and the recent meals; and buttons for `b`
  and `s` (above). The life waits while the schematic is open.

The view runs at 10 ticks a frame, but slows to 1 while the paths grow and until a little after the creature starts
moving, so the pulses can be seen running down them. A life goes: "where am I" (to about tick 450), "wiring", then
"moving and learning". Within a few thousand ticks the poison sensor's chance of firing both falls towards 0, and the
food sensor's rises towards 1.

## Other commands

```bash
python creature.py --seed 3         # a particular life
python creature.py --measure 32     # every brain, 32 lives each with learning and 32 without, headless
                                    # (--brains to choose; --all-food: lives where both colours are food)
python creature.py --brain minimal  # the baseline for recruitment: drives at every block, taste goes nowhere
python creature.py --brain adjusting  # rung 0 of recruitment: each neuron adjusts its own excitability from taste
python recruit_test.py 32           # recruitment's local signals, neuron by neuron, watched from outside
python test_rules.py                # check every rule keeps the rules below
python test_compiled.py             # check the compiled circuit and eyes against plain numpy versions
python watch.py organs              # one stage on its own (organs, wiring; --show picks the numbers drawn)
python organs_test.py               # when the coordinates and names come right, life by life
python wiring_test.py               # pulses sent from S1 and S2: how many arrive, and how soon
python diagram.py                   # redraw media/cell.svg, what runs inside one cell
python schematic.py                 # redraw media/mixed_signal.svg and .png, the mixed-signal brain's circuit
                                    # (needs pip install schemdraw cairosvg pillow)
python creature.py --record frames  # save a life's frames as PNGs, headless (media/life.gif: --seed 0 --ticks 10000,
                                    # 180 frames taken evenly by tick)
```

## The rules can't be broken by accident

Whatever the simulation lets a design exploit, whoever optimises it will find: once, asked to cut the channels
between cells, an agent packed several into different bits of one floating-point number. So the simulator gives no
lockstep, no precision below the noise, and nothing else to lean on, and the rules are built into the code:

- **`sheet.py` is the only code that knows there is a grid.** A rule (`rules/*.py`) declares its numbers, which of
  them its neighbours can see, and what every cell is born with, and one compiled function
  `update(me, mean, count, inp, out)`. It is given its own numbers, its neighbours' **mean** of each shared number,
  how many neighbours it has, and what the body delivered: nothing else. Not its position, the size, a clock, or any
  neighbour on its own.
- **A rule never holds a view into the sheet.** The engine copies a cell's numbers and its neighbours' means into the
  rule's own small arrays, and `test_rules.py` runs every rule with array bounds checked, so an index past the end
  can't reach another cell's numbers.
- **The engine does the rest.** The sheet runs in steps, 4 to each tick of the world; at each step each cell updates
  with some chance, never all at once. Every number a cell keeps gets a little noise at every update. What it shows
  its neighbours is cruder: every shared number is clipped to -1..1 and shown with noise of 1%, drawn afresh every
  step. So a shared number can't carry much: no encoding can squeeze information below the noise or spread it over
  orders of magnitude. Every cell is born from one birth vector, identical bar declared noise.
- **The body touches the brain only at cells, by the names they gave themselves:** `cells()`, `give()`, `get()`,
  `take()`. Only the cells named S1 and S2 get a stimulus, and only the cells named T get taste (+1 food, -1 poison,
  at the tick a block touches the mouth: it never says which sensor it is about); only M1 and M2 are read. Watching uses
  `view()`; the experimenter's `damage()` replaces cells with new-born ones. `test_rules.py` checks every rule's
  imports, signature and birth, and that no body code reaches inside.
- Numba-compiled: about 330,000 cell-updates a second on one core for the whole brain (about 150 steps, so 37 ticks
  of the world, a second at 49 × 49).

## What a cell can read from averages

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
- **Not the smallest.** A mean can't give the smallest of the neighbours' numbers. An earlier version found it by
  sharing exp(-5 d), with the noise added to d before the exp, so the tiny number shown was in effect free of noise:
  a cheat on the noise rule, withdrawn. Distances are now counted mod 5 (below).
- **Whole numbers.** What a cell keeps to itself is not limited: it keeps counts and timers as whole numbers,
  re-rounded at each update so its own small noise can't move them.

## What happens in a life

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

## The numbers a cell shares

28, each between -1 and 1 and seen only as averages over the neighbours, most of them in effect flags. The lizard
used 16, but not like for like: its cells saw each one through Sobel filters, which weight neighbours by where they
are, so they saw direction for free, in full-precision numbers with no noise on what neighbours show. Ours see no
direction at all, only means, so they build it from signals: the coordinates and the distance fields are most of the
28.
- where am I: 8 (the race's wave on two flags, hand, two edge labels, x, y, and the mark that places the organs);
- wiring: 9 for each of the two channels (five for the distance, three for the path, one for offers);
- learning: 2 (taste, shown by the T cells; ping, the wave that tells a sensor the other was stimulated since).

## Result

Three scores: how soon the sensors learn (set by the rules), and how much more food than poison the creature then
eats per 1,000 ticks and how many food blocks for each poison (set by the brain's behaviour and the body). 32 lives of
10,000 ticks with learning and 32 without, half with red as poison and half blue, each with its own random wiring
(`python creature.py --measure 32`). "Learned": both sensors' chance of firing both thrusters within 0.2 of right
(poison's at most 0.2, food's at least 0.8), counted from when the creature starts moving.

|  | learned | food minus poison per 1,000 ticks, by third of life after moving | food:poison, by third | firing both at the end |
|---|---|---|---|---|
| learning on | 24 of 32 lives, median 4,982 ticks | +0.25, +0.53, +0.89 | 1.5, 2.0, 3.0 | poison's sensor 0.17, food's 0.91 |
| learning off | none | 0, 0, 0 | 1.0 | both 0.50 |

Lives learn from taste alone: the brain works out which sensor a taste is about. An earlier version had the body hand
the taste to the eaten colour's sensor, which did that work for it (withdrawn: see `LESSONS.md`). Now a taste after
both colours were seen at once is sometimes credited to the wrong sensor, so p wanders a little near its target.
Learning is slow because meals are few, about 1.5 per 1,000 ticks: in 8 lives of 32 the sensors had not both come
right by 10,000 ticks. With p set perfect from birth by hand the creature eats 3.6, 2.7 and 4.8 food for each poison
by thirds (32 lives): the limit of this body with a brain this slow. The body is a triangle whose point is the mouth,
with small kicks that die away quickly. The square before it, whose whole front edge was the mouth and whose kicks
carried it into what lay ahead, ate nearly as much poison as food even with p perfect (`LESSONS.md`).
Once learned, the thirds differ much by noise: poison meals are few, and even 32 lives are few for this score.

## A second brain, for comparison: mixed signal

The same body and world can run a different brain (`python creature.py --brain mixed-signal`): a small circuit,
designed rather than grown, built from the one element of Ribar and Sepulchre's [Neuromorphic
Control](https://arxiv.org/abs/2011.04441) (`mixed_feedback.py`): a leaky node, and elements that each put a current
into a node, a sigmoid of a low-pass-filtered voltage, with a sign (positive or negative feedback) and a timescale.
Four excitable neurons, alike: two sensors and two motors. Each sensor excites the motor on its side (a coin toss at
birth) through a synapse that relays every spike, and the other through a plastic synapse whose strength p sets: at p
= 1 it relays nearly every spike, at 0 none, in between noise decides. The sensors hush each other: a sensor's spikes
charge a node that for about 10 ticks holds the other sensor down, so the creature heeds one colour at a time. The
circuit runs 4 of its ticks to each tick of the world, so its spikes come often and each kick is small. Learning is
three factors, all in the circuit: each sensor's spikes charge its eligibility node, which leaks away over 10 ticks,
and empty the other sensor's (cross-inhibition, so only the sensor that fired last is eligible); one taste node,
driven by the same taste input, charges or empties a capacitor holding p while taste is good or bad, as fast as
eligibility allows. p sets the plastic synapse's strength. Noise on every node makes the odd spontaneous spike, so a
creature that sees nothing still moves. It keeps the grown brain's symmetry: nothing in it says what a sensor senses
or what a motor does. Its panel in the live view shows each neuron's voltage, a white line at each spike. Its time is
continuous: its lives don't change with the integration step (DT 0.2 to 0.01), though its learning does depend on the
shape of the taste pulse (`LESSONS.md`). Compiled with numba, with the world, a life of 10,000 ticks takes about half
a second.

`--measure` runs both brains on the same lives (the same worlds and wirings):

|  | learned | food minus poison per 1,000 ticks, by third of life after moving | food:poison, by third |
|---|---|---|---|
| grown | 24 of 32 lives, median 4,982 ticks | +0.25, +0.53, +0.89 | 1.5, 2.0, 3.0 |
| mixed signal | 28 of 32 lives, median 3,622 ticks | +0.54, +1.23, +1.15 | 2.2, 5.9, 4.6 |

The mixed-signal brain moves from the first tick (the grown brain spends about 600 building itself), so its thirds
span the whole life; it reacts at once, where a pulse takes about 13 ticks to cross the grown brain; and its sensors
hush each other. Over 64 lives of 10,000 ticks it ate 4.3 food for each poison, 7.0 in the second half, and 14.8 with
p set perfect by hand; it nets about twice as much food as the grown brain. The comparison says what the sheet costs:
building takes time, and a big brain is slow.

## Next: mixed feedback, simplicity and recruitment

The mixed-signal brain does the job with a handful of neurons where the sheet uses thousands of cells, so the next
step explores brains built from mixed-feedback parts: evolved in graph form with a strong preference for simplicity,
and then, from a local perspective only, recruiting more parts in a life when the task needs them.
`MIXED_FEEDBACK.md` summarises the mixed-feedback approach (Sepulchre and colleagues), what is new in it and what it
suggests here; `RECRUITMENT.md` gathers how brains might recruit more computational power with no god, and the
phased plan.

## Damage

Press `d` in the live view to replace a disc of cells under the mouse with new-born ones, as with the lizard. A band 7
rows deep across the middle (6 lives of 6): the new cells relearn x and y within 90-180 steps, names are kept (or
retaken, where the band took one), and paths cut off from their source fade and regrow, so every route carries pulses
again (measured with an earlier version of the organs). Damage the organiser's corner (a disc of radius 4, 6 lives
of 6): it takes up beating again, at the same corner; but if its two coin-tossed neighbours went too, the toss can come
out the other way, and the sensors swap names, so each now gets the other colour and what each learned is about the
wrong one. Damage a sensor and a new cell takes the name, but what the old one had learned is gone.

## Not yet

- Odd sizes only, and tested at 49 × 49: on an even sheet the middle of an edge falls between two cells.
- Learning is slow, because meals are few: in 8 of 32 lives the grown brain had not learned by 10,000 ticks.
- A taste after both colours were seen at once can go to the wrong sensor, so the grown brain's p wanders a little
  near its target (0.17 and 0.91 at the end, where crediting by hand gives 0 and 1).
- In about 1 sheet in 32, two cells take the same actuator name (M1).
- The coordinates take about 1,500 steps to settle (they are averages, and averages spread slowly).
- 28 shared numbers: fewer would be better, though the lizard's 16 also carried direction, which ours must build.
- Every life starts from scratch: the brain builds itself again (about 2,500 steps, 600 ticks, before the creature moves), and
  the sensors learn again.

## Inside one cell

Everything a cell does, as a block diagram: the rule's three layers and their stages, with what each reads from its
neighbours' means and the body on the left, and what it shows its neighbours and gives the body on the right.

![What runs inside one cell: organs (the race, handedness, edge labels, coordinates, naming), the brain (choose,
taste, ping and learn, in sensors and T cells) and the wiring for each of the two channels](media/cell.svg)

## Files

| | |
|---|---|
| `creature.py` | a life (a body, a brain and the body's wiring), the live view, and the measurement |
| `world.py` | the world and the body: blocks, eyes, thrusters, mouth |
| `brains/grown.py` | the grown brain: the sheet, by the names its cells took |
| `brains/mixed_signal.py` | the mixed-signal brain: four excitable neurons |
| `brains/minimal.py` | the minimal brain: those neurons alone, driving at every block (the baseline for recruitment) |
| `brains/adjusting.py` | the minimal brain with every neuron adjusting its own excitability, all circuit (rung 0 of recruitment) |
| `recruit_test.py` | recruitment's local signals, watched from outside a circuit brain |
| `mixed_feedback.py` | the mixed-feedback element and circuit the mixed-signal brain is built from |
| `sheet.py` | the engine: the only code that knows the grid |
| `rules/organs.py` | where am I: the race, handedness, edge labels, coordinates, names |
| `rules/wiring.py` | growing paths and running pulses, built on `rules/organs.py` |
| `rules/brain.py` | choosing and learning, built on `rules/wiring.py` |
| `rules/see.py` | what cells read from averages, and the distance field and path signs the rules share |
| `test_rules.py` | checks every rule and every body file keep the rules |
| `test_compiled.py` | checks the compiled circuit (`mixed_feedback.py`) and eyes and mouth (`world.py`) against plain numpy versions |
| `watch.py`, `organs_test.py`, `wiring_test.py` | each stage on its own, live or measured |
| `diagram.py` | draws `media/cell.svg`, the diagram above (by hand from the rules: redraw it when one changes) |
| `schematic.py` | draws `media/mixed_signal.svg` and `.png`, the mixed-signal brain as a circuit (by hand: redraw it when the brain changes) |
| `LESSONS.md` | how it got here: what was tried, what failed and why |
| `MIXED_FEEDBACK.md` | the mixed-feedback approach (Sepulchre and colleagues): what is new in it, the literature, and what it suggests here |
| `RECRUITMENT.md` | how a brain might recruit more computational power locally, with no god: the literature, insights and plan |

## Licence

MIT: see `LICENSE`.
