"""Procedural map generation routines."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Iterable, Iterator, List, Tuple
import math
import random

import numpy as np

from .settings import MAP_WIDTH, MAP_HEIGHT
from .utils import Rect, flood_fill, manhattan


class Tile(IntEnum):
    WALL = 0
    FLOOR = 1
    DOOR = 2
    LOCKED_DOOR = 3
    STAIRS_UP = 4
    STAIRS_DOWN = 5
    ACID = 6
    LAVA = 7
    TRAP = 8


@dataclass
class MapData:
    width: int
    height: int
    tiles: np.ndarray
    start: Tuple[int, int]
    stairs_up: Tuple[int, int]
    stairs_down: Tuple[int, int]
    locked_doors: List[Tuple[int, int]] = field(default_factory=list)
    key_positions: List[Tuple[int, int]] = field(default_factory=list)
    door_keys: Dict[Tuple[int, int], Tuple[int, int]] = field(default_factory=dict)
    hazards: List[Tuple[int, int]] = field(default_factory=list)
    trap_hints: List[Tuple[int, int]] = field(default_factory=list)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def tile_at(self, x: int, y: int) -> Tile:
        return Tile(self.tiles[y, x])

    @property
    def walkable(self) -> np.ndarray:
        walk = np.isin(self.tiles, [Tile.FLOOR, Tile.DOOR, Tile.LOCKED_DOOR, Tile.STAIRS_UP, Tile.STAIRS_DOWN, Tile.ACID, Tile.LAVA, Tile.TRAP])
        return walk

    @property
    def transparent(self) -> np.ndarray:
        return np.isin(self.tiles, [Tile.FLOOR, Tile.DOOR, Tile.LOCKED_DOOR, Tile.STAIRS_UP, Tile.STAIRS_DOWN, Tile.ACID, Tile.LAVA, Tile.TRAP])

    def reachable(self, start: Tuple[int, int], blocked: Iterable[Tuple[int, int]] | None = None) -> set[Tuple[int, int]]:
        blocked_set = set(blocked or [])
        return flood_fill(self.walkable, start, blocked=blocked_set)


@dataclass
class MapGenerator:
    width: int = MAP_WIDTH
    height: int = MAP_HEIGHT
    floor: int = 1
    rng: random.Random = field(default_factory=random.Random)
    _start_position: Tuple[int, int] | None = None

    def generate(self, layout: str = "rooms") -> MapData:
        if layout == "caves":
            base = self._generate_caves()
        else:
            base = self._generate_rooms()
        self._post_process(base)
        return base

    def _generate_rooms(self) -> MapData:
        tiles = np.full((self.height, self.width), Tile.WALL, dtype=np.int8)
        rooms: List[Rect] = []
        max_rooms = 12
        min_size, max_size = 5, 10
        attempts = 0
        while len(rooms) < max_rooms and attempts < 200:
            w = self.rng.randint(min_size, max_size)
            h = self.rng.randint(min_size, max_size)
            x = self.rng.randint(1, self.width - w - 1)
            y = self.rng.randint(1, self.height - h - 1)
            new_room = Rect(x, y, w, h)
            if any(new_room.intersect(room) for room in rooms):
                attempts += 1
                continue
            rooms.append(new_room)
            tiles[new_room.y : new_room.y + new_room.h, new_room.x : new_room.x + new_room.w] = Tile.FLOOR

        def carve_corridor(a: Tuple[int, int], b: Tuple[int, int]) -> None:
            ax, ay = a
            bx, by = b
            if self.rng.random() < 0.5:
                self._carve_h(tiles, ax, bx, ay)
                self._carve_v(tiles, ay, by, bx)
            else:
                self._carve_v(tiles, ay, by, ax)
                self._carve_h(tiles, ax, bx, by)

        for i in range(1, len(rooms)):
            prev = rooms[i - 1].center
            cur = rooms[i].center
            carve_corridor(prev, cur)

        if not rooms:
            raise RuntimeError("Failed to generate rooms")
        start_room = rooms[0]
        start = start_room.center
        self._start_position = start
        stairs_down = max(rooms, key=lambda r: manhattan(r.center, start)).center
        tiles[start[1], start[0]] = Tile.STAIRS_UP
        self._start_position = start
        tiles[stairs_down[1], stairs_down[0]] = Tile.STAIRS_DOWN
        return MapData(
            width=self.width,
            height=self.height,
            tiles=tiles,
            start=start,
            stairs_up=start,
            stairs_down=stairs_down,
        )

    def _generate_caves(self) -> MapData:
        tiles = np.full((self.height, self.width), Tile.WALL, dtype=np.int8)
        fill_prob = 0.45
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                tiles[y, x] = Tile.FLOOR if self.rng.random() > fill_prob else Tile.WALL
        for _ in range(5):
            tiles = self._smooth(tiles)
        walkable_positions = np.argwhere(tiles == Tile.FLOOR)
        if walkable_positions.size == 0:
            raise RuntimeError("No floor tiles in cave generation")
        start_idx = self.rng.randrange(len(walkable_positions))
        start = tuple(int(v) for v in walkable_positions[start_idx][::-1])
        reachable = flood_fill(tiles == Tile.FLOOR, start)
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in reachable:
                    tiles[y, x] = Tile.WALL
        floors = np.argwhere(tiles == Tile.FLOOR)
        end = tuple(int(v) for v in floors[self.rng.randrange(len(floors))][::-1])
        tiles[start[1], start[0]] = Tile.STAIRS_UP
        self._start_position = start
        tiles[end[1], end[0]] = Tile.STAIRS_DOWN
        return MapData(
            width=self.width,
            height=self.height,
            tiles=tiles,
            start=start,
            stairs_up=start,
            stairs_down=end,
        )

    def _post_process(self, data: MapData) -> None:
        walkable_positions = list(map(tuple, np.argwhere(data.walkable)[:, ::-1]))
        self.rng.shuffle(walkable_positions)
        hazards = walkable_positions[: max(3, len(walkable_positions) // 40)]
        for (x, y) in hazards:
            if data.tile_at(x, y) == Tile.FLOOR:
                tile = Tile.ACID if self.rng.random() < 0.5 else Tile.LAVA
                data.tiles[y, x] = tile
                data.hazards.append((x, y))
        # Place traps with hints
        trap_candidates = [pos for pos in walkable_positions if data.tile_at(*pos) == Tile.FLOOR]
        for (x, y) in trap_candidates[: len(trap_candidates) // 30 + 1]:
            data.tiles[y, x] = Tile.TRAP
            data.trap_hints.extend(self._ring_positions(x, y))
        # Doors along corridors: convert chokepoints
        doors: List[Tuple[int, int]] = []
        for y in range(1, data.height - 1):
            for x in range(1, data.width - 1):
                if data.tile_at(x, y) != Tile.FLOOR:
                    continue
                neighbours = [data.tile_at(nx, ny) for nx, ny in self._cardinal_neighbours(x, y)]
                if neighbours.count(Tile.WALL) >= 2 and neighbours.count(Tile.FLOOR) >= 2:
                    data.tiles[y, x] = Tile.DOOR
                    doors.append((x, y))
        if doors:
            locked = doors[self.rng.randrange(len(doors))]
            data.tiles[locked[1], locked[0]] = Tile.LOCKED_DOOR
            data.locked_doors.append(locked)
            accessible_without_lock = data.reachable(data.start, blocked=[locked])
            key_position = self._pick_key_position(accessible_without_lock)
            if key_position:
                data.key_positions.append(key_position)
                data.door_keys[locked] = key_position
        # Guarantee stairs reachable
        reachable = data.reachable(data.start, blocked=data.locked_doors)
        if data.stairs_down not in reachable:
            self._ensure_connection(data, reachable)

    def _pick_key_position(self, reachable: Iterable[Tuple[int, int]]) -> Tuple[int, int] | None:
        reachable_list = list(reachable)
        if not reachable_list:
            return None
        self.rng.shuffle(reachable_list)
        for pos in reachable_list:
            if pos != (self._start_position or reachable_list[0]):
                return pos
        return reachable_list[0]

    def _ensure_connection(self, data: MapData, reachable: set[Tuple[int, int]]) -> None:
        queue = [data.stairs_down]
        visited: set[Tuple[int, int]] = set()
        while queue:
            x, y = queue.pop(0)
            if (x, y) in reachable:
                path = self._trace_back((x, y), data.start)
                for px, py in path:
                    if data.tile_at(px, py) == Tile.WALL:
                        data.tiles[py, px] = Tile.FLOOR
                return
            visited.add((x, y))
            for nx, ny in self._cardinal_neighbours(x, y):
                if not data.in_bounds(nx, ny):
                    continue
                if (nx, ny) in visited:
                    continue
                if data.tile_at(nx, ny) == Tile.WALL:
                    continue
                queue.append((nx, ny))

    def _trace_back(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        path: List[Tuple[int, int]] = []
        x, y = start
        gx, gy = goal
        while (x, y) != (gx, gy):
            path.append((x, y))
            if x < gx:
                x += 1
            elif x > gx:
                x -= 1
            if y < gy:
                y += 1
            elif y > gy:
                y -= 1
        return path

    def _carve_h(self, tiles: np.ndarray, x1: int, x2: int, y: int) -> None:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            tiles[y, x] = Tile.FLOOR

    def _carve_v(self, tiles: np.ndarray, y1: int, y2: int, x: int) -> None:
        for y in range(min(y1, y2), max(y1, y2) + 1):
            tiles[y, x] = Tile.FLOOR

    def _smooth(self, tiles: np.ndarray) -> np.ndarray:
        new_tiles = tiles.copy()
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                neighbours = self._count_neighbours(tiles, x, y)
                if neighbours > 4:
                    new_tiles[y, x] = Tile.WALL
                elif neighbours < 4:
                    new_tiles[y, x] = Tile.FLOOR
        return new_tiles

    def _count_neighbours(self, tiles: np.ndarray, x: int, y: int) -> int:
        total = 0
        for ny in range(y - 1, y + 2):
            for nx in range(x - 1, x + 2):
                if nx == x and ny == y:
                    continue
                if tiles[ny, nx] == Tile.WALL:
                    total += 1
        return total

    def _cardinal_neighbours(self, x: int, y: int) -> List[Tuple[int, int]]:
        return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

    def _ring_positions(self, x: int, y: int) -> List[Tuple[int, int]]:
        ring: List[Tuple[int, int]] = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    ring.append((nx, ny))
        return ring


def generate_floor(seed: int, floor: int, layout: str) -> MapData:
    rng = random.Random(seed + floor * 97)
    gen = MapGenerator(floor=floor, rng=rng)
    return gen.generate(layout)


__all__ = ["Tile", "MapData", "MapGenerator", "generate_floor"]
