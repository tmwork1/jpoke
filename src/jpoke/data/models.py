from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict, Callable
if TYPE_CHECKING:
    from jpoke.enums import Event, DomainEvent, LethalEvent
    from jpoke.core import Handler, LethalHandler

from dataclasses import dataclass, field

from jpoke.types import AbilityFlag, PokemonType, MoveCategory, MoveTarget, MoveFlag


class PokemonData:
    def __init__(self, data) -> None:
        self.name: str = data["name"]
        self.pre_evolution: str = data.get("pre_evolution", "")
        self.weight: float = data["weight"]
        self.types: list[PokemonType] = [data[f"type-{i+1}"] for i in range(2) if data[f"type-{i+1}"]]
        self.abilities: list[str] = [data[f"ability-{i+1}"] for i in range(3) if data[f"ability-{i+1}"]]
        self.base: list[int] = [data[s] for s in ["H", "A", "B", "C", "D", "S"]]

        if not self.abilities:
            self.abilities = [""]


@dataclass
class AbilityData:
    flags: set[AbilityFlag] = field(default_factory=set)
    handlers: dict[Event | DomainEvent, Handler | list[Handler]] = field(default_factory=dict)
    lethal_handlers: dict[LethalEvent, LethalHandler] = field(default_factory=dict)
    name: str = ""


@dataclass
class ItemData:
    removable: bool = True
    fling_power: int = 0
    power_modifier_by_type: dict[PokemonType, float] = field(default_factory=dict)
    damage_modifier_by_type: dict[PokemonType, float] = field(default_factory=dict)
    mega_evolve: tuple[str, ...] | None = None
    handlers: dict[Event | DomainEvent, Handler | list[Handler]] = field(default_factory=dict)
    lethal_handlers: dict[LethalEvent, LethalHandler] = field(default_factory=dict)
    name: str = ""


class MultiHit(TypedDict):
    min: int
    max: int
    check_hit_each_time: bool
    power_sequence: tuple[int, ...]


@dataclass
class MoveData:
    type: PokemonType
    category: MoveCategory
    pp: int
    power: int | None = None
    accuracy: int | None = None
    priority: int = 0
    critical_rank: int = 0
    target: MoveTarget = "foe"
    multi_hit: MultiHit | None = None
    flags: set[MoveFlag] = field(default_factory=set)
    handlers: dict[Event | DomainEvent, Handler | list[Handler]] = field(default_factory=dict)
    lethal_handlers: dict[LethalEvent, LethalHandler] = field(default_factory=dict)
    name: str = ""


@dataclass
class FieldData:
    max_count: int = 1
    handlers: dict[Event | DomainEvent, Handler | list[Handler]] = field(default_factory=dict)
    lethal_handlers: dict[LethalEvent, LethalHandler] = field(default_factory=dict)
    name: str = ""


@dataclass
class AilmentData:
    is_sleep: bool = False
    uncurable: bool = False
    handlers: dict[Event | DomainEvent, Handler | list[Handler]] = field(default_factory=dict)
    lethal_handlers: dict[LethalEvent, LethalHandler] = field(default_factory=dict)
    name: str = ""


@dataclass
class VolatileData:
    handlers: dict[Event | DomainEvent, Handler | list[Handler]] = field(default_factory=dict)
    forced: bool = False
    lethal_handlers: dict[LethalEvent, LethalHandler] = field(default_factory=dict)
    name: str = ""
