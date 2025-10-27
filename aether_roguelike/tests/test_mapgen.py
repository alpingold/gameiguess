import random

import numpy as np

from aether.mapgen import MapGenerator, Tile, generate_floor


def test_rooms_map_connectivity_and_density():
    gen = MapGenerator(rng=random.Random(1234))
    data = gen.generate("rooms")
    reachable = data.reachable(data.start, blocked=data.locked_doors)
    assert data.stairs_down in reachable
    floors = np.count_nonzero(data.tiles != Tile.WALL)
    density = floors / data.tiles.size
    assert 0.28 <= density <= 0.72
    for door in data.locked_doors:
        key = data.door_keys.get(door)
        assert key is not None
        accessible = data.reachable(data.start, blocked=[door])
        assert key in accessible


def test_caves_map_stairs_reachable():
    gen = MapGenerator(rng=random.Random(4321))
    data = gen.generate("caves")
    reachable = data.reachable(data.start)
    assert data.stairs_down in reachable


def test_generate_floor_deterministic():
    floor_a = generate_floor(101, 2, "rooms")
    floor_b = generate_floor(101, 2, "rooms")
    assert np.array_equal(floor_a.tiles, floor_b.tiles)
    assert floor_a.stairs_down == floor_b.stairs_down
