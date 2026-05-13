from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict
if TYPE_CHECKING:
    from jpoke.core import Handler
    from jpoke.enums import Event, DomainEvent

from dataclasses import dataclass, field

from jpoke.utils.constants import STATS
from jpoke.utils.type_defs import AbilityFlag, Type, MoveCategory, MoveTarget, MoveLabel


HandlersType = dict[Event | DomainEvent, Handler | list[Handler]]


class PokemonData:
    def __init__(self, data) -> None:
        self.name: str = data["name"]
        self.id: int = data["id"]
        self.form_id: int = data["form-id"]
        self.alias: str = data["alias"]
        self.weight: float = data["weight"]
        self.types: list[Type] = [data[f"type-{i+1}"] for i in range(2) if data[f"type-{i+1}"]]
        self.abilities: list[str] = [data[f"ability-{i+1}"] for i in range(3) if data[f"ability-{i+1}"]]
        self.base: list[int] = [data[s] for s in STATS[:6]]


@dataclass
class AbilityData:
    flags: list[AbilityFlag] = field(default_factory=list)
    handlers: HandlersType = field(default_factory=dict)
    name: str = ""


@dataclass
class ItemData:
    fling_power: int = 0
    consumable: bool = False
    power_modifier_by_type: dict[Type, float] = field(default_factory=dict)
    damage_modifier_by_type: dict[Type, float] = field(default_factory=dict)
    handlers: HandlersType = field(default_factory=dict)
    name: str = ""


class MultiHit(TypedDict):
    min: int
    max: int
    check_hit_each_time: bool
    power_sequence: tuple[int, ...]


@dataclass
class MoveData:
    type: Type
    category: MoveCategory
    pp: int
    power: int | None = None
    accuracy: int | None = None
    priority: int = 0
    critical_rank: int = 0
    target: MoveTarget = "foe"
    multi_hit: MultiHit | None = None
    labels: list[MoveLabel] = field(default_factory=list)
    handlers: HandlersType = field(default_factory=dict)
    name: str = ""


@dataclass
class FieldData:
    turn_extension_item: str | None = None
    handlers: HandlersType = field(default_factory=dict)
    name: str = ""


@dataclass
class AilmentData:
    handlers: HandlersType = field(default_factory=dict)
    name: str = ""


@dataclass
class VolatileData:
    handlers: HandlersType = field(default_factory=dict)
    forced: bool = False
    name: str = ""
