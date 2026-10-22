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
from units import C_TYP, E, I_TYP, K_B, MILLI, PULSE, Q_BIO, R_TYP, T, T_TYP, TICK

nA, Ct, Rt = I_TYP, C_TYP, R_TYP        # (a typical current, capacitor and resistor: 1 nA, 2.5 pF, 1 GOhm)


def plain_tick(c, V, Vx, armed, drive, z):
    """Steps of circuit c by the equations in mixed_feedback's docstring, plainly in numpy; drive: each step's pulse
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
        var = (c.q * gross + c.rest) * mf.DT                # the charge's variance over the step
        V = np.clip(V + (mf.DT * dV + np.sqrt(var) * z[k]) / cap, lo, hi)
        up = armed & (V > mf.SPIKE)
        spikes += up
        armed = (armed & ~up) | (V < mf.RESET)
    return V, Vx, armed, spikes


def plain_pulse(buf, node, current, at, length=PULSE):
    """A pulse by its description: each step gets the current times the share of the step within the pulse."""
    t0 = np.arange(len(buf)) * mf.DT
    buf[:, node] += current * np.clip(np.minimum(t0 + mf.DT, at + length) - np.maximum(t0, at), 0.0, None) / mf.DT


def random_circuit(rng):
    """Neurons, leaky and clamped nodes, and elements of every kind between them, some gated."""
    c = mf.Circuit(seed=int(rng.integers(1 << 30)))
    nodes = [c.neuron(f"n{i}", bias=rng.uniform(-1.8, -1.2) * nA, tau=rng.uniform(2, 20) * T_TYP) for i in range(4)]
    nodes += [c.node(f"m{i}", R=rng.choice([None, rng.uniform(0.5, 10) * Rt]), C=rng.uniform(1, 50) * Ct, lo=0.0,
                     hi=1.0, start=rng.choice([None, 0.5])) for i in range(3)]
    nodes += [c.node(f"k{i}", R=None, lo=0.0, hi=1.0, start=0.5, memory=True) for i in range(2)]
    for _ in range(12):
        to, frm = rng.choice(nodes, 2)
        c.element(int(to), int(frm), rng.uniform(-3, 3) * nA, rng.uniform(-1, 1),
                  tau=rng.choice([0.0, rng.uniform(0.2, 5) * T_TYP]),
                  slope=rng.uniform(0.5, 10), sigmoid=bool(rng.integers(2)),
                  gate=int(rng.choice([-1, *nodes[4:]])))
    return c


def check_circuit(c, inputs, ticks, rng):
    """Runs c compiled and plainly from the same state and noise, a typical time (T_TYP) at a time, with pulses at random
    moments (some running on into the next); the largest voltage difference, and whether every run's spikes agreed."""
    c._ready()
    V, Vx, armed = c.V.copy(), c.Vx.copy(), c.armed.copy()
    worst, same = 0.0, True
    per = int(round(T_TYP / mf.DT))
    buf = np.zeros((3 * per, len(c.names)))
    for t in range(ticks):
        if rng.random() < 0.3:
            node, current, at = int(rng.choice(inputs)), rng.uniform(-3, 6) * nA, rng.uniform(0, 1) * T_TYP
            c.pulse(node, current, at)
            plain_pulse(buf, node, current, at)
        state = c.rng.bit_generator.state
        z = c.rng.standard_normal((per, len(c.names)))
        c.rng.bit_generator.state = state                     # the compiled tick draws the same noise
        got = c.run(T_TYP)
        V, Vx, armed, want = plain_tick(c, V, Vx, armed, buf[:per], z)
        buf = np.concatenate([buf[per:], np.zeros((per, len(c.names)))])
        worst = max(worst, float(np.abs(V - c.V).max()))
        same &= bool(np.array_equal(got, want))
        V, Vx, armed = c.V.copy(), c.Vx.copy(), c.armed.copy()   # carry on from the compiled state
    return worst, same


def spread(build, seconds, dt, lives=100, substrate="biology"):
    """The spread (sd) over lives of one node's voltage after this long, at integration step dt: build(c) -> the node.
    Without mismatch (only here, to see the noise alone: each life's own mismatch would move its mean)."""
    old, out, mismatch = mf.DT, [], mf.MISMATCH
    mf.DT, mf.MISMATCH = dt, 0.0
    try:
        for s in range(lives):
            c = mf.Circuit(seed=1000 + s, substrate=substrate)
            n = build(c)
            c.run(seconds)
            out.append(c.V[n])
    finally:
        mf.DT, mf.MISMATCH = old, mismatch
    return float(np.std(out))


def check_noise():
    """The noise model (mixed_feedback's docstring): the same at any integration step; a memory still while idle and
    written roughly by the square root of the charge written, in charges of the substrate's events (biology's Q_BIO,
    silicon's single electrons); size buys quiet only as its square root; silicon's resting noise the thermal noise of
    a node's leak (kT/C); the noise can't be turned off."""
    def written(c):                                             # a memory written 10 V (0.05 nA for 0.5 s into 2.5 pF)
        m = c.node("m", R=None, lo=-50.0, hi=50.0, start=0.0, memory=True)
        c.node("idle", R=None, lo=0.0, hi=1.0, start=0.3, memory=True)
        c.element(m, c.node("one", bias=nA, R=Rt), 0.05 * nA, -10.0, sigmoid=True)
        return m

    def leaky(k):                                               # a node at rest, scaled k times
        return lambda c: c.node("x", bias=0.5 * k * nA, R=2.0 / k * Rt, C=k * Ct)

    out, dt = {}, mf.DT
    w1, w2 = spread(written, 0.5, dt), spread(written, 0.5, dt / 2)
    want = np.sqrt(Q_BIO * 0.05 * nA * 0.5) / Ct
    out["memory written: sd at step %g and %g s, expected about %.2f V" % (dt, dt / 2, want)] = (
        (w1, w2), 0.75 < w1 / w2 < 1.33 and 0.75 < w1 / want < 1.33)
    ws = spread(written, 0.5, dt, substrate="silicon")
    want_si = np.sqrt(E * 0.05 * nA * 0.5) / Ct
    out["silicon, memory written: sd, expected about %.1e V (single electrons)" % want_si] = (
        ws, 0.75 < ws / want_si < 1.33)
    c = mf.Circuit(seed=1)
    written(c)
    c.run(0.5)
    out["memory idle: held exactly"] = (c.V[1], c.V[1] == 0.3)
    a1, a2 = spread(leaky(1), 0.125, dt), spread(leaky(1), 0.125, dt / 2)
    out["leaky node: sd at step %g and %g s" % (dt, dt / 2)] = ((a1, a2), 0.75 < a1 / a2 < 1.33)
    big = spread(leaky(4), 0.125, dt)
    out["the same node 4 times as big: quieter by about 2 (sqrt 4), not 4"] = ((a1, big), 1.6 < a1 / big < 2.5)
    th = spread(leaky(1), 0.125, dt, substrate="silicon")
    kTC = np.sqrt(K_B * T / Ct)
    out["silicon, leaky node at rest: sd, expected about sqrt(kT/C) = %.1e V" % kTC] = (th, 0.75 < th / kTC < 1.33)
    try:
        mf.Circuit(substrate="none")
        off = True
    except AssertionError:
        off = False
    out["the noise can't be turned off"] = (off, not off)
    return out


def check_mismatch():
    """Every part is off by about MISMATCH, each by draws of its own, also when grown in a life."""
    c = mf.Circuit(seed=3)
    for i in range(200):
        c.node(f"n{i}", bias=nA, R=Rt, C=Ct)
        c.element(i, i, nA, 0.0, tau=T_TYP, slope=1.0)
    c._ready()
    sd = float(np.std(c.node_arr[2] / Ct - 1.0)), float(np.std(c.el_arr[0] / nA - 1.0)), float(np.std(c.el_arr[1]))
    before = c.el_arr[0, :5].copy()
    g = c.element(0, 1, nA, 0.0)
    c.grow()
    kept = np.array_equal(c.el_arr[0, :5], before)
    grown = c.el_arr[0, g] != nA
    ok = all(0.7 * mf.MISMATCH < x < 1.3 * mf.MISMATCH for x in sd) and kept and grown
    return sd, kept, grown, ok


def check_pulse(rng):
    """A pulse brings the same charge however it falls across steps, and none before it starts (the worst error as a
    share of the charge)."""
    worst, early = 0.0, False
    for _ in range(200):
        c = mf.Circuit(seed=0)
        c.node("x")
        c.element(0, 0, 0.0, 0.0)
        at, length = rng.uniform(0, 4) * T_TYP, rng.uniform(0.3, 2) * T_TYP
        c.pulse(0, 3 * nA, at, length)
        worst = max(worst, abs(c.drive[:, 0].sum() * mf.DT / (3 * nA * length) - 1.0))
        early |= bool(c.drive[: int(at / mf.DT), 0].any())
    return worst, early


def check_growth():
    """Growth during a life: splitting a synapse with a relay neuron keeps every existing node's state, and the relay
    passes spikes on (a stimulated neuron still drives its target, now through the relay)."""
    c = mf.Circuit(seed=7)
    a, b = c.neuron("a"), c.neuron("b")
    e = c.synapse(b, a, nA)
    before = 0
    for _ in range(200):
        c.pulse(a, 3 * nA, 0.0)
        before += c.run(TICK)[b]
    V = c.V.copy()
    r = c.neuron("relay")
    c.redirect(e, r)
    c.synapse(b, r, nA)
    c.grow()
    kept = np.array_equal(c.V[:2], V)
    after = 0
    for _ in range(200):
        c.pulse(a, 3 * nA, 0.0)
        after += c.run(TICK)[b]
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
    return far, kind, [min(1.0, v) for v in seen]


def plain_touching(body, h0, h1):
    """The mouth: the blocks within EAT of the path from h0 to h1 (sums written out, in the compiled order), and those
    within a rounding error of EAT, where the compiled code's last bit may decide the other way."""
    s = body.wrap(h1 - h0)
    ss = s[0] * s[0] + s[1] * s[1]
    out, edge = [], set()
    for b, (x, y) in enumerate(body.wrap(body.xy - h0)):
        u = min(max((x * s[0] + y * s[1]) / ss, 0.0), 1.0) if ss > 0.0 else 0.0
        e = (x - u * s[0], y - u * s[1])
        d = np.sqrt(e[0] * e[0] + e[1] * e[1])
        if d < world.EAT:
            out.append(b)
        if abs(d - world.EAT) < 1e-12:
            edge.add(b)
    return out, edge


def check_world(rng, scenes):
    """Random scenes, crowded near the mouth so that rays are blocked and blocks touch: compiled against plain."""
    bad, paths = 0, np.random.default_rng(1)            # (the mouth's paths from their own stream: the scenes as before)
    for _ in range(scenes):
        body = world.Body(np.random.default_rng(int(rng.integers(1 << 30))))
        body.pos = rng.uniform(0, world.WORLD, 2)
        body.heading = rng.uniform(-10, 10)
        h, f = body.head(), body.forward()
        near = rng.random(len(body.xy)) < 0.5                  # half the blocks just ahead, some touching the mouth
        n = int(near.sum())
        body.xy[near] = (h + f * rng.uniform(-1, 8, (n, 1)) * MILLI + rng.normal(0, 1.5, (n, 2)) * MILLI) % world.WORLD
        far, kind, seen = plain_look(body)
        _, far2, kind2 = body.look()
        seen2 = list(body.sees().values())
        h0 = (h - f * paths.uniform(0, 3) * MILLI + paths.normal(0, 0.3, 2) * MILLI) % world.WORLD  # where it came from
        (touching, edge), touching2 = plain_touching(body, h0, h), list(world._touching(body.xy, h0, h))
        touching, touching2 = [b for b in touching if b not in edge], [b for b in touching2 if b not in edge]
        bad += not (np.array_equal(far, far2) and np.array_equal(kind, kind2) and seen == seen2
                    and touching == touching2)
    return bad


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    failed = False
    b = DesignedBrain(3)
    worst, same = check_circuit(b.circuit, [*b.sensors, b.taste_node], 2000, rng)
    ok = worst < 1e-9 and same
    print(f"circuit, designed circuit, 2,000 runs of {T_TYP * 1e3:g} ms: spikes {'the same' if same else 'DIFFER'}, voltages within "
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
    print(f"circuits, 20 random, 300 runs of {T_TYP * 1e3:g} ms each:", "FAILED" if failed else "ok")
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
    print(f"pulses: charge right within {worst:.1e} of itself, none early {not early}: {'ok' if ok else 'FAILED'}")
    failed |= not ok
    bad = check_world(rng, 3000)
    print(f"world, 3,000 random scenes: {'ok' if not bad else f'{bad} differ: FAILED'}")
    failed |= bool(bad)
    raise SystemExit(1 if failed else 0)
