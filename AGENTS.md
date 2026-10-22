# Agent notes

When changing the code, prefer a rip-up-and-rewrite to a cleaner, smaller design over incremental edits that keep
legacy structure. Work directly on `main`. Commit and push only when the user says "Push".

Before pushing, run the three checks, `python test_rules.py` (the sheet brain's golden rules), `python
test_compiled.py` (the compiled simulation against its plain equations) and `python -m minimal.test_minimal` (the
minimal circuit search's rules), in a fresh venv built from
`requirements.txt` alone: another environment may have extra packages that hide a missing dependency (numba's `@`
needs scipy, which isn't required, so a push once failed). There is no GitHub CI (it only repeated the first two, slowly).
Never make the user wait: on "Push", commit, then in one background task run the checks on a clean checkout of that
commit (a temporary `git worktree`, so foreground edits can't leak into the test) and push only if they pass. Say
nothing more if all passes; report only a failure, with its log.

The user is colour-blind: use colour, but never as the only cue (pair it with shape, line style or a label), and
avoid hues that are hard to tell apart, such as red and green (a colour-blind-safe palette, e.g. Okabe-Ito).

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
fresh seeds. For an optimised circuit, also limits on time constants and gains against the step. Details in
`LESSONS.md` (Principles; Simulating the designed circuit; Noise as biology makes it).

**Circuit noise is biology's, and the simulator's alone** (`mixed_feedback.py`, the user's decision, 2026-10-20):
shot noise on every device current (gross, not net), membrane noise in proportion to each capacitance (none on a
memory node, whose noise is its writers' shot noise), 10% mismatch in every part (also parts grown in a life), and
the body's pulses at random moments within a tick (each eye a Poisson process). All of it lives in the one
integration step every simulation calls (`_step`) and in how the arrays are built, with no switch to turn it off: the
noise can only be scaled within half to double. Never add a way round it (a brain-level noise setting, a second
integrator, parameters edited after the arrays are built), and keep `python test_compiled.py` checking that it is
the same at any step and can't be dodged.

Brains: the **sheet brain** (`brains/sheet.py`, the grid of cells, below) and the **circuit brains**, built from
mixed-feedback parts (`mixed_feedback.py`, sharing `brains/circuit.py`): the **designed circuit** (`brains/designed.py`,
drawn by `schematic.py`: redraw it when the circuit changes), kept for comparison; and the recruitment series, the
**baseline**, **adjusting**, **knowing**, **recruiting** and **healing circuits** and the **healing cascade**
(`RECRUITMENT.md`; experiments in `experiments/NOTEBOOK.md`, ranked in `experiments/LEADERBOARD.md`). Terms coined
along the way are defined in the README (Terms); define any new one there when it first appears in a user-facing
document. The circuit brains keep: no
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
  memory node, noisy only when written (rough by the square root of what is written).

## The minimal circuit search (`minimal/`, its notebook `minimal/NOTEBOOK.md`)

How simple can a circuit be that learns the bit, with no architectural constraints (no neurons, locality or growth)?
The task, body and interface stay as for every brain. The rules, each enforced in software (`minimal/spec.py`:
`check` refuses an illegal circuit, so none can be built or lived; `python -m minimal.test_minimal` tests it):

- **Within the supply**: every node is held within the rails (+-3 V); a clamp inside them is a part.
- **Not faster than the step**: nothing may move a node more than 10 V per circuit tick (0.5 V per integration
  step), whether an element (gain / C), a leak (1 / RC) or the body's pulse into an input (3 / C); and an unfiltered
  element on its own node acts no faster than gain x slope / C = 2 per circuit tick (a time constant of at least 10
  steps: a device fed back to itself must not be infinitely fast).
- **Judged honestly**: held-out seeds, at the nominal noise with the simulator's mismatch (both above: no circuit
  can change them), and a finer step in the real `creature.Life`; paired lives (red, then blue, as poison, on one
  seed), so a circuit that ignores taste scores below 0. (Until 2026-10-20 also at half and double the old fixed
  noise; with noise modelled on biology, the user settled on the nominal level alone.) Starving is counted life by
  life and third by third, and the job allows at most 5% of lives stranded (no food in the last third): summed over
  all lives, a fifth of the winners' lives spinning on the spot for ever went unseen (the user found it live).
- **Moving costs, in meals** (the user's decision, 2026-10-21: a low-energy brain is no use if it drives the body
  wastefully): a thruster firing costs `spec.THRUST` (0.002) of a meal, and the circuit's power `spec.ENERGY` (0.001)
  per unit, so that today's circuits spend about a hundredth on thinking of what they spend on moving (R = 100, fixed,
  not tied to any circuit). Both are guesses, to adjust; `search.py --thrust` tries another price.
- **Counted plainly**: parts are capacitors, resistors, diodes and transistors (a gated element two, a filtered input
  a resistor and capacitor more); power is what each device dissipates, its current times the voltage across it.
- **Three objectives, never traded** (the user's, 2026-10-22), each among circuits doing the job: the simplest
  brain (parts); the best driver for energy (efficiency: meals gained, food less `spec.COST` a poison, per meal
  spent resting, `spec.NEED` per 1,000 ticks, moving and thinking, so that both haste and dawdling cost); and the
  best for speed and accuracy (gain rate: meals gained per 1,000 ticks, energy free). The league
  (`minimal/LEAGUE.md`) names the best at each; the open search keeps all three as objectives, doing the job a
  constraint (the score leads circuits that don't towards it); `search.py` and `prune.py --by efficiency|gain`
  polish and prune for one (default the score), so a part kept for speed isn't pruned for its cost. Thrift (food
  per firing) is shown, not ranked.
- **Match the brain's speed to the body's**: a far block gives about one eye pulse as the gaze sweeps it, so a
  brain must hold its course for some ticks after a sighting (`LESSONS.md`). Starts for a search should include
  designs that do (the hold-and-roam circuit, HR), or it stays among circuits that react too briefly.
- **Sure, or within noise**: the league shows every measure with its 95% interval (a bootstrap over seeds, each
  seed's pair of lives together; stranding a Wilson interval) and compares designs paired on the same seeds: one is
  above another only if the interval of the difference excludes 0, else they are tied, and a design does the job
  surely only if every interval is within the limits. Claim no order the league marks as tied.

An experiment may declare **Sepulchre's rules** in a spec (`rules: "mixed"`): every node leaky except memory nodes, no
clamps. Sepulchre is silent on learning and non-volatile storage, so our gates and memory nodes (floating gates) stay
allowed under his rules (the user's decision, 2026-10-21; `MIXED_FEEDBACK.md`). `--noises 0.5 1 2` judges a polish,
pruning or open search across the noise range, the worst level counting.

Every polish (`minimal/search.py`) ends with pruning (`minimal/prune.py`): the polish tunes values and can't remove
a part, so parts that stopped mattering stay (one winner carried 7) unless something tries taking each away.

Add a rule to `check` and a case to the test whenever one is added here.

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
