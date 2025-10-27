"""Inventory helpers."""
from __future__ import annotations

from typing import List

from . import components as c


EQUIP_ORDER = ["weapon", "armor", "ring_left", "ring_right", "charm"]


def equip_item(equipment: c.Equipment, item: c.Item) -> bool:
    if not item.slot:
        return False
    slot = item.slot
    if slot == "ring" and equipment.ring_left and equipment.ring_right:
        return False
    if slot == "ring":
        target = "ring_left" if equipment.ring_left is None else "ring_right"
        setattr(equipment, target, item)
        return True
    setattr(equipment, slot, item)
    return True


def unequip_item(equipment: c.Equipment, slot: str) -> c.Item | None:
    if slot == "ring":
        if equipment.ring_right:
            item = equipment.ring_right
            equipment.ring_right = None
            return item
        item = equipment.ring_left
        equipment.ring_left = None
        return item
    item = getattr(equipment, slot, None)
    setattr(equipment, slot, None)
    return item


def list_equipped(equipment: c.Equipment) -> List[c.Item]:
    items: List[c.Item] = []
    for slot in EQUIP_ORDER:
        item = getattr(equipment, slot, None)
        if item:
            items.append(item)
    return items
