import random

from aether import components as c
from aether.combat import gain_xp, resolve_attack, apply_status_damage
from aether.status import apply_status


def _make_stats(hp: int = 20) -> c.Stats:
    stats = c.Stats(
        max_hp=hp,
        hp=hp,
        max_mp=5,
        mp=5,
        atk=8,
        defense=2,
        evasion=5,
        speed=90,
    )
    return stats


def test_resolve_attack_respects_resistance_and_status():
    attacker = _make_stats()
    defender = _make_stats()
    defender.resistances["fire"] = 0.5
    tracker = c.StatusTracker()
    rng = random.Random(42)
    result = resolve_attack(attacker, defender, defender_status=tracker, rng=rng, element="fire", status_chance={"burn": 1.0})
    assert result.damage >= 1
    assert defender.hp <= defender.max_hp
    assert any(s.name == "burn" for s in tracker.statuses)


def test_apply_status_damage_and_expiration():
    stats = _make_stats()
    tracker = c.StatusTracker()
    apply_status(tracker, "bleed", duration=2, potency=3)
    damage_log = apply_status_damage(stats, tracker)
    assert damage_log["bleed"] == 3
    expired = tracker.tick()
    assert not expired
    damage_log = apply_status_damage(stats, tracker)
    assert damage_log["bleed"] == 3
    tracker.tick()
    assert not tracker.statuses


def test_gain_xp_levels():
    stats = _make_stats()
    leveled = gain_xp(stats, reward=50)
    assert leveled
    assert stats.level > 1
    assert stats.hp == stats.max_hp
