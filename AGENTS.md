# Agent notes

The rules, for agents and people alike: how to work here, and the constraints the brain keeps. The quest, the big
picture and what has been learned are in the README; the history behind each rule is in the notebook. Each fact in
this repository lives in one place (below); other files link to it.

## Working

- **Push only when the user says "Push".** Work directly on `main`. On "Push": commit in the foreground, then in one
  background task run the checks (`python test_rules.py`, `python test_world.py`) in a fresh venv built from
  `requirements.txt` alone, on a clean checkout of that commit (a temporary `git worktree`), and push only if they
  pass. Say nothing if all pass; report a failure with its log. (A fresh venv because another may hide a missing
  dependency. No GitHub CI.)
- **Rip up and rewrite**: prefer a cleaner, smaller design to incremental edits that keep legacy structure.
- **Real units, from few axioms** (the user's decision): every quantity in SI, every number that can be derived
  derived from the axioms in `units.py`; a design's own choices stay with the design, in SI. Rates are per 10 s, a
  life lasts 100 s.
- **Each fact in one place**; link, don't copy:

  | what | where |
  |---|---|
  | the rules | this file |
  | the quest, what has been learned (each finding explained for a newcomer), how to run things, the terms | `README.md` (define a new term in its Terms when it first appears in a user-facing document) |
  | the current state ("Where it stands", rewritten as it changes), then the dated history, methods, results and dead ends | `NOTEBOOK.md` |
  | the axioms: units and the tick | `units.py` |
  | open questions, most valuable first | `QUESTIONS.md` |

- **Open questions** (the user's idea, 2026-10-28): a question that occurs mid-quest is parked in `QUESTIONS.md`
  rather than chased; one answered leaves it, its answer in the notebook. With nothing else to do (the user away),
  take the most valuable one.
- **Where findings go.** Record every finding and dead end in the notebook as you go. When one changes the direction
  of the work, add it to the README's "What we've learned": a short heading, then what it means in plain terms a
  newcomer understands, with a link to the notebook. Keep the notebook's "Where it stands" current.
- **Measure, and trace each failure to a cause before fixing it.** **Show a working behaviour live**
  (`python creature.py`) before reporting it.
- **The user is colour-blind**: use colour, never as the only cue (pair it with shape, line style or a label), and no
  hues hard to tell apart, such as red and green (Okabe-Ito).
- **Long runs** share one laptop: one job at a time. Kill processes only by explicit PID, never by a pattern. To pause
  a run, stop (SIGSTOP) only its pool's workers, never a shell or a process the harness waits on. Don't change code a
  running job will import later.

## Ground rules for the brain

The point is a brain that learns in situ, so the brain must do the work.

- **The interface.** The body (`world.py`) and `Life` (`creature.py`) talk to a brain only through sensors 0 and 1,
  motors 0 and 1, and one taste (`stimulate`, `taste`, `step`). Taste is +1 (food) or -1 (poison) for a tick when a
  block touches the mouth, else 0, and never says which sensor it is about. The body draws its wiring (colour to
  sensor, thruster to motor) at random each life, so the brain doesn't know what its organs are for. Never change
  the task's ground rules (what an organ is, what connects to what) without asking the user first.
- **The body must never become part of the solution.** A change that lets the body or world do a job the brain could
  do (credit assignment, choosing which cells learn, timing, filtering) is not a simplification. Say plainly what job
  moves out of the brain before proposing it, and expect no. Ask before adding or changing any body-to-brain signal.
  If the brain stops needing a mechanism after a body change, ask where its work went (`NOTEBOOK.md`: reward at
  contact). Nor is any property of the body (a pulse's length, a thruster's strength) a reference the brain may tune
  itself against: the body should be as variable as the brain (the user, 2026-10-29); a brain tunes itself towards
  better outcomes, not to a setpoint the body supplies.
- **Nor may the simulator.** An optimiser, an agent included, finds anything a design can exploit. So: random timing
  (no lockstep, no inputs only on tick boundaries), noise on everything, nothing carried below the noise; a result
  must hold on fresh seeds.
- **Local only, no god.** A unit knows only its own state and its neighbours' signals. It may draw from its own noise,
  but a choice among units comes from their local competition, never from outside. No unit knows it is optimally
  tuned: "finished" means its own adjustment has stalled while its own discomfort persists.
- **Comparisons are fair.** Brains are compared on the same lives (the same worlds and wirings); a refactor of one
  brain leaves the others' lives unchanged. All-food lives (both colours food) are the control for anything that
  should happen only when there is something to learn.

## The sheet brain (README: The sheet brain)

- Identical cells running one local rule (`rules/`). A cell sees only its own numbers, its neighbours' **mean** of each
  shared number, and its neighbour count; `sheet.py` enforces this and `test_rules.py` checks it.
- **Noise must matter.** Neighbours see each shared number clipped to -1..1 with 1% noise (the user's setting); no
  encoding may squeeze information below the noise or stretch it over orders of magnitude (`NOTEBOOK.md`, The
  engine: the exp(-beta d) cheat). What a cell keeps to itself is not limited.
- **No magic knowledge**: a path finds its target by a signal the target sends out, never by where it should be.
- Few shared numbers (28 now), counted in the README when they change.
- Random asynchronous updates, noise in every number, whole numbers re-rounded at each update.
- No hidden size: no fixed wait, cap or threshold tuned to one sheet; stages hand over when their work is done.
- The body gives inputs to, and takes outputs from, cells by the names they took, and never decides from a
  sheet-wide view (watching may).
