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
- **The fast model** (D13; `model.py`, its numbers benched by `blocks.py` on `cmos.py`'s circuit B): the circuit's
  blocks as their measured numbers, a life in a second, tied with ngspice on
  the circuit's own lives; judged robustly (each life its own parts' errors), which exposed a knife-edge the nominal
  searches exploited. Its best design, **B**: doubt a bounded tally (+ a poison, - a food, no leak, the bit flipping
  at a threshold and the tally then reset), 2.38 held out with tolerances, learning costing it 0.15 against being told
  the colour. Built in transistors (151 parts, 3.7 nW), benched on 32 seeds, its score predicted before ngspice
  lived it: 2.03 predicted, **1.65 [1.47, 1.84] lived** (held out, 64 lives, the job done, none stranded): 80% of the
  prediction. The gap is one quirk between blocks (the second thruster firing alone as a drive begins); with it in the
  model they tie. **The method is close enough** (the user, 2026-10-29): design in the model, check in SPICE that it
  is realisable, retune there only when realism matters.
- **Which level to think at** (D14): B at three levels. Tuned in its own simulator, B built of Sepulchre's elements
  ties with the block model (2.06 against 2.03) but costs 8 times the power of gates (31 nW, 841 parts, against 3.7 nW,
  151) and fails with biology's noise, which no setting of its knobs survives but size does: four times the capacitance on the bit's chain does the job with it for 48 nW (twice biology's still fails). Blocks are the fastest place to design, and both levels below realise them
  faithfully; gates are cheapest; Sepulchre's elements have the knobs a self-tuning brain would turn.
- **Self-tuning** (D15): B's knobs mistuned at birth (up to 3 times off), tuned from its own outcomes (taste and its
  own firings) in 10,000 s lives. A tuner with no coordinator (each knob wiggling at its own moments, correlating
  its wiggle with a broadcast "better than usual") reaches 1.98 against the floor's 1.74 and the ceiling's 2.47
  (+0.24 [+0.15, +0.34]), and on lopsided bodies, the balance a sixth knob, 0.90 against 0.19 and 1.94. A Bayesian
  optimiser with the same information and unlimited computation does no better (1.61, never converging; 0.92 on
  lopsided bodies), and annealing hurts: within a life, perfect is local; the global search is evolution's.
- **Tricks nobody designed** (D16): 200 random sequence detectors beside B, each adding a beat to a motor, credited
  by taste through fading tags. On lopsided bodies +0.30 [+0.16, +0.44] over B (0.59, stranding 61% to 14%), by
  learning (+0.71 over the same detectors not learning), but not by steering: it prunes the harmful random beats and
  keeps those that unstrand. On the standard body it costs 0.26.
- **Recruitment, case 1** (D17): with taste wired to nothing, a generic grower (predict what follows each eye, grow a
  recruit where a bad outcome is predicted and happens anyway, let it try the pathway's operations) grows in every
  poison life on the poison eye, in no all-food life, and, trying every operation once before keeping the best,
  reaches 1.80, tied with B's designed learning (2.01; the unwired -3.35).
- **The arena** (D18): ten robots that eat each other by biting tails, being bitten a bad taste; each robot a disc
  since 2026-10-31 (the triangle's colliding discs hooked each other; the figures below are the triangle's; on the
  disc, with firing charged (uncharged before: every earlier arena figure ignored firing's cost), escape grown nets
  +0.14, matching the best scripted burst, but against a tracker whose standing policy is tuned for the arena only
  +0.03; no pursuit or memory pays; what standing policy pays depends on the population). Beside the tracker
  (a Braitenberg steerer, evolution's design here), a grower told nothing of its purpose grows escape from bites, a
  pain no sense predicts: a recruit of two knobs (each motor's rate when bitten), jittered at each bite and judged by
  the taste just after, reaches 86-97% of the best scripted reflex held out (+0.22 to +0.25 meals a 10 s net, the
  ceiling +0.25); its gain vanishes when no response can stop the pain. Steering, pursuit and a memory of recent
  bites failed to certify as growth cases.
- **A lopsided body learned from every drive** (D19): the drive's balance jittered at each drive and judged by the
  food pulses that drive saw, the jitter shrinking with experience: 0.98 [0.78, 1.17] held out in 2,000 s lives
  (floor 0.36, ceiling 1.92), surely above D15's meal-judged tuner on the same lives (+0.26 [+0.07, +0.45]). On the
  drive started in step (D20): 1.02 against the tuner's 0.80 (+0.21 [+0.02, +0.40]), ceiling 2.15: 37% of the gap.
- **The body learned by prediction** (D20): scanning with one motor turns the body steadily, so what it sees comes round
  once a revolution, and the period gives that thruster's strength. Sweeps of its own (5 s with one motor, every 20 s
  until its estimate stalls) and a bank of coincidence counters find both periods: 1.66 [1.55, 1.76] held out on
  lopsided bodies, 83% of the gap closed, surely above every outcome-judged learner (+0.68 over D19's); with 8 s
  sweeps 1.71 (87%), costing 0.18 on the standard body (2.46 to 2.27), all of it in the first minutes. Sweeping
  only when frustrated (fewer than 8 meals in the last 32 s) removes that cost (2.47, tied with B) and keeps the gain
  (1.68 on lopsided bodies, 85% of the gap, 5 sweeps instead of 12; 1.39 on fully varied ones). A bank of 96
  log-spaced coincidence counters, chance from their neighbours (lateral inhibition) and a fixed comb does as well as
  the exact histogram held out: what is left for a circuit is the delay line holding a sweep's pulses. Sweeping at birth and every 12 s until the evidence is in, gated by the meal rate on a
  clock that stops while sweeping: lopsided 1.81 held out, 93% of the gap; standard 2.48, tied with B. A balanced
  drive used to start out of step (each motor its own oscillator, motor 1's stale from the last drive), costing
  ceilings and learners alike; started in step (`sync=1`): ceiling 2.15, learner **2.03 held out, 93% of the gap**,
  standard body 2.45, tied with B; fully varied: ceiling 1.94, learner 1.59. In counters on the fixed drive, lopsided:
  the bank 1.92 (87% of the gap, a little below the exact histogram, -0.11 [-0.25, -0.01]), its delay line's stages
  holding up to 3 pulses (2 bits) 1.88, tied with the bank; one-bit stages 1.78 (79%), probably below it. Restricted
  to what a circuit could hold (192 counters, 2-bit stages; still blocks, nothing built in transistors): lopsided 1.93 (88%), fully varied 1.68, standard 2.49, each
  tied with the exact histogram.
- **Bodies** (D13): with each thruster 0.5-2, every fixed design collapses (B 0.32, the best searched on such bodies
  0.76); told its balance, B gets 1.92 (2.15 with its drive started in step, D20); eight local rules for finding the balance reach at most 0.8; judging each
  drive does better (D19), and a model learned from its own turning far better (D20).
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

**B in transistors, and the model's prediction, written before SPICE lives it** (2026-10-29). The circuit
(`scratchpad/cmos.py`'s `pol` with mirror, counter, runfast; 151 parts): doubt a capacitor split between the rails
(13.8 pF), poison stepping it up through four unit pMOS copies of the taste pulse, food stepping it down through four
unit nMOS copies fed by a pMOS from the taste node (gate held at 1.1 V), no leak, the supply's rail the bound of
trust, the flip pulling it down until its Schmitt lets go; drive hold 16 pF, boredom 45 pF, the run on the fast
oscillator. Two of my own knife-edges found on the bench: the food pMOS's gate at 1.3 V left five seeds of 32 with a
food step of 0.18 V instead of 0.65 (the taste node reached its clamp first); at 1.1 V all are sound. The bench
first kept every node of every step (1.2 GB a run: eight at once ran the laptop out of memory); it now saves only
what it reads (240 MB). Benched on 32 seeds (`blocksB.py`): hold 0.176 s, boredom 6.04 s, scan 12.3, drive 50, run
43.6 per s, steps +0.656 V (poison) and -0.708 V (food), a drift towards trust of 0.020 V/s, threshold 1.476 V, reset
to 0.195 V, 3.7 nW; each with its spread. **The prediction** (`predict.py`, the fast model with those numbers and
spreads), on the seeds SPICE will live (50000-50031 x 2): **efficiency 2.03 [1.85, 2.21], gain 3.54, food 6.06,
poison 1.26 per 10 s, 366 firings per 10 s, 2% stranded**; the mean over 512 other lives 2.28 [2.21, 2.35]. The
method stands if SPICE ties with it, paired on those seeds (the interval of the difference including 0).

**It didn't.** Lived closed loop in ngspice on those seeds (`trypc.py`, 3 h 50 min with 8 at a time): efficiency
**1.65 [1.47, 1.84]**, gain 2.85, food 5.16, poison 1.15 per 10 s, 357 firings, none stranded, the job done; paired
against the prediction, efficiency -0.38 [-0.68, -0.08], gain -0.69 [-1.20, -0.20]: the model surely flatters it.
Poison (1.15 against 1.26) and firings (357 against 366) were as predicted, and food fell short by the same 15% in
each third (15.8, 18.2, 17.7 against 18.6, 21.0, 21.1 per life), so learning is as modelled and foraging isn't: some
block behaves differently in the closed loop than on the bench. (Life by life the two don't correlate, 0.06, as
expected: the model draws its own tolerances, not the seed's.)

*Tracing it.* Not the timers' response to sparse pulses: a lone eye pulse restarts the drive hold and boredom in full,
the same as a train (`bench_lone.py`, 8 seeds). Not the tolerances' spread: the 32 held-out seeds benched
(`benchH/`) and each lived in the model with its own numbers still gives 2.09 [1.91, 2.28], food 6.19
(`predseed.py`). So some closed-loop behaviour is missing from the model. Four lives traced in ngspice (`trace_life.py`:
each tick's mode, firings, sightings) against the model's of the same seeds (`trace_cmp.py`): the time in each mode,
the firing rates and the sightings agree, but the circuit's drives are shorter (0.229 s against 0.278) and more
frequent (10.7 against 9.2 per 10 s). The cause: **in the first tick of 55% of drives the second thruster fires alone**
(its excess over the first: 0.54-0.57 in the first tick, 0.00 ± 0.03 in every other). Motor A fires on each beat's
rising edge; motor B's gate (an AOI21: beat and DRIVE) opens the moment a food pulse starts a drive, and if the slow
oscillator's output is already high (about half its cycle) B fires at once, without A: a lone turn at the very moment
the block is sighted. The model drives with balanced pairs from the first beat.

*It accounts for the miss.* With that firing in the model (`cmodel4`'s `lone`: at a drive's start, not from a run,
B fires alone if the beat's phase is in the first 55% of its cycle), each seed with its own numbers gives 1.46
[1.31, 1.61], and ngspice ties with it: +0.19 [-0.04, +0.43] in efficiency, +0.27 [-0.14, +0.68] in gain; the drives
agree (0.244 s against 0.229, 10.3 against 10.7 per 10 s). Left over: during a drive the model fires 12% faster than
the circuit (97 against 86 per s). This is an explanation after the fact, not a prediction, so the method isn't yet
shown to stand. The lesson for benching: a block's numbers aren't enough, its **edges** (what happens at the moment
one block turns another on) must be benched too; the stray firing lived between blocks, in no block's numbers.

*A fix tried, and stopped.* Motor B latched to the beat (`cmos.pol`'s `edge`: DRIVE-or-RUN through a transmission
gate while the beat's output y is high, held by a weak keeper through the beat, B on nor(y, latched); 12 transistors,
0.4 nW more) only halved the stray firing (B alone in 23-38% of drives' first ticks, against 54-57%; four traced lives
ate 50 food against 45): B's first firing waited for the next beat, but A still missed it at times. Not chased
further. **The user's call (2026-10-29): the point of SPICE is to check we're close to something physically
realisable, not to match the model exactly.** B is: it does the job held out in SKY130 at 3.7 nW, at 80% of the
model's score, and the gap is understood. So the method stands as a lab: iterate design questions in the fast model;
check a design in SPICE (and retune it there) only when its physical realism matters. Parked: the drive's first beat
(`QUESTIONS.md`).

*Moved into the repository* (2026-10-29): the fast model, slimmed to B's blocks, as `discrete/model.py` (doubt in the
bench's volts; the failed variants of this entry stay in the scratch files named above, not kept), circuit B as
`cmos.py`'s `cmos_b` (the D12 variants dropped), its bench as `blocks.py`, its 32-seed bench as
`results/cmos_b_bench.json`; `test_model.py` checks the model lives the predicted lives (all 64 identical to the
scratch model's) and B is built part for part as benched and lived. One seed in 32 (23) still has a food step of
0.18 V against 0.70: the knife-edge of the food pMOS is rarer at vbf 1.1, not gone; the model's spread includes it.

The plan, in the model (seeds 0-127 to tune, held out from 50000 to judge), then the best in transistors, its blocks
benched, verified closed loop in ngspice and judged held out:
1. clearing on a flip and on food tasted, searched;
2. confidence (doubt below rest, food building trust) against the floor;
3. leaving by poison seen, and by a Charnov comparator, against boredom;
4. the best leak and threshold life by life and on bodies built differently: do they vary enough to learn?
5. bursts: poison's rate just after a food or a poison, the bit right, against its mean.

## D14: which level to think at (2026-10-29)

The user's plan (QUESTIONS.md): find the best level to think at, then, at that level, ask how a brain can know it
isn't doing a good job and compensate (tuning itself or recruiting). So: one architecture, B, rendered at three
levels, compared on its score, what it costs (parts, power), and what each level makes easy.

| level | built of | B |
|---|---|---|
| below Sepulchre | gates, Schmitt triggers, flip-flops, capacitors | `cmos.py`'s `cmos_b` (D13) |
| Sepulchre | leaky nodes, saturating elements, events from fast positive feedback and slow negative feedback | below |
| above Sepulchre | timers, oscillators, tallies as primitives | `model.py` (D13) |

**B at Sepulchre's level** (`scratchpad/sepb.py`), in the minimal line's language (mixed_feedback's nodes and
elements) under its rules "mixed" (every node leaky but memory nodes, no clamps), lived by its simulator (noise,
mismatch), its parts and power as `chip.py` builds it in SKY130: 13 nodes, 20 elements. The eyes and taste leaky
nodes a pulse holds up for tens of ms; the bit a memory node with a node copying its negative; food and poison routed
by four elements reading the bit, each gated by one eye's pulse; hold and boredom leaky nodes (0.19 s, 3.7 s) read
at thresholds; drive-or-run a node either sets; the beat Sepulchre's relaxation oscillator (fast positive feedback,
slow negative at 0.25 s, a faster negative at 55 ms gated by drive-or-run), motor A the oscillator, motor B following
it through an element gated by drive-or-run; doubt a memory node written by taste through two sigmoids set well
away from rest; the flip a monostable (fast positive and slow negative feedback) that resets doubt to trust and
writes the bit against a slow copy of itself (master-slave).

Getting it to work took four fixes, each a lesson about the level: a tanh reading a node at its rest writes all the
time once mismatch shifts its offset (10% of a typical voltage), so a memory written by taste drifted: read events
through sigmoids set away from rest; a node counts a spike only after it falls below a typical voltage below zero, so
an oscillator that leaks back to zero never fires a motor; an oscillator whose "fast" node is slower than its "slow"
feedback settles at a fixed point instead (Sepulchre's condition: the resting point on the fast I-V curve's
negative slope); a taste node held up for 30 ms wrote doubt 1.2 V per poison.

Benched (`sepbench.py`, as `blocks.py` benches `cmos_b`): hold 0.17 s, boredom 5.8 s, scan 11.3, drive 44, run 44
beats per s, a poison's step 0.72 V (B's: 0.18 s, 6.0 s, 12.3, 50, 44, 0.66 V). Untuned, judged held out (50000-50031
x 2): with silicon's noise it does the job, efficiency 0.83 [0.64, 1.02], food 3.8, poison 1.2 per 10 s; with
biology's noise it eats as much poison as food (-0.85; twice biology's -1.56): its bit flips by itself (4 times in 30
s with no input at biology's noise, 150 at twice), the slow nodes (taste, eyes, hold) moving 0.14-0.27 V by noise,
enough to cross thresholds 0.3-0.6 V away. Built, it is **841 parts (638 transistors) and 29 nW**, against
`cmos_b`'s 151 and 3.7 nW. Rejecting noise costs power at this level: a node's noise falls with a larger capacitor
or a shorter time constant, both needing larger currents, and every element draws twice its gain from rail to rail
all the time, gated or not (`chip.static`). `cmos_b` never meets the problem: its signals swing rail to rail, and
real thermal noise is microvolts. So the levels are compared in silicon, where both would be built.

**Tuned** (`sepsearch.py`: minimal.search's CMA-ES on 17 of its numbers, by efficiency, silicon's noise, fresh seeds
each generation, 30 generations, 20 minutes): held out, **efficiency 2.06 [1.85, 2.27]**, gain 3.30, food 5.21,
poison 0.95 per 10 s, the job done, 31 nW, 841 parts; still failing with biology's noise (-0.90). Paired on the same
worlds: **tied with the block model's prediction for B** (+0.03 [-0.26, +0.35]), and better than `cmos_b` lived in
SPICE (+0.41 [+0.17, +0.67]), though that was never retuned in SPICE and keeps its drive-start quirk. The search
slowed the scan (tau 0.48 s), shortened the hold's leak and set doubt's threshold higher; its power didn't fall
(efficiency barely feels 30 nW against the creature's 1 uW).

**The three levels, for B:**

| | blocks (`model.py`) | Sepulchre (`sepb.py`) | gates (`cmos_b`) |
|---|---|---|---|
| efficiency, held out | 2.03 predicted (2.38 over more lives) | 2.06, its own simulator | 1.65 lived in SPICE (2.0 modelled) |
| parts / power | (none: numbers) | 841 (638 transistors) / 31 nW | **151 / 3.7 nW** |
| noise | each life's tolerances | silicon's yes, biology's no | none in SPICE (rail-to-rail swings) |
| an idea tried in | **a second a life** | about a second a life, an hour to build, 20 min to tune | minutes a life; a day to design (D12-D13) |
| knobs | every block's number | every element's gain, offset and time constant, each settable by another node (a gate) | widths and lengths fixed when built; bias voltages |

What it says:
- **Both lower levels realise the blocks faithfully**: the Sepulchre circuit, tuned, ties with the block model;
  the transistors reach 80% of it untuned, the gap one quirk where blocks meet (D13). So designing at the block level
  loses little, and ideas are tried there fastest.
- **For the same function in silicon, Sepulchre's level costs 8 times the power and 5.6 times the parts of gates.**
  Each of its elements is a biased amplifier drawing twice its gain all the time; a starved CMOS gate draws a
  nanoamp only as it switches. And its slow analogue nodes are easily moved by noise, where gates swing rail to rail.
- **What Sepulchre's level gives instead is knobs**: every gain, offset and time constant is a bias, settable by
  another node through a gate, so a slow loop inside the circuit can tune it. That is the next phase's question
  (tuning towards better outcomes), so the comparison on B, a design of decisions with almost no regulation, is
  biased towards gates (the user agreed, 2026-10-29: regulation means tuning towards outcomes, the next phase).
- What biology's noise costs at Sepulchre's level (2026-10-31): not reachable with B's knobs. The same CMA-ES (30
  generations of 16, fresh seeds each) judged by the worst of silicon's, biology's and twice biology's noise, from
  the hand-built start, never left a score of about -11.6 (each generation's best within noise of the first), while
  its step size grew: a flat landscape. Its final design is worse everywhere held out: silicon 0.63 [0.42, 0.83],
  biology -0.66 [-0.78, -0.53], biology x2 -0.48, 33 nW. Six of its 17 knobs ended on a bound, all towards slower
  and quieter (the scan's and drive's time constants at 0.8 s and 0.15 s, the eyes' resistance at 74 GOhm, near the
  chip's 77; doubt's threshold, the boredom level and the poison eye's gain at their limits): it wants filtering B's
  structure doesn't have. The knobs are gains, offsets and time constants of B's existing elements, not added
  capacitance or structure, so this says B as drawn can't be tuned into robustness; the minimal line's leaders,
  searched over structure too, survive biology at about 500 parts and 130 nW, so robustness can be built, not tuned
  (scratchpad `sepsearch.py`, `v/sep_search_silicon_biology_biologyx2.json`).
- Robustness built by size (2026-10-31): the silicon-tuned design with every node's capacitance and every current into
  it scaled by K (resistances by 1/K: the same dynamics, a node's noise down about sqrt(K), its power up K), the inputs
  (eyes, taste: the body's pulses are fixed charges) and boredom (already 50 pF, the limit) left alone. Held out:

  | scaled | silicon | biology | biology x2 | power |
  |---|---|---|---|---|
  | nothing (K 1) | 2.06, job | -0.90 | -1.53 | 31 nW |
  | all, K 4 | 1.92, job | **0.86 [0.49, 1.19], job** | -1.24 | 99 nW |
  | all, K 16 | 1.56, job | 0.84, job | -0.91 | 367 nW |
  | the bit's chain (bit, its copy, doubt, flip), K 4 | 2.04, job | **0.67 [0.24, 1.07], job** | -1.29 | 48 nW |
  | the bit's chain, K 16 | 1.97, job | 0.82, job | -1.09 | 113 nW |

  So biology's noise is survived by size, not by tuning, and mostly in one place: the bit flipping by itself. Four
  times the capacitance on the bit's chain alone does the job with biology's noise for 48 nW (half again B's), still
  841 parts (the minimal line's leaders: about 500 parts, 130 nW). Beyond K 4 biology gains nothing and silicon
  slowly loses; twice biology's noise fails at every size, so what remains is in the nodes not scaled, the inputs
  most likely (the taste node's noise stepping doubt, an eye's faking a sighting), which size can't fix: they need
  structure (a filter that waits for a pulse's whole charge). Untraced. (scratchpad `sepscale.py`, `ONLY=` for a
  subset; `v/sepscale.log`, `v/sepscale_bit.log`.)

## D15: can a brain tune its own spending? (2026-10-29)

Phase 2 of the plan (QUESTIONS.md), at the block level (the user's choice, D14): a brain that notices it isn't doing
well and compensates, tuning towards better outcomes (never a setpoint, AGENTS.md). Testbed: B's five spending knobs
(hold, boredom, scan, drive and run rates) drawn at birth up to 3 times off its searched values (log-uniform, each
life its own), against the floor (fixed there) and the ceiling (B's values, fixed), on the same lives, robustly judged
(`scratchpad/selftune.py`; 16 held-out seeds x 2).

**The tuner**: simultaneous perturbation (SPSA; node perturbation, as in Fiete and Seung's birdsong model, 2006).
Each epoch, every knob nudges itself by its own random sign for one half and the other way for the other half; the
brain's efficiency in each half (food - 2 poison, against resting and its own firings, all counted from taste and its
own motors) moves each knob along its own nudge by their difference. Each knob knows only its own sign, its own
setting and one broadcast outcome, and the outcome only taste and the brain's own firings (one imperfect timer
serves both halves, so its error cancels). **Not local in one way** (the user asked, 2026-10-29): a shared epoch
clock switches every knob's halves in lockstep, and a central accountant holds the first half's tally, divides and
compares: a controller over the knobs. A broadcast outcome is plausible (as dopamine); a brain-wide metronome for
every unit's experiment is not. The coordinator-free form, continuous-time node perturbation (Fiete and Seung):
each knob wiggles at its own random moments, one leaky integrator turns taste and firings into an outcome rate, its
difference from its own slower average is broadcast, and each knob correlates it with its own recent wiggle through
a trace of its own. And a block model in Python, not a circuit: in one, each knob a memory node setting a block's
bias.

| tuner | life | efficiency | against the floor (paired) |
|---|---|---|---|
| ceiling (B, fixed) | 2,000 s | 2.52 [2.45, 2.59] | |
| floor (mistuned, fixed) | 2,000 s | 1.74 [1.51, 1.97] | |
| meals, nudges 15%, epochs 40 s | 2,000 s | 1.72 [1.51, 1.93] | none |
| + food sightings 0.02 of a meal each | 2,000 s | 1.67 | none |
| + nudges 30% | 2,000 s | 1.86 [1.73, 2.00] | |
| meals, nudges 30%, epochs 80 s | 2,000 s | 1.73 | none |
| sightings 0.02, nudges 30% | **10,000 s** | **1.93 [1.87, 1.99]** (last third 1.95) | **+0.18 [+0.03, +0.32]**; gain tied |

Why so weak: **the landscape is flat near B and steep only far from it** (`landscape.py`, each knob alone scaled,
64 lives): within about x0.7 to x1.4 no knob moves efficiency by more than 0.2; beyond x2 hold, scan and drive cost
0.3 to 1.2; the run rate barely matters anywhere, and boredom is flat but for x1/3. So a nudge has signal only where
a knob is badly off, and there a 30% nudge separates the halves by about 0.36 of efficiency against noise of about
40% (some 12 meals in a 20 s half); five knobs nudging at once add each other's effects to every knob's noise. A
life of 2,000 s holds about 1,200 meals; telling a few per cent apart takes about 1,000 meals per comparison. Given
10,000 s, knobs starting beyond x2 come about halfway back (hold 0.93 to 0.53 in the log, drive 0.95 to 0.54, run
0.90 to 0.46; boredom least, 0.87 to 0.71), and lives' spread narrows (the bad lives rescued); it saves by firing
less (298 firings per 10 s against 405) rather than eating more.

So **knowing it isn't doing well is possible from outcomes alone, but slowly**: a quarter of the gap closed in
10,000 s. The limit is the signal (sparse meals, flat near the optimum), as for the body (D13), not the mechanism.

**A yardstick: the best use of the brain's information** (the user, 2026-10-29: what does "perfect" look like, given
how sparse the feedback is?). Not the ceiling (told the best setting from birth) but the best a learner could do
with only what the brain senses (meals, food sightings, its own firings) and unlimited computation: a Bayesian
optimiser inside the life (`scratchpad/bo2.py`: each 40 s window one setting of the knobs, its efficiency recorded;
a Gaussian process over the knobs, a length scale per knob and the noise fitted from the life's own windows; the next
setting by Thompson sampling, so it explores while unsure and settles as it learns). Godlike in computation, never in
information, and never a brain. Run on the standard body (spending only) and on lopsided bodies (thrusters 0.5-2,
the drive's balance a sixth knob, starting level; the ceiling told its balance, as D13's oracle), against floor and
ceiling on the same lives; 32 held-out seeds x 2, lives of 10,000 s. Efficiency over the whole life (what learning
costs counts), and the last third's gain rate (food less 2 poison per 10 s: where learning ended up), paired:

| body | arm | efficiency | against the floor | last third's gain | against the floor |
|---|---|---|---|---|---|
| standard | floor (mistuned, fixed) | 1.74 [1.58, 1.91] | | 3.16 | |
| standard | local tuner (sightings 0.02, nudges 30%) | **1.90 [1.86, 1.95]** | **+0.17 [+0.04, +0.28]** | 3.06 | -0.10 [-0.35, +0.15] |
| standard | yardstick | 1.61 [1.55, 1.68] | -0.13 [-0.27, +0.01] | 2.66 | -0.50 [-0.78, -0.22] |
| standard | ceiling (B, fixed) | 2.47 [2.39, 2.53] | | 4.21 | +1.05 [+0.79, +1.32] |
| lopsided | floor | 0.19 [0.06, 0.35] (58% stranded) | | 0.49 | |
| lopsided | local tuner (+ a balance knob) | 0.66 [0.55, 0.77] (3% stranded) | +0.48 [+0.34, +0.60] | 1.32 | +0.83 [+0.45, +1.19] |
| lopsided | yardstick | **0.92 [0.85, 0.99]** | **+0.73 [+0.61, +0.84]** | 2.05 | +1.56 [+1.20, +1.90] |
| lopsided | ceiling (told its balance) | 1.94 [1.82, 2.06] | | 3.41 | +2.92 [+2.53, +3.28] |

**The yardstick is no yardstick on the standard body: the local tuner beats it** (+0.30 [+0.21, +0.37] in
efficiency, +0.47 in gain). It never converges: its settings stay a median of about twice off B in every knob in
every third of the life, and almost no window (0.3%) has all five within x1.5. With some 12 meals in a window and
the landscape flat within x1.4 of B (above), 250 windows can't locate an optimum in five dimensions, so it keeps
paying to explore settings far off. Its window (20 s, 80 s) and the sightings' weight (0) change nothing surely.
On lopsided bodies, where the floor is a catastrophe, wandering pays: it closes about 40% of the gap from floor to
ceiling in efficiency and half in the last third's gain.

On lopsided bodies the local tuner, given the balance as a sixth knob, rescues the stranded lives too but reaches
only two thirds of the yardstick's gain (-0.25 [-0.36, -0.14] in efficiency). The difference is the balance: the
yardstick finds each body's almost exactly (its last third's setting against the true balance: correlation 0.98,
slope 0.93), the local tuner moves it only a quarter of the way (0.27; median error 0.29 in the log from 0.38). The
balance is steep, a strong signal, so there the local tuner is limited by its step, not by information; it moves
every knob at one rate, set for the flat spending knobs.

**Without a coordinator** (`discrete/tuner.py`, checked by `test_model.py`; continuous-time node perturbation, Fiete
and Seung): each knob wiggles at its own random moments (on average every 20 s, by up to +-0.3 in the log); one
outcome node, a leaky efficiency rate (gain over spending, each a leaky tally, 20 s), and its own slower average (200
s); the difference broadcast; each knob keeps a trace of its own wiggle (20 s) and moves by rate x broadcast x trace.
No epochs, no shared clock, no accountant; every quantity a node. Same lives (paired):

| body | tuner | efficiency | against the floor | against the epoch tuner |
|---|---|---|---|---|
| standard | rate 0.03 | 1.56 [1.47, 1.65] | -0.18 [-0.32, -0.02] | -0.34 |
| standard | **rate 0.01** | **1.98 [1.89, 2.08]** | **+0.24 [+0.15, +0.34]** | +0.08 [-0.01, +0.16], tied |
| standard | rate 0.03, annealed (wiggles 4 times as wild at birth, calming over 2,000 s) | 1.50 | -0.24 | -0.40 |
| lopsided | rate 0.03 | 0.45 | +0.26 | -0.22 |
| lopsided | **rate 0.01** | **0.90 [0.69, 1.10]** | **+0.71 [+0.56, +0.86]** | **+0.24 [+0.12, +0.35]**; the yardstick's 0.92 tied (-0.01 [-0.17, +0.14]) |
| lopsided | rate 0.03, annealed | 0.33 | +0.14 | -0.33 |

So the coordinator was never needed: the local form ties the epoch tuner on the standard body (a third of the gap
from floor to ceiling closed) and beats it on lopsided bodies, where it ties the Bayesian optimiser. **Annealing
hurts**, as the optimiser's exploring did: wild tries cost more than they find when meals are sparse. Too fast a rate
(0.03) is worse than none, its knobs chasing noise; slower ones (0.005, 0.003) tie 0.01 on the standard body
(-0.02, -0.07) and fall behind on lopsided bodies (-0.08 [-0.14, -0.02], -0.19), so 0.01, broadly. **A fault, mended** (the user's
question, 2026-10-30): the rate was chosen on the held-out seeds it was then judged on. Chosen again on training
seeds 0-31: on the standard body 0.003 to 0.01 tie (1.98, 2.02, 1.95; 0.02 1.78; fixed 1.85), on lopsided bodies
0.01 is best (0.79; 0.003 0.67, 0.005 0.73, 0.02 0.67; fixed 0.16): 0.01 again, so the held-out scores stand. A rate
fixed for every individual, suited to the kind of world, is evolution's knowledge like B's other numbers, and
legitimate; set per individual from its body it would not be (AGENTS.md). Whether one fixed rate survives a world
with sparser signals is open (QUESTIONS.md). Knobs end nearer B than the epoch tuner's (median log error
falling about a third; the scan least), and the balance's median error from 0.38 to 0.14, though its fit to the
true balances is loose (correlation 0.31).

**Each knob its own rate** (the user's layers, 2026-10-30: how fast to turn the knobs is itself to be learned;
`discrete/tuner.py`, meta=1): delta-bar-delta (Jacobs 1988; Sutton's IDBD 1992), each knob's log-rate rising while
its step agrees with its own memory of its steps, falling while it disagrees, within x10 of 0.01. Compared with its
fresh memory, every rate climbed to the ceiling and the knobs chased noise (standard 0.91 to 1.15, -0.83 to -1.08
against one rate; lopsided 0.15, -0.75): the steps come from slow signals (a 20 s trace, a slower outcome), so a step
agrees with its own recent past even in noise. Compared with its memory as it was 100 s ago, beyond that
correlation, the rates stay near 0.01 (the balance's drifting slower, not faster) and gain nothing: standard 1.95,
tied (-0.04 [-0.10, +0.03]); lopsided 0.82, -0.08 [-0.15, -0.02] (meta-rate 0.0005; 0.002 worse, -0.18 and -0.16).
There was no headroom to find: 0.003 to 0.01 tie on the standard body, and the balance made faster by hand loses
(x3: 0.57, -0.34 [-0.46, -0.21]; x10: 0.21, -0.70).

**Shadows that compete** (the user's idea, 2026-10-29; `scratchpad/shadow.py`): sixteen copies of the hold (0.03
to 1.5 s), each judged counterfactually from every drive without driving, its meals kept less the drive's extra
firings at the brain's own price of energy; the hold used the best shadow's (winner takes all), on a random fifth of
drives twice that, so longer shadows are judged too. **A dead end**: 1.28 against the floor's 1.74 (-0.46 [-0.56,
-0.36]), the hold driven to a median of 8.6 times B's. Each way of replaying a drive was biased, and the last bias
can't be removed:
- judged per gap between sightings, short holds won (0.05 s): the sightings after a gap came only because the drive
  went on, so a short hold seemed to keep meals it would have lost;
- judged per drive, a shadow's drive ending at the first gap it wouldn't bridge, long shadows judged also on drives
  poison ended won 1.5 s: a sample that leaves out the drives where a long hold wastes its firings; judged only on
  drives whose hold was drawn before the drive, still long, because a shorter hold is charged with every meal after
  losing the block, when in truth the creature scans and often finds it again; what it would have seen scanning was
  never seen.
So off-policy judging works only for a choice whose alternative leaves what is seen unchanged; hold and boredom both
change it. On the same lives, the hold alone restored to B's is worth +0.17 [+0.08, +0.27]; the coordinator-free
tuner on the hold alone recovers about half of that (+0.09 [+0.01, +0.17]).

So **within a life, perfect is local**: from a life's own sparse outcomes even unlimited computation can't search
the space globally; small careful steps from a decent start do better. The global search belongs to evolution
(searching designs across lives, as this project's searches do), a life's own tuning only to polish, and to rescue
it where something is badly wrong (a lopsided body). This yardstick is a lower bound on "perfect", not an upper one:
an optimiser that explored less would score higher, and the ceiling stays the only true upper bound. Shadows that compete were a dead end (above).

In a world with sparser meals (2026-10-31; QUESTIONS step 2's open: does one fixed rate survive?). Six blocks of
each colour instead of 18 (`world.BLOCKS`, patched for the experiment, scratchpad `sparse.py`), standard body,
mistuned at birth, 10,000 s, seeds 0-31: food falls to about 1.4 per 10 s and efficiency to 0.29 for the floor; B's
own knobs, untuned, get 0.45, so there is at least 0.16 to gain (B's knobs were chosen for the dense world, so the
true ceiling is higher). The tuner barely moves: rates 0.003 and 0.01 both 0.32 (+0.02 [-0.01, +0.06] over the
floor, tied with each other), 0.03 0.27 (below 0.01, -0.05 [-0.09, -0.00]). So the rate's order holds (0.01 or
slower; 0.03 chases noise), but no rate recovers much: with meals four times sparser, a 20 s wiggle judged on a 20 s
outcome tally holds almost no signal. What fails is the signal, not the rate: a tuner for a sparse world would need
outcome windows scaled to the meals' spacing (which would itself have to be learned), or a proxy available every
moment, as D19 and D20 use for the balance. Windows scaled by hand don't rescue it: wiggles, outcome tally and its
average all 3 times slower (60, 60, 600 s), rate 0.01: 0.34, the first sure gain over the floor (+0.05 [+0.00,
+0.09]) but tied with the 20 s windows (+0.02 [-0.01, +0.06]); 6 times slower 0.30; 3 times slower at rate 0.003,
0.31. A longer window holds more meals but leaves fewer trials in a life (some 170 of 60 s for five knobs in 10,000
s), so the information a life holds, not how it is windowed, is what runs out. In a sparse world, judged by meals
alone, a life can't tune its spending; it needs a proxy seen every moment. Food sightings, the obvious one (far more
frequent than meals), don't serve: weighted 0, 0.1 or 0.3 in the outcome (0.02 normally), 0.31, 0.31 and 0.27, the
heaviest below the usual weight (-0.05 [-0.08, -0.01]): a sighting rewards looking at food, which the knobs can buy
without eating it (a long hold on a block it doesn't reach). Unlike the balance (D19, D20), spending has no proxy that
tracks meals closely; found here, none.

## D16: can a brain learn tricks nobody designed? (2026-10-30)

Phase 3 of the plan (QUESTIONS.md; the user's idea, 2026-10-29): beside B (fixed, its own tolerances), a reservoir
of 200 random sequence detectors over the brain's own events (`scratchpad/trick.py`): each fires when its event b
(an eye, or a motor's beat) comes its own delay (up to 1 s) after its event a, within 50 ms, and may then add a beat
to its own motor, with probability 0.01 + w, w its memory node. Each keeps a fading tag (2 s) of whether it acted
against its odds (+(1 - p) if it did, -p if not, so the tag averages zero whatever the meals: REINFORCE); taste
credits every tag (food +1, poison -2, rate 0.01), and each extra beat is charged its cost at once. Three-factor
learning on a random reservoir (Izhikevich 2007; Fremaux and Gerstner 2016). The trick hoped for: steering a lopsided
body. 32 held-out seeds x 2, lives of 10,000 s, paired:

| body | brain | efficiency | stranded | against plain B |
|---|---|---|---|---|
| lopsided | plain B | 0.29 [0.11, 0.50] | 61% | |
| lopsided | detectors, learning off | -0.12 [-0.35, 0.11] | 0% | -0.41 [-0.56, -0.27] |
| lopsided | **detectors, learning** | **0.59 [0.36, 0.83]** | 14% | **+0.30 [+0.16, +0.44]**; +0.71 [+0.55, +0.88] over learning off |
| standard | plain B | 2.47 [2.39, 2.53] | 0% | |
| standard | detectors, learning | 2.21 [2.07, 2.33] | 0% | -0.26 [-0.37, -0.16] |

Learning is real, but **no steering was learned**: detectors that grew beat the weaker thruster's motor half the
time (51% of 582), and those that survived are mostly keyed to the eyes (rare, so cheap); two thirds died. The
random beats alone unstrand a lopsided creature but spoil its choices (food:poison in the last third 1.9);
learning prunes the harmful ones and keeps most of the rescue. On the standard body nothing needs rescuing, and
exploring is pure cost. Below the coordinator-free tuner with a balance knob (0.90): a designed knob beats an
undesigned trick here, as expected, since a random detector has to be lucky to be the right correction, and its
credit comes only through sparse meals, a thousand of them per life.

## D17: recruitment, case 1: taste wired to nothing (2026-10-30)

The plan's step 4 (QUESTIONS.md; the user: how can a brain realise it isn't solving the problem and recruit more
neurons?), at the block level. The unwired brain is B without its learning: either eye starts a drive, taste goes
nowhere (`scratchpad/grow.py`). Beside it, per eye, a generic grower: **predict** (a fading tag of the eye's pulses,
1 s; at each taste the eye's prediction moves towards it by its tag); **notice the gap** (frustration: a leaky count,
50 s, of poisons tasted while the eye was tagged and predicted bad); **grow** (frustration past 2 grows a recruit on
that eye's pathway, the declared primitive); **experiment** (the recruit knows nothing of the circuit: it tries the
generic operations on its pathway, block and reverse, the eye then ending a drive, 20 s each, judging each by the
taste that follows its own eye, against the pathway as it was, judged by the same running rate before it grew;
win-stay lose-shift). Lives of 100 s, 32 held-out seeds x 2, robust:

| brain | efficiency | last third food:poison | |
|---|---|---|---|
| unwired | -3.35 | 1.00 | eats both colours alike |
| **grower** | **1.43 [1.21, 1.65]** | 4.31 | grew in 64 of 64 lives, always on the poison eye, the food eye kept; in all-food lives, 0 of 64 |
| B (designed learning) | 2.01 [1.83, 2.20] | 5.27 | |

It grows early (a median 7 s into the life) and in the right place every time, and never without cause. It is
-0.58 [-0.86, -0.30] behind B. Its first version re-tested the pathway as it was for 20 s before trying anything
(0.20); judging that from what had already followed the eye mended it. What remains: the recruit settles on block
in 61 lives, reverse in 3; both make the taste after the poison eye vanish, so its own judge can't tell them apart,
but reverse (B's way: the poison eye ends a drive, turning away) also avoids poison bumped into, which only the
whole outcome shows. The menu of operations (drive, block, reverse) is generic for a pathway, but it holds B's
answer; whether a grower finds what no menu holds is case 2's question.

**Mended: try everything once.** Judging by the whole outcome (all taste, the broadcast) changed nothing (1.44,
+0.01): the recruit never tried reverse, since block already beat the pathway as it was and it stayed. Trying every
operation once before keeping the best: **1.80 [1.63, 1.96], tied with B** (-0.21 [-0.50, +0.07]; +0.37 [+0.19,
+0.55] over win-stay), reverse kept in 40 lives and block in 24, and still grown in every poison life and no all-food
life. With the whole-outcome judge as well, 1.73 (tied with the eye's own judge, +0.07 [-0.03, +0.17] for the eye's).
So the judge's reach mattered less than exploring before settling: a recruit has to see every option before win-stay.

**A lopsided body: not a recruitment case** (the user, 2026-10-30: a case must be one no tuning of the brain's
parts can solve; one more knob, a gain per motor, solves this one, D15). Tried anyway (`scratchpad/grow2.py`). B with D16's detectors grown only where the gap is:
frustration, a leaky count of drives that end with the block lost, grows batches of detectors over the events of
driving (the food eye, the motors' beats); a lost drive is also credited as a bad outcome through the tags, as taste
is. 8 seeds x 2, 2,000 s, lopsided bodies: all 200 grown at once (drives fail constantly on such a body), 130 extra
beats per 10 s, 0.30 against D16's random detectors' 0.65; with 40 and less exploration 0.96, B alone 0.79, all
within noise; the lost-drive teacher changes nothing (0.97 without). No steering was learned. The building block is
wrong for the job: a detector adds single beats, while steering a lopsided body means changing one motor's rate by
1.5 to 2 times on every drive, hundreds of coordinated beats, each credited only through rare outcomes. The eyes say only how much of a
colour is in view, not where, so prediction can't read a veer's direction either.

**A world that frustrates: guarded food** (the user's idea, 2026-10-30; `scratchpad/guarded.py`). Still a random
world, one statistic changed: each food block has a poison guard beside it (2.5 mm from its centre, at a random
angle), the pair kept together. The rays stop at the first block, so the food hides behind its guard from one side.
100 s lives, 32 held-out seeds x 2:

| brain | plain world | guarded (2.5 mm) |
|---|---|---|
| B | 2.01 | 1.06 (2.1 mm: 0.46; 4 mm: 2.07, no effect) |
| B told the colour, learning off | 2.54 | 1.38 |
| B's knobs searched in the guarded world (200 random settings, learning steps too; best of 5 held out) | | 1.08 |

Tuning can't recover it (B's own values are as good as any found). The loss is mostly driving (told the colour, B
loses as much), and more from learning: guards eaten while chasing food add doubt, flipping the bit 3.1 times a life
against 1.7. But no extra structure has recovered it either: a scripted detour (poison seen just after food: swing
away on one motor, pass, swing back), told the colour, scores below plain told B on training seeds (0.43 to 0.96
against 1.58): the eyes say how much of a colour is in view, not where, so a detour can't be aimed, and half the
time it swings into the guard. Not yet certified as a recruitment case: the limit may be the eyes, not the brain.

## D18: the arena, robots that eat each other (2026-10-30)

The user's idea (QUESTIONS.md, step 6): no food or poison, only N robots, each the creature's body, trying to eat each
other; the arms race as the engine of frustration, with no hand-made worlds. The user's rules: each robot two-tone,
its mouth half red and its tail half blue (so the eyes, two colours wired at random, say mouth from tail); born with
a full belly; eating takes time (while a mouth touches another's tail, energy flows to the biter, who tastes +1 each
tick; the bitten can pull away); mouth to mouth nothing happens; collisions; an empty belly is death, and a newborn
(a fresh brain, its own wiring) appears at random at once, so N stay alive and newborns are the world's food. My
choices: belly 20 meals, a bite 1 meal a second, soft springs between discs slow against the tick, and no pain for
the bitten (taste is what touches the mouth; a pain sense would be a new body-to-brain signal, the user's decision).
`scratchpad/arena.py`, watched live by `scratchpad/arena_watch.py` (mouth M and tail T lettered, bites drawn).

First look, four robots with B's brain, 16 arenas of 1,000 s (559 robots): robots bite, get bitten, starve and are
replaced (lives of about 115 s), and clump in biting chains. B can't learn the colour here: it learns from poison
alone (doubt rises with each and flips the bit), and nothing tastes bad, so the bit never flips (0 flips in every
life). Belief barely matters: robots believing blue (tails) is food eat 0.57 a 10 s, those believing red 0.65 (and
lose 0.72 against 0.56); all eat far less than they spend (about 1.3), so nearly all starve, their meals mostly
accidental. Chasing a tail at the same speed rarely catches it unless it turns.

Mended after the user watched (2026-10-30): robots drove through each other, since only the two coloured discs
collided; now five discs cover each triangle (mouth, tail, rear corners, centre) and the spring is stiffer (K 3000;
still slow against the tick). Over 300 s, robots touch in 32% of ticks, overlapping by a median 0.16 mm, 0.66 mm at
the 99th percentile, 1.3 mm at worst (a disc is 2 mm across). The bitten now taste -1 a tick (pain as bad taste:
the user's decision); B's doubt now rises with pain whatever its eyes see, flipping its bit 10 to 14 times a life.
The view shows its speed against real time and slows to 1/100 of it.

Robots sprinted blindly (the user, watching): B's own program, made for scattered static blocks. With 8 coloured
discs in the world against 36 blocks, sightings are rare, so B is often bored and runs (17% of the time) or drives at
whatever it believes is food (13%), both at full speed (35 mm/s, nine body lengths a second); robots alike in speed
can't catch a runner. The user's changes: ten robots, and each thruster pushing a third as hard (top speed a third,
turning as before). Now (200 s): driving 37% of the time, running 6%, scanning 57%; speed a median 4 mm/s, 11 at the
90th percentile; still 0.24 meals eaten a robot a 10 s, so all starve (16 deaths in 200 s); collisions overlap a
median 0.17 mm when touching, 1.7 mm at worst.

Two eyes (the user's decision, 2026-10-30: one eye per colour can't track; robots mostly circled each other): each
a fan of 12 rays from the mouth, from 5 degrees across the middle out to 40 degrees on its own side, so four
sensors; the body draws which colour feeds which pair and which of a pair is the left eye. Brains: B adapted (each
colour's pair summed: it can't steer), B told the colour (learning off), and a hand-built Braitenberg tracker (told
its wiring and the colour: while driving, the thruster that turns it towards the eye seeing more tail fires more).
The tracker first spun (a firing turns the body about 18 degrees once settled, and with a third of the push turning
dominates); its gain scanned 0.03, 0.1, 0.25: 0.1 best. 10 robots, arenas of 300 s, meals eaten a robot a 10 s:

| arena | eaten (95%) | |
|---|---|---|
| all B | 0.15 [0.14, 0.16] | believing tails food 41% |
| all told B | 0.33 [0.32, 0.35] | |
| all trackers | 0.40 [0.38, 0.41] | |
| told B with trackers, half each (16 arenas) | told 0.33 [0.32, 0.35], tracker 0.42 [0.40, 0.44] | |
| B with trackers | B 0.21 [0.19, 0.22], tracker 0.39 [0.37, 0.41] | |

So the arena is certified for two kinds of growth: steering (the tracker beats told B in the same arena, by about a
quarter), and learning the colour, which B now learns wrongly: pain comes from behind while it chases a tail ahead,
so it blames the tail and believes it is food only 41% of the time. Eating is zero-sum (all eaten is lost by
another) and every robot spends, so on average every robot starves: success is outliving the others, the newborns
the world's food.

The arena made three times faster (each step's mouths and tails computed once, every robot's eyes in one compiled
call, bites found at once: 1.2 to 0.4 ms a step; the same eyes, shapes and collisions to the bit, only the order of
random draws changed: told 0.33, tracker 0.40 on 16 arenas). The viewer draws every robot's rays.

Steering grown (`grow_arena.py`): told B and a grower; a failed chase (a drive with no bite) is frustration, which
grows one recruit linking the food pair's two sensors' difference to the motors' balance, trying no link, one sign,
the other, each for a timed trial, keeping the best. Catches are too few to judge by (a "chase" lasts 0.08 s, 53 a
10 s, 6% caught; robots live about 96 s), but how much food it sees separates the signs (forced, `steer_probe.py`:
right 28.6 tail pulses a second, eating 0.41; none 25.4, 0.31; wrong 17.4, 0.14). Judged so, it kept the right sign
in 180 of 240 lives (15 s trials; wrong 25), yet ate no more than told B (0.32 vs 0.33; trials of 6 and 3 s the
same, choosing worse): in a life of 96 s the wrong sign's trial costs what the right one gains. The trigger fired in
every life (chases nearly always fail), so it discriminates nothing. The user's verdict: in this world the colour
and the thruster wiring are the same every life, so evolution's: the baseline brain becomes the Braitenberg tracker.

Escape from bites (`escape.py`), certified before a grower looks for it: trackers half, the other half the tracker
with a scripted response to pain (a bad taste: being bitten), for 0.5 s firing 50 a second. Both thrusters (speed
away) is worse: lost 0.46 a 10 s vs 0.29, dying younger (the biter, behind, simply follows). One thruster (a turn)
cuts the loss from 0.37 to 0.14 and nets (eaten minus lost) +0.23 [+0.20, +0.26] a 10 s over the tracker, paired
by arena (16 arenas; either side the same within noise). Eating alone misjudges it: the net is what the belly sees.

The escape grower (`grow_escape.py`), told nothing of what it is for, beside the tracker: each sensor a fading tag and
a running rate of pain onsets while tagged; a bite no tagged sensor predicted (none above twice the rate at any
time) is frustration, which grows one recruit on the taste's pathway to the motors: on a bad taste's onset it fires,
for 0.5 s at 50 a second, one generic operation (nothing, motor 0, motor 1, both), each tried for a timed trial,
judged by the taste summed over it (+ biting, - bitten: what bites move in and out of the belly), the best kept. A
first predictor (towards -1 at each bite, slowly back otherwise) let every sensor "predict" pain, as robots see each
other nearly always, so it grew in 14 lives of 247; compared with the rate at any time, the user's point held: no sense
predicts a bite (40,610 of 40,631 unpredicted) and it grew in every life, about 8 s in. Half the arena growers, half
trackers, net over the tracker: trial 15 s +0.078 [+0.055, +0.103] (16 arenas); 8 s +0.102 [+0.083, +0.122] (48
arenas: kept a turn in 463 of 720, nothing 103, both 154); 30 s +0.127 (16 arenas, but no robot lived through four
trials: the gain of trying turns, not of choosing). The control, one operation drawn and kept without judging: +0.067
[+0.044, +0.092] (48 arenas). Judged minus drawn, paired: +0.035 [+0.012, +0.061]. So escape grows and pays, surely;
of the scripted turn's +0.23 it gets 0.10, most of that because half its operations are turns; judging adds a third
of it, held back by lives of 96 s and a judge as noisy as 8 s of taste (it keeps the harmful "both" in a fifth of
lives). Watch: `arena_watch.py 1 --kinds grow,tracker` (each grower labelled with its operation, "?" while trying,
OUCH while bitten).

Judged bite by bite instead (`bite=1`, now the default): at each bite's onset the four operations compete, each its
running mean plus its own noise (sd / sqrt(1 + tries)), the winner responds, and the taste of the next `win` s is its
outcome. Chosen on arenas 0-15 (net over the tracker): win 1 s, sd 0.3: +0.138; win 0.5: +0.172; 2: +0.128; sd 0.1:
+0.184; 1: +0.090; win 0.5 and sd 0.1: +0.202; **win 0.25, sd 0.1: +0.215** (a turn kept in 230 of 240); win 0.5,
sd 0.03: +0.202. Judged on fresh arenas 100-147: **+0.186 [+0.173, +0.199]**, a turn kept in 696 of 721 lives, its
loss to bites halved (0.37 to 0.18 a 10 s); the scripted turn on the same arenas +0.241 [+0.223, +0.259]: the grower
gets 77% of it. (Motor 0 kept 410 times, motor 1 286: B's drive is not symmetric in its motors, its lone first beat
on motor 1.) Traced (`findbite.py`): bitten, the grower fires its motor and the bite is broken within a tick, then
it spins on, 480 degrees in the 0.5 s response; a shorter scripted response does as well (0.1 s +0.241, 0.04 s
+0.244 on arenas 0-15), so the response's length doesn't matter and the scripted ceiling stands.

The control (`phantom=1`): pain no response can stop, the grower's bad tastes replaced by phantom ones at random
(0.6 onsets a second, 0.3 s each; its real bites still drain its belly, unfelt). Arenas 0-15: net over the tracker
+0.011 [-0.008, +0.029], tied (escapable: +0.215); kept nothing 54, motor 0 104, motor 1 45, both 41 (escapable: 4,
146, 84, 6): a turn 61%, near chance's 50%. Motor 0 is favoured here too, as in the real arena (410 to 286): perhaps
firing it disturbs B's drive less (its lone first beat is motor 1's), so fewer of its own bites are lost; untraced.
With no bites at all it can't grow (frustration counts only bad tastes).

The arms race (QUESTIONS.md, the plan, 4, candidate a; `pursuit.py`), certified first: every robot the tracker with
the escape grower; half also respond to a bite ending (good taste stopping) by firing at 50 a second. Net minus the
plain escape growers', arenas 0-15: left 0.2 s -0.027 [-0.040, -0.016], right -0.021 [-0.032, -0.009], both -0.024
[-0.037, -0.013]; 0.04 s: left -0.003 [-0.014, +0.007], both -0.030 [-0.044, -0.016]. No pursuit pays: the victim
turns to its own side, differing between robots, so a fixed response is right half the time, and the tracker already
steers to a tail still in view. So escape leaves the biter nothing simple to grow, and the arms race stops at one
round here. With every robot escaping, each eats less than half as much (0.16 a 10 s against 0.39 among trackers):
the world grows hungrier, which every robot pays for alike.

Candidate (c), a memory of a recent bite (`alert.py`), certified first: half the escape growers, for T s after a bite
ends, unless escaping or chasing, keep moving (both thrusters at B's running rate) or keep still. Net minus the plain
escape growers', arenas 0-15: run 3 s -0.043 [-0.057, -0.034] (lost 0.124 vs 0.133, but ate 0.098 vs 0.150, dying
younger), run 10 s -0.069 [-0.082, -0.056], still 3 s -0.065 [-0.076, -0.055] (losing more). No response to a recent
bite pays, so there is no memory to grow either. In this arena, escape is the one reflex worth growing in the life;
steering pays more but is evolution's (the same every life).

A recruit with no menu (QUESTIONS.md, the plan, 4: "a menu that doesn't already hold the answer"; `grow_escape.py
knob=1`): the recruit two knobs, firing motor k at 50 sigmoid(w_k + e_k) a second for 0.5 s after a bite's onset,
e_k its own noise (sd 1) drawn each bite; the taste of the next 0.25 s against its running mean (10 bites) moves each
knob by (outcome - mean) e_k (node perturbation). Its first form replaced the brain's output while it responded, so a
weak response stopped the robot dead (from w0 = -2: -0.054 [-0.088, -0.020]); a recruit adds beats to its pathway, so
now they are added to the brain's own. With beats added the scripted responses change: a turn +0.241 [+0.214,
+0.274], and both thrusters, harmful when replacing, +0.242 [+0.224, +0.261] (on top of the tracker's own firing,
uneven while it steers, it is a turn and a burst), so the ceiling stays about +0.24. Arenas 0-15, net over the
tracker: from w0 = 0 (both at half rate) +0.236 [+0.216, +0.256], learning off +0.165 (the jitter alone turns it,
one motor firing harder each bite); from w0 = -2 (barely responding) +0.161 [+0.142, +0.182], learning off +0.049.
Held out (arenas 100-147): **from w0 = 0 +0.229 [+0.212, +0.246]** (95% of the scripted turn; the menu grower got
+0.186), ending firing both in 502 of 755 lives, motor 0 harder in 228, motor 1 in 24; **from w0 = -2 +0.152
[+0.136, +0.167]** (63%), ending motor 0 in 443 of 729, motor 1 in 56, both 82, nothing 148. So no menu is needed:
two knobs and per-bite perturbation find the escape; where they start matters (from nothing, in some 75 bites a
life, a fifth of lives haven't left it). Motor 0 is favoured strongly here (443 to 56), as before, untraced.

Why motor 0 (`spincheck.py`): B scanning fires motor 0 alone, so a robot not chasing is always spinning motor 0's
way. At 71% of 9,945 bites' onsets the tracker wasn't chasing, spinning +1.82 rad/s motor 0's way (chasing, -0.01);
two bites in three found it turning so. A motor 0 response adds to that spin, a motor 1 response first cancels it.
Scripted by motor (arenas 0-15): m0 +0.264 [+0.244, +0.282], m1 +0.238 [+0.215, +0.258]; added to the tracker's own
beats, m0 +0.274 [+0.250, +0.306], m1 +0.266 [+0.242, +0.291]. At full strength the difference is small; at the
weak responses a knob recruit starts from it is large, so every jitter towards motor 0 tastes better and the knobs go
that way. So the ceiling was low: the best scripted response, m0 added, held out (arenas 100-147) +0.253 [+0.244,
+0.262]. Against it: the knob recruit from w0 = 0 91%, from w0 = -2 60%, the menu grower 74% (replacing, against m0
replacing, not measured held out).

Why a fifth of lives never leave the low start: near w = -2 the response barely changes with the jitter, so each of
some 75 bites teaches little. Larger steps and jitter (arenas 0-15, from w0 = -2): eta 3 +0.193, jitter sd 2 +0.197,
both +0.217 [+0.195, +0.241], those left responding hardly at all 14 of 253 (42 before); from w0 = 0, both +0.262
[+0.241, +0.282]. Held out (arenas 100-147), now the defaults (eta 3, sd 2): **from w0 = -2 +0.218 [+0.203, +0.232],
86% of the best scripted escape** (38 of 739 left responding hardly at all); **from w0 = 0 +0.245 [+0.230, +0.261],
97%**. So where it starts barely matters once its steps are large enough for a short life.

A disc body (the user's decision, 2026-10-31: the triangle's five colliding discs hooked each other as robots turned
past; then the disc everywhere, `NOTEBOOK.md`, The disc). Each robot is now the creature's disc (radius 2.3 mm, the
triangle's circumradius), its front half red and its rear half blue, its mouth the front point of its rim, its
thrusters on its rear rim (their physics unchanged: a firing adds forward speed and a turn); collisions a spring along
the line of centres, frictionless, so no push spins a robot; the eyes see the colour of the half each ray meets; a
mouth within 0.3 mm of another's rim, on its rear half, bites. The triangle arena is kept as
`scratchpad/arena_triangle.py`. Over 200 s, robots touch in 92% of ticks (they clump), overlapping a median 0.07 mm,
0.25 mm at the 99th percentile (rarely far more, 3.9 mm once: probably a newborn placed on another robot, untraced).
A rear half is a far bigger target than a tail disc, so robots eat two to three times as much (16 arenas of 300 s,
meals eaten a robot a 10 s): told B 0.76 [0.73, 0.78] (0.33 on the triangle), the tracker 1.08 [1.06, 1.11] (0.40), so
steering still pays (the arena stays certified for it).

Escape and the failed certifications re-run on the disc; then **a flaw in the arena's accounting** (2026-10-31): the
net every arena script reported (eaten minus lost to bites) never charged firing, though each firing drains the belly
by `spec.THRUST` (0.002 meals; a 0.5 s burst at 50 a second, 0.05). So any response that added firing looked free,
and some looked good: on the disc, firing more seemed to pay whatever triggered it (keeping moving for 10 s after a
bite +0.12, always +0.14; bursts after a bite ends +0.13, at random moments +0.14; escape's control, pain no response
stops, +0.07). Every arena result before this, on the triangle too, was judged so (the escape grower's 86-97% above
included); they stand only as uncharged. Firing now charged (`AR.THRUST * r.firings` in lost), on the disc, net over
the plain tracker or escape grower a 10 s, paired by arena:

| | net, firing charged |
|---|---|
| escape, scripted, beats added, a turn (held out) | +0.088 [+0.061, +0.117] |
| escape, scripted, both thrusters (held out) | +0.123 [+0.101, +0.146] |
| **escape grown, two knobs from w0 = 0 (held out)** | **+0.136 [+0.115, +0.157]** |
| its control, pain no response stops (held out) | -0.094 [-0.118, -0.070] |
| pursuit, both thrusters 0.5 s after a bite ends (0-15) | -0.191 [-0.220, -0.157] |
| the same bursts at random moments (0-15) | -0.321 [-0.344, -0.298] |
| keep moving always (both at B's run rate, not driving or escaping; 0-15) | -0.489 [-0.514, -0.464] |
| **keep still always (no scanning; 0-15)** | **+0.426 [+0.390, +0.460]** |

So: escape grows and pays, surely, and its control now costs, as a control should; the grower matches or beats the
scripted bursts (it learns its rates, so it needn't fire at full rate). No pursuit pays. And the tracker's scanning
is its biggest waste in a crowded arena: robots that never scan net +0.43 a 10 s more, three times escape's gain.
That looked like a standing policy to fix (evolution's), but it isn't one: **what pays depends on who else is in the
arena.** The tracker's standing policy hill-climbed by invasion, firing charged (`arena_tune.py`: B's hold, boredom,
scan, drive and run rates and the tracker's gain, each doubled or halved in turn, kept if surely better than the best
so far, arenas 0-15): scanning twice as fast (+0.14 [+0.11, +0.17]), then holding half as long (+0.06 [+0.01,
+0.10]); held out (arenas 100-147) the tuned tracker nets **+0.139 [+0.114, +0.165]** over the plain one. Never
scanning, among trackers, costs: -0.37 [-0.41, -0.31] (scanning at a quarter rate -0.30; without running too, -0.45).
Decomposed (arenas 0-7, a 10 s): among trackers, a robot that keeps still eats half as much (0.64 against 1.26) and
loses more to bites (1.14 against 0.94); among escape growers it eats as much (0.62 against 0.61) and loses as much
(0.64 against 0.65) while firing far less (0.66 against 1.04). Robots that escape are hard to catch, so chasing and
scanning for them is wasted; robots that don't are worth hunting. So the best standing policy is
frequency-dependent: evolution's answer shifts with the population, as in any arms race, and a growth case must be
certified against the population it will live in. Firing is costly here: about a meal a 10 s, as much as a robot eats.

Escape against the tuned tracker (every robot's standing policy scaled, `grow_escape.py t_scan=2 t_hold=0.5`, held
out, arenas 100-147, firing charged): grown from w0 = 0 **+0.029 [+0.004, +0.054]**, from w0 = -2 +0.018 [-0.011,
+0.044], its control -0.073 [-0.092, -0.054]. Against the plain tracker it was +0.136. So most of escape's value was
the plain tracker's poor standing policy: once evolution's part is tuned (faster scanning, shorter holds: a biter
that re-finds its prey quickly, so a broken bite costs it little), a grown escape barely pays for its firing. The
grower still beats its control by about +0.10 (it does find the response that helps most), but the case no longer
certifies well: a growth case must be certified against a tuned baseline, and in this arena, with firing charged,
there is little left that the life must learn.

## D19: a lopsided body learned from every drive (2026-10-30)

The plan's step 5 (QUESTIONS.md: learn from what happens every moment, not only from meals), its first experiment,
with D18's lesson (judge each try at once, against its own jitter). B (its tolerances drawn, its learning as
designed) on bodies with each thruster 0.5 to 2 (`bodies.THRUSTERS`), lives of 2,000 s, the other knobs B's
(`drivebal.py`, in the scratchpad). The drive's balance x (log of motor 0's rate over motor 1's) is jittered afresh
by e at each drive's start; the drive's outcome, the food pulses it saw (a drive lasts while the block stays in view,
so one that curves off loses it sooner), against its running mean (20 drives), moves x by eta (outcome - mean) e.
About 9 drives a 10 s, so some 1,800 lessons a life, against a few hundred meals.

Seeds 0-31 (choosing): floor (balance 0) 0.22 [0.02, 0.43], stranded 38%; ceiling (told its body, the
drive balanced) 2.11 [2.04, 2.20]. Jitter sd 0.3: eta 0.01 0.74 [0.57, 0.89]; 0.03 0.80 [0.63, 0.95] (the balance
within 0.13 of the oracle's by 200 s, 0.08 by 500 s, median; correlation 0.87 at the end); 0.003 0.38. Close to
the right balance, yet far below the ceiling: born at the oracle's balance, learning off, it gets the ceiling (2.11)
with no jitter and 1.07 with jitter 0.3, so the exploring costs half, the score being steep in the balance. Smaller
jitter with the step scaled by 1/sd^2 is unstable (sd 0.1: 0.22; 0.05: 0.06; the outcome's noise swamps it); sd 0.1
with eta 0.1 0.82, last third 4.31 but 19% stranded. Paired opposite jitters (0.77) and outcomes relative to the
usual (0.53, barely learning) don't help. The stranded lives stop driving, so their balance freezes where it was,
often still near 0: learning needs successful drives to learn from (with eta 0.03, 4 of 64 stranded, the most
lopsided: median |oracle| 0.75 against 0.47). Jitter shrinking with experience, sd 0.3 / sqrt(1 + drives / N):
N 200 1.14 [0.96, 1.31]; 500 1.07; 1000 1.09 [0.96, 1.22], stranded 3%, the job done, the balance's correlation with
the oracle's 0.96 (slope 0.92). (In D15, annealing hurt the meal-judged tuner; here the balance converges in a few
hundred drives, so there is time to settle.)

Held out (seeds 50000-50031), N 1000, eta 0.03: **0.98 [0.78, 1.17]**, stranded 8%, last third 4.30; floor 0.36
[0.14, 0.61], 31% stranded; ceiling 1.92 [1.80, 2.04]: 40% of the gap closed in 2,000 s. D15's tuner (`discrete.
tuner body=1 mistune=1`: every knob and the balance, starting at B's, judged by meals and sightings per energy) on
the same lives: 0.72 [0.54, 0.90], none stranded; **per-drive minus it +0.26 [+0.07, +0.45]**, paired. Judging each
drive by what it saw learns the balance far faster than judging by meals (D15's SPSA tuner moved it about 27% of the way
in 10,000 s; this one 54-92% in 2,000 s). What's left: the exploring's cost (even shrinking, a jitter on a steep
knob), and the lives that strand before they learn. Next: is it prediction? Not yet: the outcome is a fixed proxy
(food seen), not a learned model of what a beat does to the eyes; a unit predicting its eyes from its beats is the
next step.

## D20: the body learned by prediction: what comes round again (2026-10-30)

The plan's step 5 proper: a model of this body learned from what its own beats do to its eyes, no outcome and no
jitter. While B scans, one motor alone turns it at a steady rate, so whatever it sees comes round again once a
revolution, and a revolution's period goes as 1 / that thruster's strength. So scanning with each motor in turn and
finding each one's period gives the thrusters' ratio, and the drive's balance x = log(T0 / T1) straightens the drive
(k0 g0 = k1 g1). The goal (keep what is chased ahead) is the same every life, evolution's; the model of this body
is the life's (QUESTIONS.md, step 5). `periodbal.py`, in the scratchpad; lopsided bodies (each thruster 0.5 to 2),
lives of 2,000 s, B's other knobs as designed.

Feasibility (`period_probe.py`, 60 s of one-motor scanning): the eye pulses' intervals recur at 0.79 of the period
the body's spin predicts, in every one of 16 scans (the factor, from beats' discrete timing, cancels in the ratio),
once the estimator finds the fundamental rather than a multiple. In a life, though, B's own scans are short (a
median 0.4 to 0.6 s, ended by the first food sighting; 4 to 29% last a revolution), and their intervals gave
nonsense (correlation with the right balance -0.36, then -0.14 with intervals counted against chance per scan, each
scan's pulses placed at random within it). So the brain makes its own experiments: sweeps, every `cal_every` s for
`cal_len` s, ignoring what it sees and turning with one motor alone at its scan rate, the motor alternating; only
the sweeps' pulses counted. Pooled with B's own scans the estimate is worse (47% within 0.2): they aren't a steady
spin, starting from rest or a drive's momentum.

The estimator, in four steps, each traced on lives whose periods are known: the shortest comb within 90% of the best
picked halves; the best comb picked multiples (teeth beyond a 5 s sweep have no data: now only teeth chance expects
data in count); the shortest fraction of the best recurring at its own lag left 3 of 16 wrong (5x, 3x, 1.5x); then
subharmonic summation (Hermes 1988, from pitch detection: each multiple k of a candidate period weighted 0.84^(k-1)
and summed, so a multiple of the period loses the teeth between and a fraction gains empty ones), each tooth's
evidence the excess over chance in units of chance's spread ((observed - expected) / sqrt(expected): a ratio over a
tiny expectation was noisy). Then 16 of 16 lives found both periods, every balance within 0.02 of the right one.

Seeds 0-31 (choosing): sweeps of 5 s every 50 s, 1.50 [1.40, 1.60] (98% of balances within 0.2; the sweeps alone,
balance fixed at 0, 0.23); sweeping stopped once its last 3 estimates agree within 0.03 (its own adjustment stalled:
a body doesn't change within a life) but with too little evidence locks in wrong ones (1.18 to 1.38, 70 to 75%
within 0.2); requiring 2,000 intervals a motor first, 1.74 [1.60, 1.87]; 5,000, sweeps every 20 s: **1.80 [1.72,
1.89]**, every balance within 0.2, none stranded, sweeping stopped after a median of 36 sweeps (some 700 s).

Held out (seeds 50000-50031): **1.66 [1.55, 1.76]**, none stranded, 98% of balances within 0.2 (correlation 0.99);
floor 0.36, ceiling 1.92: 83% of the gap closed. Paired, on the same lives: above D19's per-drive learner by +0.68
[+0.51, +0.86], above D15's meal-judged tuner by +0.93 [+0.73, +1.14], below the ceiling by -0.27 [-0.36, -0.16].
Its price on the standard body, where there is nothing to learn: plain B 2.46 [2.34, 2.54], the period learner 2.15
[2.07, 2.22] (-0.31: the sweeps, about 9% of the life turning blind, and small errors).

So prediction beats outcome here by far: a model of what its own turning does to what it sees, learned from a few
minutes of deliberate experiment, finds the body almost exactly, where learning from outcomes (meals, or food seen
per drive) found it roughly and slowly, and paid for exploring all life long. What it needed that B lacked:
experiments of its own (a sweep is a question asked of the body), a bank of coincidence counters (the intervals'
histogram, with chance's), and a way to tell a period from its multiples.

Cheaper sweeps. On the standard body the cost is all early: in the last third the period learner equals plain B
(6.14 against 6.10, seeds 0-31). Seeds 0-31, standard body (plain B 2.52) and lopsided: 5 s sweeps every 20 s
stopping at 5,000 intervals 2.13 and 1.80; at 3,000 2.14 and 1.83; 3 s every 12 s 1.99 and 1.67 (a short sweep holds
few long intervals); 8 s every 32 s (3,000) 2.29 and 1.83, 13 sweeps; 12 s every 48 s 2.32 and 1.73 (94% within 0.2).
Pairs grow as a sweep's length squared, so longer sweeps gather evidence faster, until too few sweeps leave some
estimates wrong. Held out, **8 s every 32 s, stopping at 3,000 intervals and 0.05**: standard body 2.27 [2.16,
2.36], **-0.18 [-0.31, -0.04] against plain B** (5 s sweeps: -0.31); lopsided **1.71 [1.52, 1.88]**, tied with
5 s sweeps (+0.05 [-0.12, +0.19]), 87% of the gap closed, below the ceiling by -0.21 [-0.39, -0.07]; sweeping ends
after a median 12 to 14 sweeps (about 7 minutes).

Watched (`watch_pb.py`, seed 50001): the panel shows each sweep as it happens and the motor sweeping; run on without
drawing, after 2 sweeps (100 s) both periods match what its thrusters give (1.37 and 1.12 s against 1.37 and 1.13)
and the balance is the one it needs (+0.20); sweeping stopped after 10.

Bodies varied in every factor (`allbody=1`: overall strength, an asymmetry between the thrusters, the eyes'
sensitivity and drag, beside each thruster), held out: floor 0.34 [0.16, 0.56], 31% stranded; ceiling 1.75 [1.48,
2.00]; **the period learner 1.28 [0.99, 1.56]**, 8% stranded, two thirds of the gap, 84% of balances within 0.2.
Each failure is off by log 2 (0.69 to 0.71): one motor's period found at half or double. Traced (seed 50027, a weak
thruster): excess 22 at the true 2.48 s and 13 at twice it, but a real 7 at half it (cause untraced: not a wider
circle, since a one-motor sweep's circle has radius PUSH / TURN, about 1.25 mm, whatever the thruster's strength). The multiples' weight doesn't help (seeds 0-31:
0.84 89% within 0.2, 0.7 88%, 0.6 83%); choosing among the best, its double and its half by the strength of each
one's own first recurrence is much worse (61% and 66%: shorter lags hold more chance pairs, so their excess in chance's
spread is smaller). In one long sweep on that body (`halftrace.py`, 120 s) there are no pulse pairs at half the
period at all, so the half period comes from pooling short sweeps: within a sweep any two blocks give intervals at
their bearings' difference plus whole revolutions, a few times over, and a pass is a burst of pulses, so each
coincidence counts the burst's size squared; such clumps land at random lags, noisier than chance's Poisson spread
allows. Counting a pass, not a pulse (pulses within 0.15 s one event) doesn't help (seeds 0-31: 86% within 0.2 on
fully varied bodies, 97% on lopsided ones, but 23 sweeps against 12, efficiency 1.16 and 1.61). Nor does making each
sweep one vote (its pairs scaled to one before pooling, each lag's excess over the votes' spread: 83% and 91%, against
89% and 98% without), nor more evidence before sweeping stops (6,000 intervals, fully varied: 91%, efficiency 1.30
against 1.34): the errors persist, so they are systematic for some bodies, not noise. Traced (seed 50027, motor 0,
the first 240 s): one sweep gives nearly all the half-period pairs (99 pulses, 279 pairs at half the period, 387 at
the period; the others 0 to 27), the sweep with the nearest block (2.6 to 5.1 mm from the body's centre as it
circles, against 5 to 12 mm in the others): a block that close plausibly crosses the 2 mm corridor twice a
revolution (unproven). Discarding sweeps denser than 8 pulses a second: 91% within 0.2 on fully varied bodies (89%
without), 98% on lopsided ones, but 20 to 22 sweeps against 12, efficiency unchanged (1.35, 1.80); 10 a second, 88%.
So a near block is likely the cause, and none of five remedies is worth its cost; left at 89% on fully varied bodies.

Sweeps only when frustrated (2026-10-31; QUESTIONS.md, step 5's open "cheaper sweeps"). A body that already drives
well needn't be swept, and the brain knows it is doing badly from its own taste: at each slot (every 32 s) it sweeps
only if it has eaten fewer than `gate` meals since the last slot (`gate=8`). Once the balance is right the meals rise
and the sweeps stop of themselves: the bad outcome ends the experiments, as step 4's candidate answer says. The gate
is a meal rate, an outcome, not a property of the body, but it is tied to this world's food (B eats about 20 meals
in 32 s on the standard body, about 5 on a lopsided one before it learns): evolution's, for this world. Seeds 0-31,
standard body (B with no sweeps 2.52) / lopsided / fully varied: gate 6, 2.55 / 1.79 / 1.25 (sweeps 0 / 4 / 5);
gate 8, 2.49 / 1.88 / 1.31 (0 / 5 / 7); gate 10, 2.45 / 1.92 / 1.38 (2 / 7 / 10); ungated, 2.29 / 1.83 / 1.34 (13 /
12 / 12). Held out (seeds 50000-50031), **gate 8**: standard body **2.47 [2.43, 2.51], tied with plain B (+0.01
[-0.06, +0.11])** and surely above ungated sweeps (+0.20 [+0.11, +0.31]): the sweeps' cost is gone; lopsided **1.68
[1.50, 1.84]**, tied with ungated (-0.03 [-0.11, +0.06]), 85% of the gap, with 5 sweeps instead of 12; fully varied
**1.39 [1.11, 1.66]**, against ungated 1.28 (+0.11 [-0.06, +0.30], not sure), 88% of balances within 0.2, three
quarters of the gap. A mildly lopsided body is swept late, since it is frustrated only now and then: seed 50001
(balance +0.20) eats 8 meals in most slots, first sweeps after some 400 s and has its balance (+0.19) by 600 s;
seed 50027 (-0.50) sweeps from the start, a first estimate wrong (+1.21, too little evidence) corrected by 220 s
(-0.49). Standard bodies (seeds 50001, 50005) never sweep. `gatetrace.py`, `gatepair.py`; the viewer
(`watch_pb.py`, now gated, with `--standard` for the standard body) shows the meals counted since the last slot.

What a circuit would have to hold (2026-10-31; QUESTIONS.md, step 5's open "a circuit for the counters and the
period-finder"), before designing one: not a fine histogram (1,700 bins of 10 ms) with chance computed from each
sweep's length and pulse count, but a bank of K coincidence counters at log-spaced lags (0.1 to 17 s), each counting
the intervals within half a spacing of its lag; each candidate period one counter, scored by fixed wiring from the
counters nearest its multiples (weights 0.84^(k-1): evolution's wiring); chance taken from the counters' neighbours
(the mean of those within 25% of a counter's lag, excluding itself: lateral inhibition), not computed
(`fundamental_bank`, `bank=K local=1`). Seeds 0-31, lopsided bodies, gated sweeps (the fine histogram 1.88, 98%
within 0.2), chance computed: K = 32, 1.49 (88% within 0.2, 31% within 0.05); 48, 1.52; 64, 1.69 (91%, 69%); 96,
1.86 (98%, 91%). Chance from the neighbours: 96, **1.87 (100%, 92%)**; 128, 1.90; neighbours within 50%, 1.82; and
the excess as a plain difference, not over chance's spread (no square root), 1.87 again. Held out, 96 counters with
neighbours' chance, paired with the fine histogram on the same lives: standard body 2.48 (+0.01 [-0.00, +0.03]; B
2.46), lopsided 1.66 (-0.02 [-0.17, +0.16], 97% within 0.2), fully varied 1.34 (-0.06 [-0.25, +0.16], 84%): tied
everywhere. So the period-finder needs about 100 counters (a 4% spacing: a period's quantisation then costs the
balance under 0.05), lateral inhibition and a fixed comb, and nothing computed. Left for the circuit: the delay line
that holds a sweep's pulses for up to 17 s (a sweep has some 100), so that each new pulse can be compared with every
earlier one; the counters as memory nodes written by coincidences; the winner-take-all over the candidates.
The natural delay line, a chain of 96 one-bit stages at the counters' lags (a stage marks that some pulse passed
that long ago; pulses within a stage merge, and each new pulse adds at most one to each occupied stage's counter,
`binary=1`), loses: seeds 0-31, lopsided 1.70 [1.54, 1.84] (94% within 0.2) against 1.87 (100%) counting, fully
varied 1.31 against 1.34. Traced (seed 3, motor 0, 600 s): the stages saturate as they widen with lag, keeping 78%
of the coincidences at 0.1 to 1 s, 46% at 1 to 3 s and 32% at 3 to 8 s, so the comb's higher teeth flatten. So the
line's stages must carry how many pulses passed, not whether one did: charge packets, as in a bucket-brigade line,
each coincidence adding its stage's charge to its counter. (A sweep lasts 8 s, so lags beyond 8 s hold nothing;
the line need only be 8 s long, still beyond a chip's slowest leak, 3.9 s, so its stages are memory-like.)

Where the rest of the gap goes (2026-10-31). Held out, gated (gate 8), lopsided: food per 10 s by third 4.30, 5.19,
5.26, against the ceiling's 5.47, 5.45, 5.35: the loss is in the first third, the time to learn (the balance within
0.1 for good after a median 140 s; 380 s for mildly lopsided bodies, swept late), plus 7 of 64 lives whose balance
stays 0.05 or more out and lose a third of the last third's food. So learn sooner: a first sweep at birth and slots
every 12 s until each motor has 1,000 intervals, then every 32 s (`cal_first=0 cal_fast=12`). Seeds 0-31, lopsided:
the first sweep at birth alone 1.87 (gated 1.88); with 12 s slots 2.00, but the standard body falls to 2.36 (8
sweeps), since no body eats 8 meals in a 12 s slot. So the gate became a rate (`gate_rate=1`: frustrated if the
last 32 s hold fewer than 8 meals, or pro rata early in life): standard 2.35, still 7 sweeps, because a sweep is 8 s
of fasting that itself trips the gate. Counted on a foraging clock that stops during sweeps (a sweep's own fast
isn't frustration): standard **2.48**, lopsided **2.02** (100% within 0.2), fully varied 1.37 (seeds 0-31). Held
out (seeds 50000-50031), paired with the plain gate on the same lives: standard **2.48** (+0.01 [-0.06, +0.07]; B
2.46, 2 sweeps); lopsided **1.81 [1.68, 1.93]**, +0.13 [-0.01, +0.31], 98% within 0.2, 8 sweeps, **93% of the gap**,
below the ceiling by -0.12 [-0.22, -0.02] (gated: -0.24); fully varied **1.51**, +0.12 [-0.15, +0.35], 91% within
0.2, 83% of the gap, below the ceiling by -0.23 [-0.45, -0.08]. These are now the period learner's settings
(`watch_pb.py`).

A flaw in the drive whenever it is balanced (2026-10-31), found while trying B's own scans (below). With equal gains
the fast model's drive fires both thrusters on each beat; with any balance at all (g0 != g1) each motor has an
oscillator of its own (`model.Model.step`), and motor 1's only runs while driving or running, so each drive starts
with the two out of step, by whatever its phase was left at and motor 0's moved on during the scan. B with gains
1.0001 and 0.9999 on the standard body: 2.29 against 2.52 (seeds 0-31): unpaired first beats turn the body off the
block it has just seen. Two fixes, as options in `model.py` (off by default, so earlier results stand): `paired=1`,
the slower motor firing beside some of the faster one's beats: 2.51 there, but the lopsided ceiling falls (1.93
against 2.11); `sync=1`, the two oscillators set in step at each drive's start: **2.56** there, and the lopsided
ceiling **2.24** (seeds 0-31). So the cost was the drive's start, not unpaired beats as such. Held out (seeds
50000-50031), with `sync=1`: the ceiling (told its balance) **2.15 [2.03, 2.26]** on lopsided bodies, +0.23 [+0.10,
+0.35] over the old drive's 1.92, and **1.94** on fully varied ones (+0.20 [+0.07, +0.32] over 1.75); the floor
(B, balance 0, so equal gains) unchanged, 0.36. The period learner with it: lopsided **2.03 [1.89, 2.16]**, +0.22
[+0.12, +0.33] over the same learner without, 98% within 0.2, **93% of the new gap**, below the ceiling by -0.12
[-0.25, +0.02] (no longer surely); standard body 2.45, tied with B (-0.01 [-0.15, +0.13]); fully varied 1.59 (+0.08
[-0.08, +0.24]), 78% of the new gap. Every balanced result before this (D13's oracle, D15's tuner, D19, D20 above)
paid this flaw, ceilings and learners alike; the gaps quoted there are on the old drive. Re-judged on the fixed
drive (held out, floor 0.36, ceiling 2.15): D15's tuner (`discrete.tuner body=1 mistune=1`, 2,000 s) 0.80 (+0.08
[+0.02, +0.15] over the old drive), 25% of the gap; D19's per-drive learner 1.02 (+0.04 [-0.09, +0.17]), 37%; the
period learner 2.03, 93%. The order holds: D19 above the tuner by +0.21 [+0.02, +0.40], the period learner above
D19 by +1.01 [+0.83, +1.19]. The flaw cost the learners judged by outcomes little (their balances are rough
anyway) and the ones that find the balance almost exactly most. A circuit's drive would
start both thrusters from one oscillator anyway: this is the fast model being fairer to a balance, not a new
mechanism. (QUESTIONS.md's "B's drive starts cleanly, in transistors" is the same cost in SPICE: a drive's first
beat matters.)

B's own scans again (2026-10-31; step 5's open "B's own scans made usable"). Counting only their steady part (after
0.5 s, scans of 1 s or more) made little difference (seeds 0-31, lopsided, no sweeps: 0.68, 64% within 0.2,
correlation 0.79). The cause was in the model: B's scan rate is its drive oscillator's, so scaled by g0, which moves
as the balance is learned, smearing the periods pooled over the life (the sweeps run at the bare scan rate). With
the scan at its own rate (`scan_rate=1`): 1.38, 92% within 0.2, correlation 0.93, with no sweeps at all; with the
drive also started in step, 1.75 (94%). So B's scans do carry the body; D20's first finding, that they gave
nonsense, was mostly this smear. But they are worse than sweeps: on the standard body scans alone cost 0.24 (2.28
against 2.52, the balance re-estimated all life from evidence a little biased by scans' starts), and added to the
sweeps they lower the lopsided score (2.08 against 2.21). Left out.

How many pulses a delay stage must hold (2026-10-31). Re-tried on the current settings (early, rate-gated sweeps;
the drive started in step), lopsided bodies: on seeds 0-31 one-bit stages tie the bank (2.06 against 2.10, -0.04
[-0.18, +0.09]; stages holding 2 pulses 2.07, any number 2.08). The old deficit (1.70) was mostly the old settings:
one-bit stages with the early sweeps 1.96 (+0.26 [+0.14, +0.39]), with the drive in step 1.88 (+0.19 [-0.02,
+0.38]). Held out (seeds 50000-50031, floor 0.36, ceiling 2.15), paired on the same lives: the bank with counting
stages 1.92, below the exact histogram (2.03) by -0.11 [-0.25, -0.01] (tied before the drive was fixed: a finer
balance now pays); stages holding any number 1.93, the same as the bank (+0.01 [-0.01, +0.04]); stages holding up
to 3 pulses (`cap=3`) **1.88, tied with the bank** (-0.04 [-0.18, +0.08]); one-bit stages 1.78, -0.14 [-0.29,
+0.01] against the bank, -0.25 [-0.43, -0.07] against the exact histogram. On other bodies one-bit stages tie the
exact histogram (fully varied 1.63 against 1.59, standard 2.38 against 2.45, both within noise). So a stage needs to
count to about 3 (two bits, or a charge packet that saturates at three), not to carry exact counts; the remaining
cost of counters over the exact histogram, about 0.1 on lopsided bodies, may be the bank's quantisation (96
counters, 4% apart) now that the drive's balance is finer. Held out, lopsided, against the exact histogram: 128
counters 1.90 (-0.12 [-0.31, +0.02]), 192 counters 2.01 (-0.01 [-0.15, +0.09]), 128 counters with 3-pulse stages
1.97 (-0.05 [-0.16, +0.03]); 128 against 96 -0.01 [-0.22, +0.19], 192 against 96 +0.10 [-0.05, +0.24]. No
ordering is sure: differences of 0.1 are within these 64 lives' noise. So 96 to 192 counters with stages counting
to 3 come within about 0.1 of the exact histogram, and 192 ties it; more lives would be needed to price the spacing.
The period learner restricted to what a circuit could hold (still the block model, not built: 192 counters, chance from neighbours, a fixed comb, a delay line of
stages holding up to 3 pulses; `bank=192 binary=1 cap=3`), held out on all three bodies, paired on the same lives:
lopsided **1.93**, tied with the exact histogram (-0.10 [-0.30, +0.06]), 88% of the gap, below the ceiling (-0.22
[-0.44, -0.01]); fully varied **1.68**, tied with the exact histogram (+0.09 [-0.09, +0.33]), 84% of the gap, below
the ceiling (-0.26 [-0.44, -0.11]); standard **2.49**, tied with B (+0.03 [-0.09, +0.16]). So nothing in it needs
exact counting: some 200 counters and a short delay line of 2-bit stages would do. Building them in SKY130 is not
started.

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
