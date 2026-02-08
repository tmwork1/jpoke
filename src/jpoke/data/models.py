from typing import Literal
from dataclasses import dataclass, field

from jpoke.utils.constants import STATS
from jpoke.utils.type_defs import MoveCategory, PokeType, MoveLabel
from jpoke.core.event import Event, Handler


class PokemonData:
    def __init__(self, data) -> None:
        self.name: str = data["name"]
        self.id: int = data["id"]
        self.form_id: int = data["form-id"]
        self.label: str = data["alias"]
        self.weight: float = data["weight"]
        self.types: list[PokeType] = [data[f"type-{i+1}"] for i in range(2) if data[f"type-{i+1}"]]
        self.abilities: list[str] = [data[f"ability-{i+1}"] for i in range(3) if data[f"ability-{i+1}"]]
        self.base: list[int] = [data[s] for s in STATS[:6]]


@dataclass
class AbilityData:
    flags: list[str] = field(default_factory=list)
    handlers: dict[Event, Handler] = field(default_factory=dict)
    name: str = ""


@dataclass
class ItemData:
    fling_power: int = 0
    consumable: bool = False
    power_modifier_by_type: dict[PokeType, float] = field(default_factory=dict)
    damage_modifier_by_type: dict[PokeType, float] = field(default_factory=dict)
    handlers: dict[Event, Handler] = field(default_factory=dict)
    name: str = ""


@dataclass
class MoveData:
    type: PokeType
    category: MoveCategory
    pp: int
    power: int | None = None
    accuracy: int | None = None
    priority: int = 0
    critical_rank: int = 0
    labels: list[Move] = field(default_factory=list)
    handlers: dict[Event, Handler] = field(default_factory=dict)
    name: str = ""


@dataclass
class FieldData:
    turn_extension_item: str | None = None
    handlers: dict[Event, Handler] = field(default_factory=dict)
    name: str = ""


@dataclass
class AilmentData:
    handlers: dict[Event, Handler] = field(default_factory=dict)
    name: str = ""


@dataclass
class VolatileData:
    handlers: dict[Event, Handler] = field(default_factory=dict)
    name: str = ""
