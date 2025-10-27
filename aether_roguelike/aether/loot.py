"""Loot table helpers."""
from __future__ import annotations

from typing import Dict, Tuple
import random

from . import components as c
from .utils import weighted_choice


WEAPON_TABLE: Dict[str, list[Tuple[str, int]]] = {
    "default": [
        ("Rusty Dagger", 5),
        ("Iron Sword", 8),
        ("Glacial Shortsword of Haste", 1),
    ]
}

ARMOR_TABLE: Dict[str, list[Tuple[str, int]]] = {
    "default": [
        ("Tattered Robe", 6),
        ("Chainmail", 4),
        ("Aetheric Aegis", 1),
    ]
}

CONSUMABLE_TABLE: Dict[str, list[Tuple[str, int]]] = {
    "default": [
        ("Potion of Healing", 8),
        ("Scroll of Firebolt", 4),
        ("Scroll of Blink", 4),
        ("Scroll of Reveal", 3),
        ("Scroll of Silence", 2),
    ]
}


def create_item_from_name(name: str) -> c.Item:
    if "Sword" in name:
        return c.Item(name=name, slot="weapon", power=6, description="A reliable blade.")
    if "Dagger" in name:
        return c.Item(name=name, slot="weapon", power=4, description="Light but weak.")
    if "Chainmail" in name or "Robe" in name or "Aegis" in name:
        return c.Item(name=name, slot="armor", power=2, description="Protective garb.")
    if "Potion" in name:
        return c.Item(name=name, stackable=True, quantity=1, description="Restores HP.")
    if "Scroll" in name:
        return c.Item(name=name, stackable=True, quantity=1, description="Casts a spell.")
    return c.Item(name=name)


def roll_loot(rng: random.Random, floor: int) -> c.Item:
    table_key = "default"
    roll_type = weighted_choice(rng, [("weapon", 3 + floor), ("armor", 2 + floor), ("consumable", 6 + floor * 2)])
    if roll_type == "weapon":
        name = weighted_choice(rng, WEAPON_TABLE[table_key])
    elif roll_type == "armor":
        name = weighted_choice(rng, ARMOR_TABLE[table_key])
    else:
        name = weighted_choice(rng, CONSUMABLE_TABLE[table_key])
    return create_item_from_name(name)


__all__ = ["roll_loot", "create_item_from_name"]
