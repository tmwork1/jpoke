from typing import Literal, get_args

ContextRole = Literal["source", "target", "attacker", "defender"]

# role:side 形式で、特定の側のロールを指定 (例: "target:foe", "source:self")
RoleSpec = Literal[
    "source:self", "source:foe",
    "target:self", "target:foe",
    "attacker:self",
    "defender:self",
]

Factor = Literal["ability", "item", "move"]

LogPolicy = Literal["always", "on_success", "on_failure", "never"]

Side = Literal["self", "foe"]

Stat = Literal["H", "A", "B", "C", "D", "S", "ACC", "EVA"]

Type = Literal["ノーマル", "ほのお", "みず", "でんき", "くさ", "こおり", "かくとう", "どく",
               "じめん", "ひこう", "エスパー", "むし", "いわ", "ゴースト", "ドラゴン", "あく", "はがね", "フェアリー", "ステラ"]

Gender = Literal["", "オス", "メス"]

MoveCategory = Literal["物理", "特殊", "変化"]

AilmentName = Literal["", "どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"]

GlobalField = Literal["weather", "terrain", "gravity", "trickroom"]

SideField = Literal["reflector", "lightwall", "shinpi", "whitemist", "oikaze", "wish",
                    "makibishi", "dokubishi", "stealthrock", "nebanet"]

Weather = Literal["", "はれ", "あめ", "ゆき", "すなあらし"]

Terrain = Literal["", "エレキフィールド", "グラスフィールド", "サイコフィールド", "ミストフィールド"]

BoostSource = Literal["", "ability", "item", "weather", "terrain"]


def stats() -> list[str]:
    return list(get_args(Stat))
