"""Entity factory helpers."""
from __future__ import annotations

import random
from typing import Dict, Tuple

from . import components as c
from .ecs import World
from .status import base_resistances
from .settings import PLAYER_START_HP, PLAYER_START_MP


COLORS: Dict[str, Tuple[int, int, int]] = {
    "player": (200, 240, 255),
    "brute": (200, 40, 40),
    "skirmisher": (220, 180, 60),
    "ranged": (120, 200, 255),
    "summoner": (180, 120, 200),
    "sapper": (90, 180, 90),
    "boss": (255, 120, 40),
    "item": (220, 220, 220),
    "hazard": (140, 40, 40),
}


def create_player(world: World, x: int, y: int) -> int:
    stats = c.Stats(
        max_hp=PLAYER_START_HP,
        hp=PLAYER_START_HP,
        max_mp=PLAYER_START_MP,
        mp=PLAYER_START_MP,
        atk=6,
        defense=3,
        evasion=5,
        speed=90,
    )
    stats.resistances.update(base_resistances("player"))
    entity = world.create_entity(
        c.Position(x, y, 0),
        c.Renderable("@", COLORS["player"], order=5),
        stats,
        c.Energy(current=0, recovery=stats.speed),
        c.Inventory(width=5, height=4),
        c.Equipment(),
        c.StatusTracker(),
        c.MessageLog(),
        tags=["player"],
    )
    return entity


def create_monster(world: World, archetype: str, x: int, y: int, floor: int) -> int:
    rng = random.Random(floor * 1337 + x * 17 + y * 31)
    hp = rng.randint(8, 18) + floor * 2
    mp = rng.randint(0, 6) + floor
    atk = rng.randint(4, 8) + floor
    defense = rng.randint(1, 5) + floor // 2
    evasion = rng.randint(2, 6) + floor
    speed = 100 - min(20, floor * 2)
    stats = c.Stats(
        max_hp=hp,
        hp=hp,
        max_mp=mp,
        mp=mp,
        atk=atk,
        defense=defense,
        evasion=evasion,
        speed=speed,
    )
    stats.resistances.update(base_resistances(archetype))
    glyphs = {
        "brute": "B",
        "skirmisher": "S",
        "ranged": "R",
        "summoner": "Σ",
        "sapper": "τ",
        "boss": "Ω",
    }
    render = c.Renderable(glyphs.get(archetype, "?"), COLORS.get(archetype, (200, 200, 200)), order=4)
    return world.create_entity(
        c.Position(x, y, floor),
        render,
        stats,
        c.Energy(current=0, recovery=stats.speed),
        c.AI(archetype=archetype),
        c.StatusTracker(),
        c.ExperienceReward(amount=5 + floor * 2),
        tags=["monster"],
    )


def create_item(world: World, item: c.Item, x: int, y: int, floor: int) -> int:
    return world.create_entity(
        c.Position(x, y, floor),
        c.Renderable("!", COLORS["item"], order=2),
        item,
        tags=["item"],
    )


def create_hazard(world: World, glyph: str, x: int, y: int, floor: int) -> int:
    color = COLORS["hazard"] if glyph == "~" else (255, 80, 80)
    return world.create_entity(
        c.Position(x, y, floor),
        c.Renderable(glyph, color, order=1),
        tags=["hazard"],
    )
