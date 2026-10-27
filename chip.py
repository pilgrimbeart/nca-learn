"""How each part of a circuit (mixed_feedback.py) is built on a chip, as far as the simulator needs to know it: which
blocks of transistors an element takes, the current they draw from the supply, and so what the circuit's power is
(the user's decision, 2026-10-26: power is what the supply delivers to the transistors, not only the currents into
nodes; a closed-loop life in SPICE drew 150 times the old figure). minimal/spice.py writes the same blocks out as
SKY130 transistors, from the same decisions here, so that SPICE measures what the simulator reckons.

The blocks (standard subthreshold CMOS after Mead, "Analog VLSI and Neural Systems", 1989; every mirror and tail a
wide-swing cascode, as the outputs must hold their current across the rails):

  element    a differential pair of nMOS reading its input against its offset, its tail a mirrored bias current of
             |gain| (the reference branch draws |gain| too); a sigmoid's one branch mirrored into the node (twice, to
             sink it); a tanh's both (Mead's wide-range amplifier: one branch sourced into the node, the other mirrored
             twice and sunk from it, so that the two cancel at rest and only their difference reaches the node)
  gate       the tail made by a second pair reading the gate node, its own tail and reference |gain|, its one branch
             (|gain| x the gate's opening) mirrored into the element's tail reference
  steep      a slope above the pair's own (NATIVE) needs a preamplifier, a wide-range amplifier of AUX into a resistor
  shallow    below it, resistors in the pair's sources (degeneration); much below, a divider (towards the middle of
             the pair's range)
  far        an offset beyond the pair's range (RANGE) needs a source follower to shift its input, of AUX
  filter     a follower (a wide-range amplifier of AUX, so that the filter doesn't load its node), a resistor, a capacitor
  node       a capacitor to ground; a leak, a resistor to analogue ground (0 V, one buffer for the chip); its bias, a
             mirrored current from a rail (its reference branch drawing as much)
  memory     a SONOS cell (charge trapped in nitride, held for years), written by tunnelling: each write's output
             flows into analogue ground through a pulse driver whose duty sets the tunnelling, so a write's current
             doesn't fade near the rails, and nothing that leaks touches the cell; the driver fires only above DEAD of
             the write's full current. A known anomaly (the user's decision, 2026-10-26): the
             writing needs 10.5 V across the cell (SKY130: +6.7 V and -3.8 V, 2 ms across the window), from charge
             pumps or extra supplies, whose driver and pumps are not in the power reckoned here

The supply delivers (power, the _step of mixed_feedback): every current from a rail to a rail through a block (its
reference, its pair, a gate's pair and copy, a sigmoid's second mirror, the part of a tanh's two branches that cancels,
each auxiliary amplifier) across the whole supply; every current into a node from the rail it comes from, every
current out of it to the rail it goes to; a leak's current through its resistor, and the analogue ground's net
current to a rail. Static: what flows whatever the circuit does (STATIC, still()); the rest is reckoned each step.
"""

from __future__ import annotations

import numpy as np

from units import KAPPA, PICO, SUPPLY, U_T

NATIVE = KAPPA / U_T        # /V: the slope of one branch of a subthreshold differential pair (a sigmoid's), about
                            # 26 /V; a tanh (both branches) has half
VGS_N, VSG_P = 0.42, 0.88   # V: an nMOS's gate-source voltage at 10 nA, a pMOS's (SKY130 nfet_01v8, pfet_01v8: the
                            # standard pMOS, which leaks a millionth of the low-threshold one's picoampere when off,
                            # 4 x 4 um, typical corner: measured)
RANGE = (-SUPPLY / 2 + 0.6, SUPPLY / 2 - VSG_P + 0.09)  # V: the offsets a pair reads at, its cascoded tail and loads
                            # saturated (measured)
PRE_MARGIN = 0.15           # V: a pair with a preamplifier keeps this much further inside RANGE, so that the
                            # preamplifier's output can swing both ways
AUX = 100 * PICO            # A: an auxiliary amplifier's bias (a preamplifier, follower or level shifter): small beside
                            # the elements', well above leakage
KNEE_P, KNEE_N = 0.030, 0.025   # V: an output's current fades near the rail it comes from as 1 - exp(-d / KNEE), d its
                            # distance from that rail: a pMOS cascode sourcing from +RAIL, an nMOS one sinking to -RAIL
                            # (measured in SPICE: half at 0.02 V, 90% at 0.05-0.08 V)
CENTRE = sum(RANGE) / 2     # V: a divider divides towards the middle of a pair's range ...
DIV_MAX = 0.9 * (RANGE[1] - RANGE[0]) / 2 / (SUPPLY / 2 + abs(CENTRE))     # ... by at least this, so that a node
                            # swinging rail to rail stays inside it (a filtered input always: its follower must)
WIDE = 3                    # an auxiliary wide-range amplifier draws about this many times its bias: its reference,
                            # its pair, and its mirrored branches
GROUND = WIDE * AUX         # A: the analogue ground's buffer, one for the chip
DEAD = 0.01                 # a memory's write fires its high-voltage driver only above this share of the write's full
                            # current (the driver's threshold): below it, as the transistors' off-leakage, nothing tunnels


def native(sigmoid: bool) -> float:
    return NATIVE if sigmoid else NATIVE / 2


def blocks(offset: float, slope: float, tau: float, sigmoid: bool, trim_slope: float = 1.0, trim_off: float = 0.0):
    """What an element takes beside its pair: (the divider's share of its input, 1 if none; whether it has a
    preamplifier; whether its input is filtered (a follower); its level shift, +1 up, -1 down, 0 none)."""
    a = abs(slope) / native(sigmoid) * trim_slope
    share = min(a, DIV_MAX) if tau > 0 or a < 0.5 else 1.0
    off, a = divided(offset + trim_off, share), a / share
    return share, a > 1, tau > 0, shifted(off, a)


def divided(v: float, share: float) -> float:
    """A voltage after a divider of this share towards CENTRE (1: none)."""
    return v if share == 1.0 else CENTRE + share * (v - CENTRE)


def shifted(off: float, a: float) -> int:
    """Whether a pair reading against off needs its input shifted into its range: +1 up, -1 down, 0 not (with a
    preamplifier, a > 1, it keeps further from the rails)."""
    lo, hi = RANGE
    if a > 1:
        lo, hi = lo + PRE_MARGIN, hi - PRE_MARGIN
    return int(off < lo) - int(off > hi)


def static(gain: float, offset: float, slope: float, tau: float, sigmoid: bool, gated: bool) -> float:
    """The current (A) an element draws from rail to rail whatever its input: its tail's reference and pair (a gated
    element's gate pair and its tail's reference instead: its own pair's current depends on the gate), and its
    auxiliary amplifiers."""
    share, pre, follow, shift = blocks(offset, slope, tau, sigmoid)
    return 2 * abs(gain) + WIDE * AUX * (pre + follow) + 2 * AUX * abs(shift)


def still(nodes: np.ndarray, el: np.ndarray, link: np.ndarray, supply: float = SUPPLY) -> float:
    """The circuit's static power (W): every element's static current, and the analogue ground's buffer, across the
    supply (nodes, el, link: mixed_feedback.Circuit's arrays)."""
    I = GROUND + sum(static(el[0, j], el[1, j], el[2, j], el[3, j], el[4, j] > 0.5, link[2, j] >= 0)
                     for j in range(el.shape[1])) + float(np.abs(nodes[0]).sum())   # (and each bias's reference)
    return supply * I
