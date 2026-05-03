from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Handler
    from jpoke.enums import Event

from dataclasses import dataclass, field

from jpoke.utils.constants import STATS
from jpoke.utils.type_defs import AbilityFlag, MoveCategory, Type, MoveLabel


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
    handlers: dict[Event, Handler] = field(default_factory=dict)
    name: str = ""


@dataclass
class ItemData:
    fling_power: int = 0
    consumable: bool = False
    power_modifier_by_type: dict[Type, float] = field(default_factory=dict)
    damage_modifier_by_type: dict[Type, float] = field(default_factory=dict)
    handlers: dict[Event, Handler] = field(default_factory=dict)
    name: str = ""


@dataclass
class MoveData:
    type: Type
    category: MoveCategory
    pp: int
    power: int | None = None
    accuracy: int | None = None
    priority: int = 0
    critical_rank: int = 0
    self_targeting: bool = False
    field_targeting: bool = False
    min_hits: int = 1
    max_hits: int = 1
    check_hit_each_time: bool = False
    power_sequence: tuple[int, ...] = ()
    labels: list[MoveLabel] = field(default_factory=list)
    move_secondary: bool = False  # 追加効果判定（ちからずく/てんのめぐみの対象）
    recoil_ratio: float = 0  # 反動割合（与えたダメージに対する割合）。0 なら反動なし。
    handlers: dict[Event, Handler] = field(default_factory=dict)
    name: str = ""

    @property
    def sheer_force(self) -> bool:
        """互換プロパティ: 旧名 sheer_force は move_secondary と同義。"""
        return self.move_secondary

    @sheer_force.setter
    def sheer_force(self, value: bool) -> None:
        self.move_secondary = value


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
    forced: bool = False
    name: str = ""
