"""pygame_gui based UI widgets."""
from __future__ import annotations

import pygame
import pygame_gui
from typing import Dict, Tuple

from . import components as c


class UIManager:
    def __init__(self, resolution: Tuple[int, int], theme_path: str | None = None) -> None:
        self.manager = pygame_gui.UIManager(resolution, theme_path)
        self.hud_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(0, resolution[1] - 80, resolution[0], 80),
            manager=self.manager,
            anchors={"left": "left", "right": "right", "bottom": "bottom"},
        )
        self.message_list = pygame_gui.elements.UITextBox(
            html_text="",
            relative_rect=pygame.Rect(8, 8, resolution[0] - 16, 64),
            manager=self.manager,
            container=self.hud_panel,
        )
        self.inventory_window: pygame_gui.elements.UIWindow | None = None
        self.equipment_window: pygame_gui.elements.UIWindow | None = None

    def update_messages(self, log: c.MessageLog) -> None:
        text = "<br/>".join(log.entries[-8:])
        self.message_list.set_text(text)

    def show_inventory(self, inventory: c.Inventory) -> None:
        if self.inventory_window:
            self.inventory_window.kill()
        self.inventory_window = pygame_gui.elements.UIWindow(
            pygame.Rect(40, 40, 260, 320),
            manager=self.manager,
            window_display_title="Inventory",
        )
        contents = "<br/>".join(f"{item.name} x{item.quantity}" if item.stackable else item.name for item in inventory.items)
        pygame_gui.elements.UITextBox(
            html_text=contents or "Inventory empty",
            relative_rect=pygame.Rect(8, 32, 240, 240),
            manager=self.manager,
            container=self.inventory_window,
        )

    def show_equipment(self, equipment: c.Equipment) -> None:
        if self.equipment_window:
            self.equipment_window.kill()
        self.equipment_window = pygame_gui.elements.UIWindow(
            pygame.Rect(320, 40, 240, 260),
            manager=self.manager,
            window_display_title="Equipment",
        )
        layout = []
        for slot, item in equipment.slots().items():
            layout.append(f"{slot.title()}: {item.name if item else '-'}")
        pygame_gui.elements.UITextBox(
            html_text="<br/>".join(layout),
            relative_rect=pygame.Rect(8, 32, 220, 200),
            manager=self.manager,
            container=self.equipment_window,
        )

    def process_event(self, event: pygame.event.Event) -> None:
        self.manager.process_events(event)

    def update(self, dt: float) -> None:
        self.manager.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self.manager.draw_ui(surface)
