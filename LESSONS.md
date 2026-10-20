# Lessons

*Names (2026-10-18): the "grown brain" is now the **sheet brain**, and the "mixed-signal brain" the **designed circuit**; the minimal, adjusting, knowing and recruiting brains are the **…-circuit** brains. Earlier entries keep the names they were written with.*

What was tried, what worked, what didn't and why, so settled questions aren't reopened. Each finding was traced to a
cause before it was fixed. Each entry gives the lesson, then what the code does now; dead ends are kept because they
are lessons too.

## Principles

- **Local behaviour only, no global god.** No global clock, no broadcast, no harness switching the cells' behaviour.
  The only things from outside are the body's inputs (a sensor's stimulus, and taste), delivered to the cells that
  named themselves.
- **The body is never part of the solution.** The body says what happened (this colour is in view; that was food),
  never what it means for learning (which sensor earned the taste). A body change that lets the brain drop some
  mechanism has moved that mechanism's job into the body (below: reward at contact).
- **Nor is the simulator.** Whatever the simulation lets a design exploit, whoever optimises it (an agent, the user,
  evolution) will find: lockstep, unlimited precision, a fixed seed, integration error, the exact shape of an input.
  Before this project, the user asked an agent to cut the number of channels between cells, and it packed several
  into different bits of one floating-point number. The exp(-beta d) cheat (The engine, below) was the same kind. So
  every brain runs with random timing, noise on everything and limited precision, and a result must survive a finer
  simulation and fresh seeds (defences for the circuit brains: Simulating the designed circuit, below).
- **No hidden scale.** A cell knows only its own state and its neighbours' averages; never the sheet's size or its
  position in it.
- **Stochastic updates only.** Every cell updates at random times, never in lockstep: lockstep lets rules lean on a
  shared rhythm and makes artefacts (flipping every tick, checkerboard oscillations).
- **Noise must matter.** Neighbours see a shared number as the cell shows it, clipped to -1..1 and with noise of 1%.
  No encoding may squeeze information below the noise or spread it over orders of magnitude. What a cell keeps to
  itself is not limited (counts and timers are whole numbers, re-rounded at each update).
- **Inputs spike.** Sparse kicks, never continuous levels.
- **No magic knowledge.** Every cell learns everything from its neighbours' signals. Above all, a path finds its
  target by a signal the target cell itself sends out, never by where the rule says the target should be. And no
  cell knows what an organ is for: the rule is unchanged if the two sensors, or the two actuators, are swapped.
- **Don't build features into the body or world to make learning easy.** The body and world are as simple as they
  can be; what the brain needs, it does itself.
- **Symmetry must be broken, and noise breaks it.** Identical cells in a regular sheet can't choose between equal
  options (a corner, a handedness, a route). Something local and random breaks the tie, and the rule then has to make
  the choice stick.

## The engine

- **Rules kept only in prose drift, so make the rule the structure.** The golden rule is that each cell sees only the
  mean of each number its neighbours share. Earlier experiments (before this project) quietly broke it, reading each
  neighbour separately (the smallest, one by tag, each one's sums), and nothing in the code stopped them.
- **What `sheet.py` does.** Only the engine knows the grid. A rule module declares its numbers, which are shared, and
  their birth values, and one compiled `update(me, mean, count, inp, out)`: its own numbers, its neighbours' mean of
  each shared one, how many neighbours it has, and what the body delivered. The engine updates each cell with chance
  UPDATE, adds a little noise to every number a cell keeps, shows each shared number clipped to -1..1 with noise of
  1% (drawn afresh every tick), and builds the sheet from one birth vector (identical bar declared noise). The body
  reaches the sheet only through `cells()`, `give()`, `get()` and `take()`; watching uses `view()`, and the
  experimenter's `damage()` replaces cells with new-born ones. `test_rules.py` checks every rule's imports, signature
  and birth at two sizes, and that no body code reaches inside.
- **A loophole, closed.** The engine once passed a rule its own numbers as a view into the sheet's memory, and
  compiled code doesn't check bounds: a rule indexing past its own numbers would have read its neighbour's. The engine
  now copies into the rule's own small arrays, and `test_rules.py` runs every rule with bounds checking on.
- **A cheat, closed.** The engine once let a rule share exp(-beta d): it showed exp(-5 d), but added the noise to d
  first, so the tiny number shown (about 1e-300 at d = 140) was in effect free of noise, and the mean gave the
  neighbours' smallest d exactly. It broke the spirit of the noise rule. Twelve of the 18 shared numbers of that
  version used it: the election, ring counts, x, y, both distance fields, tips, offers and news. The engine now
  encodes nothing; the user set the range (-1..1) and the noise (first 10%, then 5%, settled at 1%).

## What averages can do, honestly

- **Read sums, not means.** A neighbour moves the mean by at most 2 / count, so a cell works with the sum over its
  neighbours (count x mean), whose noise is about 0.03 at 1%.
- **Flags count exactly.** Shown as +1 or -1, a flag's sum counts the neighbours showing +1. At noise 10% (the
  first setting) a count of 8 was wrong once in 2,500 reads, and a single misread could seed a whole false field
  (below); at 1% it doesn't happen.
- **A few levels, if every mix stays apart.** A number shown at a few strengths tells a cell how many neighbours
  show each, as long as every mix that can occur sums clearly apart. Trap: path + tip summed exactly to two pulses
  (2 + 0.8 = 1.4 + 1.4), so cells beside parallel paths took pulses that weren't there and paths pulsed by
  themselves. The strengths now leave every mix of up to two cells at least 0.4 apart (`rules/see.py`).
- **Gradients for where.** Hold some cells fixed and let every other cell take its neighbours' mean: the sheet
  settles into a smooth field, read closely from means. The obvious tool for coordinates; I first veered away from
  it, trying to keep the counted coordinates of the old version.
- **Waves.** An excitable flag runs outwards from where it starts and dies at the edges and where waves meet.
- **Not the smallest.** No mean gives the smallest of the neighbours' numbers. What a cell can get instead: a count
  mod K, shown one-hot on K flags (below).

## Distance mod 5 (`rules/see.py`)

- **What it is.** A field from some source cells: each cell shows its distance mod K on K flags. In a settled field
  a cell's neighbours are one step nearer, level or farther, three residues in a row, so the lowest is the one after
  the gap, and a cell is one more than that.
- **Mod 4 isn't enough.** On a diagonal of a square ring a cell has only one neighbour one step nearer. If that one is
  wrong, the next cell sees "lowest = level" and shifts up one; the cell at the break then sees four residues, which
  mod 4 can't place, and the defect locks in. Mod 5 sees the gap: 20 single-source fields of 20 exact, against 8 of
  20 at mod 4.
- **A value may only fall.** If one more than its lowest neighbour would be higher than what a cell has (or there is
  none), it lets go and rests a few updates before taking a value again. Without that, a single misread (at 10%
  noise) seeded a false field that counted up for ever, a perpetual source of waves; and a field whose source has
  gone fades instead of counting up.
- **Only from one source, at any size.** Where waves from several sources meet, one can arrive a few steps early by
  chance; mod 5 can't tell distance 45 from 50, and the meeting line settles in the wrong place for good. At 97 that
  happened in 8 lives of 10 (mod 6: 1 of 10; slower, steadier fronts helped but not enough); the unevenness of fronts
  grows with size, so no fixed K is safe at any size. A first plan placed the organs where the corners' fields meet
  (the edge midpoints and the centre lie on that cross); it was dropped for this. Fields from one source (each
  actuator) are fine.

## Where am I (`rules/organs.py`)

- **The race.** Corners beat as pacemakers at random periods; one reached by another's wave before its own beat
  stands down. Exactly one left, the organiser (once called V, when it was also an actuator), in 20 lives of 20,
  typically by tick 100-500 (worst about 1,100). Traps:
  - with a rest of 4 updates after excitation, waves re-entered and circled (about 600 cells excited at all times),
    and in 4 lives of 10 every corner stood down; a rest of 10 cured it;
  - damage started circling waves (spirals) anyway, which beat faster than the organiser and knocked it out. Each beat now
    carries its number mod 3 (two flags), and a cell takes only the next beat after the last it took: a wave curling
    back, or a stray piece of an older beat, is refused. Alternating two parities wasn't enough: a stray piece of the
    previous beat has the other parity and was still taken, by the organiser too.
- **Labels need their own pulses.** Labels first rode the organiser's waves along the edges. But those sweep each
  far edge all at once (every cell of it is the same distance from the organiser), so a label started at a far corner
  had only the rest time to travel, and reached about 11 cells. Labels now run as their own pulses along the edges,
  started by the organiser's two coin-tossed neighbours at each of its beats.
- **Labels must expire.** Before the race is decided, a corner that later loses labels the edges; when it stands down,
  edges and corners it labelled get no more pulses and kept the old labels for ever (in 1 life of 8 a far corner held
  an old -1 and never started its +1). A label lapses after some of the organiser's beats with no pulse to renew it
  (3, then 6: below).
- **A label stops at a corner.** The two edge cells beside a corner are each other's neighbours, so a label would leak
  round the corner. The cell at the end of an edge shows its label at half strength, which edge cells ignore and
  corners take; a corner starts the next edge's label at 0.75, which the edge cell beside it takes only when it sees
  no full label.
- **Gradients settle slowly, so: momentum while drifting.** Plain averaging settles in about size^2 updates (at 49,
  labels right by tick 750, x within a column by about 3,000). With a cell carrying on 0.9 of its last move while its
  short and long averages of x differ by more than 0.03, about 1,500. Momentum always on amplified the noise (x
  wobbled by 1-2 columns).
- **The noise keeps slow wobbles up**, about half a column at 49 at 1% (at 5%, up to 5 columns at 97): no stillness
  test finer than that can pass, and a cell exactly on a threshold flips. So a mark (the band that places a name)
  flips only when x is 0.05 past its threshold, and stillness is judged at 0.03.
- **Names must stand still, and stay.** Names taken early drifted a cell or two as x settled, and each move re-grew a
  field and its paths. Now: a cell takes a place only while still; a name after 300 updates of holding it (80 let a
  turning point of the momentum pass for still: one life named an organ three cells off, and a second of it
  appeared later); a named cell keeps its name while its x stays within 0.15 of the place's, and shows 0 on mark so
  no neighbour takes the same name. 12 lives of 12 named by tick 1,270-2,160; in 10 no name ever changed, in 2 one
  was lost and retaken once (the lapsing labels, below); the organs within 2 cells of where they belong. A slower average for the marks (600 updates) was worse: it
  lagged while x settled.

- **One missed beat costs three, so labels must outlive it.** The user saw every path vanish at about tick 10,000
  (seed 0), and come back about 1,000 ticks later. Traced: the coin-tossed cell that starts the x = -1 edge's label
  pulses, beside the organiser, missed one beat (it didn't update while any neighbour was excited by it: rare, as
  updates are random). A cell takes only the next beat after the last it took, so it then refused the next two as
  out of turn, and started no label pulse for three beats. With STALE = 3 the x = -1 edge forgot its label; so did
  the far corner, which starts the y = 1 edge's +1; so did the y = 1 edge, and the sensors on it lost their names
  and their paths faded. STALE is now 6 beats (a count of beats, not tied to size). Seed 0 then holds every name and
  path to tick 12,000, and 6 lives of 12,000 ticks had no name change after first naming (before: 2 and 4 in two
  lives of 4 at 4,000 ticks).

## Wiring (`rules/wiring.py`)

- **Breadcrumbs are impossible from averages** (a cell remembering which neighbour a wave came from). Instead a cell
  needs its distance to each sink, and which neighbours are one step nearer or farther.
- **The sinks send the distance fields: no magic knowledge.** To save two shared numbers, the wiring once took a
  cell's distance to one sink to be its row (making that sink the whole tail edge to fit) and to the other the larger
  of x and y. That built
  into the rule where the organs were meant to be. Now each sink, once named, sends out its own field.
- **Path cells show their residue as a pattern on three flags** (any three residues in a row independent, so the
  sums untangle into nearer, level and farther), at a strength for path, tip or pulse. The patterns chosen add the
  least noise when untangled (at most 1.41 times one sum's); the first choice added up to 1.73, and at residue 4 a
  misread started a pulse every few hundred ticks. None now in 12,000 ticks.
- **The tip must show itself on the path flags.** Tips announcing themselves on the offer flag instead let cells level
  with a tip (beside it, below its parent) offer too, and paths spread into fans of 300-590 cells. Excluding cells
  with a path cell level with them stopped the fans but stranded tips on a field's diagonal, where the only cell one
  step nearer sat beside another path. Now a candidate is a cell that sees a tip one step farther: exact.
- **A handshake by counting.** The tip says "go" while it sees exactly one raised hand (twice in a row to start);
  a candidate joins after three "go"s in a row with its hand up. A candidate with another path cell above it as well
  raises its hand rarely: joining would give that path a second way on and split its pulses.
- **Two copies of one pulse must read as a pulse.** Where paths run side by side a cell can have two parents, and a
  pulse coming down one splits; the copies may meet again at once. With strengths where two pulses summed like a
  tip and a path, the cell where they met took neither and the pulse died.
- **Result.** 8 lives of 49: 319 of 320 pulses arrived, 1 extra arrival, about 53 ticks each.
- **Fading and pulses.** A path cell with no path cell one step farther leaves (after 2 reads). A pulse is carried
  for 6 updates, then rested 7; the next cell must update at least once meanwhile (it almost always does at 0.9).

## Learning, first brain (withdrawn)

The first brain had sensors R and B and actuators A (forward) and V (back off and turn), a news wave, a trace and a
chew delay; all are gone (below: symmetric organs, reward at contact). Its lessons:

- **News as a wave.** The news of a kick was first a min-age field (the withdrawn exp trick), then a wave across the
  sheet: a sensor that saw news around it after its own had gone by forgot its own kick, so only the more recently
  kicked kept a trace. Trap: a sensor still resting from sending its own news ignored the other's, so both kept
  their traces and a bad taste lowered the food's balance too (food ended at 0.83); noticing news whenever its own
  had gone by fixed it (0.97).
- **The min-age field** (kept for its lessons): a field ages more slowly than a cell's own count, so "news fresher
  than my kick" fired on a cell's own echo; and one field for both sensors conflated kicks a few updates apart.
- **Two factors.** The balance moved by taste x the cell's recent-input trace; which way it sent its pulse didn't
  enter. Tumbles (now and then a pulse to V) made a creature that saw nothing search.

## Symmetric organs: no purpose in the cells (2026-10-16)

- **The rule knew what the organs were for.** R and B differed only in name, but A and V were different kinds (V was
  the organiser corner as well as an actuator), and the brain preferred A: born b = 0.9 towards A, a good taste
  pushed b towards A and a bad one towards V, a bad taste made R and B recoil towards V, and tumbles went to V. So
  "A approaches, V avoids" was built into the cells. The test now: the rule is unchanged if the two sensors, or the
  two actuators, are swapped, and the body draws its wiring (colour to sensor, thruster to actuator) at random each
  life.
- **Organs.** The organiser corner is no longer an organ. Sensors S1, S2 sit either side of the middle of the y = 1
  edge and actuators M1, M2 likewise on y = -1, placed by one rule; 1 or 2 is the side of the middle (x < 0: 1), which
  the coin toss settled. Named within 1-2 cells of their places in 4 lives of 4; but 2 and 4 name changes after first
  naming in two lives (before: 0 or 1). Traced to labels lapsing after a missed beat (see Where am I): fixed.
- **The old rule did credit assignment for free.** With "good means A" built in, it only had to learn what a colour is
  worth (two factors). A symmetric rule has to learn which action earned the reward (three factors), and that is
  hard here. Poison's share of meals by thirds after moving, 16 lives of 8,000 ticks with learning (`--measure 16`)
  unless said:

  | version | poison share | chance of going forward at the end: poison / food |
  |---|---|---|
  | old, asymmetric | 43%, 39%, 42% | 0.20 / 0.84 |
  | symmetric, a fresh choice for each pulse | 46%, 49%, 49% | 0.46 / 0.54 |
  | a held mode, chosen afresh after each reward | 49%, 48%, 54% | 0.38 / 0.43 |
  | held mode, 16 lives of 24,000 | 47%, 38%, 40% | 0.42 / 0.49; several lives locked at 0 or 1 |
  | ... and the eaten colour's sensor stimulated on eating | 50%, 44%, 37% | 0.36 / 0.24; worse lock-in |
  | ... and learning steps x 0.3 | 51%, 46%, 45% | 0.42 / 0.53; no lock-in, weak |
  | ... and no learning where the other sensor fired first | 40%, 49%, 46% | 0.41 / 0.42 |
  | learning off | 50% | 0.50 / 0.50 |

- **Why: the delay.** A pulse takes about 53 ticks to cross the brain, and the reward comes 17 after the meal. With a
  fresh choice for each pulse, the sends a trace weights most (a median 17 updates before the reward) were still in
  flight at the meal: at a reward the eaten colour's trace pointed to A 32% of the time, to V 28%. A held mode makes
  the pulses in flight and those that drove the meal agree: 43% against 24%.
- **Why: the sensors compete.** A colour is often eaten while its sensor is in the mode for V, and not soon after it
  switched (a median 18 firings in that mode): the other sensor's pulses to A push harder than V pulls back, so the
  creature eats what one sensor was steering it away from. That sensor then learns the wrong way whichever the taste:
  good reinforces V, bad pushes it to A. So the poison's sensor settles near a third of the way to A, and the food's
  has a tipping point there: below it, it slides to V and stays (it eats food only by accident, in V's mode).
- **Dead ends.** Stimulating the eaten colour's sensor on eating (so it holds the trace) credits it for those
  accidental meals too: worse. Ignoring meals where the other sensor fired first didn't help either.
- **The way out: two forward thrusters, two factors.** The user's design: the actuators mirror the sensors, two
  thrusters at the tail's corners, both pushing forward; one alone also turns the body away from its side. A sensor
  learns only "fire both, or one?" (one: always the same, its side, by a coin toss; a random side each time would
  average out to straight ahead). Two factors again (a good reward makes both more likely), but no cell knows what
  either actuator does: "good: drive harder" is a gain, and swapping sensors or actuators changes nothing. 16 lives
  of 8,000, with the trace and news: poison's share 50%, 45%, 45%; chance of firing both at the end, poison 0.07,
  food 0.91 (learning off: 50%, and 0.50 both).
- **The body caps the behaviour, not the learning.** With p set by hand from birth (poison's sensor 0, food's 1),
  poison was still 46% of meals; a sharper veer (turning 2x, 4x) didn't help (41-55%), nor firing nothing at all at
  poison (45-48%). Every poison meal had been seen clearly just before (median strength 0.99): the creature charges
  straight at food, its eyes can't tell left from right, so it can't steer round poison in the strip ahead, and a
  pulse takes about 53 ticks to cross the brain.
- **Reward at contact (withdrawn: it made the body assign credit).** The chew delay with eyes shut, the flavour
  stimulus on eating, the news wave and the trace were all there to credit the reward to the eaten colour's sensor
  when both sensors got it. I proposed that the body give the reward only to the eaten colour's sensor, as the block
  touches the mouth, and called it a simplification; the user agreed on that framing. It was the body doing the
  credit assignment the brain had been doing (see Taste, below). With it, p moved a quarter (later half) of the way
  to 1 or 0 at each reward, with 26 shared numbers. 16 lives of 8,000: poison's share 50%, 47%, 43%; firing both at
  the end, poison 0.09, food 0.91. As good as the trace and news, but only because the body did their work. Ceiling
  with p perfect: 48%, 42%, 47%.

## Vision (`creature.py`)

- **Shorter, and blocks hide what is behind them.** The eyes cast 25 parallel rays across the strip the mouth sweeps;
  each stops at the first block it meets (a disc of radius 1, its drawn size) within 15 units, and a block counts
  1 / (1 + (d / 5)^2), less where hidden or partly outside. Before: no hiding, out to half the world, half-weight at 10.
  The view draws the rays as a fading beam, with shadows behind blocks.

## Scoring per unit of time

- **Score per tick, not per meal** (the user). Two scores: how soon the sensors learn (ticks after moving until both
  are within 0.2 of right: the rules), and food minus poison per 1,000 ticks (the sheet and the body). Poison's share
  of meals alone hides the rate: a slow creature can eat well and little.
- **Slower or sparser raises the ceiling but costs meals.** Ceiling with p perfect, poison's share by thirds (meals
  per third, 32 lives): thrust 0.5 (now) 48%, 42%, 47% (about 380); 0.25: 43%, 41%, 44% (180); 0.125: 23%, 32%, 30%
  (80). 9 blocks of each colour instead of 18: 41%, 43%, 46% (135); 5: 34%, 36%, 42% (75). For the same meals, slower
  is better than sparser: it gives the 53-tick brain time to act. But per tick the slow creature loses (16 lives
  each, learning on):

  | version | learned (median ticks after moving) | food minus poison per 1,000 ticks, by third |
  |---|---|---|
  | thrust 0.5, p moves 1/4 of the way | 16 of 16, 1,331 | -0.03, +0.38, +1.06 |
  | thrust 0.5, p moves 1/2 of the way (now) | 16 of 16, 997 | -0.20, +2.15, +0.48 |
  | thrust 0.125, 1/2 of the way | 13 of 16, 2,945 | +0.14, +0.41, +0.68 |

  Once learned the thirds differ by noise; 16 lives are too few to rank the net food finely.
- **Angling the thrusters doesn't help** (the user's idea: a lone thruster should mostly turn the body, not drive it
  round a wide circle into the poison). A thruster at angle a from straight back pushes cos a forward and sin a to
  its own side (so its turn adds up: (cos a + sin a) x today's turn); both at once go straight, at cos a of today's
  speed. Ceiling with p perfect, poison's share by thirds (meals, 32 lives): 0 degrees (now) 48%, 42%, 47% (about
  380); 60: 44%, 51%, 39% (about 100); 80: 43%, 45%, 21% (about 23: it hardly reaches a block). Fewer meals, no
  better share: the poison is eaten while the food's sensor drives straight at food behind or beside it, not
  while the poison's sensor veers.

## A second brain: the designed circuit (then `brains/mixed_signal.py`, now `brains/designed.py`)

- **Why.** The user, after Sepulchre's work (Ribar and Sepulchre 2021, "Neuromorphic Control"; Huo, Forni and
  Sepulchre 2025, rebound winner-take-all): one mixed-feedback element (a leaky node; elements that put a current into
  a node, a sigmoid of a filtered voltage, with a sign and a timescale) builds both discrete and continuous behaviour.
  A designed circuit for the whole creature, beside the sheet, says what the sheet costs, and is the groundwork
  for rebuilding a cell as such a circuit.
- **The split.** The body and world went to `world.py`; `Life` talks to any brain through sensors 0, 1 and motors 0, 1;
  the sheet became `brains/grown.py` (now `brains/sheet.py`). Four recorded lives matched the old code bit for bit
  (meals, firings and sensors' p), so the refactor changed nothing. Thrusters must fire in the same order as before:
  spin is a float sum.
- **The neuron.** The paper's spiking neuron (fast positive feedback, slow negative; tanh) at the paper's bias was
  bistable, not excitable: one pulse set off firing that never stopped (bias -1.2 to -1.4, recovery 5-20 ticks). At
  bias -1.6 it rests: one spike for any pulse above about 1 (a tick long), and noise 0.2 gives about 6.5 spikes per
  1,000 ticks of its own (the sheet's sensors fire by themselves about 9 per 1,000).
- **Noise grades a synapse.** A sensor's spike crosses a synapse of weight 0.05 almost never, 0.15 half the time, 0.35
  almost always: noise makes the choice, so a plastic weight between them is a chance of firing the other motor too,
  as the sheet's sensor's p is.
- **A/B, the same 16 lives each:** sheet learned in 16 of 16 (median 1,024 ticks after moving), food minus poison per
  1,000 ticks by third -0.20, +1.97, +0.37, poison's share 52%, 38%, 47%; designed circuit 16 of 16 (median 1,090),
  +0.89, +1.13, +1.32, and 40%, 39%, 35%. Learning after moving is about as fast (set by how often it eats); but the
  circuit moves from the first tick and reacts at once, where a pulse takes about 53 ticks to cross the sheet, so it
  steers round more poison than the sheet brain could even with perfect p (about 46%), and nets about twice the food
  in a life.

## Taste: one input, and credit assigned inside the brain (2026-10-16)

- **How the body came to assign credit.** The user had described the sensor cell as having "two inputs (what it
  senses and food/poison)". I read "a food/poison input on the sensor" as licence to route the reward to the right
  sensor, and proposed "reward at contact": the body gives food or poison only to the eaten colour's sensor. I
  presented it as removing four mechanisms (chew delay, flavour stimulus, news wave, trace) and one shared number, and
  argued "the body is allowed to know what it ate and what colour it was, just as it knows which eye saw it". What I
  didn't say: those four mechanisms were the brain's credit assignment, which this file had already named the hard
  part ("the old rule did credit assignment for free"). Deleting them didn't simplify the problem; it moved its
  hardest part into the body. The user agreed to a "simplification", not to that. The warning signs were all
  written down and passed over: the README's count of shared numbers said "learning: none (everything a sensor learns
  from is delivered to it by the body)"; the designed circuit was then built on the same `reward(sensor, value)`,
  with four reward terminals beside the sensors; and learning got faster and cleaner just as the brain got simpler.
  The user found it from the schematic, by asking where the reward input was. The lesson: whenever a change lets the
  brain drop machinery, ask where that machinery's job went, and if the answer is the body, say so plainly or don't
  propose it (now in `AGENTS.md`).

- **Why.** Learning had been `reward(sensor, value)`: the body handed the reward to the eaten colour's sensor, so the
  body did the credit assignment. The user's ruling: for every brain, taste is one input, +1 for food and -1 for
  poison at the tick a block touches the mouth, else 0, saying nothing about which sensor. The body must never be part
  of the solution. The sheet brain gets taste through a fifth organ, T (the marked cells on the y = 1 edge between S1
  and S2), not a broadcast to every cell: a sheet-wide signal would be magic.
- **Measuring.** 16 lives are too few to rank variants: with perfect p from birth, net food per 1,000 ticks came out
  +0.38 in one run of 32 and the oracle's (the old body credit) +0.47. Rank by lives learned, median time and p at
  the end; use 64 lives; and run the oracle as the reference in the same batch.
- **What a sensor can know.** At each meal (sheet brain), ticks since each sensor's last stimulus: the eaten colour's
  sensor was stimulated within 10 ticks in 85% of meals, the other in 17%. Giving credit only to the sensor stimulated
  last cuts the wrong share to 7% (within 20 ticks: right 89%, wrong 7%). So the one taste carries enough, if the
  sensors also know which of them was stimulated last.
- **Designed circuit.** An eligibility node per sensor (charged by its spikes, leaking over ELIGIBLE ticks) gates two
  amplifiers that charge or empty P while taste is good or bad. Each spike also empties the other sensor's E (FORGET,
  cross-inhibition). 64 lives: E 10 with FORGET learned 63/64, median 1,512, net +0.86 (no FORGET: 64/64, 1,830, +0.72;
  the oracle about +0.92).
- **Sheet, first try:** a sensor learned when taste began on a T cell beside it and it had been stimulated within
  ELIGIBLE updates. 24 of 32 lives learned. Counting two stimuli, or a lower RATE, did no better (23 and 21 of 32).
- **Pings.** A stimulated sensor shows a ping for 2 updates, then rests for 4. A T cell that sees a ping does the same,
  so a one-way wave runs along the T cells to the other sensor (about 8 updates), which forgets its stimulus. A cell
  that has just pinged rests, so its echo is ignored. This is the circuit's FORGET, made from local signals: 31 of 32
  lives learned. It costs one shared number, ping. Waves from both sensors at once annihilate, and then both stay
  eligible, as before.
- **A gap in the taste organ.** The lives that still failed (6-8 of 64) each had one sensor whose p never moved. Its
  T neighbour was missing: the mark's end had drifted a cell after the sensor took its name, and the cell between was
  neither marked (so not T) nor free to be a sensor (a named neighbour). Fix: a cell on y = 1 between a named sensor
  and the mark takes T too; a T cell shows mark +1 and keeps its name while marked or beside a sensor. Every sensor in
  32 sheets then had a T neighbour at 4,000 and 8,000 ticks. After the fix, 64 lives: ELIGIBLE 15 learned 64/64
  (median 1,210 ticks after moving; net +0.46; p at the end 0.17 and 0.86), ELIGIBLE 10 63/64 (1,305; +0.44); the
  oracle 64/64 (584; +0.58).
- **Not fixed: a doubled actuator name.** In one sheet of 32 (Life seed 17) two cells took M1. It happens with or
  without the gap fix, so it is older.

## Telling food from poison: a pointed body and a faster circuit (2026-10-17)

The user's target: at least 2 food for each poison after 10,000 ticks, ideally nearer 10, worked out on the
designed circuit (quicker to learn and to tune). Measured as food:poison over 24-32 lives, with p held perfect by
hand (the ceiling) or learning; "second half" is ticks 5,000-10,000. Before: 1.5 at the ceiling, 1.5 learning, 4.7
meals per 1,000 ticks.

- **Where poison was eaten.** Every poison meal had been in view for at least 30 ticks. Three causes, each measured:
  the square's mouth was its whole front edge (5 units), and every turn swept it across poison beside the corridor;
  each neuron could spike only about once in 17 circuit ticks, so the creature moved in big lunges that coasted 2-3
  units into whatever lay ahead (the user's "slow brain and momentum"); and the plastic synapse leaked (at p = 1 a
  sensor's spike reached both motors only 74% of the time, so a quarter of food sightings became veers).
- **An ideal reflex first.** A controller with no brain (straight at food, veer from poison, the right thruster at
  once) found what a body allows: on a pointed body with gentler thrust it reached 10-27 (0.5-2.6 meals per 1,000),
  refractory time and blind wandering cost little, and 10% leak in the reflex halved it. So the body had to change,
  and then the brain had to be fast and clean.
- **The body** (ground rules, agreed with the user): an equilateral triangle, point forward, the point the mouth
  (eaten within EAT of it; the eyes' corridor is 2 EAT wide); PUSH 0.5 → 0.2, TURN 0.08 → 0.16, DRAG 0.2 → 0.5
  (small kicks that die quickly, a tighter turn); SENSE 0.21 → 0.5. Triangle alone: ceiling 1.5 → 2.5. Slower thrust
  or more drag alone raised the ceiling but starved the creature (0.1-0.6 meals per 1,000 ticks) while the circuit
  still lunged.
- **The circuit runs 4 of its ticks to each tick of the world** (SPEED). Its refractory time is unchanged in circuit
  ticks, so it spikes four times as often and each kick is a quarter as big relative to the body's motion. Ceiling
  4.6 at SPEED 4 (1.0 meals per 1,000). A shorter recovery (tau 3 instead of 10) broke the neuron: almost no spikes.
- **A clean synapse.** WEAK 0.05 → 0 and STRONG 0.35 → 0.7: a sensor at p = 1 now reaches both motors about 99% of
  the time, at p = 0 never. Ceiling 4.6 → 12.7, meals 1.6.
- **Each sensor hushes the other** (INHIBIT 1.5 over HUSH 10 ticks, a hush node per sensor): while it sees food the
  creature stops answering poison, and the other way round, so it no longer swerves between them into a third block.
  Ceiling 12.7 → 14.2; learning, second half, 4.5 → 8.5. Stronger (3) or longer (25 ticks) did no better.
- **Learning, 10,000 ticks (24 lives): 4.5 over the whole life, 8.5 in the second half, 1.8 meals per 1,000; p at
  the end poison 0.13, food 0.99.** Over 20,000 ticks: 6.1 over the life, 8.2 over ticks 10,000-20,000. 64 lives of
  10,000 ticks: 4.3 over the life, 7.0 in the second half, ceiling 14.8; on `--measure`'s 32 lives the thirds are
  2.2, 5.9, 4.6. Poison meals are few, so the ratio differs a lot between sets of lives: rank variants on 64. p for
  poison settles near 0.1, not 0: poison meals are now rare, and each is a learning event, while food meals now and
  then credit the poison sensor when both were seen.
- **Dead ends.** Fewer blocks (5 or 9 of each colour, on the square: Scoring, above): fewer meals, little better
  share. More spontaneous spikes (a neuron's bias -1.6 → -1.4 or -1.3): blind forward kicks hit poison, and with the
  hush on, its sensor was then silenced (ceiling 0.9-1.9). A lower bias (-2.0): no meals at all. A boredom drive
  (both motors pushed while neither sensor had fired lately): more meals (2.4) but a worse ratio (7.9 in the second
  half). LEARN 0.5 or ELIGIBLE 20: worse (6.2, 7.2). SENSE 1.0: 7.2; TURN 0.24: 6.9.
- **The sheet brain on the new body: starved.** Each kick now moves the body about a fifth as far, and the mouth is
  a point, so at one sheet update per tick it ate about 0.9 meals per 1,000 ticks and learned in only 12 of 32 lives
  within 10,000 ticks (median 4,613 after moving; it had been 32 of 32 on the square). Its food:poison by thirds was
  1.2, 2.6, 2.5 (1.2 on the square); with p perfect, 6.7, 5.3, 2.2 at 0.7 meals per 1,000. The same cure as the
  circuit's: run the sheet several updates (steps) to each tick of the world (SPEED). 32 lives, learning: 2 steps,
  17 learned, food:poison 1.2, 1.7, 4.0, about 1.0 meals; 4 steps, 24 learned, 1.5, 2.0, 3.0, 1.3-1.8 meals, net
  food +0.25, +0.53, +0.89 per 1,000 ticks; with p perfect, 3.6, 2.7, 4.8 at 1.6 meals. Kept at 4: a pulse crosses
  the sheet in about 13 ticks instead of 53, and the creature moves after about 600 ticks instead of 2,500. The cost
  is compute: 37 ticks a second instead of 150.
- **What would go further.** The eyes can't tell left from right, so a veer is always to one side, sometimes into
  poison lying beside the food: one sensor per side would fix it, but that is more sensors, a ground-rule change.

## Simulating the designed circuit (2026-10-18)

Reviewed with evolving circuit brains in mind (many lives of 10,000 ticks), so it must be fast and must not be
exploitable.

- **Where the time goes.** A life took about 1.5 s per 1,000 ticks, 85% of it in `Circuit._advance`: 80 integration
  steps per world tick, each a dozen numpy calls on 11 nodes and 24 elements, so call overhead swamps the arithmetic.
  The same integration as one numba loop, drawing from the same random generator, matched the original (voltages
  within 2e-12; motor spikes the same over 3,000 ticks, and the meals of 4 lives) and ran the circuit about 45x faster
  (0.28 s per 10,000 ticks). Then the world (`look`, `move`) and the per-tick Python in `Life` dominated (about 3.5 s
  a life), so the eyes and mouth are compiled too (blocks held as arrays). Passing numpy's random generator into
  compiled code costs about 25 us a call, so each tick's noise is drawn beforehand in one call (the same stream). A
  life now takes about 0.5 s (from about 15). `test_compiled.py` checks both against plain numpy versions of the same
  equations (random circuits and scenes; it catches a 0.1% error in the circuit and 1e-15 in the eyes). The whole
  life in one compiled function would save most of the rest, for when evolution needs it.
- **An exact check needs the same arithmetic on every machine.** The eyes' check once failed on GitHub (1,006 of
  3,000 scenes differing) though nothing had changed: the plain version used numpy's `d @ f` and `norm`, which go
  to OpenBLAS, and OpenBLAS picks its kernel by CPU; on an AVX-512 machine those round differently in the last bit
  from the compiled `dx * f[0] + dy * f[1]`. The plain version now writes the sums out in the same order (it passes
  under `OPENBLAS_CORETYPE=SkylakeX`). The lives use BLAS only where blocks are placed (a `norm` against a
  threshold), so a last bit there could change a life only for a block exactly at the threshold.
- **The integration step doesn't matter.** An input is a current lasting one circuit tick (a quarter of a world
  tick), fixed in model time, not in steps; noise is scaled by sqrt(DT); spikes are found with hysteresis at each
  step. From DT 0.2 to 0.01 (now 0.05) these agreed within sampling noise: spontaneous spikes (10-11 per 1,000
  ticks), spikes per stimulus (0.87-0.91), how often the plastic synapse relays, and one taste's move of p (0.287-0.289,
  noise off). 64 lives at DT 0.05, 0.1 and 0.2: food:poison 4.2, 4.8, 4.2 (poison meals 205, 172, 199, give or take
  14). So DT 0.1 would halve the cost, if checked.
- **Pulse shape: stimulus safe, taste not.** A stimulus works by charge: the same charge over 0.25 to 8 circuit
  ticks gave 0.85-0.86 spikes per pulse. Learning works by how long the taste node stays above 0.5 (a steep sigmoid,
  with LEARN's gain set by hand for "above half about 1.3 ticks"): the same charge over 0.25, 1, 2 and 4 circuit ticks
  moved p by 0.22, 0.29, 0.36 and 0.05. Harmless while the pulse is fixed, but an evolved circuit would tune itself
  to that exact rectangle. An input delivered as a charge at an instant, with the input node's own leak setting how
  long it lasts, leaves no tick in the interface (it changes both input nodes, and LEARN would need recalibrating).
- **The plastic synapse is graded only for p below about 0.4.** Its weight is STRONG x p = 0.35 at p = 1/2, which
  relays about 85% of spikes, not "about half" as the docstring said.
- **Defences, for any circuit brain that is optimised:** each input at a random time within its tick (inputs on the
  tick boundaries make intervals whole ticks, a rhythm a resonator could lock to: the circuit's lockstep; not built
  until 2026-10-20, below: Noise as biology makes it); limits on
  time constants (at least about 5 DT) and on gain x slope / capacitance, and each generation's best re-run at DT/2;
  fresh seeds for every evaluation, and the result judged on lives never trained on; every parameter a few percent
  off at birth (mismatch, as Sepulchre stresses: no knife-edge tuning or exact cancellation between identical parts);
  noise on every node, as now. Each motor spike is a full kick, so a fast oscillator gets the most thrust: how the
  body bounds thrust is a body question for the user.

## Noise as biology makes it (2026-10-20)

The user asked how noise was decided, where it goes in, and whether it could be cheated. The answers were: 0.2 per
node, picked when the first circuit neuron was built; a fixed current on every node; and yes, in three ways. So the
noise was remodelled on biology's (Faisal, Selen and Wolpert, "Noise in the nervous system", Nat Rev Neurosci 2008),
which subthreshold silicon shares (Sarpeshkar, Delbrueck and Mead 1993), and the user accepted it all.

- **Three holes in the old noise.** (1) *Inputs on tick boundaries*: listed above as a defence (Simulating the
  designed circuit) but never built: every stimulus and taste was a rectangle starting exactly as a world tick began,
  so intervals were whole ticks and the taste's shape fixed, a rhythm and a template an optimiser could lock to.
  (2) *Memory write noise vanished at a finer step*: rough by 10% of each step's change, its variance over a fixed
  time fell in proportion to the step, so the half-step check saw a quieter memory and could flatter a design.
  (3) *Size bought silence for free*: noise was a fixed current per node, so scaling a node's capacitance and every
  current into it by k (the same behaviour; the slew limit, being current over capacitance, can't see it) cut its
  noise k times, for power alone (0.01 per unit in the minimal search's score) and no extra parts. The minimal search
  was heading there: tuned sensors at C 4-6, where they were designed at 1.
- **What biology does.** Noise comes from discrete events: channels opening (relative noise 1/sqrt of their number),
  vesicles released (binomial), photons and receptor events (Poisson, in continuous time). Thermal noise is
  microvolts, negligible. Quiet is bought with more channels, so area and energy (Laughlin, de Ruyter van Steveninck
  and Anderson 1998): reliability costs power. Awake cortex fluctuates by about 2-4 mV against 15-20 mV from rest to
  threshold; the old 0.2 gave the standard neuron about 0.14 V against about 1 V, inside that, so the size was right
  and the scaling wrong. And parts differ: identified neurons of one type by 2-5 times in channel density (Marder and
  Goaillard 2006), held in shape by homeostasis; analogue transistors by 10% or more (Pelgrom 1989).
- **The model** (`mixed_feedback.py`; the details in its docstring). Shot noise of variance SHOT x |I| per tick on
  every device current, summed gross over a node (two big opposing currents still flicker), the body's pulses
  included; membrane noise of variance MEMBRANE x C per tick on every node but a memory; a memory node only its
  writers' shot noise (still while unwritten, rough by the square root of what is written); 10% mismatch in every
  part, drawn per part from the seed when the arrays are built (so parts grown or changed in a life get it too);
  each eye a Poisson process and every pulse at a random moment within its tick, spread over the steps it overlaps.
  Scaling a node by k now buys sqrt(k) quiet for k times the power. It lives in one integration step (`_step`) that
  the circuit and `minimal/fastlife.py` both call, so neither can leave it out, with no switch: the noise can only be
  scaled within half to double. `test_compiled.py` checks it: memory and leaky-node spreads the same at step 0.05
  and 0.025 (the old model fails: its memory spread fell by 1.4), a node 4 times as big quieter by 2, not 4, every
  part mismatched by about 10%, a pulse's charge exact wherever it falls.
- **Calibration.** SHOT (0.005) and MEMBRANE (0.02) share the old variance equally for the standard neuron at rest
  (its two elements carry 1.87 each, cancelling: gross 3.7, net 0). Without mismatch it fires 4.4 times per 1,000
  ticks on its own, as before (4.6; the 6.5 above was with older parameters), one spike per pulse.
- **The paper's neuron doesn't survive 10% mismatch.** With it, about a third of standard neurons (35% of 200) fire
  on their own at 20-60 per 1,000 ticks (median 2), and a pulse gives 1.46 spikes on average, not 1 (3%: 11.5 per
  1,000, 1.15). Its excitability balances fast positive against slow negative feedback of equal gain and bias -1.6,
  near the bistable range (bias -1.2 to -1.4, above): a 10% shift in bias or in either gain tips it into firing by
  itself. Biology keeps such neurons in shape by homeostasis; these circuits have none, except the adjusting
  circuit's rung 0, which adjusts each neuron's excitability.
- **Every circuit brain collapses** (32 lives of 10,000 ticks, the same lives under the old and the new simulator;
  food:poison in the last third, old -> new): designed circuit 4.6 -> 1.0, recruiting circuit 5.4 -> 1.3, adjusting
  1.7 -> 0.9, healing circuit 1.2 -> 1.2 and healing cascade 0.9 -> 1.2 (these two need longer lives: their
  leaderboard is at 30,000 and 100,000 ticks). Taking mismatch away (a diagnostic only) separates the causes: the
  designed circuit 2.54 with none, 1.63 at 3%, 1.02 at 10%; the recruiting circuit 3.27, 1.81, 1.26; the healing
  circuit 1.52, 1.50, 1.18. So mostly mismatch; the rest of the designed circuit's loss (4.6 to 2.5 with no
  mismatch) is the new noise or the random timing, not yet traced. These brains were built by hand on
  exact parts and never asked to survive mismatch; the minimal circuit search's designs, tuned with mismatch and
  varied noise from the start, do survive it, and polished under the new rules they improve (minimal/NOTEBOOK.md,
  M7). The polish shrank every sensor's capacitance (by a third to two thirds) and raised its resistance, keeping its
  time constant on smaller currents: under a fixed noise per node the search had begun making nodes big to drown it;
  now a big node is noisier in absolute terms, so the cheat is gone and the search goes the other way. The
  recruitment series' results
  (`experiments/LEADERBOARD.md`) stand only for the old simulator until they are re-run.
- **What else cost the designed circuit (the night of 2026-10-20; diagnostics with switches the rules forbid, in
  scratch code only).** With no mismatch it fell from 4.6 to 2.5. Putting the body's pulses back on tick boundaries
  changes nothing (2.41 against 2.54): the hand-built neurons never leaned on lockstep. The noise level does: at half
  the noise the creature never moves (no meal in 32 lives), at 0.75 food:poison 1.54, at 1 2.54, at 1.5 1.64, at 2
  0.88. Noise is both its engine (the spontaneous spikes that make it move and search) and its enemy (it blurs which
  colour was seen), so it was tuned to the old noise's pattern across its nodes, and no level of the new one gives
  that back.
- **Mismatch breaks the neurons, not the learning.** With mismatch in one group of parts at a time (64 lives, last
  third food:poison): none 1.70, the neurons' own parts 0.99, synapses 2.05, learning (E, P and their writers) 1.59,
  hush 2.15, taste 2.02. So the neurons alone do the damage. Of 200 standard neurons under 10% mismatch, half fire
  more than 10 times per 1,000 ticks of their own accord, and those that don't miss pulses; moving them further from
  threshold trades one for the other (bias -2.0: 14% fire on their own, 28% of pulses missed; no margin tried gives
  both under 10%). An excitable neuron sits near the point where it starts to oscillate, and 10% mismatch pushes a
  share of them over it.
- **Rate homeostasis restores the rates, not the function** (an experiment, not kept): each neuron given a knob, a
  memory node charged by a steady current and drained by its own spikes, feeding a current back into it, so that it
  settles at its designed rate (sensors 19, motors 45 per 1,000 ticks; the target mismatched like every part). Under
  10% mismatch the rates come back (sensors from 0.1-179 to 12-37, 10th-90th percentile; motors from 0.3-199 to
  31-74), but food:poison barely moves (1.11 against 0.97; sensors only 0.92). A rate can't tell a spike the eye
  caused from one of the neuron's own, so a dull sensor is woken until noise fills its quota. The minimal search's
  winners escape all of this: their sensors are leaky integrators, not spiking relays, so mismatch only rescales them.

## Recruitment, step 0: the baseline (2026-10-18)

The plan (`RECRUITMENT.md`, agreed with the user): keep the one-bit task, start from a brain with no machinery for
telling food from poison, and let it discover in its life that it needs more. The control, agreed too: all-food lives
(`--all-food`), where tastes are never bad and nothing should be recruited.

- **The minimal circuit** (`brains/minimal.py`): the designed circuit's four neurons, each sensor driving both motors
  through a synapse that relays every spike, taste into a node connected to nothing. Both circuit brains now share
  `CircuitBrain` (neurons, taste node, running, drawing); 32 recorded lives were unchanged, every meal and firing.
- **64 lives of 10,000 ticks:**

  | | poison lives: food:poison by third | meals per 1,000 ticks | all-food lives: food per 1,000 ticks by third |
  |---|---|---|---|
  | minimal | 1.0, 1.0, 1.0 | 3.14 (half poison) | 3.09, 3.38, 2.97 |
  | designed circuit, learning | 2.3, 6.4, 5.3 (55 of 64 learned) | 1.66 | 2.17, 2.54, 2.80 |

- **Machinery costs food when there is nothing to learn.** In all-food lives the learner eats a fifth less than the
  minimal circuit: its sensors hush each other, and with p at 1/2 half its sightings become veers. Even in poison lives
  it eats less food (about 1.3 against 1.6 per 1,000 ticks); what it gains is avoiding poison (about 0.3 against 1.6).
  That cost is what makes recruiting machinery only when needed worth anything.
- **Why non-learners score exactly 1.0:** lives are paired, each seed run once with red as poison and once with blue,
  and a brain that ignores taste behaves identically in both, so its food and poison counts mirror exactly.
- **Agreed for step 0.2** (the user): no detector hand-placed where it will be needed (design smuggled in). Instead
  every unit gets the same generic essential variable (Ashby): here, its own disturbance by bad tastes; the unit taste
  enters is generic, merely the one disturbed. Spare units are generic and identical, sparsely or locally connected,
  and connections grow toward a signal the disturbed unit sends out (as the sheet's paths grow toward a sink's
  field), under one rule that knows nothing of roles.

## Recruitment: where the pain goes, and what a unit can ask (2026-10-18)

- **Flooding every unit with "pain" was a ground-rule question.** It wouldn't move credit assignment into the body
  (every unit gets the same signal, saying nothing about which sensor earned it; each unit's own eligibility does the
  credit assignment). But the sheet had ruled a sheet-wide taste "magic", and routed it through the T organ. In real
  brains the broadcast is brain structure: dopamine neurons receive the reward signal and project widely, a fan-out
  that costs wiring and energy and that evolution built. Two options: (A) taste enters at one unit and spreading it
  is the brain's job, grown or recruited at a cost; (B) the starting brain is born with a declared, generic modulator
  projection from the taste unit to every unit (as evolution gave us a dopamine system), costing energy like any
  connection. **Decided (the user): B for now**, declared openly; A is the harder version for later. A third,
  local variant, pain reaching only the sensors (taste sits beside them, as the sheet's T organ does), is under
  discussion below.
- **Three local questions a unit can ask**, each pointing somewhere different:
  1. *Am I involved?* (eligibility): was I active shortly before the pain? A unit that wasn't ignores it. This is
     the standard three-factor rule (a widely spread signal changes only units with a recent activity trace), and
     the designed circuit already learns this way.
  2. *Am I implicated?* Does my activity predict pain, over many events, more than my activity in general does?
  3. *Can I fix it myself?* (frustration): implicated, and adjusting myself doesn't stop it (nothing adjustable,
     or at its limit), so I need help: recruit.

  In the minimal circuit, in a red-poison life: the red sensor is involved and implicated (it was stimulated within
  10 ticks before 85% of red meals, the other sensor before 17%: "What a sensor can know", above) but can change
  nothing, so it is frustrated: recruitment should start there. The motors fire before bad *and* good tastes:
  involved but conflicted, which shows the colours were merged upstream. In all-food lives there is no pain, so
  nothing is implicated, frustrated or recruited.
- **Recruited units as bridges (the user's idea), and the decisions on it.** The poison sensor is reliable but
  powerless: it knows (its activity predicts pain) but cannot act. The motors act but cannot know (they fire before
  good and bad meals alike). A recruited unit is the learnable link between them: a wire with a memory rather than a
  new neuron (in level-0 terms the distinction dissolves), much as NEAT's "add node" splits a connection, but
  triggered by local frustration instead of random mutation. Decided:
  - **pain reaches only the sensors** (taste sits beside them, as the sheet's T organ does), replacing B; so the
    bridge is one-sided: the frustrated sensor's signal travels down its own outputs, the sheet's path growth
    reversed (there the target sent the field; here the source signals, along wiring it already has);
  - **a new, generic unit is created on demand**, placed by the local rule (equivalent to a reserve of spare cells);
  - **a ladder, measured from the bottom:** rung 0, adjust myself (intrinsic) while that still helps; rung 1, recruit
    a bridge when I am reliable but powerless; rung 2, recruit a feature (a conjunction detector) when nothing
    upstream predicts reliably. **Recruit only when self-adjustment is exhausted**: for a simple unit, roughly "my
    knobs are at their best on average, and the pain continues", cascade-correlation's trigger (add a unit when the
    error stops falling) made local; or, with synapses that track their own uncertainty, "confidently settled and
    still implicated".
  - Principles: insert transparently (a new bridge first passes the signal unchanged); exactly one bridge per need
    (the sheet's handshake, or mutual inhibition); hold what was learned when the pain stops (it stopped *because* of
    the bridge).
- **Locality, stated strictly (the user's corrections).**
  - *No coin toss between units.* A unit may draw a random number from its own noise (the sheet's sensors tossing
    for their side happened inside one cell), but a choice *among* units must come out of their local competition;
    nothing may compare them from outside. So recruitment starts at both sensors (the food sensor too was active
    before some poison meals, about 17% of them, against 85% for the poison sensor); the poison sensor's stronger
    evidence most likely forms its bridge first, the pain falls for everyone, and the other's recruitment dies away.
    Likewise between a sensor's two output wires: bridges start on both, noise decides which forms first, and the
    other dies away when the creature starts to veer.
  - *No unit can know it is optimally tuned*: that would need how the creature's success varies with its
    parameters, which no unit has. A unit knows its own activity, the signals on its connections, and pain only if
    pain reaches it. With pain only at the sensors, the motors have no information about success: they can't tune
    for the task, only regulate their own activity (homeostasis) or stay fixed. A unit that feels pain can only
    correlate ("when I was active, pain followed") or perturb a knob and keep changes after which pain falls. So
    "finished adjusting" means *my own adjustment has stalled (a knob at its limit, or a slow trace of its change near
    zero) while my own discomfort persists*: both observable by the unit itself.
  - *Every parameter is declared a constant (fixed at birth, with noise) or a plastic knob with a local rule.* The
    minimal circuit has constants only; rung 0 adds one knob, the sensors' excitability.
  - *Make it the structure*, as `sheet.py` does: each unit's rule sees only its own state, the signals on its own
    connections and what is delivered to it; the engine creates units and connections only when a unit's rule asks,
    attached locally to it; and a test checks that no rule reaches further.
- **De-recruitment (open).** A bridge that is no longer needed costs energy, so it should go, but not merely because
  the pain stopped. Proposed criterion: remove a bridge once it has been *transparent* (passing its signal unchanged,
  as if absent) for a long time; one holding a closed gate keeps a memory, however rarely used. Failed recruits (no
  fall in the frustration that summoned them) go too, as in ultrastability.
- **For later:** pain felt by the motors instead of the sensors. Nothing in the mechanism should depend on which end
  feels it; the bridge would then grow from the other end.

## Recruitment, step 0.2: the net, and rung 0 (2026-10-18; the rule layer withdrawn, below)

The engine and rules described here were programs beside the circuit, withdrawn for that reason ("The rules were not
circuits", below); rung 0 was rebuilt as circuit ("Recruitment, rung 0 rebuilt as circuit"). The findings stand as a
specification of the local signals a circuit needs.


- **Locality made the structure** (`net.py`, as `sheet.py` is for the sheet). A unit is a circuit node with its
  elements; connections are elements between units' nodes. Every unit runs the same compiled rule (`net_rules/`) once
  per world tick, given only its own numbers and spikes, what the body delivered to it, the spikes and messages that
  came along its own connections, and messages sent back; it writes only its own numbers, its messages, and knobs
  that set its own node. The engine hands each unit its connections in a fresh random order every tick, so a rule
  can't learn which is which (the circuit's version of the sheet's means). Messages are clipped to -1..1 and noisy.
  `test_net_rules.py` checks imports, signature, birth values and knobs, and runs each rule with bounds checked on
  random nets (an index past a rule's own arrays fails there: tested).
- **A knob is a memory: its noise comes with writing, not with time.** At first every kept number got noise every
  tick, knobs included; a knob clamped at its top then walked down from it, the motors (never tasted, so never
  written) ended less excitable (bias -1.67 against -1.60), fewer spontaneous kicks explored, and all-food lives ate
  2.27 per 1,000 ticks against the minimal circuit's 3.12. With noise only on writes (10% of the change, as agreed for
  non-volatile memory) the adjusting circuit eats exactly as the minimal circuit where nothing is learned.
- **Slow averages refreshed only at events need a fade.** Updated only at tastes but noised every tick, they
  random-walked in units that never taste; they now fade over 2,000 ticks without evidence.
- **Rung 0** (`brains/adjusting.py`, `net_rules/adjust.py`): every unit's excitability is a knob, moved by
  eligibility x taste; only the sensors feel taste. 64 lives of 10,000 ticks (`python recruit_test.py 64`):

  | | poison lives: food, poison per 1,000 ticks (food:poison) | all-food lives: food per 1,000 ticks |
  |---|---|---|
  | minimal | 1.57, 1.57 (1.0) | 3.1-3.4 |
  | adjusting (rung 0) | 1.48, 0.99 (1.5) | 3.12 |
  | designed circuit, designed learning | about 1.3, 0.3 (5.3 in the last third) | 2.2-2.8 |

  Rung 0 helps (a third less poison) but is far from enough: the case for rung 1.
- **Confidence (the user's "firing confidence")**, implication over involvement, how reliably a unit's activity
  predicts pain (+1) or a good taste (-1), counted only with evidence (5 tastes, involvement above the traces' noise):
  poison's sensor +0.46 on what it received; food's sensor -0.85; in all-food lives the sensors -0.96; the motors
  never taste, so they have no evidence and no confidence. The pattern step 0.2 looked for.
- **Self-adjustment blinds a unit's own-spike evidence.** Lowering its excitability, the poison sensor's own
  involvement fell to 0.04 (within the noise), while its received-input involvement stayed 0.13 with confidence
  +0.46: it still receives what predicts pain, though it no longer fires. Its knob stalled (moving 0.002 per taste)
  at -2.57, short of its limit (-3.0), because the knob moves only while the unit fires; and pain continued (0.99 per
  1,000 ticks). So frustration must be judged on what a unit *receives*, not on what it does, or self-adjustment hides
  the very problem it failed to fix. Frustrated, by that test: the poison sensor; not the food sensor; nothing in
  all-food lives.
- **Decision confidence (the user's comparator idea)**: not what firing leads to, but how decisively the unit decides,
  its inputs against its own threshold. The engine now gives each rule its own node's highest voltage per tick (the
  circuit records it; no arithmetic changes). Two measures, since a spike is all-or-none and only misses show how close
  they came: *firing consistency* (the share of input events that made it fire; near 0 or 1 is decided, near 1/2
  noise decides) and *misses* (for events that didn't fire, how far the voltage peak stayed below threshold, as a
  share of the way from rest; the threshold, the edge of the fast positive feedback at -2.82, is set by the unit's own
  elements, not by the knob, which moves its rest). 64 lives:

  | | fires | decided (\|2 fires - 1\|) | miss | outcome confidence (received) |
  |---|---|---|---|---|
  | poison's sensor | 0.03 | 0.93 | 0.03 (near misses) | +0.44 |
  | food's sensor | 0.69 | 0.37 | 0.26 | -0.83 |
  | motors | 0.94 | 0.89 | 0.30 | no evidence |
  | sensors, all-food lives | 0.68 | 0.36 | 0.25 | -0.99 |

- **The poison sensor stalls exactly at the edge.** Its knob moves only while it fires, and it fires only while a
  stimulus crosses threshold; so it settles where stimuli lift its voltage to just below threshold (rest -4.9, peaks
  near -2.9): firing almost never (decided, by consistency) but with near misses (by the margin). Consistency is the
  better test of whether the knob can still change behaviour (firing can fall no further than 0); the margin shows
  where it sits (a step up would make it fire again). So frustration, by three local conditions: decided (the knob
  can't change what I do), what I receive predicts pain, and the pain goes on: the poison sensor, and nothing else.
- **The rules were not circuits (the user's question).** The net's unit rules (`net_rules/adjust.py`) are compiled
  programs layered on the circuit: per-tick traces, event bookkeeping ("pending", a peak over two ticks, an estimate
  of rest), a hard-coded threshold, and a knob that writes the circuit's bias from outside it. The locality checks
  stopped a rule seeing other units, but inside a unit it was free digital computation: functionality beyond the
  literal circuit, which the mixed-feedback track promises not to have ("everything, learning too, is nodes and
  elements"). It should have been said when the engine was proposed. What stands: the measurements (watching may
  compute anything) and the rung-0 findings as a specification of which local signals are needed; what doesn't: rung
  0's behaviour as a mixed-feedback result. The same kind of mistake as "reward at contact": machinery outside the
  thing being studied doing its work. Rule of thumb: for every number that affects behaviour, ask "which node holds
  it, and which elements move it?"; if the answer is "the program", it isn't the circuit.

## Recruitment, rung 0 rebuilt as circuit (2026-10-18)

- **Decided (the user): in the circuit brains everything is explicit circuit**, so that at any point the whole
  brain can be drawn as a circuit diagram. The rule layer (`net.py`, `net_rules/`) is retired. In a circuit locality
  is built in: a node feels only the elements attached to it. The one exception, for rung 1: *growth*. A recruited
  unit doesn't exist until it is recruited, then appears suddenly, by a declared primitive triggered entirely locally
  (by a node's own voltage) and attached locally.
- **Memory nodes** (`mixed_feedback.py`): no leak, and noise only when written (WRITE, 10% of each change), so a knob
  holds its value exactly while nothing writes it. `test_compiled.py` checks it.
- **Rung 0 in circuit** (`brains/adjusting.py`): every neuron has the same motif, an eligibility node charged by its
  own spikes and a memory node (the knob) driving a current of up to 1.4 out of the neuron (an amplifier whose bias
  current the knob sets: a gated element reading the knob, gated by it); for the sensors only, two amplifiers from the
  taste node into the knob, gated by eligibility (bad charges it, good empties it), as the designed circuit's P.
- **Measurement watches from outside** (`recruit_test.py`): the brain logs what went in and what each neuron did;
  the observer computes the local quantities (involvement, confidence, firing consistency, misses) over the second
  half of each life. 64 lives of 10,000 ticks:

  | | poison lives: food, poison per 1,000 (food:poison) | poison's sensor: excitability, fires, confidence (received), miss | all-food lives: food per 1,000 |
  |---|---|---|---|
  | minimal | 1.57, 1.57 (1.0) | 1.00, 0.70, +0.73, 0.22 | 3.14 |
  | adjusting (circuit) | 1.46, 1.05 (1.4) | 0.34, 0.18, +0.57, 0.03 | 3.15 |

  The rule version's result (1.5) holds in circuit form: rung 0 cuts poison by a third, and the poison sensor again
  stalls at the edge (near misses, miss 0.03). The food sensor stays calm (excitability 0.98, confidence -0.89); in
  all-food lives nothing changes.
- **Rung 0 is itself one-bit learning in a life**, by intrinsic plasticity alone (no synapse changes): the poison
  sensor's knob fills, it becomes less excitable, and the creature stops driving at poison. It learns which colour to
  *ignore*, a weaker thing than the designed circuit's veering *away* (an ignored poison block is still eaten beside
  food or by drift): 1.4 food per poison against about 5. And it costs nothing when there is nothing to learn: in
  all-food lives no knob ever charges and it eats exactly as the minimal circuit, where the designed learner, its
  machinery always on, eats a fifth less. Paying only when there is something to learn is already rung 0's property.
- **Not yet tried: a knob that also makes a unit keener.** The knobs start empty (as excitable as a neuron can be
  without firing by itself, about 0.2 of bias short of that), so good tastes can't push further. A knob starting
  mid-range could move both ways: keener on what tastes good, which might help even in all-food lives.
- **The motors' conflict, seen from outside.** In the minimal circuit the motors are involved before every taste
  (involvement 1.00) with confidence exactly 0.00: equally before good and bad (exactly, as lives are paired). The
  motors can't know this themselves (they feel no taste); the observer can.

## Recruitment: a starting animal that may know but can't act (2026-10-18)

- **A cleaner test (the user's).** In the rung-0 animal each sensor could change its own behaviour (ignore what
  predicts pain), so the starting animal could already learn a little. Instead: the minimal circuit plus a taste
  neuron T that can *learn* what predicts pain but has *no outputs*. It may know, and must recruit in order to act.
  What it learns is a prediction, available before contact, which is what avoiding needs; its frustration is crisp
  ("I predict pain confidently and it still comes"); and one "danger" signal serves any poison colour. The sensors'
  own knobs (rung 0) go; pain reaches only T, the taste organ. Rung 0 stays on record as the earlier variant.
- **The knowing circuit** (`brains/knowing.py`), all circuit: T fires innately at a bad taste (an amplifier from the
  taste node), and through a plastic synapse from each sensor whose strength is a memory node, charged by a bad
  taste and emptied by a good one while that sensor was recently active (the designed circuit's P motif, on the
  sensor-to-T synapses). 64 lives of 10,000 ticks (`python recruit_test.py 64 10000 knowing`):

  | | poison lives | all-food lives |
  |---|---|---|
  | behaviour | food 1.58, poison 1.58 per 1,000 (1.0, as the minimal circuit) | food 3.16 per 1,000 (as the minimal circuit) |
  | T's synapses | from poison's sensor 0.87, from food's 0.13 | 0.00 |
  | T anticipates (a spike within 10 ticks before the taste) | 96% of poison meals; 51% of food meals | (no poison); 19% of meals |
  | T's confidence (when it fired before a meal, the meal was poison) | 0.66 | 0.00 |

  Knowledge leaks nowhere (behaviour as the minimal circuit's). T learns the association, and anticipates nearly every
  poison meal; its false alarms are about chance at its rate (about 50 spikes per 1,000 ticks, against 18 in all-food
  lives, which is its own spontaneous firing): red blocks are often in view on the way to a blue one, so T has become
  a "danger in view" detector, which is arguably the right signal for avoiding. Frustrated by the test (confident,
  pain going on) in poison lives; calm in all-food lives.

## Recruitment, rung 1: growing the link that lets knowledge act (2026-10-18)

The full record, with methods, tables and working, is `experiments/NOTEBOOK.md` (E0-E6); in brief:

- **It works.** The recruiting circuit (`brains/recruiting.py`) starts as the knowing circuit: its taste neuron T learns
  what predicts pain but has no outputs. Circuit only, plus one growth primitive: frustration F at T ("I predicted
  this pain and it came anyway"); help routed back along T's input synapses, only to a sensor whose synapse predicts
  pain and only while frustrated; competing sprouts on each sensor's output synapses; and, when a sprout passes its
  level, a bridge splitting that synapse (a relay held down while T has fired lately, so the creature veers from
  danger). On held-out lives it grows exactly the oracle's structure in 61 of 64 poison lives, nets +1.00 food per
  1,000 ticks over the knowing circuit (oracle at birth +1.15; the gap is only the time before growth, about 1,700
  ticks: a time-matched oracle does no better), and grows nothing in all-food lives, where a built-in bridge costs.
- **Essential**: routing by what each synapse onto T learned (without it, bridges land on the food sensor: veering
  from food); competition among a neuron's sprouts (without it every sprout grows); help as a logical AND (predicts
  pain, and frustrated); a sprouted neuron stays changed (one bridge per neuron). Frustration needs both knowledge and
  unprevented pain, so chance frustration grows nothing.
- **Methods**: oracle structures as ceilings; paired lives with per-node noise streams (`Circuit(streams=True)`):
  before them, two variants of different sizes differed by chance as much as by design; quiet slow nodes (a slow
  integrator's capacitance must grow as the square root of its time, or noise swamps it); held-out lives to confirm
  choices; and every script pinned to the settings it ran.
- **Power, corrected**: by the worst case (every amplifier fully biased) the recruiting circuit seemed to need half the
  designed circuit's static power; by the more physical gated average (a gated amplifier's bias set by its gate) it
  needs about 1.7 times as much, and nearly half of that is the one-bridge-per-neuron inhibitor holding a losing sprout
  at 0 with an ungated, full-strength current for ever. Fix to test: growth closes that sprout's charging gate instead.
  Big currents go with big quiet capacitors (current = C x rate), and gating is what makes them affordable.
- **A bug found and fixed**: `start = moving or ticks` treated a creature that moved at tick 0 as never moving
  (measurement only; no earlier result was affected).
- **The bridge's link to the taste neuron was a non-local shortcut** (the user noticed it looked unconnected in the
  block view): the growth rule attached the bridge's hold to `self.T`, knowledge the circuit didn't have. Replaced
  (E7) by a local hold, charged by the sensor's own spikes gated by its synapse onto T; better as well as more local
  (+0.11 [+0.03, +0.19] net food, pooled over 128 lives; last-third food:poison about 5), because the creature now
  veers only when the poison sensor fires, not at T's false alarms. The growth rule now needs to know only where the
  winning sprout is. Lesson: when a growth or wiring rule names a part ("connect to T"), ask how the circuit itself
  would find it.
- **Found on the way: the neuron is fragile to mismatch.** 5% random error in every gain and bias costs both R3 and
  the designed circuit most of what they learn. All of it comes from the neuron's own fast and slow elements and its
  bias; mismatch in the whole recruitment machinery costs nothing. The neuron cancels two equal elements at rest and
  sits 0.38 V below threshold, so 5% moves its rest by up to 70% of the margin: a precise-parts design, to be
  redesigned for margin.

## Recruitment: a generic recruit that knows nothing (the healing circuit, 2026-10-19)

`brains/healing.py`; the H series in `experiments/NOTEBOOK.md`; `experiments/LEADERBOARD.md`. The user's design: a
frustrated unit grows a recruit that attaches to it and its one-edge neighbours, sees their signals, learns which
connection, treated how, reduces frustration, and if it fails is frustrated itself, so the next recruit reaches one
edge further: "an inflammation/healing response". The recruit knows nothing of what the circuit does: it gets a
menu (inhibit or excite each attached neuron, turn down a synapse) and a local rule for choosing.

- **A recruit that knows nothing matches the guided bridge.** Win-stay lose-shift in circuit (enables that latch,
  pairwise rivalry, tiredness that knocks an option out), listening to everything attached, a menu of inhibiting and
  gating: +1.16 net food per 1,000 ticks against +1.16 for rung 1's guided bridge (held out, paired -0.06 [-0.13,
  +0.03]), choosing "gate the poison eye's synapse to a motor" out of seven options in every life.
- **Judge an option by the share of bad tastes after it, not their rate.** Judged by rates (tiredness fading with
  time), an option was still being switched at tick 70,000-90,000, and anything that made the creature do less looked
  like a cure. Judged by share (tiredness that hardly fades while the option is on, a step up per pain, half a step
  down per good taste), it settles by tick 8,000-13,000 after 3-5 switches, and the last third's food:poison doubles
  (4.4 to 7.0, held out; the guided bridge 3.7). But a share can't judge an option followed by no tastes at all.
- **Choosing is the slow part, not waiting for frustration.** T is frustrated 1,000 ticks into a life. The user's
  idea of recruiting early and learning "in shadow mode" moved nothing measurably: a shadow can learn what to listen to,
  not which action helps, which needs acting. And a shadow gated by the parent's frustration withdraws the recruit as
  soon as its help calms the parent (a fix that undoes itself); commissioning it for good (a memory node) fixes that.
  Passing knowledge forward does help: a recruit whose listening is gated by its parent's own learned memories
  ("inherit") beats one learning from scratch (+0.92 to +1.05).
- **Doing nothing well beats doing something precisely.** Listening to everything attached beat learned listening: R
  then acts constantly, so win-stay lose-shift gets many trials; and for a gating action, firing too often costs
  nothing. The action's target gives the selectivity (the local hold's lesson again). Committing to one option beat
  graded blending (a REINFORCE-like rule kept harmful options on beside good ones: +0.16 at best).
- **Wireheading is real.** Recruits learning from anticipated pain only chose to silence T five times as often:
  recruits must learn from pain itself.
- **The cascade works when the cure is one edge further.** With a menu of the synapses arriving at attached neurons,
  wave 1 (on T and the eyes) can do nothing useful; still frustrated 10,000 ticks later, it is frustrated itself, and
  wave 2, reaching the motors, gates the poison eye's synapse in about 60% of lives. Its failures: a neuron-level
  cure (inhibit a motor while the poison eye fires) is a real veer but costs half the meals (turning needs the motor
  off for 10 ticks, and a shorter hold loses the veer); with full listening it froze the creature; and wave 1's last
  option stays on after wave 2 cures the poison, and then looks good, even when harmful (credit leaking between waves).
  Best so far (+0.66, last third 4.9): every wave frustrated by the first unit's own flag, and "starve" (while an
  option is on its tiredness creeps up, eased only by good tastes, so a freeze is knocked out within 20,000 ticks).
- **De-recruitment by retiring failed in every form.** A recruit frustrated enough to recruit stood down for good;
  but while the pain lasts every recruit reaches that point, the last one too, and then no one acts. What standing
  down should mean (may the last recruit? a cap on waves would be a hidden size) is open; a recruit that walks would
  release its old action as it moves (`RECRUITMENT.md`, future work).
- **Sigmoid tails are constant currents.** Twice: a dozen resting rivals' tails summed past an enable's rise, so none
  ever won; and a pain input's resting tail, cancelled by the good-taste input's while the steps were equal, charged
  tiredness once they weren't. Summed over many inputs or a long time constant, "almost zero" isn't.
- **Power: choosing cost more than acting.** A generic recruit added about 1,200 units of gated static power (the
  guided bridge about 200), most of it the enables' pairwise rivalry: n(n-1) ungated elements, fully biased for ever.
  Gating each latch, rivalry and knock-out element by its own source cut it to about the guided bridge's (gated
  average 550 against 528), with behaviour unchanged. Gate every element by the node whose state it reports.
- **Open: level 1 has no rules (the user's question, 2026-10-20).** Level 0 is strict (nodes and elements only), but
  the parts built from them are invented as needed. A grown healing circuit has 48 nodes and 128 elements, of which 6
  are neurons; the other 42 are about eight unnamed kinds (eligibility trace, weight, pulse, slow level, comparator,
  latch, resting-open gate, hold). The block view draws them all as the same meter, though some are states belonging
  to a neuron or synapse and others are functional units in their own right. And half the recruit (21 nodes, about
  60 elements) is machinery for choosing among 7 options, while its choice of where to connect is trivial: the
  decisions sit inside complicated parts, not in how simple parts connect. A proposal: a small catalogue of level-1
  parts, each with named ports, a glyph and rules for what may connect to what. The parts: a neuron, with its own
  adaptation; a synapse, with its weight, eligibility and an optional gate (presynaptic inhibition); and a modulator,
  a diffuse signal like ouch and yum. The rules, for example: only neurons send spikes, and a weight changes only when
  eligibility and a modulator coincide (three-factor learning). Growth would add only catalogue parts, connected port
  to port. Win-stay lose-shift would become 7 mutually inhibiting neurons whose adaptation is the tiredness
  (winner-take-all with adaptation, the textbook rivalry circuit). The test: rebuild the healing circuit from the
  catalogue and check it still learns, then redraw the block view to match, before a harder test bed makes the
  structural choices real.

## The second body: a square with two forward thrusters (withdrawn 2026-10-17)

Its mouth was its whole front edge, and its kicks were big (PUSH 0.5, TURN 0.08, DRAG 0.2): the ceiling with p
perfect was 1.5 food per poison (about 45-49% poison), whatever the brain. Replaced by the triangle (above).

## The first body (withdrawn)

The first body had a forward thruster at the tail (A) and one at the side that backed and turned it (V), and the
reward came after a chew delay with eyes shut. Its lessons:

- **The body's ceiling.** With balances fixed perfect from birth, poison was still about a third of meals: the learner
  was at the body's limit. Backing and turning swept the mouth over the poison it was avoiding, so the mouth eats only
  what it moves forward into (perfect balances 33%, 29%, 33% by thirds → 31%, 17%, 28%). Longer pulses, body tweaks
  and a 33 × 33 brain made no clear difference.
- **Results by version** (poison's share of meals by thirds of life after moving, 16 lives with learning; no
  learning about 50%):

  | version | learning on |
  |---|---|
  | 18 shared numbers, distance fields, V near a far corner | 32%, 21%, 26% |
  | 20: names that hold, x and y, V halfway down a side | 38%, 23%, 33% |
  | 16: coordinates as distances (magic knowledge, withdrawn), V at the tail corner, straight paths | 45%, 34%, 34% |
  | 18: A one cell again, A and V send distance fields (the exp cheat, withdrawn) | 35%, 39%, 34% (no learning 43%, 47%, 51%) |
  | 27, honest: flags and gradients, -1..1 at 1% noise | 43%, 39%, 42% (no learning 49%, 48%, 54%); balances poison 0.20, food 0.84 |

  V in the far corner (so R's and B's paths are easier to tell apart) doubles the way to V, and the recoil arrives
  later. The individual-neighbour version before this project had 43%, 27%, 24%.
- **Damage, as with the lizard.** A band 7 rows deep across the middle, replaced by new-born ones at tick 4,000, 6
  lives of 6: x and y back within 1.5 columns in 90-180 ticks, names kept (or retaken where the band took one), every
  route carrying pulses again. Damaging the organiser's corner is not fatal in principle (no surviving corner can
  restart the race, but a new-born corner is a pacemaker again); not yet measured.
