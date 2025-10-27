"""Serialization helpers for saving/loading game state."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Tuple
import numpy as np

from . import components as c
from .mapgen import MapData


@dataclass
class ActorSnapshot:
    entity_id: int
    position: Tuple[int, int, int]
    stats: Dict[str, Any]
    inventory: List[Dict[str, Any]]
    equipment: Dict[str, Any]
    statuses: List[Dict[str, Any]]


@dataclass
class MapSnapshot:
    width: int
    height: int
    tiles: List[int]
    start: Tuple[int, int]
    stairs_up: Tuple[int, int]
    stairs_down: Tuple[int, int]
    locked_doors: List[Tuple[int, int]]
    key_positions: List[Tuple[int, int]]


@dataclass
class GameSnapshot:
    floor: int
    seed: int
    rng_state: Tuple[Any, ...]
    map: MapSnapshot
    actors: List[ActorSnapshot]
    log: List[str]


def map_to_snapshot(map_data: MapData) -> MapSnapshot:
    return MapSnapshot(
        width=map_data.width,
        height=map_data.height,
        tiles=map_data.tiles.astype(int).ravel().tolist(),
        start=map_data.start,
        stairs_up=map_data.stairs_up,
        stairs_down=map_data.stairs_down,
        locked_doors=list(map(tuple, map_data.locked_doors)),
        key_positions=list(map(tuple, map_data.key_positions)),
    )


def snapshot_to_map(snapshot: MapSnapshot) -> MapData:
    tiles = np.array(snapshot.tiles, dtype=np.int8).reshape((snapshot.height, snapshot.width))
    return MapData(
        width=snapshot.width,
        height=snapshot.height,
        tiles=tiles,
        start=snapshot.start,
        stairs_up=snapshot.stairs_up,
        stairs_down=snapshot.stairs_down,
        locked_doors=list(snapshot.locked_doors),
        key_positions=list(snapshot.key_positions),
    )


def actor_to_snapshot(
    entity_id: int,
    position: c.Position,
    stats: c.Stats,
    inventory: c.Inventory | None,
    equipment: c.Equipment | None,
    statuses: c.StatusTracker | None,
) -> ActorSnapshot:
    items = []
    if inventory:
        items = [asdict(item) for item in inventory.items]
    equip_data: Dict[str, Any] = {}
    if equipment:
        for slot, item in equipment.slots().items():
            equip_data[slot] = asdict(item) if item else None
    status_list = []
    if statuses:
        status_list = [asdict(effect) for effect in statuses.statuses]
    return ActorSnapshot(
        entity_id=entity_id,
        position=(position.x, position.y, position.floor),
        stats=asdict(stats),
        inventory=items,
        equipment=equip_data,
        statuses=status_list,
    )


def snapshot_to_actor(snapshot: ActorSnapshot) -> Dict[str, Any]:
    stats = c.Stats(**snapshot.stats)
    inventory = c.Inventory(width=5, height=4)
    inventory.items = [c.Item(**item) for item in snapshot.inventory]
    equipment = c.Equipment()
    for slot, item in snapshot.equipment.items():
        if item:
            setattr(equipment, slot, c.Item(**item))
    statuses = c.StatusTracker()
    for status in snapshot.statuses:
        statuses.add(c.StatusEffect(**status))
    position = c.Position(*snapshot.position)
    return {
        "entity_id": snapshot.entity_id,
        "position": position,
        "stats": stats,
        "inventory": inventory,
        "equipment": equipment,
        "statuses": statuses,
    }


def game_snapshot_to_dict(snapshot: GameSnapshot) -> Dict[str, Any]:
    return {
        "floor": snapshot.floor,
        "seed": snapshot.seed,
        "rng_state": list(snapshot.rng_state),
        "map": asdict(snapshot.map),
        "actors": [asdict(actor) for actor in snapshot.actors],
        "log": snapshot.log,
    }


def dict_to_game_snapshot(data: Dict[str, Any]) -> GameSnapshot:
    map_snapshot = MapSnapshot(**data["map"])
    actors = [ActorSnapshot(**actor) for actor in data["actors"]]
    return GameSnapshot(
        floor=data["floor"],
        seed=data["seed"],
        rng_state=tuple(data["rng_state"]),
        map=map_snapshot,
        actors=actors,
        log=list(data.get("log", [])),
    )


__all__ = [
    "GameSnapshot",
    "MapSnapshot",
    "ActorSnapshot",
    "map_to_snapshot",
    "snapshot_to_map",
    "actor_to_snapshot",
    "snapshot_to_actor",
    "game_snapshot_to_dict",
    "dict_to_game_snapshot",
]
