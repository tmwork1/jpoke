from typing import Literal


BattlePhase = Literal["", "selection", "action", "switch"]
CommandType = Literal["any", "move", "switch"]


LethalSubject = Literal["attacker", "defender"]

AbilityDisabledReason = Literal[
    "consumed", "かがくへんかガス", "かたやぶり", "とくせいなし",
]

ItemDisabledReason = Literal[
    "ぶきよう", "マジックルーム",
]


HandlerSource = Literal["ability", "item", "move", "ailment", "volatile", "field"]

AbilityState = Literal["", "idle", "charged", "active", "inactive", "can_act", "skip_next"]

ContextRole = Literal["source", "target", "attacker", "defender"]


RoleSpec = Literal[
    "source:self", "source:foe",
    "target:self", "target:foe",
    "attacker:self",
    "defender:self",
]  # role:side 形式で、特定の側のロールを指定


Side = Literal["self", "foe"]

Nature = Literal[
    "さみしがり", "いじっぱり", "やんちゃ", "ゆうかん",  # A+
    "ずぶとい", "わんぱく", "のうてんき", "のんき",  # B+
    "ひかえめ", "おっとり", "うっかりや", "れいせい",  # C+
    "おだやか", "おとなしい", "しんちょう", "なまいき",  # D+
    "おくびょう", "せっかち", "ようき", "むじゃき",  # S+
    "がんばりや", "すなお", "てれや", "きまぐれ", "まじめ",  # 無補正
]

Stat = Literal["hp", "atk", "def", "spa", "spd", "spe", "accuracy", "evasion"]

Type = Literal[
    "", "ノーマル", "ほのお", "みず", "でんき", "くさ",
    "こおり", "かくとう", "どく", "じめん", "ひこう",
    "エスパー", "むし", "いわ", "ゴースト", "ドラゴン",
    "あく", "はがね", "フェアリー", "ステラ"
]

Gender = Literal["", "male", "female"]

MoveCategory = Literal["physical", "special", "status"]

MoveTarget = Literal["foe", "foe_side", "own_side", "self", "field"]

BoostSource = Literal["", "item", "field"]

HPChangeReason = Literal[
    "",                     # その他のダメージ
    "move_damage",          # 技によるダメージ
    "sandstorm",            # すなあらし等の天候ダメージ (ぼうじんによる無効化のため)
    "poison",               # どく/もうどくによる定期HP変化 (ポイズンヒールによる回復のため)
    "burn",                 # やけどによる定期ダメージ (たいねつ特性の軽減判定のため)
    "recoil",               # 反動ダメージ（いしあたまによる無効化のため）
    "self_attack",          # こんらん自傷（ききかいひ不発）
    "pain_split",           # いたみわけ（ききかいひ不発）
    "self_cost",            # 自己HP消費（みがわり等）
    "bench_heal",           # 控え回復（さいせいりょく等、かいふくふうじ無効）
    "drain",                # 吸収技・やどりぎのタネによる回復 (ヘドロえきのダメージ変換用)
    "perish",               # ほろびのうた/みちづれによるひんし（マジックガードで防げない）
]

StatChangeReason = Literal[
    "",                     # 通常（理由なし）
    "いかく",
    "ミラーアーマー",        # ミラーアーマーによる反射
]

AbilityFlag = Literal[
    "uncopyable",  # トレース・なかまづくり等でコピー/再現させない特性。
    "protected",  # スキルスワップ等の上書き・変更から保護する特性。
    "per_battle_once",  # 対戦中に一度だけ成立する性質を持つ特性。
    "mold_breaker_ignorable",  # かたやぶり系特性で無視される対象特性。
    "gas_proof",  # かがくへんかガスで無効化されない特性。
]

MoveFlag = Literal[
    "bite",  # かみつく系。がんじょうあご等の対象判定に使う。
    "bullet",  # たま・だん系。ぼうだん等の対象判定に使う。
    "bypass_substitute",  # みがわりを貫通する技。
    "contact",  # 接触技。さめはだ等の接触トリガー判定に使う。
    "dance",  # おどり技。おどりこ等の対象判定に使う。
    "gravity_restricted",  # じゅうりょく中に使用・選択不可になる技（はねる・そらをとぶ・でんじふゆう等）。
    "heal",  # 回復技。かいふくふうじ等の対象判定に使う。
    "non_copycat",  # まねっこで選ばれない技（スターモービル専用アクセル技）。
    "non_encore",  # アンコールで固定できない技。
    "non_negoto",  # ねごとで選ばれない技。
    "non_onnen",  # おんねんのPP消失対象外の技（わるあがき等）。
    "unprotectable",  # まもる等の防御効果を無視する技。
    "ohko",  # 一撃必殺技。
    "powder",  # 粉・胞子技。ぼうじん等の対象判定に使う。
    "protect",  # 守る系技。連続使用失敗の判定に使う（まもる・みきり・キングシールド・ニードルガード等）。
    "pulse",  # はどう技。メガランチャー等の対象判定に使う。
    "punch",  # パンチ技。てつのこぶし等の対象判定に使う。
    "physical_damage",  # 物理判定の特殊技。ダメージ計算に使う
    "recoil",  # 反動技。すてみ等の対象判定に使う。
    "slash",  # きる・つるぎ系。きれあじ等の対象判定に使う。
    "sound",  # 音技。ぼうおん等の対象判定に使う。
    "thaw",  # こおり状態で使用可能な技。こおり状態の解除判定に使う。
    "wind",  # 風技。かぜのり等の対象判定に使う。
    "minimize",  # ちいさくなる対象との相互作用を持つ技。
    "explosion",  # 爆発技。しめりけ等の対象判定に使う。
    "check_hit_each_time",  # 連続技で、毎回命中判定を行う技。
    "secondary_effect",  # 追加効果の有無。ちからずく・てんのめぐみ等の判定に使う。
]
