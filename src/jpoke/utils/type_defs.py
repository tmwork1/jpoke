from typing import Literal

ContextRole = Literal["source", "target", "attacker", "defender"]

# role:side 形式で、特定の側のロールを指定 (例: "target:foe", "source:self")
RoleSpec = Literal[
    "source:self", "source:foe",
    "target:self", "target:foe",
    "attacker:self",
    "defender:self",
]

EffectSource = Literal["ability", "item", "move", "ailment", "volatile"]

LogPolicy = Literal["always", "on_success", "on_failure", "never"]

Side = Literal["self", "foe"]

Nature = Literal[
    "さみしがり", "いじっぱり", "やんちゃ", "ゆうかん",  # A↑
    "ずぶとい", "わんぱく", "のうてんき", "のんき",  # B↑
    "ひかえめ", "おっとり", "うっかりや", "れいせい",  # C↑
    "おだやか", "おとなしい", "しんちょう", "なまいき",  # D↑
    "おくびょう", "せっかち", "ようき", "むじゃき",  # S↑
    "がんばりや", "すなお", "てれや", "きまぐれ", "まじめ",  # 無補正
]

Stat = Literal["H", "A", "B", "C", "D", "S", "ACC", "EVA"]

Type = Literal["ノーマル", "ほのお", "みず", "でんき", "くさ", "こおり", "かくとう", "どく",
               "じめん", "ひこう", "エスパー", "むし", "いわ", "ゴースト", "ドラゴン", "あく", "はがね", "フェアリー", "ステラ"]

Gender = Literal["", "オス", "メス"]

MoveCategory = Literal["物理", "特殊", "変化"]

AilmentName = Literal["", "どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"]

# TODO: volatileの実装と完全に一致させる
VolatileName = Literal[
    "アクアリング",
    "あめまみれ",
    "アンコール",
    "うちおとす",
    "かいふくふうじ",
    "かなしばり",
    "きゅうしょアップ",
    "こんらん",
    "しおづけ",
    "じごくずき",
    "じゅうでん",
    "たくわえる",
    "ちょうはつ",
    "でんじふゆう",
    "にげられない",
    "ねむけ",
    "ねをはる",
    "のろい",
    "バインド",
    "ひるみ",
    "ほろびのうた",
    "みがわり",
    "みちづれ",
    "メロメロ",
    "やどりぎのタネ",
]

GlobalField = Literal["じゅうりょく", "トリックルーム"]

SideField = Literal["リフレクター", "ひかりのかべ", "しんぴのまもり", "しろいきり", "おいかぜ", "ねがいごと",
                    "まきびし", "どくびし", "ステルスロック", "ねばねばネット", "オーロラベール"]

Weather = Literal["", "はれ", "あめ", "ゆき", "すなあらし"]

Terrain = Literal["", "エレキフィールド", "グラスフィールド", "サイコフィールド", "ミストフィールド"]

BoostSource = Literal["", "ability", "item", "weather", "terrain"]

MoveLabel = Literal[
    "bite",
    "bullet",
    "bypass_substitute",
    "contact",
    "dance",
    "heal",
    "non_encore",
    "powder",
    "pulse",
    "punch",
    "slash",
    "sound",
    "wind",
    "minimize",
]
