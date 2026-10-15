# Agent notes

When changing the code, prefer a rip-up-and-rewrite to a cleaner, smaller design over incremental edits that keep
legacy structure. Work directly on `main`. Commit and push only when the user says "Push".

The user is colour-blind: views in greys, no cue by colour alone.

## The rules (see the README)

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
- Keep the shared numbers few (27 now, nearly all flags; the lizard used 16) and count them in the README when
  they change.
- Never change the task's ground rules (what an organ is, what connects to what) without asking the user first and
  saying so plainly.
- Random asynchronous updates and noise in every number; whole numbers re-rounded at each update for anything kept.
- No hidden size: no fixed wait, cap or threshold tuned to one sheet; stages hand over when their work is done.
- The body (`creature.py`) only gives inputs to, and takes outputs from, cells by the names they took; it never
  decides anything from a sheet-wide view (watching and measuring may).
- Measure, trace each failure to a cause before fixing it, and record findings and dead ends in `LESSONS.md`. Show
  a working behaviour live (`python creature.py`) before reporting it.
