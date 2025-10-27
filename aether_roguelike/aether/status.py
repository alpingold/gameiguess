"""Status effect utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .components import Stats, StatusTracker, StatusEffect
from .settings import STATUS_DURATION_DEFAULT


STATUS_TEMPLATES: Dict[str, dict] = {
    "bleed": {"element": "physical", "potency": 2},
    "burn": {"element": "fire", "potency": 3},
    "freeze": {"element": "ice", "potency": 2},
    "poison": {"element": "poison", "potency": 2},
    "shock": {"element": "shock", "potency": 2},
    "slow": {"element": "physical", "potency": 0},
    "haste": {"element": "physical", "potency": 0},
}


def apply_status(tracker: StatusTracker, name: str, duration: int | None = None, potency: int | None = None) -> None:
    template = STATUS_TEMPLATES[name]
    tracker.add(
        StatusEffect(
            name=name,
            duration=duration or STATUS_DURATION_DEFAULT,
            potency=potency if potency is not None else template.get("potency", 0),
            element=template.get("element", "physical"),
        )
    )


def tick_statuses(stats: Stats, tracker: StatusTracker) -> Dict[str, StatusEffect]:
    expired = tracker.tick()
    ongoing: Dict[str, StatusEffect] = {}
    for effect in tracker.statuses:
        ongoing[effect.name] = effect
        if effect.name == "bleed":
            stats.take_damage(effect.potency, "physical")
        elif effect.name == "burn":
            stats.take_damage(effect.potency, "fire")
        elif effect.name == "poison":
            stats.take_damage(effect.potency, "poison")
        elif effect.name == "shock":
            pass
    return {effect.name: effect for effect in expired}


def base_resistances(archetype: str) -> Dict[str, float]:
    table: Dict[str, Dict[str, float]] = {
        "player": {"physical": 0.05},
        "brute": {"physical": 0.1},
        "skirmisher": {"shock": 0.1},
        "ranged": {"fire": 0.05},
        "summoner": {"poison": 0.2},
        "sapper": {"physical": 0.05, "poison": 0.1},
        "boss": {"fire": 0.15, "ice": 0.15, "poison": 0.15},
    }
    return table.get(archetype, {})


__all__ = ["apply_status", "tick_statuses", "base_resistances"]
