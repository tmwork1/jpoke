from typing import Literal, get_args

Side = Literal["self", "foe", "all"]

Stat = Literal["H", "A", "B", "C", "D", "S", "ACC", "EVA"]

Gender = Literal["", "オス", "メス"]

MoveCategory = Literal["物理", "特殊", "変化"]

AilmentName = Literal["", "どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"]

GlobalField = Literal["weather", "terrain", "gravity", "trickroom"]

SideField = Literal["reflector", "lightwall", "shinpi", "whitemist", "oikaze", "wish",
                    "makibishi", "dokubishi", "stealthrock", "nebanet"]

Weather = Literal["", "はれ", "あめ", "ゆき", "すなあらし"]

Terrain = Literal["", "エレキフィールド", "グラスフィールド", "サイコフィールド", "ミストフィールド"]

BoostSource = Literal["", "ability", "item", "weather", "terrain"]


def get_stats() -> list[str]:
    return list(get_args(Stat))
