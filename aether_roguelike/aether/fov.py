"""Field-of-view helper using tcod."""
from __future__ import annotations

from typing import Tuple

import numpy as np
import tcod

from .mapgen import MapData


def compute_fov(map_data: MapData, origin: Tuple[int, int], radius: int = 8, light_walls: bool = True) -> np.ndarray:
    transparency = map_data.transparent.astype(np.bool_)
    tcod_map = tcod.map.Map(width=map_data.width, height=map_data.height, order="F")
    tcod_map.transparent[:] = transparency.T
    tcod_map.walkable[:] = map_data.walkable.T
    fov = tcod.map.compute_fov(
        transparency=tcod_map.transparent,
        pov=origin[::-1],
        radius=radius,
        algorithm=tcod.FOV_SHADOW,
        light_walls=light_walls,
    )
    return fov.T


__all__ = ["compute_fov"]
