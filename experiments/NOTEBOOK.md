# Lab notebook: rung 1 of recruitment

*Names (2026-10-18): the "grown brain" is now the **sheet brain**, and the "mixed-signal brain" the **designed circuit**; the minimal, adjusting, knowing and recruiting brains are the **…-circuit** brains. Earlier entries keep the names they were written with.*

Rung 1 (RECRUITMENT.md): the knowing brain (brains/knowing.py) learns what predicts pain in its taste neuron T, but T
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
| E5 | How does it compare? | Grown against oracle against designed; both starting animals; cost |

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
- **Common random numbers.** The recruiting brain with growth off ate 3.49 food per 1,000 ticks in all-food lives
  against the minimal brain's 3.14, intervals not overlapping, though its extra nodes have no outputs. Paired by seed,
  the difference was +0.34 with a standard deviation of 1.00: paired lives were uncorrelated, because all nodes drew
  noise from one stream and adding nodes reshuffled the sensors' and motors' noise. The noise stream, not the seed,
  decides a life. Fix: each node draws from its own stream, seeded by its index (`Circuit(streams=True)`, used by the
  recruitment brains; the grown and mixed-signal brains keep theirs, so their lives are unchanged). Then the minimal,
  knowing and recruiting-without-growth brains live *identical* lives (paired difference 0.00, standard deviation
  0.00): nothing in the extra circuitry leaks into behaviour, and the +0.34 was chance. Lessons: at 64 lives two
  independent noise streams differ by about 0.15 food per 1,000 ticks by chance alone (the minimal brain's own figure
  moved from 3.14 to 3.02 with the change of stream), so unpaired comparisons of different brains are weak; with
  common random numbers, variants are compared life for life.

## E1: oracle structures (2026-10-18)

*Question.* If recruitment produced the ideal structure, which structure is it? *Method.* Each candidate placed by
hand at birth by an oracle that knows the poison colour (recruitment never will), the rest as the knowing brain.
`python -m experiments.e1_oracle 64`; results/e1.txt.

| structure | food:poison [95%] | last third | net food vs knowing, poison lives | all-food lives |
|---|---|---|---|---|
| none (knowing) | 1.00 [0.92, 1.09] | 1.00 | | |
| O1: a bridge on one of the poison sensor's synapses | 2.87 [2.63, 3.14] | 3.47 | +1.07 [+0.93, +1.22] | -0.19 [-0.42, +0.03] |
| O2: a bridge on one of the food sensor's synapses | 0.33 [0.28, 0.39] | 0.20 | -0.99 [-1.17, -0.82] | -0.16 [-0.37, +0.06] |
| O3: bridges on both of the poison sensor's synapses | 1.85 [1.71, 1.99] | 2.12 | +0.78 [+0.61, +0.94] | +0.30 [+0.10, +0.50] |
| O4: bridges on all four synapses | 1.69 [1.52, 1.87] | 2.08 | +0.55 [+0.39, +0.71] | +0.30 [+0.10, +0.51] |
| O5: T's hold inhibits one motor (colour-agnostic) | 1.63 [1.41, 1.88] | 1.78 | +0.23 [+0.08, +0.39] | -1.28 [-1.49, -1.09] |
| designed (mixed-signal), for reference | 4.18 [3.78, 4.64] | 5.32 | +1.02 [+0.86, +1.18] | -0.52 [-0.76, -0.28] |

*Findings.* (1) O1 is the target: one bridge, on the poison sensor, on one of its two motor synapses, nets as much
food as the designed brain (+1.07 against +1.02; intervals overlap), with a lower ratio (2.9 against 4.2) because it
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
lives? *Method.* Paired with the knowing brain (growth off) and the oracle O1. `python -m experiments.e3_growth 64`;
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
| designed (mixed-signal) | -0.72 [-0.90, -0.52] | -1.04 [-1.25, -0.82] |

Both lose most of what they learned at 5%: the opposite of "robust through balance". *(e) Which mismatch?* (R3, 5%,
one class of parameter at a time):

| mismatch in | net food change |
|---|---|
| each neuron's own fast and slow elements | -0.66 [-0.90, -0.43] |
| node biases | -0.37 [-0.53, -0.21] |
| everything else (synapses, learning, frustration, routing, sprouts, growth) | -0.01 [-0.15, +0.13] |
| all | -0.64 [-0.90, -0.40] |

The recruitment machinery is robust; all the fragility is in the neuron, shared with (and inherited from) the
mixed-signal brain. Working: its fast positive and slow negative elements have equal strength (2.0) at the same offset,
cancelling exactly at rest, which leaves it 0.38 V below threshold (rest -3.2, threshold -2.82), with a bias 12% from
firing by itself (-1.6 against -1.41). A 5% error in either strength leaves about +/-0.13 of net current at rest,
shifting rest by about +/-0.26 V, up to 70% of the margin: a precise-parts design. A neuron whose rest moves toward
threshold fires more by itself; for the taste neuron that means false "danger", which explains the extra food-sensor
bridges under mismatch (23 against 2). The fix belongs to the neuron (a design that keeps its margin under
mismatch), a change of substrate outside rung 1.

*(d) Cost* (at the end of one poison life): minimal 5 nodes, 12 elements, sum of gains 20; knowing 10, 23, 49; R3
22, 42, 531; designed 11, 24, 1,006. The sum of gains approximates static power in the worst case (each element an
amplifier drawing about its gain as bias current, all fully biased). *Corrected (the user asked for detail):* a gated
amplifier's bias is set by its gate, so the more physical measure is gain x gate, averaged over the second half of a
life. Worst case / gated average: minimal 20 / 20; knowing 49 / 48; designed 1,005 / 264; R3 531 / 412; R4 650 / 456.
So R3 needs about half the designed brain's power only in the worst case; by the gated average R4 needs about 1.7
times as much. Breakdown: big currents go with big quiet capacitors (current = C x rate: the designed brain's
learning amplifiers into P, C = 1,000, gains 231 each; R4's frustration charger into F, C = 775, gain 298); gating
makes them affordable (the designed brain's 923 averages 182, gated by eligibility; R4's charger 298 averages 107);
and the one-bridge-per-neuron inhibitor wastes power, holding the losing sprout at 0 with an ungated, full-strength
current (gain 200, for the sprout's big capacitor) for ever: nearly half of R4's power. Untested fix: let growth close
the gate on the losing sprout's charging amplifier (re-gate it with a memory node at 0) instead of fighting it with a
current: the same effect at no running cost, bringing R4 to about 256, level with the designed brain. Dynamic power
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
E5b. Adopted: R4 is the recruiting brain's default. And on these lives the hand-placed bridge costs significantly in
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
   times the designed brain's (gated average), nearly half of it a wasteful always-on inhibitor (E5d, with a fix).
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
for the same reason, T firing too often). Last-third food:poison 4.9-5.7, as good as the designed brain's (5.3).
Adopted: the local hold is the default; the growth rule now needs nothing beyond the synapses of the neuron it grows
from. (Hand-placed local bridges eat more in all-food lives, +0.46 and +0.12 against the knowing brain: with W near 0
the local hold never holds, and the bridge neuron's own spontaneous spikes add exploratory kicks, E1's confound.)

## Conclusions, revised after E7

The recruiting brain (defaults: sharp routing, one bridge per neuron, frustration rise 0.5, growth level 0.6, local
hold) grows exactly the oracle's structure in about 62 of 64 poison lives, nets about +1.1 food per 1,000 ticks over
the knowing brain with last-third food:poison about 5, and grows nothing in all-food lives. Everything is circuit
except the growth primitive, and the primitive now needs to know only where the winning sprout is: the bridge
connects to the synapses of the sensor it grows from and nothing else.
