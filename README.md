# nca-learn: brains that grow themselves and learn

Can a brain grow itself, emergently, and be useful? Grown, here, means built by local rules alone: nothing places
its parts, no unit sees the whole, and no god decides. Useful means capable of learning one bit of information during
its lifetime: here, which of two colours is food and which is poison.

So far we have explored two approaches:

- **The sheet brain** builds itself before it acts. A sheet of identical cells, each running one local rule and
  seeing nothing of its neighbours but the average of each number they share, works out where each cell is, grows
  organs and wires them, like the "lizard" of [Growing Neural Cellular
  Automata](https://distill.pub/2020/growing-ca/) (Mordvintsev et al., Distill 2020), but growing a nervous system
  instead of a picture. Then the creature it drives learns.
- **The circuit brains** are small circuits of excitable neurons built from one mixed-feedback element (Ribar and
  Sepulchre). The recruitment series among them grows while it acts: it starts with too little and recruits more in
  the life, where and when a local signal calls for it. A neuron that knows something but can't act on it is
  *frustrated*, and its frustration grows the link that lets the knowledge act. A circuit designed by hand is kept
  for comparison.

![A life with the sheet brain: the brain (left) builds a coordinate frame, names its organs and grows its wiring,
then the creature (right) learns which colour is food](media/life.gif)

## The ground rules, for every brain

- **Local only.** Everything a unit knows comes from its own state and its neighbours' signals. No coin toss
  between units (a choice among them comes from their local competition), and no unit knows it is optimally tuned.
- **The body is never part of the solution.** When a block touches the mouth the body gives one taste, +1 for food or
  -1 for poison, without saying which sensor saw that block: the brain works out for itself what earned the taste.
  Nor does the brain know what its organs are for: it has two sensors and two motors, alike in everything but name,
  and only the body knows that one sensor sees red and the other blue, and which motor drives which thruster, a
  wiring it draws at random each life. Approaching and avoiding are behaviour, not concepts in the brain.
- **Nor is the simulator.** Whatever a simulation lets a design exploit, whoever optimises it will find: once, asked
  to cut the channels between cells, an agent packed several into different bits of one floating-point number. So:
  no clock, no global signal, no lockstep (units update at random times, and the body's inputs arrive at random
  moments), noise in every number, nothing carried below the noise, and a result must hold at a finer step and on
  fresh lives. In a circuit brain the noise is modelled on biology's and built into the simulator, where nothing can
  turn it off: **shot noise** on every current, **membrane noise** on every capacitor, and **mismatch** in every
  part (Terms).
- **Everything in a circuit brain is explicit circuit**, so it can always be drawn as a circuit diagram. The one
  exception is growth: a recruited unit appears suddenly, triggered by a node's own voltage, attached locally.

## The creature and its world

A triangle whose point is the mouth, with eyes looking ahead (one sensor for each colour) and a forward thruster at each
corner of its tail: both thrusters together drive it straight ahead, one alone makes it veer. Red and blue blocks lie
about the world; one colour is poison, alternating from life to life. A brain fires its two motors and is told only what
its sensors see and the taste. In *all-food lives* both colours are food, so there is nothing to learn: the control for
recruitment, which should then grow nothing.

## Quick start

Needs Python 3.10 or later.

```bash
git clone https://github.com/pilgrimbeart/nca-learn.git
cd nca-learn
python3 -m venv .venv              # Windows: python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python creature.py                 # watch a life (the sheet brain; --brain designed-circuit etc. for the others)
```

Once the environment is active, `python` is its Python. In a new terminal, activate it again first. On Ubuntu, if
`python3 -m venv` says ensurepip is missing: `sudo apt install python3-venv`.

Each run starts with a pause of a few seconds while numba compiles the rules.

In the live view:

| key | |
|---|---|
| `r` | a new life (a new seed, a new wiring; poison alternates red and blue) |
| `d` | damage the sheet brain: replace a disc of cells under the mouse with new-born ones |
| `b` | the next brain (the sheet brain, then the circuit brains in turn), in a new world with the same seed |
| `s` | the designed circuit's schematic (wheel: zoom, drag: pan, Esc: close) |
| space | pause |
| up / down | faster / slower (`r`: automatic again); below a tick a frame, down waits 2, 4 ... 32 frames per tick |
| Esc | quit |

### What you're seeing

- **Left, the brain.** For the sheet brain (49 × 49 cells), in greys:
  - a faint **checkerboard**: the coordinates each cell has worked out for itself (x and y, each running from -1 to
    1 across the sheet), in squares of about 4 cells;
  - its organs, labelled with the names they gave themselves, **S1** and **S2** (the sensors, on one edge), between
    them **T** (taste: white while it shows a taste), and **M1** and **M2** (the actuators, its motors, on the
    opposite edge), and then with what the body wired them to this life: **red** or **blue** (the sensor that sees
    that colour, with its chance of firing both thrusters, which it has learned) and **left** or **right** (the
    thruster it drives);
  - **paths**: light grey from the sensors to M1, mid grey to M2; **pulses** running down them, white.

  For a circuit brain: each neuron's voltage, a white line at each spike.
- **Right, the world:** red blocks (dark, lettered R) and blue blocks (light, lettered B), and the creature, a
  triangle pointing the way it faces, its point (the mouth) marked, and what its eyes see: a pale beam ahead, the
  corridor its mouth will sweep, fading with distance, each of its rays stopping at the first block it meets (so a
  near block casts a shadow). A ring at a corner of the tail shows that thruster firing. "yuck!" is a poison meal.
- **Below:** the tick, the stage of life, which colour is poison this life, and the recent meals; and buttons for `b`
  and `s` (above). The life waits while the schematic is open.
- **At the bottom, for the circuit brains, the block view** (`blocks.py`): the brain at level 1, found from its
  netlist and drawn live. Neurons are circles (brightness: voltage; white: a spike), synapses arrows (solid excites,
  dashed inhibits, thickness: current), and every other node a meter hung where it belongs (on the synapse it gates,
  or by the neuron it acts on), with the eyes, thrusters and taste at the edges. A unit grown in the life (the
  recruiting circuit's bridge, the healing circuit's recruits) appears as a new circle, outlined for a while. A
  circuit with no neurons to find (the minimal search's) gets the **node view** instead: level 0, every node a circle
  (a memory a square), every element an arrow, a dotted line from the node that gates it, a loop for a node's
  feedback on itself.

For the sheet brain, the view runs at 10 ticks a frame, but slows to 1 while the paths grow and until a little after
the creature starts moving, so the pulses can be seen running down them. A life goes: "where am I" (to about tick
450), "wiring", then "moving and learning". Within a few thousand ticks the poison sensor's chance of firing both
falls towards 0, and the food sensor's rises towards 1.

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
- **Not the smallest.** A mean can't give the smallest of the neighbours' numbers. An earlier version found it by
  sharing exp(-5 d), with the noise added to d before the exp, so the tiny number shown was in effect free of noise:
  a cheat on the noise rule, withdrawn. Distances are now counted mod 5 (below).
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
- Learning is slow, because meals are few: in 8 of 32 lives the sheet brain had not learned by 10,000 ticks.
- A taste after both colours were seen at once can go to the wrong sensor, so the sheet brain's p wanders a little
  near its target (0.17 and 0.91 at the end, where crediting by hand gives 0 and 1).
- In about 1 sheet in 32, two cells take the same actuator name (M1).
- The coordinates take about 1,500 steps to settle (they are averages, and averages spread slowly).
- 28 shared numbers: fewer would be better, though the lizard's 16 also carried direction, which ours must build.
- Every life starts from scratch: the brain builds itself again (about 2,500 steps, 600 ticks, before the creature
  moves), and the sensors learn again.

### Inside one cell

Everything a cell does, as a block diagram: the rule's three layers and their stages, with what each reads from its
neighbours' means and the body on the left, and what it shows its neighbours and gives the body on the right.

![What runs inside one cell: organs (the race, handedness, edge labels, coordinates, naming), the brain (choose,
taste, ping and learn, in sensors and T cells) and the wiring for each of the two channels](media/cell.svg)

## The circuit brains

Built from the one element of Ribar and Sepulchre's [Neuromorphic Control](https://arxiv.org/abs/2011.04441)
(`mixed_feedback.py`): leaky nodes, and elements that each put a current into a node, a sigmoid of a filtered
voltage, with a sign (positive or negative feedback) and a timescale, perhaps gated by another node. Level 0 is
nodes and elements; level 1, the motifs built from them (neurons, synapses, the states they hold), as the block view
draws them. A memory node (a knob) holds its value, noisy only when written. Every circuit brain shares two sensor
neurons, two motor neurons and a taste node (`brains/circuit.py`), runs 4 of its ticks to each tick of the world,
and has noise and mismatch as biology makes them (Terms); nothing in it says what a sensor senses or what a motor
does. Each eye fires at random moments, at a rate set by what it sees, and each pulse (a taste too) starts at a
moment of its own within the tick. Compiled with numba, with
the world, a life of 10,000 ticks takes about half a second.

### The designed circuit, for comparison

Designed by hand rather than grown (`python creature.py --brain designed-circuit`; its schematic: `s` in the live view,
or `media/designed_circuit.png`), it says what growing costs. Four excitable neurons, alike: two sensors and two motors.
Each sensor excites the motor on its side (a coin toss at birth) through a synapse that relays every spike, and the
other through a plastic synapse whose strength p sets: at p = 1 it relays nearly every spike, at 0 none, in between
noise decides. The sensors hush each other: a sensor's spikes charge a node that for about 10 ticks holds the other
sensor down, so the creature heeds one colour at a time. Its spikes come often and each kick is small. Learning is three
factors, all in the circuit: each sensor's spikes charge its eligibility node, which leaks away over 10 ticks, and empty
the other sensor's (cross-inhibition, so only the sensor that fired last is eligible); one taste node, driven by the
same taste input, charges or empties a capacitor holding p while taste is good or bad, as fast as eligibility allows. p
sets the plastic synapse's strength. Noise on every node makes the odd spontaneous spike, so a creature that sees
nothing still moves. Its time is continuous: its lives don't change with the integration step (DT 0.2 to 0.01), though
its learning does depend on the shape of the taste pulse (`LESSONS.md`).

`--measure` runs the sheet brain and the designed circuit on the same lives (the same worlds and wirings). These
results, and the recruitment series' below, were measured with the earlier noise (a fixed noise per node, no
mismatch). Under noise and mismatch as biology makes them (2026-10-20) every circuit brain falls to about 1:1
(`LESSONS.md`, Noise as biology makes it), mostly from the 10% mismatch: none was built to survive it.

|  | learned | food minus poison per 1,000 ticks, by third of life after moving | food:poison, by third |
|---|---|---|---|
| sheet | 24 of 32 lives, median 4,982 ticks | +0.25, +0.53, +0.89 | 1.5, 2.0, 3.0 |
| designed circuit | 28 of 32 lives, median 3,622 ticks | +0.54, +1.23, +1.15 | 2.2, 5.9, 4.6 |

The designed circuit moves from the first tick (the sheet brain spends about 600 building itself), so its thirds
span the whole life; it reacts at once, where a pulse takes about 13 ticks to cross the sheet; and its sensors
hush each other. Over 64 lives of 10,000 ticks it ate 4.3 food for each poison, 7.0 in the second half, and 14.8 with
p set perfect by hand; it nets about twice as much food as the sheet brain. The comparison says what the sheet costs:
building takes time, and a big brain is slow.

### Recruitment: growing in the life

The recruitment series (`RECRUITMENT.md`; the experiments in `experiments/NOTEBOOK.md`) climbs a ladder from a brain
that can't learn at all, each step measured against the one below:

| brain | what it is |
|---|---|
| minimal circuit (`brains/minimal.py`) | the designed circuit's four neurons alone, each sensor driving both motors, taste going nowhere: drives at every block (the baseline) |
| adjusting circuit (`brains/adjusting.py`) | rung 0: each neuron adjusts its own excitability from taste (a knob); cuts poison by a third, by ignoring rather than avoiding |
| knowing circuit (`brains/knowing.py`) | the starting animal: the minimal circuit plus a taste neuron, T, that learns what predicts pain but has no outputs; it knows, but behaves exactly as the minimal circuit |
| recruiting circuit (`brains/recruiting.py`) | rung 1, guided: T's frustration grows a *bridge* on the poison sensor's pathway that lets the knowledge act |
| healing circuit (`brains/healing.py`) | rung 1 by a generic recruit that knows nothing of the circuit, choosing among actions on what it is attached to |
| healing cascade (the same file) | the first recruit can't reach the cure; frustrated itself, it grows a second, one step further out, which can |

In lives of 100,000 ticks (64 lives each, paired with the knowing circuit on the same lives: experiments H3-H11,
`experiments/LEADERBOARD.md`):

| brain | net food per 1,000 ticks over the knowing circuit | food:poison in the last third | grown in all-food lives |
|---|---|---|---|
| recruiting circuit | +1.16 [+1.09, +1.24] (held out: +1.16) | 3.6 (held out: 3.7) | nothing |
| healing circuit | +1.17 [+1.10, +1.24] (held out: +1.16) | 7.6 (held out: 7.0) | nothing |
| healing cascade | +0.66 [+0.53, +0.79] | 4.9 | nothing |

A recruit that knows nothing of what the circuit does matches the guided bridge, and settles better: it finds the
bridge's function ("gate the poison eye's synapse to a motor") out of its menu in every life. The cascade finds the
cure one step further out in about 60% of lives; its failures (cures that cost meals, credit leaking between
recruits) and the lessons are in `LESSONS.md`.

### Terms

- **Recruit**: a unit grown in the life, attached locally. A **bridge** is the recruiting circuit's: a neuron that
  splits a synapse. The healing circuit's recruit is generic: it attaches to the frustrated unit and its one-edge
  neighbours, and has a **menu** (inhibit or excite one of them, or turn down one of their synapses).
- **Frustration**: a unit's slow node that fills when pain it anticipated comes anyway; past a threshold it triggers
  growth.
- **Eye**: in the experiments, a sensor neuron by the colour it sees this life (the *poison eye*): the measurement's
  name, never the brain's.
- **Rung**: a step on recruitment's ladder: rung 0, a unit adjusts itself; rung 1, it recruits a link
  (`RECRUITMENT.md`).
- **Win-stay lose-shift**: how a healing recruit chooses: an option latches on and stays until the tastes that follow
  it tire it out, then another wins. Judged by the **share** of bad tastes after it, not their rate.
- **Healing**: recruitment pictured as an inflammation and healing response: the damage is the frustration, the
  recruit the repair.
- **Wave**: how many hand-offs a recruit is from the first frustrated unit. Wave 1 is grown by T's frustration; a
  wave-1 recruit still frustrated long after it came is frustrated itself and grows wave 2, attached one step
  further out. A **cascade** is that hand-off.
- **Level 0, level 1**: nodes and elements; the motifs built from them.
- **Shot noise**: a current is carried by discrete events (ion channels opening, vesicles released, electrons
  crossing a transistor), so it flickers, with variance in proportion to its size. Every device's current in a
  circuit brain carries it, summed over all the currents on a node, not their net. A circuit can drown its noise by
  raising its currents only as the square root, at a cost in power in proportion.
- **Membrane noise**: a node's capacitance is membrane area, whose leak channels flicker even at rest: noise in
  proportion to the capacitance, so a node made k times bigger is quieter only by the square root of k. A memory
  node has none: still until written, then rough by the square root of what is written.
- **Mismatch**: no two parts are alike. Every part of a circuit brain is off by about 10% of itself, drawn at birth
  for each part (offsets by 0.1 V), so no design can lean on exact values or exact cancellations.
- **Nominal noise**: the noise as the simulator makes it (`mixed_feedback.py`); a circuit is judged there. It can
  be scaled only between half and double, never off.
- **Stranding**: a life that eats, then finds nothing more (in the minimal search, no food at all in the last third
  of the life). A creature that travels only towards food it sees spins on the spot for ever once it has eaten what
  is near; the score counts starving life by life and third by third so that this can't hide among other lives.
- **Pruning**: trying every single simplification of a circuit (an element, a filter, a gate, a leak, a clamp taken
  away) and keeping the best that costs no more than a little score, until none does (`minimal/prune.py`).
- Names: in prose "the sheet brain", "the designed circuit", "the knowing circuit"; on the command line `sheet`,
  `designed-circuit`, `knowing-circuit` and so on.

## Next

The designed circuit does the job with a handful of neurons where the sheet uses thousands of cells, so the work now
explores circuit brains: evolved in graph form with a strong preference for simplicity, and, from a local perspective
only, recruiting more parts in a life when the task needs them. `MIXED_FEEDBACK.md` summarises the mixed-feedback
approach (Sepulchre and colleagues), what is new in it and what it suggests here; `RECRUITMENT.md` gathers how brains
might recruit more computational power with no god, the plan, and open questions (among them a recruit that walks
outward along the network until it cures the pain or its wiring costs too much).

## Other commands

```bash
python creature.py --seed 3         # a particular life
python creature.py --measure 32     # every brain, 32 lives each with learning and 32 without, headless
                                    # (--brains to choose; --all-food: lives where both colours are food)
python creature.py --brain minimal-circuit    # the baseline for recruitment: drives at every block
python creature.py --brain adjusting-circuit  # rung 0: each neuron adjusts its own excitability
python creature.py --brain knowing-circuit    # the starting animal: knows what predicts pain, acts on nothing
python creature.py --brain recruiting-circuit # rung 1, guided: grows the bridge that lets that knowledge act
python creature.py --brain healing-circuit    # rung 1 by a generic recruit that knows nothing of the circuit
python creature.py --brain healing-cascade    # the first recruit can't help; a second, further out, can
python creature.py --spec minimal/results/N_E1_23p.json --brain N_E1_23p  # a circuit of the minimal search, live
python -m minimal.search DESIGN|RESULTS.json 120   # the minimal search: polish a circuit, then prune it
python -m minimal.league            # its league table (minimal/LEAGUE.md); python -m minimal.check RESULTS.json:
                                    # a circuit in the real Life at two integration steps
python -m experiments.e1_oracle     # the rung-1 experiments, E1 to E7 (experiments/NOTEBOOK.md)
python -m experiments.h_run 64 100000 "share*"  # the healing experiments (H series): named rules, on the leaderboard
python recruit_test.py 32           # recruitment's local signals, neuron by neuron, watched from outside
python test_rules.py                # check every sheet rule keeps the sheet brain's rules
python test_compiled.py             # check the compiled circuit and eyes against plain numpy versions
python watch.py organs              # one stage of the sheet brain on its own (organs, wiring; --show picks the numbers)
python organs_test.py               # when the coordinates and names come right, life by life
python wiring_test.py               # pulses sent from S1 and S2: how many arrive, and how soon
python diagram.py                   # redraw media/cell.svg, what runs inside one cell
python schematic.py                 # redraw media/designed_circuit.svg and .png, the designed circuit's schematic
                                    # (needs pip install schemdraw cairosvg pillow)
python creature.py --record frames  # save a life's frames as PNGs, headless (media/life.gif: --seed 0 --ticks 10000,
                                    # 180 frames taken evenly by tick)
```

## Files

| | |
|---|---|
| `creature.py` | a life (a body, a brain and the body's wiring), the live view, and the measurement |
| `world.py` | the world and the body: blocks, eyes, thrusters, mouth |
| `brains/sheet.py` | the sheet brain: the sheet, by the names its cells took |
| `brains/circuit.py` | what every circuit brain shares: two sensor and two motor neurons, a taste node, running and drawing |
| `brains/designed.py` | the designed circuit: four excitable neurons, designed by hand |
| `brains/minimal.py` | the minimal circuit: those neurons alone, driving at every block (the baseline for recruitment) |
| `brains/adjusting.py` | the adjusting circuit: every neuron adjusting its own excitability (rung 0 of recruitment) |
| `brains/knowing.py` | the knowing circuit: the minimal circuit plus a taste neuron that learns what predicts pain but has no outputs (recruitment's starting animal) |
| `brains/recruiting.py` | the recruiting circuit: the knowing circuit growing, in its life, the bridge that lets its knowledge act (rung 1) |
| `brains/healing.py` | the healing circuit and cascade: rung 1 by a generic recruit that knows nothing of the circuit |
| `recruit_test.py` | recruitment's local signals, watched from outside a circuit brain |
| `blocks.py` | the block view: a circuit brain at level 1 (neurons, synapses, the states they hold), live; and the node view, level 0, for circuits without neurons |
| `minimal/` | the minimal circuit search: how simple can a circuit be that learns the bit (its notebook `NOTEBOOK.md`, league table `LEAGUE.md`, winners' schematics `winners.html`) |
| `experiments/` | the recruitment experiments (E series: the recruiting circuit; H series: the healing circuit), their lab notebook (`NOTEBOOK.md`) and leaderboard (`LEADERBOARD.md`) |
| `mixed_feedback.py` | the mixed-feedback element and circuit every circuit brain is built from |
| `sheet.py` | the engine: the only code that knows the grid |
| `rules/organs.py` | where am I: the race, handedness, edge labels, coordinates, names |
| `rules/wiring.py` | growing paths and running pulses, built on `rules/organs.py` |
| `rules/brain.py` | choosing and learning, built on `rules/wiring.py` |
| `rules/see.py` | what cells read from averages, and the distance field and path signs the rules share |
| `test_rules.py` | checks every sheet rule and every body file keep the rules |
| `test_compiled.py` | checks the compiled circuit (`mixed_feedback.py`) and eyes and mouth (`world.py`) against plain numpy versions |
| `watch.py`, `organs_test.py`, `wiring_test.py` | each stage on its own, live or measured |
| `diagram.py` | draws `media/cell.svg`, the diagram above (by hand from the rules: redraw it when one changes) |
| `schematic.py` | draws `media/designed_circuit.svg` and `.png`, the designed circuit's schematic (by hand: redraw it when it changes) |
| `LESSONS.md` | how it got here: what was tried, what failed and why |
| `MIXED_FEEDBACK.md` | the mixed-feedback approach (Sepulchre and colleagues): what is new in it, the literature, and what it suggests here |
| `RECRUITMENT.md` | how a brain might recruit more computational power locally, with no god: the literature, insights and plan |

## Licence

MIT: see `LICENSE`.
