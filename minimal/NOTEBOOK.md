# The minimal circuit: lab notebook

The question (the user's, 2026-10-20): how simple can a creature be that learns one bit in its life (which colour is
poison), designed by hand as a proxy for evolution, or found by search? Simple means as few parts as possible, and
those parts as simple as possible. A detour from the mixed-feedback (Sepulchre) programme: no neurons, locality or
growth required. What is found is to be mapped back onto it afterwards.

## Definitions (fixed before any results)

- **The task is unchanged.** The same world and body, and the same interface: the body injects a pulse into one of
  two sensor nodes when that sensor's colour is seen, counts the spikes of two motor nodes (one thruster kick per
  spike), and injects one taste pulse (+ food, - poison) into a taste node after a meal. The wiring of colours to
  sensors and thrusters to motors is drawn at random each life, and poison alternates red and blue.
- **The honesty rules stay** (AGENTS.md): noise on every node, a result must hold on fresh seeds and with mismatch
  (every parameter off by about 3% at birth, offsets by 0.03 V), and at a finer step and other noise levels.
  *From M7 (2026-10-20):* noise and mismatch as biology makes them, built into the simulator (below), mismatch 10%,
  and judged at the nominal noise only (the user's decision).
- **The substrate** is level 0 of `mixed_feedback.py`, read as an analogue circuit: a node is a capacitor, with a
  resistor to a rail if it leaks and a diode per clamp; an element is a transistor (a transconductor: a current
  gain x f(slope x (V - offset)), f a sigmoid or tanh), with a second in series if gated, and a resistor and capacitor
  if its input is filtered. **Parts** = capacitors + resistors + diodes + transistors (`minimal/spec.py`).
- **The noise** is the simulator's: a current of fixed size on every node (`noise = 0.2`), so a smaller capacitor's
  voltage jitters more, as thermal noise on a real one would. It is free: no part pays for it. Because a design may
  use it (to explore, say), every result is also checked at half and double it. *From M7:* shot noise on every
  device current and membrane noise in proportion to capacitance (README, Terms; `mixed_feedback.py`), so quiet
  costs power and size; inputs at random moments within the tick.
- **The score**, per 1,000 ticks of life: food - 2 x poison - 2 x (food short of 1). A circuit that ignores taste
  scores below 0 (lived paired, red and blue as poison on the same seed, it nets -(what it eats)), one that never
  moves -2; only learning scores above 0. Plain net (food - poison) rewarded eating more as much as eating better: a
  first search shrank the motors' capacitors until noise fired them constantly, and ate 17 food and 13 poison per
  1,000 ticks (food:poison 1.4). Without the starving term, the search stood still (0 beats any movement before
  learning).
- **Does the job**: on held-out lives (64 seeds x 2, seeds the search never saw), with mismatch, at least 1 food
  per 1,000 ticks and food:poison of at least 3 over the last third of a 10,000-tick life. For scale, the designed
  circuit: 78 parts (11 nodes, 24 elements), score +0.70, food 1.27, poison 0.28, last third 5.07.

## Method

1. **A lower bound from necessity**: what any solution must have.
2. **An upper bound by construction**: a hand design that does the job.
3. **Pruning from above**: remove one part or merge two, retune, keep it if the job is still done.
4. **An open search over topologies**, for designs the reasoning missed.

Tools: `minimal/fastlife.py`, a whole life in one compiled call, the same life as `creature.Life` tick for tick
(checked: identical meals); `minimal/spec.py`, circuits as plain descriptions, parts counted, lives scored;
`minimal/search.py`, CMA-ES on the score, each generation on fresh seeds (the same for every candidate), then
held-out lives (at three noise levels until M7, at the nominal noise since); `minimal/prune.py` (from M7), method 3
made a standard step at the end of every polish: every single simplification tried on paired lives, the best kept
while the score stays within 0.1 of where it started; `minimal/designs.py`, the circuits.

## M1: design A, by hand (27 parts)

Six nodes: two sensors (capacitors), two motors (resting below threshold, so a kick gives one spike), taste, and a
memory node m holding the bit. Each sensor drives its own motor; the other motor through m (sensor 0 while m is
high, sensor 1 while it is low: the element's input is m, its gate the sensor). A good taste after a sensor was
active (the write element's filtered input: the eligibility) moves m towards it. 6 elements.

- With the sensors and taste resting at 0, noise held their gates (clip 0..1) a little open: m filled with no meal.
  Rested below 0.
- Then nothing fired the motors with nothing in view, and the creature never moved: **exploring needs a source of
  spontaneous movement**, which here can only be noise (or an oscillator). Motor leak and capacitance became
  parameters.
- Tuned (CMA-ES, 60 generations of 16 candidates on 8 fresh seeds x 2 each, mismatch 0.03) at the usual noise only,
  it does the job there (score +0.68, food 1.71, poison 0.52, last third 4.10) but not at half noise (it hardly
  moves: food 0.02) or double (it races: food 6.7, poison 6.2). With nothing in view only noise fires its motors,
  and the rate at which noise carries a node over a threshold is steep in the noise level: **a design that explores
  by noise is tuned to one noise level**, the simulator as part of the solution. So: trained with each life at a
  noise level of its own (from half to double, the pair sharing it), and judged at all three.
- Retuned so: at half noise food 0.92 (short of 1), at double last third 2.12 (short of 3). Close, not done.
- The designed circuit, for scale, under the same test (held out, mismatch 0.03): score -0.13, last third 2.05 at
  the usual noise (5.07 without mismatch): it was tuned by hand without mismatch.

## M2: spin and search (design C, 29 parts)

A robust explorer needs a clock: a relaxation oscillator, firing at a rate its own parts set. Delayed self-inhibition
alone (two time constants, negative feedback only) settles instead of cycling; it needs fast positive feedback too:
a neuron biased to fire on its own (2 elements on a node). At bias -1 it fired 216-233 times per 1,000 ticks at half,
the usual and double noise (and stuck high, depolarisation block, at bias 0 and above). So: motor 1 is the clock,
and the creature circles, its eyes sweeping all round; seeing food kicks motor 0 too, and it drives straight at it;
seeing poison leaves it circling, so it turns away. The bit says which sensor kicks motor 0.
- Tuned across noise levels (60 generations): it eats robustly (food 1.45, 1.49, 1.73 at half, usual and double
  noise), so the clock works; and does the job at half and the usual noise (last third 4.21, 3.80), but not at
  double (1.76). Traced: at double noise the memory wanders (0.08, 0.46, 0, 0.02, 1.0 over one life). The tuned
  taste node leaks slowly (R 6.7), so its voltage is noisy, and at double noise noise lifts it past 0 often enough
  to open the write gates; the sensors likewise. **A gate (clip 0..1) is a soft threshold that noise opens**: a
  quieter node needs a bigger capacitor, which a pulse then lifts less. The taste and sensor capacitances became
  parameters.
- Retuned from there (80 generations, 12 seeds x 2 each): **design C does the job at all three noise levels**, 29
  parts (`minimal/results/C_tuned.json`). Held out, mismatch 0.03:

  | noise | score | food | poison | food:poison, last third |
  |---|---|---|---|---|
  | x 0.5 | +0.68 [+0.52, +0.85] | 1.62 | 0.47 | 4.95 |
  | x 1 | +0.78 [+0.63, +0.91] | 1.72 | 0.47 | 5.16 |
  | x 2 | +0.58 [+0.39, +0.77] | 1.93 | 0.67 | 3.21 |

## The lower bound: what any solution needs

Counting parts as above, every solution must have:

1. **The two sensor nodes and the taste node**, each a capacitor and a resistor (each must recover after its pulse):
   6 parts. They can't be one node: the taste would arrive as if seen, or the colours as one.
2. **Two motor outputs that spike repeatedly.** A node spikes when it rises through 0 having been below -1, so a
   motor needs no neuron: a node resting below -1 gives one spike per kick. A motor may even be a sensor node itself
   (the pulse is the kick), but then whatever drives that motor also looks, to anything reading the node, like that
   sensor seeing its colour: credit is confused (M1, design A's merged variants test it).
3. **A memory**: a node holding the bit for a life, a capacitor with no leak (1 part), or a bistable node (more).
4. **A write**: the bit must change only when a taste follows one sensor's activity, which needs an element whose
   current depends on both: a gated element (2 parts) at least, and a time constant spanning the delay between
   seeing a block and tasting it (a tick or two): the sensor node's own decay, or a filter (2 parts).
5. **A read** in both directions: each sensor's effect on the motors must depend on the bit, so at least one
   element per sensor involving the memory, gated (2 x 2 parts), for a full flip. One element can give a default
   guess (one colour avoided from birth) that evidence corrects only half the time (M2's variants test it).
6. **A way to explore that doesn't hang on the noise level.** With nothing in view only noise or a clock can fire
   a motor, and noise's rate of crossing a threshold is steep in its level (M1). A clock is a relaxation
   oscillator: a node with fast positive and slow negative feedback (2 elements, one filtered: 4 parts), which can
   be a motor node itself.

Together: 6 + 2 + 2 (the two motor nodes) + 1 + 2 + 4 + 4 = **21 parts at the least**, with no clamps and the
eligibility in a sensor's own decay; 19 if a motor is merged into a sensor (with credit confused). Design C's
simplest variant (no clamps, one write, no filter: C1) has exactly 21. So if C1 does the job, it is minimal within
this argument, and the open search (step 4) tests the argument itself: whether something smaller, of a kind not
foreseen here, does it too.

## M3: pruning design C

Each variant tuned from C's values (60 generations, 12 seeds x 2), judged as before:

| variant | parts | change from C | does the job? |
|---|---|---|---|
| C2 | 23 | no clamps, no filter (eligibility in the sensor's own decay) | **yes**: score +0.50, +0.70, +0.21 at the usual, half and double noise; last third 3.68, 5.83, 3.02 |
| C1 | 21 | no clamps, no filter, one write (good tastes, after sensor 0) | no: last third 1.75 at the usual noise |
| C1f | 23 | no clamps, one write, filter kept | no: learns nothing (food:poison exactly 1.00) |
| Cc1f | 25 | one write, clamps and filter kept | no: the same |

- **A default guess can't learn from good tastes in spin and search.** One write starts from a guess (sensor 1 is
  food) and moves the bit on a good taste after sensor 0. When the guess is wrong, the food is the colour it circles
  away from, so it never tastes it and never corrects. But it does eat the poison it wrongly approaches: so a
  one-write learner should write on bad tastes (variant b). And a better write element for noise: the taste node as
  the element's input, through a steep threshold below its rest, and the sensor as its gate, instead of the taste
  node as a gate (clip 0..1, which noise opens).
- Variant b (bad-taste writes; the taste node the write's input through a steep threshold, the sensor its gate),
  tuned from C's values, 80 generations:

  | variant | parts | usual noise | half | double | does the job? |
  |---|---|---|---|---|---|
  | C1b (one write) | 21 | score +0.61, last third 4.10 | +0.60, 3.25 | -0.06, 1.81 | no (double) |
  | C2b (two writes) | 23 | +0.62, 4.94 | +0.50, 4.18 | +0.14, 2.53 | no (double) |

- **A one-write learner can't undo a mistake.** Traced at double noise: in lives where C1b's guess was right, the
  bit crept up (0, 0.06, 0.52, 1.47, 2.47, 7.78 in one life) as poison meals were credited to the food's sensor
  (seeing food at the moment of a bad taste, or noise holding its gate a little open); with one write it only
  rises, and once past 1/2 the creature approaches the poison, whose bad tastes (after the other sensor) write
  nothing. At the usual noise it does the job, at the lower bound of 21 parts; at double, the missing way back
  shows. Several tuned values sat on their bounds (the write gain, the taste node's rest; in C2 the clock's gain and
  time constant): bounds widened, C1b and C2b retuned.
- Retuned with the bounds widened: C1b scores +0.32, +0.51, +0.26 (last third 2.57, 3.67, 2.54): more even, short
  of 3 at the usual and double noise; C2b +0.66, +0.67, -0.04 (4.73, 5.06, 2.43). Neither does the job.

## M4: the user's questions about C2 (2026-10-20), and two new rules

Shown C2's schematic (`minimal/c2.html`, published), the user asked three things:

1. **The clock's fast amplifier has no capacitor: an oscillator leaning on the simulator's step?** Its speed is set
   by M1's capacitor over its gain, but the tuned capacitor was small (0.23) and the gains large (5.3, and 20 for the
   slow one, which could move M1 by 4 V in one integration step). Measured: the clock's rate held at 231, 233, 233
   kicks per 1,000 ticks at steps 0.05, 0.025, 0.0125 (its timing is the slow filter's), and C2 in the real Life at
   half the step scored +0.94 against +0.56 (16 seeds x 2; intervals overlap). Not an artefact, but **the rule in
   AGENTS.md (limits on gains and time constants against the step, for an optimised circuit) had not been applied**.
   Now: nothing may move a node more than 10 V per circuit tick (0.5 V per step): an element (|gain| / C), a leak
   (1 / RC), or the body's pulse into a sensor or the taste node (3 / C). Every design so far broke it (C2 86, C1b
   20, C2b 719, C 16), so every result above is to be redone under it.
2. **The clock drives one thruster, unconnected to the other: must their rates match for a straight approach?**
   Measured (after learning): with food in view, motor 0 (the eyes) 148 kicks per 1,000 ticks against the clock's
   206; with nothing in view, 0 against 232. So it doesn't go straight: it closes on food along a gentle arc (turning
   much more slowly than its search circle), which catches the near blocks. Matching isn't needed, but the mismatch
   sets how far off food can be and still be caught.
3. **Two current sources in series between +V and ground, CMOS-style: a short circuit, or wasted energy?** Not a
   short (each source is limited to its gain), but measured: the writes conduct only during a taste (both gated by
   it), on average 0; **the clock burns 7 units of current**, its fast stage near full almost all the time and the
   slow one fighting it (about 1.0 straight through), against 0.25 for both reads together. Current cost nothing in
   the score. Now: each design's mean power (the summed size of its elements' currents) is reported, and costs 0.05
   per unit in the score (the user had raised energy as a cost before; the size of the cost is a choice to revisit).

## Two dimensions, and the league table (the user's request, 2026-10-20)

The user asked to track **simplicity** and **energy** independently, balance them about 50:50 in a league table,
and watch for outliers that excel in one and do badly in the other; and doubted current as the energy measure
("current by itself doesn't mean waste"). Answer: every element draws its current from fixed rails, so its power is
that current times the supply's span, and as the circuit does no outside work (the body powers the thrusters) all
of it ends as heat; charge put on a capacitor came from the supply too. What current alone missed was the leak
resistors, which dissipate whenever a node is away from its rail. The user then pointed out that a resistor's current
is supply current too, so it should have been in the argument all along: right, only the elements' currents had been
summed. And current x the supply's whole span overstates an element's share. So **power** is now what each device
dissipates, its current times the voltage across it, averaged over the life (`minimal/fastlife.py`): an element
feeding a node from the +3 V rail, |I| x (3 - V); one draining it to -3 V, |I| x (V + 3); a leak resistor,
(V - rest)^2 / R; a capacitor gives back what it stores. The score's cost is 0.01 per unit.

`minimal/league.py` writes `minimal/LEAGUE.md`: every tuned design re-validated under the current rules; **entry**
by doing the job at all three noise levels within the slew limit (learning is a gate, not a dimension); **value**,
parts and power 50:50, the geometric mean of (best / own) for each, so twice the parts costs as much as twice the
power; **Pareto** marks the designs no other beats on both (the outliers worth a look); the near misses listed apart.
Parts (capacitors, resistors, diodes, transistors) rank; level-0 blocks (nodes and elements) shown beside them. The
open search (`minimal/evolve.py`) now has three objectives: score, parts and power.

## M5: redoing the designs under the slew limit and the energy cost

- **C2**, from its values pulled inside the limit (capacitors raised until nothing moves a node more than 10 V per
  circuit tick), 80 generations: power fell from about 36 to 5.5 (on the device-dissipation measure), and it nearly
  does the job: food 0.99, 1.12, 1.20 and last third 3.45, 4.22, 2.66 at half, usual and double noise (short at
  half, on food, and at double, on food:poison). The mean score was still rising (-1.6 at generation 19, +0.2 at
  79): continued.
- **C1t** (21 parts: one write both ways, a tanh of the taste node about its rest, gated by sensor 0): learned
  nothing (food - poison exactly 0 at all three noise levels): its bit never moved from where it started. Parked;
  the open search may find such structures for itself.
- C2 continued (100 more generations): does the job at half and the usual noise (last third 3.74, 3.90), not at
  double (2.25); power 25 on the device measure. Under the slew limit, **double noise is what no design passes**.

## M6: the open search

- **From random circuits (`evolve0`), it found nothing that learns.** 130 generations of 48 parents and 48 children
  (three objectives, each generation on 8 fresh seeds x 2): no circuit scored above 0. The best were tiny
  non-learners (down to 6 parts) eating both colours alike, about -1. Stopped. Why, I think: learning pays only once
  a memory, a write and a read exist together and fit; any one alone gains nothing, and with paired lives every
  non-learner scores at most 0, so random mutation has no slope to climb. **From scratch, at this budget, evolution
  can't check the lower bound independently.**
- **Seeded (`evolve1`)**: the population begins with C2 and C2b, C1b and C (each pulled inside the slew limit) and
  their mutants, so that evolution can change structure as well as parameters: drop parts, re-route a gate, swap
  a soft gate for a sharp threshold (what double noise seems to need, and parameter tuning can't do).
- **A device fed back to itself** (the user, 2026-10-20: "a naked device fed back to itself implies infinite
  speed"). It feeds its own node's capacitor (a gm-C loop), so its speed is C / (gain x slope); but the slew limit
  alone allowed a time constant of about 2 integration steps, and the C2 first drawn had one of about 1 step (M1's
  capacitor 0.23). Now also: every unfiltered self-feedback acts no faster than gain x slope / C = 2 per circuit tick,
  a time constant of at least 10 steps (the designed circuit's neurons sit exactly there). C2 as now tuned meets it
  (M1's capacitor 9.3: the fast loop 4.4 circuit ticks, 88 steps; the slow one set by its filter, 79 circuit ticks).
- **The inputs' source impedance** (the user: with an infinitely stiff source, the input capacitors would do
  nothing). The body drives each input as a current source (infinite impedance, like a photodiode): a fixed charge
  per stimulus (3 for a circuit tick), so the capacitor is what turns it into a voltage (q / C) and with the leak sets
  its decay; it doesn't run away because each pulse is brief and the leak drains it. But nothing stopped a node going
  beyond the supply: the slew limit allowed a pulse to lift a node 10 V, a tuned taste node rested at -3 V and fell far
  below on a bad taste, and the power measure assumed rails at +-3 V. Now **every node is held within the rails
  (+-3 V)**: what a real supply does, so not counted as parts (a clamp inside the rails still costs two diodes). The
  seeded search (`evolve1`) was restarted under all the rules.
- **The rules, enforced** (the user: rules should be in software as well as written down, as the sheet brain's
  locality is). Until then the slew and loop limits were only penalised in the score (an illegal circuit still
  lived, and scored badly); the rails were enforced by construction. Now `check` (`minimal/spec.py`) refuses an
  illegal circuit, so none can be built or lived (the search scores one, without living it, as starving, with a
  penalty graded by how far over it is, so a search can find its way back); `python -m minimal.test_minimal` tests
  each refusal, the rails and the parts count, and that fastlife still lives creature.Life's lives (a push check);
  and the rules are in AGENTS.md.
- **C2 under all the rules** (rails too, 80 generations from its last values): score +0.34, +0.32, -0.23 and last
  third 4.14, 3.98, 2.17 at the usual, half and double noise; power 12.5. Short at double noise only.
- **Seeded (`evolve1`, 120 generations from C2, C2b, C1b and C, all made legal)**: nothing smaller than 23 parts
  scored above 0 in any generation. The best circuit of each size (23-44 parts) was validated in the league table:
  none does the job. The nearest: **E1_32p** (32 parts, power 10.4) does at double noise (last third 3.46: the first
  legal circuit to) and the usual (3.77), and misses at half only on food (0.92 against 1). Against C2, evolution
  filtered the clock's fast loop (17 steps: legal), made sensor 0 (gated by motor 0) drive the clock motor too, and
  added a node and element that look inert (a slow inverted copy of sensor 1, feeding the memory through a
  threshold it never reaches). So the two nearest misses fail in opposite directions: C2 at double noise on
  food:poison, E1_32p at half noise on food.
- Next: polishing a raw circuit's own parameters with CMA-ES (`minimal/designs.py`, raw: every rest, leak,
  capacitance, gain, offset, slope and filter, within a factor of 4), which evolution's coarse jitter can't: E1_32p
  (49 parameters), then C2's raw form (its mirror parts free to differ).
- **Polished (CMA-ES on each circuit's own parameters, 120 generations, under the old noise):** P_E1_32p (32 parts,
  power 8.6) and P_E1_23p (23 parts, power 7.7) both did the job at half and the usual noise (last third 4.37, 4.12;
  4.46, 3.73) and missed at double (2.47; 2.63), as C2 did.

## M7: noise as biology makes it (2026-10-20)

The user asked how the noise was decided and whether it could be cheated: it could, three ways (inputs on tick
boundaries; memory write noise that vanished at a finer step; a fixed noise per node, so scaling a node up silenced it
for free, which the search was starting to do to the sensors). The noise is now modelled on biology's and built into
the simulator, where no design can change it (LESSONS.md, Noise as biology makes it; README, Terms): shot noise on
every current, membrane noise in proportion to capacitance, writes rough by the square root of what is written, 10%
mismatch in every part, inputs at random moments. The user settled on judging at the nominal noise only, and I
predicted every design would now fail, mostly on the mismatch (from 3% to 10%).

- **Wrong: the two polished circuits do the job** (league, 64 held-out seeds x 2): **P_E1_23p** (23 parts, power
  7.6) score +0.14, food 1.13, last third 3.72; **P_E1_32p** (32 parts, power 8.3) score +0.30, food 1.41, last
  third 3.64. C2 and the unpolished evolve1 circuits miss (last third 2.0-2.7).
- **In the real `creature.Life`, at the step and at half of it** (`minimal/check.py`, 32 other seeds x 2): P_E1_32p
  last third 4.34 and 4.03, score +0.33 and +0.37, food 1.41 and 1.52: it holds. P_E1_23p 2.51 and 3.77, score -0.03
  and +0.07: marginal, passing on one set of held-out lives and missing on another.
- **The circuit brains, by contrast, collapse** (LESSONS.md): the designed circuit's last third falls from 4.6 to
  1.0, the recruiting circuit's from 5.4 to 1.3, mostly from mismatch, which they were never built to survive. The
  minimal designs were tuned with mismatch (3%) and varying noise from the start, so their robustness was searched
  for; the hand-built neurons' was not.
- **Polished again under the new rules** (CMA-ES from P_E1_23p and P_E1_32p, 120 generations, 24 a generation, 12
  seeds x 2 each; 65 and 90 minutes), both do the job better (league, 64 held-out seeds x 2):

  | design | parts | power | score | food | last third | real `Life`, step 0.05 / 0.025: score, last third |
  |---|---|---|---|---|---|---|
  | **N_E1_32p** | 32 | **4.8** (was 8.3) | +0.35 | 1.52 | 4.76 | +0.53 / +0.41, 6.16 / 4.95 |
  | **N_E1_23p** | 23 | 7.2 (was 7.6) | +0.36 | 1.40 | 4.33 | +0.55 / +0.64, 5.66 / 5.50 |

  Both are Pareto: N_E1_32p heads the league (value 0.85) on power, N_E1_23p (0.82) on parts. Both hold in the real
  `creature.Life` at the step and at half of it, on 32 seeds x 2 the search never saw; N_E1_23p, marginal before,
  now passes comfortably.
- **What the polish changed**: every sensor's capacitance shrank (S0 1.1 -> 0.66 and S1 1.5 -> 1.0 in N_E1_32p;
  1.4 -> 0.90 and 3.2 -> 0.91 in N_E1_23p) while its resistance rose, so its time constant RC stayed about where it
  was (8.5 and 8.6 ticks; 7.9 and 16.7) on smaller currents. Under the old fixed noise per node the search had begun
  to make nodes big to drown it; now a node's noise grows with its size and its currents, so that is gone and the
  search goes the other way: small sensors.
- **The two winners are one circuit** (zeroing each element's gain in turn, 32 held-out seeds x 2; a zero gain keeps
  every other part's mismatch draw). Every element of N_E1_23p is needed: without any one, the score falls below -0.8.
  N_E1_32p is the same six elements plus three that do nothing: n6 <- S1 and m <- n6 (n6 can only fall below its
  rest, -0.56 V, and the second needs it near +3.2 V, so it never passes a current) and M1 <- S0 gated by M0 (score
  +0.44 without it, against +0.40). Those are 7 dead parts (n6's C and R, five transistors), kept because the polish
  (CMA-ES) tunes values only and cannot remove an element. The rest of the difference is a filter on the
  clock's fast feedback (2 parts). Its power is lower because the clock's slow reset is gentler (gain -1.25 against
  -28): zeroing the reset cuts N_E1_23p's power from 7.2 to 1.1, so the clock is nearly all of it, as in C2.
- **Pruned N_E1_32p** (dead branch removed; league seeds, fastlife): 25 parts, power 4.5, score +0.45, food 1.60, last
  third 3.74: does the job. Also without the filter: 23 parts, power 4.4, score +0.36, last third 3.38: does the job,
  narrowly, and would beat N_E1_23p on power at the same parts. Not yet in the league or checked in the real `Life`.
- **Pruning made a standard step** (`minimal/prune.py`, at the end of every polish; the user agreed it should be).
  Every single simplification (delete an element and whatever it leaves unread, take away a filter, a gate, a leak or
  a clamp) is tried on paired lives of pruning's own; the best that keeps the score within 0.1 of where pruning
  started is kept, and again until none does. From N_E1_32p it went 32 -> 30 (the fast feedback unfiltered) -> 29
  (n6's leak) -> ... -> 23 (the dead parts) -> 22 (M1's leak) -> **21 (M1's fast positive feedback deleted)**:
  **N_E1_32p_pruned**, 21 parts, power 1.3, score +0.32, food 1.33, last third 4.12 on the league's seeds, so it
  does the job at the lower bound argued above (The lower bound). From N_E1_23p only M1's leak went: N_E1_23p_pruned, 22 parts, power
  6.8, score +0.42, last third 3.84.
- **The 21-part clock runs on noise.** M1 is now a capacitor with one delayed, saturating negative feedback (gain
  -1.25 through a filter of 22 circuit ticks): a damped resonance that noise keeps ringing. Its spikes per 1,000
  ticks (16 seeds): 23 at half the noise, 162 at the usual, 240 at double. The 23- and 32-part clocks are true
  oscillators: 184 and 186 at half, the same at double. Under the rule (judged at the nominal noise only, the user's
  decision) the 21-part circuit is legal; but it is exactly the dependence the old half-and-double check caught, and
  the lower bound's item 6 excludes ("a way to explore that doesn't hang on the noise level"), so it reaches 21 by
  breaking the argument's own terms, and is flagged for the user rather than crowned. Counted the argument's way, the
  winners are its 21 plus a second write (two writes, one each way: 23).
- **In the real `Life`** (32 other seeds x 2, at the step and at half of it): N_E1_32p_pruned last third 5.09 and
  4.13, score +0.43 and +0.51; N_E1_23p_pruned 3.93 and 5.11, +0.45 and +0.62: both hold. Polished again (CMA-ES,
  120 generations, from N_E1_32p_pruned), **NP_E1_32p** scores better on the league's lives (+0.55, food 1.56, last
  third 4.27, power 1.9; pruning then found nothing more) but misses in the real `Life` (last third 2.62 and 2.87):
  its gain on the league's seeds did not carry to others. So under these rules the league's leader is
  N_E1_32p_pruned (21 parts, power 1.3, Pareto alone), with its noise-driven clock.
- **Stress tests** (N_E1_23p; the 21-part circuit alike): with learning off, food and poison are exactly equal (1,354
  each over 64 paired lives), so all of the preference is learned. Over 100,000-tick lives, whenever it eats it still
  picks food 4-5 times as often as poison, but food per 1,000 ticks falls from 1.34 (first tenth) to 0.3-0.4 (last
  tenths) and the share of lives eating nothing in a tenth rises to 75%. If the poison colour swaps halfway through a
  20,000-tick life, food:poison drops to 0.2-0.3 and stays there: it learns only from food (a bad taste shuts the
  writes' gates harder), and having learned, it no longer approaches the colour that is now food.
- **Stranding** (the user, watching seed 1 live): after 10 food and 4 poison, N_E1_23p circled on the spot (a
  2.5-unit patch) for the rest of its life. Its only way to travel is to see food, and a distant block gives few eye
  pulses, so once it has eaten what is near, it never moves again. Over the league's lives **21-24% of the winners'
  lives eat nothing in their last third**, hidden because the score summed food over all lives. See M8.

