"""Runtime settings handling for Caverns of Aether."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
import json
from typing import Dict, Any

ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
SETTINGS_FILE = ASSET_DIR / "settings.json"


def _ensure_asset_dir() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Settings:
    seed: int | None = None
    generator: str = "rooms"
    scale: int = 2
    fullscreen: bool = False
    vsync: bool = True
    durability_enabled: bool = False
    keybinds: Dict[str, int] = field(default_factory=dict)
    show_debug: bool = False

    @classmethod
    def load(cls) -> "Settings":
        _ensure_asset_dir()
        if SETTINGS_FILE.exists():
            data = json.loads(SETTINGS_FILE.read_text())
            return cls(**data)
        return cls()

    def save(self) -> None:
        _ensure_asset_dir()
        SETTINGS_FILE.write_text(json.dumps(asdict(self), indent=2))

    def apply_cli(self, args: Any) -> None:
        if getattr(args, "seed", None) is not None:
            self.seed = int(args.seed)
        if getattr(args, "gen", None):
            self.generator = str(args.gen)
        if getattr(args, "scale", None):
            self.scale = max(1, int(args.scale))
        if getattr(args, "fullscreen", None) is not None:
            self.fullscreen = bool(int(args.fullscreen))
        if getattr(args, "vsync", None) is not None:
            self.vsync = bool(int(args.vsync))


DEFAULT_INTERNAL_RESOLUTION = (400, 240)
TILE_SIZE = 24
MAP_WIDTH = 48
MAP_HEIGHT = 32
MAX_FLOORS = 8
PLAYER_START_HP = 30
PLAYER_START_MP = 12
BASE_ENERGY = 100

STATUS_DURATION_DEFAULT = 6

# Element tags
ELEMENTS = ("physical", "fire", "ice", "poison", "shock")


def settings_summary(settings: Settings) -> str:
    return (
        f"Seed={settings.seed or 'random'} "
        f"Gen={settings.generator} Scale={settings.scale} "
        f"Fullscreen={int(settings.fullscreen)} VSync={int(settings.vsync)}"
    )
