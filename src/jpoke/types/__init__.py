from .literals import (
    AbilityDisabledReason,
    AbilityFlag,
    AbilityState,
    BattlePhase,
    BoostSource,
    CommandType,
    ContextRole,
    Gender,
    HandlerSource,
    HPChangeReason,
    ItemDisabledReason,
    LethalSubject,
    MoveCategory,
    MoveFlag,
    MoveTarget,
    Nature,
    RoleSpec,
    Side,
    Stat,
    StatChangeReason,
    Type,
)
from .ailment import AilmentName
from .global_field import GlobalFieldName
from .side_field import SideFieldName
from .terrain import TerrainName
from .volatile import VolatileName
from .weather import WeatherName

# TODO : PokemonName, AbilityName, ItemName, MoveName もスクリプトで自動生成する
# TODO : ポケモン名の型ヒントをstrからPokemonNameに移行
# TODO : 特性名の型ヒントをstrからAbilityNameに移行
# TODO : アイテム名の型ヒントをstrからItemNameに移行
# TODO : 技名の型ヒントをstrからMoveNameに移行

__all__ = [
    "AbilityDisabledReason",
    "AbilityFlag",
    "AbilityState",
    "AilmentName",
    "BattlePhase",
    "BoostSource",
    "CommandType",
    "ContextRole",
    "Gender",
    "GlobalFieldName",
    "HandlerSource",
    "HPChangeReason",
    "ItemDisabledReason",
    "LethalSubject",
    "MoveCategory",
    "MoveFlag",
    "MoveTarget",
    "Nature",
    "RoleSpec",
    "Side",
    "SideFieldName",
    "Stat",
    "StatChangeReason",
    "TerrainName",
    "Type",
    "VolatileName",
    "WeatherName",
]
