# Lab notebook: rung 1 of recruitment

*Names (2026-10-18): the "grown brain" is now the **sheet brain**, and the "mixed-signal brain" the **designed circuit**; the minimal, adjusting, knowing and recruiting brains are the **…-circuit** brains. Earlier entries keep the names they were written with. (2026-10-21: the minimal circuit is now the **baseline circuit**, `baseline-circuit`, so that "minimal" means only the minimal circuit search; the printed results in `results/` keep the old label.)*

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
  gains scaled to keep its time and rates. Physics, not tuning: the same disease as the knobs' drift (LESSONS), cured
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
first tick. Fixed in experiments/common.py, creature.py and recruit_test.py; it had affected no earlier result (no
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
weak synapse (false alarms before about half of food meals, `LESSONS.md`), and each time the T hold makes the creature
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
