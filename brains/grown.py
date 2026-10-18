"""The grown brain: a sheet of identical cells that builds itself, then learns (sheet.py, rules/). Sensor k is the
cell that named itself S(k+1), motor k the cell that named itself M(k+1), taste the cells that named themselves T;
the brain touches the sheet only through them, by name. The sheet runs SPEED updates to each tick of the world."""

from __future__ import annotations

import numpy as np

import sheet
from rules import brain, wiring

SIZE = 49           # the sheet: SIZE x SIZE cells
SPEED = 4           # the sheet's updates per tick of the world: how fast the brain runs beside the body
UPDATE = 0.9        # the chance a cell updates in an update of the sheet (never all at once)
NAME = {"S1": 1, "S2": 2, "M1": 3, "M2": 4, "T": 5}     # the names cells give themselves
DAMAGE = 7          # watching: the radius of the disc of cells damage_at replaces with new-born ones
BAND = 4            # watching: the faint checkerboard's squares, in cells


class GrownBrain:
    def __init__(self, seed: int):
        self.sheet = sheet.Sheet(brain, SIZE, seed, update=UPDATE)

    def _cells(self, name: str) -> np.ndarray:
        return self.sheet.cells("name", NAME[name])

    def stimulate(self, sensor: int) -> None:
        self.sheet.give(self._cells(f"S{sensor + 1}"), "stimulus")

    def taste(self, value: float) -> None:
        self.sheet.give(self._cells("T"), "taste", value)

    def step(self) -> list:
        """One tick of the world; the motors that fired (a motor once for each pulse its cell took)."""
        self.sheet.step(SPEED)
        return [m for m in (0, 1) for _ in range(int(self.sheet.take(self._cells(f"M{m + 1}"), f"fired_{m + 1}").sum()))]

    def drive(self, sensor: int) -> float:
        """Measuring and watching: the chance that this sensor fires both motors."""
        p = self.sheet.get(self._cells(f"S{sensor + 1}"), "p")
        return min(max(float(p.mean()) / brain.STEPS, 0.0), 1.0) if p.size else 0.5

    def built(self) -> bool:
        """Watching: whether all five organs have named themselves."""
        return len(set(np.unique(np.round(self.sheet.view("name"))).astype(int)) - {0}) == 5

    def stage(self) -> str:
        return "wiring" if self.built() else "where am I"

    def damage_at(self, fx: float, fy: float) -> None:
        """The experimenter: a disc of cells around this point of the panel (0..1 across and down) is new-born."""
        rows, cols = np.mgrid[0:SIZE, 0:SIZE]
        self.sheet.damage((rows - fy * SIZE) ** 2 + (cols - fx * SIZE) ** 2 < DAMAGE ** 2)

    def draw(self, screen, side: int, font, sensors: list, motors: list, lit) -> None:
        """Its panel, side x side at the top left, in greys: the cells' coordinates as a faint checkerboard; paths to M1
        light grey and to M2 mid grey, pulses white; the organs labelled beside their cells with their own names and
        what the body wired them to (sensors and motors: labels by number). lit: a sensor to highlight, or None."""
        import pygame
        scale = side // SIZE
        view = self.sheet.view
        cols = np.floor((view("x") + 1) / 2 * (SIZE - 1) / BAND + 0.5)     # the cells' coordinates, in bands of cells
        rows = np.floor((view("y") + 1) / 2 * (SIZE - 1) / BAND + 0.5)
        shade = 0.06 + 0.08 * ((cols + rows) % 2)
        for c, level in (("2", 0.45), ("1", 0.75)):
            on = view(f"on_{c}") > 0.5
            shade = np.where(on, np.maximum(shade, level), shade)
            shade = np.where(on & (np.round(view(f"timer_{c}")) > wiring.REST), 1.0, shade)
        names = np.round(view("name"))
        taste = names == NAME["T"]
        shade = np.where(taste, np.where(np.round(view("tshow")) != 0, 1.0, 0.3), shade)   # tasting: white
        grey = (255 * shade).astype(np.uint8).T.repeat(scale, 0).repeat(scale, 1)
        screen.blit(pygame.surfarray.make_surface(np.stack([grey] * 3, axis=-1)), (0, 0))
        if taste.any():                                                 # the taste organ: one label, beside it
            r, c = np.argwhere(taste).mean(axis=0)
            label = font.render("T taste", True, (255, 255, 255), (60, 60, 60))
            w, h = label.get_size()
            px = c * scale - w // 2 if 0 < c < SIZE - 1 else (c * scale + scale + 3 if c == 0 else c * scale - w - 3)
            py = r * scale + 2 * scale + 3 if r < SIZE / 2 else r * scale - h - 2 * scale
            if 0 < r < SIZE - 1:
                py = r * scale - h // 2
            screen.blit(label, (min(max(0, int(px)), side - w), min(max(0, int(py)), side - h)))
        for k in np.unique(names[(names > 0) & ~taste]):
            own = next(n for n, v in NAME.items() if v == k)
            index = int(own[1]) - 1
            role = (sensors if own[0] == "S" else motors)[index]
            hot = own[0] == "S" and lit == index
            for r, c in np.argwhere(names == k):
                label = font.render(f"{own} {role}", True, (0, 0, 0) if hot else (255, 255, 255),
                                    (255, 255, 255) if hot else (60, 60, 60))
                w, h = label.get_size()                                 # beside the cell, inside the sheet
                px = c * scale + scale + 3 if c == 0 else c * scale - w - 3 if c == SIZE - 1 else c * scale - w // 2
                py = r * scale + scale + 3 if r == 0 else r * scale - h - 3 if r == SIZE - 1 else r * scale - h // 2
                if k % 2 == 0 and r in (0, SIZE - 1):              # the pair sit close on one edge: stagger them
                    py += h if r == 0 else -h
                screen.blit(label, (min(max(0, px), side - w), min(max(0, py), side - h)))
