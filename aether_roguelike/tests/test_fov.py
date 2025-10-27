import numpy as np

from aether.mapgen import MapData, Tile
from aether.fov import compute_fov


def test_fov_blocked_by_wall():
    tiles = np.full((5, 5), Tile.WALL, dtype=np.int8)
    tiles[2, 1:4] = Tile.FLOOR
    tiles[1:4, 2] = Tile.FLOOR
    tiles[2, 2] = Tile.FLOOR
    tiles[2, 3] = Tile.WALL  # blocking tile
    data = MapData(
        width=5,
        height=5,
        tiles=tiles,
        start=(1, 2),
        stairs_up=(1, 2),
        stairs_down=(3, 2),
    )
    origin = (1, 2)
    fov = compute_fov(data, origin, radius=3)
    assert fov[1, 2]
    assert not fov[3, 2]
    assert fov[2, 1]
