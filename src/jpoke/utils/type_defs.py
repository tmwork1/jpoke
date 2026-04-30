from typing import Literal

ContextRole = Literal["source", "target", "attacker", "defender"]

# role:side 形式で、特定の側のロールを指定
RoleSpec = Literal[
    "source:self", "source:foe",
    "target:self", "target:foe",
    "attacker:self",
    "defender:self",
]

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

VolatileName = Literal[
    "アクアリング",
    "あばれる",
    "あめまみれ",
    "アンコール",
    "いちゃもん",
    "うちおとす",
    "おんねん",
    "かいふくふうじ",
    "かなしばり",
    "かえんのまもり",
    "キングシールド",
    "きゅうしょアップ",
    "こだわり",
    "こんらん",
    "さわぐ",
    "さわがしい",
    "しおづけ",
    "じごくずき",
    "じゅうでん",
    "たくわえる",
    "タールショット",
    "ちいさくなる",
    "ちょうはつ",
    "でんじふゆう",
    "とくせいなし",
    "トーチカ",
    "にげられない",
    "ねむけ",
    "ねをはる",
    "のろい",
    "バインド",
    "ひるみ",
    "ふういん",
    "ほろびのうた",
    "マジックコート",
    "まるくなる",
    "まもる",
    "みがわり",
    "みちづれ",
    "メロメロ",
    "やどりぎのタネ",
    "ロックオン",
    "かくれる",
    "あなをほる",
    "そらをとぶ",
    "ダイビング",
    "シャドーダイブ",
    "スレッドトラップ",
]

GlobalField = Literal["じゅうりょく", "トリックルーム"]

SideField = Literal["リフレクター", "ひかりのかべ", "しんぴのまもり", "しろいきり", "おいかぜ", "ねがいごと",
                    "まきびし", "どくびし", "ステルスロック", "ねばねばネット", "オーロラベール"]

Weather = Literal["", "はれ", "あめ", "ゆき", "すなあらし"]

Terrain = Literal["", "エレキフィールド", "グラスフィールド", "サイコフィールド", "ミストフィールド"]

BoostSource = Literal["", "ability", "item", "weather", "terrain"]

HPChangeReason = Literal[
    "move_damage",          # 技によるダメージ
    "self_attack",          # こんらん自傷（ききかいひ不発）
    "pain_split",           # いたみわけ（ききかいひ不発）
    "other",                # その他のダメージ
]

ItemLostCause = Literal["", "consume", "remove", "swap", "steal", "burn", "gas"]

MoveLabel = Literal[
    "bite",  # かみつく系。がんじょうあご等の対象判定に使う。
    "bullet",  # たま・だん系。ぼうだん等の対象判定に使う。
    "bypass_substitute",  # みがわりを貫通する技。
    "contact",  # 接触技。さめはだ等の接触トリガー判定に使う。
    "dance",  # おどり技。おどりこ等の対象判定に使う。
    "heal",  # 回復技。かいふくふうじ等の対象判定に使う。
    "non_encore",  # アンコールで指定不可の技。
    "ohko",  # 一撃必殺技。
    "powder",  # 粉・胞子技。ぼうじん等の対象判定に使う。
    "pulse",  # はどう技。メガランチャー等の対象判定に使う。
    "punch",  # パンチ技。てつのこぶし等の対象判定に使う。
    "slash",  # きる・つるぎ系。きれあじ等の対象判定に使う。
    "sound",  # 音技。ぼうおん等の対象判定に使う。
    "wind",  # 風技。かぜのり等の対象判定に使う。
    "minimize",  # ちいさくなる対象との相互作用を持つ技。
]

AbilityFlag = Literal[
    "uncopyable",  # トレース・なかまづくり等でコピー/再現させない特性。
    "protected",  # スキルスワップ等の上書き・変更から保護する特性。
    "undeniable",  # かがくへんかガス等でも基本的に無効化されない特性。
    "per_battle_once",  # 対戦中に一度だけ成立する性質を持つ特性。
    "mold_breaker_ignorable",  # かたやぶり系特性で無視される対象特性。
]

