# Mixed feedback

What the "mixed-feedback" approach of Rodolphe Sepulchre and colleagues is, what is new and valuable in it, what is
not, and what it suggests for this project. Written from a literature search in October 2026. The core paper
(Ribar and Sepulchre 2021) was read in full; most others from their abstracts or summaries, so details of those
should be checked against the papers before relying on them. References are numbered at the end.

## In one paragraph

Engineering has kept positive and negative feedback apart: negative feedback for robust, linear, analog regulation
(Black's amplifier), positive feedback for switches, memory and clocks (latches, oscillators, digital logic).
Nervous systems don't separate them: in every neuron, fast positive feedback (sodium) makes a discrete event, a
spike, and slower negative feedback (potassium) ends it and keeps it regulated. Sepulchre's group argues that this
**interlocking of positive and negative feedback at separated timescales** is a control principle in its own right,
and the reason neurons are at once digital (spikes are reliable, countable events) and analog (thresholds, rates and
rhythms are continuously tuned), robust to sloppy parts and easy to modulate. They turn it into a design method: a
circuit is a capacitor in parallel with a few identical elements, each giving positive or negative feedback in one
voltage window and one timescale, and a behaviour (resting, spiking, bursting, rebound, rhythm) is designed by
shaping the circuit's current-voltage curve as seen at each timescale [1, 2, 3].

## The building blocks

The circuit of [1, 3] (their Figure 3), which `mixed_feedback.py` follows:

- **A node**: a capacitor C in parallel with a *passive* resistive element whose current rises with voltage
  everywhere (dI/dV > 0: a leak; the "monotone backbone"), plus any injected current.
- **A feedback element**: a current into the node, a static saturating function of a low-pass filtered voltage,
  `I = ±α tanh(Vx − δ)`, `τx dVx/dt = V − Vx`. α sets its strength, δ the voltage window where it acts, τx its
  timescale, the sign whether it is a negative conductance (positive feedback) or a positive one (negative feedback).
  Every element is **localised in amplitude** (tanh saturates outside its window) and **localised in time** (one τ).
- **A synapse**: the same element reading another neuron's voltage, with a sigmoid: `I = α S(β(Vx − δ))`, excitatory
  or inhibitory by the sign of α [1, eq. 17]. The only difference between an ion channel and a synapse is whose
  voltage it reads. Resistive (gap-junction) couplings between nodes are also allowed.
- **In hardware**, both are standard subthreshold parts of Mead's neuromorphic engineering [4]: the
  transconductance amplifier, whose output current is `ib tanh((v1 − v2)/2v0)` with its gain ib set by a bias
  voltage, and the follower-integrator (the same amplifier driving a capacitor), whose time constant is set by its
  bias [1]. So each element is a voltage-controlled current source with a programmable gain.

Elements are grouped by sign and timescale: fast (as fast as the membrane, often instantaneous), slow, ultra-slow,
with `τ_fast ≪ τ_slow ≪ τ_ultraslow`. A neuron is named by which of `I−f, I+s, I−s, I+us` it has.

## What is new

### 1. Positive feedback is a design element, not a hazard

The historical split [1, sidebar "Positive and negative feedback"]: negative feedback became the basis of robust
design with unreliable parts; positive feedback was confined to bistable switches and oscillators. A static
saturating plant shows the continuum: negative feedback linearises it and lowers its sensitivity; positive feedback
raises sensitivity until, at a critical gain, it becomes ultrasensitive, and beyond it bistable (hysteresis: a bit).
Excitable systems live on this continuum, with positive and negative feedback present together but acting at
different speeds [1, 5]. The claim is that the mix, not either alone, gives robustness and flexibility together.

### 2. Behaviour is read off current-voltage curves at each timescale

Because currents add (the elements are in parallel) and timescales are separated, the circuit can be analysed one
timescale at a time with slower currents frozen. Define the I-V curve at timescale τx as the passive curve plus every
element as fast as τx or faster. Then [1]:

- **Excitable** (one spike per input pulse above threshold): the fast I-V curve is N-shaped (a window of negative
  conductance: fast bistability) and the slow I-V curve is monotone (negative feedback restores it).
- **Spiking**: the same, with the resting point inside the negative-conductance window.
- **Bursting**: the same motif repeated one level slower: an N-shaped slow curve (slow positive feedback, `I−s`) and
  a monotone ultra-slow curve (`I+us`), with the slow threshold below the fast one.
- **The rest-spike transition** (Hopf or saddle-node, so a discontinuous or continuous frequency curve) is set by
  whether the fast and slow curves' turning points line up.

This turns nonlinear design into something like classical loop shaping: each element shapes one curve in one
window, and the conditions are graphical. The Hodgkin-Huxley model, linearised, has exactly this structure (sodium
activation: fast negative conductance; sodium inactivation and potassium: slow positive) [1]. Bursting neurons
repeat it slower (calcium: slow negative; calcium-activated potassium: ultra-slow positive) [1, 6].

### 3. Spikes are mixed signals: physical system and automaton at once

Digital control separates physical systems (continuous) from automata (discrete), joined by clocks and
quantisers. A spike is both: a continuous-time physical trajectory that can also be counted as a discrete event [2,
7]. Fast positive feedback gives the event digital reliability (its timing is precise and survives noise), slow
negative feedback gives analog regulation. Neurons combine analog adaptation with digital reliability, without a
clock, which is what Sarpeshkar argued is the efficient regime for noisy hardware [8]. Recent work extracts
discrete-event (automaton) models from the continuous circuits [9] and adapts describing functions and phase
response curves to excitable systems via an operator from input event trains to output event trains [10].

An early demonstration: the "neuron servo" of DeWeerth, Nielsen, Mead and Åström (1991), a PD controller whose
output drove a motor through two spike generators, acted like pulse-width modulation at high speed and like a
stepper motor at low speed, where each pulse carried enough energy to overcome static friction that defeated the
analog controller [1].

### 4. Robustness through balance, not precise parts

The behaviour depends on the *balance* of positive and negative conductance in each timescale and voltage window,
not on any single parameter, which gives a highly redundant tuning mechanism robust to large uncertainty in each
element [1, 11]. This matches neurophysiology's degeneracy: similar activity from very different conductance mixes
(Prinz, Bucher and Marder 2004 [12]), and firing rates robust and tunable because many channels contribute to the
same feedback [11]. For analog chips, where transistor mismatch has been the field's main hurdle for decades, this is
the selling point: "turn the variability of transistors into a feature rather than a hurdle" [1]. A 180 nm silicon
neuron built on the architecture (three timescales, current mode) reports robustness across currents and temperatures
[13]; earlier, robust switching between spiking modes in resistor-capacitor-transistor circuits [14] and SPICE
simulations of weak-inversion transistor circuits [3].

### 5. Modulation is control

The natural control inputs are the elements' maximal conductances (α), which is exactly what neuromodulators change
in real neurons. So neuromodulation is controller design, "loop shaping" of the feedback balances [1, 3, 15]:

- **One parameter switches the kind of behaviour.** The slow negative conductance (`I−s`) alone moves a neuron
  between slow spiking and bursting (through a pitchfork at the aligned thresholds) [1, 6]. Many textbook bursting
  models lack any slow negative conductance, which is why they cannot reproduce this transition [1].
- **Nodal mode and network mode.** A slow-spiking neuron relays each input spike (nodal mode); a bursting one ignores
  single spikes and joins the network's slow rhythm (network mode) [1]. In a population, a switchable slow cellular
  conductance turns network rhythms on and off largely independently of size and connectivity, decoupling fast
  global state switches from slower tuning by plasticity or homeostasis [16]; positive feedback at the cellular level
  makes circuit rhythms both robust and modulable [17].
- **Functional topology without rewiring.** In a five-neuron network modelled on the crab stomatogastric ganglion,
  switching nodes between modes connects and disconnects whole rhythms, changing the network's functional topology
  while its wiring stays fixed [1, 18].
- **Intrinsic as well as synaptic.** Artificial neural networks control synaptic weights; these papers argue that the
  modulation of each node's intrinsic feedback balance is an equally powerful lever [1].

### 6. Networks from the same motif

Post-inhibitory rebound (a spike or burst on release from inhibition, from a slow negative conductance active at low
voltage) lets two mutually inhibiting neurons make an anti-phase rhythm though neither oscillates alone (the
half-centre oscillator) [1, 17]. Generalised: all-to-all inhibition between rebound-excitable neurons gives
winner-take-all dynamics, a discrete state machine whose transitions are continuously tunable, used to design
central pattern generators with adaptive phase and frequency [19] and proposed as the "rebound winner-take-all"
motif of a scalable event-based control architecture, demonstrated on a snake robot [20]. The same mixed feedback in
space (short-range excitation, longer-range inhibition) as well as time gives a model of excitability across scales,
from cells to population events [21]. A pendulum controlled by event-based actuation and sensing (a rhythmic
automaton plus a regulator of event timing) shows the approach on a physical plant [22].

### 7. A theory to go with it

- **Maximal monotonicity** generalises passivity to nonlinear, incremental behaviour, and links circuit physics,
  convex optimisation and feedback theory. A negative-conductance element is not monotone, but it is the *difference*
  of two monotone operators, so a spiking circuit is a monotone backbone with a few localised, disciplined departures
  from it [2, 23].
- **Dominance theory** (p-dominance, differential dissipativity) generalises stability to systems whose long-run
  behaviour is low-dimensional: 1-dominant systems have equilibria or limit cycles only, giving tools for
  multistability and oscillation [24].
- **Simulation.** Monotonicity also gives algorithms: operator-splitting methods whose structure mirrors the circuit's,
  proposed as better than conventional ODE integration for multiscale neuromorphic events [25].
- **Estimation.** Conductance-based models are linear in their maximal conductances, so adaptive observers can learn
  them online from voltage (recursive least squares, with contraction-based guarantees) [26].

## What is not new

- The parts: subthreshold amplifiers and follower-integrators are Mead's, from the late 1980s [4]; silicon neurons
  date from Mahowald and Douglas 1991.
- Excitability as fast positive and slow negative feedback: FitzHugh-Nagumo (1961-62), and Hodgkin-Huxley before it;
  bursting as a slower copy: Hindmarsh-Rose (1984) and the classic bursting literature.
- Half-centre oscillators (Graham Brown, early 1900s), post-inhibitory rebound, and neuromodulation as the source of
  circuit flexibility (Marder and colleagues over forty years [12, 15]).

What is new is the synthesis: a single element type, localised in voltage and time, as the universal component; the
classification of every current by sign and timescale; I-V curves per timescale as the design tool; modulation of
feedback balance as the control input; and a control theory (monotonicity, dominance) under it. The claim is less "a
new circuit" than "a way to design circuits that are digital and analog at once, and robust because they are
balanced rather than precise".

## How mixed-feedback is different from today's classic deep learning approach

Deep learning [37] and mixed feedback both descend from neurons, but took opposite halves of them.

| | deep learning | mixed feedback |
|---|---|---|
| the unit | a fixed, memoryless nonlinearity (ReLU, sigmoid) | a node with its own dynamics: positive and negative feedback at several timescales |
| signals | numbers, passed in layers or steps | continuous voltages and spikes: events in continuous time, no clock |
| time | discrete steps; memory added as explicit state (recurrence, attention over a context) | intrinsic: every element has a timescale, and memory is held in slow variables and bistability |
| where adaptivity lives | synaptic weights only; the neuron never changes | intrinsic conductances as much as synapses: modulating one changes the *kind* of behaviour (relaying or bursting), not just a gain |
| how it is set | gradient descent on a loss, offline, over huge data | designed by shaping I-V curves, and tuned by modulation; no general learning method yet |
| noise and imprecision | needs precise arithmetic (reduced precision is an engineering trick) | robust through balance, so noisy, mismatched analog parts are acceptable |
| hardware | digital, clocked, energy-hungry (GPUs) | subthreshold analog: currents and charge do the arithmetic, at very low power |
| understanding | behaviour spread over millions of weights | each element has a meaning (positive or negative feedback, in one window, at one timescale) |
| what it does today | vision, language, games, at scale | small circuits: spiking, bursting, rhythms, event-based control of simple plants |

The main differences:

- **Neurons that compute, not just sum.** In deep learning the neuron is a fixed function and everything learned is a
  weight. In mixed feedback the node is itself a small dynamical system that can switch between qualitatively
  different behaviours, so much of the computation and adaptation is inside the nodes [1].
- **Events and analog regulation at once.** Deep learning is digital throughout. Mixed-feedback circuits make
  discrete, reliable events (spikes, bursts, winner-take-all decisions) from continuous physics, and keep the
  continuous tuning of their thresholds and rhythms [2, 20].
- **Robust by construction rather than by precision.** Deep networks rely on exact arithmetic for training and
  inference. Mixed-feedback behaviour depends on a few balances with wide margins, which is what makes noisy analog
  hardware usable at all [1, 13].
- **Time is native.** A deep network sees time only as a sequence of steps or a window of context. A mixed-feedback
  circuit lives in continuous time, and its timescales (fast, slow, ultra-slow) are its structure.

Spiking neural networks sit between the two: they use spikes and are trained by gradient descent (with "surrogate
gradients" smoothing over the spike's discontinuity [38]), but their neurons are usually simple leaky integrate-and-fire
units and adaptation is still in the weights, so the intrinsic, mixed-feedback half is mostly absent.

The honest comparison runs the other way too. Deep learning has a general, scalable learning method and solves real
problems at scale; mixed feedback has a design method and robust small circuits, but no general way for a circuit to
learn. Gradient descent is awkward here: the behaviours that matter (a spike, a switch to bursting) are bifurcations,
where gradients are discontinuous or huge. That gap is what this project's two routes address: a brain that grows and
learns by local rules, and circuits shaped by evolution, which needs no gradients.

## Learning: what the literature covers, and what it doesn't

- **Modulation, not learning.** In these papers the conductances are set by a designer or an external controller
  (neuromodulation); the circuits show *what modulation can do*, not how a circuit could find good settings itself.
- **Estimation.** Adaptive observers learn a circuit's conductances from its voltage [26]: system identification,
  not learning a task.
- **Adaptive sensitivity in decisions.** Franci, Leonard and colleagues' nonlinear opinion dynamics use the same
  saturating feedback, with state feedback on an "attention" parameter that adapts sensitivity [27].
- **Bursting and plasticity.** Drion's group finds that switching a network from tonic firing to bursting pulls
  synaptic weights into an attractor set by the plasticity rule, a controllable consolidation stage [28].
- **What I could not find**: a mixed-feedback circuit that learns a task from reward within its lifetime, or any
  evolution or automatic design of Ribar-Sepulchre circuits. This project's designed circuit (a three-factor rule
  built from the same elements, learning from one taste signal) sits in that gap.

## Related work from evolutionary robotics

Closest in spirit to evolving such circuits:

- **Continuous-time recurrent neural networks (CTRNNs)**, evolved for adaptive behaviour by Beer and colleagues since
  the early 1990s [29]: leaky nodes coupled through sigmoids, which is this project's level 0 without input filters,
  gates or clamps.
- **Learning without plasticity**: CTRNNs with fixed weights evolved to learn within their lifetime, with the learning
  held in their dynamics [30, 31] (a temperature-food association, much like food and poison here).
- **Evolved neuromodulated plasticity**: networks given modulatory neurons that gate plasticity evolved to use them,
  and learned better in reward-based tasks [32, 33]; the gate in `mixed_feedback.py` is that idea in circuit form.
- **NEAT**: evolving topology by starting minimal and growing, with historical markings for crossover and speciation
  to protect new structure [34].
- **The simulator is never part of the solution**: Thompson's FPGA evolved a tone discriminator that depended on
  unconnected cells and the chip's physics [35]; Jakobi's "radical envelope of noise" hid what a simulation models
  badly inside noise, so evolved controllers couldn't exploit it [36]. Both bear on the defences in `LESSONS.md`.

## What it suggests for this project

- **Our element is theirs, with three additions.** `mixed_feedback.py` has their node and element (tanh or sigmoid
  of a filtered voltage) and adds a **gate** (a third node scaling the current, so modulation is a signal inside the
  circuit rather than a parameter set from outside), **clamps** and **perfect integrators** (no leak). The gate is how
  learning lives in our circuit; clamps and integrators are idealisations their framework avoids: every node has a
  passive, monotone resistive element. That is the same rule as "every node must leak" proposed for evolution.
- **Coordinates for evolution.** Describe elements by sign and timescale band (fast, slow, ultra-slow, separated by
  a factor of several) and by voltage window, not as free parameters; behaviour changes kind at known boundaries of
  balance, so the search space has meaningful axes.
- **Cheap analysis before simulation.** The I-V curves at each timescale are static and quick to compute: a circuit
  whose motor nodes have no N-shaped fast curve can't spike, and need not be simulated.
- **Learning as modulation.** The designed circuit learns a synaptic gain (P gates a synapse). The literature suggests
  learning could equally shift a node's intrinsic balance, for example a slow negative conductance switching a neuron
  between relaying and ignoring its input: a lever an evolved circuit might find.
- **Robustness as a test.** Their central claim is robustness to mismatch through balance. An evolved circuit should
  keep working with every parameter a few percent off at birth; that is both a defence against overfitting the
  simulator and a check that it has found a mixed-feedback solution rather than a fine-tuned one.
- **Our behaviour is events driving kicks**, like the 1991 neuron servo: each motor spike is a fixed kick, so the body
  is driven by event timing and rate, the regime this literature is about.
- **Not yet used here**: slow positive feedback (bursting), rebound, winner-take-all, resistive couplings. The hush
  between our sensors is a crude winner-take-all; a rebound winner-take-all [19, 20] is its principled form.

## How the simplest circuits found map onto it (2026-10-21)

The user's question: had we started from Sepulchre's components alone, would we have reached circuits as simple and as
effective as the minimal circuit search's (`minimal/`)? The simplest that do the job, or nearly, are HFT_E1_23p_pruned
(22 parts, does the job at the nominal noise) and three of 21 parts that strand (N_E1_32p_pruned, EV_21p,
NP_E1_32p); all four are the same circuit, give or take one element. Piece by piece (HFT_E1_23p_pruned):

| piece | what it is | one of Sepulchre's components? |
|---|---|---|
| S0, S1, T | passive leaky nodes (time constants about 9, 12 and 0.6 ticks): the eyes' pulses low-pass filtered into a voltage, the taste a brief pulse | yes: a node with its monotone backbone and no elements |
| M0 (a motor) | a passive leaky node, pushed up by currents; counted as spiking when it rises through 0 having been below -1 | the node, yes; but its events are made by the body's spike counter, not by fast positive feedback |
| M1 (the clock, the other motor) | no leak; one slow negative self-feedback (filtered over 204 ticks) holds it near -0.37 V, and noise carries it across 0 and back below -1 | partly: slow negative feedback is theirs (I+s), but no leak breaks the monotone backbone, and with no fast positive feedback it has no spike of its own: its rate is the noise's (133, 225 and 252 spikes per 1,000 ticks, seeing nothing, at half, the usual and double noise) |
| m (the bit) | a memory node: a capacitor with no leak | no: their memory is bistability, from positive feedback; a perfect integrator is the idealisation they avoid |
| m <- S0, S1, gated by T | the write: a three-factor rule (what was seen, times the taste) | no: a gate (one node's voltage scaling an element's current) is this project's addition; they modulate gains from outside the circuit |
| M0 <- m, gated by S0, S1 | the read: the bit sets each eye's effect on the motor | no, as above |
| M0 <- M1 | a synapse: now and then a forward run when nothing is in view | yes |

**There is not one positive-feedback loop in it.** Everything Sepulchre gets from positive feedback, the simplest
circuit gets elsewhere: its **events** from the body's spike counter (rising through 0, re-armed below -1: a comparator
with hysteresis, a Schmitt trigger, the only positive feedback in the system, and it sits in the interface, the same
for every brain); its **memory** from a perfect integrator; its **rhythm** from noise.

**It got that way by pruning a mixed-feedback circuit.** The circuits it was pruned from have a true relaxation
oscillator in M1: a leak, fast positive feedback and slow negative feedback (filtered over 200-290 ticks). Seeing
nothing, their clocks don't care about the noise:

| clock | half noise | usual | double (M1 spikes per 1,000 ticks, 4 lives x 3,000 ticks) |
|---|---|---|---|
| N_E1_23p (23 parts), mixed feedback | 183 | 183 | 181 |
| HFT_E1_23p (28 parts), mixed feedback | 269 | 269 | 268 |
| N_E1_32p_pruned (21 parts), noise | 23 | 158 | 229 |
| HFT_E1_23p_pruned (22 parts), noise | 133 | 225 | 252 |

Pruning, judged at the nominal noise alone, took the leak and the fast positive feedback (2 parts), because there noise
did the same job (LESSONS.md, "Judged at one noise level, pruning trades mechanism for noise"). So a mixed-feedback
clock costs 2 parts and buys a rate that doesn't hang on the noise; the judging decides which wins, and at one noise
level noise is free. The pruned circuit pays where the noise differs: at half noise it strands 23% of lives.

**A first test, unpolished.** SEP_24p is HFT_E1_23p without its hunger node: the clock kept, the run path ungated (24
parts). Held out (64 seeds x 2):

| | half noise | usual | double |
|---|---|---|---|
| SEP_24p, clock kept: food, last third food:poison, stranded | 1.55, 3.29, 0%: does the job | 1.59, 2.54, 5% | 1.97, 2.16, 0% |
| HFT_E1_23p_pruned, noise clock | 0.91, 3.90, 23% | 2.16, 3.64, 5%: does the job | 3.13, 2.74, 0% |

Neither does the job at all three. SEP_24p's run path was tuned to be gated by hunger, and ungated it runs on every
clock cycle, eating less selectively; it needs polishing (and pruning judged across the noise range) before it says
anything about what a mixed-feedback circuit of its size can do.

**An estimate for a circuit of their components only.** Against HFT_E1_23p_pruned's 22 parts:

- a clock that makes its own events: +2 (a leak and fast positive feedback);
- the bit as a latch, not an integrator: +2 (a leak and positive self-feedback). A latch flips rather than adds up
  evidence: a closer fit to a task of one bit, and with poison writing too, the reversal (which every circuit fails)
  might work;
- gates: if a gate counts as theirs (in hardware it is Mead's transconductance amplifier, whose gain a bias voltage
  sets, that voltage taken from a node), nothing more. If not: either the bit shifts each sensor node's level so that
  its synapse to the motor passes or not (about the same parts, but several thresholds stacked in one voltage, under
  10% mismatch), or coincidence neurons (about 5 parts for each of the four gated paths).

So roughly 26 parts with gates, and 26 to 40 without, against 22: **not as simple, but robust where the simplest is
not.** The 4 parts more are what the 22-part circuit borrows from the noise and the integrator. Effectiveness is open
until the same search runs under their rules and judged across the noise range.

**Sepulchre's rules, as we enforce them** (the user's decision, 2026-10-21). Sepulchre's framework is silent on
learning and on non-volatile storage: its gains are set from outside the circuit, and its memory is what dynamics
give, slow variables (graded, but they fade, and noise wanders them) and positive feedback (a latch: robust, but
binary, and like any node voltage lost when the power goes). Real neuromorphic chips pair such neurons with
non-volatile weights (floating gates), as brains pair activity-held working memory with structure-held long-term
memory. So under "Sepulchre's rules" (`rules: "mixed"` in a spec, refused otherwise by `minimal/spec.py`'s `check`)
the dynamics must be his, every node leaky but memory nodes and no clamps, while our own components for learning and
storage stay allowed: gates, and memory nodes (a floating gate: graded, no leak, no membrane noise, only its writes'
shot noise).

**What building a stricter circuit showed** (no memory nodes at all, from HFT_E1_23p): a leaky node holding the bit
fails, because a leaky node is membrane and gets membrane noise, which random-walks a slow bit by about 2.7 V in
1,000 ticks (food:poison about 1.2); a latch fails differently, settling at birth into "approach colour 1, avoid colour
0" and, learning only from food, never eating colour 0 to find out. The integrator's graded middle had been doing
quiet work: an undecided state at birth, so that the creature tries both colours until meals commit it. A latch works
only with a way back from a wrong guess: learning from poison (a poison node, and a write that flips the latch on
tasting poison while seeing colour 1), 33 parts unpolished, against 28 for the circuit it came from. Which, with the
reversal (where every circuit so far fails, learning only from food), may be worth having anyway.

**The experiment** (queued 2026-10-21): three arms from HFT_E1_23p, each polished and pruned judged at half, usual and
double noise, the worst level counting: free; Sepulchre's rules with a floating-gate memory (MX_fg); and strict, the
bit a latch corrected by poison (MX_latchP).

## References

1. L. Ribar, R. Sepulchre, "Neuromorphic control: designing multiscale mixed-feedback systems", IEEE Control
   Systems Magazine 41(6), 2021. [arXiv:2011.04441](https://arxiv.org/abs/2011.04441)
2. R. Sepulchre, "Spiking control systems", Proceedings of the IEEE 110(5), 2022.
   [arXiv:2112.03565](https://arxiv.org/abs/2112.03565)
3. L. Ribar, R. Sepulchre, "Neuromodulation of neuromorphic circuits", IEEE Transactions on Circuits and Systems I,
   2019. [arXiv:1805.05696](https://arxiv.org/abs/1805.05696); code:
   [Circuit-Neuromodulation](https://github.com/lukaribar/Circuit-Neuromodulation); thesis: L. Ribar, *Synthesis of
   neuromorphic circuits with neuromodulatory properties*, Cambridge, 2019.
4. C. Mead, *Analog VLSI and Neural Systems*, Addison-Wesley, 1989; "Neuromorphic electronic systems", Proc. IEEE
   78(10), 1990.
5. R. Sepulchre, G. Drion, A. Franci, "Control across scales by positive and negative feedback", Annual Review of
   Control, Robotics, and Autonomous Systems 2, 2019.
   [Cambridge repository](https://www.repository.cam.ac.uk/handle/1810/305893); and "Excitable behaviors", 2018,
   [arXiv:1704.04989](https://arxiv.org/abs/1704.04989).
6. A. Franci, G. Drion, R. Sepulchre, "Robust and tunable bursting requires slow positive feedback", Journal of
   Neurophysiology 119, 2018; "Modeling the modulation of neuronal bursting: a singularity theory approach", SIAM J.
   Applied Dynamical Systems 13, 2014.
7. ERC Advanced Grant SpikyControl (KU Leuven, 2023-2027), [CORDIS](https://cordis.europa.eu/project/id/101054323);
   its predecessor Switchlet (Cambridge), [CORDIS](https://cordis.europa.eu/project/id/670645).
8. R. Sarpeshkar, "Analog versus digital: extrapolating from electronics to neurobiology", Neural Computation 10,
   1998.
9. K. Scheres, R. Sepulchre, "Discrete event system modeling of neuromorphic circuits", 2025.
   [arXiv:2511.15594](https://arxiv.org/abs/2511.15594)
10. R. Wroblowski, R. Sepulchre, "Describing functions and phase response curves of excitable systems", 2025-2026.
    [arXiv:2511.16235](https://arxiv.org/abs/2511.16235)
11. G. Drion, T. O'Leary, E. Marder, "Ion channel degeneracy enables robust and tunable neuronal firing rates", PNAS
    112, 2015; G. Drion, A. Franci, J. Dethier, R. Sepulchre, "Dynamic input conductances shape neuronal spiking",
    eNeuro 2, 2015.
12. A. A. Prinz, D. Bucher, E. Marder, "Similar network activity from disparate circuit parameters", Nature
    Neuroscience 7, 2004.
13. L. Mendolia et al., "A neuromodulable current-mode silicon neuron for robust and adaptive neuromorphic systems",
    2025. [arXiv:2512.01133](https://arxiv.org/abs/2512.01133)
14. F. Castaños, A. Franci, "Implementing robust neuromodulation in neuromorphic circuits", Neurocomputing 233, 2017.
    [arXiv:1608.03908](https://arxiv.org/abs/1608.03908)
15. R. Sepulchre, T. O'Leary, G. Drion, A. Franci, "Control by neuromodulation: a tutorial", European Control
    Conference, 2019; E. Marder, "Neuromodulation of neuronal circuits: back to the future", Neuron 76, 2012.
16. G. Drion, J. Dethier, A. Franci, R. Sepulchre, "Switchable slow cellular conductances determine robustness and
    tunability of network states", PLoS Computational Biology 14(4), 2018.
    [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5940245/)
17. J. Dethier, G. Drion, A. Franci, R. Sepulchre, "A positive feedback at the cellular level promotes robustness and
    modulation at the circuit level", Journal of Neurophysiology 114, 2015.
    [arXiv:1409.6338](https://arxiv.org/abs/1409.6338)
18. G. Drion, A. Franci, R. Sepulchre, "Cellular switches orchestrate rhythmic circuits", Biological Cybernetics,
    2019.
19. Y. Huo, F. Forni, R. Sepulchre, "A winner-takes-all mechanism for event generation", 2025.
    [arXiv:2504.11374](https://arxiv.org/abs/2504.11374)
20. Y. Huo, F. Forni, R. Sepulchre, "A neuromorphic architecture for scalable event-based control", 2025-2026.
    [arXiv:2511.11924](https://arxiv.org/abs/2511.11924)
21. T. S. J. Burger, R. Sepulchre, "Excitability across scales: a unifying EI model", 2026.
    [arXiv:2610.13275](https://arxiv.org/abs/2610.13275)
22. R. Schmetterling, F. Forni, A. Franci, R. Sepulchre, "Neuromorphic control of a pendulum", 2024.
    [arXiv:2404.05339](https://arxiv.org/abs/2404.05339)
23. T. Chaffey, R. Sepulchre, "Monotone one-port circuits", IEEE Transactions on Automatic Control 69(2), 2024.
    [arXiv:2111.15407](https://arxiv.org/abs/2111.15407)
24. F. Forni, R. Sepulchre, "Differential dissipativity theory for dominance analysis", IEEE Transactions on
    Automatic Control, 2019. [arXiv:1710.01721](https://arxiv.org/abs/1710.01721)
25. A. Shahhosseini, T. Chaffey, R. Sepulchre, "Operator-splitting methods for neuromorphic circuit simulation",
    2025, [arXiv:2505.22363](https://arxiv.org/abs/2505.22363); "An operator-theoretic framework to simulate
    neuromorphic circuits", CDC 2024, [arXiv:2404.06255](https://arxiv.org/abs/2404.06255).
26. T. B. Burghi, R. Sepulchre, "Adaptive observers for biophysical neuronal circuits", IEEE Transactions on
    Automatic Control, 2024. [arXiv:2111.02176](https://arxiv.org/abs/2111.02176)
27. A. Bizyaeva, A. Franci, N. E. Leonard, "Nonlinear opinion dynamics with tunable sensitivity", IEEE Transactions on
    Automatic Control 68(3), 2023. [arXiv:2009.04332](https://arxiv.org/abs/2009.04332)
28. K. Jacquerie, D. Tyulmankov, P. Sacré, G. Drion, "Burst firing creates an attractor in synaptic weight dynamics",
    PLoS Computational Biology, 2026. [ORBi](https://orbi.uliege.be/handle/2268/346004)
29. R. D. Beer, "On the dynamics of small continuous-time recurrent neural networks", Adaptive Behavior 3(4), 1995.
30. B. M. Yamauchi, R. D. Beer, "Sequential behavior and learning in evolved dynamical neural networks", Adaptive
    Behavior 2(3), 1994.
31. E. Izquierdo, I. Harvey, R. D. Beer, "Associative learning on a continuum in evolved dynamical neural networks",
    Adaptive Behavior 16(6), 2008.
32. A. Soltoggio, J. A. Bullinaria, C. Mattiussi, P. Dürr, D. Floreano, "Evolutionary advantages of neuromodulated
    plasticity in dynamic, reward-based scenarios", Artificial Life XI, 2008.
    [EPFL](https://infoscience.epfl.ch/record/121548)
33. A. Soltoggio, K. O. Stanley, S. Risi, "Born to learn: the inspiration, progress, and future of evolved plastic
    artificial neural networks", Neural Networks 108, 2018.
34. K. O. Stanley, R. Miikkulainen, "Evolving neural networks through augmenting topologies", Evolutionary
    Computation 10(2), 2002.
35. A. Thompson, "An evolved circuit, intrinsic in silicon, entwined with physics", Evolvable Systems (ICES 1996),
    LNCS 1259, 1997. [doi:10.1007/3-540-63173-9_61](https://doi.org/10.1007/3-540-63173-9_61)
36. N. Jakobi, "Evolutionary robotics and the radical envelope-of-noise hypothesis", Adaptive Behavior 6(2), 1997.
37. Y. LeCun, Y. Bengio, G. Hinton, "Deep learning", Nature 521, 2015.
38. E. O. Neftci, H. Mostafa, F. Zenke, "Surrogate gradient learning in spiking neural networks", IEEE Signal
    Processing Magazine 36(6), 2019.
