# Agent notes

When changing the code, prefer a rip-up-and-rewrite to a cleaner, smaller design over incremental edits that keep
legacy structure. Work directly on `main`. Commit and push only when the user says "Push".

Before pushing, run the CI steps (`.github/workflows/test.yml`) in a fresh venv built from `requirements.txt` alone:
another environment may have extra packages that hide a missing dependency (numba's `@` needs scipy, which isn't
required, so a push once failed). After pushing, check the run passed (`gh run list`, `gh run view --log-failed`).
Never make the user wait for either: on "Push", commit, then do the rest in one background task: run the CI steps
on a clean checkout of that commit (a temporary `git worktree`, so foreground edits can't leak into the test), push
only if they pass, then wait for the GitHub run. Say nothing more if all passes; report only a failure, with its
log.

The user is colour-blind: views in greys, no cue by colour alone.

## Brains

The body (`world.py`) and `Life` (`creature.py`) talk to a brain only through sensors 0, 1, motors 0, 1 and one taste
(`stimulate`, `taste`, `step`). Taste is +1 (food) or -1 (poison) for a tick when a block touches the mouth, else 0,
and never says which sensor it is about.

**The body must never become part of the solution.** The project's point is a brain that learns in situ. Any change
that lets the body or world do a job the brain could do (credit assignment, choosing which cells learn, timing,
filtering) is not a simplification, however much brain code it deletes. Say plainly what job moves out of the
brain before proposing it, and expect the answer to be no. Ask before adding or changing any body-to-brain signal.
This went wrong once: "reward at contact" gave the reward to the eaten colour's sensor, presented as a
simplification. It moved credit assignment into the body, and it stood until the user found it (see `LESSONS.md`).
A rule of thumb: if the brain stops needing some mechanism after a body change, ask where that mechanism's work went.

**Nor may the simulator become part of the solution.** Anything a design can exploit in the simulation, an
optimiser will find, an agent included: asked to cut the channels between cells, an agent once packed several into
different bits of one float. So for every brain: random timing (never lockstep, and no inputs only on tick
boundaries), noise on everything, nothing carried below the noise, and a result must hold at a finer step and on
fresh seeds. For an optimised circuit, also mismatch (parameters a few percent off at birth) and limits on time
constants and gains against the step. Details in `LESSONS.md` (Principles; Simulating the mixed-signal brain, now the designed circuit).

Brains: the **sheet brain** (`brains/sheet.py`, the grid of cells, below) and the **circuit brains**, built from
mixed-feedback parts (`mixed_feedback.py`, sharing `brains/circuit.py`): the **designed circuit** (`brains/designed.py`,
drawn by `schematic.py`: redraw it when the circuit changes), kept for comparison; and the recruitment series, the
**minimal**, **adjusting**, **knowing** and **recruiting circuits** (`RECRUITMENT.md`). The circuit brains keep: no
knowledge of what a sensor senses or a motor does, noise on every node, continuous time, and learning only through the
taste. `--measure` compares brains on the same lives; a refactor of one must leave the others' lives unchanged.
All-food lives (`--all-food`) are recruitment's control.

## Circuit brains (recruitment: `RECRUITMENT.md`)

- **Everything that affects behaviour is explicit circuit**: nodes and elements (`mixed_feedback.py`), so the whole
  brain can always be drawn as a circuit diagram. No program beside the circuit: for every number that affects
  behaviour, ask "which node holds it, and which elements move it?" The only exception (the user's decision) is
  growth: a recruited unit appears suddenly, by a declared primitive triggered by a node's own voltage and attached
  locally. Watching and measuring may compute anything, but never feed back.
- No coin toss between units: a choice among units comes from their local competition. No unit knows it is optimally
  tuned; "finished adjusting" means its own adjustment has stalled while its own discomfort persists. A knob is a
  memory node, noisy only when written.

## The rules of the sheet brain (see the README)

- A sheet of identical cells running one local rule (`rules/`). A cell sees only its own numbers, its neighbours'
  **mean** of each shared number, and its neighbour count. `sheet.py` enforces this; keep it so, and keep
  `python test_rules.py` passing.
- **Noise must matter.** Neighbours see each shared number as the cell shows it: clipped to -1..1, with noise of 1%
  added to what is shown (the user's setting), and the engine encodes nothing. No encoding may squeeze information
  below the noise or stretch it over many orders of magnitude. An earlier version had the engine show exp(-beta d)
  with the noise added to d first, so the tiny number shown was in effect noise-free and the mean gave the
  neighbours' smallest d: a cheat, withdrawn. What a cell keeps to itself is not limited, though simplicity is wanted.
- No magic knowledge: everything a cell knows comes from its neighbours' signals. A path finds its target by a
  signal the target cell itself sends out, never by where the rule says the target should be.
- Keep the shared numbers few (28 now, nearly all flags; the lizard used 16) and count them in the README when
  they change.
- Never change the task's ground rules (what an organ is, what connects to what) without asking the user first and
  saying so plainly.
- Random asynchronous updates and noise in every number; whole numbers re-rounded at each update for anything kept.
- No hidden size: no fixed wait, cap or threshold tuned to one sheet; stages hand over when their work is done.
- The body (`creature.py`) only gives inputs to, and takes outputs from, cells by the names they took; it never
  decides anything from a sheet-wide view (watching and measuring may).
- Measure, trace each failure to a cause before fixing it, and record findings and dead ends in `LESSONS.md`. Show
  a working behaviour live (`python creature.py`) before reporting it.
