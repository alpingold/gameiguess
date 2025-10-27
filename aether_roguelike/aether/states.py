"""Game state machine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class GameState:
    name: str
    handler: Callable[[float], None]


class StateMachine:
    def __init__(self) -> None:
        self._states: dict[str, GameState] = {}
        self._current: Optional[GameState] = None

    def add_state(self, state: GameState) -> None:
        self._states[state.name] = state

    def switch(self, name: str) -> None:
        self._current = self._states[name]

    def update(self, dt: float) -> None:
        if self._current:
            self._current.handler(dt)
