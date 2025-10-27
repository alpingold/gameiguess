"""Pathfinding helpers built on tcod."""
from __future__ import annotations

from typing import Iterable, List, Tuple

import numpy as np
import tcod

from .mapgen import MapData


def astar_path(map_data: MapData, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
    walkable = map_data.walkable.astype(np.bool_)
    cost = np.where(walkable, 1.0, 0.0).astype(np.float32)
    graph = tcod.path.SimpleGraph(cost=cost.T, cardinal=2, diagonal=3)
    pathfinder = tcod.path.Pathfinder(graph)
    pathfinder.add_root(start[::-1])
    path = pathfinder.path_to(goal[::-1]).tolist()
    return [tuple(reversed(p)) for p in path]


def dijkstra_flow(map_data: MapData, goals: Iterable[Tuple[int, int]]) -> np.ndarray:
    walkable = map_data.walkable.astype(np.bool_)
    cost = np.where(walkable, 1.0, 0.0).astype(np.float32)
    graph = tcod.path.SimpleGraph(cost=cost.T, cardinal=2, diagonal=3)
    pathfinder = tcod.path.Pathfinder(graph)
    flow = np.full((map_data.height, map_data.width), np.inf, dtype=np.float32)
    for goal in goals:
        pathfinder.add_root(goal[::-1])
    pending = pathfinder.compute_map()
    flow[:] = pending.T
    return flow


__all__ = ["astar_path", "dijkstra_flow"]
