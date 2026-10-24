# nca-learn: brains that grow themselves and learn

Can a brain grow itself, emergently, and be useful? Grown, here, means built by local rules alone: nothing places
its parts, no unit sees the whole, and no god decides. Useful means capable of learning one bit of information during
its lifetime: here, which of two colours is food and which is poison.

It is an open-ended exploration, learning by doing, and it has gone beyond the cellular automata of its name; it may
yet loop back to them. Three lines of work so far:

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
- **The minimal circuit search** drops every architectural constraint (no neurons, locality or growth) and asks how
  simple a circuit can be that learns the bit, and how well a circuit can drive the body, searching by hand and by
  optimisation.

![A life with the sheet brain: the brain (left) builds a coordinate frame, names its organs and grows its wiring,
then the creature (right) learns which colour is food](media/life.gif)

## The ground rules, for every brain

Every brain keeps the same ground rules, set out in `AGENTS.md`: the body talks to the brain only through two
sensors, two motors and one taste that never says which sensor it is about, and never does the brain's work (credit
assignment, timing, filtering); nor does the simulator, so there is no clock or lockstep, noise is everywhere, and a
result must hold at a finer step and on fresh lives; everything is local, with no god; and in a circuit brain
everything is explicit circuit, with noise modelled on biology's built into the simulator (Terms).

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

The first run after a brain's code changes pauses for 15-30 s while numba compiles it (the window says so); after
that it starts in about a second, from numba's cache.

In the live view:

| key | |
|---|---|
| `r` | a new life (a new seed, a new wiring; poison alternates red and blue) |
| `d` | damage the sheet brain: replace a disc of cells under the mouse with new-born ones |
| `b` | the next brain (the sheet brain, then the circuit brains in turn), in a new world with the same seed |
| `s` | the designed circuit's schematic (wheel: zoom, drag: pan, Esc: close) |
| `i` | the rules the simulation enforces: the interface, noise, limits, seeds, the job, the score, what is measured (wheel or up/down: scroll; numbers read from the code; "copy all" puts them on the clipboard as text, "open as text" opens them in a text viewer; `python creature.py --rules` prints them) |
| space | pause |
| up / down | faster / slower; below a tick a frame, down waits 2, 4 ... 32 frames per tick |
| `a` | automatic speed again (slow while the sheet brain wires itself and first moves, fast otherwise) |
| Esc | quit |

### What you're seeing

- **Left, the brain.** For the sheet brain (49 × 49 cells):
  - a faint **checkerboard**: the coordinates each cell has worked out for itself (x and y, each running from -1 to
    1 across the sheet), in squares of about 4 cells;
  - its organs, labelled with the names they gave themselves, **S1** and **S2** (the sensors, on one edge), between
    them **T** (taste: white while it shows a taste), and **M1** and **M2** (the actuators, its motors, on the
    opposite edge), and then with what the body wired them to this life: **red** or **blue** (the sensor that sees
    that colour, with its chance of firing both thrusters, which it has learned) and **left** or **right** (the
    thruster it drives);
  - **paths**: sky blue from the sensors to M1, orange to M2; **pulses** running down them, white.

  For a circuit brain: each neuron's voltage (sky blue), a white line at each spike.
- **Right, the world:** red blocks and blue blocks, lettered R and B, and the creature, a
  triangle pointing the way it faces, its point (the mouth) marked, and what its eyes see: a pale beam ahead, the
  corridor its mouth will sweep, fading with distance, each of its rays stopping at the first block it meets (so a
  near block casts a shadow). A ring at a corner of the tail shows that thruster firing. "yuck!" is a poison meal.
- **Below:** the tick, the stage of life, which colour is poison this life, and the recent meals; and buttons for `b`,
  `i` and `s` (above). The life waits while the rules or the schematic are open. The window can be resized or
  maximised: the panels stay square, centred, and the block view takes the rest.
- **At the bottom, for the circuit brains, the block view** (`blocks.py`): the brain at level 1, found from its
  netlist and drawn live. Neurons are circles (brightness: voltage; white: a spike), synapses arrows (solid excites,
  dashed inhibits, thickness: current), and every other node a meter hung where it belongs (on the synapse it gates,
  or by the neuron it acts on), with the eyes, thrusters and taste at the edges. A unit grown in the life (the
  recruiting circuit's bridge, the healing circuit's recruits) appears as a new circle, outlined for a while. A
  circuit with no neurons to find (the minimal search's) gets the **node view** instead: level 0, every node a circle
  (a memory a square), every element an arrow, a dotted line from the node that gates it, a loop for a node's
  feedback on itself.

For the sheet brain, the view runs at 10 ticks a frame, but slows to 1 while the paths grow and until a little after
the creature starts moving, so the pulses can be seen running down them. A life goes: "where am I" (to about 4.5 s),
"wiring", then "moving and learning". Within a few tens of seconds the poison sensor's chance of firing both
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
  noise rule to get it: `LESSONS.md`). Distances are counted mod 5 instead (below).
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
the taste to the eaten colour's sensor, which did that work for it (withdrawn: see `LESSONS.md`). Now a taste after
both colours were seen at once is sometimes credited to the wrong sensor, so p wanders a little near its target.
Learning is slow because meals are few, about 1.5 per 10 s: in 8 lives of 32 the sensors had not both come
right by 100 s. With p set perfect from birth by hand the creature eats 3.6, 2.7 and 4.8 food for each poison
by thirds (32 lives): the limit of this body with a brain this slow (earlier bodies capped it lower: `LESSONS.md`).
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

## The circuit brains

Built from the one element of Ribar and Sepulchre's [Neuromorphic Control](https://arxiv.org/abs/2011.04441)
(`mixed_feedback.py`; the approach and its literature in `MIXED_FEEDBACK.md`): leaky nodes, and elements that each put
a current into a node, a sigmoid of a filtered voltage, with a sign (positive or negative feedback) and a timescale,
perhaps gated by another node. Level 0 is nodes and elements; level 1, the motifs built from them (neurons, synapses,
the states they hold), as the block view draws them. A memory node (a knob) holds its value, noisy only when written.
Every circuit brain shares two sensor neurons, two motor neurons and a taste node (`brains/circuit.py`), is integrated
in steps of 0.125 ms (80 to each 10 ms tick of the world), and has noise and mismatch as a substrate makes them
(Terms). Each eye fires at random moments, at a rate set by what it sees, and each pulse (a taste too) starts at a
moment of its own within the tick. Compiled with numba, with the world, a life of 100 s takes about a second.

**Under biological noise every hand-built circuit brain falls to about 1 food for each poison** (2026-10-20): 10%
mismatch pushes a share of their excitable neurons into firing on their own or missing pulses, and none was built to
survive it (`LESSONS.md`, Noise as biology makes it). The results in this section were measured with the earlier
noise (a fixed noise per node, no mismatch), and stand only for it until these brains are rebuilt on a neuron that
survives mismatch.

### The designed circuit, for comparison

Designed by hand rather than grown (`python creature.py --brain designed-circuit`; its schematic: `s` in the live view,
or `media/designed_circuit.png`), it says what growing costs. Four excitable neurons, alike: two sensors and two motors.
Each sensor excites the motor on its side (a coin toss at birth) through a synapse that relays every spike, and the
other through a plastic synapse whose strength p sets: at p = 1 it relays nearly every spike, at 0 none, in between
noise decides. The sensors hush each other: a sensor's spikes charge a node that for about 0.1 s holds the other
sensor down, so the creature heeds one colour at a time. Its spikes come often and each kick is small. Learning is three
factors, all in the circuit: each sensor's spikes charge its eligibility node, which leaks away over 0.1 s, and empty
the other sensor's (cross-inhibition, so only the sensor that fired last is eligible); one taste node, driven by the
same taste input, charges or empties a capacitor holding p while taste is good or bad, as fast as eligibility allows. p
sets the plastic synapse's strength. Noise on every node makes the odd spontaneous spike, so a creature that sees
nothing still moves.

Under the earlier noise, on the same 32 lives as the sheet brain (`--measure 32`), it learned in 28 (median 36
s) and ate 2.2, 5.9 and 4.6 food for each poison by thirds of life, netting about twice the sheet brain's food: it
moves from the first tick (the sheet spends about 6 s building itself), reacts at once where a pulse takes about 0.13
s to cross the sheet, and its sensors hush each other. So building costs time, and a big brain is slow.

### Recruitment: growing in the life

The recruitment series (the ideas and plan in `RECRUITMENT.md`; the experiments in `experiments/NOTEBOOK.md`) climbs a
ladder from a brain that can't learn at all, each step measured against the one below:

| brain | what it is |
|---|---|
| baseline circuit (`brains/baseline.py`) | the designed circuit's four neurons alone, each sensor driving both motors, taste going nowhere: drives at every block (the baseline) |
| adjusting circuit (`brains/adjusting.py`) | rung 0: each neuron adjusts its own excitability from taste (a knob); cuts poison by a third, by ignoring rather than avoiding |
| knowing circuit (`brains/knowing.py`) | the starting animal: the baseline circuit plus a taste neuron, T, that learns what predicts pain but has no outputs; it knows, but behaves exactly as the baseline circuit |
| recruiting circuit (`brains/recruiting.py`) | rung 1, guided: T's frustration grows a *bridge* on the poison sensor's pathway that lets the knowledge act |
| healing circuit (`brains/healing.py`) | rung 1 by a generic recruit that knows nothing of the circuit, choosing among actions on what it is attached to |
| healing cascade (the same file) | the first recruit can't reach the cure; frustrated itself, it grows a second, one step further out, which can |

Under the earlier noise (`experiments/LEADERBOARD.md`), a recruit that knows nothing of what the circuit does matched
the guided bridge, and settled better: it found the bridge's function ("gate the poison eye's synapse to a motor") out
of its menu in every life. The cascade found the cure one step further out in about 60% of lives, and nothing grew in
all-food lives.

## The minimal circuit search

How simple can a circuit be that learns the bit, and how well can a circuit drive the body? No neurons, locality or
growth are required: a circuit is any nodes and elements of `mixed_feedback.py`, written as a plain description (a
spec, `minimal/spec.py`), its parts counted as an analogue build would need them. The task, body, interface and noise
are every brain's, and the rules against cheating the simulator are enforced in code (`AGENTS.md`). Circuits are
designed by hand, tuned (a polish, `minimal/search.py`), pruned part by part (`minimal/prune.py`) and searched by
evolution over topologies (`minimal/evolve.py`), all judged on fresh seeds with the noise of silicon, biology and
twice biology's (Terms: substrate).

Three objectives, each among the circuits that do the job (learn the bit, eat enough, rarely strand), never traded
against each other: the simplest brain, the best driver for energy (body efficiency) and the best for speed and
accuracy (gain rate). The league (`minimal/LEAGUE.md`, generated) names the best at each and how sure that is;
the notebook (`minimal/NOTEBOOK.md`) tells how they were found.

What it has found so far:

- **The simplest circuit that does the job, robustly, has 30 parts, and it is also among the best drivers.** Judged at
  one noise level, circuits of about 22 parts seemed to do it: the bit a perfect integrator (a floating gate) written
  by a three-factor rule (what was seen, times the taste), the creature spinning until food is in view. But their
  rhythm came from noise: in silicon, about 280 times quieter, they never get moving. Only the hold-and-roam circuit,
  whose scan is an oscillator and whose roam is a timer, does the job in silicon, biology and at twice biology's noise
  (35 parts: HR_si); open searches from it, within a chip's limits, took parts of its motor stage away and retuned the
  rest, and a polish and pruning one more: HR_31p_pol_pruned (30 parts, `media/HR_31p_pol_pruned.svg`, its
  signal-flow graph and schematic), with HR_31p_pol (31) the best driver yet (`minimal/NOTEBOOK.md`, M12-M14).
- **Match the brain's speed to the body's.** Spinning sweeps the eyes' narrow corridor past far food faster than a
  brief reaction can catch it. A slow node that holds the course for some ticks after a sighting, and a timer that
  sends the creature off to roam after a long spell of seeing nothing (the hold-and-roam circuit), more than doubled
  the best efficiency.
- **Noise costs no parts, so a search judged at one noise level buys it**: pruning twice replaced a mechanism (a clock,
  a hunger) by noise doing the job at the nominal level only. Hence judging with three noises: silicon's (about 280
  times quieter than biology's at these currents, so a design that needs noise fails there), biology's, and twice
  biology's.

## Next

- **Object persistence**: a creature that has just lost sight of food sweeps back for it (the body can turn both
  ways), the user's idea.
- **Reversal**: every circuit so far learns only from food, so none unlearns when the poison colour swaps.
- **A smaller robust circuit still**: the open search again, from HR_31p_pol_pruned.
- **Sepulchre's discipline**: do circuits of mixed-feedback components (every node leaky, events from positive
  feedback) do the job as simply? The first three-arm experiment settled nothing (`MIXED_FEEDBACK.md`): it needs a
  start built of his components.
- **Recruitment under biological noise**, on a neuron that survives mismatch; and a recruit that walks
  (`RECRUITMENT.md`).
- **Back to the sheet**: cellular automata again, with what the circuits have taught.

## Terms

**Units** (the axioms: `units.py`)

- **Real units**: everything in SI, every number that can be derived derived from a few axioms (`units.py`).
- **Tick**: the body's step, 10 ms: the eyes look, the thrusters fire and the body moves once a tick (a reaction in 2
  to 4 ticks is an insect's). The circuit is integrated in steps of 0.125 ms, 80 to a tick. The live view shows real
  time at about 3 ticks a frame (it says how fast it runs against real time).
- **Typical sizes**: what circuits are built around, as in subthreshold analogue silicon: a current of 1 nA, a
  capacitor of 2.5 pF (which 1 nA moves 1 V in 2.5 ms, the body's pulse) and a resistor of 1 GOhm.

**Circuits and noise** (the model: `mixed_feedback.py`'s docstring)

- **Level 0, level 1**: nodes and elements; the motifs built from them.
- **Shot noise**: a current is carried by discrete events (ion channels opening, vesicles released, electrons
  crossing a transistor), so it flickers, with variance in proportion to its size, summed over all the currents on a
  node, not their net. A circuit can drown it by raising its currents only as the square root, for power in proportion.
- **Resting noise**: what a node has even when no net current flows. In biology, membrane noise: a node's capacitance
  is membrane area, whose channels flicker even at rest: noise in proportion to the capacitance, so a node k times
  bigger is quieter only by the square root of k. In silicon, a leak's thermal noise (kT/C). A memory node has none:
  still until written, then rough by the square root of what is written.
- **Mismatch**: no two parts are alike: every part off by about 10% of itself (offsets by 0.1 V), drawn at birth, so
  no design can lean on exact values or exact cancellations.
- **Substrate**: whose noise a circuit lives with, never none: **biology** (shot noise in events of 12.5 fC, between
  an ion channel's and a vesicle's, and membrane noise), **silicon** (single electrons and a leak's thermal noise:
  about 280 times quieter in amplitude at these currents) and **biology x2** (twice biology's, a margin).

**Recruitment**

- **Recruit**: a unit grown in the life, attached locally. A **bridge** is the recruiting circuit's: a neuron that
  splits a synapse. The healing circuit's recruit is generic: it attaches to the frustrated unit and its one-edge
  neighbours, and has a **menu** (inhibit or excite one of them, or turn down one of their synapses).
- **Frustration**: a unit's slow node that fills when pain it anticipated comes anyway; past a threshold it triggers
  growth.
- **Eye**: in the experiments, a sensor neuron by the colour it sees this life (the *poison eye*): the measurement's
  name, never the brain's.
- **Rung**: a step on recruitment's ladder: rung 0, a unit adjusts itself; rung 1, it recruits a link.
- **Win-stay lose-shift**: how a healing recruit chooses: an option latches on and stays until the tastes that follow
  it tire it out, then another wins. Judged by the **share** of bad tastes after it, not their rate.
- **Healing**: recruitment pictured as an inflammation and healing response: the damage is the frustration, the
  recruit the repair.
- **Wave**: how many hand-offs a recruit is from the first frustrated unit. A wave-1 recruit still frustrated long
  after it came is frustrated itself and grows wave 2, one step further out. A **cascade** is that hand-off.

**The minimal circuit search** (the rules: `AGENTS.md`)

- **Parts**: capacitors, resistors, diodes and transistors, counted as an analogue build would need them.
- **The job**: learning the bit well enough (food:poison at least 3 in the last third of a life), eating enough (1
  food per 10 s) and rarely stranding (at most 5% of lives), with every substrate judged.
- **Stranding**: a life that eats, then finds nothing more (no food at all in its last third). A creature that
  travels only towards food it sees spins on the spot for ever once it has eaten what is near.
- **Buildable**: within a chip's limits (`units.py`), a rule since 2026-10-23: no resistance above about 74 GOhm, no
  capacitor above 50 pF, no time constant above about 3.7 s without a floating gate, no current below 1 pA.
- **Polish**: tuning a circuit's values (CMA-ES), each generation on fresh lives. **Pruning**: trying every single
  simplification (an element, a filter, a gate, a leak, a clamp taken away) and keeping the best that costs no more
  than a little, until none does.
- **Meals gained**: food, less 2 for each poison (as in the score).
- **Body efficiency**: meals gained per meal's worth of energy spent (a meal being worth 10 uJ): resting (1 uW, a
  meal every 10 s, whatever a creature does), moving (20 nJ a thruster firing) and thinking (the circuit's power, a few
  nW, for today's circuits a hundredth of moving). Above 1 a creature gains. Haste wastes fuel and dawdling the resting cost,
  so a careful creature has a best speed.
- **Gain rate**: meals gained per 10 s, energy free: speed and accuracy.
- **The three objectives**: the simplest brain doing the job (fewest parts), the best driver for energy (body
  efficiency) and the best for speed and accuracy (gain rate), each its own dimension, never traded.
- **Thrift**: food per 1,000 thruster firings (fuel alone, time no object); shown, not ranked.
- **Area**: what a circuit would take on a chip, by analogy with subthreshold analogue CMOS, in unit transistors (15
  square microns each): an element 5 (a transconductance amplifier), a gate 3 more, a leak 2, a clamp 1, a memory
  node's floating gate 5, and each capacitor its own area as a MOS capacitor (5 fF per square micron: 2.5 pF is 33
  unit transistors). Capacitors dominate, as on real neuromorphic chips. Shown, not ranked.
- **Hold**, **roam** (the hold-and-roam circuit, HR): after a sighting of the food colour, a slow node keeps both
  thrusters firing together for a fraction of a second, so the creature goes on to the food instead of reacting for a moment and
  sweeping past it; after a long spell with nothing seen, a timer sends it straight off to look elsewhere. Matching
  the brain's speed to the body's sweep and momentum (impedance matching).
- **Sepulchre's rules**: an experiment's constraint, every node leaky except memory nodes and no clamps (gates and
  floating-gate memories allowed).

**Names**: in prose "the sheet brain", "the designed circuit", "the knowing circuit"; on the command line `sheet`,
`designed-circuit`, `knowing-circuit` and so on. Recruitment's baseline, the **baseline circuit**, was called the
minimal circuit until 2026-10-21; "minimal" now means only the minimal circuit search (`minimal/`). A minimal-search
design is named by its origin and its parts (EF_22p: 22 parts, from the open search EF), with `_pol` once polished and
`_pruned` once pruned.

## Other commands

```bash
python creature.py --seed 3         # a particular life
python creature.py --measure 32     # every brain, 32 lives each with learning and 32 without, headless
                                    # (--brains to choose; --all-food: lives where both colours are food)
python creature.py --brain baseline-circuit   # the baseline for recruitment: drives at every block
python creature.py --brain adjusting-circuit  # rung 0: each neuron adjusts its own excitability
python creature.py --brain knowing-circuit    # the starting animal: knows what predicts pain, acts on nothing
python creature.py --brain recruiting-circuit # rung 1, guided: grows the bridge that lets that knowledge act
python creature.py --brain healing-circuit    # rung 1 by a generic recruit that knows nothing of the circuit
python creature.py --brain healing-cascade    # the first recruit can't help; a second, further out, can
python creature.py --spec minimal/results/N_E1_23p.json --brain N_E1_23p  # a circuit of the minimal search, live
python -m minimal.search RESULTS.json 60   # the minimal search: polish a circuit, then prune it
                                    # (--by efficiency|gain: for one objective; default the score)
python -m minimal.prune RESULTS.json  # prune alone
python -m minimal.evolve 60 --start RESULTS.json ...  # the open search over topologies
                                    # (--name NAME --resume: carry on after a stop, from its last save)
python -m minimal.league            # its league table (minimal/LEAGUE.md)
python -m minimal.check RESULTS.json  # a circuit in the real Life at two integration steps
python -m minimal.physical RESULTS.json  # could it be built? its parts in real units against a chip's limits
python -m minimal.draw RESULTS.json  # draw a circuit (media/NAME.svg): its signal-flow graph and its schematic
python -m experiments.e1_oracle     # the rung-1 experiments, E1 to E7 (experiments/NOTEBOOK.md)
python -m experiments.h_run 64 1000 "share*"  # the healing experiments (H series): named rules, on the leaderboard
python measure_recruitment.py 32    # recruitment's local signals, neuron by neuron, watched from outside
python test_rules.py                # check every sheet rule keeps the sheet brain's rules
python test_compiled.py             # check the compiled circuit and eyes against plain numpy versions
python watch.py organs              # one stage of the sheet brain on its own (organs, wiring; --show picks the numbers)
python measure_organs.py            # when the coordinates and names come right, life by life
python measure_wiring.py            # pulses sent from S1 and S2: how many arrive, and how soon
python diagram.py                   # redraw media/cell.svg, what runs inside one cell
python schematic.py                 # redraw media/designed_circuit.svg and .png, the designed circuit's schematic
                                    # (needs pip install schemdraw cairosvg pillow)
python creature.py --record frames  # save a life's frames as PNGs, headless (media/life.gif: --seed 0 --seconds 100,
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
| `brains/baseline.py` | the baseline circuit: those neurons alone, driving at every block (the baseline for recruitment) |
| `brains/adjusting.py` | the adjusting circuit: every neuron adjusting its own excitability (rung 0 of recruitment) |
| `brains/knowing.py` | the knowing circuit: the baseline circuit plus a taste neuron that learns what predicts pain but has no outputs (recruitment's starting animal) |
| `brains/recruiting.py` | the recruiting circuit: the knowing circuit growing, in its life, the bridge that lets its knowledge act (rung 1) |
| `brains/healing.py` | the healing circuit and cascade: rung 1 by a generic recruit that knows nothing of the circuit |
| `measure_recruitment.py` | recruitment's local signals, watched from outside a circuit brain |
| `blocks.py` | the block view: a circuit brain at level 1 (neurons, synapses, the states they hold), live; and the node view, level 0, for circuits without neurons |
| `minimal/` | the minimal circuit search: `spec.py` (circuits as descriptions, the rules, scoring), `fastlife.py` (a whole life in one compiled call), `designs.py` (hand designs), `search.py` (polish), `prune.py`, `evolve.py` (open search), `league.py`, `check.py` (the real `Life` at two steps), `test_minimal.py`; its notebook `NOTEBOOK.md`, league table `LEAGUE.md`, results in `results/` |
| `experiments/` | the recruitment experiments (E series: the recruiting circuit; H series: the healing circuit), their lab notebook (`NOTEBOOK.md`) and leaderboard (`LEADERBOARD.md`) |
| `mixed_feedback.py` | the mixed-feedback element and circuit every circuit brain is built from |
| `sheet.py` | the engine: the only code that knows the grid |
| `rules/organs.py` | where am I: the race, handedness, edge labels, coordinates, names |
| `rules/wiring.py` | growing paths and running pulses, built on `rules/organs.py` |
| `rules/brain.py` | choosing and learning, built on `rules/wiring.py` |
| `rules/see.py` | what cells read from averages, and the distance field and path signs the rules share |
| `rules/interface.py` | the signature every rule's compiled update has (so numba can cache the sheet) |
| `test_rules.py` | checks every sheet rule and every body file keep the rules |
| `test_compiled.py` | checks the compiled circuit (`mixed_feedback.py`) and eyes and mouth (`world.py`) against plain numpy versions |
| `watch.py`, `measure_organs.py`, `measure_wiring.py` | each stage on its own, live or measured |
| `diagram.py` | draws `media/cell.svg`, the diagram above (by hand from the rules: redraw it when one changes) |
| `schematic.py` | draws `media/designed_circuit.svg` and `.png`, the designed circuit's schematic (by hand: redraw it when it changes) |
| `AGENTS.md` | the rules, for agents and people: principles, honesty, every brain's constraints, how to work here |
| `LESSONS.md` | how it got here: what was tried, what failed and why |
| `MIXED_FEEDBACK.md` | the mixed-feedback approach (Sepulchre and colleagues): what is new in it, the literature, and what it suggests here |
| `RECRUITMENT.md` | how a brain might recruit more computational power locally, with no god: the literature, insights and plan |

## Licence

MIT: see `LICENSE`.
