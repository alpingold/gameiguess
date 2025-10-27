# Caverns of Aether — Advanced Edition

Caverns of Aether is a turn-based roguelike that mixes tight tactical combat, procedural dungeon floors, and an inventory-driven progression system. Everything is implemented in pure Python 3.11 with pygame for rendering/input, numpy for fast array manipulation, tcod for pathfinding and field-of-view, and pygame_gui for diegetic UI panels.

## Features

- Deterministic procedural generation supporting BSP room-corridor floors and cellular-automata caves.
- Seedable command-line interface (`--seed`, `--gen rooms|caves`, `--scale`, `--fullscreen`, `--vsync`).
- ECS-lite architecture with decoupled systems for input, AI, combat, rendering, loot, and persistence.
- Six distinct monster families (brute, skirmisher, ranged, summoner, sapper, boss) with bespoke AI behaviours.
- Status effects (bleed, burn, freeze, poison, shock, slow/haste) with resistances and durations.
- Inventory grid with equipment slots (weapon, armor, rings ×2, charm), cursed gear, and stackable consumables.
- Scroll-based magic (firebolt, blink, reveal, silence) plus trap disarming, environmental hazards, and elite modifiers.
- Save/Load (`savegame.sav`) preserves full state, including RNG and map exploration, enabling deterministic replays.
- Multiple floors culminating in retrieving the Aether Core on floor 8 before escaping to win.

## Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
python main.py --seed 123
```

## Running & Controls

- Movement: `WASD` / Arrow keys
- Wait: `.` or `SPACE`
- Interact / Open: `E`
- Pick up: `G`
- Inventory: `I`
- Equipment: `Q`
- Character sheet: `C`
- Drop: `D`
- Use / Confirm: `ENTER`
- Cancel / Menu: `ESC`
- Stairs: `>` (descend), `<` (ascend)
- Targeting with spells: mouse to aim, `ENTER` to cast, `ESC` to cancel.

Pause with `ESC` to open settings. Settings allow toggling fullscreen, window scale (1×–4×), vsync, durability toggles, and key remapping. Settings persist to `assets/settings.json`.

## Command Line Flags

```
python main.py --seed 123 --gen caves --scale 3 --fullscreen 0 --vsync 1
```

- `--seed <int>`: deterministic RNG seed.
- `--gen rooms|caves`: choose BSP rooms or cellular caves.
- `--scale <int>`: internal resolution scale (default 2).
- `--fullscreen 0|1`: toggle fullscreen.
- `--vsync 0|1`: toggle vsync (if supported).

## Architecture Overview

The project lives under `aether/` and is structured around a light ECS (entity-component-system) model:

- `ecs.py` defines the core registries and dispatch helpers for components and systems.
- `components.py` contains typed dataclasses for gameplay components (position, stats, AI brains, inventory, statuses, etc.).
- `systems.py` implements update passes: input, action queue, AI, combat resolution, projectile simulation, FOV, rendering, UI, and persistence hooks.
- `entities.py` offers factory helpers for creating players, monsters, items, and interactive props.
- `mapgen.py` produces deterministic numpy-backed maps for rooms or caves, with guarantee of connectivity, stairs, doors, keys, and hazards.
- `fov.py` and `path.py` wrap tcod’s compute_fov and A* / Dijkstra pathfinding using numpy arrays.
- `game.py` orchestrates the state machine (`states.py`), manages floors, handles win/lose flows, and integrates `pygame_gui` HUD panels.
- `combat.py`, `loot.py`, `ai.py`, `inventory.py`, `status.py`, and `ui.py` contain logic for those respective domains.
- `save.py` + `serialization.py` manage JSON+gzip save files, ensuring deterministic reloads including RNG state.
- `utils.py` includes helpers (random table pulls, weighted selection, flood fill, geometry).

Internally we render to a fixed 400×240 surface, then scale with nearest-neighbour to the configured window size. Numpy arrays back the tile map, FOV, and walkability grids to avoid per-frame allocations. Systems batch events to a message log, and combat applies hit flashes, screen shake, and floating damage indicators procedurally.

## Tips

- Early floors favour melee brutes—secure a ranged option quickly.
- Keys always spawn on the accessible side of locked doors; look for etched rune hints near locks.
- Scrolls are unidentified until used or appraised. Silence shuts down summoners.
- Bosses enrage below 50% HP; prepare resistances beforehand.
- You can toggle a debug overlay (`F3`) to view floor/seed and FOV boundaries.

## Known Issues & Troubleshooting

- Some Linux environments report ALSA warnings on pygame mixer init; audio is entirely procedural, so you can disable sound via the settings menu if desired.
- On macOS retina displays, window scaling may appear blurry—set scale to 2× or higher for crisp pixels.
- If the window opens off-screen after switching displays, delete `assets/settings.json` to reset.
- Headless environments (e.g., CI) should avoid launching the main loop; run `pytest` to validate systems without starting pygame.

## Testing

Run unit tests with:

```bash
pytest
```

The tests cover map generation connectivity and solvability, deterministic field-of-view cones, combat resistances & statuses, and save/load round-tripping of core state.

## License

MIT License © Caverns of Aether Team
