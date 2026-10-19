"""Checks that the compiled simulation computes what its plain description says (python test_compiled.py): the
circuit's integration (mixed_feedback.py) and the eyes and mouth (world.py), each against a plain numpy version of
the same equations, on the designed circuit and on random circuits and scenes. The world must agree exactly; the
circuit to rounding (numpy's exp and tanh may differ from the compiled ones in the last bit), with the same spikes.
"""

from __future__ import annotations

import math

import numpy as np

import mixed_feedback as mf
import world
from brains.designed import DesignedBrain


def plain_tick(c, V, Vx, armed, inject, z):
    """One tick of circuit c by the equations in mixed_feedback's docstring, plainly in numpy; z: its noise draws."""
    bias, leak, cap, lo, hi, write = c.node_arr
    gain, offset, slope, tau, sig = c.el_arr
    to, frm, gate = c.link
    spikes = np.zeros(len(V), dtype=np.int64)
    for k in range(len(z)):
        slow = tau > 0
        Vx = np.where(slow, Vx + mf.DT * (V[frm] - Vx) / np.where(slow, tau, 1.0), V[frm])
        x = slope * (Vx - offset)
        f = np.where(sig > 0.5, 1.0 / (1.0 + np.exp(-x)), np.tanh(x))
        f = np.where(gate >= 0, f * np.clip(V[gate], 0.0, 1.0), f)
        dV = -leak * V + bias + inject
        np.add.at(dV, to, gain * f)
        d = mf.DT * dV / cap
        rough = np.where(write > 0, write * np.abs(d) * z[k], c.noise * np.sqrt(mf.DT) * z[k] / cap)
        V = np.clip(V + d + rough, lo, hi)
        up = armed & (V > mf.SPIKE)
        spikes += up
        armed = (armed & ~up) | (V < mf.RESET)
    return V, Vx, armed, spikes


def random_circuit(rng):
    """Neurons, leaky and clamped nodes, and elements of every kind between them, some gated."""
    c = mf.Circuit(seed=int(rng.integers(1 << 30)))
    nodes = [c.neuron(f"n{i}", bias=rng.uniform(-1.8, -1.2), tau=rng.uniform(2, 20)) for i in range(4)]
    nodes += [c.node(f"m{i}", R=rng.choice([None, rng.uniform(0.5, 10)]), C=rng.uniform(1, 50), lo=0.0, hi=1.0,
                     start=rng.choice([None, 0.5])) for i in range(3)]
    nodes += [c.node(f"k{i}", R=None, lo=0.0, hi=1.0, start=0.5, memory=True) for i in range(2)]
    for _ in range(12):
        to, frm = rng.choice(nodes, 2)
        c.element(int(to), int(frm), rng.uniform(-3, 3), rng.uniform(-1, 1), tau=rng.choice([0.0, rng.uniform(0.2, 5)]),
                  slope=rng.uniform(0.5, 10), sigmoid=bool(rng.integers(2)),
                  gate=int(rng.choice([-1, *nodes[4:]])))
    return c


def check_circuit(c, inputs, ticks, rng):
    """Runs c compiled and plainly from the same state and noise; the largest voltage difference, and whether every
    tick's spikes agreed."""
    c._ready()
    V, Vx, armed = c.V.copy(), c.Vx.copy(), c.armed.copy()
    worst, same = 0.0, True
    per = int(round(1 / mf.DT))
    for t in range(ticks):
        inject = np.zeros(len(c.names))
        if rng.random() < 0.3:
            inject[rng.choice(inputs)] = rng.uniform(-3, 6)
        state = c.rng.bit_generator.state
        z = c.rng.standard_normal((per, len(c.names)))
        c.rng.bit_generator.state = state                     # the compiled tick draws the same noise
        got = c.tick(inject)
        V, Vx, armed, want = plain_tick(c, V, Vx, armed, inject, z)
        worst = max(worst, float(np.abs(V - c.V).max()))
        same &= bool(np.array_equal(got, want))
        V, Vx, armed = c.V.copy(), c.Vx.copy(), c.armed.copy()   # carry on from the compiled state
    return worst, same


def check_memory():
    """A memory node holds its value exactly while nothing writes it, and is written roughly (by about WRITE of each
    change) when something does."""
    c = mf.Circuit(seed=5)
    n = c.neuron("n")
    idle = c.node("idle", R=None, lo=0.0, hi=1.0, start=0.3, memory=True)
    used = c.node("used", R=None, lo=-50.0, hi=50.0, start=0.0, memory=True)
    c.element(used, n, 0.0, 0.0)                                # a gain of 0: no write ...
    c.element(used, c.node("one", bias=1.0, R=1.0), 0.05, -10.0, sigmoid=True)   # ... and a steady small write
    c.tick(np.zeros(len(c.names)), 1000)
    rough = abs(c.V[used] - 0.05 * 1000) / (0.05 * 1000)
    return c.V[idle] == 0.3, rough


def check_growth():
    """Growth during a life: splitting a synapse with a relay neuron keeps every existing node's state, and the relay
    passes spikes on (a stimulated neuron still drives its target, now through the relay)."""
    c = mf.Circuit(seed=7)
    a, b = c.neuron("a"), c.neuron("b")
    e = c.synapse(b, a, 1.0)
    pulse = np.zeros(2)
    pulse[a] = 3.0
    before = sum(c.tick(pulse, 4)[b] for _ in range(200))
    V = c.V.copy()
    r = c.neuron("relay")
    c.redirect(e, r)
    c.synapse(b, r, 1.0)
    c.grow()
    kept = np.array_equal(c.V[:2], V)
    pulse = np.zeros(3)
    pulse[a] = 3.0
    after = sum(c.tick(pulse, 4)[b] for _ in range(200))
    return kept, before, after


def plain_look(body):
    """The eyes, as world.py described them before they were compiled: rays across the corridor, each stopping at
    the first block it meets."""
    f, h = body.forward(), body.head()
    side, w = np.array([f[1], -f[0]]), world.EAT
    across = -w + (np.arange(world.RAYS) + 0.5) * 2 * w / world.RAYS
    far, kind = np.full(world.RAYS, world.RANGE), np.full(world.RAYS, -1)
    for (x, y), k in zip(body.xy, body.kind):
        d = body.wrap(np.array([x, y]) - h)
        ahead, off = d[0] * f[0] + d[1] * f[1], d[0] * side[0] + d[1] * side[1]    # not @: BLAS rounds by CPU
        if ahead <= -world.BLOCK or ahead - world.BLOCK >= world.RANGE or abs(off) >= w + world.BLOCK:
            continue
        gap = world.BLOCK ** 2 - (across - off) ** 2
        for r in np.nonzero(gap > 0)[0]:
            hit = max(0.0, ahead - np.sqrt(gap[r]))
            if hit < far[r]:
                far[r], kind[r] = hit, k
    seen = [0.0] * len(world.COLOURS)
    for d, k in zip(far, kind):
        if k >= 0:
            seen[k] += world.SHARE / (1 + (d / world.REACH) ** 2)
    touching = [b for b, (x, y) in enumerate(body.wrap(body.xy - h)) if np.sqrt(x * x + y * y) < world.EAT]
    return far, kind, [min(1.0, v) for v in seen], touching


def check_world(rng, scenes):
    """Random scenes, crowded near the mouth so that rays are blocked and blocks touch: compiled against plain."""
    bad = 0
    for _ in range(scenes):
        body = world.Body(np.random.default_rng(int(rng.integers(1 << 30))))
        body.pos = rng.uniform(0, world.WORLD, 2)
        body.heading = rng.uniform(-10, 10)
        h, f = body.head(), body.forward()
        near = rng.random(len(body.xy)) < 0.5                  # half the blocks just ahead, some touching the mouth
        n = int(near.sum())
        body.xy[near] = (h + f * rng.uniform(-1, 8, (n, 1)) + rng.normal(0, 1.5, (n, 2))) % world.WORLD
        far, kind, seen, touching = plain_look(body)
        _, far2, kind2 = body.look()
        seen2 = list(body.sees().values())
        touching2 = list(world._touching(body.xy, h))
        bad += not (np.array_equal(far, far2) and np.array_equal(kind, kind2) and seen == seen2
                    and touching == touching2)
    return bad


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    failed = False
    b = DesignedBrain(3)
    worst, same = check_circuit(b.circuit, [*b.sensors, b.taste_node], 2000, rng)
    ok = worst < 1e-9 and same
    print(f"circuit, designed circuit, 2,000 ticks: spikes {'the same' if same else 'DIFFER'}, voltages within "
          f"{worst:.1e}: {'ok' if ok else 'FAILED'}")
    failed |= not ok
    for i in range(20):
        c = random_circuit(rng)
        worst, same = check_circuit(c, list(range(4)), 300, rng)
        ok = worst < 1e-9 and same
        failed |= not ok
        if not ok:
            print(f"circuit, random {i}: spikes {'the same' if same else 'DIFFER'}, voltages within {worst:.1e}:"
                  " FAILED")
    print("circuits, 20 random, 300 ticks each:", "FAILED" if failed else "ok")
    kept, before, after = check_growth()
    ok = kept and after > 0.8 * before
    print(f"growth: state kept {kept}; target spikes {before} before a relay split its synapse, {after} after:"
          f" {'ok' if ok else 'FAILED'}")
    failed |= not ok
    held, rough = check_memory()
    ok = held and rough < 3 * mf.WRITE / np.sqrt(1000 / mf.DT) + 0.01
    print(f"memory nodes: held exactly while idle {held}; written 50.0 with error {rough:.4f}: {'ok' if ok else 'FAILED'}")
    failed |= not ok
    bad = check_world(rng, 3000)
    print(f"world, 3,000 random scenes: {'ok' if not bad else f'{bad} differ: FAILED'}")
    failed |= bool(bad)
    raise SystemExit(1 if failed else 0)
