"""Core systems used by the game loop."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple
import pygame

from . import components as c
from .ecs import World
from .fov import compute_fov
from .mapgen import MapData, Tile
from .settings import TILE_SIZE


@dataclass
class TurnQueue:
    order: List[int]
    index: int = 0

    def current(self) -> int | None:
        if not self.order:
            return None
        return self.order[self.index % len(self.order)]

    def advance(self) -> None:
        if self.order:
            self.index = (self.index + 1) % len(self.order)


class FOVSystem:
    def __init__(self) -> None:
        self.visible: Dict[int, Tuple[int, int]] = {}

    def update(self, world: World, map_data: MapData, radius: int = 8) -> Dict[Tuple[int, int], bool]:
        player = next(iter(world.tagged.get("player", [])))
        position = world.get_component(player, c.Position)
        fov = compute_fov(map_data, (position.x, position.y), radius)
        visible: Dict[Tuple[int, int], bool] = {}
        for y in range(map_data.height):
            for x in range(map_data.width):
                visible[(x, y)] = bool(fov[x, y])
        return visible


class RenderSystem:
    def __init__(self, surface: pygame.Surface) -> None:
        self.surface = surface

    def draw_map(self, map_data: MapData, visible: Dict[Tuple[int, int], bool], explored: Dict[Tuple[int, int], bool]) -> None:
        for y in range(map_data.height):
            for x in range(map_data.width):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                tile = map_data.tile_at(x, y)
                base_color = (20, 20, 30)
                if tile == Tile.FLOOR:
                    base_color = (40, 40, 60)
                elif tile == Tile.DOOR:
                    base_color = (90, 60, 40)
                elif tile == Tile.LOCKED_DOOR:
                    base_color = (120, 70, 40)
                elif tile == Tile.STAIRS_UP:
                    base_color = (80, 120, 80)
                elif tile == Tile.STAIRS_DOWN:
                    base_color = (80, 80, 120)
                elif tile == Tile.ACID:
                    base_color = (40, 120, 40)
                elif tile == Tile.LAVA:
                    base_color = (180, 60, 20)
                elif tile == Tile.TRAP:
                    base_color = (80, 40, 80)
                visible_now = visible.get((x, y), False)
                if visible_now:
                    explored[(x, y)] = True
                    color = base_color
                elif explored.get((x, y)):
                    color = tuple(int(c * 0.3) for c in base_color)
                else:
                    color = (10, 10, 15)
                pygame.draw.rect(self.surface, color, rect)

    def draw_entities(self, world: World, visible: Dict[Tuple[int, int], bool]) -> None:
        ordered: List[Tuple[int, c.Renderable]] = []
        for entity, (pos,) in world.entities_with(c.Position):
            renderable = world.try_component(entity, c.Renderable)
            if not renderable:
                continue
            if not visible.get((pos.x, pos.y), False):
                continue
            ordered.append((entity, renderable))
        ordered.sort(key=lambda item: item[1].order)
        for entity, renderable in ordered:
            pos = world.get_component(entity, c.Position)
            rect = pygame.Rect(pos.x * TILE_SIZE, pos.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.surface, renderable.bg, rect)
            text_surf = pygame.font.SysFont("consolas", 18).render(renderable.glyph, True, renderable.fg)
            self.surface.blit(text_surf, (rect.x + 4, rect.y + 2))


__all__ = ["TurnQueue", "FOVSystem", "RenderSystem"]
