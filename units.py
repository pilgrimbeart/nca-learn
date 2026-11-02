"""The axioms: the physical numbers everything else rests on (the user's decision, 2026-10-22: real units everywhere,
every number derived where possible from as few axioms as possible, so that no maintainer has to keep numbers
plausible by hand).

Every quantity in the code is in SI base units: seconds and metres. A prefix below is only a factor (a millimetre is
written 1 * MILLI). An axiom says why it has its value; a design's own choices (the world's geometry, the sheet's
rate) stay with the design, in these units.
"""

import math

# SI prefixes: factors, not units.
TERA, GIGA, MEGA, KILO = 1e12, 1e9, 1e6, 1e3
MILLI, MICRO, NANO, PICO, FEMTO = 1e-3, 1e-6, 1e-9, 1e-12, 1e-15

# Time.
TICK = 10 * MILLI           # s (axiom): the body's step, in which the eyes look, the thrusters fire and the body moves
                            # once; 10 ms makes a reaction in 2 to 4 ticks an insect's 20 to 40 ms


def si(value: float, unit: str) -> str:
    """value in unit with an engineering prefix: si(2.5e-12, 'F') -> '2.5 pF'."""
    if value == 0 or not math.isfinite(value):
        return f"{value:g} {unit}"
    for f, p in ((TERA, "T"), (GIGA, "G"), (MEGA, "M"), (KILO, "k"), (1.0, ""), (MILLI, "m"), (MICRO, "u"),
                 (NANO, "n"), (PICO, "p"), (FEMTO, "f")):
        if abs(value) >= f * 0.9995:
            return f"{value / f:.3g} {p}{unit}"
    return f"{value:.3g} {unit}"
