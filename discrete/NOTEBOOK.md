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
  (D8). The circuit's gap to them is not in its speeds (the policies' best speeds made it worse).
- Values not yet tuned for `learn_avoid` (its values are learn_hold's and the prototype's). A pruned circuit
  must be judged held out: pruning's last cut, "not surely worse" on 12 seeds, was surely worse held out (D9).
- **The simulator** is checked in both step and tolerance: ngspice's error control is tightened in every netlist
  (D7).
- Queue 7 re-judged every circuit with the tightened control (D7) and re-tuned learn_hold (noise, no trend: its
  output kept as `results/learn_hold_tune_q7.json`, never judged); the foraging circuits' re-tunes were cancelled
  (their results stand, D7).
- Open: bodies are still identical in tuning and judging (but for `--motors`), though the body's dynamics should
  vary from life to life (D5); making that the default awaits the user's choice of factors and spreads. Identical
  thrusters make a giving-up run exactly straight, and one such run stranded a life on the torus (D9).
- Open: high-value resistors (500 MOhm to 1 GOhm) are rarely better than 5% and leak across a board's surface;
  `life.TOL`'s 1% is optimistic for them.

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
