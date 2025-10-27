"""Game orchestration."""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pygame

from . import components as c
from .ai import Brain
from .combat import gain_xp, resolve_attack
from .entities import create_item, create_monster, create_player
from .fov import compute_fov
from .mapgen import MapData, Tile, generate_floor
from .settings import (
    DEFAULT_INTERNAL_RESOLUTION,
    MAX_FLOORS,
    Settings,
)
from .systems import RenderSystem
from .ui import UIManager
from .loot import roll_loot


@dataclass
class FloorState:
    map_data: MapData
    visible: Dict[Tuple[int, int], bool]
    explored: Dict[Tuple[int, int], bool]


class Game:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        pygame.init()
        pygame.display.set_caption("Caverns of Aether — Advanced Edition")
        internal_w, internal_h = DEFAULT_INTERNAL_RESOLUTION
        self.internal_surface = pygame.Surface((internal_w, internal_h))
        flags = pygame.SCALED | pygame.RESIZABLE
        if settings.fullscreen:
            flags |= pygame.FULLSCREEN
        self.window = pygame.display.set_mode(
            (internal_w * settings.scale, internal_h * settings.scale), flags, vsync=1 if settings.vsync else 0
        )
        self.clock = pygame.time.Clock()
        self.ui = UIManager((internal_w, internal_h))
        from .ecs import World  # late import to avoid circular

        self._world_cls = World
        self.world = self._world_cls()
        self.player: int = 0
        self.floor = 1
        self.seed = settings.seed or random.randint(0, 999999)
        self.rng = random.Random(self.seed)
        self.brain = Brain(self.rng)
        self.map_state: FloorState | None = None
        self.message_log = c.MessageLog()
        self.player_stats: c.Stats | None = None
        self.running = True
        self.aether_core_retrieved = False
        self.keyring: set[str] = set()

    def new_game(self) -> None:
        self.world = self._world_cls()
        self.message_log = c.MessageLog()
        self.keyring = set()
        self.floor = 1
        map_data = generate_floor(self.seed, self.floor, self.settings.generator)
        self.map_state = FloorState(map_data=map_data, visible={}, explored={})
        self.player = create_player(self.world, *map_data.start)
        self.player_stats = self.world.get_component(self.player, c.Stats)
        self.message_log = self.world.get_component(self.player, c.MessageLog)
        self.message_log.add("You descend into the Caverns of Aether.")
        self.populate_floor()
        self.recompute_fov()

    def populate_floor(self) -> None:
        assert self.map_state is not None
        map_data = self.map_state.map_data
        monster_types = ["brute", "skirmisher", "ranged", "summoner", "sapper", "boss" if self.floor == MAX_FLOORS else "brute"]
        floor_budget = 6 + self.floor * 2
        placed = 0
        for y in range(map_data.height):
            for x in range(map_data.width):
                if (x, y) == map_data.start:
                    continue
                if not map_data.walkable[y, x]:
                    continue
                if self.rng.random() < 0.03 and placed < floor_budget:
                    archetype = self.rng.choice(monster_types[:-1]) if placed < floor_budget - 1 else monster_types[-1]
                    create_monster(self.world, archetype, x, y, self.floor)
                    placed += 1
        # Place keys and items
        for key_pos in map_data.key_positions:
            item = c.Item(name=f"Key-{self.floor}", stackable=True, quantity=1, identified=True)
            create_item(self.world, item, key_pos[0], key_pos[1], self.floor)
        # Additional loot
        for _ in range(4):
            x = self.rng.randint(1, map_data.width - 2)
            y = self.rng.randint(1, map_data.height - 2)
            if map_data.walkable[y, x]:
                item = roll_loot(self.rng, self.floor)
                create_item(self.world, item, x, y, self.floor)
        if self.floor == MAX_FLOORS:
            core_item = c.Item(name="Aether Core", stackable=False, identified=True, description="The legendary core.")
            create_item(self.world, core_item, map_data.stairs_down[0], map_data.stairs_down[1], self.floor)

    def recompute_fov(self) -> None:
        assert self.map_state is not None
        position = self.world.get_component(self.player, c.Position)
        visible = compute_fov(self.map_state.map_data, (position.x, position.y), radius=8)
        vis_dict: Dict[Tuple[int, int], bool] = {}
        for y in range(self.map_state.map_data.height):
            for x in range(self.map_state.map_data.width):
                if visible[x, y]:
                    vis_dict[(x, y)] = True
                    self.map_state.explored[(x, y)] = True
        self.map_state.visible = vis_dict

    def run(self) -> None:
        self.new_game()
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.render()
            pygame.display.flip()
        pygame.quit()

    def handle_events(self) -> None:
        assert self.map_state is not None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                else:
                    self.handle_key(event.key)
            self.ui.process_event(event)
        self.ui.update(0.016)

    def handle_key(self, key: int) -> None:
        if not self.player_stats or self.player_stats.hp <= 0:
            return
        direction_map = {
            pygame.K_UP: (0, -1),
            pygame.K_DOWN: (0, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_RIGHT: (1, 0),
            pygame.K_w: (0, -1),
            pygame.K_s: (0, 1),
            pygame.K_a: (-1, 0),
            pygame.K_d: (1, 0),
            pygame.K_KP8: (0, -1),
            pygame.K_KP2: (0, 1),
            pygame.K_KP4: (-1, 0),
            pygame.K_KP6: (1, 0),
        }
        if key in direction_map:
            self.player_move(direction_map[key])
        elif key in (pygame.K_PERIOD, pygame.K_SPACE):
            self.end_player_turn()
        elif key == pygame.K_g:
            self.pick_up_item()
        elif key == pygame.K_i:
            inventory = self.world.get_component(self.player, c.Inventory)
            self.ui.show_inventory(inventory)
        elif key == pygame.K_q:
            equipment = self.world.get_component(self.player, c.Equipment)
            self.ui.show_equipment(equipment)
        elif key == pygame.K_GREATER:
            self.use_stairs(descend=True)
        elif key == pygame.K_LESS:
            self.use_stairs(descend=False)

    def player_move(self, delta: Tuple[int, int]) -> None:
        assert self.map_state is not None
        position = self.world.get_component(self.player, c.Position)
        new_x = position.x + delta[0]
        new_y = position.y + delta[1]
        if not self.map_state.map_data.in_bounds(new_x, new_y):
            return
        tile = self.map_state.map_data.tile_at(new_x, new_y)
        if tile == Tile.WALL:
            return
        if tile == Tile.LOCKED_DOOR:
            key_name = f"Key-{self.floor}"
            if key_name in self.keyring:
                self.map_state.map_data.tiles[new_y, new_x] = Tile.DOOR
                self.message_log.add("You unlock the door.")
            else:
                self.message_log.add("The door is locked.")
                return
        target = self.get_actor_at(new_x, new_y)
        if target and target != self.player:
            self.resolve_melee(target)
            return
        position.x = new_x
        position.y = new_y
        self.message_log.add(f"You move to ({new_x},{new_y}).")
        self.handle_tile_effect(tile)
        self.end_player_turn()

    def handle_tile_effect(self, tile: Tile) -> None:
        if tile == Tile.ACID:
            damage = max(1, self.player_stats.max_hp // 15)
            taken = self.player_stats.take_damage(damage, "poison")
            self.message_log.add(f"Acid burns you for {taken} damage!")
        elif tile == Tile.LAVA:
            taken = self.player_stats.take_damage(max(2, self.player_stats.max_hp // 10), "fire")
            self.message_log.add(f"Lava sears you for {taken} damage!")
        elif tile == Tile.TRAP:
            taken = self.player_stats.take_damage(4, "physical")
            self.message_log.add("A trap triggers underfoot!")

    def get_actor_at(self, x: int, y: int) -> int | None:
        for entity, (pos,) in self.world.entities_with(c.Position):
            if pos.x == x and pos.y == y and pos.floor == self.floor:
                if self.world.try_component(entity, c.Stats) is None:
                    continue
                return entity
        return None

    def resolve_melee(self, target: int) -> None:
        attacker_stats = self.world.get_component(self.player, c.Stats)
        defender_stats = self.world.get_component(target, c.Stats)
        defender_status = self.world.try_component(target, c.StatusTracker)
        result = resolve_attack(attacker_stats, defender_stats, defender_status=defender_status, rng=self.rng)
        self.message_log.add(
            f"You {'crit ' if result.critical else ''}hit for {result.damage} {result.element} damage."
        )
        if defender_stats.hp <= 0:
            exp = self.world.try_component(target, c.ExperienceReward)
            if exp:
                leveled = gain_xp(attacker_stats, exp.amount)
                self.message_log.add(f"You slay the foe and gain {exp.amount} XP.")
                if leveled:
                    self.message_log.add("You feel stronger.")
            self.world.remove_entity(target)
        self.end_player_turn()

    def pick_up_item(self) -> None:
        inventory = self.world.get_component(self.player, c.Inventory)
        position = self.world.get_component(self.player, c.Position)
        for entity, (pos, item) in self.world.entities_with(c.Position, c.Item):
            if (pos.x, pos.y, pos.floor) == (position.x, position.y, position.floor):
                if inventory.add(item):
                    if item.name.startswith("Key"):
                        self.keyring.add(item.name)
                    if item.name == "Aether Core":
                        self.aether_core_retrieved = True
                    self.world.remove_entity(entity)
                    self.message_log.add(f"Picked up {item.name}.")
                else:
                    self.message_log.add("Inventory full.")
                break

    def end_player_turn(self) -> None:
        self.recompute_fov()
        self.enemy_turns()
        if self.player_stats and self.player_stats.hp <= 0:
            self.message_log.add(f"You died. Seed {self.seed}.")
            self.running = False

    def enemy_turns(self) -> None:
        assert self.map_state is not None
        player_pos = self.world.get_component(self.player, c.Position)
        for entity, (pos, stats, ai) in self.world.entities_with(c.Position, c.Stats, c.AI):
            if stats.hp <= 0:
                continue
            action = self.brain.decide(ai.archetype, pos, stats, self.map_state.map_data, (player_pos.x, player_pos.y))
            if action.type == "attack":
                result = resolve_attack(stats, self.player_stats, defender_status=self.world.get_component(self.player, c.StatusTracker), rng=self.rng)
                self.message_log.add(f"{ai.archetype.title()} hits you for {result.damage}.")
            elif action.type == "move" and action.target:
                tx, ty = action.target
                if not self.map_state.map_data.in_bounds(tx, ty):
                    continue
                if self.get_actor_at(tx, ty) in (None, self.player):
                    pos.x, pos.y = tx, ty
        if self.player_stats and self.player_stats.hp <= 0:
            self.running = False

    def use_stairs(self, descend: bool) -> None:
        assert self.map_state is not None
        position = self.world.get_component(self.player, c.Position)
        target = self.map_state.map_data.stairs_down if descend else self.map_state.map_data.stairs_up
        if (position.x, position.y) != target:
            self.message_log.add("You are not on the stairs.")
            return
        if not descend and self.floor == 1:
            if self.aether_core_retrieved:
                self.message_log.add("You escape with the Aether Core. You Win!")
            else:
                self.message_log.add("You cannot leave without the Aether Core.")
            return
        if descend:
            if self.floor >= MAX_FLOORS:
                self.message_log.add("The caverns end here.")
                return
            self.floor += 1
        else:
            self.floor = max(1, self.floor - 1)
        self.generate_new_floor(descend)

    def generate_new_floor(self, descend: bool) -> None:
        assert self.map_state is not None
        map_data = generate_floor(self.seed, self.floor, self.settings.generator)
        self.map_state = FloorState(map_data=map_data, visible={}, explored={})
        position = self.world.get_component(self.player, c.Position)
        position.x, position.y = map_data.start
        position.floor = self.floor
        self.world.purge_tag("monster")
        self.world.purge_tag("item")
        self.populate_floor()
        self.recompute_fov()
        self.message_log.add(f"Entering floor {self.floor} (seed {self.seed}).")

    def render(self) -> None:
        assert self.map_state is not None
        self.internal_surface.fill((0, 0, 0))
        renderer = RenderSystem(self.internal_surface)
        renderer.draw_map(self.map_state.map_data, self.map_state.visible, self.map_state.explored)
        renderer.draw_entities(self.world, self.map_state.visible)
        self.ui.update_messages(self.message_log)
        self.ui.draw(self.internal_surface)
        scaled_surface = pygame.transform.scale(
            self.internal_surface, (self.window.get_width(), self.window.get_height())
        )
        self.window.blit(scaled_surface, (0, 0))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Caverns of Aether — Advanced Edition")
    parser.add_argument("--seed", type=int, default=None, help="Deterministic RNG seed")
    parser.add_argument("--gen", choices=["rooms", "caves"], default="rooms", help="Generation algorithm")
    parser.add_argument("--scale", type=int, default=None, help="Pixel scale")
    parser.add_argument("--fullscreen", type=int, default=None, help="Fullscreen toggle")
    parser.add_argument("--vsync", type=int, default=None, help="VSync toggle")
    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    settings = Settings.load()
    settings.apply_cli(args)
    settings.save()
    game = Game(settings)
    game.settings.generator = args.gen
    game.run()


if __name__ == "__main__":  # pragma: no cover
    main()
