# Recruitment

How could a brain, from a local perspective only and with no god, recruit more computational power when it needs
it? ("When a single neuron realises that it cannot solve XOR, how does it recruit other neurons around it into an
ensemble that can?") This file gathers what the literature offers, the insights drawn from it, and the plan for
exploring it with mixed-feedback circuits (`MIXED_FEEDBACK.md`). Written from a literature search in October 2026,
mostly from abstracts and summaries; check details against the papers before relying on them. References are
numbered at the end.

## Three timescales, and which may have a god

| | who decides | must be local? |
|---|---|---|
| evolution | selection across a population | no: a global optimiser is how nature found brains too |
| development | the cells, building themselves | yes |
| learning | the cells, during a life | yes |

Recruiting more power when needed belongs to development and learning, so it must be local. The parallel to "the
body must never be part of the solution": **the evolutionary algorithm must not be the recruiter.** At most it may
evolve the *rule* by which cells recruit.

## Ways to recruit, from the literature

| mechanism | trigger | what is recruited | local? |
|---|---|---|---|
| size principle [1] | rising common drive; units have graded thresholds | more of the same units, smallest first | fully |
| memory allocation [2, 3, 4] | a learning event; neurons compete, the most excitable win | a neuron into a memory's ensemble; raised excitability then links memories formed close in time | yes: excitability and mutual inhibition |
| adaptive resonance theory [5] | mismatch: no existing unit matches well enough | a free unit, as a new category | mostly |
| ultrastability [6, 7] | an essential variable leaves its bounds | random parameter changes until stable again | fully |
| homeostatic structural plasticity [8]; neurotrophic competition [9] | activity below a set point | new connections, favouring active partners | yes |
| growing neural gas [10] | the highest local error count | a new unit where error is worst | mostly |
| cascade-correlation [11]; self-expanding networks [12]; GradMax [13] | loss stops falling, or a score predicting gain | a new unit or layer | no: global error |
| recruitment learning [14, 15, 16]; assembly calculus [17] | features co-occurring once | free units in a random graph, as a conjunction detector or assembly | yes |
| behavioural-timescale plasticity [18] | a plateau potential driven by an instructive input | a neuron, to a new place field, in one trial | within the cell |
| within one neuron [19, 20] | local dendritic activity | a dendritic branch's coupling; dendrites can compute XOR | within the cell |
| neurogenesis [21] | new, highly excitable neurons | preferential recruitment of young neurons | yes |
| evolved developmental programs [22, 23, 24] | the evolved rule's own signals | growth and rewiring by local rules | yes: evolution supplies only the rule |

## Insights

1. **The common pattern is random variation plus local selection.** Almost every local mechanism generates
   candidates at random and selects them locally: Ashby's random parameter jumps, kept if stable [6]; Valiant's
   random wiring, where units that happen to see a conjunction are kept [15]; memory allocation's random
   excitability, where the most excitable wins [2]; and this project's own sheet, where random raised hands let a
   path's tip pick exactly one. Randomness replaces the god: a unit need not work out *what* to recruit, only have a
   source of variety and a local signal that says "keep this".
2. **Two kinds of recruitment.** More of the same (the size principle: more force), which graded thresholds give
   for free; and *new computation* (a conjunction, a category), which XOR needs. Recruitment learning, adaptive
   resonance and the assembly calculus all recruit conjunction detectors from a pool of free, randomly connected
   units, so the substrate needs such a pool.
3. **The unit need not "realise" much.** Ashby's point: the trigger only has to say "not OK", not what to do [6].
   Documented local triggers: activity out of bounds [6, 7, 8]; mismatch or novelty [5]; learning that won't settle
   (synapses that track their own uncertainty and learn faster when unsure [25]); and a third factor such as reward
   or surprise [26], as this project's taste is.
4. **Excitability is the recruiting variable.** In memory allocation the recruited neurons are the most excitable
   ones [2, 3], an intrinsic property, not a synaptic one. That fits Sepulchre's emphasis on intrinsic conductances
   and Drion's nodal and network modes (`MIXED_FEEDBACK.md`): a free unit is recruited when an intrinsic switch takes
   it from silent or relaying into firing with an ensemble. Mixed feedback is a natural vocabulary for recruitment.
5. **Recruitment pays only when demand varies.** If every life poses the same task, evolution simply builds the
   right size of brain. Structural plasticity helps most where rewards change [24]. So the experiments need lives
   that differ in what they demand, and an energy cost for every active unit, so that a fixed large brain loses.
6. **Richer units need less recruitment.** XOR is hard for a monotone unit, not for one with amplitude-localised
   feedback, which can respond to "exactly one input"; real dendrites compute XOR [20]. Sometimes the answer to "I
   can't solve this" is more feedback inside the unit.

## The plan

**Step 0: show the trigger exists.** Before building recruitment, show that a local "not OK" signal appears when a
circuit faces a problem it can't solve, for example a learning variable that keeps reversing instead of settling.

**Phase A: the minimal learner (evolution may be the god).** Graph mode, the level-0 vocabulary of
`mixed_feedback.py`, with the bounds and defences in `LESSONS.md`. Search by increasing size for tiny circuits, and
keep a MAP-Elites archive [27] with size and energy as axes, so the whole trade-off curve is visible; lexicographic
parsimony [28] breaks ties in favour of the smaller. Energy is the brain's draw from supply to ground: elements' bias
currents plus capacitor charging. Seed with today's designed brain, counted honestly at level 0 (11 nodes, 24
elements).

**Phase B: local recruitment (evolution may supply only the rule).**
1. Lives that differ in what they demand, and an energy cost for every active unit.
2. A substrate: a pool of free, generic mixed-feedback units with sparse random connections [15], each with an
   intrinsic mode switch, under mutual inhibition (a rebound winner-take-all, `MIXED_FEEDBACK.md`).
3. Hand-designed recruitment rules from the literature, each tested: *allocation by excitability* (when the trigger
   is high, free units' excitability rises; those active at the next taste win through mutual inhibition and are
   kept by a reward-gated latch, later consolidated), and *ultrastability* (the trigger causes random jumps in free
   units' parameters until outcomes stop contradicting each other).
4. Then evolve the rule (as with developmental programs [22, 23, 24]), scored across the varied lives with the energy
   cost. Evolution never places a recruited unit; it only shapes the rule.

## References

1. E. Henneman and colleagues, 1957 onwards: the size principle of motor unit recruitment.
   [Overview](https://en.wikipedia.org/wiki/Henneman%27s_size_principle)
2. J.-H. Han, S. A. Kushner, A. P. Yiu, ... S. A. Josselyn, "Neuronal competition and selection during memory
   formation", Science 316, 2007.
3. S. A. Josselyn, P. W. Frankland, "Memory allocation: mechanisms and function", Annual Review of Neuroscience 41,
   2018. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9623596)
4. D. J. Cai, ... A. J. Silva, "A shared neural ensemble links distinct contextual memories encoded close in time",
   Nature 534, 2016. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5063500)
5. G. A. Carpenter, S. Grossberg, "A massively parallel architecture for a self-organizing neural pattern
   recognition machine", Computer Vision, Graphics, and Image Processing 37, 1987 (adaptive resonance theory).
   [Overview](https://en.wikipedia.org/wiki/Adaptive_resonance_theory)
6. W. R. Ashby, *Design for a Brain*, Chapman & Hall, 1952 (ultrastability, the homeostat).
7. E. A. Di Paolo, "Homeostatic adaptation to inversion of the visual field and other sensorimotor disruptions",
   From Animals to Animats 6, 2000.
8. M. Butz, A. van Ooyen, "A simple rule for dendritic spine and axonal bouton formation can account for cortical
   reorganization after focal retinal lesions", PLoS Computational Biology 9(10), 2013.
   [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3794906)
9. A. van Ooyen, D. J. Willshaw, "Competition for neurotrophic factor in the development of nerve connections",
   Proceedings of the Royal Society B 266, 1999. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC1689926)
10. B. Fritzke, "A growing neural gas network learns topologies", NIPS 7, 1994.
    [NeurIPS](https://papers.nips.cc/paper/1994/hash/d56b9fc4b0f1be8871f5e1c40c0067e7-Abstract.html)
11. S. E. Fahlman, C. Lebiere, "The cascade-correlation learning architecture", NIPS 2, 1989.
    [NeurIPS](https://papers.nips.cc/paper/1989/hash/69adc1e107f7f7d035d7baf04342e1ca-Abstract.html)
12. R. Mitchell, M. Mundt, K. Kersting, "Self expanding neural networks", 2023.
    [arXiv:2307.04526](https://arxiv.org/abs/2307.04526)
13. U. Evci et al., "GradMax: growing neural networks using gradient information", ICLR 2022.
    [Google Research](https://research.google/pubs/gradmax-growing-neural-networks-using-gradient-information/)
14. J. A. Feldman, "Dynamic connections in neural networks", Biological Cybernetics 46, 1982.
15. L. G. Valiant, *Circuits of the Mind*, Oxford University Press, 1994; "Memorization and association on a
    realistic neural model", Neural Computation 17, 2005. [PDF](https://cenl.ucsd.edu/Jclub/Valiant_2005.pdf)
16. J. Diederich, C. Günay, J. M. Hogan, *Recruitment Learning*, Springer, 2010.
17. C. H. Papadimitriou, S. S. Vempala, D. Mitropolsky, M. Collins, W. Maass, "Brain computation by assemblies of
    neurons", PNAS 117(25), 2020. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7322080)
18. K. C. Bittner, A. D. Milstein, C. Grienberger, S. Romani, J. C. Magee, "Behavioral time scale synaptic plasticity
    underlies CA1 place fields", Science 357, 2017.
19. A. Losonczy, J. K. Makara, J. C. Magee, "Compartmentalized dendritic plasticity and input feature storage in
    neurons", Nature 452, 2008.
20. A. Gidon, ... M. E. Larkum, "Dendritic action potentials and computation in human layer 2/3 cortical neurons",
    Science 367, 2020. [ModelDB](https://modeldb.science/260178)
21. J. B. Aimone, J. Wiles, F. H. Gage, "Computational influence of adult neurogenesis on memory encoding", Neuron 61,
    2009. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC2670434)
22. J. F. Miller, G. M. Khan, "Where is the brain inside the brain?", Memetic Computing 3, 2011; G. M. Khan, J. F.
    Miller, D. M. Halliday, "Evolution of Cartesian genetic programs for development of learning neural
    architecture", Evolutionary Computation 19(3), 2011.
23. E. Najarro, S. Sudhakaran, S. Risi, "Towards self-assembling artificial neural networks through neural
    developmental programs", ALIFE 2023. [arXiv:2307.08197](https://arxiv.org/abs/2307.08197)
24. E. Plantec, J. W. Pedersen, M. L. Montero, E. Nisioti, S. Risi, "Evolving self-assembling neural networks: from
    spontaneous activity to experience-dependent learning", ALIFE 2024.
    [arXiv:2406.09787](https://arxiv.org/abs/2406.09787)
25. L. Aitchison, J. Jegminat, J. A. Menendez, J.-P. Pfister, A. Pouget, P. E. Latham, "Synaptic plasticity as
    Bayesian inference", Nature Neuroscience 24, 2021. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7617048)
26. W. Gerstner, M. Lehmann, V. Liakoni, D. Corneil, J. Brea, "Eligibility traces and plasticity on behavioral time
    scales: experimental support of neoHebbian three-factor learning rules", Frontiers in Neural Circuits 12, 2018.
    [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6079224/)
27. J.-B. Mouret, J. Clune, "Illuminating search spaces by mapping elites", 2015.
    [arXiv:1504.04909](https://arxiv.org/abs/1504.04909)
28. S. Luke, L. Panait, "Lexicographic parsimony pressure", GECCO 2002.
