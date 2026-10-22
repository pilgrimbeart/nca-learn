"""Measures the wiring rule on the 49 sheet: send pulses from S1 and S2 down each channel; how many arrive, how soon,
and how many arrive more than once (a fork in a path doubles a pulse).

    python measure_wiring.py [LIVES] [WARMUP]
"""
import sys, time, numpy as np
import sheet
from rules import wiring

N = 49
UPDATE = 0.9        # as in the creature
NAMES = {1: "S1", 2: "S2", 3: "M1", 4: "M2"}


def life(seed, warmup, trials=40, wait=300, after=60):
    """Each trial sends one pulse; counts how many reach the sink (exactly one is right) and when the first did."""
    s = sheet.Sheet(wiring, N, seed, update=UPDATE)
    s.step(warmup)
    paths = [int((s.view(f"on_{c}") > 0.5).sum()) for c in "12"]
    got, late, extra = {}, {}, 0
    rng = np.random.default_rng(seed)
    for i in range(trials):
        src, ch = 1 + i % 2, (i // 2) % 2
        sink, c = 3 + ch, "12"[ch]
        s.take(s.cells("name", sink), f"fired_{c}")
        s.give(s.cells("name", src), f"send_{c}")
        arrived, first = 0, None
        for t in range(wait):
            s.step(1)
            arrived += int(s.take(s.cells("name", sink), f"fired_{c}").sum())
            if arrived and first is None:
                first = t
            if first is not None and t > first + after:
                break
        if first is not None:
            late.setdefault((src, ch), []).append(first)
            got[(src, ch)] = got.get((src, ch), 0) + 1
            extra += arrived - 1
        s.step(int(rng.integers(20, 40)))
    return paths, got, late, trials // 4, extra


if __name__ == "__main__":
    lives = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    warmup = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    for seed in range(lives):
        t0 = time.time()
        paths, got, late, each, extra = life(seed, warmup)
        parts = [f"{NAMES[src]}->{NAMES[3 + ch]} {got.get((src, ch), 0)}/{each} in {np.mean(late.get((src, ch), [np.nan])):.0f}"
                 for src in (1, 2) for ch in (0, 1)]
        print(f"seed {seed}: path cells to M1 {paths[0]}, to M2 {paths[1]};  arrived, mean steps: {'  '.join(parts)}"
              f";  extra arrivals {extra}  ({time.time() - t0:.0f}s)", flush=True)
