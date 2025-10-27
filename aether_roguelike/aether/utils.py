"""Utility helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple
import math
from collections import deque

import numpy as np


@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.w // 2, self.y + self.h // 2)

    def intersect(self, other: "Rect") -> bool:
        return not (
            other.x + other.w <= self.x
            or other.x >= self.x + self.w
            or other.y + other.h <= self.y
            or other.y >= self.y + self.h
        )


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def flood_fill(walkable: np.ndarray, start: Tuple[int, int], blocked: Iterable[Tuple[int, int]] | None = None) -> set[Tuple[int, int]]:
    blocked_set = set(blocked or [])
    width = walkable.shape[1]
    height = walkable.shape[0]
    q: deque[Tuple[int, int]] = deque()
    visited: set[Tuple[int, int]] = set()
    if not (0 <= start[0] < width and 0 <= start[1] < height):
        return visited
    if not walkable[start[1], start[0]] or start in blocked_set:
        return visited
    q.append(start)
    visited.add(start)
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if (nx, ny) in visited or (nx, ny) in blocked_set:
                continue
            if not walkable[ny, nx]:
                continue
            visited.add((nx, ny))
            q.append((nx, ny))
    return visited


def weighted_choice(rng, table: Sequence[Tuple[str, int]]) -> str:
    total = sum(weight for _, weight in table)
    roll = rng.random() * total
    upto = 0.0
    for item, weight in table:
        upto += weight
        if roll <= upto:
            return item
    return table[-1][0]


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def bresenham(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    path: List[Tuple[int, int]] = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        path.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy
    return path
