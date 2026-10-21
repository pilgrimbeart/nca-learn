"""What every rule's update is, declared for the compiler: update(me, mean, count, inp, out), four arrays of the
cell's own and a number (sheet.py). Declared so that the sheet can take a rule as a typed function pointer: numba
caches a compiled function that takes another only so (a function's own type is new in every process, so passing one
recompiled the sheet, 5-12 s, at every start). A library, no update of its own."""

from numba import types

RULE = types.void(types.float64[::1], types.float64[::1], types.float64, types.float64[::1], types.float64[::1])
