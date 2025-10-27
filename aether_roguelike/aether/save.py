"""Save/load handling."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

from .serialization import GameSnapshot, game_snapshot_to_dict, dict_to_game_snapshot

SAVE_PATH = Path("savegame.sav")


def save_game(path: Path, snapshot: GameSnapshot) -> None:
    data = game_snapshot_to_dict(snapshot)
    encoded = json.dumps(data).encode("utf-8")
    with gzip.open(path, "wb") as fh:
        fh.write(encoded)


def load_game(path: Path) -> GameSnapshot:
    with gzip.open(path, "rb") as fh:
        data = json.loads(fh.read().decode("utf-8"))
    return dict_to_game_snapshot(data)


__all__ = ["save_game", "load_game", "SAVE_PATH"]
