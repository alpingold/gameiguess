"""Entity/component registry helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Type, TypeVar, Generic, Iterable, Callable, Iterator, Any

EntityId = int
T = TypeVar("T")


class ComponentStore(Generic[T]):
    """Stores components of a single type."""

    def __init__(self) -> None:
        self._data: Dict[EntityId, T] = {}

    def add(self, entity: EntityId, component: T) -> None:
        self._data[entity] = component

    def remove(self, entity: EntityId) -> None:
        self._data.pop(entity, None)

    def get(self, entity: EntityId) -> T:
        return self._data[entity]

    def try_get(self, entity: EntityId) -> T | None:
        return self._data.get(entity)

    def items(self) -> Iterable[tuple[EntityId, T]]:
        return list(self._data.items())


class World:
    """Simple ECS world registry."""

    def __init__(self) -> None:
        self._next_entity: EntityId = 1
        self._components: Dict[Type[Any], ComponentStore[Any]] = {}
        self.tagged: Dict[str, set[EntityId]] = {}

    def create_entity(self, *components: Any, tags: Iterable[str] | None = None) -> EntityId:
        entity = self._next_entity
        self._next_entity += 1
        for component in components:
            self.add_component(entity, component)
        if tags:
            for tag in tags:
                self.tagged.setdefault(tag, set()).add(entity)
        return entity

    def add_component(self, entity: EntityId, component: Any) -> None:
        store = self._components.setdefault(type(component), ComponentStore())
        store.add(entity, component)

    def remove_entity(self, entity: EntityId) -> None:
        for store in self._components.values():
            store.remove(entity)
        for tag_entities in self.tagged.values():
            tag_entities.discard(entity)

    def get_component(self, entity: EntityId, comp_type: Type[T]) -> T:
        return self._components[comp_type].get(entity)

    def try_component(self, entity: EntityId, comp_type: Type[T]) -> T | None:
        store = self._components.get(comp_type)
        if not store:
            return None
        return store.try_get(entity)

    def entities_with(self, *comp_types: Type[Any]) -> Iterator[tuple[EntityId, list[Any]]]:
        if not comp_types:
            return iter(())
        primary_store = self._components.get(comp_types[0])
        if not primary_store:
            return iter(())
        for entity, comp in primary_store.items():
            components = [comp]
            valid = True
            for comp_type in comp_types[1:]:
                store = self._components.get(comp_type)
                if not store:
                    valid = False
                    break
                other = store.try_get(entity)
                if other is None:
                    valid = False
                    break
                components.append(other)
            if valid:
                yield entity, components

    def purge_tag(self, tag: str) -> None:
        for entity in list(self.tagged.get(tag, set())):
            self.remove_entity(entity)
        self.tagged.pop(tag, None)


@dataclass
class System:
    """Base class for systems."""

    priority: int = 0

    def initialize(self, world: World) -> None:  # pragma: no cover - override hook
        pass

    def update(self, world: World, dt: float) -> None:  # pragma: no cover - override hook
        raise NotImplementedError


class SystemManager:
    """Maintains ordered system updates."""

    def __init__(self) -> None:
        self._systems: list[System] = []

    def add(self, system: System) -> None:
        self._systems.append(system)
        self._systems.sort(key=lambda s: s.priority)

    def initialize(self, world: World) -> None:
        for system in self._systems:
            system.initialize(world)

    def update(self, world: World, dt: float) -> None:
        for system in self._systems:
            system.update(world, dt)
