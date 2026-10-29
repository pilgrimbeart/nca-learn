# Open questions

What we'd like to know and haven't tested, roughly most valuable first. A question raised mid-quest is parked here
rather than chased; one answered leaves, its answer recorded in its line's notebook. Each: the question, who raised it
and when, why it matters, the line it belongs to, and the experiment that would answer it.

## Discrete circuits (`discrete/NOTEBOOK.md`)

- **Can a brain adapt its reflexes to its body?** (the user, 2026-10-28; the body left as it is, 2026-10-29: learning
  a lopsided body likely takes more than a life, and better eyes) Open: with each thruster
  0.5 to 2 (`bodies.THRUSTERS`), the best fixed design (B) falls from 2.38 to 0.32, 11% stranded (D13). First the best
  fixed design searched on such bodies (robust judge); then a brain that tunes itself in its life (its drive's
  balance between thrusters, its rates), each unit from its own signals; the gap between them prices adaptation.
  Since (D13): the oracle (told its body, the drive balanced) gets 1.92 held out, the best fixed design 0.76; tried
  and short of it: extremum seeking (about 0.5), re-find time as a sign, sightings per firing, sweeping back. Next
  ideas: the extremum seeker with a better reward (the pulse rate rising as it nears); given three lives' time it
  only reaches 0.8 (D13), so the signal, not the time, is short. A zigzag within the drive failed (an eye's corridor
  shows nothing of a block's place within it).
- **B's drive starts cleanly, in transistors** (D13; only when B's physical realism matters): the second thruster
  fires alone at a drive's first beat in over half the drives, costing about 20% of its score in SPICE; a latch on
  the beat halved it, but motor A still misses some first beats (its starved inverter, which also drives the
  oscillator, is the suspect).
- **The same task at Sepulchre's level** (the user, 2026-10-28): once the transistor-level design is concluded, repeat
  it with Sepulchre's blocks, and compare the low-level components.
- **Which blocks are good to design with, and at what scale** (the user, 2026-10-28): sub-Sepulchre (gates,
  flip-flops), Sepulchre (a fast bistable with a slow leaky integrator), or super-Sepulchre; so far the pair does
  every job (D13).
- High-value resistors (500 MOhm to 1 GOhm) are rarely better than 5% and leak across a board's surface: the bipolar
  circuits' 1% (`life.TOL`) was optimistic.

## Every brain

- **How much could a clever brain gain?** (the user, 2026-10-28) A ladder of ceilings on the same lives, each a policy
  in Python (a second a life or so): omniscient (knows every block and its own body: the absolute ceiling); a mapping
  brain (legal inputs only, but unlimited memory and thought: it learns its body, integrates its own path from what it
  fired, takes a bearing from its heading and a range from the pulse rate at each sighting, keeps a map and plans);
  short memory (where it last saw food: object persistence, below); the best reactive policy (2.3-2.7); our circuits.
  The gaps price each ability in meals, so they say which are worth a brain's cost, and which small circuit (a ring
  attractor for heading, as in insects' path integration) would capture most of it. Done: the omniscient rung, a
  crude one, about efficiency 20 and 58 food per 10 s (`discrete/NOTEBOOK.md`, D13): ten times B. Next the mapping
  rung. A short memory (the heading where food was last seen) is worse than none: a heading without a range rarely
  points at the block (D13); learning the colour costs B only 0.15 against being told it. The seer (a perfect map of
  what it has seen) gets 4.5: intelligence is worth at most about twice B here, the rest (to 20) is the eyes' coverage.
  Open: a mapper that infers places from pulses (ranging by moving) to see how much of the 2x a real brain reaches.

## The minimal search (`minimal/NOTEBOOK.md`)

- **Object persistence** (the user): a creature that has just lost sight of food sweeps back for it (the body can
  turn both ways); the bottom rung of the ladder above.
- **Reversal**: every minimal circuit learns only from food, so none unlearns when the poison colour swaps. The
  discrete line's B (doubt a bounded tally) reverses well (D13): its doubt could go into a minimal design.
- **A smaller robust circuit still**: the open search again, from HR_31p_pol_pruned.
- **Sepulchre's discipline**: do circuits of mixed-feedback components (every node leaky, events from positive
  feedback) do the job as simply? The first three-arm experiment settled nothing (`MIXED_FEEDBACK.md`): it needs a
  start built of his components.

## Recruitment (`experiments/NOTEBOOK.md`)

- **Recruitment under biological noise**, on a neuron that survives mismatch; de-recruitment (retiring a recruit
  failed in every form, H11); a recruit that walks (`RECRUITMENT.md`).
- **Level 1 has no rules** (the user, 2026-10-20): the parts built from nodes and elements are invented as needed,
  about eight unnamed kinds (`experiments/NOTEBOOK.md`).

## The sheet brain (`NOTEBOOK.md`)

- **Back to the sheet**: cellular automata again, with what the circuits have taught. Every unit a fast bistable and a
  slow integrator, each slow variable outlasting the loop it closes, each tuning its own time constant from its own
  signals (D13): the project's real goal, self-optimisation from local signals.
