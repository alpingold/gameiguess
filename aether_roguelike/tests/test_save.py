from pathlib import Path
import random

from aether import components as c
from aether.mapgen import MapGenerator
from aether.serialization import (
    GameSnapshot,
    actor_to_snapshot,
    map_to_snapshot,
    snapshot_to_actor,
    snapshot_to_map,
)
from aether.save import load_game, save_game


def test_save_load_roundtrip(tmp_path):
    rng = random.Random(99)
    gen = MapGenerator(rng=rng)
    map_data = gen.generate("rooms")
    map_snapshot = map_to_snapshot(map_data)
    stats = c.Stats(max_hp=30, hp=28, max_mp=10, mp=10, atk=7, defense=3, evasion=5, speed=90)
    inventory = c.Inventory(width=5, height=4)
    inventory.add(c.Item(name="Potion", stackable=True, quantity=2))
    equipment = c.Equipment()
    equipment.weapon = c.Item(name="Iron Sword", slot="weapon", power=6)
    statuses = c.StatusTracker()
    actor_snapshot = actor_to_snapshot(1, c.Position(2, 2, 1), stats, inventory, equipment, statuses)
    snapshot = GameSnapshot(
        floor=1,
        seed=123,
        rng_state=(1, 2, 3),
        map=map_snapshot,
        actors=[actor_snapshot],
        log=["Test entry"],
    )
    path = tmp_path / "savegame.sav"
    save_game(path, snapshot)
    loaded = load_game(path)
    assert loaded.floor == snapshot.floor
    assert loaded.seed == snapshot.seed
    assert tuple(loaded.rng_state) == snapshot.rng_state
    loaded_map = snapshot_to_map(loaded.map)
    assert loaded_map.stairs_down == map_data.stairs_down
    loaded_actor = snapshot_to_actor(loaded.actors[0])
    assert loaded_actor["stats"].hp == stats.hp
    assert loaded_actor["inventory"].items[0].quantity == 2
