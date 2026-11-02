"""Checks that the compiled eyes and mouth (world.py) compute what their plain description says (python
test_world.py): each against a plain numpy version of the same geometry, on random scenes crowded near the mouth.
They must agree exactly.
"""

from __future__ import annotations

import numpy as np

import world
from units import MILLI


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
    bad = check_world(np.random.default_rng(0), 3000)
    print(f"world, 3,000 random scenes: {'ok' if not bad else f'{bad} differ: FAILED'}")
    raise SystemExit(1 if bad else 0)
