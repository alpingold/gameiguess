"""Component dataclasses."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

from .settings import ELEMENTS, STATUS_DURATION_DEFAULT


@dataclass
class Position:
    x: int
    y: int
    floor: int = 0


@dataclass
class Renderable:
    glyph: str
    fg: Tuple[int, int, int]
    bg: Tuple[int, int, int] = (0, 0, 0)
    order: int = 1


@dataclass
class Stats:
    max_hp: int
    hp: int
    max_mp: int
    mp: int
    atk: int
    defense: int
    evasion: int
    speed: int
    xp: int = 0
    level: int = 1
    resistances: Dict[str, float] = field(default_factory=lambda: {el: 0.0 for el in ELEMENTS})

    def take_damage(self, amount: int, element: str = "physical") -> int:
        resist = self.resistances.get(element, 0.0)
        mitigated = int(amount * max(0.0, 1.0 - resist))
        self.hp = max(0, self.hp - mitigated)
        return mitigated

    def heal(self, amount: int) -> int:
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before


@dataclass
class Energy:
    current: int = 0
    recovery: int = 100

    def gain(self, amount: int) -> None:
        self.current += amount

    def spend(self, amount: int) -> bool:
        if self.current >= amount:
            self.current -= amount
            return True
        return False


@dataclass
class AI:
    archetype: str
    cooldown: int = 0
    memory: Dict[str, int] = field(default_factory=dict)


@dataclass
class Item:
    name: str
    slot: Optional[str] = None
    stackable: bool = False
    quantity: int = 1
    identified: bool = False
    cursed: bool = False
    durability: Optional[int] = None
    power: int = 0
    element: str = "physical"
    description: str = ""

    def copy(self) -> "Item":
        return Item(
            name=self.name,
            slot=self.slot,
            stackable=self.stackable,
            quantity=self.quantity,
            identified=self.identified,
            cursed=self.cursed,
            durability=self.durability,
            power=self.power,
            element=self.element,
            description=self.description,
        )


@dataclass
class Inventory:
    width: int
    height: int
    items: List[Item] = field(default_factory=list)

    def capacity(self) -> int:
        return self.width * self.height

    def add(self, item: Item) -> bool:
        if item.stackable:
            for stored in self.items:
                if stored.name == item.name and stored.identified == item.identified:
                    stored.quantity += item.quantity
                    return True
        if len(self.items) >= self.capacity():
            return False
        self.items.append(item)
        return True

    def remove(self, item: Item) -> None:
        if item in self.items:
            if item.stackable and item.quantity > 1:
                item.quantity -= 1
            else:
                self.items.remove(item)


@dataclass
class Equipment:
    weapon: Optional[Item] = None
    armor: Optional[Item] = None
    ring_left: Optional[Item] = None
    ring_right: Optional[Item] = None
    charm: Optional[Item] = None

    def slots(self) -> Dict[str, Optional[Item]]:
        return {
            "weapon": self.weapon,
            "armor": self.armor,
            "ring_left": self.ring_left,
            "ring_right": self.ring_right,
            "charm": self.charm,
        }


@dataclass
class StatusEffect:
    name: str
    duration: int = STATUS_DURATION_DEFAULT
    potency: int = 0
    element: str = "physical"


@dataclass
class StatusTracker:
    statuses: List[StatusEffect] = field(default_factory=list)

    def add(self, effect: StatusEffect) -> None:
        for existing in self.statuses:
            if existing.name == effect.name:
                existing.duration = max(existing.duration, effect.duration)
                existing.potency = max(existing.potency, effect.potency)
                return
        self.statuses.append(effect)

    def tick(self) -> List[StatusEffect]:
        expired: List[StatusEffect] = []
        for effect in list(self.statuses):
            effect.duration -= 1
            if effect.duration <= 0:
                expired.append(effect)
                self.statuses.remove(effect)
        return expired


@dataclass
class Projectile:
    direction: Tuple[int, int]
    speed: int
    remaining: int
    element: str
    power: int


@dataclass
class MessageLog:
    entries: List[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        self.entries.append(message)
        self.entries = self.entries[-64:]


@dataclass
class Memory:
    explored: Dict[Tuple[int, int, int], bool] = field(default_factory=dict)


@dataclass
class LootTable:
    weights: Dict[str, int]


@dataclass
class ExperienceReward:
    amount: int
