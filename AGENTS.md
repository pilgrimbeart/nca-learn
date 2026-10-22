# Agent notes

This is an open-ended exploration, learning by doing: brains that build themselves and learn one bit in their life
(README). This file holds the rules, for agents and people alike; each fact in this repository lives in one place
(below), and other files link to it.

## Working

- **Push only when the user says "Push".** Work directly on `main`. On "Push": commit in the foreground, then in one
  background task run the three checks, `python test_rules.py` (the sheet brain's rules), `python test_compiled.py`
  (the compiled simulation against its plain equations, and that its noise can't be dodged) and `python -m
  minimal.test_minimal` (the minimal circuit search's rules), in a fresh venv built from `requirements.txt` alone, on
  a clean checkout of that commit (a temporary `git worktree`, so foreground edits can't leak in), and push only if
  they pass. Say nothing if all pass; report a failure with its log. (A fresh venv because another environment may
  hide a missing dependency: numba's `@` needs scipy, which isn't required, and a push once failed. No GitHub CI: it
  only repeated the checks, slowly.)
- **Rip up and rewrite**: prefer a cleaner, smaller design to incremental edits that keep legacy structure.
- **Each fact in one place**; link, don't copy:

  | what | where |
  |---|---|
  | the rules (principles, honesty, every brain's constraints) | this file |
  | an overview, how to run things, and the terms coined along the way | `README.md` (Terms: define a new term there when it first appears in a user-facing document) |
  | the noise model | `mixed_feedback.py`'s docstring |
  | lessons that cut across the project | `LESSONS.md` |
  | each line of work's history, methods and results | the sheet brain: `LESSONS.md`'s part on it; recruitment: `experiments/NOTEBOOK.md`; the minimal search: `minimal/NOTEBOOK.md` |
  | rankings | `experiments/LEADERBOARD.md`, `minimal/LEAGUE.md` (generated) |
  | background reading | `MIXED_FEEDBACK.md`, `RECRUITMENT.md` |

- **Measure, trace each failure to a cause before fixing it, and record findings and dead ends** (dead ends are
  lessons too). **Show a working behaviour live** (`python creature.py`) before reporting it: watching a life has
  found what no table did.
- **The user is colour-blind**: use colour, but never as the only cue (pair it with shape, line style or a label), and
  avoid hues that are hard to tell apart, such as red and green (a colour-blind-safe palette, e.g. Okabe-Ito).
- **Long runs**, which share one laptop: one job at a time (more workers than cores gain nothing). Kill processes only
  by explicit PID, never by a pattern (`pkill -f`) that may match your own command. To pause a run, stop (SIGSTOP)
  only its pool's worker processes, never a shell or a process the harness waits on: stopping a queue's shell once got
  the whole queue killed. Don't change code that a running job will import later: a polish imports the pruning code
  at its end, and once crashed on a name added meanwhile.

## Ground rules for every brain

The project's point is a brain that learns in situ, so the brain must do the work.

- **The interface.** The body (`world.py`) and `Life` (`creature.py`) talk to a brain only through sensors 0 and 1,
  motors 0 and 1, and one taste (`stimulate`, `taste`, `step`). Taste is +1 (food) or -1 (poison) for a tick when a
  block touches the mouth, else 0, and never says which sensor it is about. The brain doesn't know what its organs are
  for: the body draws its wiring (colour to sensor, thruster to motor) at random each life, so approaching and
  avoiding are behaviour, not concepts in the brain. Never change the task's ground rules (what an organ is, what
  connects to what) without asking the user first and saying so plainly.
- **The body must never become part of the solution.** Any change that lets the body or world do a job the brain
  could do (credit assignment, choosing which cells learn, timing, filtering) is not a simplification, however much
  brain code it deletes. Say plainly what job moves out of the brain before proposing it, and expect the answer to be
  no. Ask before adding or changing any body-to-brain signal. Rule of thumb: if the brain stops needing some mechanism
  after a body change, ask where that mechanism's work went. (It went wrong once: "reward at contact", `LESSONS.md`.)
- **Nor may the simulator.** Anything a design can exploit in the simulation, an optimiser will find, an agent
  included: asked to cut the channels between cells, an agent once packed several into different bits of one float.
  So for every brain: random timing (never lockstep, no inputs only on tick boundaries), noise on everything, nothing
  carried below the noise, and a result must hold at a finer step and on fresh seeds; for an optimised circuit, also
  limits on time constants and gains against the step (the minimal search's rules, below).
- **Circuit noise is biology's, and the simulator's alone** (the user's decision, 2026-10-20): shot noise, membrane
  noise, mismatch and pulses at random moments, as `mixed_feedback.py`'s docstring specifies. All of it lives in the
  one integration step every simulation calls (`_step`) and in how the arrays are built, with no switch to turn it
  off: it can only be scaled within half to double. Never add a way round it (a brain-level noise setting, a second
  integrator, parameters edited after the arrays are built), and keep `test_compiled.py` checking that it is the same
  at any step and can't be dodged.
- **Local only, no god.** Everything a unit knows comes from its own state and its neighbours' signals. A unit may draw
  from its own noise (a cell tossing for its side), but a choice *among* units must come from their local
  competition, never from outside. No unit knows it is optimally tuned: "finished adjusting" means its own adjustment
  has stalled while its own discomfort persists.
- **Comparisons are fair.** `--measure` compares brains on the same lives (the same worlds and wirings); a refactor of
  one brain must leave the others' lives unchanged. All-food lives (`--all-food`, both colours food) are the control
  for anything that should happen only when there is something to learn.

## The sheet brain (README: The sheet brain)

- A sheet of identical cells running one local rule (`rules/`). A cell sees only its own numbers, its neighbours'
  **mean** of each shared number, and its neighbour count. `sheet.py` enforces this; keep it so, and keep
  `test_rules.py` passing.
- **Noise must matter.** Neighbours see each shared number as the cell shows it: clipped to -1..1, with noise of 1%
  (the user's setting), and the engine encodes nothing. No encoding may squeeze information below the noise or
  stretch it over many orders of magnitude (the exp(-beta d) cheat, `LESSONS.md`). What a cell keeps to itself is not
  limited, though simplicity is wanted.
- **No magic knowledge**: a path finds its target by a signal the target cell itself sends out, never by where the
  rule says the target should be.
- Keep the shared numbers few (28 now, nearly all flags) and count them in the README when they change.
- Random asynchronous updates and noise in every number; whole numbers re-rounded at each update for anything kept.
- No hidden size: no fixed wait, cap or threshold tuned to one sheet; stages hand over when their work is done.
- The body only gives inputs to, and takes outputs from, cells by the names they took; it never decides anything from
  a sheet-wide view (watching and measuring may).

## The circuit brains (README: The circuit brains)

- **Everything that affects behaviour is explicit circuit**: nodes and elements (`mixed_feedback.py`), so the whole
  brain can always be drawn as a circuit diagram. No program beside the circuit: for every number that affects
  behaviour, ask "which node holds it, and which elements move it?" The one exception (the user's decision) is
  growth: a recruited unit appears suddenly, by a declared primitive triggered by a node's own voltage, attached
  locally. Watching and measuring may compute anything, but never feed back.
- A knob is a memory node, noisy only when written.
- No knowledge of what a sensor senses or a motor does, continuous time, and learning only through the taste.
- The designed circuit is drawn by `schematic.py`: redraw it when the circuit changes.

## The minimal circuit search (README: The minimal circuit search; `minimal/NOTEBOOK.md`)

How simple can a circuit be that learns the bit, and how well can a circuit drive the body, with no architectural
constraints (no neurons, locality or growth)? The task, body and interface stay as for every brain. Every rule is
enforced in software (`minimal/spec.py`: `check` refuses an illegal circuit, so none can be built or lived; `python -m
minimal.test_minimal` tests it); add a rule to `check` and a case to the test whenever one is added here.

- **Within the supply**: every node is held within the rails (+-3 V); a clamp inside them is a part.
- **Not faster than the step**: nothing may move a node more than 10 V per circuit tick (0.5 V per integration
  step), whether an element (gain / C), a leak (1 / RC) or the body's pulse into an input (3 / C); and an unfiltered
  element on its own node acts no faster than gain x slope / C = 2 per circuit tick (a time constant of at least 10
  steps: a device fed back to itself must not be infinitely fast).
- **Judged honestly**: on seeds the search never saw, with the simulator's mismatch, at half, nominal and double
  noise, the worst level counting and the job required at every level (the user's decision, 2026-10-22: judged at
  one level, pruning traded mechanism for noise); every polish, pruning and open search judges the same way. Lives
  are paired (red, then blue, as poison, on one seed), so a circuit that ignores taste scores below 0. A design must
  also hold in the real `creature.Life` at a finer step (`minimal/check.py`).
- **The job**: at least 1 food per 1,000 ticks, food:poison at least 3 in the last third of a 10,000-tick life, and
  at most 5% of lives stranded (no food in the last third); the score charges starving life by life and third by
  third (`spec.py`), so failing lives can't hide among the rest.
- **Moving and thinking cost, in meals** (the user's decision, 2026-10-21: a low-energy brain is no use if it drives
  the body wastefully): a thruster firing `spec.THRUST` (0.002) of a meal, and the circuit's power `spec.ENERGY`
  (0.001) per unit, so that today's circuits spend about a hundredth on thinking of what they spend on moving. Both
  are guesses, to adjust; `search.py --thrust` tries another price.
- **Counted plainly**: parts are capacitors, resistors, diodes and transistors (a gated element two, a filtered input
  a resistor and capacitor more); power is what each device dissipates, its current times the voltage across it.
- **Three objectives, never traded** (the user's, 2026-10-22), each among circuits doing the job: the simplest brain
  (parts), the best driver for energy (efficiency) and the best for speed and accuracy (gain rate) (README, Terms).
  The league names the best at each; the open search keeps all three, doing the job a constraint (the score leads
  circuits that don't towards it); `search.py` and `prune.py --by efficiency|gain` polish and prune for one (default
  the score).
- **Sure, or within noise**: every measure with its 95% interval (a bootstrap over seeds, each seed's pair of lives
  together; stranding a Wilson interval); designs compared paired on the same seeds, one above another only if the
  interval of the difference excludes 0, else tied; the job done surely only if every interval is within its limits.
  Claim no order the league marks as tied.
- **Every polish ends with pruning** (`minimal/prune.py`): the polish tunes values and can't remove a part, so parts
  that stopped mattering stay unless something tries taking each away.
- **Sepulchre's rules**, for an experiment that declares them (`rules: "mixed"` in a spec): every node leaky except
  memory nodes, no clamps; our gates and memory nodes (floating gates) stay allowed, since Sepulchre is silent on
  learning and non-volatile storage (the user's decision, 2026-10-21).
- **Starts matter**: a search only refines what its starts can reach; include designs of every kind that works
  (`LESSONS.md`: match the brain's speed to the body's).
