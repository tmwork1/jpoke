from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict, Literal
if TYPE_CHECKING:
    from jpoke.enums import Event, DomainEvent, LethalEvent
    from jpoke.core import Handler, LethalHandler

from dataclasses import dataclass, field

from jpoke.types import AbilityFlag, Type, MoveCategory, MoveTarget, MoveFlag, \
    PokemonName, AbilityName, MoveName, ItemName, Regulation


class PokemonData:
    def __init__(self, name, data, learnset: list[MoveName] | None = None) -> None:
        self.name: PokemonName = name
        self.pre_evolution: PokemonName | Literal[""] = data.get("prevo", "")
        self.weight: float = data["weight"]
        self.types: list[Type] = list(data["types"])
        self.abilities: list[AbilityName] = list(data["abilities"])
        stats = data["baseStats"]
        self.base: list[int] = [stats["hp"], stats["atk"], stats["def"], stats["spa"], stats["spd"], stats["spe"]]
        self.learnset: list[MoveName] = learnset if learnset is not None else []
        self.regulations: set[Regulation] = field(default_factory=set)

        if not self.abilities:
            self.abilities = [""]


@dataclass
class AbilityData:
    flags: set[AbilityFlag] = field(default_factory=set)
    handlers: dict[Event | DomainEvent, Handler | list[Handler]] = field(default_factory=dict)
    lethal_handlers: dict[LethalEvent, LethalHandler] = field(default_factory=dict)
    name: AbilityName = ""


@dataclass
class ItemData:
    removable: bool = True
    fling_power: int = 0
    no_fling: bool = False
    power_modifier_by_type: dict[Type, float] = field(default_factory=dict)
    damage_modifier_by_type: dict[Type, float] = field(default_factory=dict)
    mega_evolve: tuple[PokemonName, ...] | None = None
    handlers: dict[Event | DomainEvent, Handler | list[Handler]] = field(default_factory=dict)
    lethal_handlers: dict[LethalEvent, LethalHandler] = field(default_factory=dict)
    name: ItemName = ""
    regulations: set[Regulation] = field(default_factory=set)


class MultiHit(TypedDict):
    min: int
    max: int
    check_hit_each_time: bool
    power_sequence: tuple[int, ...]


@dataclass
class MoveData:
    """技の静的パラメータとハンドラを保持する。

    Note:
        `type`/`category`/`pp`/`target`は未設定を表す空文字センチネルを持つ。
        ps-champ-jaでカバーされる技はmove_*.py側でこれらを指定せず、
        `data/move.py`の`common_setup()`がインポート時にps-champ-jaのスナップショット
        （`data/ps-champ-ja/moves.json`）から値を埋める。カバーされない技はmove_*.py側で
        明示的にリテラル値を指定する（センチネルのまま残るとcommon_setup()がエラーにする）。
    """
    type: Type | Literal[""] = ""
    category: MoveCategory | Literal[""] = ""
    pp: int = 0
    power: int | None = None
    accuracy: int | None = None
    priority: int = 0
    crit_ratio: int = 0
    target: MoveTarget | Literal[""] = ""
    multi_hit: MultiHit | None = None
    flags: set[MoveFlag] = field(default_factory=set)
    handlers: dict[Event | DomainEvent, Handler | list[Handler]] = field(default_factory=dict)
    lethal_handlers: dict[LethalEvent, LethalHandler] = field(default_factory=dict)
    name: MoveName | Literal[""] = ""
    exist: bool = False


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
