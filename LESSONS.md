# Lessons

What was tried, what worked, what didn't and why, so settled questions aren't reopened. Each finding was traced to a
cause before it was fixed. Each entry gives the lesson, then what the code does now; dead ends are kept because they
are lessons too.

## Principles

- **Local behaviour only, no global god.** No global clock, no broadcast, no harness switching the cells' behaviour.
  The only things from outside are the body's inputs (sensor kicks, taste), delivered to the cells that named
  themselves.
- **No hidden scale.** A cell knows only its own state and its neighbours' averages; never the sheet's size or its
  position in it.
- **Stochastic updates only.** Every cell updates at random times, never in lockstep: lockstep lets rules lean on a
  shared rhythm and makes artefacts (flipping every tick, checkerboard oscillations).
- **Noise must matter.** Neighbours see a shared number as the cell shows it, clipped to -1..1 and with noise of 1%.
  No encoding may squeeze information below the noise or spread it over orders of magnitude. What a cell keeps to
  itself is not limited (counts and timers are whole numbers, re-rounded at each update).
- **Inputs spike.** Sparse kicks, never continuous levels.
- **No magic knowledge.** Every cell learns everything from its neighbours' signals. Above all, a path finds its
  target by a signal the target cell itself sends out, never by where the rule says the target should be.
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
  (the edge midpoints and the centre lie on that cross); it was dropped for this. Fields from one source (A, V) are
  fine.

## Where am I (`rules/organs.py`)

- **The race.** Corners beat as pacemakers at random periods; one reached by another's wave before its own beat
  stands down. Exactly one left in 20 lives of 20, typically by tick 100-500 (worst about 1,100). Traps:
  - with a rest of 4 updates after excitation, waves re-entered and circled (about 600 cells excited at all times),
    and in 4 lives of 10 every corner stood down; a rest of 10 cured it;
  - damage started circling waves (spirals) anyway, which beat faster than V and knocked it out. Each beat now
    carries its number mod 3 (two flags), and a cell takes only the next beat after the last it took: a wave curling
    back, or a stray piece of an older beat, is refused. Alternating two parities wasn't enough: a stray piece of the
    previous beat has the other parity and was still taken, by V too.
- **Labels need their own pulses.** Labels first rode V's waves along the edges. But V's waves sweep each far edge all
  at once (every cell of it is the same distance from V), so a label started at a far corner had only the rest time
  to travel, and reached about 11 cells. Labels now run as their own pulses along the edges, started by V's two
  coin-tossed neighbours at each of V's beats.
- **Labels must expire.** Before the race is decided, a corner that later loses labels the edges; when it stands down,
  edges and corners it labelled get no more pulses and kept the old labels for ever (in 1 life of 8 a far corner held
  an old -1 and never started its +1). A label now lapses after 3 of V's beats with no pulse to renew it.
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
  turning point of the momentum pass for still: one life named A three cells off, and a second A appeared later); a
  named cell keeps its name while its x stays within 0.15 of the place's, and shows 0 on mark so no neighbour takes
  the same name. 12 lives of 12 named by tick 1,270-2,160; in 10 no name ever changed, in 2 one was lost and retaken
  once; A, R and B within 2 cells of where they belong. A slower average for the marks (600 updates) was worse: it
  lagged while x settled.

## Wiring (`rules/wiring.py`)

- **Breadcrumbs are impossible from averages** (a cell remembering which neighbour a wave came from). Instead a cell
  needs its distance to each sink, and which neighbours are one step nearer or farther.
- **The sinks send the distance fields: no magic knowledge.** To save two shared numbers, the wiring once took a
  cell's distance to A to be its row (making A the whole tail edge to fit) and to V the larger of x and y. That built
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

## Learning (`rules/brain.py`)

- **News as a wave.** The news of a kick used to be a min-age field (the withdrawn exp trick). Now a kick starts a wave
  across the sheet, and a sensor that sees news around it after its own has gone by forgets its own kick: of R and
  B, only the more recently kicked keeps a trace. Trap: a sensor still resting from sending its own news ignored the
  other's, so both kept their traces and a bad taste lowered the food's balance too (food ended at 0.83); a sensor
  now notices news whenever its own has gone by (food ended at 0.97).
- **Earlier, with the min-age field** (kept for its lessons): a field ages more slowly than a cell's own count, so
  "news fresher than my kick" fired on a cell's own echo; and one field for both sensors conflated kicks a few
  updates apart.
- **Two factors, honestly.** The balance moves by taste × the cell's recent-input trace; which way it sent its pulse
  doesn't enter. The creature learns what each colour is worth, and its choices follow.
- **Tumbles from R and B** (now and then a pulse to V by themselves), so a creature that sees nothing still searches.

## The creature (`creature.py`)

- **The body's ceiling.** With balances fixed perfect from birth, poison is still about a third of meals: the learner
  is at the body's limit. Backing and turning swept the mouth over the poison it was avoiding, so the mouth eats only
  what it moves forward into (perfect balances 33%, 29%, 33% by thirds → 31%, 17%, 28%). Longer pulses, body tweaks
  and a 33 × 33 brain made no clear difference.
- **Results by version** (poison's share of meals by thirds of life after moving, 32 lives; no learning about 50%):

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
  route carrying pulses again. Damaging V is no longer fatal in principle (any surviving corner can't restart the race,
  but a new-born V corner is a pacemaker again); not yet measured.
