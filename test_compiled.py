"""Checks that the compiled simulation computes what its plain description says (python test_compiled.py): the
circuit's integration (mixed_feedback.py) and the eyes and mouth (world.py), each against a plain numpy version of
the same equations, on the designed circuit and on random circuits and scenes; and that the noise, mismatch and pulses
can't be dodged (the same at any integration step, size buying quiet only as its square root, every part mismatched). The world must agree exactly; the
circuit to rounding (numpy's exp and tanh may differ from the compiled ones in the last bit), with the same spikes.
"""

from __future__ import annotations

import math

import numpy as np

import mixed_feedback as mf
import world
from brains.designed import DesignedBrain


def plain_tick(c, V, Vx, armed, drive, z):
    """One tick of circuit c by the equations in mixed_feedback's docstring, plainly in numpy; drive: each step's pulse
    currents, z: its noise draws."""
    bias, leak, cap, lo, hi, memory = c.node_arr
    gain, offset, slope, tau, sig = c.el_arr
    to, frm, gate = c.link
    spikes = np.zeros(len(V), dtype=np.int64)
    for k in range(len(z)):
        slow = tau > 0
        Vx = np.where(slow, Vx + mf.DT * (V[frm] - Vx) / np.where(slow, tau, 1.0), V[frm])
        x = slope * (Vx - offset)
        f = np.where(sig > 0.5, 1.0 / (1.0 + np.exp(-x)), np.tanh(x))
        f = np.where(gate >= 0, f * np.clip(V[gate], 0.0, 1.0), f)
        I = bias - leak * V
        dV = I + drive[k]
        gross = np.abs(I) + np.abs(drive[k])
        np.add.at(dV, to, gain * f)
        np.add.at(gross, to, np.abs(gain * f))
        var = mf.SHOT * gross + np.where(memory > 0, 0.0, mf.MEMBRANE * cap)
        V = np.clip(V + (mf.DT * dV + c.noise * np.sqrt(mf.DT) * np.sqrt(var) * z[k]) / cap, lo, hi)
        up = armed & (V > mf.SPIKE)
        spikes += up
        armed = (armed & ~up) | (V < mf.RESET)
    return V, Vx, armed, spikes


def plain_pulse(buf, node, current, at, length=1.0):
    """A pulse by its description: each step gets the current times the share of the step within the pulse."""
    t0 = np.arange(len(buf)) * mf.DT
    buf[:, node] += current * np.clip(np.minimum(t0 + mf.DT, at + length) - np.maximum(t0, at), 0.0, None) / mf.DT


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
    """Runs c compiled and plainly from the same state and noise, with pulses at random moments (some running on into
    the next tick); the largest voltage difference, and whether every tick's spikes agreed."""
    c._ready()
    V, Vx, armed = c.V.copy(), c.Vx.copy(), c.armed.copy()
    worst, same = 0.0, True
    per = int(round(1 / mf.DT))
    buf = np.zeros((3 * per, len(c.names)))
    for t in range(ticks):
        if rng.random() < 0.3:
            node, current, at = int(rng.choice(inputs)), rng.uniform(-3, 6), rng.uniform(0, 1)
            c.pulse(node, current, at)
            plain_pulse(buf, node, current, at)
        state = c.rng.bit_generator.state
        z = c.rng.standard_normal((per, len(c.names)))
        c.rng.bit_generator.state = state                     # the compiled tick draws the same noise
        got = c.tick()
        V, Vx, armed, want = plain_tick(c, V, Vx, armed, buf[:per], z)
        buf = np.concatenate([buf[per:], np.zeros((per, len(c.names)))])
        worst = max(worst, float(np.abs(V - c.V).max()))
        same &= bool(np.array_equal(got, want))
        V, Vx, armed = c.V.copy(), c.Vx.copy(), c.armed.copy()   # carry on from the compiled state
    return worst, same


def spread(build, ticks, dt, lives=100):
    """The spread (sd) over lives of one node's voltage after ticks, at integration step dt: build(c) -> the node.
    Without mismatch (only here, to see the noise alone: each life's own mismatch would move its mean)."""
    old, out, mismatch = mf.DT, [], mf.MISMATCH
    mf.DT, mf.MISMATCH = dt, 0.0
    try:
        for s in range(lives):
            c = mf.Circuit(seed=1000 + s)
            n = build(c)
            c.tick(ticks)
            out.append(c.V[n])
    finally:
        mf.DT, mf.MISMATCH = old, mismatch
    return float(np.std(out))


def check_noise():
    """The noise model (mixed_feedback's docstring): the same at any integration step; a memory still while idle and
    written roughly by the square root of the charge written; size buys quiet only as its square root; the noise
    can't be turned off."""
    def written(c):                                             # a memory written 10 (0.05 x 200 ticks)
        m = c.node("m", R=None, lo=-50.0, hi=50.0, start=0.0, memory=True)
        c.node("idle", R=None, lo=0.0, hi=1.0, start=0.3, memory=True)
        c.element(m, c.node("one", bias=1.0, R=1.0), 0.05, -10.0, sigmoid=True)
        return m

    def leaky(k):                                               # a node at rest, scaled k times
        return lambda c: c.node("x", bias=0.5 * k, R=2.0 / k, C=1.0 * k)

    out = {}
    w1, w2 = spread(written, 200, 0.05), spread(written, 200, 0.025)
    want = np.sqrt(mf.SHOT * 0.05 * 200)
    out["memory written: sd at step 0.05 and 0.025, expected about %.2f" % want] = (
        (w1, w2), 0.75 < w1 / w2 < 1.33 and 0.75 < w1 / want < 1.33)
    c = mf.Circuit(seed=1)
    written(c)
    c.tick(200)
    out["memory idle: held exactly"] = (c.V[1], c.V[1] == 0.3)
    a1, a2 = spread(leaky(1), 50, 0.05), spread(leaky(1), 50, 0.025)
    out["leaky node: sd at step 0.05 and 0.025, expected about %.2f" % np.sqrt(0.01 * 2.0)] = (
        (a1, a2), 0.75 < a1 / a2 < 1.33)
    big = spread(leaky(4), 50, 0.05)
    out["the same node 4 times as big: quieter by about 2 (sqrt 4), not 4"] = ((a1, big), 1.6 < a1 / big < 2.5)
    try:
        mf.Circuit(noise=0.0)
        off = True
    except AssertionError:
        off = False
    out["the noise can't be turned off"] = (off, not off)
    return out


def check_mismatch():
    """Every part is off by about MISMATCH, each by draws of its own, also when grown in a life."""
    c = mf.Circuit(seed=3)
    for i in range(200):
        c.node(f"n{i}", bias=1.0, R=1.0, C=1.0)
        c.element(i, i, 1.0, 0.0, tau=1.0, slope=1.0)
    c._ready()
    sd = float(np.std(c.node_arr[2] - 1.0)), float(np.std(c.el_arr[0] - 1.0)), float(np.std(c.el_arr[1]))
    before = c.el_arr[0, :5].copy()
    g = c.element(0, 1, 1.0, 0.0)
    c.grow()
    kept = np.array_equal(c.el_arr[0, :5], before)
    grown = c.el_arr[0, g] != 1.0
    ok = all(0.7 * mf.MISMATCH < x < 1.3 * mf.MISMATCH for x in sd) and kept and grown
    return sd, kept, grown, ok


def check_pulse(rng):
    """A pulse brings the same charge however it falls across steps, and none before it starts."""
    worst, early = 0.0, False
    for _ in range(200):
        c = mf.Circuit(seed=0)
        c.node("x")
        c.element(0, 0, 0.0, 0.0)
        at, length = rng.uniform(0, 4), rng.uniform(0.3, 2)
        c.pulse(0, 3.0, at, length)
        worst = max(worst, abs(c.drive[:, 0].sum() * mf.DT - 3.0 * length))
        early |= bool(c.drive[: int(at / mf.DT), 0].any())
    return worst, early


def check_growth():
    """Growth during a life: splitting a synapse with a relay neuron keeps every existing node's state, and the relay
    passes spikes on (a stimulated neuron still drives its target, now through the relay)."""
    c = mf.Circuit(seed=7)
    a, b = c.neuron("a"), c.neuron("b")
    e = c.synapse(b, a, 1.0)
    before = 0
    for _ in range(200):
        c.pulse(a, 3.0, 0.0)
        before += c.tick(4)[b]
    V = c.V.copy()
    r = c.neuron("relay")
    c.redirect(e, r)
    c.synapse(b, r, 1.0)
    c.grow()
    kept = np.array_equal(c.V[:2], V)
    after = 0
    for _ in range(200):
        c.pulse(a, 3.0, 0.0)
        after += c.tick(4)[b]
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
    for what, (got, ok) in check_noise().items():
        print(f"noise, {what}: {got}: {'ok' if ok else 'FAILED'}")
        failed |= not ok
    sd, kept, grown, ok = check_mismatch()
    print(f"mismatch: spread of capacitance, gain, offset {sd[0]:.3f}, {sd[1]:.3f}, {sd[2]:.3f} (about"
          f" {mf.MISMATCH:g}); kept on growth {kept}; a grown part mismatched {grown}: {'ok' if ok else 'FAILED'}")
    failed |= not ok
    worst, early = check_pulse(rng)
    ok = worst < 1e-9 and not early
    print(f"pulses: charge right within {worst:.1e}, none early {not early}: {'ok' if ok else 'FAILED'}")
    failed |= not ok
    bad = check_world(rng, 3000)
    print(f"world, 3,000 random scenes: {'ok' if not bad else f'{bad} differ: FAILED'}")
    failed |= bool(bad)
    raise SystemExit(1 if failed else 0)
