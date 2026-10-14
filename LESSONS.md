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
- **Robust to noise.** Every number gets noise at every update.
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
  UPDATE, adds noise to every number at every update, and builds the sheet from one birth vector (identical bar
  declared noise). The body reaches the sheet only through `cells()`, `give()`, `get()` and `take()`; watching uses
  `view()`, and the experimenter's `damage()` replaces cells with new-born ones. `test_rules.py` checks every rule's
  imports, signature and birth at two sizes, and that no body code reaches inside.
- **A loophole, closed.** The engine once passed a rule its own numbers as a view into the sheet's memory, and
  compiled code doesn't check bounds: a rule indexing past its own numbers would have read its neighbour's. The engine
  now copies into the rule's own small arrays, and `test_rules.py` runs every rule with bounds checking on.
- **Speed.** About a million cell-updates a second on one core for the whole brain: the rules' logs, exps and random
  numbers dominate; the neighbour means are cheap.

## What averages can do

- **Any, all, and the smallest.** A 0/1 flag's mean says "any neighbour" (> 0) or "all" (= 1). If a cell shares
  exp(-beta d), the mean gives the smallest d to within log(count) / beta: -log(mean) / beta is biased up, at most
  that much, when one neighbour holds the minimum; -log(count x mean) / beta down, by log(how many hold it) / beta.
  With whole numbers and rounding, that is exact. The engine applies the encoding (a shared entry `("d", beta)`), so
  the noise is added to d, not to a tiny exp(-beta d). The range is the limit: exp(-700) is about the smallest
  number, so beta x d must stay under 700 (election tags 0..139 at beta 5; ring counts to 466 at beta 1.5).
- **Which way.** A cell that shows 1, 9 or 81 by its distance mod 3 lets each neighbour count, from the sum, how many
  are one step nearer, level or farther (three base-9 digits): which way is downhill, from one shared number. Mod 3
  is enough at any distance because in a settled field neighbours differ by at most one step; while a field is still
  spreading they can differ by more and would be misread, so a source starts its path only once its distance has held
  still.
- **Ties show.** Two neighbours sharing the smallest value make -log(count x mean) / beta come out log 2 / beta off a
  whole number (0.14 at beta 5), so a cell can tell a tie from a single smallest.
- **Under noise in every number, a cell can only remember whole numbers.** A number a rule just keeps random-walks
  (about 0.1 over 10,000 updates at noise 0.001), so tags, counts, timers and the balance are whole numbers re-rounded
  at each update. Two traps: flooring a whole number plus a little negative noise drops it by one (round, don't
  floor), and the minimum of noisy numbers drifts down (round after taking it). The view must round too: flooring
  drew a blotchy checkerboard from exact numbers.

## Where am I (`rules/organs.py`)

- **Election.** Corners (3 neighbours) elect the smallest whole-number tag. The stale counts of corners that lose rise
  away by themselves (count to infinity, bounded because the true counts are finite), so nothing needs to know who
  won. Election ties (two corners with the same tag of 140) would make two origins: about 2% of lives; not handled.
- **Handedness in one shared number.** The origin shows 1 − 2 × the sum of what its neighbours show; the two edge cells
  next to it show minus a tag each, and recognise themselves by seeing a positive sum. With 1 − the sum it failed:
  the two are diagonal neighbours of each other, so each one's sum also held the other's minus-tag, which cancelled
  it (each saw only 1 + its own tag). With the factor 2 each sees 1 + 2 × its own + the other's. (This replaced an
  origin flag and two tag numbers.)
- **Ring counts.** The smaller tag starts count a round the edge, the other count b, each blocking the other's. Each
  edge cell knows a / (a + b), its place round the perimeter, and so its side (a quarter each). Trap: the cell that
  starts count a never sees count b (it is blocked), so didn't know its side; it is the first side by definition.
- **Coordinates from straight edges, not from points.** A checkerboard drawn from steps to two named points came late
  and never formed a grid: square rings round two points don't cross squarely. Steps in from two straight edges do:
  with 8 neighbours, steps from a straight edge are exactly the row. Exact in 8 lives of 8 from about tick 470.
- **Names must stand still before anything is wired to them.** At first every corner thinks it won and starts ring
  counts; the losers' counts take about 300 ticks to rise away, and the places they give drift along the edge (up to
  21 named cells at tick 50), with paths growing towards them. So a cell takes a name only after holding the place for
  80 updates in a row: with 40, a few wrong names held for about 30 ticks; with 80, none in 8 lives, all four standing
  by about tick 510.

## Wiring (`rules/wiring.py`)

- **Breadcrumbs are impossible from averages** (a cell remembering which neighbour a wave came from). Instead a cell
  needs its distance to each sink, and the mod-3 marks tell it which way is downhill.
- **The sinks send the distance fields: no magic knowledge.** To save two shared numbers, the wiring once took a
  cell's distance to A to be its row (making A the whole tail edge to fit) and to V the larger of x and y. That built
  into the rule where the organs were meant to be: the paths would have grown to the same places with no A or V
  there. It broke the first principle, and it changed what A was (the whole edge, not a cell) without saying so. Now
  each sink, once named, sends out its own distance field, and the paths follow it.
- **A handshake, not a chance.** Cells below a tip joining at random made fans, not paths (about 300 path cells for
  two routes of 48). Now the cells below a tip offer random whole numbers, the tip shows the smallest it sees, and
  only that cell joins. Trap: a cell kept its offer after the tip moved on, so a cell level with the new tip won and
  never joined, and growth stopped; offers now stand only while the cell is right below a tip.
- **Forks, three causes, each traced in a recorded growth** (a path cell with two path neighbours one step nearer
  passes each pulse down both, so pulses arrived 2 to 5 times):
  - tied offers (1 in 99 per pair): the tip now sees the tie and asks again;
  - a race: the tip switched to a smaller offer while its first choice was joining, and got both; a tip now keeps its
    choice for 6 updates;
  - paths passing: a cell joining one path sat just below another's, giving it a second way on. Forbidding such cells
    to offer stalled paths (in half the lives B never reached V); now they offer from the highest band, so are chosen
    only when nothing else offers.

  That brought duplicates down from about 1 life in 2 to 1 send in 64; now, down the distance fields, none in 320.
- **Straight paths, withdrawn.** Picking among the cells below at random makes paths wander a few cells over 48 rows.
  A version had the tip show its x and y mod 3, and the cell on the straight way to the target offered lower: but
  "straight at the target" used where the target was meant to be (magic knowledge again), so it went with the
  coordinate distances. Paths now wander a little, and R's and B's paths to A sometimes join before A; pulses still
  arrive once each.
- **Fading and pulses.** A path cell with no path neighbour one step farther leaves, so paths from passing names, or
  cut off by damage, fade. A pulse is carried for 6 of the carrier's updates; the next cell must update at least once
  meanwhile. Carried for 3, a pulse was lost about half the time over 48 steps. Carried for 6 it is a race the next
  cell almost always wins at update 0.9 (every pulse arrived exactly once, 320 of 320 sends in 8 lives, about 54
  ticks); at 0.5 it loses it often enough that about 1 pulse in 10 dies over 48 steps (traced cell by cell). So the
  wiring test runs at the creature's 0.9.

## Learning (`rules/brain.py`)

- **Lateral inhibition from averages: compare news only with news, and watch for it getting fresher.** Each step was a
  trace to a cause.
  - A min-age news field ages more slowly than a cell's own count since its kick, because a neighbour that hasn't
    updated lately holds an older, fresher-looking value. So "news fresher than my kick" fired on a cell's own echo,
    and the eaten colour's trace was gone at most tastes.
  - Keeping news in fractions of an update froze the field: a uniform field can only age as fast as news travels.
  - What is exact: without a new kick, no cell's news ever gets fresher, whatever order the cells update in. So a
    fall in a cell's news means a new kick elsewhere, and echoes can't cause one.
  - One field for both sensors conflated kicks a few updates apart. One field per sensor, and a cell forgets its kick
    when the other's news falls to fresher than its own kick: the eaten colour alone keeps its trace at almost every
    meal.
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
  | 18: A one cell again, A and V send distance fields, no straight-path rule | 35%, 39%, 34% (no learning 43%, 47%, 51%) |

  V in the far corner (so R's and B's paths are easier to tell apart) doubles the way to V, and the recoil arrives
  later. The individual-neighbour version before this project had 43%, 27%, 24%.
- **Damage, as with the lizard.** Cells replaced by new-born ones relearn their coordinates within about 30 ticks
  (about 200 when the damage takes A or V, which must hold its name again); paths cut off from their source fade and
  regrow down the distance fields; every route carries pulses again within about 500 ticks (a band 7 rows deep across
  the middle, 6 lives of 6). But damaging the corner that won the election kills the frame (6 lives of 8):
  every cell remembers the smallest tag it has heard, so the dead winner's tag lives on with no corner to own it. A
  self-healing election needs stale tags to die out (a tag's age, rising with no source, as the ring counts do): a
  17th shared number, or a cap that assumes a size. Open.
