"""Enemy AI behaviours."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import random

from . import components as c
from .path import astar_path, dijkstra_flow
from .mapgen import MapData
from .utils import manhattan


@dataclass
class AIAction:
    type: str
    target: Tuple[int, int] | None = None
    payload: Dict[str, int] | None = None


class Brain:
    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()

    def decide(self, archetype: str, actor: c.Position, stats: c.Stats, map_data: MapData, player_pos: Tuple[int, int]) -> AIAction:
        distance = manhattan((actor.x, actor.y), player_pos)
        if archetype == "brute":
            if distance <= 1:
                return AIAction("attack", target=player_pos)
            path = astar_path(map_data, (actor.x, actor.y), player_pos)
            if len(path) > 1:
                return AIAction("move", target=path[1])
        elif archetype == "skirmisher":
            if 2 <= distance <= 3:
                return AIAction("attack", target=player_pos)
            if distance < 2:
                dx = actor.x - player_pos[0]
                dy = actor.y - player_pos[1]
                retreat = (actor.x + (1 if dx <= 0 else -1), actor.y + (1 if dy <= 0 else -1))
                return AIAction("move", target=retreat)
            path = astar_path(map_data, (actor.x, actor.y), player_pos)
            if len(path) > 1:
                return AIAction("move", target=path[1])
        elif archetype == "ranged":
            if distance >= 4:
                return AIAction("attack", target=player_pos)
            path = astar_path(map_data, (actor.x, actor.y), player_pos)
            if len(path) > 1:
                step = path[-min(2, len(path) - 1)]
                return AIAction("move", target=step)
        elif archetype == "summoner":
            if distance > 4:
                return AIAction("summon", target=player_pos)
            return AIAction("move", target=astar_path(map_data, (actor.x, actor.y), player_pos)[1] if distance > 1 else player_pos)
        elif archetype == "sapper":
            flow = dijkstra_flow(map_data, [player_pos])
            best_step = (actor.x, actor.y)
            best_cost = flow[actor.y, actor.x]
            for nx, ny in ((actor.x + 1, actor.y), (actor.x - 1, actor.y), (actor.x, actor.y + 1), (actor.x, actor.y - 1)):
                if 0 <= nx < map_data.width and 0 <= ny < map_data.height and flow[ny, nx] < best_cost:
                    best_cost = flow[ny, nx]
                    best_step = (nx, ny)
            if best_step != (actor.x, actor.y):
                return AIAction("move", target=best_step)
            return AIAction("trap", target=(actor.x, actor.y))
        elif archetype == "boss":
            if stats.hp <= stats.max_hp // 2 and self.rng.random() < 0.3:
                return AIAction("enrage")
            if distance <= 2:
                return AIAction("shockwave", target=player_pos)
            path = astar_path(map_data, (actor.x, actor.y), player_pos)
            if len(path) > 1:
                return AIAction("move", target=path[1])
        return AIAction("wait")


__all__ = ["AIAction", "Brain"]
