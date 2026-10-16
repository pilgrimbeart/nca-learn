# Lessons

What was tried, what worked, what didn't and why, so settled questions aren't reopened. Each finding was traced to a
cause before it was fixed. Each entry gives the lesson, then what the code does now; dead ends are kept because they
are lessons too.

## Principles

- **Local behaviour only, no global god.** No global clock, no broadcast, no harness switching the cells' behaviour.
  The only things from outside are the body's inputs (a sensor's stimulus, and food or poison), delivered to the
  cells that named themselves.
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
- **Reward at contact (the user's simplification).** The chew delay with eyes shut, the flavour stimulus on eating,
  the news wave and the trace were all there to credit the reward to the eaten colour's sensor when both sensors got
  it. Now the body gives the reward only to the eaten colour's sensor, as the block touches the mouth: a sensor's two
  inputs are what it senses and food or poison. The rule: p moves a quarter of the way to 1 or 0 (now half: see
  scoring); 26 shared numbers. Don't build features into the body or world to make learning easy. 16 lives of
  8,000: poison's share 50%, 47%, 43%; firing both at the end, poison 0.09, food 0.91: as good as with
  the trace and news, with much less. Ceiling with p perfect: 48%, 42%, 47%.

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
