# Lab notebook: rung 1 of recruitment

*Run under the simulator before 2026-10-20 (a fixed noise per node, no mismatch): the results stand only for it
(`NOTEBOOK.md`, Noise as biology makes it). Older entries keep the names they were written with (`NOTEBOOK.md`, the
opening); the printed results in `results/` call the baseline circuit "minimal".*

## Where it stands

- **A brain can grow, in its life and by local means, the link that lets its knowledge act** (rung 1, E1-E7): the
  recruiting circuit grows exactly the structure an oracle would place in about 62 of 64 poison lives, and nothing in
  all-food lives.
- **A recruit that knows nothing of the circuit can find that link too** (the H series): the healing circuit chooses
  from a menu of actions by win-stay lose-shift and matched the guided bridge; when the first recruit can't reach the
  cure, a cascade grows a second one step further out (best: +0.66 net food over the knowing circuit, H11).
- **All of it under the earlier noise.** Under noise and mismatch as biology makes them, these hand-built neurons fire
  on their own or miss pulses, and every circuit brain falls to about 1 food for each poison: the results stand only
  for the earlier simulator until the brains are rebuilt on a neuron that survives mismatch.
- Open questions: `QUESTIONS.md`.

Rung 1 (RECRUITMENT.md): the knowing circuit (brains/knowing.py) learns what predicts pain in its taste neuron T, but T
has no outputs. Can it grow, in its life and by local means only, the link that lets that knowledge change behaviour?
Everything is circuit (mixed_feedback.py) except growth, the one declared primitive (brains/recruiting.py).

Conventions. A condition is 64 lives of 10,000 ticks: 32 seeds, each run once with red and once with blue as
poison, and the same 64 in all-food lives. Food:poison is pooled over lives, with a bootstrap 95% interval over
lives. Comparisons between variants are *paired*: the same seeds and, with per-node noise streams (below), the same
noise, so a difference is caused by the variant; the measure is net food (food minus poison) per 1,000 ticks after
the creature starts moving. Scripts: `python -m experiments.e<N>_...`; raw records in experiments/results/.

## Plan

| exp | question | method |
|---|---|---|
| E1 | If recruitment produced the ideal structure, which is best? | Oracle: hand-place candidate structures at birth |
| E2 | Can a circuit signal "my predictions don't prevent pain" honestly? | The frustration node F, in poison and all-food lives, with and without the timing guard, with learning off |
| E3 | Does local growth produce the best E1 structure? | Full mechanism: F, help routed by what T learned, competing sprouts, growth |
| E4 | Which parts matter? | Ablations: no routing, no competition, other thresholds, no guard |
| E5 | How does it compare? | Grown in life against oracle against designed circuit; both starting animals; cost |

## E0: infrastructure, and three findings on the way (2026-10-18)

- **Growth during a life** (mixed_feedback.py: `redirect`, `grow`): new nodes and elements join a running circuit
  keeping every existing state; a new node starts at its start voltage or where its leak alone would rest it.
  test_compiled.py: splitting a synapse with a relay keeps the state, and the relay passes spikes (44 target spikes
  after, 42 before).
- **Slow nodes must be quiet nodes.** First version: F (fading over 3,000 ticks) with C = 10 rose to 0.93 in an
  all-food life, and bridges grew there. Cause: every node gets the same noise current, so a node integrating over
  tau circuit ticks wanders by about 0.2 sqrt(tau / 2) / C in steady state: about 1.5 for F, against a range of 0..1,
  and the clamp at 0 turns the walk into a drift upward. A slow integrator needs a capacitance that grows as the square
  root of its time; each slow node now gets the C that holds its wander near 0.02 (F: C = 775), with R and its input
  gains scaled to keep its time and rates. Physics, not tuning: the same disease as the knobs' drift (below: Before E0), cured
  differently because F must fade.
- **Frustration's trigger moved off the noise.** The taste node's own noise (about 0.1) sometimes dipped toward the
  "bad taste" threshold (-0.5), and F integrated those leaks over thousands of ticks (F about 0.08 in all-food lives);
  the threshold for F is now -0.8 (a bad taste takes the node to about -1.3).
- **Common random numbers.** The recruiting circuit with growth off ate 3.49 food per 1,000 ticks in all-food lives
  against the baseline circuit's 3.14, intervals not overlapping, though its extra nodes have no outputs. Paired by seed,
  the difference was +0.34 with a standard deviation of 1.00: paired lives were uncorrelated, because all nodes drew
  noise from one stream and adding nodes reshuffled the sensors' and motors' noise. The noise stream, not the seed,
  decides a life. Fix: each node draws from its own stream, seeded by its index (`Circuit(streams=True)`, used by the
  recruitment brains; the sheet brain and the designed circuit keep theirs, so their lives are unchanged). Then the
  baseline, knowing and recruiting-without-growth brains live *identical* lives (paired difference 0.00, standard
  deviation 0.00): nothing in the extra circuitry leaks into behaviour, and the +0.34 was chance. Lessons: at 64 lives
  two independent noise streams differ by about 0.15 food per 1,000 ticks by chance alone (the baseline circuit's own
  figure moved from 3.14 to 3.02 with the change of stream), so unpaired comparisons of different brains are weak; with
  common random numbers, variants are compared life for life.

## E1: oracle structures (2026-10-18)

*Question.* If recruitment produced the ideal structure, which structure is it? *Method.* Each candidate placed by
hand at birth by an oracle that knows the poison colour (recruitment never will), the rest as the knowing circuit.
`python -m experiments.e1_oracle 64`; results/e1.txt.

| structure | food:poison [95%] | last third | net food vs knowing, poison lives | all-food lives |
|---|---|---|---|---|
| none (knowing) | 1.00 [0.92, 1.09] | 1.00 | | |
| O1: a bridge on one of the poison sensor's synapses | 2.87 [2.63, 3.14] | 3.47 | +1.07 [+0.93, +1.22] | -0.19 [-0.42, +0.03] |
| O2: a bridge on one of the food sensor's synapses | 0.33 [0.28, 0.39] | 0.20 | -0.99 [-1.17, -0.82] | -0.16 [-0.37, +0.06] |
| O3: bridges on both of the poison sensor's synapses | 1.85 [1.71, 1.99] | 2.12 | +0.78 [+0.61, +0.94] | +0.30 [+0.10, +0.50] |
| O4: bridges on all four synapses | 1.69 [1.52, 1.87] | 2.08 | +0.55 [+0.39, +0.71] | +0.30 [+0.10, +0.51] |
| O5: T's hold inhibits one motor (colour-agnostic) | 1.63 [1.41, 1.88] | 1.78 | +0.23 [+0.08, +0.39] | -1.28 [-1.49, -1.09] |
| designed circuit, for reference | 4.18 [3.78, 4.64] | 5.32 | +1.02 [+0.86, +1.18] | -0.52 [-0.76, -0.28] |

*Findings.* (1) O1 is the target: one bridge, on the poison sensor, on one of its two motor synapses, nets as much
food as the designed circuit (+1.07 against +1.02; intervals overlap), with a lower ratio (2.9 against 4.2) because it
keeps eating more food; its cost in all-food lives is not significant. (2) Placement is critical: the same bridge on
the food sensor (O2) is a disaster, veering from food whenever danger is in view; routing help by what each synapse
onto T learned is essential, not a refinement. (3) Competition matters: both of the poison sensor's synapses (O3,
what growth without competition tends to give) make it ignore rather than veer, 0.3 less net food than O1. (4) The
colour-agnostic design (O5) fails: T fires often (danger in view, and its own spontaneous spikes), and holding a motor
down each time cripples movement (-1.28 in all-food lives). (5) Confound: each bridge is a neuron with spontaneous
spikes of its own; several add exploratory kicks, the likely reason O3 and O4 eat more in all-food lives (+0.30).
Comparisons across numbers of bridges must keep this in mind.

*Conclusion.* Recruitment should aim for O1. Its ingredients: frustration at T, help routed back by W, and
competition between a sensor's sprouts.

## E2: frustration (2026-10-18)

*Question.* Does the frustration node F signal "my predictions don't prevent pain", and only that? *Method.* Growth
off; F sampled every 100 ticks; help while F > 0.5; and the first sprout that reached the growth level (what would
have grown). Four conditions at the first settings (rise per unprevented pain 0.1): the timing guard (a slow element
from T to its eligibility, meant to keep T's innate answer to a taste out of F) on or off, and T able to learn or not.
`python -m experiments.e2_frustration 64`; results/e2.txt.

| condition | F at 1,000 / 3,000 / 10,000 ticks | lives with F > 0.5 | help while F > 0.5, poison / food sensor | first sprout to reach growth |
|---|---|---|---|---|
| A guard, learning | 0.04 / 0.14 / 0.24 | 3 of 64 | 0.72 / 0.06 | poison's, in 11 lives |
| B no guard, learning | 0.04 / 0.15 / 0.26 | 11 of 64 | 0.83 / 0.22 | poison's, in 19 lives |
| C guard, no learning | 0.02 / 0.06 / 0.07 | 0 | | none |
| D no guard, no learning | 0.02 / 0.06 / 0.08 | 0 | | none |
| all-food lives, every condition | 0.01 / 0.01 / 0.02 | 0 | | none |

*Findings.* (1) F is honest: calm in all-food lives, low when T can't learn. (2) The guard is unneeded (C = D: T's
innate answer comes too late to count anyway) and costs genuine anticipation (3 frustrated lives against 11): dropped.
(3) Routing works: help reaches the poison sensor (0.72 against 0.06), and every sprout that reached growth was the
poison sensor's (30 of 30). (4) F is too weak. Working: F settles where its rise per unprevented pain x the rate of
poison meals (about 1.5 per 1,000 ticks) x its fading time (3,000) balances the fade, about 0.45 x T's eligibility at
the pain, so 0.2 to 0.25 (measured 0.24), against a threshold of 0.5. With a rise of 0.3 it settles near 0.7; and
once a bridge cuts poison to O1's rate (0.57 per 1,000) near 0.25, below threshold, so help stops by itself.

*E2b, recalibrated* (rise 0.3, no guard; `--second`; results/e2b.txt):

| condition | F at 1,000 / 3,000 / 10,000 | lives with F > 0.5 | help, poison / food | first sprout to reach growth |
|---|---|---|---|---|
| E learning | 0.12 / 0.42 / 0.66 | 64 of 64 (median first at 3,450) | 0.95 / 0.26 | poison's, in 63 lives (all that reached it) |
| F no learning | 0.06 / 0.16 / 0.22 | 12 of 64 | 0.02 / 0.02 | none |
| all-food lives | 0.01 / 0.01 / 0.02 | 0 | | none |

*Findings.* Frustrated in every poison life, never in all-food lives; growth would start on the poison sensor in
every life. With T unable to learn, F still passes 0.5 in 12 lives at this gain: chance coincidence of T's background
spikes with bad tastes (the floor was the same with and without the guard in E2, so not its innate answer). Harmless:
help is gated by what T learned, so it stays at 0.02 and nothing grows. Growth needs both frustration and knowledge,
two independent conditions: a robust design.

## E3: growth (2026-10-18)

*Question.* Does the full local mechanism (frustration at T; help routed back along T's inputs in proportion to what
each synapse learned; competing sprouts on each sensor's output synapses; growth) grow O1, and nothing in all-food
lives? *Method.* Paired with the knowing circuit (growth off) and the oracle O1. `python -m experiments.e3_growth 64`;
results/e3.txt.

| | food:poison [95%] | last third | net food vs knowing, poison lives | all-food lives |
|---|---|---|---|---|
| knowing (no growth) | 1.00 [0.92, 1.09] | 1.00 | | |
| oracle O1 | 2.87 [2.63, 3.14] | 3.47 [2.85, 4.28] | +1.07 [+0.93, +1.22] | -0.19 [-0.42, +0.03] |
| recruiting | 1.92 [1.73, 2.12] | 3.29 [2.50, 4.47] | +0.69 [+0.55, +0.84] | +0.00 (nothing grew) |

Bridges per poison life: exactly one, on the poison sensor (O1) 44; two on the poison sensor (O3-like) 6; one on
each sensor 10; two on poison and one on food 3; none 1. First bridge at a median of 3,307 ticks, always on the poison
sensor. Recruiting against the oracle: -0.38 [-0.55, -0.22].

*Findings.* Local growth works: in 63 of 64 poison lives a bridge grew, the first always on the poison sensor; by the
last third food:poison is indistinguishable from the oracle's (3.29 against 3.47); in all-food lives nothing grew, at
no cost. The shortfall against the oracle has two causes: the bridge comes at about tick 3,300 rather than at birth,
and 19 lives grew extra bridges. *Diagnosis of the extras.* (a) On the food sensor (13): routing is proportional (the
food sensor still gets about a quarter of the help: 0.26 in E2b), and F fades slowly, so help flows long after the
first bridge until the food sensor's sprout crosses. Wanted: a logical AND, help only to a sensor that predicts pain
and only while frustrated. (b) A second bridge on the poison sensor (9): competition holds only while the winning
sprout stays charged; after help stops it fades, its sibling is no longer held down, and if frustration returns the
sibling grows. Wanted: a sprouted neuron is changed, so it doesn't sprout again.

## E4: ablations and improvements (2026-10-18)

*Question.* Which parts matter, and do E3's two fixes close the gap to the oracle? *Method.* Sharp routing (help only
to a sensor whose synapse onto T is past 1/2, and only while a "frustrated" flag node is on: a logical AND); one
bridge per neuron (a bridge brings a memory node that keeps its neuron's other sprouts down); each alone and both;
and two ablations of the E3 design. `python -m experiments.e4_variants 64`; results/e4.txt.

| variant | lives with exactly O1 | food-sensor bridges | doubles on poison | first bridge (median tick) | food:poison, last third [95%] | net vs knowing | vs oracle O1 |
|---|---|---|---|---|---|---|---|
| R0 (E3) | 44 | 13 | 9 | 3,307 | 3.29 [2.50, 4.47] | +0.69 | -0.38 [-0.55, -0.22] |
| A1 no routing | 0 | 68 | 6 | 3,299 | 2.10 [1.52, 2.88] | +0.23 | -0.84 [-0.97, -0.72] |
| A2 no competition | 0 | 72 | 63 | 3,300 | 1.85 [1.51, 2.26] | +0.43 | -0.64 [-0.77, -0.52] |
| R1 sharp routing | 47 | 5 | 16 | 2,460 | 3.09 [2.60, 3.79] | +0.87 | -0.20 [-0.35, -0.06] |
| R2 one bridge per neuron | 52 | 11 | 0 | 3,307 | 3.90 [3.02, 5.01] | +0.71 | -0.36 [-0.52, -0.20] |
| R3 sharp + one per neuron | 62 | 2 | 0 | 2,460 | 3.92 [3.30, 4.79] | +0.93 [+0.79, +1.08] | -0.14 [-0.28, -0.00] |

No variant grew anything in all-food lives, and none cost anything there (+0.00).

*Findings.* (1) Routing and competition are both essential: without routing growth is blind (half the bridges on the
food sensor; +0.23); without competition every sprout grows (all four bridges in 36 lives; +0.43). (2) The two fixes
are complementary: sharp routing cuts food-sensor bridges (13 to 5) and brings growth earlier (2,460 against 3,307)
but leaves doubles; one bridge per neuron removes the doubles but leaves the food-sensor bridges. Together (R3) 62 of
64 lives grow exactly the oracle's structure, and the last third (3.92) matches the oracle's (3.47; intervals
overlap). (3) R3 nearly closes the gap to a hand-placed bridge (-0.14, interval just reaching 0); hypothesis: what is
left is the time before growth (the oracle's bridge is there from birth). Tested in E5.

## E5: decomposition, sensitivity, mismatch, cost (2026-10-18)

`python -m experiments.e5_analysis 64 [a] [b] [c] [d] [e]`; results/e5ad.txt, e5bc.txt, e5c.txt, e5e.txt. R3 as in E4.

*(a) Is R3's shortfall only the time before growth?* A time-matched oracle places O1 by hand at the very tick R3 grew
its bridge in the same life (same motor); a from-birth oracle at tick 1.

| comparison (net food per 1,000 ticks, paired) | difference [95%] |
|---|---|
| R3 against the time-matched oracle | +0.01 [-0.12, +0.14] |
| time-matched against from-birth oracle | -0.19 [-0.32, -0.06] |
| R3 against the from-birth oracle | -0.18 [-0.31, -0.04] |

Local growth places the bridge as well as an oracle placing it at the same moment; the whole remaining gap is the
time before growth. Hypothesis confirmed.

*(b) Sensitivity* (R3 with one setting changed; 64 lives):

| setting | lives with exactly O1 | first bridge (median tick) | net vs knowing | bridges in all-food lives |
|---|---|---|---|---|
| frustration rise 0.2 | 59 | 3,491 | +0.75 [+0.61, +0.89] | 0 |
| 0.3 (R3) | 62 | 2,460 | +0.93 [+0.79, +1.08] | 0 |
| 0.5 | 63 | 1,956 | +0.97 [+0.82, +1.11] | 0 |
| 0.8 | 61 | 1,758 | +0.96 [+0.81, +1.12] | 0 |
| growth level 0.6 | 64 | 2,447 | +0.98 [+0.84, +1.12] | 0 |
| growth level 0.95 | 61 | 2,470 | +0.86 [+0.71, +1.02] | 0 |

Broad optimum: a faster frustration brings growth earlier without misplacing it, up to a point (0.8 begins to
misplace); a lower growth level costs nothing. Nothing grows in all-food lives at any setting. Chosen for E6: 0.5
and 0.6, to be confirmed on held-out lives (the choice was made on the evaluation lives).

*(c) Mismatch* (every gain and bias off by a random 5% or 10%, normal, fixed at birth; paired with the same brain
unperturbed). First run: some lives scored "never moved". Traced: a bug, `start = moving or ticks`, counted a creature
that moved at tick 0 (moving = 0, false in Python) as one that never moved; with mismatch a motor can fire from the
first tick. Fixed in experiments/common.py, creature.py and measure_recruitment.py; it had affected no earlier result (no
unperturbed life of any of these brains moved at tick 0: checked, 0 of 64 or 128 each). After the fix:

| brain | 5% mismatch: net food change | 10% |
|---|---|---|
| R3 | -0.64 [-0.90, -0.40] | -0.84 [-1.03, -0.66] |
| designed circuit | -0.72 [-0.90, -0.52] | -1.04 [-1.25, -0.82] |

Both lose most of what they learned at 5%: the opposite of "robust through balance". *(e) Which mismatch?* (R3, 5%,
one class of parameter at a time):

| mismatch in | net food change |
|---|---|
| each neuron's own fast and slow elements | -0.66 [-0.90, -0.43] |
| node biases | -0.37 [-0.53, -0.21] |
| everything else (synapses, learning, frustration, routing, sprouts, growth) | -0.01 [-0.15, +0.13] |
| all | -0.64 [-0.90, -0.40] |

The recruitment machinery is robust; all the fragility is in the neuron, shared with (and inherited from) the
designed circuit. Working: its fast positive and slow negative elements have equal strength (2.0) at the same offset,
cancelling exactly at rest, which leaves it 0.38 V below threshold (rest -3.2, threshold -2.82), with a bias 12% from
firing by itself (-1.6 against -1.41). A 5% error in either strength leaves about +/-0.13 of net current at rest,
shifting rest by about +/-0.26 V, up to 70% of the margin: a precise-parts design. A neuron whose rest moves toward
threshold fires more by itself; for the taste neuron that means false "danger", which explains the extra food-sensor
bridges under mismatch (23 against 2). The fix belongs to the neuron (a design that keeps its margin under
mismatch), a change of substrate outside rung 1.

*(d) Cost* (at the end of one poison life): baseline 5 nodes, 12 elements, sum of gains 20; knowing 10, 23, 49; R3
22, 42, 531; designed 11, 24, 1,006. The sum of gains approximates static power in the worst case (each element an
amplifier drawing about its gain as bias current, all fully biased). *Corrected (the user asked for detail):* a gated
amplifier's bias is set by its gate, so the more physical measure is gain x gate, averaged over the second half of a
life. Worst case / gated average: baseline 20 / 20; knowing 49 / 48; designed 1,005 / 264; R3 531 / 412; R4 650 / 456.
So R3 needs about half the designed circuit's power only in the worst case; by the gated average R4 needs about 1.7
times as much. Breakdown: big currents go with big quiet capacitors (current = C x rate: the designed circuit's
learning amplifiers into P, C = 1,000, gains 231 each; R4's frustration charger into F, C = 775, gain 298); gating
makes them affordable (the designed circuit's 923 averages 182, gated by eligibility; R4's charger 298 averages 107);
and the one-bridge-per-neuron inhibitor wastes power, holding the losing sprout at 0 with an ungated, full-strength
current (gain 200, for the sprout's big capacitor) for ever: nearly half of R4's power. Untested fix: let growth close
the gate on the losing sprout's charging amplifier (re-gate it with a memory node at 0) instead of fighting it with a
current: the same effect at no running cost, bringing R4 to about 256, level with the designed circuit. Dynamic power
(charging capacitors at each spike) is not counted; the neurons are alike, so it is similar for both.

## E6: confirmation on held-out lives (2026-10-18)

*Method.* R3 against R4 (R3 with frustration rise 0.5 and growth level 0.6) on fresh seeds (100-131), with the knowing
brain and oracle O1. `python -m experiments.e6_confirm 64`; results/e6.txt.

| | exactly O1 | first bridge (median tick) | net vs knowing | all-food lives | vs oracle O1 |
|---|---|---|---|---|---|
| oracle O1 | 64 | birth | +1.15 [+1.00, +1.31] | -0.30 [-0.48, -0.13] | |
| R3 | 58 | 2,334 | +0.90 [+0.72, +1.07] | +0.00 | -0.25 [-0.39, -0.12] |
| R4 | 61 | 1,690 | +1.00 [+0.85, +1.14] | +0.00 | -0.15 [-0.32, +0.01] |

R4 against R3: +0.10 [-0.07, +0.26].

*Findings.* R3 replicates on fresh lives (+0.90 against +0.93). R4 grows earlier, places better, and is not
significantly different from a bridge present from birth; its edge over R3 is not significant alone but agrees with
E5b. Adopted: R4 is the recruiting circuit's default. And on these lives the hand-placed bridge costs significantly in
all-food lives (-0.30: an always-present relay loses spikes and adds delay), where the recruited bridge never grows:
averaged over a world where half the lives have poison, recruiting beats a bridge built in at birth (+0.50 against
+0.43 per life).

## Conclusions (rung 1)

1. *A brain can recruit, locally, the link that lets its knowledge act.* Starting from a taste neuron that knows what
   predicts pain but has no outputs, the frustration node, help routed back along what T learned, competing sprouts
   and one growth primitive grow, in nearly every poison life, exactly the structure an oracle would place (61 of 64
   held-out lives), as well as the oracle placing it at the same moment (E5a), and nothing in all-food lives.
2. *What it takes* (E2-E4): frustration needs both knowledge and unprevented pain (two independent conditions, so
   chance frustration grows nothing); routing by what each synapse learned is essential (without it growth is blind);
   competition between a neuron's sprouts is essential (without it every sprout grows); help must be a logical AND
   (predicts pain, and frustrated), and a neuron that has sprouted must stay changed (one bridge per neuron).
3. *What it buys*: as much net food as a hand-placed bridge, less the time before growth (about 1,700 ticks), and no
   cost in food where nothing needs learning, where a built-in bridge costs. In power it is not cheaper: about 1.7
   times the designed circuit's (gated average), nearly half of it a wasteful always-on inhibitor (E5d, with a fix).
4. *Methods that mattered*: oracle structures as ceilings; paired lives with per-node noise streams (common random
   numbers), without which variants of different sizes differ by chance as much as by design; quiet slow nodes
   (capacitance growing as the square root of their time); held-out lives to confirm choices.
5. *Open*: (a) the neuron is fragile to mismatch, the recruitment machinery isn't (E5c, E5e): redesign the neuron for
   margin; (b) growth from the rung-0 animal, and pain felt at the motors instead; (c) de-recruitment (a bridge
   transparent for long, or the world changing mid-life); (d) a harder task where a feature, not a bridge, must be
   recruited (rung 2).

## E7: a local hold (2026-10-18)

*Question* (prompted by the user, who saw in the block view that the bridge seemed unconnected to the taste neuron).
The bridge's hold was charged by T's spikes, so the growth rule had to know which neuron's frustration summoned the
bridge: knowledge the growth rule had (`self.T`) and the circuit didn't. It should have been flagged when built. The
alternative: charge the hold by the sensor's own spikes, gated by its synapse onto T (W: "my activity predicts
pain"), so everything the bridge connects to is on the synapses of the sensor it grows from. *Method.* Both
structures hand-placed (each one's ceiling) and grown (R4), on the original seeds (0-31) and held-out seeds (100-131),
paired. `python -m experiments.e7_local_hold 64`; results/e7.txt. (The block view, blocks.py, was fixed at the same
time to draw links through state nodes, which is why the T-hold-bridge link had looked missing.)

| | seeds 0-31 | held-out 100-131 |
|---|---|---|
| grown, T hold: net vs knowing | +0.97 [+0.80, +1.14] | +1.00 [+0.85, +1.14] |
| grown, local hold: net vs knowing | +1.10 [+0.95, +1.26] | +1.09 [+0.94, +1.25] |
| local against T hold, grown | +0.13 [+0.01, +0.23] | +0.10 [-0.01, +0.21] |
| last-third food:poison, grown T / local | 3.57 / 4.91 | 3.70 / 5.68 |
| hand-placed, local against T hold | +0.11 [-0.03, +0.26] | +0.12 [-0.01, +0.24] |
| exactly one bridge, on the poison sensor (T / local) | 62 / 63 | 61 / 62 |

Pooled over both sets (128 lives): grown, local against T hold +0.11 [+0.03, +0.19]; hand-placed +0.11 [+0.01, +0.21].
No growth and no cost in all-food lives for either.

*Findings.* The local hold is better as well as more local. Working: T fires by itself and through the food sensor's
weak synapse (false alarms before about half of food meals, below: Before E0), and each time the T hold makes the creature
veer from food; the local hold fires only with the poison sensor itself, so its veers are specific (E1's O5 failed
for the same reason, T firing too often). Last-third food:poison 4.9-5.7, as good as the designed circuit's (5.3).
Adopted: the local hold is the default; the growth rule now needs nothing beyond the synapses of the neuron it grows
from. (Hand-placed local bridges eat more in all-food lives, +0.46 and +0.12 against the knowing circuit: with W near 0
the local hold never holds, and the bridge neuron's own spontaneous spikes add exploratory kicks, E1's confound.)

## Conclusions, revised after E7

The recruiting circuit (defaults: sharp routing, one bridge per neuron, frustration rise 0.5, growth level 0.6, local
hold) grows exactly the oracle's structure in about 62 of 64 poison lives, nets about +1.1 food per 1,000 ticks over
the knowing circuit with last-third food:poison about 5, and grows nothing in all-food lives. Everything is circuit
except the growth primitive, and the primitive now needs to know only where the winning sprout is: the bridge
connects to the synapses of the sensor it grows from and nothing else.

# H series: recruiting with no knowledge of the circuit (2026-10-19, overnight, autonomous)

*Question* (the user's). Rung 1's recruiting circuit found *where* to grow by itself, but its machinery (help nodes on
the sensors, sprouts on the sensor-to-motor synapses, a frustration node on T) was placed only where it would be
needed. Can a recruit that knows nothing of the circuit, attached only to its frustrated parent and that parent's
neighbours on the graph, learn for itself which connection, treated how, reduces frustration, and if it can't, spread
the problem outward (an inflammation, a healing response)? The user's terms: only T has frustration (it may be
effectively global: "recruit something near here"); near is one edge; try any creative rules, as long as nothing
"understands" the circuit; lives up to 100,000 ticks; keep a leaderboard (LEADERBOARD.md).

*The healing circuit* (brains/healing.py). Generic throughout:
- Frustration motif: a unit that can be frustrated has F (slow: anticipated pain, pain while it had just fired:
  its prediction didn't prevent it), O (a fast "ouch" pulse at every pain) and Y (a fast "yum" pulse at every good
  taste). Only T receives taste from the body, so only T is frustrated at first. F triggers recruitment; O and Y are
  what recruits learn from (the same news T itself gets).
- Growth (the one primitive): a frustrated unit (F past 1/2) with no recruit gets one, attached to it and to every
  neuron within one edge; a recruit's own recruit attaches to it and to every neuron within one edge of anything it
  was attached to (inflammation spreading one edge per failed wave).
- The recruit: a neuron R; a hold node (its action lasts about 10 ticks after it fires); listening synapses from every
  attached neuron (strengths: memory nodes); a menu of acting options (inhibit or excite an attached neuron; turn down
  one of an attached neuron's ungated output synapses, through a gate node that rests open), each with an enable node.
- Listening ("pain"): a strength rises when its neuron fired just before an ouch and falls when it fired just before
  a yum. Choosing ("wsls", win-stay lose-shift): enables rise from nothing, latch, and hold each other down (one wins,
  by noise); each has a tiredness node, charged by pain after R acts while it's on and eased by a good taste after R
  acts; a tired option is knocked out and kept out while tiredness fades (inhibition of return), and another wins.

*Calibration, traced (H0).* First runs failed four ways, each traced to a cause: (1) listening saturated for every
input: an ouch pulse stays above half for about 8 circuit ticks, not the 1.3 assumed (the taste node's), so each pain
raised a strength by about 1.2; the pulse was shortened and measured (above half for 4.5 circuit ticks at full height)
and the gains scaled to it. (2) No option ever switched on: an enable's slow rise settled at 0.32, under its latch's
threshold; doubled. (3) Listening couldn't discriminate: the poison and food eyes rose at +0.3 and +0.2 per 1,000 ticks,
being often active together; a constant slow decline can't separate rates so close; T's own synapses discriminate
(0.87 against 0.13) because good tastes weaken them, so recruits now hear yum too: listening then sends the food eye
to 0. (4) Win-stay lose-shift gave up every few hundred ticks until every option was tired: options were blamed before
listening had learned when to act, and the tolerance would knock out even the right option (which still lets about
0.6 pains through per 1,000 ticks); tiredness is now a rate threshold (pain per tick of acting above about 1 in 3,000,
between the untreated rate and a good option's), eased by good tastes after acting. A shared inhibitor in place of
pairwise rivalry failed: every enable was born at rest above its latch threshold, all latched together, and a shared
node can't tell one option on from ten; pairwise rivalry restored, enables born at 0.

*Smoke test* (seeds 0-2, 40,000 ticks, last 10,000 ticks): red 0 settled on inhibiting the poison eye (ignore; food 18,
poison 7); red 1 and 2 on turning down the poison eye's synapse to the left motor (a veer: 18:3, 25:6); all-food lives
recruited nothing. With no knowledge of the circuit, the bridge's structure was found in two lives of three.

## H1: rules for a generic recruit, 30,000-tick lives (2026-10-19)

`python -m experiments.h1_rules 64 30000`; results/h1_30000.txt; LEADERBOARD.md. Wave 1 only (no cascade); paired
with the knowing circuit (no recruitment).

| rule | net food vs knowing | food:poison, last third | lives settling on a veer (gate poison eye -> motor) |
|---|---|---|---|
| guided bridge (rung 1's recruiting circuit, for reference) | +1.18 [+1.07, +1.28] | 3.67 | 100% |
| wsls, listening fixed full | +0.93 [+0.81, +1.05] | 5.78 | 89% |
| wsls, inhibit/gate only | +0.80 [+0.68, +0.92] | 2.57 | 80% |
| wsls (learned listening, both signs, menu with synapses) | +0.71 [+0.59, +0.83] | 2.59 | 86% |
| wsls, excite/gate only | +0.70 [+0.60, +0.81] | 2.18 | 83% |
| wsls, learning from anticipated pain only | +0.41 [+0.29, +0.52] | 1.55 | 61% |
| wsls, no listening | +0.19 [+0.08, +0.31] | 1.29 | 50% |
| all options on at once | +0.10 [+0.00, +0.19] | 1.09 | 23% |
| wsls, menu of neurons only | -0.00 [-0.11, +0.10] | 0.99 | 0% |
| one random option | -0.04 [-0.26, +0.18] | 0.93 | 25% |

No rule recruited anything in all-food lives.

*Findings.* (1) A recruit that knows nothing finds the bridge's function: with win-stay lose-shift and a menu that
includes the attached neurons' output synapses, recruits settled on turning down the poison eye's synapse to a motor in
86-89% of poison lives, out of ten options; choosing matters (one random option: nothing; all options at once: +0.10).
(2) Fixed full listening beats learned listening (+0.93 against +0.71; last third 5.8). Working: with full listening R
fires whenever anything it is attached to fires, so it acts often, win-stay lose-shift gets many more trials to judge by
and settles sooner; and firing "too often" costs nothing for a gating action, which matters only when the gated synapse
carries a spike. The action's target gives the selectivity; timing needn't be learned (the local hold's lesson again).
No listening at all fails (+0.19): R then fires only by itself, too rarely to act or to learn. (3) Wireheading
confirmed: learning from anticipated pain only (+0.41) lets an option win by silencing T's anticipation; five times as
many lives settled on inhibiting T (10 against 2). Recruits must learn from pain itself. (4) Neurons only: nothing in
wave 1 helps (0.00), as expected: a neuron-level action can't make a veer from the eyes; the cascade's case (H2).

## H2, first attempts: the cascade's trigger (2026-10-19)

Smoke tests (three lives, 60,000 ticks, neurons-only menu). (1) Recruits frustrated by any pain after acting cascaded
within about 120 ticks, before trying anything. (2) Frustrated only by pain while idle (every option knocked out:
"exhausted"), wave 2 waited 10,000-27,000 ticks, but wave 3 followed within about 100 ticks (a newborn recruit is idle
while its options rise from nothing, and one pain raised its frustration by 0.5); with slowly building idleness and
smaller steps, no second wave at all in 60,000 ticks: with full listening R acts constantly, so its tiredness tracks
pains minus good tastes, which no neuron-level option changes much, so no option is knocked out and the recruit is never
idle. (3) The user's own description is the right trigger: "if it can't reduce frustration, it itself starts to emit
frustration": a slow node filling while the parent stays frustrated (F past 1/2), about 10,000 ticks after the recruit
came. Then waves 2 and 3 grew about 10,000 ticks apart, but settled on nothing: with full listening a wave-2 recruit
fires at everything (motors too), and a neuron-level action (inhibit a motor) needs timing. So the cascade needs
learned listening: H2 proper.

## H3: the best rules in 100,000-tick lives (2026-10-19)

`python -m experiments.h_run 64 100000 ...`; results/h3_100000.txt; LEADERBOARD.md.

| rule | net food vs knowing | food:poison, last third | lives settling on a veer |
|---|---|---|---|
| guided bridge (rung 1's recruiting circuit) | +1.16 [+1.09, +1.24] | 3.60 | 100% |
| wsls, listening full, inhibit/gate only | +1.12 [+1.06, +1.18] | 4.68 | 92% |
| wsls, listening full | +1.08 [+1.01, +1.15] | 3.37 | 91% |
| wsls, inhibit/gate only | +0.76 [+0.71, +0.82] | 2.17 | 84% |
| wsls | +0.66 [+0.61, +0.72] | 1.82 | 66% |
| reinforce | +0.16 [+0.10, +0.22] | 1.19 | 25% |
| reinforce, listening full, inhibit/gate only | +0.01 [-0.04, +0.05] | 1.02 | 36% |
| reinforce, listening full | +0.00 [-0.04, +0.04] | 1.01 | 20% |

Best generic rule against the guided bridge, paired: -0.04 [-0.13, +0.04]. Nothing recruited in all-food lives.

*Findings.* (1) Over long lives a recruit that knows nothing of the circuit matches the guided bridge: win-stay
lose-shift, full listening, inhibiting or gating only, is statistically indistinguishable from it (-0.04 [-0.13,
+0.04]), with a higher last-third food:poison (4.7 against 3.6), settling on the veer in 92% of lives. No help routing,
no sprouts placed for the job, nothing named. (2) The reinforcement rule fails: graded options let gating the food
eye's synapse persist beside the poison eye's, and its constant jitter disturbs behaviour (with full listening food
fell to 0.5 per 1,000 ticks). Committing to one option beats blending, here. (3) Learned listening is less stable in
long lives (veer share 86% at 30,000 ticks, 66% at 100,000). Hypothesis: with learned listening R acts only when it
detects poison, so good tastes rarely follow its actions and never ease its tiredness, and even the right option
(which still lets some pain through) is knocked out in the end; with full listening good tastes follow its constant
action as often as they should, balancing tiredness. To check by recording when options switch.

## H4: early recruits, shadow mode and inherited knowledge (the user's idea), and the cascade (2026-10-19)

The user's suggestion: frustration takes time to build, and a recruit then learns from scratch, so either pass
knowledge forward from the frustrated unit, or recruit early and let the recruit learn in "shadow mode", acting only
once frustration passes the threshold. Three options (brains/healing.py): grow_at=0.15 (early), shadow (an early recruit
acts, and counts as having acted, only while T's "frustrated" flag, F past 1/2, is on), and listen="inherit" (where T
already holds a learned memory on its synapse from an attached neuron, the recruit's listening synapse from it is
gated by that same memory node). `python -m experiments.h_run 64 100000 ...`; results/h4_100000.txt. Switch counts are
recorded now (the last tick at which a wave-1 recruit's chosen option changed).

| rule | net food vs knowing | food:poison, last third | veer | median switches | median last switch |
|---|---|---|---|---|---|
| wsls, listening full, inhibit/gate only (rerun) | +1.14 [+1.08, +1.20] | 4.40 | 94% | 15 | 77,055 |
| ... early | +1.11 [+1.05, +1.17] | 4.28 | 86% | 17 | 71,995 |
| wsls, inhibit/gate only, inherit | +0.95 [+0.89, +1.00] | 2.56 | 83% | 25 | 87,237 |
| wsls, inhibit/gate only, early | +0.81 [+0.77, +0.85] | 2.23 | 91% | 27 | 79,994 |
| wsls, inhibit/gate only, inherit, shadow | +0.81 [+0.77, +0.87] | 2.20 | 83% | 28 | 89,999 |
| wsls (learned listening, both signs; rerun) | +0.70 [+0.64, +0.75] | 1.94 | 73% | 35 | 86,301 |
| wsls, inhibit/gate only, shadow | +0.74 [+0.70, +0.79] | 2.02 | 84% | 29 | 87,832 |
| (H3: wsls, inhibit/gate only, not rerun) | +0.76 [+0.71, +0.82] | 2.17 | 84% | | |
| wsls, neurons only, cascade | +0.02 [-0.03, +0.08] | 0.98 | 0% | 101 | 98,466 |
| wsls, neurons only, listening full, inhibit only, cascade | +0.03 [-0.01, +0.07] | 1.63 (food 0.35 per 1,000) | 0% | 15 | 25,893 |

*Replication.* The reruns use the same lives but different noise in the recruits (adding T's flag node shifted
recruit nodes' noise streams): +1.12 then +1.14, +0.66 then +0.70: the noise realisation alone moves a row by about
0.04.

*Findings on the user's idea.* (1) Waiting for frustration is not the slow part: T's frustration passes 1/2 about
1,000 ticks into a life (recruits came at ticks 949-1,228), while win-stay lose-shift is still switching at tick
70,000-90,000 (median last switch). Recruiting early (F past 0.15, about tick 360) moved nothing measurably. (2) Passing
knowledge forward works: inheriting T's learned strengths lifts learned listening from +0.76 to +0.95 and the veer share
holds; it doesn't reach full listening (+1.14), so listening at all, even well informed, still costs actions. (3)
Shadow mode as built hurt (+0.81 to +0.74; with inherit +0.95 to +0.81), and the cause is the gate, not the idea: T's
flag is off for a third of late life (0.66 on, seed 0), because the recruit's help calms T, and then the recruit stops
acting and the poison comes back: a fix that withdraws itself as soon as it works. Remedy: commission the recruit for
good the first time the flag comes on (a memory node charged by the flag; shadow="latch"): H5.

*Cascade.* (1) With learned listening and both signs, wave 2 and 3 recruits chose "nothing" in every life: the
pairwise rivalry's sigmoid tails (slope 12) from eleven resting rivals summed past the enables' rise (11 x 0.3 x
0.0028 = 0.009 of C against 0.008), so no enable ever rose. A scaling flaw: fixed by a steeper rivalry (slope 20), after
which wave 2 latches. This changes every win-stay lose-shift recruit, so H5 reruns the leaders. (2) With full listening
and inhibition only, the cascade found a degenerate cure: wave 2 inhibited a motor in 61 of 64 lives, and the creature
nearly stopped (food 0.35 per 1,000 ticks against 1.5): fewer pains, and fewer good tastes too. Frustration and
tiredness count pains and good tastes, not their ratio, so freezing looks like a cure. Lesson: a healing response
judged by pain alone rewards doing less; the judge must be the share of bad tastes, or freezing must cost something.

## H5: steeper rivalry, commissioned shadow, cascades; H6: held-out lives (2026-10-19)

results/h5_100000.txt, results/h6_100000_heldout.txt. Rivalry slope 20 throughout (see H4).

| rule | net food vs knowing | food:poison, last third | veer | median switches |
|---|---|---|---|---|
| wsls, listening full, inhibit/gate only | +1.16 [+1.10, +1.23] | 4.44 | 91% | 14 |
| wsls, inhibit/gate only, inherit, shadow, commissioned | +0.96 [+0.91, +1.02] | 2.69 | 78% | 25 |
| wsls, inhibit/gate only, inherit | +0.92 [+0.88, +0.97] | 2.63 | 84% | 26 |
| wsls, inhibit/gate only, shadow, commissioned | +0.79 [+0.74, +0.85] | 2.09 | 75% | 27 |
| wsls, neurons only, inherit, inhibit only, cascade | +0.21 [+0.17, +0.26] | 1.56 (food 0.75 per 1,000) | | 27 |
| wsls, neurons only, cascade | +0.14 [+0.10, +0.18] | 1.19 (food 1.06) | | 51 |
| wsls, neurons only, listening full, inhibit only, cascade | +0.02 [-0.02, +0.06] | 1.05 (food 0.36) | | 15 |
| *held out (seeds 100-131):* guided bridge | +1.16 [+1.07, +1.24] | 3.66 | 100% | |
| *held out:* wsls, listening full, inhibit/gate only | +1.10 [+1.04, +1.16] | 4.45 | 86% | 15 |
| *held out:* wsls, inhibit/gate only, inherit | +0.94 [+0.88, +1.00] | 2.67 | 89% | 24 |

Held out, best generic rule against the guided bridge, paired: -0.06 [-0.13, +0.03].

*Findings.* (1) The steeper rivalry leaves wave 1 as it was (+1.16; it had +1.12, +1.14). (2) Commissioning fixes
shadow mode's self-withdrawal (+0.74 to +0.79; with inherit +0.81 to +0.96), but then it only equals recruiting early
without a shadow (+0.81) or inheriting without one (+0.92): as predicted, a shadow can learn what to listen to but not
which action helps, and choosing the action is the slow part. (3) The held-out lives confirm the order and the
size: a recruit that knows nothing of the circuit matches the guided bridge in net food on fresh lives too, and beats
it on the last third's food:poison (4.45 against 3.66). (4) Wave 2 now latches, but the cascades still don't solve
the task: with the menu of neurons only, wave 2 settles on inhibiting a motor (48 of 64 lives with inherited
listening), and food falls by half: the freezing cure again, which judging by rates allows. Next: judge by shares (H7).

*A second sigmoid tail.* The first share judge (tiredness that rests only while its option is off, eased by half a
pain's step per good taste) churned: tiredness climbed with no tastes at all, 0 to 0.46 in 2,000 ticks. The resting
tail of the pain-after input (sigmoid slope 10, 0.7% of full) charges tiredness constantly; under the rate judge the
good-after input's equal tail cancels it exactly, so it never showed. With unequal steps it doesn't cancel. Fixed by a
steep sigmoid (slope 30). The general lesson, twice in a day: a sigmoid's resting tail is a small constant current, and
summed over many inputs, or left uncancelled over a long time constant, it is not small.

## H7: judging by the share of bad tastes (2026-10-19)

judge="share": an option's tiredness hardly fades while it is on (100,000 ticks), rises a step per pain after acting
and falls half a step per good taste, so it tires when more than 1 taste in 3 after acting is bad, whatever the rate;
while off, it rests over 10,000 ticks (an off node, held down by the enable, gates the rest). Step 0.05 (0.15 churned:
a run of three or four pains crossed the threshold even under the right option). results/h7_100000.txt.

| rule | net food vs knowing | food:poison, last third | veer | median switches | median last switch |
|---|---|---|---|---|---|
| share: wsls, listening full, inhibit/gate only | +1.14 [+1.08, +1.22] | 7.42 [6.81, 8.18] | 100% | 5 | 13,097 |
| share: wsls, listening full (both signs) | +1.12 [+1.06, +1.19] | 7.26 | 100% | 5 | 14,317 |
| share (step 0.15): wsls, listening full, inhibit/gate only | +1.08 [+1.02, +1.14] | 3.95 | 91% | 25 | 88,703 |
| share: wsls, inhibit/gate only, inherit | +1.05 [+0.99, +1.11] | 3.37 | 97% | 5 | 11,849 |
| share: wsls (learned listening, both signs) | +0.76 [+0.69, +0.82] | 2.23 | 94% | 8 | 25,036 |
| share: neurons only, inherit, inhibit only, cascade | +0.18 [+0.13, +0.23] | 1.46 (food 0.71 per 1,000) | | 13 | |
| share: neurons only, inherit, cascade | +0.15 [+0.10, +0.20] | 1.55 (food 0.87) | | 15 | |
| share: neurons only, cascade | +0.14 [+0.09, +0.19] | 1.21 (food 1.06) | | 19 | |

*Findings.* (1) Judging by share settles win-stay lose-shift: every life settled on the veer, after a median of 5
switches by tick 13,000 (under rates: 14 switches, still switching at tick 72,000), and the last third's food:poison
doubled, 4.4 to 7.4, against the guided bridge's 3.6. Net food over the whole life barely moves (+1.14), since it is
dominated by the first third, before T has learned which colour hurts. With both signs the menu is twice as long and
it still settles: the judge, not the menu, was the problem. (2) Inherit is better under share too (+1.05, 97% veer,
from +0.92), but full listening still leads. (3) The cascade with neurons only still fails, and not by freezing now:
wave 2 inhibits a motor while the poison eye fires, a real veer (seed 0: 12 food, 3 poison in the last 20,000 ticks),
but each spike holds the motor off for 10 ticks, and the creature fires that thruster half as often and eats half as
much. Share doesn't see the cost of eating less. A shorter hold (3 or 1 ticks) removes the cost and the veer with it:
turning away needs the motor off long enough to turn. A neuron-level veer has a cost a synapse-level one doesn't.
(4) That points to the menu: a recruit turning down the synapses arriving at its neighbours (menu "inputs") finds
nothing in wave 1, where T's inputs are memories and the eyes have none, and the eyes' synapses to the motors in
wave 2, once the cascade has reached the motors: smoke test, 3 of 4 lives found "gate poison eye -> motor" in wave 2
(ticks 12,000-38,000), 34:3 and 35:9 food:poison in the last 20,000 ticks. H9.

## Power of the generic recruit (2026-10-19)

Static power by the gated average (sum of |gain| x clip(V_gate, 0, 1), sampled over ticks 60,000-70,000, four poison
lives; scratchpad script): knowing circuit 280; guided bridge 476 (+196); share leader (wsls, listening full,
inhibit/gate only) 1,505 (+1,225); with inherit 1,553; inputs cascade (two waves) 3,653. By element kind (share
leader, seed 0), most of the recruit's power is choosing, not acting: the enables' latch and pairwise rivalry,
863 (n(n-1) ungated elements, each fully biased whether or not its rival is on), the tiredness knock-outs 221, and the
tiredness inputs 75. Fix to test: gate each rivalry, latch and knock-out element by its own source (the rival's enable,
the enable, the tiredness), so it draws current only while that node is up; one option is on at a time, so the
rivalry's cost becomes linear in the menu.

## H8: held-out lives for the share judge (2026-10-19)

results/h8_100000_heldout.txt (seeds 100-131).

| rule (held out) | net food vs knowing | food:poison, last third | veer | median switches | median last switch |
|---|---|---|---|---|---|
| share: wsls, listening full, inhibit/gate only | +1.16 [+1.09, +1.23] | 6.97 [6.40, 7.62] | 100% | 3 | 8,085 |
| share: wsls, inhibit/gate only, inherit | +1.08 [+1.01, +1.15] | 3.52 | 97% | 3 | 8,769 |
| share: wsls, listening full | +1.06 [+0.99, +1.14] | 6.93 | 100% | 5 | 11,556 |

Confirmed on fresh lives: the share judge's leader settles on the veer in every life, and its last third (7.0) is
about twice the guided bridge's (3.7, H6).

## H9: the cascade with the menu "inputs" (2026-10-19)

results/h9_100000.txt. Wave 1 can't help (T's inputs are memories, the eyes have none); a recruit still frustrated
10,000 ticks after it came is frustrated itself, and wave 2 reaches the motors, whose inputs include the eyes' synapses.

| rule | net food vs knowing | food:poison, last third | wave 2 gates the poison eye |
|---|---|---|---|
| inputs: no cascade (control) | +0.14 [+0.09, +0.20] | 1.09 | (no wave 2) |
| inputs: cascade, inherit, inhibit/gate only | +0.53 [+0.43, +0.62] | 2.81 | 31 (+6 in wave 3) of 64 |
| inputs: cascade, listening full, inhibit/gate only | +0.45 [+0.35, +0.56] | 4.27 | 34 (+3) |
| inputs: cascade, listening full, both signs | +0.37 [+0.26, +0.49] | 3.69 | 27 (+7) |
| inputs: cascade, learned listening, inhibit/gate only | +0.41 [+0.34, +0.50] | 1.96 | 34 (+7) |
| inputs: cascade, inherit, both signs | +0.44 [+0.35, +0.55] | 2.44 | 26 (+9) |

By what the waves chose (listening full, inhibit/gate only), last third: where wave 2 gated the poison eye's synapse
and wave 1 had settled on inhibiting T, 51.6 food and 7.9 poison (14 lives), as good as the wave-1 leader; where wave 1
had settled on inhibiting the food eye, 24.5 and 4.5 (13): half the food; where wave 2 inhibited a motor, about 1.5
of each (18): frozen.

*Findings.* (1) The healing cascade works as the user pictured it: a recruit that can't help is frustrated itself,
the next wave reaches one edge further, to the motors, and finds the cure there, in about 60% of lives (wave 2 or 3).
(2) Two failures, each with a cause. *Freezing:* the share judge can't judge an option that is followed by no tastes
at all; "inhibit a motor" with full listening stops the creature, and with no news it is never knocked out.
*Credit leaking between waves:* wave 1's last option stays on after wave 2 cures the poison, and then looks good
(few pains follow it), even when it is harmful (inhibit the food eye: half the food). Remedies, H10: "starve" (while
an option is on its tiredness creeps up, eased only by good tastes, so no news is bad news) and "retire" (a recruit
frustrated enough to recruit stands down for good, a memory node holding its actions off: de-recruitment). Also the
power fix (latch, rivalry, knock-out gated by their own source). Caveat seen in the smoke test: a recruit's
frustration is charged by its parent's frustration, which fades over 10,000 ticks, so a successful wave 2 can still
retire.

## H10: power gating, starve and retire (2026-10-19)

results/h10_100000.txt. All win-stay lose-shift recruits now gate their latch, rivalry and knock-out elements by
their own source.

| rule | net food vs knowing | food:poison, last third |
|---|---|---|
| gated: share: wsls, listening full, inhibit/gate only | +1.17 [+1.10, +1.24] | 7.56 [6.93, 8.31] |
| gated: share, starve: the same | +1.18 [+1.12, +1.23] | 7.05 |
| gated: inputs: cascade, listening full, inhibit/gate only | +0.38 [+0.27, +0.50] | 3.95 |
| gated: inputs: cascade, starve | +0.41 [+0.30, +0.53] | 3.17 |
| gated: inputs: cascade, retire (with or without starve, inherit) | -0.00 to -0.02 | 1.0 |

*Power.* Gated average, re-measured (two lives each): knowing 283, guided bridge 528, share leader 550 (was 1,505),
with inherit 609, inputs cascade 1,028 (was 3,653). The generic recruit now costs about what the guided bridge does,
and behaves as before (+1.17, 7.6).

*Starve* (tiredness creeping up while on, knocked out after 40,000 ticks with no good tastes): the cascade's lives
that end inhibiting a motor fall from 28 to 17 of 64 and no longer freeze (about 10 food and 10 poison per last third,
was 2 and 1.5), and those finding the poison eye's gate rise from 35 to 42; net unchanged, as a freeze still lasts
much of a life before it starves.

*Retire* (a recruit frustrated enough to recruit stands down for good) failed outright, every life reaching wave 3
and doing nothing: a recruit's frustration was charged by its parent's, which fades over 10,000 ticks and outlasts a
cure, so successful waves retired too. Charging every wave from the root's own flag (T's) instead (trigger="root")
was the remedy to try. A prediction refuted on the way: I estimated T would stay "frustrated" even when cured (0.37
pains per 1,000 ticks x 0.5 per pain x 3,000 ticks ~ 0.55); measured under the wave-1 cure, T's F averages 0.04-0.10
and its flag is on 0-4% of late ticks, as F counts only anticipated pains. Smoke tests of root-triggered retire (three
lives) still failed, for two reasons: a wave given 10,000 ticks of grace can't judge a ten-option menu, and when T
stays frustrated every wave retires in the end, the last one too, so no one acts. With 30,000 ticks, the same. H11
measures these at scale. What de-recruitment should mean (may the last recruit stand down? a cap on waves is a
hidden size) is a design question for the user.

## H11: the root trigger, a faster starve, and retire at scale (2026-10-19)

results/h11_100000.txt. Menu "inputs", listening full, inhibit/gate only, share judge, power gating throughout.

| rule | net food vs knowing | food:poison, last third | deepest wave |
|---|---|---|---|
| root: cascade, starve 20k | +0.66 [+0.53, +0.79] | 4.89 [3.98, 5.96] | 2 in 33, 3 in 31 |
| root: cascade | +0.40 [+0.28, +0.53] | 4.31 | 2 in 35, 3 in 29 |
| root, 30k grace: cascade | +0.38 [+0.27, +0.50] | 4.28 | 2 in 63, 3 in 1 |
| root (10k or 30k grace): cascade, retire (with or without starve, inherit) | -0.00 to +0.08 | about 1.0 | 3 in all 64 |

*Findings.* (1) The best cascade yet: every wave frustrated by T's own flag, and a starve of 20,000 ticks (a freeze
knocked out twice as fast as at 40,000): +0.66, against +0.38 to +0.53 before; the root trigger alone changes little
(+0.40 against +0.38), the faster starve does the work (+0.26). (2) A longer grace (30,000 ticks before a recruit is
frustrated itself) holds the cascade at wave 2 in nearly every life, without gain. (3) Retire fails in every form,
confirming the smoke tests: with T still frustrated every recruit stands down in the end, the last one too, and no one
acts. What de-recruitment should mean is left to the user (RECRUITMENT.md, future work: a walking recruit would
release its old action as it moves). The app's `healing-cascade` is now the best version (root trigger, starve 20k).

*Reproducing the H series.* `experiments/h_run.py` holds every rule by name (`python -m experiments.h_run LIVES TICKS
name ...`, `--seed 100` for held-out lives); H1 ran from `experiments/h1_rules.py`. Two later changes alter earlier
rows slightly if rerun: the rivalry's steeper slope (from H5) and power gating (from H10); both were checked on the
leader (+1.12, +1.14, +1.16, +1.17 across versions, within the 0.04 a new noise realisation moves a row). H2's
smoke-test script was superseded by `h_run.py` and removed.

## Lessons from this line, in full (moved from the old LESSONS.md)

- **Machinery beside the thing studied does its work: the rules were not circuits** (the user's question, 2026-10-18). The net's unit rules (`net_rules/adjust.py`) are compiled
  programs layered on the circuit: per-tick traces, event bookkeeping ("pending", a peak over two ticks, an estimate
  of rest), a hard-coded threshold, and a knob that writes the circuit's bias from outside it. The locality checks
  stopped a rule seeing other units, but inside a unit it was free digital computation: functionality beyond the
  literal circuit, which the mixed-feedback track promises not to have ("everything, learning too, is nodes and
  elements"). It should have been said when the engine was proposed. What stands: the measurements (watching may
  compute anything) and the rung-0 findings as a specification of which local signals are needed; what doesn't: rung
  0's behaviour as a mixed-feedback result. The same kind of mistake as "reward at contact": machinery outside the
  thing being studied doing its work. Rule of thumb: for every number that affects behaviour, ask "which node holds
  it, and which elements move it?"; if the answer is "the program", it isn't the circuit.
- **Enough lives, paired, with intervals on differences.** 16 lives are too few to rank variants (with perfect p from
  birth, net food came out +0.38 in one run of 32 and the oracle's +0.47); run the oracle in the same batch. Pair
  lives (the same seeds and, with per-node noise streams, the same noise), so a difference is caused by the variant;
  a league ordered by point estimates claimed orders it couldn't back, so compare designs on the same seeds, with a
  95% interval on the difference, and call the rest ties.
- **Sigmoid tails are constant currents.** Twice: a dozen resting rivals' tails summed past an enable's rise, so none
  ever won; and a pain input's resting tail, cancelled by the good-taste input's while the steps were equal, charged
  tiredness once they weren't. Summed over many inputs or a long time constant, "almost zero" isn't.

## Before E0: the baseline, rung 0 and the generic recruit (moved from the old LESSONS.md)

The ideas and plan are in `RECRUITMENT.md`, the full record in `experiments/NOTEBOOK.md` (the E and H series). All
of it ran under the earlier noise (a fixed noise per node, no mismatch); under biological noise these hand-built brains
fall to about 1 food for each poison (`NOTEBOOK.md`, Noise as biology makes it), so their results stand only for that
simulator. The lessons here are about mechanisms.

### Recruitment, step 0: the baseline (2026-10-18)

The plan (`RECRUITMENT.md`, agreed with the user): keep the one-bit task, start from a brain with no machinery for
telling food from poison, and let it discover in its life that it needs more. The control, agreed too: all-food lives
(`--all-food`), where tastes are never bad and nothing should be recruited.

- **The baseline circuit** (`brains/baseline.py`): the designed circuit's four neurons, each sensor driving both motors
  through a synapse that relays every spike, taste into a node connected to nothing. Both circuit brains now share
  `CircuitBrain` (neurons, taste node, running, drawing); 32 recorded lives were unchanged, every meal and firing.
- **64 lives of 10,000 ticks:**

  | | poison lives: food:poison by third | meals per 1,000 ticks | all-food lives: food per 1,000 ticks by third |
  |---|---|---|---|
  | baseline circuit | 1.0, 1.0, 1.0 | 3.14 (half poison) | 3.09, 3.38, 2.97 |
  | designed circuit, learning | 2.3, 6.4, 5.3 (55 of 64 learned) | 1.66 | 2.17, 2.54, 2.80 |

- **Machinery costs food when there is nothing to learn.** In all-food lives the learner eats a fifth less than the
  baseline circuit: its sensors hush each other, and with p at 1/2 half its sightings become veers. Even in poison lives
  it eats less food (about 1.3 against 1.6 per 1,000 ticks); what it gains is avoiding poison (about 0.3 against 1.6).
  That cost is what makes recruiting machinery only when needed worth anything.
- **Why non-learners score exactly 1.0:** lives are paired, each seed run once with red as poison and once with blue,
  and a brain that ignores taste behaves identically in both, so its food and poison counts mirror exactly.
- **Agreed for step 0.2** (the user): no detector hand-placed where it will be needed (design smuggled in). Instead
  every unit gets the same generic essential variable (Ashby): here, its own disturbance by bad tastes; the unit taste
  enters is generic, merely the one disturbed. Spare units are generic and identical, sparsely or locally connected,
  and connections grow toward a signal the disturbed unit sends out (as the sheet's paths grow toward a sink's
  field), under one rule that knows nothing of roles.

### Recruitment: where the pain goes, and what a unit can ask (2026-10-18)

- **Flooding every unit with "pain" was a ground-rule question.** It wouldn't move credit assignment into the body
  (every unit gets the same signal, saying nothing about which sensor earned it; each unit's own eligibility does the
  credit assignment). But the sheet had ruled a sheet-wide taste "magic", and routed it through the T organ. In real
  brains the broadcast is brain structure: dopamine neurons receive the reward signal and project widely, a fan-out
  that costs wiring and energy and that evolution built. Two options: (A) taste enters at one unit and spreading it
  is the brain's job, grown or recruited at a cost; (B) the starting brain is born with a declared, generic modulator
  projection from the taste unit to every unit (as evolution gave us a dopamine system), costing energy like any
  connection. **Decided (the user): B for now**, declared openly; A is the harder version for later. A third,
  local variant, pain reaching only the sensors (taste sits beside them, as the sheet's T organ does), is under
  discussion below.
- **Three local questions a unit can ask**, each pointing somewhere different:
  1. *Am I involved?* (eligibility): was I active shortly before the pain? A unit that wasn't ignores it. This is
     the standard three-factor rule (a widely spread signal changes only units with a recent activity trace), and
     the designed circuit already learns this way.
  2. *Am I implicated?* Does my activity predict pain, over many events, more than my activity in general does?
  3. *Can I fix it myself?* (frustration): implicated, and adjusting myself doesn't stop it (nothing adjustable,
     or at its limit), so I need help: recruit.

  In the baseline circuit, in a red-poison life: the red sensor is involved and implicated (it was stimulated within
  10 ticks before 85% of red meals, the other sensor before 17%: "What a sensor can know", above) but can change
  nothing, so it is frustrated: recruitment should start there. The motors fire before bad *and* good tastes:
  involved but conflicted, which shows the colours were merged upstream. In all-food lives there is no pain, so
  nothing is implicated, frustrated or recruited.
- **Recruited units as bridges (the user's idea), and the decisions on it.** The poison sensor is reliable but
  powerless: it knows (its activity predicts pain) but cannot act. The motors act but cannot know (they fire before
  good and bad meals alike). A recruited unit is the learnable link between them: a wire with a memory rather than a
  new neuron (in level-0 terms the distinction dissolves), much as NEAT's "add node" splits a connection, but
  triggered by local frustration instead of random mutation. Decided:
  - **pain reaches only the sensors** (taste sits beside them, as the sheet's T organ does), replacing B; so the
    bridge is one-sided: the frustrated sensor's signal travels down its own outputs, the sheet's path growth
    reversed (there the target sent the field; here the source signals, along wiring it already has);
  - **a new, generic unit is created on demand**, placed by the local rule (equivalent to a reserve of spare cells);
  - **a ladder, measured from the bottom:** rung 0, adjust myself (intrinsic) while that still helps; rung 1, recruit
    a bridge when I am reliable but powerless; rung 2, recruit a feature (a conjunction detector) when nothing
    upstream predicts reliably. **Recruit only when self-adjustment is exhausted**: for a simple unit, roughly "my
    knobs are at their best on average, and the pain continues", cascade-correlation's trigger (add a unit when the
    error stops falling) made local; or, with synapses that track their own uncertainty, "confidently settled and
    still implicated".
  - Principles: insert transparently (a new bridge first passes the signal unchanged); exactly one bridge per need
    (the sheet's handshake, or mutual inhibition); hold what was learned when the pain stops (it stopped *because* of
    the bridge).
- **Locality, stated strictly (the user's corrections).**
  - *No coin toss between units.* A unit may draw a random number from its own noise (the sheet's sensors tossing
    for their side happened inside one cell), but a choice *among* units must come out of their local competition;
    nothing may compare them from outside. So recruitment starts at both sensors (the food sensor too was active
    before some poison meals, about 17% of them, against 85% for the poison sensor); the poison sensor's stronger
    evidence most likely forms its bridge first, the pain falls for everyone, and the other's recruitment dies away.
    Likewise between a sensor's two output wires: bridges start on both, noise decides which forms first, and the
    other dies away when the creature starts to veer.
  - *No unit can know it is optimally tuned*: that would need how the creature's success varies with its
    parameters, which no unit has. A unit knows its own activity, the signals on its connections, and pain only if
    pain reaches it. With pain only at the sensors, the motors have no information about success: they can't tune
    for the task, only regulate their own activity (homeostasis) or stay fixed. A unit that feels pain can only
    correlate ("when I was active, pain followed") or perturb a knob and keep changes after which pain falls. So
    "finished adjusting" means *my own adjustment has stalled (a knob at its limit, or a slow trace of its change near
    zero) while my own discomfort persists*: both observable by the unit itself.
  - *Every parameter is declared a constant (fixed at birth, with noise) or a plastic knob with a local rule.* The
    baseline circuit has constants only; rung 0 adds one knob, the sensors' excitability.
  - *Make it the structure*, as `sheet.py` does: each unit's rule sees only its own state, the signals on its own
    connections and what is delivered to it; the engine creates units and connections only when a unit's rule asks,
    attached locally to it; and a test checks that no rule reaches further.
- **De-recruitment (open).** A bridge that is no longer needed costs energy, so it should go, but not merely because
  the pain stopped. Proposed criterion: remove a bridge once it has been *transparent* (passing its signal unchanged,
  as if absent) for a long time; one holding a closed gate keeps a memory, however rarely used. Failed recruits (no
  fall in the frustration that summoned them) go too, as in ultrastability.
- **For later:** pain felt by the motors instead of the sensors. Nothing in the mechanism should depend on which end
  feels it; the bridge would then grow from the other end.

### Recruitment, step 0.2: what a unit can sense (2026-10-18)

First built as compiled rules beside the circuit (`net.py`, `net_rules/`: locality as structure, as `sheet.py` is for
the sheet), and withdrawn because they were programs, not circuit (Lessons that cut across the project); rung 0 was
rebuilt as circuit (next). What stands is the specification of the local signals a unit needs:

- **A knob is a memory: its noise comes with writing, not with time.** Noised every tick, a knob clamped at its top
  walked down; the never-tasted motors ended less excitable and explored less (all-food lives ate 2.27 per 1,000
  ticks against the baseline circuit's 3.12). With noise only on writes the adjusting circuit eats exactly as the
  baseline circuit where nothing is learned. Likewise slow averages refreshed only at events need a fade.
- **Rung 0 helps, but far from enough**: every unit's excitability a knob moved by eligibility x taste cut poison by a
  third (food:poison 1.5 against the baseline circuit's 1.0; the designed circuit 5.3 in the last third): the case for
  rung 1.
- **Confidence**: how reliably a unit's activity predicts pain (+1) or a good taste (-1), counted only with evidence:
  poison's sensor +0.46 on what it received, food's sensor -0.85, all-food sensors -0.96; the motors never taste, so
  they have no evidence.
- **Self-adjustment blinds a unit's own-spike evidence, so judge frustration on what a unit receives.** Lowering its
  excitability, the poison sensor's own involvement fell into the noise, while what it received still predicted pain;
  its knob stalled short of its limit (it moves only while the unit fires) and the pain went on.
- **Decision confidence** (the user's comparator idea): how decisively a unit decides, by *firing consistency* (the
  share of input events that made it fire: near 0 or 1 decided) and *misses* (how far a peak that didn't fire stayed
  below threshold). The poison sensor stalls exactly at the edge: firing almost never (consistency 0.03), with near
  misses (0.03). So frustration, by three local conditions: decided (the knob can't change what I do), what I receive
  predicts pain, and the pain goes on: the poison sensor, and nothing else.

### Recruitment, rung 0 rebuilt as circuit (2026-10-18)

- **Decided (the user): in the circuit brains everything is explicit circuit**, so that at any point the whole
  brain can be drawn as a circuit diagram. The rule layer (`net.py`, `net_rules/`) is retired. In a circuit locality
  is built in: a node feels only the elements attached to it. The one exception, for rung 1: *growth*. A recruited
  unit doesn't exist until it is recruited, then appears suddenly, by a declared primitive triggered entirely locally
  (by a node's own voltage) and attached locally.
- **Memory nodes** (`mixed_feedback.py`): no leak, and noise only when written (WRITE, 10% of each change), so a knob
  holds its value exactly while nothing writes it. `test_compiled.py` checks it.
- **Rung 0 in circuit** (`brains/adjusting.py`): every neuron has the same motif, an eligibility node charged by its
  own spikes and a memory node (the knob) driving a current of up to 1.4 out of the neuron (an amplifier whose bias
  current the knob sets: a gated element reading the knob, gated by it); for the sensors only, two amplifiers from the
  taste node into the knob, gated by eligibility (bad charges it, good empties it), as the designed circuit's P.
- **Measurement watches from outside** (`measure_recruitment.py`): the brain logs what went in and what each neuron did;
  the observer computes the local quantities (involvement, confidence, firing consistency, misses) over the second
  half of each life. 64 lives of 10,000 ticks:

  | | poison lives: food, poison per 1,000 (food:poison) | poison's sensor: excitability, fires, confidence (received), miss | all-food lives: food per 1,000 |
  |---|---|---|---|
  | baseline circuit | 1.57, 1.57 (1.0) | 1.00, 0.70, +0.73, 0.22 | 3.14 |
  | adjusting (circuit) | 1.46, 1.05 (1.4) | 0.34, 0.18, +0.57, 0.03 | 3.15 |

  The rule version's result (1.5) holds in circuit form: rung 0 cuts poison by a third, and the poison sensor again
  stalls at the edge (near misses, miss 0.03). The food sensor stays calm (excitability 0.98, confidence -0.89); in
  all-food lives nothing changes.
- **Rung 0 is itself one-bit learning in a life**, by intrinsic plasticity alone (no synapse changes): the poison
  sensor's knob fills, it becomes less excitable, and the creature stops driving at poison. It learns which colour to
  *ignore*, a weaker thing than the designed circuit's veering *away* (an ignored poison block is still eaten beside
  food or by drift): 1.4 food per poison against about 5. And it costs nothing when there is nothing to learn: in
  all-food lives no knob ever charges and it eats exactly as the baseline circuit, where the designed learner, its
  machinery always on, eats a fifth less. Paying only when there is something to learn is already rung 0's property.
- **Not yet tried: a knob that also makes a unit keener.** The knobs start empty (as excitable as a neuron can be
  without firing by itself, about 0.2 of bias short of that), so good tastes can't push further. A knob starting
  mid-range could move both ways: keener on what tastes good, which might help even in all-food lives.
- **The motors' conflict, seen from outside.** In the baseline circuit the motors are involved before every taste
  (involvement 1.00) with confidence exactly 0.00: equally before good and bad (exactly, as lives are paired). The
  motors can't know this themselves (they feel no taste); the observer can.

### Recruitment: a starting animal that may know but can't act (2026-10-18)

- **A cleaner test (the user's).** In the rung-0 animal each sensor could change its own behaviour (ignore what
  predicts pain), so the starting animal could already learn a little. Instead: the baseline circuit plus a taste
  neuron T that can *learn* what predicts pain but has *no outputs*. It may know, and must recruit in order to act.
  What it learns is a prediction, available before contact, which is what avoiding needs; its frustration is crisp
  ("I predict pain confidently and it still comes"); and one "danger" signal serves any poison colour. The sensors'
  own knobs (rung 0) go; pain reaches only T, the taste organ. Rung 0 stays on record as the earlier variant.
- **The knowing circuit** (`brains/knowing.py`), all circuit: T fires innately at a bad taste (an amplifier from the
  taste node), and through a plastic synapse from each sensor whose strength is a memory node, charged by a bad
  taste and emptied by a good one while that sensor was recently active (the designed circuit's P motif, on the
  sensor-to-T synapses). 64 lives of 10,000 ticks (`python measure_recruitment.py 64 10000 knowing`):

  | | poison lives | all-food lives |
  |---|---|---|
  | behaviour | food 1.58, poison 1.58 per 1,000 (1.0, as the baseline circuit) | food 3.16 per 1,000 (as the baseline circuit) |
  | T's synapses | from poison's sensor 0.87, from food's 0.13 | 0.00 |
  | T anticipates (a spike within 10 ticks before the taste) | 96% of poison meals; 51% of food meals | (no poison); 19% of meals |
  | T's confidence (when it fired before a meal, the meal was poison) | 0.66 | 0.00 |

  Knowledge leaks nowhere (behaviour as the baseline circuit's). T learns the association, and anticipates nearly every
  poison meal; its false alarms are about chance at its rate (about 50 spikes per 1,000 ticks, against 18 in all-food
  lives, which is its own spontaneous firing): red blocks are often in view on the way to a blue one, so T has become
  a "danger in view" detector, which is arguably the right signal for avoiding. Frustrated by the test (confident,
  pain going on) in poison lives; calm in all-food lives.

### Recruitment, rung 1: growing the link that lets knowledge act (2026-10-18)

The full record, with methods, tables and working, is `experiments/NOTEBOOK.md` (E0-E6); in brief:

- **It works.** The recruiting circuit (`brains/recruiting.py`) starts as the knowing circuit: its taste neuron T learns
  what predicts pain but has no outputs. Circuit only, plus one growth primitive: frustration F at T ("I predicted
  this pain and it came anyway"); help routed back along T's input synapses, only to a sensor whose synapse predicts
  pain and only while frustrated; competing sprouts on each sensor's output synapses; and, when a sprout passes its
  level, a bridge splitting that synapse (a relay held down while T has fired lately, so the creature veers from
  danger). On held-out lives it grows exactly the oracle's structure in 61 of 64 poison lives, nets +1.00 food per
  1,000 ticks over the knowing circuit (oracle at birth +1.15; the gap is only the time before growth, about 1,700
  ticks: a time-matched oracle does no better), and grows nothing in all-food lives, where a built-in bridge costs.
- **Essential**: routing by what each synapse onto T learned (without it, bridges land on the food sensor: veering
  from food); competition among a neuron's sprouts (without it every sprout grows); help as a logical AND (predicts
  pain, and frustrated); a sprouted neuron stays changed (one bridge per neuron). Frustration needs both knowledge and
  unprevented pain, so chance frustration grows nothing.
- **Methods**: oracle structures as ceilings; paired lives with per-node noise streams (`Circuit(streams=True)`):
  before them, two variants of different sizes differed by chance as much as by design; quiet slow nodes (a slow
  integrator's capacitance must grow as the square root of its time, or noise swamps it); held-out lives to confirm
  choices; and every script pinned to the settings it ran.
- **Power, corrected**: by the worst case (every amplifier fully biased) the recruiting circuit seemed to need half the
  designed circuit's static power; by the more physical gated average (a gated amplifier's bias set by its gate) it
  needs about 1.7 times as much, and nearly half of that is the one-bridge-per-neuron inhibitor holding a losing sprout
  at 0 with an ungated, full-strength current for ever. Fix to test: growth closes that sprout's charging gate instead.
  Big currents go with big quiet capacitors (current = C x rate), and gating is what makes them affordable.
- **A bug found and fixed**: `start = moving or ticks` treated a creature that moved at tick 0 as never moving
  (measurement only; no earlier result was affected).
- **The bridge's link to the taste neuron was a non-local shortcut** (the user noticed it looked unconnected in the
  block view): the growth rule attached the bridge's hold to `self.T`, knowledge the circuit didn't have. Replaced
  (E7) by a local hold, charged by the sensor's own spikes gated by its synapse onto T; better as well as more local
  (+0.11 [+0.03, +0.19] net food, pooled over 128 lives; last-third food:poison about 5), because the creature now
  veers only when the poison sensor fires, not at T's false alarms. The growth rule now needs to know only where the
  winning sprout is. Lesson: when a growth or wiring rule names a part ("connect to T"), ask how the circuit itself
  would find it.
- **Found on the way: the neuron is fragile to mismatch.** 5% random error in every gain and bias costs both the recruiting
  circuit and the designed circuit most of what they learn. All of it comes from the neuron's own fast and slow elements and its
  bias; mismatch in the whole recruitment machinery costs nothing. The neuron cancels two equal elements at rest and
  sits 0.38 V below threshold, so 5% moves its rest by up to 70% of the margin: a precise-parts design, to be
  redesigned for margin.

### Recruitment: a generic recruit that knows nothing (the healing circuit, 2026-10-19)

`brains/healing.py`; the H series in `experiments/NOTEBOOK.md`; `experiments/LEADERBOARD.md`. The user's design: a
frustrated unit grows a recruit that attaches to it and its one-edge neighbours, sees their signals, learns which
connection, treated how, reduces frustration, and if it fails is frustrated itself, so the next recruit reaches one
edge further: "an inflammation/healing response". The recruit knows nothing of what the circuit does: it gets a
menu (inhibit or excite each attached neuron, turn down a synapse) and a local rule for choosing.

- **A recruit that knows nothing matches the guided bridge.** Win-stay lose-shift in circuit (enables that latch,
  pairwise rivalry, tiredness that knocks an option out), listening to everything attached, a menu of inhibiting and
  gating: +1.16 net food per 1,000 ticks against +1.16 for rung 1's guided bridge (held out, paired -0.06 [-0.13,
  +0.03]), choosing "gate the poison eye's synapse to a motor" out of seven options in every life.
- **Judge an option by the share of bad tastes after it, not their rate.** Judged by rates (tiredness fading with
  time), an option was still being switched at tick 70,000-90,000, and anything that made the creature do less looked
  like a cure. Judged by share (tiredness that hardly fades while the option is on, a step up per pain, half a step
  down per good taste), it settles by tick 8,000-13,000 after 3-5 switches, and the last third's food:poison doubles
  (4.4 to 7.0, held out; the guided bridge 3.7). But a share can't judge an option followed by no tastes at all.
- **Choosing is the slow part, not waiting for frustration.** T is frustrated 1,000 ticks into a life. The user's
  idea of recruiting early and learning "in shadow mode" moved nothing measurably: a shadow can learn what to listen to,
  not which action helps, which needs acting. And a shadow gated by the parent's frustration withdraws the recruit as
  soon as its help calms the parent (a fix that undoes itself); commissioning it for good (a memory node) fixes that.
  Passing knowledge forward does help: a recruit whose listening is gated by its parent's own learned memories
  ("inherit") beats one learning from scratch (+0.92 to +1.05).
- **Doing nothing well beats doing something precisely.** Listening to everything attached beat learned listening: R
  then acts constantly, so win-stay lose-shift gets many trials; and for a gating action, firing too often costs
  nothing. The action's target gives the selectivity (the local hold's lesson again). Committing to one option beat
  graded blending (a REINFORCE-like rule kept harmful options on beside good ones: +0.16 at best).
- **Wireheading is real.** Recruits learning from anticipated pain only chose to silence T five times as often:
  recruits must learn from pain itself.
- **The cascade works when the cure is one edge further.** With a menu of the synapses arriving at attached neurons,
  wave 1 (on T and the eyes) can do nothing useful; still frustrated 10,000 ticks later, it is frustrated itself, and
  wave 2, reaching the motors, gates the poison eye's synapse in about 60% of lives. Its failures: a neuron-level
  cure (inhibit a motor while the poison eye fires) is a real veer but costs half the meals (turning needs the motor
  off for 10 ticks, and a shorter hold loses the veer); with full listening it froze the creature; and wave 1's last
  option stays on after wave 2 cures the poison, and then looks good, even when harmful (credit leaking between waves).
  Best so far (+0.66, last third 4.9): every wave frustrated by the first unit's own flag, and "starve" (while an
  option is on its tiredness creeps up, eased only by good tastes, so a freeze is knocked out within 20,000 ticks).
- **De-recruitment by retiring failed in every form.** A recruit frustrated enough to recruit stood down for good;
  but while the pain lasts every recruit reaches that point, the last one too, and then no one acts. What standing
  down should mean (may the last recruit? a cap on waves would be a hidden size) is open; a recruit that walks would
  release its old action as it moves (`RECRUITMENT.md`, future work).
- **Power: choosing cost more than acting.** A generic recruit added about 1,200 units of gated static power (the
  guided bridge about 200), most of it the enables' pairwise rivalry: n(n-1) ungated elements, fully biased for ever.
  Gating each latch, rivalry and knock-out element by its own source cut it to about the guided bridge's (gated
  average 550 against 528), with behaviour unchanged. Gate every element by the node whose state it reports.
- **Open: level 1 has no rules (the user's question, 2026-10-20).** Level 0 is strict (nodes and elements only), but
  the parts built from them are invented as needed. A grown healing circuit has 48 nodes and 128 elements, of which 6
  are neurons; the other 42 are about eight unnamed kinds (eligibility trace, weight, pulse, slow level, comparator,
  latch, resting-open gate, hold). The block view draws them all as the same meter, though some are states belonging
  to a neuron or synapse and others are functional units in their own right. And half the recruit (21 nodes, about
  60 elements) is machinery for choosing among 7 options, while its choice of where to connect is trivial: the
  decisions sit inside complicated parts, not in how simple parts connect. A proposal: a small catalogue of level-1
  parts, each with named ports, a glyph and rules for what may connect to what. The parts: a neuron, with its own
  adaptation; a synapse, with its weight, eligibility and an optional gate (presynaptic inhibition); and a modulator,
  a diffuse signal like ouch and yum. The rules, for example: only neurons send spikes, and a weight changes only when
  eligibility and a modulator coincide (three-factor learning). Growth would add only catalogue parts, connected port
  to port. Win-stay lose-shift would become 7 mutually inhibiting neurons whose adaptation is the tiredness
  (winner-take-all with adaptation, the textbook rivalry circuit). The test: rebuild the healing circuit from the
  catalogue and check it still learns, then redraw the block view to match, before a harder test bed makes the
  structural choices real.
