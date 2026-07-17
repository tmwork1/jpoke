"""poke-env との相互変換テーブル・変換関数。

互換の方向は poke-env → jpoke のみ（jpoke → poke-env のエクスポートは対象外）。
.internal/poke-env/compat_plan.md の Phase 4 に対応する。

キーの正規化規則: 各マップのキーは poke-env Enum の `name.lower()` に統一する
（例: `Weather.SUNNYDAY` → `"sunnyday"`、`Field.ELECTRIC_TERRAIN` → `"electric_terrain"`）。
Showdown のメッセージ ID（`"electricterrain"` 等）とは異なる場合があるので混同しないこと。
"""

TYPE_MAP: dict[str, str] = {
    "Normal":   "ノーマル", "Fire":    "ほのお", "Water":   "みず",
    "Electric": "でんき",  "Grass":   "くさ",   "Ice":     "こおり",
    "Fighting": "かくとう","Poison":  "どく",   "Ground":  "じめん",
    "Flying":   "ひこう",  "Psychic": "エスパー","Bug":     "むし",
    "Rock":     "いわ",    "Ghost":   "ゴースト","Dragon":  "ドラゴン",
    "Dark":     "あく",    "Steel":   "はがね",  "Fairy":  "フェアリー",
    "Stellar":  "ステラ",
}
TYPE_MAP_INV = {v: k for k, v in TYPE_MAP.items()}

# poke-env の Status には FNT（瀕死）もあるが、jpoke は状態異常ではなく hp == 0 で表現するため対象外
STATUS_MAP: dict[str, str] = {
    "brn": "やけど", "frz": "こおり", "par": "まひ",
    "psn": "どく",   "slp": "ねむり", "tox": "もうどく",
}
STATUS_MAP_INV = {v: k for k, v in STATUS_MAP.items()}

# poke-env の Weather には HAIL（あられ）もあるが、Champions（第9世代準拠）は ゆき のみのため対象外
WEATHER_MAP: dict[str, str] = {
    "sunnyday":     "はれ",     "raindance":    "あめ",
    "sandstorm":    "すなあらし","snow":         "ゆき",
    "desolateland": "おおひでり","primordialsea":"おおあめ",
    "deltastream":  "らんきりゅう",
}
WEATHER_MAP_INV = {v: k for k, v in WEATHER_MAP.items()}

# poke-env の Field Enum のうち地形（terrain）4 種 → jpoke TerrainName
TERRAIN_MAP: dict[str, str] = {
    "electric_terrain": "エレキフィールド",
    "grassy_terrain":   "グラスフィールド",
    "psychic_terrain":  "サイコフィールド",
    "misty_terrain":    "ミストフィールド",
}
TERRAIN_MAP_INV = {v: k for k, v in TERRAIN_MAP.items()}

# poke-env の Field Enum のうち地形以外（jpoke では GlobalFieldName に分離）
GLOBAL_FIELD_MAP: dict[str, str] = {
    "gravity":    "じゅうりょく",   "trick_room":  "トリックルーム",
    "magic_room": "マジックルーム", "wonder_room": "ワンダールーム",
    "fairy_lock": "フェアリーロック",
}
GLOBAL_FIELD_MAP_INV = {v: k for k, v in GLOBAL_FIELD_MAP.items()}

# poke-env の SideCondition Enum → jpoke SideFieldName
# jpoke の SideFieldName のうち いやしのねがい・みかづきのまい・ねがいごと・みらいよち・はめつのねがい は
# poke-env では SideCondition ではなく slot condition 扱いのため対象外
SIDE_CONDITION_MAP: dict[str, str] = {
    "reflect":      "リフレクター",   "light_screen": "ひかりのかべ",
    "aurora_veil":  "オーロラベール", "safeguard":    "しんぴのまもり",
    "mist":         "しろいきり",     "tailwind":     "おいかぜ",
    "spikes":       "まきびし",       "toxic_spikes": "どくびし",
    "stealth_rock": "ステルスロック", "sticky_web":   "ねばねばネット",
}
SIDE_CONDITION_MAP_INV = {v: k for k, v in SIDE_CONDITION_MAP.items()}

NATURE_MAP: dict[str, str] = {
    "Lonely": "さみしがり", "Adamant": "いじっぱり",
    "Naughty": "やんちゃ",  "Brave":   "ゆうかん",
    "Bold":    "ずぶとい",  "Impish":  "わんぱく",
    "Lax":     "のうてんき","Relaxed": "のんき",
    "Modest":  "ひかえめ",  "Mild":    "おっとり",
    "Rash":    "うっかりや","Quiet":   "れいせい",
    "Calm":    "おだやか",  "Gentle":  "おとなしい",
    "Careful": "しんちょう","Sassy":   "なまいき",
    "Timid":   "おくびょう","Hasty":   "せっかち",
    "Jolly":   "ようき",    "Naive":   "むじゃき",
    "Hardy":   "がんばりや","Docile":  "すなお",
    "Bashful": "てれや",    "Quirky":  "きまぐれ",
    "Serious": "まじめ",
}
NATURE_MAP_INV = {v: k for k, v in NATURE_MAP.items()}

# jpoke の Stat（"hp", "atk", "def", "spa", "spd", "spe", "accuracy", "evasion"）のうち
# 種族値・個体値・努力値に対応する6種のインデックス
STAT_INDEX: dict[str, int] = {
    "hp": 0, "atk": 1, "def": 2, "spa": 3, "spd": 4, "spe": 5,
}


def stats_from_poke_env(d: dict[str, int]) -> list[int]:
    """poke-env の {"hp":..., "atk":...} をインデックス順（hp, atk, def, spa, spd, spe）のリストに変換する。

    `Pokemon.set_ivs` が受け取る `ivs: list[int]`（各値0〜31）はスケールが
    poke-env と同じため、この関数の戻り値をそのまま渡せる。
    """
    return [d.get(k, 0) for k in ("hp", "atk", "def", "spa", "spd", "spe")]


def evs_from_poke_env(d: dict[str, int]) -> list[int]:
    """poke-env の evs（各値 0〜252）を Champions 形式の努力値（各値 0〜32）に変換する。

    Champions 形式は 0 または 8x - 4（x = 1〜32）に相当する値のみ表現できるため、
    中間値は切り捨てで近似する（非可逆）。
    戻り値は `Pokemon.set_evs` が受け取る `evs: list[int]` にそのまま渡せる。
    """
    return [0 if v < 4 else (v + 4) // 8 for v in stats_from_poke_env(d)]
