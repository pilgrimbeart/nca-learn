"""A whole life in one compiled call, for searching for the minimal circuit (minimal/NOTEBOOK.md): the same world, body
and circuit as creature.Life with a circuit brain, tick for tick, from the same random generators, so a life here is
the same life (test: python -m minimal.fastlife). About 2-3x faster than Life (about 0.7 s a life of 100 s), which spends
its time between compiled calls in Python. Only for brains whose noise comes from one stream (STREAMS False). The circuit is stepped by
mixed_feedback's own step, noise, pulses and mismatch included, so nothing here can leave them out.
"""

from __future__ import annotations

import math
import os
import sys

import numpy as np
from numba import njit

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import mixed_feedback as mf  # noqa: E402
import world  # noqa: E402
from brains.circuit import PULSES  # noqa: E402
from units import PULSE, TICK  # noqa: E402
from world import BODY, DRAG, EAT, PUSH, SENSE, TURN, WORLD  # noqa: E402

SQ3 = math.sqrt(3)


@njit(cache=True)
def _somewhere(g, pos):
    while True:
        p = g.uniform(0.0, WORLD, 2)
        dx = (p[0] - pos[0] + WORLD / 2) % WORLD - WORLD / 2
        dy = (p[1] - pos[1] + WORLD / 2) % WORLD - WORLD / 2
        if np.sqrt(dx * dx + dy * dy) > 3 * EAT + BODY:
            return p


@njit(cache=True)
def _life(V, Vx, armed, node, el, link, q, rest, sensors, motors, taste_node, wrng, crng, pos, heading, xy, kind,
          sensor_of, motor_of, poison, learning, ticks, dt, cfg, pulse):
    """The life from tick 0 to ticks (each units.TICK). sensor_of[colour] -> sensor, motor_of[thruster] -> motor (0
    left, 1 right); poison: a colour index, or -1 for all food; q, rest: the substrate's noise (mixed_feedback._step);
    pulse: the body's pulse, A (brains.circuit.PULSES typical currents).
    Returns the meals (tick, colour), the first tick a thruster fired, the circuit's mean power (W) and how many times
    the thrusters fired."""
    n = V.shape[0]
    steps = int(round(TICK / dt))
    drive = np.zeros((2 * steps, n))                                # pulses to come, this tick's and the next's
    dV, gross, vmax = np.empty(n), np.empty(n), np.zeros(n)
    spikes = np.zeros(n, dtype=np.int64)
    speed = np.zeros(2)
    spin = 0.0
    meal_t = np.empty(4 * ticks + 8, dtype=np.int64)
    meal_c = np.empty(4 * ticks + 8, dtype=np.int64)
    meals = 0
    moving = -1
    power_sum = 0.0
    firings = 0
    decay = math.exp(-DRAG * TICK)
    for t in range(ticks):
        f0, f1 = math.cos(heading), math.sin(heading)
        h = np.array([pos[0] + f0 * BODY / SQ3, pos[1] + f1 * BODY / SQ3])
        far, hit = world._look(xy, kind, h, np.array([f0, f1]))
        seen = world._sees(far, hit, 2)
        for c in range(2):                                          # each eye fires at random moments (as Life)
            for _ in range(wrng.poisson(SENSE * seen[c] * TICK)):
                mf._pulse(drive, sensors[sensor_of[c]], pulse, wrng.random() * TICK, PULSE, dt)
        z = crng.standard_normal((steps, n))                        # the circuit's noise for this tick
        spikes[:] = 0
        for k in range(steps):
            power_sum += mf._step(V, Vx, armed, spikes, vmax, drive[k], node, el, link, z[k], q, rest, dt, dV, gross,
                                  cfg)
        drive[:steps] = drive[steps:]
        drive[steps:] = 0.0
        fired = False
        for th in range(2):                                         # left's firings, then right's, as Life
            for _ in range(spikes[motors[motor_of[th]]]):
                fired = True
                firings += 1
                speed[0] += PUSH * f0
                speed[1] += PUSH * f1
                spin += TURN if th == 1 else -TURN
        if fired and moving < 0:
            moving = t
        g0, g1 = math.cos(heading), math.sin(heading)
        h0 = np.array([pos[0] + g0 * BODY / SQ3, pos[1] + g1 * BODY / SQ3])   # where the point starts the tick
        pos[0] = (pos[0] + speed[0] * TICK) % WORLD                 # move
        pos[1] = (pos[1] + speed[1] * TICK) % WORLD
        heading += spin * TICK
        speed[0] *= decay
        speed[1] *= decay
        spin *= decay
        g0, g1 = math.cos(heading), math.sin(heading)
        if speed[0] * g0 + speed[1] * g1 <= 0:
            continue
        eaten = world._touching(xy, h0, np.array([pos[0] + g0 * BODY / SQ3, pos[1] + g1 * BODY / SQ3]))
        taste = 0.0
        for b in eaten:
            xy[b] = _somewhere(wrng, pos)
            meal_t[meals], meal_c[meals] = t, kind[b]
            meals += 1
            taste += -1.0 if kind[b] == poison else 1.0
        if taste != 0.0:
            at = wrng.random()                                      # (with learning off too, as Life)
            if learning:
                mf._pulse(drive, taste_node, pulse * min(max(taste, -1.0), 1.0), at * TICK, PULSE, dt)
    return meal_t[:meals], meal_c[:meals], moving, power_sum / (ticks * steps), firings


def life(make, seed: int, poison: str | None, ticks: int, learning: bool = True):
    """One life of the brain make(seed) builds, as creature.Life would live it: (meals as [(tick, colour)], the first
    tick a thruster fired or None, the circuit's mean power, the thrusters' firings)."""
    from creature import COLOURS, THRUSTERS, Life
    lf = Life(seed, poison, learning, brain=make)
    b, c = lf.brain, lf.brain.circuit
    assert not c.streams, "fastlife draws every node's noise from one stream"
    c._ready()
    body = lf.body
    t, k, moving, power, firings = _life(c.V, c.Vx, c.armed, c.node_arr, c.el_arr, c.link, c.q, c.rest,
                                np.array(b.sensors, dtype=np.int64), np.array(b.motors, dtype=np.int64), b.taste_node,
                                lf.rng, c.rng, body.pos.astype(float), float(body.heading), body.xy, body.kind,
                                np.array([lf.sensor[x] for x in COLOURS], dtype=np.int64),
                                np.array([lf.motor[x] for x in THRUSTERS], dtype=np.int64),
                                -1 if poison is None else COLOURS.index(poison), learning, ticks, mf.DT, c.cfg,
                                PULSES * c.unit())
    return [(int(a), COLOURS[int(z)]) for a, z in zip(t, k)], (None if moving < 0 else int(moving)), power, \
        int(firings)


if __name__ == "__main__":
    import time
    from creature import Life
    from brains.designed import DesignedBrain
    for seed, poison in ((0, "red"), (1, "blue"), (2, None)):
        t0 = time.time()
        lf = Life(seed, poison, brain=DesignedBrain)
        while lf.t < 3000:
            lf.step()
        t1 = time.time()
        meals, moving, _, _ = life(DesignedBrain, seed, poison, 3000)
        t2 = time.time()
        same = [(a, c) for a, c in lf.meals] == meals and moving == lf.moving
        print(f"seed {seed}, poison {poison}: {len(meals)} meals; the same as Life: {same}; "
              f"Life {t1 - t0:.2f} s, fast {t2 - t1:.2f} s")
