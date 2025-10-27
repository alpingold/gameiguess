"""Combat resolution helpers."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Tuple

from . import components as c
from .status import apply_status
from .utils import clamp


@dataclass
class AttackResult:
    damage: int
    element: str
    critical: bool = False
    status_applied: str | None = None


def resolve_attack(
    attacker: c.Stats,
    defender: c.Stats,
    attacker_status: c.StatusTracker | None = None,
    defender_status: c.StatusTracker | None = None,
    rng: random.Random | None = None,
    element: str = "physical",
    base_damage: Tuple[int, int] | None = None,
    crit_chance: float = 0.1,
    status_chance: Dict[str, float] | None = None,
) -> AttackResult:
    rng = rng or random.Random()
    base_low, base_high = base_damage or (attacker.atk // 2, attacker.atk)
    raw = rng.randint(max(1, base_low), max(base_low, base_high))
    variance = rng.uniform(0.85, 1.15)
    damage = int(raw * variance)
    # defense mitigation
    mitigated = max(0, damage - defender.defense)
    crit = rng.random() < crit_chance
    if crit:
        mitigated = int(mitigated * 1.5 + attacker.atk * 0.25)
    dealt = defender.take_damage(mitigated, element)
    applied: str | None = None
    if status_chance and defender_status:
        for status, chance in status_chance.items():
            if rng.random() < chance:
                apply_status(defender_status, status)
                applied = status
                break
    return AttackResult(damage=dealt, element=element, critical=crit, status_applied=applied)


def apply_status_damage(stats: c.Stats, tracker: c.StatusTracker) -> Dict[str, int]:
    damage_log: Dict[str, int] = {}
    for effect in list(tracker.statuses):
        if effect.name in {"bleed", "burn", "poison"}:
            damage = stats.take_damage(effect.potency, effect.element)
            damage_log[effect.name] = damage
    return damage_log


def gain_xp(stats: c.Stats, reward: int) -> bool:
    stats.xp += reward
    threshold = 10 + stats.level * 5
    if stats.xp >= threshold:
        stats.level += 1
        stats.max_hp += 4
        stats.max_mp += 2
        stats.atk += 1
        stats.defense += 1
        stats.hp = stats.max_hp
        stats.mp = stats.max_mp
        stats.xp -= threshold
        return True
    return False


__all__ = ["AttackResult", "resolve_attack", "apply_status_damage", "gain_xp"]
