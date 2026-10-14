# nca-learn: a brain that builds itself from averages, then learns

A sheet of identical cells, each born the same bar random noise, each running one local rule, and each seeing
nothing of its neighbours but the **average** of each number they share. Like the "lizard" of
[Growing Neural Cellular Automata](https://distill.pub/2020/growing-ca/) (Mordvintsev et al., Distill 2020), it
builds something from nothing and repairs itself when damaged. But it doesn't grow a picture. It grows a nervous
system: it works out where it is, names its organs, wires its sensors to its thrusters, and then the creature it
drives learns, within its own lifetime, which of two colours is food.

![A life: the brain (left) builds a coordinate frame, names its organs and grows its wiring, then the creature
(right) learns to avoid the poison](media/life.gif)

Nothing in the cells is told which colour is poison, where it is in the sheet, or how big the sheet is. No clock, no
global signal, no lockstep: cells update at random, with noise in every number.

## Quick start

Needs Python 3.10 or later.

```bash
git clone https://github.com/pilgrimbeart/nca-learn.git
cd nca-learn
python3 -m venv .venv              # Windows: python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python creature.py                 # watch a life
```

Once the environment is active, `python` is its Python. In a new terminal, activate it again first. On Ubuntu, if
`python3 -m venv` says ensurepip is missing: `sudo apt install python3-venv`.

Each run starts with a pause of a few seconds while numba compiles the rules.

In the live view:

| key | |
|---|---|
| `r` | a new life (a new seed; poison alternates red and blue) |
| `d` | damage the brain: replace a disc of cells under the mouse with new-born ones |
| space | pause |
| up / down | faster / slower (takes over from the automatic speed; `r` hands it back) |
| Esc | quit |

### What you're seeing

- **Left, the brain** (49 × 49 cells), in greys:
  - a faint **checkerboard**: the coordinates each cell has worked out for itself, in squares of 4 cells;
  - its organs, lettered: **R** and **B** (the red and blue sensors, with each one's balance, its learned chance
    of approaching what it sees), **A** (the middle of the tail edge: forward thrust) and **V** (the tail's corner: back off and
    turn);
  - **paths**: light grey from R and B to A, mid grey to V; **pulses** running down them, white;
  - a fading **red glow** (also brighter) as news of a kick to R or B spreads.
- **Right, the world:** red blocks (dark, lettered R) and blue blocks (light, lettered B), and the creature, a
  square with its head marked. A ring at the tail or the side shows a thruster firing. "yuck!" is a poison meal.
- **Below:** the tick, the stage of life, which colour is poison this life, and the recent meals.

The view runs at 10 ticks a frame, but slows to 1 while the paths grow and until a little after the creature starts
moving, so the pulses can be seen running down them. A life goes: "where am I" (to about tick 510), "wiring" (to
about tick 950), then "moving and learning". Within a few thousand ticks the poison sensor's balance falls towards 0
and the creature mostly backs away from poison.

## Other commands

```bash
python creature.py --seed 3         # a particular life
python creature.py --measure 16     # 16 lives with learning, 16 without, headless: how much poison it eats
python test_rules.py                # check every rule keeps the rules below
python watch.py organs              # one stage on its own (organs, wiring; --show picks the numbers drawn)
python organs_test.py               # when the coordinates and names come right, life by life
python wiring_test.py               # pulses sent from R and B: how many arrive, and how soon
python creature.py --record frames  # save a life's frames as PNGs, headless (media/life.gif is --seed 1 --ticks 4000)
```

## The rules can't be broken by accident

- **`sheet.py` is the only code that knows there is a grid.** A rule (`rules/*.py`) declares its numbers, which of
  them its neighbours can see, and what every cell is born with, and one compiled function
  `update(me, mean, count, inp, out)`. It is given its own numbers, its neighbours' **mean** of each shared number,
  how many neighbours it has, and what the body delivered: nothing else. Not its position, the size, a clock, or any
  neighbour on its own.
- **A rule never holds a view into the sheet.** The engine copies a cell's numbers and its neighbours' means into the
  rule's own small arrays, and `test_rules.py` runs every rule with array bounds checked, so an index past the end
  can't reach another cell's numbers.
- **The engine does the rest.** Each tick each cell updates with some chance, never all at once. Every number gets a
  little noise at every update. Every cell is born from one birth vector, identical bar declared noise.
- **The body touches the brain only at cells, by the names they gave themselves:** `cells()`, `give()`, `get()`,
  `take()`. Only the cells named R and B get sensory input (and the taste); only A and V are read. Watching uses
  `view()`; the experimenter's `damage()` replaces cells with new-born ones. `test_rules.py` checks every rule's
  imports, signature and birth, and that no body code reaches inside.
- Numba-compiled: about a million cell-updates a second on one core for the whole brain (about 375 ticks a second at
  49 × 49).

## Averages are enough

- **Any and all.** A cell that shares a 0/1 flag tells its neighbours "any of you" (mean > 0) or "all" (mean = 1).
- **The smallest.** A cell that shares exp(-5 d) (the engine does this for a shared `("d", 5)`) lets its neighbours
  find the smallest d among them from the mean, to within log 8 / 5 < 1/2: rounded, it is exact. So cells can count
  steps and elect.
- **Which way.** In a settled distance field (each cell one more than its neighbours' smallest, a whole number), a
  neighbour is always one step nearer, level, or one step farther. A cell that shows 1, 9 or 81 by its distance mod 3
  lets each neighbour count, from the sum, how many of them are each (three base-9 digits). Mod 3 is enough because
  it only has to tell -1, 0 and +1 apart, at any distance. It does rely on the field having settled: while one is
  still spreading, a neighbour two steps away would be misread.
- **Whole numbers.** With noise in every number at every update, a cell can only remember whole numbers, re-rounded at
  each update. So tags, counts, timers and even the balance (in twentieths) are whole numbers.

## What happens in a life

The rules are layered: `rules/brain.py` runs `rules/wiring.py`, which runs `rules/organs.py`.

1. **Where am I** (`rules/organs.py`).
   - **Election.** The four corners know they are corners: they have three neighbours. They elect an origin: the
     smallest random tag wins.
   - **Handedness.** The origin's two edge neighbours pick a direction round the edge (the one with the smaller of two
     more random tags goes first).
   - **Ring counts.** Edge cells count steps round the edge both ways, so each knows its place round the perimeter,
     and so its side.
   - **Coordinates.** One side counts rows in, the next columns: every cell gets x and y (with 8 neighbours, steps from
     a straight edge are exactly the row).
   - **Organs.** The first side is the tail: the cell in its middle names itself A, and its corner, V. Two cells in the
     middle of the far side, the head, 6 apart, name themselves R and B. A cell takes a name only once it has held it
     for 80 updates in a row: at first every corner thinks it won, and the losers' counts take a while to rise away,
     giving places that drift. So nothing is wired until the organs stand still.
2. **Wiring** (`rules/wiring.py`).
   - **Signals from the sinks.** Once A and V have named themselves, each sends out a distance field: it shows 0, and
     every other cell one more than the smallest of its neighbours'. Nothing in the wiring knows where A and V are:
     the paths follow the fields, so if A or V named itself somewhere else, the paths would grow there.
   - **Growth.** R and B start a path down each field once their distance has held still for 20 updates. The end of a
     path (a tip) asks its neighbours one step nearer for offers, each a random whole number; it shows the smallest
     offer it sees, and that cell joins. So a path grows one cell at a time, downhill, until it reaches A (or V). Paths
     wander a little, and R's and B's paths to A sometimes join before they reach it. Three refinements, each traced
     from a fault:
     - if two cells share the smallest offer, the tip sees it (the mean comes out a little off a whole number) and
       asks again;
     - a tip keeps its choice for a few updates, so it can't change its mind while the chosen cell joins, and get two;
     - a cell that would also touch another path offers a bigger number, so it is chosen only if no other cell offers.
   - **Fading.** A path cell with no path neighbour one step farther leaves, so a path cut off from its source fades
     and its source grows a new one.
   - **Pulses.** A pulse runs down a path, from a cell to its neighbour one step nearer, and A (or V) counts the pulses
     it takes: the body fires that thruster.
3. **Choosing** (`rules/brain.py`). When a sensor kicks R or B, that cell sends a pulse towards A (forward, at what
   it sees) with chance b, its balance; otherwise towards V (back off and turn). Born b = 0.9, so a new-born creature
   is drawn to anything it sees. R and B also send towards V now and then by themselves: a tumble, so it searches.
4. **Learning, in R and B only** (`rules/brain.py`).
   - **The trace.** A kicked cell keeps how many updates since its kick.
   - **News.** Every cell keeps the news of each sensor: how old the freshest kick of R it has heard of is, and of B.
     A cell's news never gets fresher unless there was a new kick, whatever order the cells update in. So when R's
     news of B gets fresher than R's own kick, B has been kicked since, and R forgets its own kick (and likewise B).
     Of R and B, only the more recently kicked keeps a trace.
   - **A meal** kicks the eaten colour's cell once (its flavour), and the creature chews with its eyes shut, so the
     news has time to cross.
   - **The taste** (delivered to R and B) then moves b by taste × exp(-trace / 30), towards 0 or 1. So the change
     needs a recent input (the trace, sharpened by the news) and the taste; it doesn't depend on which way the cell
     sent its pulse. Strictly that is two factors, a stimulus trace and a reward, not the three of a three-factor rule
     (pre, post, reward): the creature learns what each colour is worth, and its choices follow from that. A bad taste
     also makes R and B send towards V for a while: the creature recoils.
   - All other cells only build and carry: frame, paths, pulses, news.

No stage waits a fixed time: each starts when the one before has produced what it needs.

## The numbers a cell shares

18, all seen only as averages over the neighbours (the lizard used 16: getting there honestly is the next step):
- where am I: 6 (the election, handedness, two ring counts, x and y);
- wiring: 5 for each of the two channels (distance, path, tip, pulse, offer);
- learning: 2 (news of R, news of B).

## Result

Poison's share of meals in each third of life after the creature starts moving: 32 lives of 8,000 ticks, half with
red as poison and half with blue (`python creature.py --measure 16`).

|  | first third | second | last | balance at the end |
|---|---|---|---|---|
| learning on | 35% | 39% | 34% | poison 0.19, food 0.97 |
| learning off | 43% | 47% | 51% | both 0.90 |

Most of the learning happens within the first third: a creature usually eats each colour within its first few
meals. With learning it also eats less (376 meals against 592), as it backs away from the poison more often.

The balances come out right; the behaviour is at the body's limit. With balances fixed perfect from birth, poison is
still about a third of meals (37%, 29%, 30%; 16 lives, measured with the previous wiring). Mostly that's because both colours are often in view at once:
food drives the creature forward into the poison. It also acts on old news: a pulse takes about 55 ticks to cross the
brain.

## Damage

Press `d` in the live view to replace a disc of cells under the mouse with new-born ones, as with the lizard. The new
cells relearn their coordinates from their neighbours within about 30 ticks (about 200 if the damage took A or V,
whose new cell must hold its name for 80 updates again); a path cut off from its source fades and regrows down the
distance fields, and every route carries pulses again within about 500 ticks (a band 7 rows deep across the middle,
6 lives of 6). Damage R or B and the
new cell takes the name again, but what the old one had learned is gone. Damage the corner that won the election and
the frame dies (6 lives of 8): every cell remembers the smallest tag it has heard, so the dead winner's tag lives on
with no corner to own it, and no corner wins again. Not yet handled.

## Not yet

- It is tuned for a 49 × 49 sheet only; the rules are meant to work at any size, but haven't been tested beyond it.
- Election ties (two corners with the same tag, about 2% of lives) would make two origins.
- Damaging the winning corner kills the frame (above).
- The starvation trap: a creature that learns to avoid everything stops eating.

## Files

| | |
|---|---|
| `creature.py` | the body, the world, the live view and the measurement |
| `sheet.py` | the engine: the only code that knows the grid |
| `rules/organs.py` | where am I: election, handedness, ring counts, coordinates, names |
| `rules/wiring.py` | growing paths and running pulses, built on `rules/organs.py` |
| `rules/brain.py` | choosing and learning, built on `rules/wiring.py` |
| `test_rules.py` | checks every rule and every body file keep the rules |
| `watch.py`, `organs_test.py`, `wiring_test.py` | each stage on its own, live or measured |
| `LESSONS.md` | how it got here: what was tried, what failed and why |

## Licence

MIT: see `LICENSE`.
