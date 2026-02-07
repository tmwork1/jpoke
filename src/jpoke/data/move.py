"""技データ定義モジュール。

Note:
    このモジュール内の技定義はMOVES辞書内で五十音順に配置されています。
"""
from functools import partial
from jpoke.core.event import Event, Handler, HandlerReturn
from .models import MoveData
from jpoke.handlers import common, move as h, volatile as v


def common_setup() -> None:
    """
    全ての技に共通ハンドラを追加する。

    この関数は、MOVESディクショナリ内の全てのMoveDataに対して、
    PP消費のためのON_CONSUME_PPイベントハンドラを追加します。

    追加されるハンドラ:
        - ON_CONSUME_PP: 技使用時のPP消費処理

    呼び出しタイミング: モジュール初期化時（ファイル末尾）

    Note:
        dictインスタンスはスキップされます（MoveDataオブジェクトのみ処理）
    """
    for name, obj in MOVES.items():
        MOVES[name].name = name

        # 共通ハンドラを追加
        MOVES[name].handlers |= {
            Event.ON_CONSUME_PP: h.MoveHandler(
                h.consume_pp,
                subject_spec="attacker:self",
                log="always"
            ),
        }


MOVES: dict[str, MoveData] = {
    "１０まんばりき": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=95,
        accuracy=95,
        flags=["contact"],
    ),
    "３ぼんのや": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,

        flags=["high_critical"],
    ),
    "ＤＤラリアット": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=85,
        accuracy=100,
        flags=["contact"],
    ),
    "Ｇのちから": MoveData(
        type="くさ",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,

    ),
    "アームハンマー": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=100,
        accuracy=90,
        flags=["contact", "punch"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(
                    common.modify_stat, stat="S", v=-1, target_spec="attacker:self", source_spec="attacker:self"
                ),
            )
        }
    ),
    "アイアンテール": MoveData(
        type="はがね",
        category="物理",
        pp=15,
        power=100,
        accuracy=75,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self", prob=0.3)
            )
        }
    ),
    "アイアンヘッド": MoveData(
        type="はがね",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,

        flags=["contact"],
    ),
    "アイアンローラー": MoveData(
        type="はがね",
        category="物理",
        pp=5,
        power=130,
        accuracy=100,
        flags=["contact"],
    ),
    "アイススピナー": MoveData(
        type="こおり",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,
        flags=["contact"],
    ),
    "アイスハンマー": MoveData(
        type="こおり",
        category="物理",
        pp=10,
        power=100,
        accuracy=90,

        flags=["contact", "punch"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-1, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "アクアカッター": MoveData(
        type="みず",
        category="物理",
        pp=20,
        power=70,
        accuracy=100,
        flags=["slash", "high_critical"],
    ),
    "アクアジェット": MoveData(
        type="みず",
        category="物理",
        pp=20,
        power=40,
        accuracy=100,
        priority=1,
        flags=["contact"],
    ),
    "アクアステップ": MoveData(
        type="みず",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=1, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "アクアテール": MoveData(
        type="みず",
        category="物理",
        pp=10,
        power=90,
        accuracy=90,
        flags=["contact"],
    ),
    "アクアブレイク": MoveData(
        type="みず",
        category="物理",
        pp=10,
        power=85,
        accuracy=100,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self", prob=0.2)
            )
        }
    ),
    "アクセルブレイク": MoveData(
        type="かくとう",
        category="物理",
        pp=5,
        power=100,
        accuracy=100,
        flags=["contact"],
    ),
    "アクセルロック": MoveData(
        type="いわ",
        category="物理",
        pp=20,
        power=40,
        accuracy=100,
        priority=1,
        flags=["contact"],
    ),
    "アクロバット": MoveData(
        type="ひこう",
        category="物理",
        pp=15,
        power=55,
        accuracy=100,
        flags=["contact"],
    ),
    "あなをほる": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,
        flags=["contact", "hide"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="あなをほる", target_spec="attacker:self", source_spec="attacker:self", count=1),
            )
        }
    ),
    "あばれる": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=120,
        accuracy=100,
        flags=["contact", "rage"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                v.あばれる_apply,
            )
        }
    ),
    "あんこくきょうだ": MoveData(
        type="あく",
        category="物理",
        pp=5,
        power=75,
        accuracy=100,
        flags=["contact", "critical", "punch"],
    ),
    "イカサマ": MoveData(
        type="あく",
        category="物理",
        pp=15,
        power=95,
        accuracy=100,
        flags=["contact"],
    ),
    "いかりのまえば": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=0,
        accuracy=90,
        flags=["contact"],
    ),
    "いじげんラッシュ": MoveData(
        type="あく",
        category="物理",
        pp=5,
        power=100,
        accuracy=100,

        flags=["anti_protect"],
    ),
    "いっちょうあがり": MoveData(
        type="ドラゴン",
        category="物理",
        pp=10,
        power=80,
        accuracy=100
    ),
    "いわおとし": MoveData(
        type="いわ",
        category="物理",
        pp=15,
        power=50,
        accuracy=90
    ),
    "いわくだき": MoveData(
        type="かくとう",
        category="物理",
        pp=15,
        power=40,
        accuracy=100,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self", prob=0.5)
            )
        }
    ),
    "いわなだれ": MoveData(
        type="いわ",
        category="物理",
        pp=10,
        power=75,
        accuracy=90,

    ),
    "インファイト": MoveData(
        type="かくとう",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stats, stats={"B": -1, "D": -1}, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "ウェーブタックル": MoveData(
        type="みず",
        category="物理",
        pp=10,
        power=120,
        accuracy=100,

        flags=["contact"],
    ),
    "うちおとす": MoveData(
        type="いわ",
        category="物理",
        pp=15,
        power=50,
        accuracy=100
    ),
    "ウッドハンマー": MoveData(
        type="くさ",
        category="物理",
        pp=15,
        power=120,
        accuracy=100,

        flags=["contact"],
    ),
    "ウッドホーン": MoveData(
        type="くさ",
        category="物理",
        pp=10,
        power=75,
        accuracy=100,

        flags=["contact"],
    ),
    "うっぷんばらし": MoveData(
        type="あく",
        category="物理",
        pp=5,
        power=75,
        accuracy=100,
        flags=["contact"],
    ),
    "えだづき": MoveData(
        type="くさ",
        category="物理",
        pp=40,
        power=40,
        accuracy=100,
        flags=["contact"],
    ),
    "オーラぐるま": MoveData(
        type="でんき",
        category="物理",
        pp=10,
        power=110,
        accuracy=100,

    ),
    "おどろかす": MoveData(
        type="ゴースト",
        category="物理",
        pp=15,
        power=30,
        accuracy=100,

        flags=["contact"],
    ),
    "おはかまいり": MoveData(
        type="ゴースト",
        category="物理",
        pp=10,
        power=50,
        accuracy=100
    ),
    "かいりき": MoveData(
        type="ノーマル",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,
        flags=["contact"],
    ),
    "カウンター": MoveData(
        type="かくとう",
        category="物理",
        pp=20,
        power=0,
        accuracy=100,
        priority=-5,
        flags=["contact"],
    ),
    "かえんぐるま": MoveData(
        type="ほのお",
        category="物理",
        pp=25,
        power=60,
        accuracy=100,

        flags=["contact", "unfreeze"],
    ),
    "かえんボール": MoveData(
        type="ほのお",
        category="物理",
        pp=5,
        power=120,
        accuracy=90,

        flags=["bullet", "unfreeze"],
    ),
    "かかとおとし": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=120,
        accuracy=90,

        flags=["contact"],
    ),
    "かげうち": MoveData(
        type="ゴースト",
        category="物理",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        flags=["contact"],
    ),
    "かげぬい": MoveData(
        type="ゴースト",
        category="物理",
        pp=10,
        power=80,
        accuracy=100
    ),
    "かたきうち": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=70,
        accuracy=100,
        flags=["contact"],
    ),
    "かみくだく": MoveData(
        type="あく",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,

        flags=["bite", "contact"],
    ),
    "かみつく": MoveData(
        type="あく",
        category="物理",
        pp=25,
        power=60,
        accuracy=100,

        flags=["bite", "contact"],
    ),
    "かみなりのキバ": MoveData(
        type="でんき",
        category="物理",
        pp=15,
        power=65,
        accuracy=95,

        flags=["contact"],
    ),
    "かみなりパンチ": MoveData(
        type="でんき",
        category="物理",
        pp=15,
        power=75,
        accuracy=100,

        flags=["contact", "punch"],
    ),
    "がむしゃら": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=0,
        accuracy=100,
        flags=["contact"],
    ),
    "からげんき": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=70,
        accuracy=100,
        flags=["contact"],
    ),
    "ガリョウテンセイ": MoveData(
        type="ひこう",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stats, stats={"B": -1, "D": -1}, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "かわらわり": MoveData(
        type="かくとう",
        category="物理",
        pp=15,
        power=75,
        accuracy=100,
        flags=["contact", "break_wall"],
    ),
    "がんせきアックス": MoveData(
        type="いわ",
        category="物理",
        pp=15,
        power=65,
        accuracy=90,
        flags=["contact", "slash"],
    ),
    "がんせきふうじ": MoveData(
        type="いわ",
        category="物理",
        pp=15,
        power=60,
        accuracy=95,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "がんせきほう": MoveData(
        type="いわ",
        category="物理",
        pp=5,
        power=150,
        accuracy=90,
        flags=["bullet", "immovable"],
    ),
    "きあいパンチ": MoveData(
        type="かくとう",
        category="物理",
        pp=20,
        power=150,
        accuracy=100,
        priority=-3,
        flags=["contact", "non_negoto", "punch", "quick_charge"],
    ),
    "ギガインパクト": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=150,
        accuracy=90,
        flags=["contact", "immovable"],
    ),
    "きしかいせい": MoveData(
        type="かくとう",
        category="物理",
        pp=15,
        power=1,
        accuracy=100,
        flags=["contact", "variable_power"],
    ),
    "きゅうけつ": MoveData(
        type="むし",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(h.apply_hp_drain, rate=0.5),
            )
        }
    ),
    "きょけんとつげき": MoveData(
        type="ドラゴン",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,
        flags=["contact"],
    ),
    "きょじゅうざん": MoveData(
        type="はがね",
        category="物理",
        pp=5,
        power=100,
        accuracy=100,
        flags=["contact", "slash"],
    ),
    "きょじゅうだん": MoveData(
        type="はがね",
        category="物理",
        pp=5,
        power=100,
        accuracy=100,
        flags=["contact"],
    ),
    "キラースピン": MoveData(
        type="どく",
        category="物理",
        pp=15,
        power=30,
        accuracy=100,

        flags=["contact"],
    ),
    "きりさく": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=70,
        accuracy=100,
        flags=["contact", "slash", "high_critical"],
    ),
    "クイックターン": MoveData(
        type="みず",
        category="物理",
        pp=20,
        power=60,
        accuracy=100,
        flags=["contact", "switch"],
    ),
    "くさわけ": MoveData(
        type="くさ",
        category="物理",
        pp=20,
        power=50,
        accuracy=100,

        flags=["contact"],
    ),
    "くちばしキャノン": MoveData(
        type="ひこう",
        category="物理",
        pp=15,
        power=100,
        accuracy=100,
        priority=-3,
        flags=["bullet", "non_negoto", "quick_charge"],
    ),
    "くらいつく": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,
        flags=["bite", "contact"],
    ),
    "グラススライダー": MoveData(
        type="くさ",
        category="物理",
        pp=20,
        power=55,
        accuracy=100,
        priority=1,
        flags=["contact"],
    ),
    "クラブハンマー": MoveData(
        type="みず",
        category="物理",
        pp=10,
        power=100,
        accuracy=90,
        flags=["contact", "high_critical"],
    ),
    "クロスサンダー": MoveData(
        type="でんき",
        category="物理",
        pp=5,
        power=100,
        accuracy=100
    ),
    "クロスチョップ": MoveData(
        type="かくとう",
        category="物理",
        pp=5,
        power=100,
        accuracy=80,
        flags=["contact", "high_critical"],
    ),
    "クロスポイズン": MoveData(
        type="どく",
        category="物理",
        pp=20,
        power=70,
        accuracy=100,

        flags=["contact", "slash", "high_critical"],
    ),
    "げきりん": MoveData(
        type="ドラゴン",
        category="物理",
        pp=10,
        power=120,
        accuracy=100,
        flags=["contact", "rage"],
    ),
    "けたぐり": MoveData(
        type="かくとう",
        category="物理",
        pp=20,
        power=1,
        accuracy=100,
        flags=["contact", "variable_power"],
    ),
    "こうげきしれい": MoveData(
        type="むし",
        category="物理",
        pp=15,
        power=90,
        accuracy=100,
        flags=["high_critical"],
    ),
    "こうそくスピン": MoveData(
        type="ノーマル",
        category="物理",
        pp=40,
        power=50,
        accuracy=100,

        flags=["contact"],
    ),
    "ゴーストダイブ": MoveData(
        type="ゴースト",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,
        flags=["contact", "hide", "anti_protect"],
    ),
    "こおりのキバ": MoveData(
        type="こおり",
        category="物理",
        pp=15,
        power=65,
        accuracy=95,

        flags=["contact"],
    ),
    "こおりのつぶて": MoveData(
        type="こおり",
        category="物理",
        pp=30,
        power=40,
        accuracy=100,
        priority=1
    ),
    "ゴッドバード": MoveData(
        type="ひこう",
        category="物理",
        pp=5,
        power=140,
        accuracy=90,

        flags=["charge", "high_critical"],
    ),
    "このは": MoveData(
        type="くさ",
        category="物理",
        pp=40,
        power=40,
        accuracy=100
    ),
    "コメットパンチ": MoveData(
        type="はがね",
        category="物理",
        pp=10,
        power=90,
        accuracy=90,
        flags=["contact", "punch"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=1, target_spec="attacker:self", source_spec="attacker:self", prob=0.2)
            )
        }
    ),
    "ころがる": MoveData(
        type="いわ",
        category="物理",
        pp=20,
        power=30,
        accuracy=90,
        flags=["contact"],
    ),
    "サイコカッター": MoveData(
        type="エスパー",
        category="物理",
        pp=20,
        power=70,
        accuracy=100,
        flags=["slash", "high_critical"],
    ),
    "サイコファング": MoveData(
        type="エスパー",
        category="物理",
        pp=10,
        power=85,
        accuracy=100,
        flags=["bite", "contact", "break_wall"],
    ),
    "サイコブレイド": MoveData(
        type="エスパー",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,
        flags=["contact"],
    ),
    "サンダーダイブ": MoveData(
        type="でんき",
        category="物理",
        pp=15,
        power=100,
        accuracy=95,

        flags=["contact"],
    ),
    "ジェットパンチ": MoveData(
        type="みず",
        category="物理",
        pp=15,
        power=60,
        accuracy=100,
        priority=1,
        flags=["contact", "punch"],
    ),
    "シェルブレード": MoveData(
        type="みず",
        category="物理",
        pp=10,
        power=75,
        accuracy=95,
        flags=["contact", "slash"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self", prob=0.5)
            )
        }
    ),
    "しおづけ": MoveData(
        type="いわ",
        category="物理",
        pp=15,
        power=40,
        accuracy=100
    ),
    "じごくづき": MoveData(
        type="あく",
        category="物理",
        pp=15,
        power=80,
        accuracy=100
    ),
    "シザークロス": MoveData(
        type="むし",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,
        flags=["contact", "slash"],
    ),
    "じしん": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=100,
        accuracy=100
    ),
    "したでなめる": MoveData(
        type="ゴースト",
        category="物理",
        pp=30,
        power=30,
        accuracy=100,

        flags=["contact"],
    ),
    "じたばた": MoveData(
        type="ノーマル",
        category="物理",
        pp=15,
        power=1,
        accuracy=100,
        flags=["contact", "variable_power"],
    ),
    "じだんだ": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=75,
        accuracy=100,
        flags=["contact"],
    ),
    "しっぺがえし": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=50,
        accuracy=100,
        flags=["contact"],
    ),
    "じならし": MoveData(
        type="じめん",
        category="物理",
        pp=20,
        power=60,
        accuracy=100,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "しねんのずつき": MoveData(
        type="エスパー",
        category="物理",
        pp=15,
        power=80,
        accuracy=90,

        flags=["contact"],
    ),
    "じばく": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=200,
        accuracy=100,

    ),
    "しめつける": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=15,
        accuracy=85,
        flags=["bind", "contact"],
    ),
    "ジャイロボール": MoveData(
        type="はがね",
        category="物理",
        pp=5,
        power=1,
        accuracy=100,
        flags=["bullet", "contact", "variable_power"],
    ),
    "シャドークロー": MoveData(
        type="ゴースト",
        category="物理",
        pp=15,
        power=70,
        accuracy=100,
        flags=["contact", "high_critical"],
    ),
    "シャドーダイブ": MoveData(
        type="ゴースト",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,
        flags=["contact", "hide", "anti_protect"],
    ),
    "シャドーパンチ": MoveData(
        type="ゴースト",
        category="物理",
        pp=20,
        power=60,
        accuracy=0,
        flags=["contact", "punch"],
    ),
    "じゃれつく": MoveData(
        type="フェアリー",
        category="物理",
        pp=10,
        power=90,
        accuracy=90,

        flags=["contact"],
    ),
    "じわれ": MoveData(
        type="じめん",
        category="物理",
        pp=5,
        power=0,
        accuracy=30,
        flags=["one_ko"],
    ),
    "しんそく": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=80,
        accuracy=100,
        priority=2,
        flags=["contact"],
    ),
    "スイープビンタ": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=25,
        accuracy=85,
        flags=["contact", "combo_2_5"],
    ),
    "すいりゅうれんだ": MoveData(
        type="みず",
        category="物理",
        pp=5,
        power=25,
        accuracy=100,
        flags=["contact", "critical", "punch", "combo_3_3"],
    ),
    "スケイルショット": MoveData(
        type="ドラゴン",
        category="物理",
        pp=20,
        power=25,
        accuracy=90,
        flags=["combo_2_5"],
    ),
    "ずつき": MoveData(
        type="ノーマル",
        category="物理",
        pp=15,
        power=70,
        accuracy=100,

        flags=["contact"],
    ),
    "すてみタックル": MoveData(
        type="ノーマル",
        category="物理",
        pp=15,
        power=120,
        accuracy=100,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(h.apply_recoil, rate=1/3),
            )
        }
    ),
    "ストーンエッジ": MoveData(
        type="いわ",
        category="物理",
        pp=5,
        power=100,
        accuracy=80,
        flags=["high_critical"],
    ),
    "すなじごく": MoveData(
        type="じめん",
        category="物理",
        pp=15,
        power=35,
        accuracy=85,
        flags=["bind"],
    ),
    "スパーク": MoveData(
        type="でんき",
        category="物理",
        pp=20,
        power=65,
        accuracy=100,

        flags=["contact"],
    ),
    "スマートホーン": MoveData(
        type="はがね",
        category="物理",
        pp=10,
        power=70,
        accuracy=0,
        flags=["contact"],
    ),
    "せいなるつるぎ": MoveData(
        type="かくとう",
        category="物理",
        pp=15,
        power=90,
        accuracy=100,
        flags=["contact", "slash", "ignore_rank"],
    ),
    "せいなるほのお": MoveData(
        type="ほのお",
        category="物理",
        pp=5,
        power=100,
        accuracy=95,

        flags=["unfreeze"],
    ),
    "ソウルクラッシュ": MoveData(
        type="フェアリー",
        category="物理",
        pp=15,
        power=75,
        accuracy=100,
        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "ソーラーブレード": MoveData(
        type="くさ",
        category="物理",
        pp=10,
        power=125,
        accuracy=100,
        flags=["charge", "contact", "slash", "solar"],
    ),
    "そらをとぶ": MoveData(
        type="ひこう",
        category="物理",
        pp=15,
        power=90,
        accuracy=95,
        flags=["contact", "hide"],
    ),
    "たいあたり": MoveData(
        type="ノーマル",
        category="物理",
        pp=35,
        power=40,
        accuracy=100,

        flags=["contact"],
    ),
    "だいばくはつ": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=250,
        accuracy=100,

    ),
    "ダイビング": MoveData(
        type="みず",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,
        flags=["contact", "hide"],
    ),
    "だいふんげき": MoveData(
        type="ほのお",
        category="物理",
        pp=10,
        power=120,
        accuracy=100,
        flags=["rage"],
    ),
    "ダイヤストーム": MoveData(
        type="いわ",
        category="物理",
        pp=5,
        power=100,
        accuracy=95,

    ),
    "たきのぼり": MoveData(
        type="みず",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,

        flags=["contact"],
    ),
    "ダストシュート": MoveData(
        type="どく",
        category="物理",
        pp=5,
        power=120,
        accuracy=80,

    ),
    "たたきつける": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=80,
        accuracy=75,
        flags=["contact"],
    ),
    "タネばくだん": MoveData(
        type="くさ",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,
        flags=["bullet"],
    ),
    "タネマシンガン": MoveData(
        type="くさ",
        category="物理",
        pp=30,
        power=25,
        accuracy=100,
        flags=["bullet", "combo_2_5"],
    ),
    "ダブルアタック": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=35,
        accuracy=90,
        flags=["contact", "combo_2_2"],
    ),
    "ダブルウイング": MoveData(
        type="ひこう",
        category="物理",
        pp=10,
        power=40,
        accuracy=90,
        flags=["contact", "combo_2_2"],
    ),
    "ダメおし": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=60,
        accuracy=100,
        flags=["contact"],
    ),
    "だんがいのつるぎ": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=120,
        accuracy=85
    ),
    "ちきゅうなげ": MoveData(
        type="かくとう",
        category="物理",
        pp=20,
        power=0,
        accuracy=100,
        flags=["contact"],
    ),
    "ついばむ": MoveData(
        type="ひこう",
        category="物理",
        pp=20,
        power=60,
        accuracy=100,
        flags=["contact"],
    ),
    "つけあがる": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=20,
        accuracy=100,
        flags=["contact"],
    ),
    "つじぎり": MoveData(
        type="あく",
        category="物理",
        pp=15,
        power=70,
        accuracy=100,
        flags=["contact", "slash", "high_critical"],
    ),
    "ツタこんぼう": MoveData(
        type="くさ",
        category="物理",
        pp=10,
        power=100,
        accuracy=100,
        flags=["high_critical"],
    ),
    "つつく": MoveData(
        type="ひこう",
        category="物理",
        pp=35,
        power=35,
        accuracy=100,
        flags=["contact"],
    ),
    "つっぱり": MoveData(
        type="かくとう",
        category="物理",
        pp=20,
        power=15,
        accuracy=100,
        flags=["contact", "combo_2_5"],
    ),
    "つのでつく": MoveData(
        type="ノーマル",
        category="物理",
        pp=25,
        power=65,
        accuracy=100,
        flags=["contact"],
    ),
    "つのドリル": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=0,
        accuracy=30,
        flags=["contact", "one_ko"],
    ),
    "つばさでうつ": MoveData(
        type="ひこう",
        category="物理",
        pp=35,
        power=60,
        accuracy=100,
        flags=["contact"],
    ),
    "つばめがえし": MoveData(
        type="ひこう",
        category="物理",
        pp=20,
        power=60,
        accuracy=0,
        flags=["contact", "slash"],
    ),
    "つららおとし": MoveData(
        type="こおり",
        category="物理",
        pp=10,
        power=85,
        accuracy=90,

    ),
    "つららばり": MoveData(
        type="こおり",
        category="物理",
        pp=30,
        power=25,
        accuracy=100,
        flags=["combo_2_5"],
    ),
    "つるのムチ": MoveData(
        type="くさ",
        category="物理",
        pp=25,
        power=45,
        accuracy=100,
        flags=["contact"],
    ),
    "であいがしら": MoveData(
        type="むし",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,
        priority=2,
        flags=["contact", "first_turn"],
    ),
    "デカハンマー": MoveData(
        type="はがね",
        category="物理",
        pp=5,
        power=160,
        accuracy=100,
        flags=["unrepeatable"],
    ),
    "でんこうせっか": MoveData(
        type="ノーマル",
        category="物理",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        flags=["contact"],
    ),
    "でんこうそうげき": MoveData(
        type="でんき",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,
        flags=["contact"],
    ),
    "どくづき": MoveData(
        type="どく",
        category="物理",
        pp=20,
        power=80,
        accuracy=100,

        flags=["contact"],
    ),
    "どくどくのキバ": MoveData(
        type="どく",
        category="物理",
        pp=15,
        power=50,
        accuracy=100,

        flags=["contact"],
    ),
    "どくばり": MoveData(
        type="どく",
        category="物理",
        pp=35,
        power=15,
        accuracy=100,

    ),
    "どくばりセンボン": MoveData(
        type="どく",
        category="物理",
        pp=10,
        power=60,
        accuracy=100,

    ),
    "どげざつき": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=80,
        accuracy=0,
        flags=["contact"],
    ),
    "ドゲザン": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=85,
        accuracy=0,
        flags=["contact", "slash"],
    ),
    "とっしん": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=90,
        accuracy=85,

        flags=["contact"],
    ),
    "とっておき": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=140,
        accuracy=100,
        flags=["contact"],
    ),
    "とどめばり": MoveData(
        type="むし",
        category="物理",
        pp=25,
        power=50,
        accuracy=100,
        flags=["contact"],
    ),
    "とびかかる": MoveData(
        type="むし",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,
        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "とびつく": MoveData(
        type="むし",
        category="物理",
        pp=20,
        power=50,
        accuracy=100,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "とびはねる": MoveData(
        type="ひこう",
        category="物理",
        pp=5,
        power=85,
        accuracy=85,

        flags=["contact", "hide"],
    ),
    "とびひざげり": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=130,
        accuracy=90,

        flags=["contact"],
    ),
    "ともえなげ": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=60,
        accuracy=90,
        priority=-6,
        flags=["contact"],
    ),
    "ドラゴンアロー": MoveData(
        type="ドラゴン",
        category="物理",
        pp=10,
        power=50,
        accuracy=100,
        flags=["combo_2_2"],
    ),
    "ドラゴンクロー": MoveData(
        type="ドラゴン",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,
        flags=["contact"],
    ),
    "ドラゴンダイブ": MoveData(
        type="ドラゴン",
        category="物理",
        pp=10,
        power=100,
        accuracy=75,

        flags=["contact"],
    ),
    "ドラゴンテール": MoveData(
        type="ドラゴン",
        category="物理",
        pp=10,
        power=60,
        accuracy=90,
        priority=-6,
        flags=["contact"],
    ),
    "ドラゴンハンマー": MoveData(
        type="ドラゴン",
        category="物理",
        pp=15,
        power=90,
        accuracy=100,
        flags=["contact"],
    ),
    "ドラムアタック": MoveData(
        type="くさ",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "トリックフラワー": MoveData(
        type="くさ",
        category="物理",
        pp=10,
        power=70,
        accuracy=0,
        flags=["critical"],
    ),
    "トリプルアクセル": MoveData(
        type="こおり",
        category="物理",
        pp=10,
        power=20,
        accuracy=90,
        flags=["contact", "combo_3_3"],
    ),
    "トリプルキック": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=10,
        accuracy=90,
        flags=["contact", "combo_3_3"],
    ),
    "トリプルダイブ": MoveData(
        type="みず",
        category="物理",
        pp=10,
        power=30,
        accuracy=95,
        flags=["contact", "combo_3_3"],
    ),
    "ドリルくちばし": MoveData(
        type="ひこう",
        category="物理",
        pp=20,
        power=80,
        accuracy=100,
        flags=["contact"],
    ),
    "ドリルライナー": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=80,
        accuracy=95,
        flags=["contact", "high_critical"],
    ),
    "ドレインパンチ": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=75,
        accuracy=100,

        flags=["contact", "punch"],
    ),
    "トロピカルキック": MoveData(
        type="くさ",
        category="物理",
        pp=15,
        power=70,
        accuracy=100,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "どろぼう": MoveData(
        type="あく",
        category="物理",
        pp=25,
        power=60,
        accuracy=100,
        flags=["contact"],
    ),
    "とんぼがえり": MoveData(
        type="むし",
        category="物理",
        pp=20,
        power=70,
        accuracy=100,
        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(h.pivot)
        }
    ),
    "なげつける": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=1,
        accuracy=100,
        flags=["variable_power"],
    ),
    "にぎりつぶす": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=1,
        accuracy=100,
        flags=["contact", "variable_power"],
    ),
    "にどげり": MoveData(
        type="かくとう",
        category="物理",
        pp=30,
        power=30,
        accuracy=100,
        flags=["contact", "combo_2_2"],
    ),
    "ニトロチャージ": MoveData(
        type="ほのお",
        category="物理",
        pp=20,
        power=50,
        accuracy=100,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=1, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "ねこだまし": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=40,
        accuracy=100,
        priority=3,
        flags=["contact", "first_turn"],
    ),
    "ネコにこばん": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=40,
        accuracy=100
    ),
    "ネズミざん": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=20,
        accuracy=90,
        flags=["contact", "slash", "combo_10_10"],
    ),
    "のしかかり": MoveData(
        type="ノーマル",
        category="物理",
        pp=15,
        power=85,
        accuracy=100,

        flags=["contact"],
    ),
    "ハードプレス": MoveData(
        type="はがね",
        category="物理",
        pp=10,
        power=1,
        accuracy=100,
        flags=["contact", "variable_power"],
    ),
    "ハイパードリル": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=100,
        accuracy=100,
        flags=["contact", "anti_protect"],
    ),
    "はいよるいちげき": MoveData(
        type="むし",
        category="物理",
        pp=10,
        power=70,
        accuracy=90,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "ばかぢから": MoveData(
        type="かくとう",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stats, stats={"A": -1, "B": -1}, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "はがねのつばさ": MoveData(
        type="はがね",
        category="物理",
        pp=25,
        power=70,
        accuracy=90,

        flags=["contact"],
    ),
    "ばくれつパンチ": MoveData(
        type="かくとう",
        category="物理",
        pp=5,
        power=100,
        accuracy=50,

        flags=["contact", "punch"],
    ),
    "ハサミギロチン": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=0,
        accuracy=30,
        flags=["contact", "contact", "one_ko"],
    ),
    "はさむ": MoveData(
        type="ノーマル",
        category="物理",
        pp=30,
        power=55,
        accuracy=100,
        flags=["contact", "contact"],
    ),
    "はたきおとす": MoveData(
        type="あく",
        category="物理",
        pp=20,
        power=65,
        accuracy=100,
        flags=["contact", "contact"],
    ),
    "はたく": MoveData(
        type="ノーマル",
        category="物理",
        pp=35,
        power=40,
        accuracy=100,
        flags=["contact", "contact"],
    ),
    "はっけい": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=60,
        accuracy=100,

        flags=["contact"],
    ),
    "はっぱカッター": MoveData(
        type="くさ",
        category="物理",
        pp=25,
        power=55,
        accuracy=95,
        flags=["slash", "high_critical"],
    ),
    "はなふぶき": MoveData(
        type="くさ",
        category="物理",
        pp=15,
        power=90,
        accuracy=100,
        flags=["wind"],
    ),
    "はやてがえし": MoveData(
        type="かくとう",
        category="物理",
        pp=15,
        power=65,
        accuracy=100,
        priority=3,
        flags=["contact"],
    ),
    "バリアーラッシュ": MoveData(
        type="エスパー",
        category="物理",
        pp=10,
        power=70,
        accuracy=90,

        flags=["contact"],
    ),
    "バレットパンチ": MoveData(
        type="はがね",
        category="物理",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        flags=["contact", "punch"],
    ),
    "パワーウィップ": MoveData(
        type="くさ",
        category="物理",
        pp=10,
        power=120,
        accuracy=85,
        flags=["contact"],
    ),
    "パワフルエッジ": MoveData(
        type="いわ",
        category="物理",
        pp=5,
        power=95,
        accuracy=100,
        flags=["contact", "anti_protect"],
    ),
    "ヒートスタンプ": MoveData(
        type="ほのお",
        category="物理",
        pp=10,
        power=1,
        accuracy=100,
        flags=["contact", "variable_power"],
    ),
    "ひけん・ちえなみ": MoveData(
        type="あく",
        category="物理",
        pp=15,
        power=65,
        accuracy=90,
        flags=["contact"],
    ),
    "ひっかく": MoveData(
        type="ノーマル",
        category="物理",
        pp=35,
        power=40,
        accuracy=100,
        flags=["contact"],
    ),
    "ひょうざんおろし": MoveData(
        type="こおり",
        category="物理",
        pp=10,
        power=100,
        accuracy=85,

    ),
    "びりびりちくちく": MoveData(
        type="でんき",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,

        flags=["contact"],
    ),
    "ふいうち": MoveData(
        type="あく",
        category="物理",
        pp=5,
        power=70,
        accuracy=100,
        priority=1,
        flags=["contact"],
    ),
    "フェイタルクロー": MoveData(
        type="どく",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,

        flags=["contact"],
    ),
    "フェイント": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=30,
        accuracy=100,
        priority=2,
        flags=["anti_protect"],
    ),
    "ふくろだたき": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=0,
        accuracy=100
    ),
    "ぶちかまし": MoveData(
        type="じめん",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,

        flags=["contact", "punch"],
    ),
    "ふみつけ": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=65,
        accuracy=100,

        flags=["contact"],
    ),
    "フライングプレス": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=100,
        accuracy=95,
        flags=["contact"],
    ),
    "フリーズボルト": MoveData(
        type="こおり",
        category="物理",
        pp=5,
        power=140,
        accuracy=90,

        flags=["charge"],
    ),
    "ブリザードランス": MoveData(
        type="こおり",
        category="物理",
        pp=5,
        power=120,
        accuracy=100
    ),
    "フレアドライブ": MoveData(
        type="ほのお",
        category="物理",
        pp=15,
        power=120,
        accuracy=100,

        flags=["contact", "unfreeze"],
    ),
    "ブレイククロー": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=75,
        accuracy=95,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self", prob=0.5)
            )
        }
    ),
    "ブレイズキック": MoveData(
        type="ほのお",
        category="物理",
        pp=10,
        power=85,
        accuracy=90,

        flags=["contact", "high_critical"],
    ),
    "ブレイブバード": MoveData(
        type="ひこう",
        category="物理",
        pp=15,
        power=120,
        accuracy=100,

        flags=["contact"],
    ),
    "プレゼント": MoveData(
        type="ノーマル",
        category="物理",
        pp=15,
        power=0,
        accuracy=90
    ),
    "ふんどのこぶし": MoveData(
        type="ゴースト",
        category="物理",
        pp=10,
        power=50,
        accuracy=100,
        flags=["contact", "punch"],
    ),
    "ぶんまわす": MoveData(
        type="あく",
        category="物理",
        pp=20,
        power=60,
        accuracy=100,
        flags=["contact"],
    ),
    "ヘビーボンバー": MoveData(
        type="はがね",
        category="物理",
        pp=10,
        power=1,
        accuracy=100,
        flags=["contact", "variable_power"],
    ),
    "ホイールスピン": MoveData(
        type="はがね",
        category="物理",
        pp=5,
        power=100,
        accuracy=100,

        flags=["contact"],
    ),
    "ポイズンテール": MoveData(
        type="どく",
        category="物理",
        pp=25,
        power=50,
        accuracy=100,

        flags=["contact", "high_critical"],
    ),
    "ほうふく": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=0,
        accuracy=100,
        flags=["contact"],
    ),
    "ボーンラッシュ": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=25,
        accuracy=90,
        flags=["combo_2_5"],
    ),
    "ほしがる": MoveData(
        type="ノーマル",
        category="物理",
        pp=25,
        power=60,
        accuracy=100,
        flags=["contact"],
    ),
    "ほっぺすりすり": MoveData(
        type="でんき",
        category="物理",
        pp=20,
        power=20,
        accuracy=100,

        flags=["contact"],
    ),
    "ボディプレス": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,
        flags=["contact"],
    ),
    "ほのおのキバ": MoveData(
        type="ほのお",
        category="物理",
        pp=15,
        power=65,
        accuracy=95,

        flags=["contact"],
    ),
    "ほのおのパンチ": MoveData(
        type="ほのお",
        category="物理",
        pp=15,
        power=75,
        accuracy=100,

        flags=["contact", "punch"],
    ),
    "ほのおのムチ": MoveData(
        type="ほのお",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,

        flags=["contact"],
    ),
    "ポルターガイスト": MoveData(
        type="ゴースト",
        category="物理",
        pp=5,
        power=110,
        accuracy=90
    ),
    "ボルテッカー": MoveData(
        type="でんき",
        category="物理",
        pp=15,
        power=120,
        accuracy=100,

        flags=["contact"],
    ),
    "まきつく": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=15,
        accuracy=90,
        flags=["bind", "contact"],
    ),
    "マッハパンチ": MoveData(
        type="かくとう",
        category="物理",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        flags=["contact", "punch"],
    ),
    "ミサイルばり": MoveData(
        type="むし",
        category="物理",
        pp=20,
        power=25,
        accuracy=95,
        flags=["combo_2_5"],
    ),
    "みだれづき": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=15,
        accuracy=85,
        flags=["contact", "combo_2_5"],
    ),
    "みだれひっかき": MoveData(
        type="ノーマル",
        category="物理",
        pp=15,
        power=18,
        accuracy=80,
        flags=["contact", "combo_2_5"],
    ),
    "みねうち": MoveData(
        type="ノーマル",
        category="物理",
        pp=40,
        power=40,
        accuracy=100,
        flags=["contact"],
    ),
    "むしくい": MoveData(
        type="むし",
        category="物理",
        pp=20,
        power=60,
        accuracy=100,
        flags=["contact"],
    ),
    "むねんのつるぎ": MoveData(
        type="ほのお",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,

        flags=["contact", "slash"],
    ),
    "メガトンキック": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=120,
        accuracy=75,
        flags=["contact"],
    ),
    "メガトンパンチ": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=80,
        accuracy=85,
        flags=["contact", "punch"],
    ),
    "メガホーン": MoveData(
        type="むし",
        category="物理",
        pp=10,
        power=120,
        accuracy=85,
        flags=["contact"],
    ),
    "メタルクロー": MoveData(
        type="はがね",
        category="物理",
        pp=35,
        power=50,
        accuracy=95,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=1, target_spec="attacker:self", source_spec="attacker:self", prob=0.1)
            )
        }
    ),
    "メタルバースト": MoveData(
        type="はがね",
        category="物理",
        pp=10,
        power=0,
        accuracy=100
    ),
    "メテオドライブ": MoveData(
        type="はがね",
        category="物理",
        pp=5,
        power=100,
        accuracy=100,
        flags=["ignore_ability"],
    ),
    "もろはのずつき": MoveData(
        type="いわ",
        category="物理",
        pp=5,
        power=150,
        accuracy=80,

        flags=["contact"],
    ),
    "やけっぱち": MoveData(
        type="ほのお",
        category="物理",
        pp=10,
        power=75,
        accuracy=100,
        flags=["contact"],
    ),
    "ゆきなだれ": MoveData(
        type="こおり",
        category="物理",
        pp=10,
        power=60,
        accuracy=100,
        priority=-4,
        flags=["contact"],
    ),
    "らいげき": MoveData(
        type="でんき",
        category="物理",
        pp=5,
        power=130,
        accuracy=85,

        flags=["contact"],
    ),
    "らいめいげり": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "リーフブレード": MoveData(
        type="くさ",
        category="物理",
        pp=15,
        power=90,
        accuracy=100,
        flags=["contact", "slash", "high_critical"],
    ),
    "レイジングブル": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,
        flags=["contact", "break_wall"],
    ),
    "れいとうパンチ": MoveData(
        type="こおり",
        category="物理",
        pp=15,
        power=75,
        accuracy=100,

        flags=["contact", "punch"],
    ),
    "れんぞくぎり": MoveData(
        type="むし",
        category="物理",
        pp=20,
        power=40,
        accuracy=95,
        flags=["contact", "slash"],
    ),
    "ローキック": MoveData(
        type="かくとう",
        category="物理",
        pp=20,
        power=65,
        accuracy=100,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "ロックブラスト": MoveData(
        type="いわ",
        category="物理",
        pp=10,
        power=25,
        accuracy=90,
        flags=["bullet", "combo_2_5"],
    ),
    "ワイドブレイカー": MoveData(
        type="ドラゴン",
        category="物理",
        pp=15,
        power=60,
        accuracy=100,

        flags=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "ワイルドボルト": MoveData(
        type="でんき",
        category="物理",
        pp=15,
        power=90,
        accuracy=100,

        flags=["contact"],
    ),
    "わるあがき": MoveData(
        type="ステラ",
        category="物理",
        pp=999,
        power=40,
        flags=["contact", "non_encore"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_hp, target_spec="attacker:self", r=-1/4),
            )
        }
    ),
    "１０まんボルト": MoveData(
        type="でんき",
        category="特殊",
        pp=15,
        power=90,
        accuracy=100
    ),
    "アーマーキャノン": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=120,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stats, stats={"B": -1, "D": -1}, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "あおいほのお": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=130,
        accuracy=85
    ),
    "あくうせつだん": MoveData(
        type="ドラゴン",
        category="特殊",
        pp=5,
        power=100,
        accuracy=95,
        flags=["high_critical"],
    ),
    "あくのはどう": MoveData(
        type="あく",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,

        flags=["wave"],
    ),
    "アシストパワー": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=20,
        accuracy=100
    ),
    "アシッドボム": MoveData(
        type="どく",
        category="特殊",
        pp=20,
        power=40,
        accuracy=100,

        flags=["bullet"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-2, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "アストラルビット": MoveData(
        type="ゴースト",
        category="特殊",
        pp=5,
        power=120,
        accuracy=100
    ),
    "いじげんホール": MoveData(
        type="エスパー",
        category="特殊",
        pp=5,
        power=80,
        accuracy=100,
        flags=["anti_protect"],
    ),
    "いてつくしせん": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-1, target_spec="defender:self", source_spec="attacker:self", prob=0.1)
            )
        }
    ),
    "イナズマドライブ": MoveData(
        type="でんき",
        category="特殊",
        pp=5,
        power=100,
        accuracy=100,
        flags=["contact"],
    ),
    "いにしえのうた": MoveData(
        type="ノーマル",
        category="特殊",
        pp=10,
        power=75,
        accuracy=100,

        flags=["sound"],
    ),
    "いのちがけ": MoveData(
        type="かくとう",
        category="特殊",
        pp=5,
        power=0,
        accuracy=100
    ),
    "いびき": MoveData(
        type="ノーマル",
        category="特殊",
        pp=15,
        power=50,
        accuracy=100,

        flags=["sound", "sleep"],
    ),
    "ウェザーボール": MoveData(
        type="ノーマル",
        category="特殊",
        pp=10,
        power=50,
        accuracy=100,
        flags=["bullet"],
    ),
    "うずしお": MoveData(
        type="みず",
        category="特殊",
        pp=15,
        power=35,
        accuracy=85,
        flags=["bind"],
    ),
    "うたかたのアリア": MoveData(
        type="みず",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,
        flags=["sound"],
    ),
    "うらみつらみ": MoveData(
        type="ゴースト",
        category="特殊",
        pp=10,
        power=75,
        accuracy=100,

    ),
    "エアカッター": MoveData(
        type="ひこう",
        category="特殊",
        pp=25,
        power=60,
        accuracy=95,
        flags=["slash", "high_critical", "wind"],
    ),
    "エアスラッシュ": MoveData(
        type="ひこう",
        category="特殊",
        pp=15,
        power=75,
        accuracy=95,

        flags=["slash"],
    ),
    "エアロブラスト": MoveData(
        type="ひこう",
        category="特殊",
        pp=5,
        power=100,
        accuracy=95,
        flags=["high_critical", "wind"],
    ),
    "エコーボイス": MoveData(
        type="ノーマル",
        category="特殊",
        pp=15,
        power=40,
        accuracy=100,
        flags=["sound"],
    ),
    "エナジーボール": MoveData(
        type="くさ",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        flags=["bullet"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-1, target_spec="defender:self", source_spec="attacker:self", prob=0.1)
            )
        }
    ),
    "エレキネット": MoveData(
        type="でんき",
        category="特殊",
        pp=15,
        power=55,
        accuracy=95,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "エレキボール": MoveData(
        type="でんき",
        category="特殊",
        pp=10,
        power=1,
        accuracy=100,
        flags=["bullet", "variable_power"],
    ),
    "エレクトロビーム": MoveData(
        type="でんき",
        category="特殊",
        pp=10,
        power=130,
        accuracy=100,
        flags=["charge"],
    ),
    "オーバードライブ": MoveData(
        type="でんき",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,
        flags=["sound"],
    ),
    "オーバーヒート": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=130,
        accuracy=90,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=-2, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "オーラウイング": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,

        flags=["high_critical"],
    ),
    "オーロラビーム": MoveData(
        type="こおり",
        category="特殊",
        pp=20,
        power=65,
        accuracy=100,

    ),
    "かえんほうしゃ": MoveData(
        type="ほのお",
        category="特殊",
        pp=15,
        power=90,
        accuracy=100,

    ),
    "かぜおこし": MoveData(
        type="ひこう",
        category="特殊",
        pp=35,
        power=40,
        accuracy=100,
        flags=["wind"],
    ),
    "カタストロフィ": MoveData(
        type="あく",
        category="特殊",
        pp=10,
        power=0,
        accuracy=90
    ),
    "かふんだんご": MoveData(
        type="むし",
        category="特殊",
        pp=15,
        power=90,
        accuracy=100,
        flags=["bullet"],
    ),
    "かみなり": MoveData(
        type="でんき",
        category="特殊",
        pp=10,
        power=110,
        accuracy=70,
        flags=["rainy_accuracy"],
        handlers={
            Event.ON_CALC_ACCURACY: h.MoveHandler(
                h.かみなり_accuracy,
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "かみなりあらし": MoveData(
        type="でんき",
        category="特殊",
        pp=10,
        power=100,
        accuracy=80,

        flags=["rainy_accuracy", "wind"],
    ),
    "きあいだま": MoveData(
        type="かくとう",
        category="特殊",
        pp=5,
        power=120,
        accuracy=70,

        flags=["bullet"],
    ),
    "ギガドレイン": MoveData(
        type="くさ",
        category="特殊",
        pp=10,
        power=75,
        accuracy=100,

    ),
    "きまぐレーザー": MoveData(
        type="ドラゴン",
        category="特殊",
        pp=5,
        power=80,
        accuracy=100
    ),
    "くさのちかい": MoveData(
        type="くさ",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100
    ),
    "くさむすび": MoveData(
        type="くさ",
        category="特殊",
        pp=20,
        power=1,
        accuracy=100,
        flags=["contact", "variable_power"],
    ),
    "クリアスモッグ": MoveData(
        type="どく",
        category="特殊",
        pp=15,
        power=50,
        accuracy=0
    ),
    "クロスフレイム": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=100,
        accuracy=100,
        flags=["unfreeze"],
    ),
    "クロロブラスト": MoveData(
        type="くさ",
        category="特殊",
        pp=5,
        power=150,
        accuracy=95,

    ),
    "ゲップ": MoveData(
        type="どく",
        category="特殊",
        pp=10,
        power=120,
        accuracy=90,
        flags=["non_negoto"],
    ),
    "げんしのちから": MoveData(
        type="いわ",
        category="特殊",
        pp=5,
        power=60,
        accuracy=100,

    ),
    "こおりのいぶき": MoveData(
        type="こおり",
        category="特殊",
        pp=10,
        power=60,
        accuracy=90,
        flags=["critical"],
    ),
    "コールドフレア": MoveData(
        type="こおり",
        category="特殊",
        pp=5,
        power=140,
        accuracy=90,

        flags=["charge"],
    ),
    "ゴールドラッシュ": MoveData(
        type="はがね",
        category="特殊",
        pp=5,
        power=120,
        accuracy=100,

    ),
    "こがらしあらし": MoveData(
        type="ひこう",
        category="特殊",
        pp=10,
        power=100,
        accuracy=80,

        flags=["rainy_accuracy", "wind"],
    ),
    "こごえるかぜ": MoveData(
        type="こおり",
        category="特殊",
        pp=15,
        power=55,
        accuracy=95,

        flags=["wind"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "こごえるせかい": MoveData(
        type="こおり",
        category="特殊",
        pp=10,
        power=65,
        accuracy=95,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "こなゆき": MoveData(
        type="こおり",
        category="特殊",
        pp=25,
        power=40,
        accuracy=100,

    ),
    "こんげんのはどう": MoveData(
        type="みず",
        category="特殊",
        pp=10,
        power=110,
        accuracy=85,
        flags=["wave"],
    ),
    "サイケこうせん": MoveData(
        type="エスパー",
        category="特殊",
        pp=20,
        power=65,
        accuracy=100,

    ),
    "サイコキネシス": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-1, target_spec="defender:self", source_spec="attacker:self", prob=0.1)
            )
        }
    ),
    "サイコショック": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,
        flags=["physical"],
    ),
    "サイコノイズ": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=75,
        accuracy=100,
        flags=["sound"],
    ),
    "サイコブースト": MoveData(
        type="エスパー",
        category="特殊",
        pp=5,
        power=140,
        accuracy=90,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=-2, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "サイコブレイク": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=100,
        accuracy=100,
        flags=["physical"],
    ),
    "さばきのつぶて": MoveData(
        type="ノーマル",
        category="特殊",
        pp=10,
        power=100,
        accuracy=100
    ),
    "さわぐ": MoveData(
        type="ノーマル",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,
        flags=["non_negoto", "sound"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                v.さわぐ_apply,
            )
        }
    ),
    "サンダープリズン": MoveData(
        type="でんき",
        category="特殊",
        pp=15,
        power=80,
        accuracy=90,
        flags=["bind"],
    ),
    "シードフレア": MoveData(
        type="くさ",
        category="特殊",
        pp=5,
        power=120,
        accuracy=85,

    ),
    "シェルアームズ": MoveData(
        type="どく",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        flags=["contact"],
    ),
    "しおふき": MoveData(
        type="みず",
        category="特殊",
        pp=5,
        power=150,
        accuracy=100
    ),
    "しおみず": MoveData(
        type="みず",
        category="特殊",
        pp=10,
        power=65,
        accuracy=100
    ),
    "しっとのほのお": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=70,
        accuracy=100
    ),
    "シャカシャカほう": MoveData(
        type="くさ",
        category="特殊",
        pp=15,
        power=80,
        accuracy=90,

        flags=["unfreeze"],
    ),
    "シャドーボール": MoveData(
        type="ゴースト",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,

        flags=["bullet"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-1, target_spec="defender:self", source_spec="attacker:self", prob=0.2)
            )
        }
    ),
    "シャドーレイ": MoveData(
        type="ゴースト",
        category="特殊",
        pp=5,
        power=100,
        accuracy=100,
        flags=["ignore_ability"],
    ),
    "しんくうは": MoveData(
        type="かくとう",
        category="特殊",
        pp=30,
        power=40,
        accuracy=100,
        priority=1
    ),
    "じんつうりき": MoveData(
        type="エスパー",
        category="特殊",
        pp=20,
        power=80,
        accuracy=100,

    ),
    "しんぴのちから": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=70,
        accuracy=90,

    ),
    "しんぴのつるぎ": MoveData(
        type="かくとう",
        category="特殊",
        pp=10,
        power=85,
        accuracy=100,
        flags=["slash", "physical"],
    ),
    "じんらい": MoveData(
        type="でんき",
        category="特殊",
        pp=5,
        power=70,
        accuracy=100,
        priority=1
    ),
    "すいとる": MoveData(
        type="くさ",
        category="特殊",
        pp=25,
        power=20,
        accuracy=100,

    ),
    "スケイルノイズ": MoveData(
        type="ドラゴン",
        category="特殊",
        pp=5,
        power=110,
        accuracy=100,

        flags=["sound"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "スチームバースト": MoveData(
        type="みず",
        category="特殊",
        pp=5,
        power=110,
        accuracy=95,

        flags=["unfreeze"],
    ),
    "スピードスター": MoveData(
        type="ノーマル",
        category="特殊",
        pp=20,
        power=60,
        accuracy=0
    ),
    "スモッグ": MoveData(
        type="どく",
        category="特殊",
        pp=20,
        power=30,
        accuracy=70,

    ),
    "ぜったいれいど": MoveData(
        type="こおり",
        category="特殊",
        pp=5,
        power=0,
        accuracy=30,
        flags=["one_ko"],
    ),
    "ソーラービーム": MoveData(
        type="くさ",
        category="特殊",
        pp=10,
        power=120,
        accuracy=100,
        flags=["charge", "solar"],
    ),
    "だいちのちから": MoveData(
        type="じめん",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

    ),
    "だいちのはどう": MoveData(
        type="ノーマル",
        category="特殊",
        pp=10,
        power=50,
        accuracy=100,
        flags=["wave"],
    ),
    "ダイマックスほう": MoveData(
        type="ドラゴン",
        category="特殊",
        pp=5,
        power=100,
        accuracy=100,
        flags=["non_encore", "non_negoto"],
    ),
    "だいもんじ": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=110,
        accuracy=85,

    ),
    "タキオンカッター": MoveData(
        type="はがね",
        category="特殊",
        pp=10,
        power=50,
        accuracy=100,
        flags=["combo_2_2"],
    ),
    "だくりゅう": MoveData(
        type="みず",
        category="特殊",
        pp=10,
        power=90,
        accuracy=85,

    ),
    "たたりめ": MoveData(
        type="ゴースト",
        category="特殊",
        pp=10,
        power=65,
        accuracy=100
    ),
    "たつまき": MoveData(
        type="ドラゴン",
        category="特殊",
        pp=20,
        power=40,
        accuracy=100,

        flags=["wind"],
    ),
    "チャージビーム": MoveData(
        type="でんき",
        category="特殊",
        pp=10,
        power=50,
        accuracy=90,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=1, target_spec="attacker:self", source_spec="attacker:self", prob=0.7)
            )
        }
    ),
    "チャームボイス": MoveData(
        type="フェアリー",
        category="特殊",
        pp=15,
        power=40,
        accuracy=0,
        flags=["sound"],
    ),
    "ツインビーム": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=40,
        accuracy=100,
        flags=["combo_2_2"],
    ),
    "てっていこうせん": MoveData(
        type="はがね",
        category="特殊",
        pp=5,
        power=140,
        accuracy=95,

    ),
    "テラクラスター": MoveData(
        type="ノーマル",
        category="特殊",
        pp=5,
        power=120,
        accuracy=100,
        flags=["terastal"],
    ),
    "テラバースト": MoveData(
        type="ノーマル",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,
        flags=["terastal"],
    ),
    "でんきショック": MoveData(
        type="でんき",
        category="特殊",
        pp=30,
        power=40,
        accuracy=100,

    ),
    "でんげきは": MoveData(
        type="でんき",
        category="特殊",
        pp=20,
        power=60,
        accuracy=0
    ),
    "でんじほう": MoveData(
        type="でんき",
        category="特殊",
        pp=5,
        power=120,
        accuracy=50,
        flags=["bullet"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.apply_ailment, ailment="まひ", target_spec="defender:self"),
            ),
        }
    ),
    "ときのほうこう": MoveData(
        type="ドラゴン",
        category="特殊",
        pp=5,
        power=150,
        accuracy=90,
        flags=["immovable"],
    ),
    "トライアタック": MoveData(
        type="ノーマル",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,

    ),
    "ドラゴンエナジー": MoveData(
        type="ドラゴン",
        category="特殊",
        pp=5,
        power=150,
        accuracy=100
    ),
    "ドレインキッス": MoveData(
        type="フェアリー",
        category="特殊",
        pp=10,
        power=50,
        accuracy=100,

        flags=["contact"],
    ),
    "どろかけ": MoveData(
        type="じめん",
        category="特殊",
        pp=10,
        power=20,
        accuracy=100,

    ),
    "ナイトバースト": MoveData(
        type="あく",
        category="特殊",
        pp=10,
        power=85,
        accuracy=95,

    ),
    "ナイトヘッド": MoveData(
        type="ゴースト",
        category="特殊",
        pp=15,
        power=0,
        accuracy=100
    ),
    "なみのり": MoveData(
        type="みず",
        category="特殊",
        pp=15,
        power=90,
        accuracy=100
    ),
    "ねっさのあらし": MoveData(
        type="じめん",
        category="特殊",
        pp=10,
        power=100,
        accuracy=80,

        flags=["rainy_accuracy", "wind"],
    ),
    "ねっさのだいち": MoveData(
        type="じめん",
        category="特殊",
        pp=10,
        power=70,
        accuracy=100,

        flags=["unfreeze"],
    ),
    "ねっとう": MoveData(
        type="みず",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,

        flags=["unfreeze"],
    ),
    "ねっぷう": MoveData(
        type="ほのお",
        category="特殊",
        pp=10,
        power=95,
        accuracy=90,

        flags=["wind"],
    ),
    "ねらいうち": MoveData(
        type="みず",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,
        flags=["high_critical"],
    ),
    "ねんりき": MoveData(
        type="エスパー",
        category="特殊",
        pp=25,
        power=50,
        accuracy=100,

    ),
    "バークアウト": MoveData(
        type="あく",
        category="特殊",
        pp=15,
        power=55,
        accuracy=95,

        flags=["sound"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "ハードプラント": MoveData(
        type="くさ",
        category="特殊",
        pp=5,
        power=150,
        accuracy=90,
        flags=["immovable"],
    ),
    "ハイドロカノン": MoveData(
        type="みず",
        category="特殊",
        pp=5,
        power=150,
        accuracy=90,
        flags=["immovable"],
    ),
    "ハイドロスチーム": MoveData(
        type="みず",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,
        flags=["unfreeze"],
    ),
    "ハイドロポンプ": MoveData(
        type="みず",
        category="特殊",
        pp=5,
        power=110,
        accuracy=80
    ),
    "ハイパーボイス": MoveData(
        type="ノーマル",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,
        flags=["sound"],
    ),
    "はかいこうせん": MoveData(
        type="ノーマル",
        category="特殊",
        pp=5,
        power=150,
        accuracy=90,
        flags=["immovable"],
    ),
    "はきだす": MoveData(
        type="ノーマル",
        category="特殊",
        pp=10,
        power=0,
        accuracy=100
    ),
    "ばくおんぱ": MoveData(
        type="ノーマル",
        category="特殊",
        pp=10,
        power=140,
        accuracy=100,
        flags=["sound"],
    ),
    "はどうだん": MoveData(
        type="かくとう",
        category="特殊",
        pp=20,
        power=80,
        accuracy=0,
        flags=["bullet", "wave"],
    ),
    "はなびらのまい": MoveData(
        type="くさ",
        category="特殊",
        pp=10,
        power=120,
        accuracy=100,
        flags=["contact", "rage"],
    ),
    "バブルこうせん": MoveData(
        type="みず",
        category="特殊",
        pp=20,
        power=65,
        accuracy=100,

    ),
    "はめつのねがい": MoveData(
        type="はがね",
        category="特殊",
        pp=5,
        power=140,
        accuracy=100
    ),
    "パラボラチャージ": MoveData(
        type="でんき",
        category="特殊",
        pp=20,
        power=65,
        accuracy=100,

    ),
    "はるのあらし": MoveData(
        type="フェアリー",
        category="特殊",
        pp=5,
        power=100,
        accuracy=80,

        flags=["wind"],
    ),
    "パワージェム": MoveData(
        type="いわ",
        category="特殊",
        pp=20,
        power=80,
        accuracy=100
    ),
    "ひのこ": MoveData(
        type="ほのお",
        category="特殊",
        pp=25,
        power=40,
        accuracy=100,

    ),
    "ひゃっきやこう": MoveData(
        type="ゴースト",
        category="特殊",
        pp=15,
        power=60,
        accuracy=100,

    ),
    "ひやみず": MoveData(
        type="みず",
        category="特殊",
        pp=20,
        power=50,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "フォトンゲイザー": MoveData(
        type="エスパー",
        category="特殊",
        pp=5,
        power=100,
        accuracy=100,
        flags=["ignore_ability"],
    ),
    "ぶきみなじゅもん": MoveData(
        type="エスパー",
        category="特殊",
        pp=5,
        power=80,
        accuracy=100,
        flags=["sound"],
    ),
    "ふぶき": MoveData(
        type="こおり",
        category="特殊",
        pp=5,
        power=110,
        accuracy=70,
        flags=["wind"],
        handlers={
            Event.ON_CALC_ACCURACY: h.MoveHandler(
                h.ふぶき_accuracy,
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "ブラストバーン": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=150,
        accuracy=90,
        flags=["immovable"],
    ),
    "ブラッドムーン": MoveData(
        type="ノーマル",
        category="特殊",
        pp=5,
        power=140,
        accuracy=100,
        flags=["unrepeatable"],
    ),
    "フリーズドライ": MoveData(
        type="こおり",
        category="特殊",
        pp=20,
        power=70,
        accuracy=100,

    ),
    "プリズムレーザー": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=160,
        accuracy=100,
        flags=["immovable"],
    ),
    "フルールカノン": MoveData(
        type="フェアリー",
        category="特殊",
        pp=5,
        power=130,
        accuracy=90,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=-2, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "フレアソング": MoveData(
        type="ほのお",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,

        flags=["sound"],
    ),
    "ふんえん": MoveData(
        type="ほのお",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,

    ),
    "ふんか": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=150,
        accuracy=100
    ),
    "ヘドロウェーブ": MoveData(
        type="どく",
        category="特殊",
        pp=10,
        power=95,
        accuracy=100,

    ),
    "ヘドロこうげき": MoveData(
        type="どく",
        category="特殊",
        pp=20,
        power=65,
        accuracy=100,

    ),
    "ヘドロばくだん": MoveData(
        type="どく",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        flags=["bullet"],
    ),
    "ベノムショック": MoveData(
        type="どく",
        category="特殊",
        pp=10,
        power=65,
        accuracy=100
    ),
    "ほうでん": MoveData(
        type="でんき",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,

    ),
    "ぼうふう": MoveData(
        type="ひこう",
        category="特殊",
        pp=10,
        power=110,
        accuracy=70,
        flags=["rainy_accuracy", "wind"],
        handlers={
            Event.ON_CALC_ACCURACY: h.MoveHandler(
                h.ぼうふう_accuracy,
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "ほのおのうず": MoveData(
        type="ほのお",
        category="特殊",
        pp=15,
        power=35,
        accuracy=85,
        flags=["bind"],
    ),
    "ほのおのちかい": MoveData(
        type="ほのお",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100
    ),
    "ほのおのまい": MoveData(
        type="ほのお",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,

    ),
    "ボルトチェンジ": MoveData(
        type="でんき",
        category="特殊",
        pp=20,
        power=70,
        accuracy=100,
        flags=["switch"],
    ),
    "マグマストーム": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=100,
        accuracy=75,
        flags=["bind"],
    ),
    "マジカルシャイン": MoveData(
        type="フェアリー",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100
    ),
    "マジカルフレイム": MoveData(
        type="ほのお",
        category="特殊",
        pp=10,
        power=75,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "マジカルリーフ": MoveData(
        type="くさ",
        category="特殊",
        pp=20,
        power=60,
        accuracy=0
    ),
    "マッドショット": MoveData(
        type="じめん",
        category="特殊",
        pp=15,
        power=55,
        accuracy=95,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "まとわりつく": MoveData(
        type="むし",
        category="特殊",
        pp=20,
        power=20,
        accuracy=100,
        flags=["bind", "contact"],
    ),
    "みずあめボム": MoveData(
        type="くさ",
        category="特殊",
        pp=10,
        power=60,
        accuracy=85
    ),
    "みずしゅりけん": MoveData(
        type="みず",
        category="特殊",
        pp=20,
        power=15,
        accuracy=100,
        priority=1,
        flags=["combo_2_5"],
    ),
    "みずでっぽう": MoveData(
        type="みず",
        category="特殊",
        pp=25,
        power=40,
        accuracy=100
    ),
    "ミストバースト": MoveData(
        type="フェアリー",
        category="特殊",
        pp=5,
        power=100,
        accuracy=100,

    ),
    "ミストボール": MoveData(
        type="エスパー",
        category="特殊",
        pp=5,
        power=95,
        accuracy=100,

        flags=["bullet"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=-1, target_spec="defender:self", source_spec="attacker:self", prob=0.5)
            )
        }
    ),
    "みずのちかい": MoveData(
        type="みず",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100
    ),
    "みずのはどう": MoveData(
        type="みず",
        category="特殊",
        pp=20,
        power=60,
        accuracy=100,

        flags=["wave"],
    ),
    "ミラーコート": MoveData(
        type="エスパー",
        category="特殊",
        pp=20,
        power=0,
        accuracy=100,
        priority=-5
    ),
    "みらいよち": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=120,
        accuracy=100
    ),
    "みわくのボイス": MoveData(
        type="フェアリー",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,
        flags=["sound"],
    ),
    "ムーンフォース": MoveData(
        type="フェアリー",
        category="特殊",
        pp=15,
        power=95,
        accuracy=100,

    ),
    "むしのさざめき": MoveData(
        type="むし",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        flags=["sound"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-1, target_spec="defender:self", source_spec="attacker:self", prob=0.1)
            )
        }
    ),
    "むしのていこう": MoveData(
        type="むし",
        category="特殊",
        pp=20,
        power=50,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "メガドレイン": MoveData(
        type="くさ",
        category="特殊",
        pp=15,
        power=40,
        accuracy=100,

    ),
    "めざめるダンス": MoveData(
        type="ノーマル",
        category="特殊",
        pp=15,
        power=90,
        accuracy=100
    ),
    "メテオビーム": MoveData(
        type="いわ",
        category="特殊",
        pp=10,
        power=120,
        accuracy=90,
        flags=["charge"],
    ),
    "もえあがるいかり": MoveData(
        type="あく",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

    ),
    "やきつくす": MoveData(
        type="ほのお",
        category="特殊",
        pp=15,
        power=60,
        accuracy=100
    ),
    "ゆめくい": MoveData(
        type="エスパー",
        category="特殊",
        pp=15,
        power=100,
        accuracy=100,

    ),
    "ようかいえき": MoveData(
        type="どく",
        category="特殊",
        pp=30,
        power=40,
        accuracy=100,

    ),
    "ようせいのかぜ": MoveData(
        type="フェアリー",
        category="特殊",
        pp=30,
        power=40,
        accuracy=100,
        flags=["wind"],
    ),
    "ライジングボルト": MoveData(
        type="でんき",
        category="特殊",
        pp=20,
        power=70,
        accuracy=100
    ),
    "ラスターカノン": MoveData(
        type="はがね",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-1, target_spec="defender:self", source_spec="attacker:self", prob=0.1)
            )
        }
    ),
    "ラスターパージ": MoveData(
        type="エスパー",
        category="特殊",
        pp=5,
        power=95,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-1, target_spec="defender:self", source_spec="attacker:self", prob=0.5)
            )
        }
    ),
    "リーフストーム": MoveData(
        type="くさ",
        category="特殊",
        pp=5,
        power=130,
        accuracy=90,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=-2, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "りゅうせいぐん": MoveData(
        type="ドラゴン",
        category="特殊",
        pp=5,
        power=130,
        accuracy=90,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=-2, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "りゅうのいぶき": MoveData(
        type="ドラゴン",
        category="特殊",
        pp=20,
        power=60,
        accuracy=100,

    ),
    "りゅうのはどう": MoveData(
        type="ドラゴン",
        category="特殊",
        pp=10,
        power=85,
        accuracy=100,
        flags=["wave"],
    ),
    "りんごさん": MoveData(
        type="くさ",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,

    ),
    "りんしょう": MoveData(
        type="ノーマル",
        category="特殊",
        pp=15,
        power=60,
        accuracy=100,
        flags=["sound"],
    ),
    "ルミナコリジョン": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "れいとうビーム": MoveData(
        type="こおり",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

    ),
    "れんごく": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=100,
        accuracy=50,

    ),
    "ワイドフォース": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100
    ),
    "ワンダースチーム": MoveData(
        type="フェアリー",
        category="特殊",
        pp=10,
        power=90,
        accuracy=95,

    ),
    "アクアリング": MoveData(
        type="みず",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "あくび": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "あくまのキッス": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=75,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "あさのひざし": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "あまいかおり": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="EVA", v=-2, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "あまえる": MoveData(
        type="フェアリー",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=-2, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "あまごい": MoveData(
        type="みず",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "あやしいひかり": MoveData(
        type="ゴースト",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "アロマセラピー": MoveData(
        type="くさ",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "アロマミスト": MoveData(
        type="フェアリー",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "アンコール": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold", "reflectable", "non_encore"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.apply_volatile, volatile="アンコール", target_spec="defender:self", source_spec="attacker:self", count=3),
            )
        }
    ),
    "いえき": MoveData(
        type="どく",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "いかりのこな": MoveData(
        type="むし",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        priority=2,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "いたみわけ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "いちゃもん": MoveData(
        type="あく",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.apply_volatile, volatile="いちゃもん", target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "いとをはく": MoveData(
        type="むし",
        category="変化",
        pp=40,
        power=0,
        accuracy=95,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "いのちのしずく": MoveData(
        type="みず",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "いばる": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        power=0,
        accuracy=85,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "いやしのすず": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "sound"],
    ),
    "いやしのねがい": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "いやしのはどう": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["blocked_by_gold", "reflectable", "heal"],
    ),
    "いやなおと": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        power=0,
        accuracy=85,
        flags=["ignore_substitute", "blocked_by_gold", "reflectable", "sound"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-2, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "うそなき": MoveData(
        type="あく",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-2, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "うたう": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        power=0,
        accuracy=55,
        flags=["ignore_substitute", "blocked_by_gold", "reflectable", "sound"],
    ),
    "うつしえ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["unprotectable", "blocked_by_gold"],
    ),
    "うらみ": MoveData(
        type="ゴースト",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "blocked_by_gold", "reflectable"],
    ),
    "エレキフィールド": MoveData(
        type="でんき",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "えんまく": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="ACC", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "おいかぜ": MoveData(
        type="ひこう",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "wind"],
    ),
    "おいわい": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "non_negoto"],
    ),
    "オーロラベール": MoveData(
        type="こおり",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "おかたづけ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "おきみやげ": MoveData(
        type="あく",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold"],
    ),
    "おさきにどうぞ": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "おたけび": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold", "reflectable", "sound"],
    ),
    "おだてる": MoveData(
        type="あく",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        flags=["unprotectable", "blocked_by_gold", "reflectable"],
    ),
    "おちゃかい": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["ignore_substitute", "blocked_by_gold"],
    ),
    "おにび": MoveData(
        type="ほのお",
        category="変化",
        pp=15,
        power=0,
        accuracy=85,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "ガードシェア": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold"],
    ),
    "ガードスワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold"],
    ),
    "かいでんぱ": MoveData(
        type="でんき",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "かいふくふうじ": MoveData(
        type="エスパー",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "かえんのまもり": MoveData(
        type="ほのお",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        priority=4,
        flags=["unprotectable", "ignore_substitute", "protect"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="かえんのまもり", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "かげぶんしん": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "かたくなる": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=1, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "かなしばり": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold", "reflectable"],
    ),
    "からにこもる": MoveData(
        type="みず",
        category="変化",
        pp=40,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=1, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "からをやぶる": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "きあいだめ": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "ギアチェンジ": MoveData(
        type="はがね",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "キノコのほうし": MoveData(
        type="くさ",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable", "powder"],
    ),
    "きりばらい": MoveData(
        type="ひこう",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        flags=["ignore_substitute", "blocked_by_gold", "reflectable"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="EVA", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "きんぞくおん": MoveData(
        type="はがね",
        category="変化",
        pp=40,
        power=0,
        accuracy=85,
        flags=["ignore_substitute", "blocked_by_gold", "reflectable", "sound"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-2, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "くすぐる": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "グラスフィールド": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "くろいきり": MoveData(
        type="こおり",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "くろいまなざし": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=100,
        flags=["unprotectable", "blocked_by_gold", "reflectable"],
    ),
    "こうごうせい": MoveData(
        type="くさ",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "こうそくいどう": MoveData(
        type="エスパー",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=2, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "コーチング": MoveData(
        type="かくとう",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold"],
    ),
    "コートチェンジ": MoveData(
        type="ノーマル",
        category="変化",
        pp=100,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "コスモパワー": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "コットンガード": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=3, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "このゆびとまれ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        priority=2,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "こらえる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        priority=4,
        flags=["unprotectable", "ignore_substitute", "protect"],
    ),
    "こわいかお": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-2, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "さいきのいのり": MoveData(
        type="ノーマル",
        category="変化",
        pp=0,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "サイコフィールド": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "サイドチェンジ": MoveData(
        type="エスパー",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        priority=2,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "さいはい": MoveData(
        type="エスパー",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        flags=["ignore_substitute", "blocked_by_gold"],
    ),
    "さいみんじゅつ": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        power=0,
        accuracy=60,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "さきおくり": MoveData(
        type="あく",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        flags=["ignore_substitute", "blocked_by_gold"],
    ),
    "さむいギャグ": MoveData(
        type="こおり",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "switch"],
    ),
    "じこあんじ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "じこさいせい": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "しっぽきり": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "switch"],
    ),
    "しっぽをふる": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "じばそうさ": MoveData(
        type="でんき",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable"],
    ),
    "しびれごな": MoveData(
        type="くさ",
        category="変化",
        pp=30,
        power=0,
        accuracy=75,
        flags=["blocked_by_gold", "reflectable", "powder"],
    ),
    "ジャングルヒール": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "じゅうでん": MoveData(
        type="でんき",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "じゅうりょく": MoveData(
        type="エスパー",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "しょうりのまい": MoveData(
        type="かくとう",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "しろいきり": MoveData(
        type="こおり",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "しんぴのまもり": MoveData(
        type="ノーマル",
        category="変化",
        pp=25,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "シンプルビーム": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "スキルスワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold"],
    ),
    "スケッチ": MoveData(
        type="ノーマル",
        category="変化",
        pp=0,
        power=0,
        accuracy=100,
        flags=["unprotectable", "ignore_substitute", "non_encore", "non_negoto"],
    ),
    "すてゼリフ": MoveData(
        type="あく",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold", "reflectable", "sound", "switch"],
    ),
    "ステルスロック": MoveData(
        type="いわ",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "reflectable"],
    ),
    "すなあつめ": MoveData(
        type="じめん",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "すなあらし": MoveData(
        type="いわ",
        category="変化",
        pp=10,
        flags=["unprotectable", "ignore_substitute", "wind"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.activate_weather, weather="すなあらし", source_spec="attacker:self"),
            )
        }
    ),
    "すなかけ": MoveData(
        type="じめん",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="ACC", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "スピードスワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold"],
    ),
    "すりかえ": MoveData(
        type="あく",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold"],
    ),
    "スレッドトラップ": MoveData(
        type="むし",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        priority=4,
        flags=["unprotectable", "ignore_substitute", "protect"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="スレッドトラップ", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "せいちょう": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "ソウルビート": MoveData(
        type="ドラゴン",
        category="変化",
        pp=100,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "sound"],
    ),
    "ダークホール": MoveData(
        type="あく",
        category="変化",
        pp=10,
        power=0,
        accuracy=50,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "タールショット": MoveData(
        type="いわ",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold", "reflectable"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.apply_volatile, volatile="タールショット", target_spec="defender:self", source_spec="attacker:self"),
            ),
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "たくわえる": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                v.たくわえる_apply,
            )
        }
    ),
    "たてこもる": MoveData(
        type="はがね",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "タマゴうみ": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "ちいさくなる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="ちいさくなる", target_spec="attacker:self", source_spec="attacker:self"),
            ),
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="EVA", v=2, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "ちからをすいとる": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable", "heal"],
    ),
    "ちょうおんぱ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=55,
        flags=["ignore_substitute", "blocked_by_gold", "reflectable", "sound"],
    ),
    "ちょうのまい": MoveData(
        type="むし",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "ちょうはつ": MoveData(
        type="あく",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold", "reflectable"],
    ),
    "つきのひかり": MoveData(
        type="フェアリー",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "つぶらなひとみ": MoveData(
        type="フェアリー",
        category="変化",
        pp=30,
        power=0,
        accuracy=100,
        priority=1,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "つぼをつく": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "つめとぎ": MoveData(
        type="あく",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "つるぎのまい": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
        }
    ),
    "テクスチャー": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "テクスチャー２": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,
        flags=["unprotectable"],
    ),
    "デコレーション": MoveData(
        type="フェアリー",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold"],
    ),
    "てだすけ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        priority=5,
        flags=["unprotectable"],
    ),
    "てっぺき": MoveData(
        type="はがね",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=2, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "テレポート": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        priority=-6,
        flags=["unprotectable", "ignore_substitute", "switch"],
    ),
    "てんしのキッス": MoveData(
        type="フェアリー",
        category="変化",
        pp=10,
        power=0,
        accuracy=75,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "でんじは": MoveData(
        type="でんき",
        category="変化",
        pp=20,
        power=0,
        accuracy=90,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "でんじふゆう": MoveData(
        type="でんき",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "とおせんぼう": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=100,
        flags=["unprotectable", "blocked_by_gold", "reflectable"],
    ),
    "トーチカ": MoveData(
        type="どく",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        priority=4,
        flags=["unprotectable", "ignore_substitute", "protect"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="トーチカ", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "とおぼえ": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "sound"],
    ),
    "どくガス": MoveData(
        type="どく",
        category="変化",
        pp=40,
        power=0,
        accuracy=90,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "どくどく": MoveData(
        type="どく",
        category="変化",
        pp=10,
        accuracy=90,
        flags=["blocked_by_gold", "reflectable"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.apply_ailment, ailment="もうどく", target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "どくのいと": MoveData(
        type="どく",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "どくのこな": MoveData(
        type="どく",
        category="変化",
        pp=35,
        power=0,
        accuracy=75,
        flags=["blocked_by_gold", "reflectable", "powder"],
    ),
    "どくびし": MoveData(
        type="どく",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "reflectable"],
    ),
    "とぐろをまく": MoveData(
        type="どく",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "とける": MoveData(
        type="どく",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "ドラゴンエール": MoveData(
        type="ドラゴン",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "トリック": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold"],
    ),
    "トリックルーム": MoveData(
        type="エスパー",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        priority=-7,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "ドわすれ": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=2, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "ないしょばなし": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "blocked_by_gold", "reflectable", "sound"],
    ),
    "なかまづくり": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "なかよくする": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "blocked_by_gold", "reflectable"],
    ),
    "なきごえ": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold", "reflectable", "sound"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "なまける": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "なみだめ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "blocked_by_gold", "reflectable"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "なやみのタネ": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "なりきり": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["unprotectable", "blocked_by_gold"],
    ),
    "ニードルガード": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        priority=4,
        flags=["unprotectable", "ignore_substitute", "protect"],
    ),
    "にほんばれ": MoveData(
        type="ほのお",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "にらみつける": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "ねがいごと": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "ねごと": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "non_encore", "non_negoto", "call_move", "sleep"],
    ),
    "ねばねばネット": MoveData(
        type="むし",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "ねむりごな": MoveData(
        type="くさ",
        category="変化",
        pp=15,
        power=0,
        accuracy=75,
        flags=["blocked_by_gold", "reflectable", "powder"],
    ),
    "ねむる": MoveData(
        type="エスパー",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "ねをはる": MoveData(
        type="くさ",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "のみこむ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "のろい": MoveData(
        type="ゴースト",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "blocked_by_gold"],
    ),
    "ハートスワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold"],
    ),
    "はいすいのじん": MoveData(
        type="かくとう",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "ハッピータイム": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "バトンタッチ": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "switch"],
    ),
    "はねやすめ": MoveData(
        type="ひこう",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "はねる": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        flags=["unprotectable", "ignore_substitute"]
    ),
    "ハバネロエキス": MoveData(
        type="くさ",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "はらだいこ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "パワーシェア": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold"],
    ),
    "パワースワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold"],
    ),
    "パワートリック": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold"],
    ),
    "ひかりのかべ": MoveData(
        type="エスパー",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "ひっくりかえす": MoveData(
        type="あく",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "ビルドアップ": MoveData(
        type="かくとう",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "ファストガード": MoveData(
        type="かくとう",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        priority=3,
        flags=["unprotectable", "ignore_substitute", "protect"],
    ),
    "ふういん": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="ふういん", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "フェアリーロック": MoveData(
        type="フェアリー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "フェザーダンス": MoveData(
        type="ひこう",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=-2, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "ふきとばし": MoveData(
        type="ノーマル",
        category="特殊",
        pp=20,
        priority=-6,
        flags=["unprotectable", "ignore_substitute", "blocked_by_gold", "reflectable", "wind"],
        handlers={
            Event.ON_HIT: h.MoveHandler(h.blow)
        }
    ),
    "フラフラダンス": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold"],
    ),
    "フラワーヒール": MoveData(
        type="フェアリー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "blocked_by_gold", "reflectable", "heal"],
    ),
    "ふるいたてる": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "ブレイブチャージ": MoveData(
        type="エスパー",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "へびにらみ": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "へんしん": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        flags=["unprotectable", "ignore_substitute", "blocked_by_gold", "non_encore"],
    ),
    "ぼうぎょしれい": MoveData(
        type="むし",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "ほえる": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        priority=-6,
        flags=["unprotectable", "ignore_substitute", "reflectable", "sound"],
    ),
    "ほおばる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "ほたるび": MoveData(
        type="むし",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=3, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "ほろびのうた": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "blocked_by_gold", "sound"],
    ),
    "まきびし": MoveData(
        type="じめん",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "reflectable"],
    ),
    "マジックルーム": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "まねっこ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "non_negoto", "call_move"],
    ),
    "まほうのこな": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "まもる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        priority=4,
        flags=["unprotectable", "ignore_substitute", "protect"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="まもる", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "まるくなる": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="まるくなる", target_spec="attacker:self", source_spec="attacker:self"),
            ),
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=1, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "みかづきのいのり": MoveData(
        type="エスパー",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "みかづきのまい": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "みがわり": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                v.みがわり_apply,
            )
        }
    ),
    "みきり": MoveData(
        type="かくとう",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        priority=4,
        flags=["unprotectable", "ignore_substitute", "protect"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="まもる", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "ミストフィールド": MoveData(
        type="フェアリー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "みずびたし": MoveData(
        type="みず",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "みちづれ": MoveData(
        type="ゴースト",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="みちづれ", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "ミラータイプ": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        flags=["ignore_substitute", "blocked_by_gold"],
    ),
    "ミルクのみ": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "heal"],
    ),
    "みをけずる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "めいそう": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "メロメロ": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        flags=["ignore_substitute", "blocked_by_gold", "reflectable"],
    ),
    "ものまね": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "non_encore", "non_negoto", "call_move"],
    ),
    "もりののろい": MoveData(
        type="くさ",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "やどりぎのタネ": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        power=0,
        accuracy=90,
        flags=["blocked_by_gold", "reflectable"],
    ),
    "ゆきげしき": MoveData(
        type="こおり",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "ゆびをふる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute", "non_negoto", "call_move"],
    ),
    "リサイクル": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "リフレクター": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
        }
    ),
    "リフレッシュ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "りゅうのまい": MoveData(
        type="ドラゴン",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "ロックオン": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        flags=["ignore_substitute"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.apply_volatile, volatile="ロックオン", target_spec="defender:self", source_spec="attacker:self", count=2),
            )
        }
    ),
    "ロックカット": MoveData(
        type="いわ",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=2, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "ワイドガード": MoveData(
        type="いわ",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        priority=3,
        flags=["unprotectable", "ignore_substitute"],
    ),
    "わたほうし": MoveData(
        type="くさ",
        category="変化",
        pp=40,
        power=0,
        accuracy=100,
        flags=["blocked_by_gold", "reflectable", "powder"],
    ),
    "わるだくみ": MoveData(
        type="あく",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=2, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "ワンダールーム": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        flags=["unprotectable", "ignore_substitute"]
    ),
    "あてみなげ": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=50,
        accuracy=100,
        priority=-1,
        flags=["contact"],
    ),
    "キングシールド": MoveData(
        type="はがね",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        priority=4,
        flags=["protect", "reflectable"],
        handlers={
            Event.ON_TRY_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="キングシールド", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "トラップシェル": MoveData(
        type="はがね",
        category="特殊",
        pp=5,
        power=150,
        accuracy=100,
        priority=-5,
        flags=["unprotectable"],
    ),
}


FLINCH_MOVES: dict[str, float] = {
    "３ぼんのや": 0.3,
    "アイアンヘッド": 0.3,
    "あくのはどう": 0.2,
    "いびき": 0.3,
    "いわなだれ": 0.3,
    "エアスラッシュ": 0.3,
    "おどろかす": 0.3,
    "かみつく": 0.3,
    "かみなりのキバ": 0.1,
    "こおりのキバ": 0.1,
    "ゴッドバード": 0.3,
    "しねんのずつき": 0.2,
    "じんつうりき": 0.1,
    "ずつき": 0.3,
    "たきのぼり": 0.2,
    "たつまき": 0.2,
    "ダブルパンツァー": 0.3,
    "つららおとし": 0.3,
    "ドラゴンダイブ": 0.2,
    "ニードルアーム": 0.3,
    "ねこだまし": 1.0,
    "ハートスタンプ": 0.3,
    "ハードローラー": 0.3,
    "はやてがえし": 1.0,
    "ひっさつまえば": 0.1,
    "ひょうざんおろし": 0.3,
    "びりびりちくちく": 0.3,
    "ふみつけ": 0.3,
    "ふわふわフォール": 0.3,
    "ホネこんぼう": 0.1,
    "ほのおのキバ": 0.1,
    "まわしげり": 0.3,
    "もえあがるいかり": 0.2,
}


def flinch_setup() -> None:
    """ひるみ付与技の共通ハンドラを追加する。"""
    for name, prob in FLINCH_MOVES.items():
        move = MOVES.get(name)
        if not move:
            continue

        flinch_handler = h.MoveHandler(
            partial(h.apply_flinch, prob=prob),
            subject_spec="attacker:self",
            log="never",
        )

        existing = move.handlers.get(Event.ON_HIT)
        if existing is None:
            move.handlers[Event.ON_HIT] = flinch_handler
        elif isinstance(existing, list):
            move.handlers[Event.ON_HIT] = [*existing, flinch_handler]
        else:
            move.handlers[Event.ON_HIT] = [existing, flinch_handler]


common_setup()
flinch_setup()
