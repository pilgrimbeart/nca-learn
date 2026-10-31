# nca-learn: brains that grow themselves and learn

Can a brain grow itself, emergently, and be useful? Grown, here, means built by local rules alone: nothing places
its parts, no unit sees the whole, and no god decides. Useful means capable of learning one bit of information during
its lifetime: here, which of two colours is food and which is poison.

It is an open-ended exploration, learning by doing, and it has gone beyond the cellular automata of its name; it may
yet loop back to them. Four lines of work so far:

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
- **Discrete circuits** ask the same of common parts (transistors, resistors, capacitors, diodes) on a coin cell,
  living closed loop in SPICE: first the simplest that forages, then one that learns the bit.

![A life with the sheet brain: the brain (left) builds a coordinate frame, names its organs and grows its wiring,
then the creature (right) learns which colour is food](media/life.gif)

## What we've learned

The findings that changed the direction of the work, each told in full in the notebook named.

- **The body must never do the brain's job.** Early on the body was changed to give food or poison only to the
  sensor whose colour was eaten. It looked like a simplification, since four mechanisms in the brain could go, but
  those mechanisms were the brain working out which sensor a taste was about (credit assignment), the hardest part
  of the task. The body was doing it instead. So whenever a change to the body lets the brain drop machinery, we ask
  where that machinery's job went (`NOTEBOOK.md`, Lessons).
- **Rules kept only in prose drift, so the code enforces them.** The sheet brain's central rule is that a cell sees
  only the average of what its neighbours show. Earlier experiments quietly broke it (reading one neighbour on its
  own), and nothing stopped them. Now each rule is built into the code's structure and tested, so breaking it fails
  loudly: the sheet's engine, the circuit brains' circuits, the minimal search's `check` (`NOTEBOOK.md`, Lessons).
- **In a circuit brain, nothing may happen outside the circuit.** The first recruitment rules were small programs
  running beside the circuit (keeping traces, thresholds, writing its settings from outside), so the program, not
  the circuit, did part of the work. The test now is: for every number that affects behaviour, which node holds it
  and which elements move it? If the answer is "the program", it isn't the circuit (`experiments/NOTEBOOK.md`,
  Lessons).
- **Find what the body allows before blaming the brain.** A scripted policy that is told the answer from birth and
  sees only what a brain would see shows the best any brain could do with that body. Twice this showed that the body,
  not the brain, was the limit: an early square body capped every brain, and the best circuits were driving the body
  badly (`NOTEBOOK.md`, The body; `minimal/NOTEBOOK.md`, M11).
- **Match the brain's speed to the body's.** A far block shows up as about one flash as the creature's narrow gaze
  sweeps past it, and the body keeps spinning for a while after a thruster stops. A brain that reacts briefly to each
  flash has lost the block before it can act. What works is a slow memory of the sighting that keeps the creature
  driving towards it for a fraction of a second (a *hold*), plus a timer that sends it off to explore after a long
  spell of seeing nothing (a *roam*). That more than doubled the best energy efficiency (`minimal/NOTEBOOK.md`, M11).
- **An average over lives hides the lives that fail.** The best circuits of one search ate plenty on average, yet in
  a fifth of their lives the creature ate what was near, then spun on the spot for the rest of its life (*stranding*);
  the other lives' meals hid it. It was found only by watching one life. Now each third of each life is charged for
  its own shortfall, the job limits stranded lives to 5%, and a behaviour is watched live before it is reported
  (`minimal/NOTEBOOK.md`, M8).
- **Noise costs no parts, so a search will use it.** Searching for the fewest parts, twice a part's job was handed to
  noise instead: a rhythm or an urge to explore that came from random jitter, not a clock. Such circuits work only
  at the noise level they were tuned at. So every circuit is judged with three noises: silicon's (about 280 times
  quieter than biology's at these currents, where any design that leans on noise fails), biology's, and twice
  biology's (`minimal/NOTEBOOK.md`, M7 and M12).
- **The body must vary from life to life, as the parts do.** Each life's circuit is built from parts with their own
  tolerances, so no design can lean on one exact resistor. The body had no such spread: every creature had the same
  strength, eyes and drag, and its two thrusters were identical to the last digit. An optimiser used that. A tuned
  9-part circuit that ignores its eyes, firing both thrusters 300 times a second, drove dead straight and ate four
  times as fast as any sighted circuit; with the thrusters 1% unequal, as any real pair would be, it drives in
  circles. The other way round, a learning circuit's straight run, pointed by chance along the world's axis, retraced
  one column it had eaten clear for its last 48 s, a stranding no built body would suffer. A circuit tuned on one
  exact body may be tuned to that body's accidents, so the body's dynamics need a spread of their own, like noise;
  and for every perfect symmetry in the simulation, ask whether a real body would have it (`discrete/NOTEBOOK.md`,
  D5, D9).
- **Declining poison isn't avoiding it, and an eaten-out patch needs leaving.** The learning circuit's only defence
  against poison was not to approach it; its mouth still ate whatever lay in its path. And eaten food reappears
  elsewhere, so a creature that eats every food near it and refuses the poison turns its patch into a poison patch,
  then circles there for the rest of its life. Both were found only by recording the nodes of the lives that failed.
  Two small additions cured both: the silenced eye's current, which had gone to ground, now turns the creature
  aside, and a few seconds with nothing seen sends it off straight (`discrete/NOTEBOOK.md`, D8).
- **A scripted policy ranks structures, not a circuit's values.** Rules that see only what a brain sees cost
  seconds a life against a circuit's minutes, and they ranked the ideas correctly: avoid poison, give up on an empty
  patch. Told the answer from birth, they also give a ceiling to measure a brain against. But their best speeds made
  the circuit worse, because a circuit's hold and drive don't behave like the rule's: values have to be found in
  the circuit itself (`discrete/NOTEBOOK.md`, D8).
- **Spinning faster doesn't see more.** The learning circuit scans by firing one thruster 54 times a second, which
  spins it nearly three turns a second. Each firing moves it along the same small circle whatever the rate, so it
  keeps re-sweeping the same view, and blocks flash past too fast for the eyes to fire. It sights food no more often
  than a policy scanning at 16 a second, so a quarter of its firings buy nothing. The circuit learns and approaches as
  well as the best policy; it loses on spending (`discrete/NOTEBOOK.md`, D10).
- **Design in a fast model of the circuit's blocks; use SPICE to check it's real.** A circuit lived in SPICE with
  real chip transistors takes minutes a life. Instead each block of the circuit (a timer, the oscillator, the
  learning node) is measured once on SPICE's bench and copied into a simple model as a few numbers, which lives a
  whole life in about a second, some 300 times faster. Its best design, built in transistors and lived in SPICE
  without retuning, did the job, at 80% of the score the model predicted; the gap was one timing quirk where two blocks
  meet (a thruster firing alone as a drive began), which no single block's bench showed. Close enough: ideas are
  tried, searched and judged in the model, and SPICE checks that a design is physically realisable, retuning it only
  when realism matters (`discrete/NOTEBOOK.md`, D12, D13).
- **Give every simulated life its own flaws, or an optimiser will find a knife-edge.** In the model every copy of a
  circuit was first identical. A search then set the learning threshold a hair below the most the learning node can
  ever reach: perfect in the model, but in real silicon each chip's parts differ a little, and in a quarter of the
  lives the bit could never flip. Now each life draws its own parts' errors (their spread measured in SPICE), and
  that design lost half its score while a sounder one lost nothing (`discrete/NOTEBOOK.md`, D13).
- **The same brain built of neuron-like elements costs 8 times the power of logic gates.** One design (B) was built
  three ways: as abstract blocks (timers, an oscillator, a tally), as Sepulchre's neuron-like elements (leaky nodes
  with fast positive and slow negative feedback), and as logic gates. Both lower levels did what the blocks
  predicted, so designing with blocks loses little and is fastest. But the neuron-like version needed 841 parts and
  31 nW against the gates' 151 and 3.7 nW: each element is an amplifier drawing current all the time, and its slow
  analogue signals are easily disturbed by noise, where gates swing rail to rail. What the elements offer instead is
  knobs a brain could turn to tune itself (`discrete/NOTEBOOK.md`, D14).
- **Within a life, the best tuning is small careful steps; the big search is evolution's.** A brain born with its
  spending settings (how long to chase, when to give up and explore) up to 3 times wrong can nudge each setting and
  keep the nudges that bring more meals per unit of energy, with no coordinator (each setting wiggling at its own
  moments and noticing whether things then went better than usual), and it recovers a third of what was lost in a
  long life. Hoping to find the best possible, we gave an idealised learner the same information (only its meals, what it
  saw and its own effort) and unlimited computing power to explore cleverly. It did no better, and worse where the
  settings matter little: meals come too rarely to tell good settings from bad ones far apart, so it kept exploring
  and paying for it. Exploring wildly early in life (annealing) hurt the simple tuner too. Finding good designs from
  scratch is for a search across many lives (evolution, or this project's searches); a life can only polish what it
  was born with, or rescue itself when something is badly wrong, like a lopsided body. So each problem has its
  solver (the user, 2026-10-30): what is the same in every life (how often meals come, how fast the body turns) is
  best set by evolution or design; what differs between lives but shows clearly in experience (which colour is
  food, a lopsided body) is best learned in the life; and what differs but barely shows (spending near its best) is
  best made not to matter: a design whose best is broad, as B's turned out to be (`discrete/NOTEBOOK.md`, D15).
- **A brain can grow a new reflex in its life, when something hurts that no sense predicts but an action can stop.** In
  an *arena* of robots that eat each other by biting tails, being bitten hurts (a bad taste), and the biter is behind,
  out of sight, so no sense can warn of it (the user's insight). Beside a brain evolution would build (one that steers
  towards tails), a generic *grower*, told nothing of what it is for, notices bad tastes no sense predicted, grows one
  new link from taste to the motors, and tries the simplest responses (fire one motor, the other, both, nothing),
  judging each by the taste of the moment after it. It found a turn, which breaks a bite at once, in 97% of lives, and
  gained three quarters of what the best designed reflex gains, judged on fresh arenas. Two things made it work: judging
  every bite rather than whole trials (lives are short), and a predictor that compares what follows a sense with what
  comes anyway. The obvious answer, speeding away, was worse than nothing: the biter just follows. Nor does it need a
  menu holding the answer: a recruit of two knobs (how hard to fire each motor when bitten), jittered at each bite and
  nudged towards whatever jitter tasted better, reached 86 to 97% of the best designed reflex, depending on where it
  started. (Those figures left out what firing costs. Since 2026-10-31 the robots are discs and firing is charged.
  Escape still grows and nets about as much as the best designed burst against the old tracker, and its control, pain
  no action can stop, now costs; but against a tracker whose fixed habits are tuned for the arena (evolution's part)
  it barely pays, +0.03 meals a 10 s: most of its value was the baseline's waste. A growth case must be judged against
  a well-tuned baseline: `discrete/NOTEBOOK.md`, D18.)
- **Learning which colour is food is a running tally of evidence, and in an unchanging world it shouldn't forget.**
  The learning node ("doubt") adds a step for each poison and takes one away for each food, and flips the creature's
  guess when the tally passes a threshold. Read as probability, each taste adds its evidence (the logarithm of how
  much likelier it is if the guess is wrong than if it's right), and the threshold is a decision. Since which colour
  is food never changes within a life, the tally should keep the trust that meals have built rather than leak it
  away: the version that keeps it was surely best, needed no time constant at all, and costs only 0.15 against being
  told the answer from birth (`discrete/NOTEBOOK.md`, D13).
- **A lopsided body defeats every fixed brain.** With each thruster drawn between half and twice its usual strength,
  every design, from either line, fell from about 2.2 to below 0.8 and stranded up to a quarter of its lives: a drive
  meant to go straight circles past its food. Told its body, the same brain recovers nearly everything by balancing its
  two thrusters, one number; but eight local rules for finding that number fell far short, because both eyes look down
  one corridor and nothing in it shows which way the creature curves (`discrete/NOTEBOOK.md`, D13;
  `minimal/NOTEBOOK.md`, M16). What does work, partly, is judging every drive rather than every meal: jitter the balance
  a little at each drive, and keep moving it the way the drives that kept their block in view longer went. That closes
  over a third of the gap in a short life, surely better than learning from meals (`discrete/NOTEBOOK.md`, D19). Far
  better still is learning a model of the body by prediction: turning with one thruster alone, the creature sees the
  same things come round again once a revolution, and how long a revolution takes says how strong that thruster is. With
  a few minutes of such sweeps, deliberate experiments of its own, it finds its body almost exactly and closes some 90%
  of the gap, surely beating every learner judged by outcomes. Sweeping only when it is eating badly costs an ordinary
  body nothing: it never sweeps, and once a lopsided body's drive is fixed the meals rise and the sweeps stop of
  themselves (`discrete/NOTEBOOK.md`, D20).
- **Behind these eyes, intelligence is worth about twice today's brains; the rest is what the eyes can't see.** A
  brain told every block's place does ten times better than our best. One told only the places of blocks its eyes
  have already seen, and remembering them, does twice as well: that is the most memory and reasoning can buy here.
  The rest is coverage: an eye sees a corridor 2 mm wide, so most blocks are never seen (`discrete/NOTEBOOK.md`, D13).
- **Check the simulator, not just the circuit.** A circuit simulator chooses its own time steps, within error limits.
  With ngspice's default limits, a transistor sitting right at its switch-on point turned on or not depending on
  where the steps happened to land, so results seemed to change with the step size. With the limits tightened,
  every step size agrees. Check that results converge in both step and error tolerance, on the first design that
  works, and distrust any design whose behaviour hangs on a knife-edge (`discrete/NOTEBOOK.md`, D7).
- **Real units show what abstract ones hide.** Written in seconds, amperes and farads, the circuits turned out to
  have a chip's sizes but biology's noise, a contradiction invisible while the units were abstract. Real units also
  give quick sanity checks (a chip can't make a resistance above about 100 GOhm) and a meaning to every number
  (`NOTEBOOK.md`, Lessons; `units.py`).
- **Count the cost as built.** The simulator first counted a circuit's power as the currents reaching its nodes. Built
  in real transistors, the same circuit drew 150 times as much, because every amplifier's bias and every mirrored copy
  of a current also flows from the supply. An optimiser told the wrong price buys the wrong things, so the price now
  comes from the transistor build, checked against SPICE (`minimal/NOTEBOOK.md`, M15).
- **Compare designs on the same lives, with an interval on the difference.** Lives vary a lot by luck. Two designs are
  compared on the same worlds (the same seeds), and one counts as better only if the 95% interval of their
  difference excludes zero; otherwise they are tied, and no order is claimed (`experiments/NOTEBOOK.md`, E0;
  `minimal/NOTEBOOK.md`, M9).

## The ground rules, for every brain

Every brain keeps the same ground rules, set out in `AGENTS.md`: the body talks to the brain only through two
sensors, two motors and one taste that never says which sensor it is about, and never does the brain's work (credit
assignment, timing, filtering); nor does the simulator, so there is no clock or lockstep, noise is everywhere, and a
result must hold at a finer step and on fresh lives; everything is local, with no god; and in a circuit brain
everything is explicit circuit, with noise modelled on biology's built into the simulator (Terms).

## The creature and its world

A disc whose front point is the mouth, with eyes looking ahead (one sensor for each colour) and a forward thruster on
each side of its rear rim: both thrusters together drive it straight ahead, one alone makes it veer. (It was a triangle
until 2026-10-31; the disc keeps the mouth where the point was, so every life is unchanged.) Red and blue blocks lie
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
  disc with its mouth marked by a dot on the rim the way it faces, its thrusters small squares on the rear rim, and what its eyes see: a pale beam ahead, the
  corridor its mouth will sweep, fading with distance, each of its rays stopping at the first block it meets (so a
  near block casts a shadow). A ring round a thruster shows it firing. "yuck!" is a poison meal.
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
survive it (`NOTEBOOK.md`, Noise as biology makes it). The results in this section were measured with the earlier
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
spec, `minimal/spec.py`), its parts counted as it is built in transistors on a 1.8 V supply (`chip.py`; SPICE checks
the build, `minimal/spice.py`). The task, body, interface and noise
are every brain's, and the rules against cheating the simulator are enforced in code (`AGENTS.md`). Circuits are
designed by hand, tuned (a polish, `minimal/search.py`), pruned part by part (`minimal/prune.py`) and searched by
evolution over topologies (`minimal/evolve.py`), all judged on fresh seeds with the noise of silicon, biology and
twice biology's (Terms: substrate).

What counts, among the circuits that do the job (learn the bit, eat enough, rarely strand): performance first (the
best driver for energy, body efficiency, and the best for speed and accuracy, gain rate, never traded against each
other), then power and area; the simplest brain behind them (Terms: what counts). The league (`minimal/LEAGUE.md`,
generated) names the best at each and how sure that is; the notebook (`minimal/NOTEBOOK.md`) tells how they were
found.

What it has found so far:

- **Built in transistors, a circuit costs what its supply delivers, 150 times what reached its nodes.** Lived closed
  loop in SPICE as SKY130 transistors, HR_31p_pol behaved as in the simulator, but its +-3 V supply delivered 1.76 uW,
  where the simulator had counted 12 nW: thinking cost more than moving. Now the simulator reckons the build's power
  (`chip.py`: element by element within 1% of SPICE, and a closed-loop life at 1.8 V 131 nW in SPICE against 130 in
  the simulator, behaviour tied) on SKY130's own 1.8 V supply, the memory is a SONOS cell that
  holds its bit (a capacitor written by transistors leaked it away in seconds), and parts are counted in transistors
  (`minimal/NOTEBOOK.md`, M15).
- **The simplest circuit that does the job, robustly, had 30 parts (counted as elements, before M15), and it is also among the best drivers.** Judged at
  one noise level, circuits of about 22 parts seemed to do it: the bit a perfect integrator (a floating gate) written
  by a three-factor rule (what was seen, times the taste), the creature spinning until food is in view. But their
  rhythm came from noise: in silicon, about 280 times quieter, they never get moving. Only the hold-and-roam circuit,
  whose scan is an oscillator and whose roam is a timer, does the job in silicon, biology and at twice biology's noise
  (35 parts: HR_si); open searches from it, within a chip's limits, took parts of its motor stage away and retuned the
  rest, and a polish and pruning one more: HR_31p_pol_pruned (30 parts, `media/HR_31p_pol_pruned.svg`, its
  signal-flow graph and schematic), with HR_31p_pol (31) the best driver yet (`minimal/NOTEBOOK.md`, M12-M14).

## Discrete circuits

Before getting clever about food and poison, what is the simplest circuit of common parts (2N3904 and 2N3906
transistors, resistors, capacitors, low-leakage diodes) that drives the body to food, and then the simplest that also
learns the bit? Each circuit is a netlist living closed loop in ngspice beside the body (`discrete/life.py`), each
seed with its own parts' tolerances, judged as the minimal search judges (`discrete/judge.py`, `discrete/poison.py`).
The notebook (`discrete/NOTEBOOK.md`) tells how they were found.

- **All food, 14 parts**: hold and drive (`media/hold_drive_14.svg`): an oscillator of a PNP and an NPN scans with
  one thruster; each pulse from an eye charges a hold capacitor through an emitter follower, and while it is charged
  the second thruster fires too, straight at the block. Efficiency 6.9, 72 nW. Fewer parts cost: 12 parts 6.6, 10
  parts (counter-turning, no hold) 4.3.
- **Blind, 9 parts**: an oscillator firing both thrusters 300 times a second eats four times as fast, as efficiently,
  but only because the simulated thrusters are identical (What we've learned).
- **A circuit doesn't need to tune itself to its body**, as far as tried: across bodies built differently (strength,
  eyes, drag, unequal thrusters) the best settings hardly move, except for unequal thrusters, and a trim for those
  can't be learned from a life's 200 meals more cheaply than it costs. Driving only while the eyes still see the
  block copes with them instead.
- **One bit, 46 parts** (`learn_avoid`, `media/learn_avoid.svg`): the eyes gated by a latch that two poisons in
  quick succession flip; once the eye it follows has seen nothing for a few seconds, both thrusters drive straight
  until the next sighting (giving up on an empty patch); and the eye it silences empties the hold, so poison ahead
  turns the creature aside. Held out (160 lives) it surely does the job: efficiency 1.78, gain 4.7 meals per 10 s,
  food:poison 4.7 in the last third, none stranded, 130 nW. Pruning took it from 48 parts and made it surely better
  on both measures. Its predecessor (`learn_hold`, 49 parts, a roam on a clock) stranded 3 lives in 64 and was
  surely less efficient (1.17). The same rules as policies, told the answer from birth, reach 2.7, and 2.3
  learning: the ceiling for this kind of brain on this body.

## Next

The open questions, most valuable first, are in [`QUESTIONS.md`](QUESTIONS.md).

## Terms

**Units** (the axioms: `units.py`)

- **Real units**: everything in SI, every number that can be derived derived from a few axioms (`units.py`).
- **Tick**: the body's step, 10 ms: the eyes look, the thrusters fire and the body moves once a tick (a reaction in 2
  to 4 ticks is an insect's). The circuit is integrated in steps of 0.125 ms, 80 to a tick. The live view shows real
  time at about 3 ticks a frame (it says how fast it runs against real time).
- **Supply**: the chip's, 1.8 V across (SKY130's core devices), analogue ground halfway. The **rails** a node stays
  within are the supply's, +-0.9 V; an output's current fades within a few hundredths of a volt of them.
- **Typical voltage**: a third of a rail, 0.3 V: the unit a design's voltages are reckoned in (a gate is open at it, a
  spike resets below minus it). The designs before 2026-10-26 were drawn at 1 V and +-3 V rails, and are converted.
- **Typical sizes**: what circuits are built around, as in subthreshold analogue silicon: a capacitor of 2.5 pF, a
  current of 0.3 nA (which moves it a typical voltage in 2.5 ms, the body's pulse) and a resistor of 1 GOhm. The body's
  pulses are 3 typical currents. The recruitment line's circuits keep a typical voltage of 1 V and a current of 1 nA:
  not yet built in transistors.

**Circuits and noise** (the model: `mixed_feedback.py`'s docstring)

- **Level 0, level 1**: nodes and elements; the motifs built from them.
- **Shot noise**: a current is carried by discrete events (ion channels opening, vesicles released, electrons
  crossing a transistor), so it flickers, with variance in proportion to its size, summed over all the currents on a
  node, not their net. A circuit can drown it by raising its currents only as the square root, for power in proportion.
- **Resting noise**: what a node has even when no net current flows. In biology, membrane noise: a node's capacitance
  is membrane area, whose channels flicker even at rest: noise in proportion to the capacitance, so a node k times
  bigger is quieter only by the square root of k. In silicon, a leak's thermal noise (kT/C). A memory node has none:
  still until written, then rough by the square root of what is written.
- **Mismatch**: no two parts are alike: every part off by about 10% of itself (offsets by a tenth of a typical
  voltage), drawn at birth, so
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

- **Parts**: as the circuit is built in transistors (`chip.py`'s blocks: an element a differential pair, its mirrored
  tail and outputs, a gate, preamplifier, level shifter or filter where it needs one): transistors, resistors,
  capacitors, diodes and bias sources.
- **Power**: what the supply delivers to the transistors: every bias, mirror copy and auxiliary amplifier, not only
  the currents into nodes (before 2026-10-26 only those were counted, 150 times too few).
- **Analogue ground**: 0 V, halfway between the rails: one buffer for the chip, to which every leak's resistor runs.
- **Memory node**: a SONOS cell (SKY130's flash transistor: charge trapped in nitride, held for years), its threshold
  the stored value, written by tunnelling through a pulse driver that fires only above 1% of the write's full current.
  Writing needs 10.5 V across the cell, from charge pumps or extra supplies: not yet in the power (a known anomaly).
- **The job**: learning the bit well enough (food:poison at least 3 in the last third of a life), eating enough (1
  food per 10 s) and rarely stranding (at most 5% of lives), with every substrate judged.
- **Stranding**: a life that eats, then finds nothing more (no food at all in its last third). A creature that
  travels only towards food it sees spins on the spot for ever once it has eaten what is near.
- **Buildable**: within a chip's limits (`units.py`), a rule since 2026-10-23: no resistance above about 77 GOhm, no
  capacitor above 50 pF, no time constant above about 3.9 s without a floating gate, no current below 1 pA.
- **Polish**: tuning a circuit's values (CMA-ES), each generation on fresh lives. **Pruning**: trying every single
  simplification (an element, a filter, a gate, a leak, a clamp taken away) and keeping the best that costs no more
  than a little, until none does.
- **Meals gained**: food, less 2 for each poison (as in the score).
- **Body efficiency**: meals gained per meal's worth of energy spent (a meal being worth 10 uJ): resting (1 uW, a
  meal every 10 s, whatever a creature does), moving (20 nJ a thruster firing) and thinking (the circuit's power, tens
  of nW: for HR_31p_pol about a sixth of what moving costs). Above 1 a creature gains. Haste wastes fuel and dawdling the resting cost,
  so a careful creature has a best speed.
- **Gain rate**: meals gained per 10 s, energy free: speed and accuracy.
- **What counts** (the user's order, 2026-10-27): among brains doing the job, performance (the best driver for
  energy, body efficiency, and the best for speed and accuracy, gain rate, each its own dimension, never traded), then
  power, then area (what it takes to build); simplicity (fewest parts) behind them, to understand a design. Evolution
  pays for power and material and rewards performance; it doesn't pay for elegance. (Until then, 2026-10-22 to 27:
  three objectives, the simplest brain, efficiency and gain rate, which the league still ranks.)
- **Thrift**: food per 1,000 thruster firings (fuel alone, time no object); shown, not ranked.
- **Area**: what a circuit would take on a chip, by analogy with subthreshold analogue CMOS, in unit transistors (15
  square microns each): an element 5 (a transconductance amplifier), a gate 3 more, a leak 2, a clamp 1, a memory
  node's floating gate 5, and each capacitor its own area as a MOS capacitor (5 fF per square micron: 2.5 pF is 33
  unit transistors). Capacitors dominate, as on real neuromorphic chips. Shown, not ranked.
- **Hold**, **roam** (the hold-and-roam circuit, HR): after a sighting of the food colour, a slow node keeps both
  thrusters firing together for a fraction of a second, so the creature goes on to the food instead of reacting for a moment and
  sweeping past it; after a long spell with nothing seen (a *giving-up time*, in foraging theory's terms), it drives
  straight off to look elsewhere. Matching
  the brain's speed to the body's sweep and momentum (impedance matching).
- **Policy**: a brain written as a few rules in code, not a circuit (`discrete/policies.py`): it gets the eyes'
  pulses and the taste and fires the thrusters, as any brain, with no parts, power or noise of its own. A life costs
  about a second against a circuit's minutes in SPICE, so policies rank ideas cheaply; told from birth which colour is
  food (`oracle`), a policy gives the ceiling for its kind of brain on this body. A rule's own values don't transfer to a
  circuit; a **fast model** does: a policy whose every part is a block of the circuit with the numbers measured on
  SPICE's bench, checked against the circuit's own lives (`discrete/NOTEBOOK.md`, D13).
- **Robust judging**: in the fast model, each life draws its own parts' errors (their spread over chips measured in
  SPICE), and its own body where an experiment says, instead of every copy being perfect and identical.
- **Doubt**: the learning node of the discrete circuits, a running tally of evidence that the creature's guess of the
  food colour is wrong; in probability's terms a log-odds, kept as a CUSUM (a tally that can't go below a floor,
  raising an alarm at a threshold: Page's 1954 test for a change).
- **Sepulchre's rules**: an experiment's constraint, every node leaky except memory nodes and no clamps (gates and
  floating-gate memories allowed).
- **Arena**: a world of ten robots and nothing else, each with a red mouth and a blue tail; a robot eats by holding
  its mouth on another's tail (a meal a second), which tastes good to the biter and bad to the bitten; an empty belly
  is death, and a newborn takes its place (`discrete/NOTEBOOK.md`, D18).
- **Grower**: generic machinery beside a brain that notices a gap (a bad outcome nothing predicted), grows a recruit
  where it is, and lets the recruit try the simplest operations, keeping what works; told nothing of what it is for.

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
python -m minimal.spice RESULTS.json --check  # build it in SKY130 transistors; each element against its formula
python -m minimal.sheets RESULTS.json  # its transistor schematics, sheet by sheet (media/NAME_transistors/)
python -m minimal.spice_life RESULTS.json --seeds 100:116  # live it in SPICE, closed loop, against the simulator
python -m discrete.watch           # discrete circuits live, ngspice beside the body (--circuit learn_avoid --poison)
python -m discrete.life hold_drive  # discrete circuits closed loop in SPICE (--set k=v: other values)
python -m discrete.tune hold_drive 20   # tune a discrete circuit's values (--poison: for one that learns)
python -m discrete.judge discrete/results/hold_drive_tuned.json  # on held-out seeds (--motors X: unequal thrusters)
python -m discrete.poison learn_avoid  # a learning circuit, each seed red then blue as poison
python -m discrete.model            # the fast model: circuit B from its SPICE bench, judged robustly (k=v: change a block)
python -m discrete.blocks 0:32 OUT.json  # bench circuit B's blocks in SPICE on 32 seeds' tolerances
python -m discrete.policies         # rules, not circuits, on the real body (and discrete.variation: bodies that differ)
python -m discrete.draw             # redraw media/hold_drive_14.svg and .png
python -m experiments.e1_oracle     # the rung-1 experiments, E1 to E7 (experiments/NOTEBOOK.md)
python -m experiments.h_run 64 1000 "share*"  # the healing experiments (H series): named rules, on the leaderboard
python measure_recruitment.py 32    # recruitment's local signals, neuron by neuron, watched from outside
python test_rules.py                # check every sheet rule keeps the sheet brain's rules
python test_compiled.py             # check the compiled circuit and eyes against plain numpy versions
python -m discrete.test_model       # check the fast model and circuit B are as benched and lived in SPICE
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
| `minimal/` | the minimal circuit search: `spec.py` (circuits as descriptions, the rules, scoring), `fastlife.py` (a whole life in one compiled call), `designs.py` (hand designs), `search.py` (polish), `prune.py`, `evolve.py` (open search), `league.py`, `check.py` (the real `Life` at two steps), `spice.py` (a circuit as SKY130 transistors, for ngspice), `sheets.py` (their schematics), `spice_life.py` (lives in SPICE, closed loop), `test_minimal.py`; its notebook `NOTEBOOK.md`, league table `LEAGUE.md`, results in `results/` |
| `discrete/` | discrete circuits: `life.py` (netlists of common parts, lives closed loop in ngspice, the bench), `circuits.py` (the designs), `cmos.py` (circuits in SKY130 CMOS: B), `model.py` (the fast model: B as its blocks' numbers), `blocks.py` (a circuit's blocks benched in SPICE, for the model), `tuner.py` (B tuning its own knobs), `test_model.py`, `policies.py` (rules, not circuits), `bodies.py` (bodies built differently), `variation.py`, `screen.py` (bench screening), `tune.py`, `prune.py` (pruning and the ladder), `judge.py` (held-out, paired), `poison.py` (lives with poison), `draw.py` (the schematic), `watch.py` (live); its notebook `NOTEBOOK.md`, results in `results/` |
| `experiments/` | the recruitment experiments (E series: the recruiting circuit; H series: the healing circuit), their lab notebook (`NOTEBOOK.md`) and leaderboard (`LEADERBOARD.md`) |
| `mixed_feedback.py` | the mixed-feedback element and circuit every circuit brain is built from |
| `chip.py` | how each part of a circuit is built in transistors: the blocks an element takes, and so the power the supply delivers |
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
| `QUESTIONS.md` | the open questions, most valuable first: parked mid-quest, removed when answered |
| `NOTEBOOK.md` | the lab notebook of the sheet brain, the body and the circuit simulator: what was tried, what failed and why |
| `MIXED_FEEDBACK.md` | the mixed-feedback approach (Sepulchre and colleagues): what is new in it, the literature, and what it suggests here |
| `RECRUITMENT.md` | how a brain might recruit more computational power locally, with no god: the literature, insights and plan |

## Licence

MIT: see `LICENSE`.
