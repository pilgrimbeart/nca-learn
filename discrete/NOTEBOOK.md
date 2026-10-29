# The simplest discrete circuit that forages

The user's question (2026-10-26): before getting clever about telling food from poison, what is the simplest analogue
circuit that drives the body to blocks efficiently in an all-food world, built of common parts (resistors, capacitors,
diodes, transistors, FETs, unijunctions)? Their expectation: no more than 20 parts should do a reasonable job.

The body, the world and the interface are every brain's (AGENTS.md); the circuits are netlists of real parts living
closed loop in SPICE (`discrete/life.py`). Judged by `minimal/spec.py`'s measures, all food: efficiency (meals gained
per meal spent resting, moving and thinking), gain rate (meals per 10 s), food, stranding.

## Where it stands

- **Foraging, all food**: hold and drive, 14 parts, efficiency about 7 at 72 nW (D3, D4): an oscillator scans with one
  thruster, and each pulse from an eye charges a hold capacitor that fires the second thruster too while it lasts. A
  9-part blind oscillator is as efficient and four times as fast, but only on a body whose two thrusters are exactly
  equal (D5).
- **Self-tuning to the body**: not found worth it yet. Bodies built differently barely move the best settings, except
  unequal thrusters, and no in-life tuning from meals beat a fixed circuit; driving only while the eyes still see the
  block copes instead (D5). A richer body (an eye on each side for each colour) is held off: the user prefers to
  learn what extreme simplicity gives first.
- **Learning the bit**: `learn_avoid`, 46 parts, surely does the job held out (160 lives): efficiency 1.78, gain
  4.7, food:poison 4.7 in the last third, none stranded, 130 nW (D8, D9). It gives up on an empty patch (both
  thrusters straight once the followed eye has seen nothing for a few seconds) and turns from poison ahead (the
  silenced eye empties the hold). Pruned from 48 parts (D9), and surely better than them. Its predecessor
  `learn_hold` (49 parts, D6) stranded: it circled in patches it had eaten clear of food.
- **The ceiling** for this kind of brain on this body, as policies: 2.7 told the answer from birth, 2.3 learning
  (D8, D10). The circuit's gap isn't in learning or approaching but in spending: it scans at 54 per s for no more
  sightings than at 16, and its giving-up run is fast and runs into poison (D10). Two speeds fight the bipolars'
  collapsing gain at nanoamps (D11).
- **In SKY130 CMOS** (D12): a copy of the best policy, about 130 parts, works at a twelfth of `learn_avoid`'s power
  but is surely worse (gain about 0.8): its drive hold was 63 ms where the policy's is 0.2 s, and its doubt couldn't
  flip back for 3.6 s.
- **The fast model** (D13): the circuit's blocks as their measured numbers, a life in a second, tied with ngspice on
  the circuit's own lives; judged robustly (each life its own parts' errors), which exposed a knife-edge the nominal
  searches exploited. Its best design, **B**: doubt a bounded tally (+ a poison, - a food, no leak, the bit flipping
  at a threshold and the tally then reset), 2.38 held out with tolerances, learning costing it 0.15 against being told
  the colour. Built in transistors (151 parts, 3.7 nW), every block works on the bench; its 32-seed bench (for the
  model's prediction, before living it in ngspice) was stopped for memory, to restart 4 at a time.
- **Bodies** (D13): with each thruster 0.5-2, every fixed design collapses (B 0.32, the best searched on such bodies
  0.76); told its balance, B gets 1.92; eight local rules for finding the balance reach at most 0.8.
- **Ceilings** (D13): omniscient about 20, a perfect memory of what it has seen 4.5, B told the colour 2.54.
- Values not yet tuned for `learn_avoid` (its values are learn_hold's and the prototype's). A pruned circuit
  must be judged held out: pruning's last cut, "not surely worse" on 12 seeds, was surely worse held out (D9).
- **The simulator** is checked in both step and tolerance: ngspice's error control is tightened in every netlist
  (D7).
- Queue 7 re-judged every circuit with the tightened control (D7) and re-tuned learn_hold (noise, no trend: its
  output kept as `results/learn_hold_tune_q7.json`, never judged); the foraging circuits' re-tunes were cancelled
  (their results stand, D7).
- Open questions: `QUESTIONS.md`.

## D1: the problem, from above (2026-10-26)

**What the body gives.** Each eye looks straight ahead along a corridor as wide as the mouth's sweep (2 mm), up to
15 mm, and pulses at random (Poisson) at up to 50 per second for a block close up, half that at 5 mm, about 5 at
15 mm. It says how much of its colour is ahead, never where: there is no bearing to steer by. Anything seen is in the
mouth's path already. With both colours food, the two eyes are interchangeable: a circuit may simply add them.

**What the thrusters do.** Each firing adds 20 mm/s forward and 16 rad/s of turn, both fading at 50 per second: 0.4 mm
and 0.32 rad (18 degrees) per firing. Both at once go straight 0.8 mm. One alone drives a circle of about 1.2 mm
radius whatever its rate. So a circuit's whole repertoire is: go straight (both), turn while creeping (one), or rest.

**What it costs.** Resting costs a meal per 10 s whatever the creature does; a firing 1/500 of a meal; the circuit
its power, a meal per 10 s per microwatt. Blocks: 36 in a 60 mm torus, 0.01 per mm^2; about 7 lie within the eyes'
range of any point, and in an all-food world a creature that keeps finding them almost never strands.

**Approaches.**

1. *Blind straight*: fire both thrusters at a steady rate and sweep a 2 mm swath. No sensing; costs about 125
   firings a meal; its efficiency rises with speed, since the resting cost is spread over more meals.
2. *Reflex and scan*: a clock fires one thruster (turning the eyes round the circle), and each pulse fires both
   (approach). Cheap per meal, but the clock keeps turning the creature while it approaches, and a far block's few
   pulses are lost.
3. *Hold and drive* (the hold-and-roam circuits' kind, without the bit): after any pulse, both thrusters fast for a
   short while; otherwise one, to scan. Equivalently, each pulse fires a burst on both thrusters and silences the
   scanner for a moment.
4. *Run and tumble* (bacteria): go straight, turn at random moments, turn less while pulses come. A cousin of 3.
5. *Roam*: drive off after a long spell of nothing; needed with poison, not, it turns out, here.

**Policies first** (`discrete/policies.py`: rules, not circuits, on the real body, 16 seeds, circuit power 0):

| policy | best values | efficiency | gain rate | firings /10 s |
|---|---|---|---|---|
| blind straight | 40 / 120 per s | 4.2 / 5.5 | 10.8 / 31.9 | 800 / 2400 |
| two free clocks, eyes ignored (a wide circle) | | 0.2 | 0.4 | strands |
| reflex and scan | scan 4 per s | 3.3 | 4.1 | 123 |
| reflex, scanner silenced 0.1 s after a pulse | scan 8 | 5.8 | 7.9 | 190 |
| ... each pulse firing both 4-8 times | scan 16-32, silenced 0.05-0.1 s | 8.5-8.9 | 18-27 | 550-1040 |
| hold and drive | scan 16, drive 80 per s, hold 0.1 s | 7.8 | 18.1 | 663 |
| hold and drive, slower drive | scan 16, drive 40, hold 0.1 | 7.2 | 13.0 | 400 |

So: a hold is worth a lot (3.3 to 5.8), a strong approach more (8.5); a long hold hurts (1 s: the creature drives on
past where the block was); stranding is rare without any roam. The target for a circuit: on any pulse, both
thrusters at 40-160 per second for 0.05-0.2 s; otherwise one at 16-32 per second. The blind driver is the baseline to
beat, and it is not weak: speed alone gives 5.5.

## D2: the technology and the bench (2026-10-26)

The interface in discrete parts (`discrete/life.py`, my choices, to confirm or change):

- a 3 V lithium coin cell; its delivered power is the circuit's;
- each eye a photodiode from the supply into its sensor node, 1 uA while it pulses (2.5 ms), unable to lift its node
  above the supply; both eyes may feed one node (a wire);
- each motor a thruster driver's CMOS Schmitt input: a firing each time its node rises through 2/3 of the supply,
  re-armed below 1/3 (the same rule as every brain's spike, in this technology);
- parts from stock: 2N3904 and 2N3906 transistors, 1N4148 diodes, resistors 1 MOhm to 1 GOhm, capacitors 47 pF to 30 nF;
  each seed draws its own tolerances (resistors 1%, capacitors 5%, a transistor's saturation current 20% and gain
  25%: one standard deviation). No noise in SPICE (a discrete circuit's thermal noise is microvolts against volts);
  the body's pulses are random and every seed's parts differ.

**Power decides the oscillator.** At a microwatt a circuit costs as much as resting, so it must run on nanoamps. A
classic astable multivibrator (one transistor always conducting) or a real programmable unijunction (valley currents
of microamps) can't. A PUT built of a PNP and an NPN can: the timing capacitor charges through a large resistor until it
passes the gate's voltage by a diode drop, the pair latches and dumps it into the NPN's base, and lets go once the
timing current alone can't hold it (below about 0.6 V over the NPN's base shunt). Seven parts; on the bench 12-32 Hz
at 80-130 nW, most of it in the gate's divider. The limit that shaped the design: the pair lets go only if its
charging current stays below that holding current, and fires only if it exceeds a peak current about 2.4 times
smaller, so a current can speed the oscillator up only about that much before it latches on. (Found on the bench:
the hold's extra current latched it until the hold drained.)

A closed-loop life of 100 s takes about 15 s of SPICE: tuning in SPICE itself is affordable.

## D3: hold and drive, 14 parts (2026-10-26)

`discrete/circuits.py`, `hold_drive`: both eyes feed one emitter follower (1 transistor), which charges a hold
capacitor at each pulse to about the supply (3.0 V on the bench: a photodiode can push its node a little above
the supply, as a solar cell does); the hold leaks through one resistor (rf) into the
oscillator's timing node, so it rests at that node's mean (below the motors' threshold) and, while charged, can speed
the oscillator up. The oscillator (7 parts) pulls motor A's pull-up low at each beat through an NPN (one thruster:
scanning); motor B's pull-up comes from the hold node, through an NPN of its own, so it fires too only while the hold
is above the motors' threshold (both thrusters: straight ahead).

What the bench and the closed loop taught, in order:

- **Tuning blind fails.** CMA-ES in closed loop from hand-set values: with fresh seeds each generation the scores
  jumped as much as any gain; with the job as a cliff (any stranded life fails the generation) the search followed
  the riskiest of the failing candidates; with a step of 0.15 of a log range (a factor of 2.8 for a resistor, where
  the switch's window is 3) every candidate was worse than the mean. Fixed: the same 16 seeds every generation, a
  smooth objective (efficiency less the shortfall of each third of each life: `tune.robust`), a step of 0.04. Even so
  a life's whole path changes with a tiny change of values, so the landscape is rugged at small scales.
- **So screen on the bench first** (`discrete/screen.py`): rates at rest, in the hold after single pulses, and
  through a burst of pulses, against the policy's best; then closed loop. Each test found a failure the closed loop
  had hidden: (1) with only a burst test, the screen chose a hold of 16 ms (motor B fired twice per pulse, the policy
  wants 0.1-0.2 s); (2) with only single pulses, a hold whose current, held at its top by a near block's frequent
  pulses, latched the oscillator: in a life it fired 7 times a second while a block was in view and 11 while none
  was, stalling exactly when it should drive (efficiency 2.5).
- **The speed-up is not needed.** With both tests the search pushed rf to its bound (1 GOhm): the best circuits
  barely speed up after a pulse; motor B simply joins motor A while the hold lasts (the policy "hold and drive" with
  drive = scan: 6.0 at 32 per s). The hold's current can only add within the switch's window anyway.
- **The best screened start**, scanning at 63 per s (closed loop, 16 seeds x 40 s): **efficiency 6.6, gain rate
  18.4, 114 nW**, none stranded: at the policy's level for its kind (5.5-6.0), four times the hold-and-roam circuits'
  (which face poison too). The hold costs power too: each pulse refills its capacitor from the supply through the
  emitter follower (a 2.25 nF hold drew 270 nW in a life against 87 at rest).
- **The diode must not leak.** A 1N4148 leaks nanoamps reversed, as much as these circuits' currents: in a pared
  variant it drained the hold. The diode is a low-leakage one (BAS416 class, picoamps).
- **The bench undercounts brief firings.** `bench` writes its traces at its step (20 us), and a motor's dip at a beat
  can be shorter: at 5 us the best start scans at 60 per s on the bench where 20 us counted 37, and after one pulse
  motor B fires on 12 beats (0.17 s, h from 3.0 V down through 2 V). The closed loop counts firings at every
  internal step and is unaffected; the screen's rates (and so its fitness) were low, a filter's error, not a
  judge's.
- **The timing node can't be a motor.** Charging it through a resistor from 3 V up past the motor's threshold (2 V)
  and down below 0.8 V needs a current range of about 3, the switch's whole window (it fires above about 0.4 V over
  its base shunt and holds below about 3 times that): it either latched or stalled at the top. A motor needs its own
  buffer.

## D4: paring to the bone (2026-10-26)

`discrete/prune.py`: each part of a circuit taken out in every way it can be (opened; shorted; for a transistor, two
of its terminals joined), every variant living the same 16 closed-loop lives; the most promising few re-screened for
new values on the bench. Two modes: **prune** keeps a cut only if the circuit does as well as the whole within noise;
the **ladder** keeps cutting the least harmful part, however much is lost, while the job is still done, to show what
each part buys.

**Pruned, hold_drive keeps all 14 parts**: the nearest cuts (the hold's leak: 6.1; the eye follower: 5.8, against
6.8) are surely worse. Re-screening values after a cut never rescued one: the bench screen is a filter, not a judge.

**The ladder** (chosen on seeds 30000-30015; judged on 32 held-out seeds, 100 s, `discrete/judge.py`):

| parts | what went | efficiency [95%] | gain rate [95%] | stranded | power |
|---|---|---|---|---|---|
| 14 | (hold and drive, whole) | 6.62 [6.45, 6.80] | 18.2 [17.5, 19.0] | 0% | 113 nW |
| 13 | the hold's leak: the hold drains only through motor B's own firings (its pull-up comes from the hold) | 6.2 (on the ladder's seeds) | 16.8 | | |
| 12 | the eye follower: the eyes charge the hold capacitor directly (for free: the follower refilled it from the supply) | 4.96 [4.58, 5.30] | 13.1 [12.0, 14.2] | 3% | 93 nW |
| 11 | the switch's base shunt: the two motor NPNs' base junctions take its current instead | 2.6 (ladder's seeds) | 4.1 | | |
| 10 | the hold capacitor: each pulse fires motor B directly while motor A scans | 2.94 [2.75, 3.13] | 4.5 [4.1, 4.8] | 0% | 151 nW |
| 9 | no cut still does the job | | | | |

What each part buys:

- **The hold is the whole difference between 3 and 5-7.** Without it the bottom rung is counter-turning (`counter10`):
  motor A scans and each pulse fires motor B, so their turns cancel while a block is in view, and the creature
  zig-zags in. The ladder found it unaided; it is the policy "counter" of D1 (3.5-3.9 there).
- **A hold can drain by doing its job**: with motor B's pull-up taken from it, each of motor B's firings spends a
  little of the hold, so it needs no leak of its own; the longer it drives, the sooner it stops.
- **The eye follower buys about 1.7** (12 to 14 parts with its leak): it lifts the hold to about the supply at once
  however weak the pulse, where the eyes' own charge (2.5 nC a pulse) lifts it only partway. It costs
  power: each refill comes from the supply.
- **The switch's shunt resistor is a part the motor buffers can do without**, at a price: their bases shunt the
  switch's NPN, so the window's edges follow two transistors' gains instead of a resistor.

**Each rung tuned as a circuit of its own** (`discrete/tune.py`, CMA-ES on seeds 20000-20015 x 40 s; then judged on
the 32 held-out seeds x 100 s, `python -m discrete.judge`, compared paired with `--compare`), with the blind straight
driver (9 parts) as the baseline:

| circuit | parts | efficiency [95%] | gain rate [95%] | stranded | firings /10 s | power |
|---|---|---|---|---|---|---|
| hold_drive, tuned | 14 | **7.07** [6.84, 7.27] | 18.6 [17.8, 19.4] | 3% | 771 | 93 nW |
| hold_drive, screened (above) | 14 | 6.62 [6.45, 6.80] | 18.2 [17.5, 19.0] | 0% | 820 | 113 nW |
| hold12, tuned | 12 | 6.50 [6.05, 6.85] | 15.9 [14.5, 16.9] | 3% | 676 | 90 nW |
| straight, tuned (blind) | 9 | 6.30 [5.51, 7.00] | **82.6** [71.5, 92.6] | 0% | 5937 | 229 nW |
| counter10, tuned | 10 | 4.06 [3.86, 4.25] | 6.6 [6.2, 6.9] | 0% | 263 | 87 nW |

Paired: tuned hold_drive is surely the most efficient (+0.45 [+0.18, +0.73] over its screened start, +0.57 over
hold12, +0.77 [+0.02, +1.53] over straight); hold12, straight and the screened hold_drive are tied on efficiency.
Tuning moved hold_drive's gate divider up (rg1 542 M, rg2 116 M), its hold down (814 pF) and rf to its bound again:
it saves power (93 nW) more than it changes behaviour.

**The blind driver found speed.** Tuned, it beats at about 300 per second, both thrusters at once: 240 mm/s, laps of
the 60 mm world four times a second, sweeping a 2 mm swath; 83 meals per 10 s, four times any sighted circuit, and as
efficient as the screened hold_drive, since the resting cost is spread over so many meals. It works only because the
two thrusters are identical: with thrusters unequal by 1% it circles (D5).

**A note on the machinery**: ngspice run as a library keeps every circuit and its results; a worker grew by half a
gigabyte in an hour and the laptop ran out of memory. Each run now unloads its circuit (`destroy all`, `remcirc`): a
worker stays at 150 MB. Bench runs and closed-loop runs can't share a process (ngspice's two modes): two pools.

## D5: can a circuit tune itself to its body? (2026-10-27)

The user's question (2026-10-26): in an all-food world, give each life's creature slightly different
characteristics; the best circuit would be one that tunes itself, in its life, to the body it finds itself in: a
subtle evolution with local learning. Asked first at the level of policies (`discrete/policies.py`, rules on the real
body, power 0), where trying a rule costs seconds.

**Bodies that differ** (`discrete/bodies.py`, my choices, to confirm): each factor on `world.py`'s values, drawn
log-uniform within 1/x to x for each life: both thrusters' strength (x2), one thruster against the other (x1.25),
the eyes' sensitivity (x2), drag (x1.5). `world.py` is unchanged: a life's body is swapped for a `VariedBody` after
`creature.Life` builds it, so the world, wiring and start are the unvaried life's.

**What is there to gain?** (`python -m discrete.variation`: hold and drive's 64 settings of scan, drive and hold on
each of nine bodies, 12 seeds x 60 s; the standard body's best setting on each body against that body's own best):

| body | own best (scan, drive, hold) | efficiency | the standard's best there | lost |
|---|---|---|---|---|
| standard | 16, 160, 0.05 | 8.25 | | 0% |
| weak (x0.5) / strong (x2) | 32, 80, 0.1 / 8, 160, 0.05 | 5.25 / 11.22 | 5.04 / 11.02 | 4% / 2% |
| dim / bright eyes | 8, 160, 0.05 / 16, 80, 0.05 | 6.67 / 9.01 | 6.64 / 8.48 | 0% / 6% |
| slippery / sticky | the standard's | 8.92 / 7.04 | | 0% |
| left / right thruster x1.25 | 32, 160, 0.05 / 32, 80, 0.05 | 5.71 / 6.66 | 5.29 / 4.70 | 7% / 29% |

So scan, drive and hold hardly need tuning: a body's own best gains at most 6% over the standard's (strength and
eyes change what a body *can* do, 5 to 11, not what it should do). The one thing that matters is **unequal thrusters**,
and no setting of these three knobs recovers it. A trim does: each motor at its own drive rate (`balance`: motor 0 at
drive x b, motor 1 at drive / b, the common rate fired together), set to cancel that body's mismatch (an oracle, per
life, from its wiring): on 24 bodies with thrusters unequal by up to x1.25, **fixed 6.78, perfectly trimmed 7.75**;
on two fixed mismatched bodies 5.0 and 4.6 against 7.8 and 8.2 trimmed. A trim error costs fast: 7.65 at 2.5% (log),
6.44 at 5%, 5.62 at 10%.

**Tuning the trim in a life fails** (24 bodies x 100 s, unless said):

| rule (the knob log b) | efficiency |
|---|---|
| fixed b = 1 | 6.78 |
| oracle trim | 7.75 |
| lock-in, rewarded by meals: wobble +-0.1, period 2 s | 5.5-5.7 (3 bodies) |
| lock-in, rewarded by the eyes' pulses while driving: wobble 0.025-0.05, period 0.5-2 s | 6.05-6.94 |
| ... 400 s lives | 5.77-6.90 (fixed 6.51, oracle 7.81) |
| per-approach dither (each approach's sign tossed), pulses or meals | 5.49-6.62 |
| run and tumble (drift; turn back when meals come slower) | 5.53-6.30 |

The lock-in does find the sign (75-100% of lives right by 100 s), but slowly, and the wobble it needs is itself a
mistrim, costing as much as it gains. The numbers say why: about 200 meals in a life, so a difference between two
halves of a wobble shows only if it is above about 14%; the trim's whole gain is 14%. The eyes' pulses are more
frequent but a poor reward: a well-aimed approach eats sooner and so sees *fewer* pulses. Earlier tries on the other
knobs: lock-in of the scan rate drifts the right way (weak bodies up, strong ones not) but the spread across lives
is wider than the difference by 100 s; a homeostat (the more eaten lately, the slower the scan; 2 parts in a circuit)
lowered every body's efficiency (8.29 to 8.12, 7.22, 3.22 as its gain rose).

**What works instead is a loop closed through the eyes.** The structures' loss with thrusters unequal by up to
x1.25 (24 bodies):

| policy | standard | unequal | lost |
|---|---|---|---|
| hold and drive, scan 16, drive 160, hold 0.05 | 8.39 | 6.78 | 19% |
| hold and drive, scan 32, drive 40, hold 0.1 | 6.36 | 6.30 | 1% |
| each pulse fires both 8 times, scanner silenced 0.1 s (`reflex_hold`, scan 32) | **8.56** | **7.37** | 14% |
| counter-turning | 3.16 | 3.22 | -2% |
| blind straight, 300 per s | 5.98 | **0.22** | 96% |

and with smaller mismatches (within x1.01 / x1.03 / x1.1): reflex_hold 8.44 / 8.56 / 8.28; hold and drive 8.45 /
8.12 / 7.77; **blind straight 1.86 / 0.63 / 0.28**. Driving only while the eyes keep pulsing corrects a curve for
free: a block that drifts out of the corridor stops the pulses, the scan finds it again.

**In SPICE** (`python -m discrete.judge ... --motors X`, the tuned circuits on the 32 held-out seeds):

| circuit | equal thrusters | within x1.03 | within x1.25 |
|---|---|---|---|
| hold_drive, tuned (14) | 7.07 [6.84, 7.27] | 6.78 [6.63, 6.94] | 6.02 [5.79, 6.23] |
| hold12, tuned (12) | 6.50 [6.05, 6.85] | 6.80 [6.59, 7.00] | 5.71 [5.44, 5.99] |
| straight, tuned (9) | 6.30 [5.51, 7.00] | **0.73** [0.36, 1.24], 34% stranded | 0.25 [0.08, 0.56], 28% stranded |

**Conclusions.**

- The blind driver's speed was the simulator's gift: two thrusters identical to the last digit. No real pair is; a
  mismatch of 1% makes it circle. *A proposal for the user* (a change to the body, so theirs to make): give every
  life's thrusters a small mismatch (a few %), so that no design can lean on perfect symmetry.
- Self-tuning, as asked, has little to work with here: the knobs a circuit could tune barely matter across bodies,
  and the one that matters (trim) can't be found from about 200 meals in a life with a wobble cheaper than the
  mistrim. The way to cope with a varied body is structural: drive while the eyes say the block is still ahead.
- **The user's lesson** (2026-10-27): the body's dynamics need to vary from life to life, as the parts' tolerances
  do, so that no circuit is tuned to one exact body's accidents (README, What we've learned).
- Untried: a richer local signal for the trim. The eyes give no bearing; what a mistrimmed approach changes is how
  long a block stays in view, which is the pulses' *rate of change*, not their count.

## D6: one bit, learned (2026-10-27)

The user's next question (2026-10-26): take the best circuit and find the simplest way to add the bit, learned in its
life: food against poison, as every brain in this project must.

**Policies first** (`discrete/policies.py`, `judge_poison`: each seed lived twice, red then blue as poison; 12-24
seeds x 100 s). The learning rules are options of any approach (`learn`), as is the roam (`bored`, `roam`):

- `toggle`: only one eye may start an approach; a poison flips which (after `n` poisons with no food between;
  `blame` "held": only poisons eaten while approaching count; `forget`: the count fades);
- `trace`: each eye's pulses leave a fading trace; poison turns off the most traced eye (and on the other), food
  turns it on (`latch`: exactly one on; `poison_only`: food changes nothing).

| rule (with the roam: 3 s with nothing, then 1 s straight at 20 per s) | efficiency | food:poison, last third | stranded | job |
|---|---|---|---|---|
| toggle, n 1 | 0.14-0.46 | 2.0-2.1 | 0% | no |
| toggle, n 1, blame held | 1.18-1.21 | 2.6-2.7 | 0% | no |
| **toggle, n 2** | **1.83-2.00** | 3.8-4.0 | 0% | **yes** |
| toggle, n 2, blame held | 2.12-2.29 | 4.1-4.6 | 0% | yes |
| toggle, n 2, forget 0.5 / 1.5 / 5 / 15 s (hold and drive) | 1.69 / 1.83 / 1.87 / 2.02 | 3.3-3.9 | 0% | yes |
| trace, tau 0.1-1 s (with or without latch) | -1.11-1.12 | 1.6-2.9 | 0% | no |
| trace, latch, poison only, tau 0.1 s | 1.56 | 3.2 | 0% | barely |
| toggle, n 2, no roam | 1.36-1.72 | 3.8-4.2 | 25-33% | no |

What decided it:

- **A roam is needed** (a third of the lives strand without it, now that only half the blocks are worth
  approaching), and it must be **slow**: driving blind eats whatever lies ahead, so a roam at 80 per s lost to one at
  20-40 (1.42 against 2.09-2.29).
- **Two poisons, not one**: a single poison is often eaten by accident (in the way of a food, or during a roam), and
  flipping on it sends the creature after poison until the next mistake. With n = 2, a creature is on the wrong
  colour for only about 1.5 s of a life. The count may fade within a second or two: when the creature follows the
  poison colour, poisons come in quick succession.
- **Trace (which eye saw most just before) misjudges** a quarter of poisons and a tenth of foods: a block of the other
  colour is often closer or more in view at the moment of a meal.
- Most poison is then eaten while scanning (turning in small circles near poison), not while approaching or learning.

**The circuit** (`discrete/circuits.py`, `learn_hold`; 49 parts): hold12 (the oscillator, motor A scanning, motor
B's pull-up from the hold) and

1. *the gate*: each eye's node feeds the hold through a diode, and a Darlington pair shorts it to ground while the
   latch feeds the pair's base (8 parts);
2. *the bit*: a latch of two cross-coupled NPNs, toggled by a falling edge through two steering diodes and capacitors
   (each junction resting at its own collector, so only the transistor that is on gets the edge; 12 parts);
3. *the doubt*: the taste node with a capacitor (each poison pulls it down by about 0.8 V; food lifts it; it recovers
   towards the supply through 1 GOhm over about 1.5 s), and two NPNs that turn its fall below about 0.65 V (the
   second poison in quick succession) into a sharp falling edge for the latch (7 parts);
4. *the roam*: a second, slow oscillator (7 parts, a beat every 2-3 s) whose discharge pulls its gate low and so
   turns on a PNP from the supply into the hold (3 parts): a phantom pulse, so both thrusters drive for a while.

Each piece was found by a failure on the bench (`bench` now takes taste pulses too):

- With the eyes on the latch's own collectors (6 parts fewer), every pulse of the shorted eye flipped the latch:
  the eye's microamp lifted the collector before the nanoamp base could take it, and the cross-coupling carried the
  lift to the other side as a flip. Speed-up capacitors (the textbook latch's) made it worse; 300 pF on each
  collector didn't cure it. Hence separate shunts.
- A 2N3904's gain collapses below a microamp (its base's recombination current, ISE, takes nanoamps at 0.45 V): a
  shunt fed 4.5 nA couldn't sink an eye's 1 uA, and the shorted eye still lifted the hold. With single shunts the
  latch needed tens of nanoamps (50 MOhm loads: on a bench scan of loads, 100 MOhm let the shorted eye lift the hold
  1-2 V, 200 MOhm fully), and the circuit drew about 440 nW, four times hold12. A Darlington pair for each shunt (2
  parts more) needs a hundredth of the base current: loads of 500 MOhm and 1 GOhm, the shorted eye lifting the hold
  0.16 V at most, the free one to 3 V, toggling right on every part draw tried; the circuit draws 180 nW.
- The threshold transistor's base loaded the taste node, holding it at 0.6 V, so that any single poison flipped the
  latch: its base resistor had to be as large as the node's pull-up.
- A resistor from the supply into the hold as the roam had no hysteresis: at 1 GOhm the hold never reached the
  motors' threshold (12% of lives stranded); at 150-300 MOhm it sat there and the creature drove blind without pause
  (efficiency -1.8 to -0.1, food:poison 1-2). Hence the oscillator, which needed its shunt within the switch's window
  (250-400 MOhm at a charging current near 1.4 nA; at 30-150 MOhm it never fired).

**First closed-loop results** (8 seeds x 2 lives x 100 s, values set by hand, `python -m discrete.poison`):

| circuit | efficiency [95%] | food:poison, last third [95%] | stranded | power | job (estimates) |
|---|---|---|---|---|---|
| hold12 (ignores taste) | -2.67 | 1.00 | 0% | 91 nW | no |
| learn_hold, roam by a 1 GOhm resistor | 0.76 [0.39, 1.09] | 3.46 [2.82, 4.15] | 12% | 401 nW | no |
| learn_hold, roam oscillator (ct2 3.3 nF) | 0.71 [0.39, 1.02] | 3.38 [2.62, 4.20] | 0% | 449 nW | yes |
| learn_hold, roam oscillator (ct2 5 nF) | 0.93 [0.67, 1.16] | 3.69 [2.67, 5.15] | 0% | 446 nW | yes |
| ... 16 seeds | 0.89 [0.66, 1.11] | 3.58 [2.98, 4.31] | 0% | 447 nW | yes |
| ... the roam only after the hold has been low a while (16 seeds; 3 parts more) | 0.69-0.85 | 3.3-3.7 | 0-3% | 446 nW | yes |
| ... Darlington shunts (16 seeds; 49 parts) | 1.21 [0.94, 1.47] | 4.16 [3.43, 5.01] | 0% | 179 nW | yes |
| **... held out** (32 seeds from 50000 x 2) | **1.12** [0.95, 1.27] | **3.48** [3.06, 3.92] | 2% [0%, 8%] | 182 nW | yes, sure but for stranding (and so with tight error control: D7) |

It learns: the latch flips 0-5 times in a life and settles on the food colour (seen live, `python -m discrete.watch
--circuit learn_hold --poison`: 13 red to 4 blue by 14 s with blue poison). Held out, it does the job by every
estimate, food:poison surely above 3, its one stranded life in 64 leaving the stranding interval's top at 8%. Against
the minimal search's chip circuits (efficiency 1.4-1.7, about 500 transistors each) it is less efficient, but it is 49
discrete parts.

A roam that waits for the hold to have been low a while (an NPN emptying the roam's timing capacitor while the hold
is above about 2 V), which doubled a policy's efficiency over a free-running roam (1.83 against 0.56-1.03), didn't
help the circuit (0.69-0.85 against 0.89, ties): its roams are short bursts (a phantom pulse, about 0.1 s of driving),
so they rarely interrupt an approach anyway. Left as an option (`rz1`), off.

**Tuned** (`python -m discrete.tune learn_hold 8 --poison --lam 8 --only cq rq ct2 rsh2 rb ch rt rp`: 8 values, 8
generations, poisoned pairs on training seeds): noise ruled it, the generations' means wandering 0.62-1.07 with no
trend. Its best mean (rt 215 MOhm, rp 11 MOhm, ch 460 pF, rb 10 MOhm, cq 3.1 nF, rq 1 GOhm, ct2 6.5 nF, rsh2 466
MOhm), held out: efficiency 1.24 [1.12, 1.36], gain 2.93, last third 4.49 [4.01, 5.10], stranded 5% (3 of 64), 181
nW. Paired with the hand-set values on the same lives, tied (efficiency -0.12 [-0.33, +0.09], gain -0.29 [-0.79,
+0.21]), and it strands more, so the hand-set values stay (the run's output kept as
`results/learn_hold_tune_tied.json`, which `watch` and `draw` don't pick up).

## D7: checking the simulation itself (2026-10-27)

Every result above was lived with SPICE's largest step at a twentieth of a tick (0.5 ms) and ngspice's default error
control. A finer step is the standing check (`--finer F` on `discrete.judge` and `discrete.poison`), and it first
seemed to undo D4 and D6; it was the check that misled.

- **At finer steps with the default error control** (held out): hold_drive went from 7.07 to 6.41 (x8), 6.17
  (x16), 6.21 (x32); learn_hold from 1.12 to 0.69 (x2), 0.05 (x4), -0.69 (x8), food:poison from 3.5 to 1.7. On the
  bench the scanning oscillator fired 462 times in 10 s at 0.5 ms and 526-545 at 62-16 us, so I took 31 us as
  converged and the earlier values as fitted to a slow oscillator.
- **But the roam never converged that way.** On the bench (learn_hold, 30 s, no eyes), motor B, which fires during
  roams, fired 85, 87 and 73 times at 31, 16 and 8 us: a marginal event, the roam's PNP barely turning on, decided by
  each step's rounding. With the error control tightened (`trtol=1 reltol=1e-4`), every step from 0.5 ms to 16 us
  agrees: the scan 1687-1697 firings, motor B 39-47.
- **With tight error control, the results stand** (held out, paired):

  | circuit | 0.5 ms, default control (before) | 0.5 ms, tight (now) | 62 us, tight | 0.5 ms, ten times tighter |
  |---|---|---|---|---|
  | hold_drive tuned, efficiency | 7.07 [6.84, 7.27] | 6.87 [6.63, 7.10] | 7.01 [6.88, 7.14], tied | 7.09 [6.70, 7.36], tied |
  | learn_hold, efficiency | 1.12 [0.95, 1.27] | 1.17 [1.04, 1.31], tied | | |
  | learn_hold, last third food:poison | 3.48 [3.06, 3.92] | 3.44 [3.08, 3.87] | | |
  | learn_hold, stranded | 2% (1 of 64) | 5% (3 of 64) | | |

  So `life.ACCURACY` (those options) is now in every netlist, and `life.STEP` stays 0.5 ms; lives take about 1.5
  times as long. The default control had been close enough at 0.5 ms, by luck, and wrong at finer steps.
- **Every circuit re-judged** with tight error control (held out, all food), against D4's values:

  | circuit | parts | efficiency [95%] | gain rate | power | D4 |
  |---|---|---|---|---|---|
  | hold_drive tuned | 14 | 6.87 [6.63, 7.10] | 19.1 | 72 nW | 7.07 |
  | hold12 tuned | 12 | 6.61 [6.38, 6.84] | 17.3 | 84 nW | 6.50 |
  | hold_drive screened | 14 | 6.39 [6.11, 6.60] | 19.5 | 85 nW | 6.62 |
  | straight tuned | 9 | 6.31 [5.51, 7.01] | 80.2 | 213 nW | 6.30 |
  | counter10 tuned | 10 | 4.33 [4.05, 4.59] | 7.5 | 84 nW | 4.06 |

- **The roam's window is narrow, but its parts stay inside it.** Its PNP turns on as the slow oscillator's gate
  dips, set by the ratio of rbe to rbg: with rbg 300 MOhm instead of 200, or rbe 25 MOhm instead of 50, it never
  fires (the hold peaks at 1.3 V); with rbg 140 MOhm or rbe 70 MOhm it never lets go (motor B fires at every beat).
  Between, across seeds' parts (1% resistors), it roams 8-10 times in 30 s, each dash 0.1 s. (With the default error
  control it had looked erratic, 3 to 11 roams and dashes of 0.01-0.4 s: the same rounding.) A capacitor from the
  gate to the PNP's base instead of rbg, to kick it on for a fixed time whatever the dip's depth, never fired: the
  gate falls too slowly.
- The lives of the misleading runs are kept in `results/coarse_default_tol/`.

## D8: why learn_hold strands, and a simpler circuit that doesn't (2026-10-27)

**The cause.** The three stranded held-out lives (seeds 50012, 50017, 50023, each with red as poison) re-lived with
their nodes recorded: each ate steadily (a meal every second or two), then for its last 50-70 s the latch sat still on
the right colour, the free eye saw nothing (its node never above 1 V), and the poison eye kept seeing blocks. Eaten
blocks reappear elsewhere, so a creature that eats every food near it and refuses the poison turns its patch into a
poison patch. Its roam, a phantom pulse every 2-3 s, fired motor B about twice a second there: dashes of 1-2 mm, a
random walk too slow to leave. So the job is a *giving-up time* (foraging theory's: nothing found here for a while,
go elsewhere), not hunger: the creature had eaten recently (the user's reading).

**Giving up, built** (a prototype on learn_hold's parts: a follower charging a slow node u, cu leaking through ru;
when u has sagged below a PNP's threshold, set by a divider rh1, rh2 from the supply to u, the PNP feeds the hold, so
both thrusters drive straight until u is lifted again). 16 training seeds x 2 lives, paired with learn_hold's 1.17
on the same lives:

| u lifted by | old roam | parts | efficiency [95%] | poison | stranded |
|---|---|---|---|---|---|
| (learn_hold) | yes | 49 | 1.17 [0.98, 1.36] | 1.81 | 2 of 32 |
| food (the taste node), divider too strong: never hungry again | no | 45 | 0.53 | 1.35 | 9 of 32 |
| food, giving up about 4 s after a meal | no | 45 | 0.58, worse | 1.97 | 1 |
| food, about 4 s | yes | 54 | 0.68, worse | 2.33 | 0 |
| food, about 15-40 s | yes | 54 | 1.03, tied | 2.10 | 0 |
| the eyes (a sighting of the followed colour), about 6 s | yes | 55 | 1.26, tied | 2.02 | 0 |
| the eyes, about 6 s | no | 46 | 1.33, tied | 1.77 | 0 |
| **... and the silenced eye empties the hold** | no | **48** | **1.54** [1.40, 1.68], better | **1.23** | 0 |

- The first divider fed u itself: with rh1 + rh2 against ru, u could never sag below about 1.87 V, above the
  threshold. Both now 500 MOhm and 1 GOhm: u floors near 1.2 V.
- Giving up on *food* runs too often, and a blind straight run through the poison patch it leaves eats poison (two in
  quick succession also flip the latch). Giving up on *sightings* (the time since the free eye last saw anything,
  D6's policy roam "3 s with nothing seen") is better and makes the old roam oscillator (10 parts) unneeded.
- **The circuit never avoided poison**, it only declined to approach it: its mouth eats whatever lies in its path,
  and a run covers ground. The silenced eye's current was going to ground through its shunt; moved to a resistor
  (rd, 1 MOhm) on the base of an NPN that empties the hold, it cuts motor B whenever poison is ahead, so the creature
  turns off its line (2 parts).

**Held out** (32 seeds from 50000 x 2, paired with learn_hold on the same lives; `learn_avoid` as it was in commit
5a14076, its netlists identical to the prototype's; pruned to 46 parts in D9; `results/learn_avoid_48_heldout.lives` and `.log`):

| circuit | parts | efficiency [95%] | gain | poison | last third food:poison [95%] | stranded [95%] | power |
|---|---|---|---|---|---|---|---|
| learn_hold | 49 | 1.17 [1.04, 1.31] | 2.95 | 1.90 | 3.44 [3.08, 3.87] | 3 of 64 [2%, 13%] | 174 nW |
| giving up and avoiding | 48 | 1.51 [1.29, 1.70] | 3.71 | 1.41 | 5.26 [4.72, 5.97] | 0 of 64 [0%, 5.7%] | 128 nW |

Surely better: efficiency +0.34 [+0.07, +0.56], gain +0.76 [+0.16, +1.31]. With 8 seeds more (50032-50039), 80
lives: efficiency 1.56 [1.36, 1.72], gain 3.82, food 6.50, poison 1.34, last third 5.56 [5.03, 6.23], **none
stranded [0%, 4.6%]**, 128 nW: every interval within its limit, so **the job surely done**, as learn_hold's never was.
Watched live (`python -m discrete.watch --circuit learn_avoid --poison --seed 50012`, a life learn_hold stranded in).

**Policies, to rank the options** (`discrete/policies.py`, hold and drive with learn toggle n 2, forget 1.5 s, the
circuit's speeds: scan and drive 56 per s, hold 0.08 s; 64 seeds x 2): avoid "drop" (poison ahead drops the hold, as
the circuit does) is best with every roam; turning away actively (two extra firings of one thruster per pulse) is
worst, below no avoidance; with no roam a third of lives strand. But at these speeds even the oracle policy (told
from birth which sensor sees food; `oracle`) reaches only 1.41, below the circuit: the rule's speeds were wrong, so it
is no ceiling. (`until_seen`: a roam lasting until the next sighting, as the circuit's run does.)

**The ceiling** (the same rule over scan 8-56, drive 40-160 per s, hold 0.05-0.2 s, either roam, avoid "drop"; 64
seeds x 2): told the answer from birth, **2.73** (scan 16, drive 40 for 0.2 s after a sighting; drive 80 for 0.1 s or
160 for 0.05 s within 0.05: about 8 straight firings a sighting); learning (toggle, n 2), **2.29** at the same
settings. So, within this family of rules, learning costs about 0.4, and the circuit (1.51) loses another 0.8, mostly
to its speeds: it scans 3.5 times too fast, and its drive can't outrun its scan (both thrusters fire off one
oscillator's beats). The giving-up run and the clock roam tie as rules (2.17 against 2.29), so the run's 10 fewer
parts decide.

**The policy's speeds don't carry over to the circuit.** Tried on the 48-part circuit (16 training seeds x 2):

- *The hold speeding the oscillator* (hold_drive's rf, from the hold to the timing node), with the scan slowed to
  17-21 per s (ct 1-1.3 nF): here the hold rests near 0 V (motor B drains it at every beat), so rf drained the timing
  node and the oscillator nearly stopped (48 firings per 10 s, 75% of lives stranded). Through a diode (1 part more),
  30 MOhm gave a 17-21 per s scan and a 50 per s drive on the bench, but draining the hold through rf left one
  sighting 1 straight firing instead of 5 (100 MOhm stalled the oscillator). Not pursued.
- *Policies with the drive tied to the scan* (one oscillator, as in the circuit; 64 seeds): best 1.76 at 20-24 per s
  and hold 0.2-0.35 s (5-7 firings a sighting), against 0.82-0.96 at 56 per s. The circuit's hold buys about 5
  firings a sighting whatever the rate (it drains by a fixed charge a firing), so slowing its oscillator alone should
  have matched that policy. **It didn't**: ct 1 nF (about 21 per s) 1.04, ct 800 pF 1.14, both surely below 1.54 at
  56 per s (-0.50 [-0.78, -0.21], -0.41 [-0.71, -0.13]); food fell by half (3.3-3.8 against 6.2). The circuit at 56
  per s also beats its own policy at 56 per s (1.54 against about 0.9): what the circuit does (a hold topped up by
  each pulse, motor B's firings draining it, the run at the scan's rate) isn't what the rule does, so the rule's best
  settings don't transfer. A policy ranks *structures* (avoid by dropping the hold; giving up; some roam needed) but
  not a circuit's values.

## D9: pruned to 46 parts, and a stranding from a perfect body (2026-10-27)

**Pruning** (`python -m discrete.prune results/learn_avoid_start.json --poison --seeds 12 --seconds 40`, training
seeds 30000-30011 x 2, about 6 h; `results/learn_avoid_prune.log`). `prune.py --poison` now lives each seed red then
blue as poison and resamples each seed's pair together; a cut must do the job; a cut surely worse than the whole, or
failing the job, is dropped for good (so after the first round of 128 only 4 were retried); `--resume` restarts from
the cuts saved after each one (comparing against the circuit resumed from, not the original). It took 3 parts
(`results/learn_avoid_pruned.json`; its line numbers are the 48-part netlist's, commit 5a14076):

| cut | parts | robust (training) |
|---|---|---|
| (the whole) | 48 | 1.72 |
| rh2 (ub to u) shorted | 47 | 1.89 |
| rh1 (the supply to ub) removed | 46 | 1.78 |
| rs of the latch's side 0 (c0 to j0) removed | 45 | 1.53 |

then nothing more could go. Held out (seeds 50000-50039 x 2, the cuts applied to the 48-part netlists), the last cut
was a fluke of 12 seeds: 45 parts 1.22 [0.72, 1.66], surely below 46 parts (-0.61 [-1.13, -0.10]). So a cut "not
surely worse" on few seeds can still be worse: every pruned circuit is judged held out, cut by cut if need be.

**The divider wasn't needed.** With the PNP's base on u itself, u sags until the PNP's own base current balances ru's
leak (it settles near 2.57 V, the PNP feeding the hold about half a microamp): the threshold sets itself. `learn_avoid`
is now this 46-part circuit (`circuits.py`, `media/learn_avoid.svg`); removing two resistors changes each seed's
tolerance draws for the four parts after them, so it was judged afresh:

| held out | parts | efficiency [95%] | gain | poison | last third food:poison [95%] | stranded [95%] | power |
|---|---|---|---|---|---|---|---|
| learn_avoid, 48 (D8), 50000-50039 | 48 | 1.56 [1.36, 1.72] | 3.82 | 1.34 | 5.56 [5.03, 6.23] | 0 of 80 [0%, 4.6%] | 128 nW |
| learn_avoid, 46, 50000-50079 | 46 | **1.78** [1.62, 1.91] | **4.73** | 1.89 | 4.70 [4.27, 5.16] | **0 of 160** [0%, 2.3%] | 130 nW |

Paired on 50000-50039: efficiency +0.24 [+0.07, +0.38], gain +0.94 [+0.48, +1.33], **surely better on both**, the
job surely done (`results/learn_avoid_46_heldout.lives` and `.log`). It eats more of both: food 8.5 against 6.5, and
poison 1.9 against 1.3 (food:poison in the last third 4.7, still well above 3). Giving up sooner and harder, it
covers more ground.

**A stranding from a perfect body.** The pruning's own netlists stranded one life in 160 (seed 50010, red as poison):
from 52 s on, both thrusters fired equally (a giving-up run), the eyes saw nothing, and a replay of its firings through
the body showed why: its heading was 0.004 rad off the world's y axis and its spin exactly 0 (identical thrusters), so
on the torus the run retraced one column, which it had eaten clear, for 48 s (x drifting 48.1 to 47.2 mm). The world
spawns a block only when one is eaten, so the column stayed empty. A body whose thrusters differ, as any built one
would (D5; README: the body must vary), curves on a straight run. A second reason for varying bodies: an exactly
straight run is an artefact the circuits can be stranded by, and so could come to depend on.

## D10: where the circuit spends, against the best policy (2026-10-28)

The best learning policy (D8's ceiling grid: scan 16 per s, drive 40 per s for 0.2 s after a sighting, giving up
after 3 s at 20 per s, poison dropping the hold) is more efficient than `learn_avoid` (2.08 against 1.78 on seeds
50000-50039 x 2) but slower (gain 3.59 against 4.73). Both lived on those 80 lives, every tick recorded (the circuit's
firings replayed through the body give the same meals; a scratch analysis): what the eyes saw, each sensor's pulses,
the bit, each meal. Modes: *approach* (motor B fired in the last 0.1 s and the followed eye pulsed in the last 1 s),
*run* (B firing, nothing seen), *scan* (B idle).

| per life (100 s), means | circuit | policy | circuit, ct 1 nF (21 per s) | policy, scan = drive = 21 |
|---|---|---|---|---|
| firings per s: approach / run / scan | 27.0 / 20.5 / 28.5 | 23.1 / 5.2 / 8.2 | 12.0 / 11.1 / 8.1 | 15.6 / 6.7 / 9.1 |
| share of time: approach / run / scan | 29% / 19% / 52% | 35% / 13% / 52% | 33% / 28% / 40% | 39% / 17% / 45% |
| food in approach, per life | 78.2 | 57.1 | 28.3 | 42.5 |
| poison: approach / run / scan | 11.6 / 2.75 / 4.65 | 7.0 / 0.11 / 4.56 | 4.6 / 1.6 / 4.3 | 5.8 / 0.1 / 3.6 |
| food sightings per 10 s | 5.2 | 5.3 | 4.7 | 4.9 |
| a block in view: ms, pulses | 20, 0.56 | 62, 1.73 | 47, 1.47 | 46, 2.01 |
| bit right, flips, learned at | 96%, 3.8, 20 s | 94%, 1.2, 24 s | 90%, 2.6, 22 s | 91%, 1.1, 24 s |
| mm per s | 37 | 18 | 16 | 16 |

- **Learning isn't the gap**: both have the bit right about 95% of the time, learned by about 20 s.
- **Approaching isn't either**: the circuit's approaches yield as much food per firing as the policy's (0.029 against
  0.025 food a firing) and, at 54 pairs a second, more food per second: its higher gain.
- **Scanning is wasted**: one thruster at 54 per s spins it 2.7 turns a second, a block crossing its view in 20 ms
  and giving 0.56 pulses; at 16 per s, 62 ms and 1.7. Food is *sighted* equally often either way (5.2 per 10 s): a
  single thruster's firings trace the same 1.25 mm circle at any rate, so spinning faster re-sweeps the same view.
  20 firings per s, 0.4 meals per 10 s, buy nothing.
- **Running is costly and eats poison**: the giving-up run fires both thrusters at the scan's 54 per s (108 a second
  against the policy's 40), for 19% of the life, and runs into poison (2.75 a life against 0.1, each costing 2
  meals): a poison sighting empties the hold for a moment, but u is still low and the PNP refills the hold, so the
  run goes on. In the policy a poison sighting ends the run.
- **Why slowing the oscillator failed (D8)**: it slowed the approach too (the drive is the scan's beat), and its
  approaches then yielded a third of the food (28 against 78), with drive time without sightings up to 28%.

**Policies on the same lives, to rank the structures** (giving up 3 s, poison dropping the hold, learning toggle n 2):

| policy | efficiency | gain | poison |
|---|---|---|---|
| the circuit's speeds (scan, drive and run 54, hold 0.08 s) | 0.92 | 2.18 | 1.84 |
| ... scan 16 | **1.95** | 3.47 | 1.44 |
| scan 16, drive 54 for 0.15 s, run 20 | **2.29** | **4.11** | 1.21 |
| scan 16, drive 40 for 0.2 s, run 20 (the grid's best) | 2.08 | 3.59 | 1.17 |

A slow scan with a fast drive more than doubles the circuit-like policy, and the best mix beats the grid's best on
both measures. (The circuit itself beats its own-speed policy, 1.78 against 0.92: its hold, topped up by each pulse
and drained by each firing, approaches better than a timer; so the values won't transfer, D8, but the structure
should.)

**Suggestions, in order of expected worth** (spending: a firing 0.002 meals; the circuit spends 2.65 meals per 10 s,
1 resting, 1.52 firing, 0.13 its own power):

1. *Two speeds*: the oscillator slow (about 16-20 per s) while the hold is empty, fast while it is up; a switched
   resistor beside rt, its switch driven from h through a high resistance (so as not to drain the hold, as D8's rf
   did). Saves about 20 firings per s in scan: spending 2.65 to about 2.25, efficiency about 2.1 at the same gain,
   if the approach is unchanged. About 3-4 parts.
2. *Poison ends the run*: the silenced eye's current (at k) also lifts u, as a sighting does (an NPN on k pulling a
   PNP from the supply into u, about 3 parts). Removes most of the 2.75 poisons a life eaten in runs: gain about
   +0.5 per 10 s.
3. *A slower run*: the run at the slow speed rather than the fast (with 1, the PNP into h should not also speed the
   oscillator); about 15 firings per s less, but the policies don't say a slower run is better on its own.

Together, if each works as measured: spending about 1.95, gain about 5.2, efficiency about 2.7, above the policy
ceiling found so far on both measures.

## D11: D10's suggestions in bipolars, and why they fight the parts (2026-10-28)

Each tried on `learn_avoid` (scratch prototypes; training seeds 0-15 x 2, where `learn_avoid` scores efficiency 1.70,
gain 4.47, 750 firings per 10 s):

| change | parts | efficiency | gain | firings | why |
|---|---|---|---|---|---|
| the hold speeding the oscillator through a follower and rf | 48 | 0.0, -0.9 | | 460-520 | the oscillator stalls (below) |
| two speeds by capacitance: 1 nF switched in while the hold is empty | 52 | 1.74 | 3.91 | 551 | half works: the diode's drop leaves the capacitor coupled for only part of the swing (32-37 per s, not 18) |
| a second oscillator for the drive, from the hold; the scan suppressed while it runs | 56-58 | 0.4-1.2 | 0.9-2.3 | 365-590 | approaches too short: the drive oscillator drained the hold, or (through a follower) slowed as it sagged, and the half-way states of scan and drive overlapped |
| poison resets the giving-up timer | 49 | 1.41 | 3.42 | 639 | 9% stranded: in a poison patch every sighting resets it |
| **poison lifts the giving-up timer partly** (rpku 300 MOhm) | 50 | **2.01**, surely better | **5.29**, surely better | 744 | |

Held out (seeds 50000-50039 x 2) the last was tied with `learn_avoid` (efficiency 1.89 against 1.78, +0.09 [-0.04,
+0.23]; gain +0.26 [-0.12, +0.63]): not kept.

**Why the bipolar circuits resist two speeds.** At the nanoamps that keep power down, a 2N3904's gain collapses (its
base leakage, the model's ISE, takes most of the base current: about 400 falls to about 20 at 0.39 V). The oscillator's
regenerative pair then has too little loop gain: with too little timing current it settles half on instead of
snapping (a at 0.89 V, b at 0.21 V); with too much it latches. An astable multivibrator at these currents sat in its
DC state, both transistors half on. Every state in between (a hold half drained, a timer half sagged) leaves the
circuit in a half mode. Positive feedback, which makes decisions clean, needs gain the parts don't have at these
currents; complementary parts (CMOS) draw nothing at rest, so they can switch with gain to spare (the user's point).

## D12: the best policy in SKY130 CMOS (2026-10-28)

The user's decisions: parts readily realisable in SKY130 (its 1.8 V core MOSFETs, R, C, diodes, bias sources), for
the power merits of complementary designs and the clean decisions of positive feedback. `Netlist(chip=True)` and
`Netlist.M` (`life.py`); the eye's and taste's pulse 0.9 nA (`CHIP_EYE`), a motor input 0.1 pF.

**A copy of the best policy** (D10: scan 16, drive 40, hold 0.2 s, bored after 3 s, the bit toggled by two poisons
within 1.5 s; a scratch circuit, 126 parts, 116 of them MOSFETs): starved Schmitt triggers read each eye, OAI22 gates
pick food and poison by the bit, a hold and a boredom capacitor each read by a Schmitt, one oscillator with a slow and
a fast pair of starved current sources, a master-slave flip-flop of transmission gates for the bit. Every mode works
on the bench at 2.5 nW. Closed loop (seeds 0-7 x 2):

| version | efficiency | gain | food | last third | firings | power |
|---|---|---|---|---|---|---|
| first | 0.26 [-0.58, 1.06] | 0.39 | 3.1 | 5.6 | 245 | 10 nW |
| the doubt window widened (below) | 0.53 [0.02, 1.08] | 0.79 | 3.1 | 3.0 | 240 | 11 nW |
| `learn_avoid` (bipolar), same lives | | | about 8 | | about 750 | 130 nW |

Both surely worse than `learn_avoid` (gain -3.8, -3.4); power a twelfth of it. Replayed through the body (D10's
analysis): learning failed in 5 of 16 lives (seed 6 red ate 23 poisons, the bit never flipped), the approach succeeded
after half the food sightings (`learn_avoid` 0.86), and the first motor-B firing came 49 ms after a sighting (0).

- **The doubt window was a fraction of a second.** Two poisons flipped the bit only if the second came before the
  taste node recovered, under a second, where the policy's window is 1.5 s; widening it needs about 0.6 pA, below
  the chip's 1 pA. Each poison's charge is fixed by the interface, so it is copied four times over by a pMOS mirror
  into an 8 pF doubt node drained by a 40 um long leak: one poison never flips the bit, two up to 1.5 s apart do (seeds
  0 and 6, on the bench). Food no longer resets doubt.
- **A pMOS's current isn't proportional to its width** at these currents in SKY130 (W 1 to 8 um: 0.93 to 1.28 nA at
  the same gate voltage; the threshold moves with width): a mirror's gain is built from unit copies.
- **A width below the models' range doesn't simulate**: varied by the seed, a 0.42 um pMOS fell below the narrowest
  bin and ngspice refused it, three hours in. Widths are now floored at 0.36 um (nMOS), 0.42 um (pMOS).
- **BSIM4 runs on OpenMP threads**: 8 lives at once ran 17 times slower than one. One thread each (`life.py`) gives
  2.3 times, the laptop's cores sharing its power. A 100 s life alone takes about 5.5 min (3.3 s a second of life);
  the bipolar circuits about 15 s.
- **So design moves to the fast model** (the user's decision, AGENTS.md): blocks measured on the bench, given to the
  policy, the policy checked against the circuit's own lives, SPICE to verify and judge.

## D13: the fast model, and what the hand-design suggests (2026-10-28)

**The model** (`scratchpad/cmodel.py`, to move into `discrete/`): the CMOS policy circuit as its blocks' measured
behaviour, each block a few lines, its numbers from short bench runs (`blocks.py`): eye 1.4 ms delay, 10 ms hold;
drive hold 63 ms after the last food pulse (the policy's: 0.2 s); boredom 2.7 s; scan 12.3, drive 44, run 12.6 per s;
doubt +1.12 V a poison, leaking 0.43 V/s, the bit flipping as doubt rises through about 1.5 V and re-arming only below
0.23 V (3.6 s after a flip, a third poison did nothing). On the same 16 lives as ngspice it is tied with the circuit
(efficiency -0.36 [-0.99, +0.37]; food 3.41 against 3.14, firings 238 against 240), a life in about a second
against 5.5 minutes. With motor B fired on each food pulse it was worse than the circuit (-0.65 [-1.11, -0.19]):
two firings close together count twice in the model, once in the circuit (a motor re-arms between them); both said
the option hurts.

What it showed in minutes (seeds 0-63, efficiency):

| change | efficiency |
|---|---|
| as built | 0.36 |
| drive hold 0.2 s (the policy's) | 1.05 |
| ... and doubt cleared by a flip | 1.72 |
| ... and by food tasted | 1.88 |
| ... but by food *seen* instead | -1.1: while the bit is wrong, "food" seen is poison, so doubt is wiped and it never flips |
| doubt's leak 0.3 V/s instead of 0.43 (no clearing) | about 0 |

A coordinate search (seeds 0-127): no clearing 1.91 (three poisons to flip); cleared by a flip 2.25, about the best
policy's 2.3. Both pushed boredom to the search's limit (8 s): the give-up as built barely helps.

**Doubt is a CUSUM** (the user asked, MacKay's way, whether it is Bayesian). Two hypotheses about the current bit, W
(wrong) and R (right), exhaustive, so one number carries the belief: the log-odds, to which each event adds its log
likelihood ratio. A poison adds log(lambda_W / lambda_R), a fixed step (the mirror's charge); food subtracts a large
step; silence drifts at the difference of the total event rates (a constant leak: the leak is a current, not an RC).
The floor at 0 V (doubt holds evidence against the bit, never confidence in it) makes it Page's CUSUM (1954), the
optimal detector of a change (Lorden 1971); the threshold is Wald's sequential test, a decision (false flips against
delay), not inference; the restart after the alarm is the reset on a flip; food's large step down, floored, is the
reset on food. All three of the model's improvements are the CUSUM's own rules; the trap (clearing on food seen) is
evidence with a likelihood ratio of about 1 taken as strong. Suggestive, not proven: leak / step should be (lambda_W -
lambda_R) / log(lambda_W / lambda_R); the circuit's 0.43 / 1.12 = 0.38 per s, the bipolar's measured poison rates
(0.18 per s right, 0.72 wrong) give 0.39, the CMOS circuit's own rates 0.17, the search chose 0.23 (with clearing on
a flip). Where it isn't Bayesian: evidence comes in bursts (the creature clears food around it, leaving poison; chance
clumps; an approach to food can sweep through a poison beside it), so two poisons close together mean less than two
independent ones; and the data depend on its own actions. Blocks are placed uniformly; food and poison may touch
(about 6% of food blocks touch a poison): kept so, the user's decision.

**But our world never changes in a life**, so the CUSUM's floor, right for a world that changes, throws away
confidence: after 50 meals two poisons flip the bit as at birth. A Bayesian here lets food build confidence (doubt
resting mid-supply, food pulling it down, poison up, bounded against bursts), so its learning rate falls as trust
grows. To test.

**Two variables per unit** (the user's thread). Belief needs one number (the log-odds); acting on it without
dithering adds one more bit of state, which way it last decided (hysteresis is a memory). The same in physics
(position needs momentum to carry the present to the future), excitable media (the sheet brain's ignition and supply;
FitzHugh-Nagumo's fast and slow variables), asynchronous cellular automata (a refractory state where a classic CA has
a global clock): a one-dimensional autonomous system can only settle; keeping time needs two (Poincare-Bendixson).
Every block of the CMOS circuit is that pair, a fast bistable (a Schmitt, the flip-flop) and a slow leaky integrator
(a capacitor and a starved current): Sepulchre's fast positive with slow negative feedback, reached from below. The
building block to design with is that pair; what differs from block to block is what feeds it and how fast it leaks.

**Time constants against delays.** A loop with delay that reacts faster than its delay oscillates, so each slow
variable must outlast the loop it closes: drive hold (about 0.2 s: the gaps in an approach), doubt's window (about
1.5 s: an approach into its taste), boredom (seconds: a search). The circuit's 63 ms hold, shorter than its gaps,
cost two thirds of its efficiency.

**How fast to learn is itself worth knowing** (the user's): the right timescale depends on evidence's noise, the
world's volatility, the loop's delay and how much is already known (a Bayesian's precision sets its learning rate:
the second variable is the learning rate). We set it now from outside (the search); whether the brain should learn it
depends on whether the best timescale differs from life to life in ways a unit can see locally (its input rates, its
reversals, the delay from its outputs to their consequences). A unit tuning its own time constant from its own
signals is self-optimisation without a god: the project's real goal.

**Stigmergy** (the user's): eating writes to the world (food cleared nearby), the eyes read it back, so the world holds
"been here". Poison *seen* with little food seen says "this patch is spent" (leave); poison *tasted* says "the bit is
wrong" (flip): two hypotheses with opposite remedies, told apart by the sense the poison comes through. Charnov's
marginal value theorem (1976): leave when the local rate falls below the habitat's; as circuit, two leaky integrators
of food seen, a fast and a slow, compared. D11's "poison seen lifts the give-up timer" was this, half done.

**Results overnight** (`scratchpad/cmodel2.py`, `msearch2.py`: each variant searched on seeds 0-127 from the best
so far, then judged on 50000-50127, paired; nominal blocks, no tolerances yet):

| variant | efficiency held out | gain |
|---|---|---|
| A: doubt cleared by a flip and by food tasted | 2.15 [2.05, 2.25] | 3.63 |
| **B: confidence** (doubt down to -1.8 V, food -0.75 V, recovering at 0.04 V/s; a poison +1.12 V, threshold 0.8 V, leak 0.30 V/s) | **2.39 [2.30, 2.48]** | **4.05** |
| C: A, and each poison seen ages the boredom timer 0.14 s | 2.18 [2.09, 2.28] | 3.64 |
| D: A, leaving by a Charnov comparator (food seen fading over 2 s against 15 s; leave below 0.15 of it) | 2.20 [2.10, 2.29] | 3.69 |
| E: doubt cleared by a flip only | 2.12 [2.01, 2.22] | 3.58 |

**B is surely better than every other** (against A: efficiency +0.24 [+0.14, +0.36], gain +0.42 [+0.23, +0.61]);
the rest are tied with each other. So confidence pays, as predicted: at birth one poison flips the bit, after a run of
meals three are needed; the learning rate falls as trust grows. Two of B's settings sit at the search's limits (the
threshold at 0.8 V, trust at -1.8 V): it may go further. Leaving by stigmergy (C, D) gains nothing over boredom in
this model (both searches pushed boredom out, to 14 s in C); clearing on food adds nothing once a flip clears (A tied
with E). Not yet with tolerances or varied bodies.

**Judged robustly** (`scratchpad/cmodel3.py`). The blocks benched in ngspice on 32 seeds (`blocks.py`), each
number's spread over the seeds' tolerances (sd of its log): eye hold 0.08, drive hold 0.14, boredom 0.21, scan and run
0.10, drive 0.07, doubt's step 0.05, its leak 0.17; doubt's lower threshold 0.23 V within 0.01 (the upper one, not
measured cleanly, taken as 0.02 V); assumed: a block redesigned keeps its relative spread. Each life then draws its
own blocks; with bodies, its own thrusters (each 0.5 to 2, `bodies.THRUSTERS`). Held out (50000-50127):

| variant | nominal | with tolerances | with tolerances and bodies |
|---|---|---|---|
| A | 2.15 | 1.06 [0.70, 1.37] | -0.27, 15% stranded |
| B (confidence) | 2.39 | **2.38 [2.29, 2.47]** | **0.32 [0.17, 0.49]**, 11% stranded |
| C | 2.18 | 1.03 | -0.09, 14% |
| D | 2.20 | 1.09 | -0.18, 13% |
| E | 2.12 | 0.99 | -0.31, 16% |

- **Every search but B's had exploited a knife-edge.** A, C, D and E set doubt's threshold at 1.79 V, a hair under its
  1.8 V ceiling (three poisons to flip); with tolerances 26% of lives drew it above the ceiling, so their bit could
  never flip. B's threshold, 0.8 V, is nowhere near: B is unmoved by tolerances, and surely better than A by +1.32
  [+0.97, +1.72]. The nominal model let the searches exploit it, "nor may the simulator"; the robust judge caught it.
- **Lopsided bodies defeat every fixed design**: B falls to 0.32, 11% of lives stranded, none does the job (B still
  surely best, +0.60 over A). A thruster at half strength makes the scan slow and the drive curve; a straight run
  becomes a circle. So the question of a brain adapting to its body is now the main one.

**Evidence is barely bursty** (`scratchpad/bursts.py`, B in the fast model with tolerances, 256 lives): with the
bit right, poison is eaten at 0.094 per s; within 0.5, 1, 2, 5 s after a poison at 1.04, 1.11, 1.07, 0.99 times that;
after a food at 1.47, 1.33, 1.13, 0.97 times (blocks lying close together), but a meal has already stepped doubt
down. So poisons are close to independent evidence, and counting each as a full step is sound: the worry about bursts
(above) was small.

**Do the best timescales vary from life to life?** (`scratchpad/timescales.py`: B with tolerances, bodies each
thruster 0.5-2 with the drive balanced by the oracle, seeds 0-127 x 2 grouped by strength, sqrt(left x right), into
thirds; efficiency):

| setting | weak | middling | strong |
|---|---|---|---|
| hold 0.1 / 0.2 / 0.4 s | 1.40 / **1.88** / 1.80 | 1.87 / **2.08** / 1.66 | **2.14** / 1.95 / 1.51 |
| drive 30 / 44 / 65 per s | 1.74 / 1.88 / **1.90** | 2.01 / **2.08** / 1.84 | **2.23** / 1.95 / 1.42 |
| boredom 3 / 6 / 12 s, scan 8 / 12 / 18 per s | flat within noise | | |

Yes, predictably: a strong body wants a slower drive and a shorter hold, a weak one the reverse (what matters is the
body's speed, rate x strength). But adapting them is worth about +0.1 overall (the oracle restoring every firing got
2.00 against balance alone's 1.92), against the balance's +1.6. Doubt in B has no timescale left to learn.

**The ladder's top rung: an omniscient brain** (`scratchpad/omni.py`; QUESTIONS.md). Told every block's place, its
own pose and wiring and which colour is food, it steers to the nearest food whose straight path passes no poison
(turning with the thruster that turns it towards it, allowing for the spin to come; pushing with both while it points
there and goes slower than a cap). Held out (50000-50063 x 2, standard bodies): **efficiency about 20 [19, 22], gain
about 58, food 52-65 per 10 s**, against B's 2.4 and 6. Even so it strands 9-16% of lives (it circles a target it
can't turn tightly enough for): a lower bound. So these organs leave about ten times today's performance to a brain
that knows where things are; the mapping rung (legal inputs only) will say how much of that knowledge can be had.

**A short memory rung** (`scratchpad/memo.py`: B's blocks with tolerances, told which colour is food and its own
heading, as perfect path integration would give; having lost sight of food it turns back to the heading where it last
saw it, within so many s, then drives; held out, 50000-50063 x 2): without memory 2.54 [2.40, 2.66]; with 0.5-4 s of
it about 2.0, worse. A first version was far worse (down to -2.0: it went back for food it had just eaten, ignoring
poison in view); cleared by any taste and by poison seen, still worse: turning back costs firings and time, and a
heading without a range rarely points at the block, lost because the creature moved past it. A memory pays only with
range too: the mapping rung. And a by-product: **told the colour from birth, B gets 2.54; learning it, 2.39** (the
same lives otherwise): learning costs it 0.15. The learning is near ideal; the headroom (to the omniscient 20) is all
in finding food.

**The seer rung, and what a map is worth** (`scratchpad/seer.py`): told the exact place of each block the moment an
eye pulses for it (the nearest of that colour in the corridor), remembering it until eaten, told its pose and which
colour is food; steering (as omni.py) to the nearest remembered food with no remembered poison on its path, scanning
with one thruster when it knows none, and after 2 s of that running straight 0.5 s (without the run it ate what it
had seen and then scanned in place: 70% stranded). Held out (50000-50063 x 2): **efficiency 4.53 [4.34, 4.73], food
9.7 per 10 s**, 2% stranded. The ladder, every rung told the colour:

| rung | efficiency | food per 10 s |
|---|---|---|
| omniscient (knows every block) | about 20 | about 58 |
| seer (a perfect map of what it has seen) | 4.5 | 9.7 |
| B | 2.54 | 6.1 |

A perfect map of what it has seen would nearly double B: that is the most intelligence (remembering and placing
blocks) can buy behind these eyes. The rest, 4.5 to 20, isn't intelligence but coverage: an eye's corridor (2 mm
wide, 15 mm long) never sees most blocks. A first mapper inferring places from pulses (`scratchpad/mapper.py`, an
evidence grid) failed (0.6 food per 10 s): scanning from one spot, an eye can't tell how far a block is, so every
cell of the corridor looks alike; it needs ranging by moving (parallax, the pulse rate as it nears).
Given the seer's exploring run and lower thresholds it still got only about 1 food per 10 s (16 seeds x 2), firing
about 900 times per 10 s: each pulse credited every cell along the corridor as strongly as if the block were in each,
so the map filled with false lines of food. A sound mapper needs a proper sensor model (one nearest block per
corridor, the evidence shared out along it): a substantial build, left open.
A second mapper with that sensor model (`scratchpad/mapper2.py`: an occupancy grid; each tick, per eye, the chance
that the nearest block of its colour lies in each bin along the corridor, or none, weighed by the pulses' Poisson
likelihood; bins nearer than it emptied, it filled, those behind kept): judged cell by cell no cell passed 0.32 (the
evidence spreads over the corridor's width) and it ate blind; judged by a block's chance within a block's size, it
avoids poison well (food:poison 8 in the last third) but finds only 2.0-2.4 food per 10 s, firing about 800 times
(efficiency 0.45-0.65, 16 seeds x 2). Still a poor lower bound: a mapping brain that beats B is possible (the seer's
4.5), but building one is a robotics project of its own.

**Reversal: confidence, bounded, doesn't cost it** (`scratchpad/reversal.py`; an experiment only, the task never
swaps): the poison colour swapped at 50 s, B against E (doubt floored at 0), tolerances, 50000-50127 x 2. Just after
(50-70 s) B eats food 4.87 and poison 2.16 per 10 s (ratio 2.3), E 4.10 and 2.88 (1.4); in the last 20 s B 6.04 and
1.00 (6.0), E 5.62 and 1.46 (3.9). B's trust is bounded (about two and a half meals' worth), so two or three poisons
undo it: the bound is the hedge a Bayesian makes against a world that might change. So B gets both: it keeps trust
where the world is steady and reverses when it isn't.

**Adapting to the body** (`scratchpad/cmodel4.py`; held out, tolerances and bodies each thruster 0.5 to 2):

| brain | efficiency | stranded |
|---|---|---|
| B, fixed | 0.32 | 11% |
| the best fixed design for such bodies (searched on them) | 0.76 [0.65, 0.88] | 7% |
| B, the drive balanced for its body (told it: an oracle) | **1.92 [1.82, 2.02]** | 0% |
| B, every firing restored to the standard body's (oracle) | 2.00 [1.91, 2.09] | 0% |
| B on standard bodies | 2.38 | 0% |

Straightening the drive recovers nearly all of it: one number per life, the ratio of the two motors' drive rates (the
rest is physics: a weak body is slower). So the target for adapting is a single balance, worth up to +1.6.
- **Extremum seeking** (each approach nudged one way, alternately; its food pulses against their running mean move the
  balance the way its nudge went; all local to the drive): 0.15 to 0.53 on training seeds (0-63). It finds the right
  balance in about half the lives, in 40 to 60 s of a 100 s life; others never get there. Slow, because each
  approach's signal is weak and noisy.
- **A dead end: the time to re-find a lost block as the balance's sign.** I reasoned that a drive curving with the
  scan loses its block on the far side, found again late, and one curving against it on the near side, soon. Measured
  (balance set wrong on purpose by -0.6, 0, +0.6, 40 lives each): median re-find 0.75, 0.46, 0.47 s. It is shortest
  near the right balance, an extremum, not a gradient; used as a sign it made things worse (to 30% stranded).
- **Extremum seeking's settings searched** (step 0.02-0.05, nudge 0.15-0.35, averaging over 3 or 8 approaches):
  every one about 0.4-0.5; the signal, not the settings, limits it.
- **A dead end: system identification from the scan.** Scanning alternately with each motor, the world sweeping past
  should show each motor's turn. Sightings begun per firing came out reversed (a slow sweep breaks one block into
  several sightings, a fast one misses some); pulses per firing pointed the right way but compressed to 0.14 of the
  truth (residual sd 0.22: inverted, an error of 1.6), the forward motion each firing also gives drowning the turn.
  The alternating scan alone cost a little (-0.12 against 0.15: it re-covers ground).
- **Sweeping back the other way after a lost block** (a feedback, not a learned number): no help (about 0.0). The
  block isn't lost behind it: a lopsided drive circles past it. Straightening needs steering during the drive, and an
  eye's corridor gives no side.
- **A dead end: a zigzag within each approach** (the balance wobbling every 0.1-0.4 s, the food pulses in its two
  halves compared, lock-in style): no better than not adapting (-0.12 to 0.10, up to 26% stranded). A first try was
  biased (every approach began in the same half, its first moments rich in pulses: the balance ran to its limit on
  every body). The deeper reason: a block wholly inside an eye's corridor pulses the same wherever it lies in it, so a
  small wobble changes nothing the eye sees until the block leaves; the wobble only spoils approaches.
- **Given time, extremum seeking stalls** (`scratchpad/longbody.py`: one body kept 300 s, each 100 s judged, seeds
  0-63 x 2): with small steps (0.01) 0.37, 0.81, 0.83; larger (0.03) 0.38, 0.45, 0.49; not adapting about 0.2; the
  oracle 1.9-2.1. Time doubles it, then it settles at less than half the oracle: its estimate never gets precise, each
  approach's signal too noisy. Weak in itself, not merely slow. A meal ending an approach added to its reward (as 5
  or 20 pulses): 0.49 and 0.11 against 0.37, within noise or worse.
- So far, on such bodies, the best brain is the fixed design searched on them (0.76 held out) or extremum seeking
  (about 0.5 in a life, 0.8 given three), against the oracle's 1.92. The eyes carry little about the balance's sign within an
  approach; open.


**The user's decisions** (2026-10-29): the body stays as it is (learning a lopsided body's balance likely takes more
than a 100 s life, and eyes that show which way it curves); no mapping brain now; robust judging and the log-uniform
thrusters confirmed; B's bench to be rerun four at a time.

The plan, in the model (seeds 0-127 to tune, held out from 50000 to judge), then the best in transistors, its blocks
benched, verified closed loop in ngspice and judged held out:
1. clearing on a flip and on food tasted, searched;
2. confidence (doubt below rest, food building trust) against the floor;
3. leaving by poison seen, and by a Charnov comparator, against boredom;
4. the best leak and threshold life by life and on bodies built differently: do they vary enough to learn?
5. bursts: poison's rate just after a food or a poison, the bit right, against its mean.

## Lessons from this line, in full (moved from the old LESSONS.md)

- **An ideal body is also a gift an optimiser takes.** The two thrusters were identical to the last digit, and a
  tuned 9-part blind driver used it: firing both 300 times a second it ate four times as fast as any sighted circuit,
  as efficiently; with the thrusters unequal by 1% it drove in circles (discrete/NOTEBOOK.md, D5). Ask of every
  perfect symmetry in the simulation whether a real body would have it.
- **A finer step alone is not a check: tighten the error control too.** The discrete circuits lived in ngspice at a
  largest step of 0.5 ms. At finer steps their results fell apart, and a night went into tracing it to a slow
  oscillator; but the finer runs were the wrong ones: with the default error control, a marginal event (a transistor
  barely turning on) fired or not by each step's rounding, at any step. Tightened, every step agreed with the first
  results (`discrete/NOTEBOOK.md` D7). Check convergence in both step and tolerance, on the first design that works,
  and distrust a design whose behaviour hangs on a marginal event: a simulator's rounding, or a real part's
  tolerance, decides it.
