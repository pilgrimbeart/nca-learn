"""The axioms: the physical numbers everything else rests on, and what follows from them (the user's decision,
2026-10-22: real units everywhere, every number derived where possible from as few axioms as possible, so that no
maintainer has to keep numbers plausible by hand).

Every quantity in the code is in SI base units: seconds, metres, volts, amperes, farads, ohms, watts, joules,
coulombs. A prefix below is only a factor (a capacitor of 25 pF is written 25 * PICO). An axiom says why it has its
value; everything computed here is derived. A design's own choices (the world's geometry, a circuit's parts) stay
with the design, in these units; the noise model is explained in mixed_feedback.py's docstring, the scoring in
minimal/spec.py.
"""

import math

# SI prefixes: factors, not units.
TERA, GIGA, MEGA, KILO = 1e12, 1e9, 1e6, 1e3
MILLI, MICRO, NANO, PICO, FEMTO = 1e-3, 1e-6, 1e-9, 1e-12, 1e-15

# Physics (exact, by the SI's definitions).
E = 1.602176634e-19         # C: the elementary charge, what one electron carries
K_B = 1.380649e-23          # J/K: Boltzmann's constant
T = 300.0                   # K (axiom): a chip at room temperature
U_T = K_B * T / E           # V: the thermal voltage, about 26 mV

# Time.
TICK = 10 * MILLI           # s (axiom): the body's step, in which the eyes look, the thrusters fire and the body moves
                            # once; 10 ms makes a reaction in 2 to 4 ticks an insect's 20 to 40 ms
STEPS = 80                  # (axiom) integration steps per tick: the simulator's accuracy (a result must hold at twice
                            # as many, minimal/check.py)
DT = TICK / STEPS           # s: the integration step, 0.125 ms
PULSE = TICK / 4            # s (axiom): how long the body's pulse into a sensor or the taste node lasts, 2.5 ms; also
                            # the circuit's typical time (T_TYP below)

# The supply (the user's decision, 2026-10-26: a supply SKY130's core devices work at, and the lowest that keeps power
# down, speed given up where needed; chip.py and minimal/spice.py build every part of the model in its transistors).
SUPPLY = 1.8                # V (axiom): vdd - vss, the chip's supply, analogue ground (0 V) halfway between: SKY130's
                            # core devices' own; the standard pMOS (which barely leaks) needs about 0.9 V across it, so
                            # that a pair's inputs have a window of only 0.4 V even here (minimal/NOTEBOOK.md, M15)
RAIL = SUPPLY / 2           # V: the rails, +-RAIL, that no node goes beyond (an output's current fades within a few
                            # hundredths of a volt of them: chip.KNEE)
V_TYP = RAIL / 3            # V: a typical voltage, the unit a design's voltages are reckoned in (an offset of a few
                            # V_TYP, a gate open at V_TYP, a slope of a few per V_TYP), 0.2 V; the designs before
                            # 2026-10-26 were drawn at 1 V and +-3 V rails, and are converted (minimal/designs.py, rescale)

# A circuit's typical sizes: what designs and searches start from and are bounded around (subthreshold analogue
# silicon). Not limits: a design may stray from them, within the honesty limits below.
T_TYP = PULSE               # s: a typical time, the body's pulse
C_TYP = 2.5 * PICO          # F (axiom): a typical capacitor
I_TYP = C_TYP * V_TYP / T_TYP   # A: a typical current, which moves a typical capacitor a typical voltage in a typical
                            # time (0.3 nA)
R_TYP = V_TYP / I_TYP       # ohm: a typical resistor, through which a typical voltage drives a typical current, 1 GOhm

# Honesty against the integration step (AGENTS.md, The minimal circuit search: not faster than the step).
STEP_MOVE = V_TYP / 2       # V (axiom: half a typical voltage): the most anything may move a node in one integration
                            # step
SLEW = STEP_MOVE / DT       # V/s: so the fastest any element, leak or pulse may move a node
TAU_LOOP = 10 * DT          # s (axiom: 10 steps): the fastest a device fed back to itself may act, 1.25 ms
TAU_LEAK = V_TYP / SLEW     # s: a leak's time constant at least the time the slew limit takes to move a node a
                            # typical voltage, 0.25 ms (a leak that far from rest then moves no faster than SLEW)

# Mismatch.
MISMATCH = 0.1              # (axiom) every part off by about this share of itself, every offset by about this many typical
                            # voltages
                            # (analogue silicon by 10% or more; neurons of one type by more, held by homeostasis)

# Noise (mixed_feedback.py's docstring): shot noise, events of a charge; and resting noise on each node.
Q_BIO = 12.5 * FEMTO        # C (axiom, calibrated): the charge one random event carries in biology, between an ion
                            # channel open for a few milliseconds (1-10 fC) and a vesicle's release (20-100 fC); set,
                            # with J_REST, so that the standard neuron (mixed_feedback.Circuit.neuron, its parts as
                            # designed) fires on its own about twice a second, as cortical neurons at rest do
J_REST = 1600.0             # A/F (axiom, calibrated): the gross current that flows across a membrane at rest, per farad
                            # of it (channels opening both ways, the net zero), whose events flicker a node at rest;
                            # with Q_BIO, about half the standard neuron's noise at rest
V_CAL = 1.0                 # V: the typical voltage Q_BIO and J_REST were calibrated at; biology's noise scales with a
                            # circuit's typical voltage (mixed_feedback.SUBSTRATES), so that the standard neuron keeps its
                            # calibration at any scale
Q_SI = E                    # C: silicon's events are single electrons
LOUDER = 2.0                # (axiom) the margin above biology a design is judged at, in amplitude: biology's noise is
                            # calibrated only to about a factor of two, and varies with an animal's state

# Plausibility on a chip (python -m minimal.physical): how far silicon goes, not rules a design must obey.
KAPPA = 0.67                # (axiom, measured: SKY130's nfet_01v8, 4 x 4 um, typical corner) a subthreshold transistor's
                            # gate coupling
I_MIN = 1 * PICO            # A (axiom): the smallest bias current usable on a chip, a little above leakage
C_MAX = 50 * PICO           # F (axiom): the largest capacitor worth building on a chip
CAP_DENSITY = 5 * FEMTO / MICRO ** 2    # F/m^2 (axiom): a MOS capacitor in a mature process, 5 fF per square micron
UNIT_AREA = 15 * MICRO ** 2             # m^2 (axiom): an analogue-sized transistor with its spacing
SWITCH = 2 * U_T / KAPPA    # V: the span over which a bare differential pair switches (its tanh's scale), about 74 mV
R_MAX = SWITCH / I_MIN      # ohm: the largest resistance a design can set (an amplifier biased at I_MIN), about 74 GOhm
TAU_MAX = R_MAX * C_MAX     # s: so the slowest time constant a chip can hold without a floating gate, about 3.7 s


def si(value: float, unit: str) -> str:
    """value in unit with an engineering prefix: si(2.5e-12, 'F') -> '2.5 pF'."""
    if value == 0 or not math.isfinite(value):
        return f"{value:g} {unit}"
    for f, p in ((TERA, "T"), (GIGA, "G"), (MEGA, "M"), (KILO, "k"), (1.0, ""), (MILLI, "m"), (MICRO, "u"),
                 (NANO, "n"), (PICO, "p"), (FEMTO, "f")):
        if abs(value) >= f * 0.9995:
            return f"{value / f:.3g} {p}{unit}"
    return f"{value:.3g} {unit}"
