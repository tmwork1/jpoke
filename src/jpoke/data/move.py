"""技データ定義モジュール。

Note:
    このモジュール内の技定義はMOVES辞書内で五十音順に配置されています。
"""
from functools import partial

from jpoke.enums import Event
from jpoke.handlers import common, move as h
from .models import MoveData


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
    for name, data in MOVES.items():
        data.name = name

        # 共通ハンドラを追加
        data.handlers[Event.ON_CONSUME_PP] = h.MoveHandler(
            h.consume_pp,
            subject_spec="attacker:self"
        )


MOVES: dict[str, MoveData] = {
    # -------------------------
    # 攻撃技
    # -------------------------
    "わるあがき": MoveData(
        type="ステラ",
        category="物理",
        pp=999,
        power=40,
        labels=["contact", "non_encore"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_hp, target_spec="attacker:self", r=-1/4, reason="self_cost"),
            )
        }
    ),
    "こんらん": MoveData(
        type="ステラ",
        category="物理",
        pp=999,
        power=40,
    ),
    "１０まんばりき": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=95,
        accuracy=95,
        labels=["contact"],
    ),
    "３ぼんのや": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,
        critical_rank=1,
        labels=["secondary_effect"],
    ),
    "ＤＤラリアット": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=85,
        accuracy=100,
        labels=["contact"],
    ),
    "Ｇのちから": MoveData(
        labels=["secondary_effect"],
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
        labels=["contact", "punch", "secondary_effect"],
        handlers={
             Event.ON_HIT: h.MoveHandler(
                 partial(common.modify_stat, stat="S", v=-1, target_spec="attacker:self", source_spec="attacker:self"),
             )
        }
    ),
    "アイアンテール": MoveData(
        type="はがね",
        category="物理",
        pp=15,
        power=100,
        accuracy=75,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, chance=0.3,
                        target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "アイアンヘッド": MoveData(
        type="はがね",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,
        labels=["contact", "secondary_effect"],
    ),
    "アイアンローラー": MoveData(
        type="はがね",
        category="物理",
        pp=5,
        power=130,
        accuracy=100,
        labels=["contact"],
    ),
    "アイススピナー": MoveData(
        type="こおり",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,
        labels=["contact"],
    ),
    "アイスハンマー": MoveData(
        labels=["secondary_effect"],
        type="こおり",
        category="物理",
        pp=10,
        power=100,
        accuracy=90,

        labels=["contact", "punch"],
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
        critical_rank=1,
        labels=["slash"],
    ),
    "アクアジェット": MoveData(
        type="みず",
        category="物理",
        pp=20,
        power=40,
        accuracy=100,
        priority=1,
        labels=["contact"],
    ),
    "アクアステップ": MoveData(
        labels=["secondary_effect"],
        type="みず",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,
        labels=["contact", "dance"],
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
        labels=["contact"],
    ),
    "アクアブレイク": MoveData(
        labels=["secondary_effect"],
        type="みず",
        category="物理",
        pp=10,
        power=85,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self", chance=0.2)
            )
        }
    ),
    "アクセルブレイク": MoveData(
        type="かくとう",
        category="物理",
        pp=5,
        power=100,
        accuracy=100,
        labels=["contact"],
    ),
    "アクセルロック": MoveData(
        type="いわ",
        category="物理",
        pp=20,
        power=40,
        accuracy=100,
        priority=1,
        labels=["contact"],
    ),
    "アクロバット": MoveData(
        type="ひこう",
        category="物理",
        pp=15,
        power=55,
        accuracy=100,
        labels=["contact"],
    ),
    "あなをほる": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                partial(v.charge_hidden_move, name="あなをほる"),
            )
        }
    ),
    "あばれる": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=120,
        accuracy=100,
        labels=["contact"],
        handlers={
        }
    ),
    "あんこくきょうだ": MoveData(
        type="あく",
        category="物理",
        pp=5,
        power=75,
        accuracy=100,
        critical_rank=3,
        labels=["contact", "punch"],
    ),
    "イカサマ": MoveData(
        type="あく",
        category="物理",
        pp=15,
        power=95,
        accuracy=100,
        labels=["contact"],
    ),
    "いかりのまえば": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        accuracy=90,
        labels=["contact"],
        handlers={
            Event.ON_MODIFY_DAMAGE: h.MoveHandler(
                h.HP_ratio_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "いじげんラッシュ": MoveData(
        labels=["secondary_effect"],
        type="あく",
        category="物理",
        pp=5,
        power=100,
        accuracy=100,
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
        labels=["secondary_effect"],
        type="かくとう",
        category="物理",
        pp=15,
        power=40,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self", chance=0.5)
            )
        }
    ),
    "いわなだれ": MoveData(
        labels=["secondary_effect"],
        type="いわ",
        category="物理",
        pp=10,
        power=75,
        accuracy=90,
    ),
    "インファイト": MoveData(
        labels=["secondary_effect"],
        type="かくとう",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,

        labels=["contact"],
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
        recoil_ratio=1/3,
        labels=["contact"],
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
        recoil_ratio=1/3,
        labels=["contact"],
    ),
    "ウッドホーン": MoveData(
        type="くさ",
        category="物理",
        pp=10,
        power=75,
        accuracy=100,

        labels=["contact"],
    ),
    "うっぷんばらし": MoveData(
        type="あく",
        category="物理",
        pp=5,
        power=75,
        accuracy=100,
        labels=["contact"],
    ),
    "えだづき": MoveData(
        type="くさ",
        category="物理",
        pp=40,
        power=40,
        accuracy=100,
        labels=["contact"],
    ),
    "オーラぐるま": MoveData(
        labels=["secondary_effect"],
        type="でんき",
        category="物理",
        pp=10,
        power=110,
        accuracy=100,
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(
                h.オーラぐるま_check_move_type,
                subject_spec="source:self",
            ),
        },
    ),
    "おどろかす": MoveData(
        labels=["secondary_effect"],
        type="ゴースト",
        category="物理",
        pp=15,
        power=30,
        accuracy=100,

        labels=["contact"],
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
        labels=["contact"],
    ),
    "カウンター": MoveData(
        type="かくとう",
        category="物理",
        pp=20,
        power=0,
        accuracy=100,
        priority=-5,
        labels=["contact"],
    ),
    "かえんぐるま": MoveData(
        labels=["secondary_effect"],
        type="ほのお",
        category="物理",
        pp=25,
        power=60,
        accuracy=100,

        labels=["contact"],
    ),
    "かえんボール": MoveData(
        labels=["secondary_effect"],
        type="ほのお",
        category="物理",
        pp=5,
        power=120,
        accuracy=90,

        labels=["bullet"],
    ),
    "かかとおとし": MoveData(
        labels=["secondary_effect"],
        type="かくとう",
        category="物理",
        pp=10,
        power=120,
        accuracy=90,

        labels=["contact"],
    ),
    "かげうち": MoveData(
        type="ゴースト",
        category="物理",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        labels=["contact"],
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
        labels=["contact"],
    ),
    "かみくだく": MoveData(
        labels=["secondary_effect"],
        type="あく",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,

        labels=["bite", "contact"],
    ),
    "かみつく": MoveData(
        labels=["secondary_effect"],
        type="あく",
        category="物理",
        pp=25,
        power=60,
        accuracy=100,

        labels=["bite", "contact"],
    ),
    "かみなりのキバ": MoveData(
        labels=["secondary_effect"],
        type="でんき",
        category="物理",
        pp=15,
        power=65,
        accuracy=95,

        labels=["contact"],
    ),
    "かみなりパンチ": MoveData(
        labels=["secondary_effect"],
        type="でんき",
        category="物理",
        pp=15,
        power=75,
        accuracy=100,

        labels=["contact", "punch"],
    ),
    "がむしゃら": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=0,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_MODIFY_DAMAGE: h.MoveHandler(
                h.がむしゃら_modify_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "からげんき": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=70,
        accuracy=100,
        labels=["contact"],
    ),
    "ガリョウテンセイ": MoveData(
        labels=["secondary_effect"],
        type="ひこう",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,

        labels=["contact"],
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
        labels=["contact"],
    ),
    "がんせきアックス": MoveData(
        type="いわ",
        category="物理",
        pp=15,
        power=65,
        accuracy=90,
        labels=["contact", "slash"],
    ),
    "がんせきふうじ": MoveData(
        labels=["secondary_effect"],
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
        labels=["bullet"],
    ),
    "きあいパンチ": MoveData(
        type="かくとう",
        category="物理",
        pp=20,
        power=150,
        accuracy=100,
        priority=-3,
        labels=["contact", "non_negoto", "punch"],
        handlers={
            Event.ON_CHECK_MOVE: h.MoveHandler(
                h.きあいパンチ_check_move,
                subject_spec="attacker:self",
            ),
        },
    ),
    "ギガインパクト": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=150,
        accuracy=90,
        labels=["contact"],
    ),
    "きしかいせい": MoveData(
        type="かくとう",
        category="物理",
        pp=15,
        power=1,
        accuracy=100,
        labels=["contact"],
    ),
    "きゅうけつ": MoveData(
        type="むし",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,
        labels=["contact"],
    ),
    "きょけんとつげき": MoveData(
        type="ドラゴン",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,
        labels=["contact"],
    ),
    "きょじゅうざん": MoveData(
        type="はがね",
        category="物理",
        pp=5,
        power=100,
        accuracy=100,
        labels=["contact", "slash"],
    ),
    "きょじゅうだん": MoveData(
        type="はがね",
        category="物理",
        pp=5,
        power=100,
        accuracy=100,
        labels=["contact"],
    ),
    "キラースピン": MoveData(
        labels=["secondary_effect"],
        type="どく",
        category="物理",
        pp=15,
        power=30,
        accuracy=100,

        labels=["contact"],
    ),
    "きりさく": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=70,
        accuracy=100,
        critical_rank=1,
        labels=["contact", "slash"],
    ),
    "クイックターン": MoveData(
        type="みず",
        category="物理",
        pp=20,
        power=60,
        accuracy=100,
        labels=["contact"],
    ),
    "くさわけ": MoveData(
        labels=["secondary_effect"],
        type="くさ",
        category="物理",
        pp=20,
        power=50,
        accuracy=100,

        labels=["contact"],
    ),
    "くちばしキャノン": MoveData(
        type="ひこう",
        category="物理",
        pp=15,
        power=100,
        accuracy=100,
        priority=-3,
        labels=["bullet", "non_negoto"],
    ),
    "くらいつく": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,
        labels=["bite", "contact"],
    ),
    "グラススライダー": MoveData(
        type="くさ",
        category="物理",
        pp=20,
        power=55,
        accuracy=100,
        priority=1,
        labels=["contact"],
    ),
    "クラブハンマー": MoveData(
        type="みず",
        category="物理",
        pp=10,
        power=100,
        accuracy=90,
        critical_rank=1,
        labels=["contact"],
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
        critical_rank=1,
        labels=["contact"],
    ),
    "クロスポイズン": MoveData(
        labels=["secondary_effect"],
        type="どく",
        category="物理",
        pp=20,
        power=70,
        accuracy=100,
        critical_rank=1,
        labels=["contact", "slash"],
    ),
    "げきりん": MoveData(
        type="ドラゴン",
        category="物理",
        pp=10,
        power=120,
        accuracy=100,
        labels=["contact"],
    ),
    "けたぐり": MoveData(
        type="かくとう",
        category="物理",
        pp=20,
        power=1,
        accuracy=100,
        labels=["contact"],
    ),
    "こうげきしれい": MoveData(
        type="むし",
        category="物理",
        pp=15,
        power=90,
        accuracy=100,
        critical_rank=1,
    ),
    "こうそくスピン": MoveData(
        labels=["secondary_effect"],
        type="ノーマル",
        category="物理",
        pp=40,
        power=50,
        accuracy=100,

        labels=["contact"],
    ),
    "ゴーストダイブ": MoveData(
        type="ゴースト",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,
        labels=["contact"],
    ),
    "こおりのキバ": MoveData(
        labels=["secondary_effect"],
        type="こおり",
        category="物理",
        pp=15,
        power=65,
        accuracy=95,

        labels=["contact"],
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
        labels=["secondary_effect"],
        type="ひこう",
        category="物理",
        pp=5,
        power=140,
        accuracy=90,
        critical_rank=1,
    ),
    "このは": MoveData(
        type="くさ",
        category="物理",
        pp=40,
        power=40,
        accuracy=100
    ),
    "コメットパンチ": MoveData(
        labels=["secondary_effect"],
        type="はがね",
        category="物理",
        pp=10,
        power=90,
        accuracy=90,
        labels=["contact", "punch"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=1, target_spec="attacker:self", source_spec="attacker:self", chance=0.2)
            )
        }
    ),
    "ころがる": MoveData(
        type="いわ",
        category="物理",
        pp=20,
        power=30,
        accuracy=90,
        labels=["contact"],
    ),
    "サイコカッター": MoveData(
        type="エスパー",
        category="物理",
        pp=20,
        power=70,
        accuracy=100,
        critical_rank=1,
        labels=["slash"],
    ),
    "サイコファング": MoveData(
        type="エスパー",
        category="物理",
        pp=10,
        power=85,
        accuracy=100,
        labels=["bite", "contact"],
    ),
    "サイコブレイド": MoveData(
        type="エスパー",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,
        labels=["contact"],
    ),
    "サンダーダイブ": MoveData(
        type="でんき",
        category="物理",
        pp=15,
        power=100,
        accuracy=95,
        labels=["minimize", "contact"],
    ),
    "ジェットパンチ": MoveData(
        type="みず",
        category="物理",
        pp=15,
        power=60,
        accuracy=100,
        priority=1,
        labels=["contact", "punch"],
    ),
    "シェルブレード": MoveData(
        labels=["secondary_effect"],
        type="みず",
        category="物理",
        pp=10,
        power=75,
        accuracy=95,
        labels=["contact", "slash"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self", chance=0.5)
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
        labels=["contact", "slash"],
    ),
    "じしん": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=100,
        accuracy=100
    ),
    "したでなめる": MoveData(
        labels=["secondary_effect"],
        type="ゴースト",
        category="物理",
        pp=30,
        power=30,
        accuracy=100,

        labels=["contact"],
    ),
    "じたばた": MoveData(
        type="ノーマル",
        category="物理",
        pp=15,
        power=1,
        accuracy=100,
        labels=["contact"],
    ),
    "じだんだ": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=75,
        accuracy=100,
        labels=["contact"],
    ),
    "しっぺがえし": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=50,
        accuracy=100,
        labels=["contact"],
    ),
    "じならし": MoveData(
        labels=["secondary_effect"],
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
        labels=["secondary_effect"],
        type="エスパー",
        category="物理",
        pp=15,
        power=80,
        accuracy=90,

        labels=["contact"],
    ),
    "じばく": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=200,
        accuracy=100,
        labels=["explosion"],
    ),
    "しめつける": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=15,
        accuracy=85,
        labels=["bind", "contact"],
    ),
    "ジャイロボール": MoveData(
        type="はがね",
        category="物理",
        pp=5,
        power=1,
        accuracy=100,
        labels=["bullet", "contact"],
    ),
    "シャドークロー": MoveData(
        type="ゴースト",
        category="物理",
        pp=15,
        power=70,
        accuracy=100,
        critical_rank=1,
        labels=["contact"],
    ),
    "シャドーダイブ": MoveData(
        type="ゴースト",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                partial(v.charge_hidden_move, name="シャドーダイブ"),
            )
        }
    ),
    "シャドーパンチ": MoveData(
        type="ゴースト",
        category="物理",
        pp=20,
        power=60,
        accuracy=0,
        labels=["contact", "punch"],
    ),
    "じゃれつく": MoveData(
        labels=["secondary_effect"],
        type="フェアリー",
        category="物理",
        pp=10,
        power=90,
        accuracy=90,

        labels=["contact"],
    ),
    "じわれ": MoveData(
        type="じめん",
        category="物理",
        pp=5,
        accuracy=30,
        labels=["ohko"],
        handlers={
            Event.ON_CHECK_IMMUNE: h.MoveHandler(
                h.ohko_check_immune,
                subject_spec="defender:self",
            ),
            Event.ON_MODIFY_DAMAGE: h.MoveHandler(
                h.ohko_modify_damage,
                subject_spec="attacker:self",
            ),
        }
    ),
    "しんそく": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=80,
        accuracy=100,
        priority=2,
        labels=["contact"],
    ),
    "スイープビンタ": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=25,
        accuracy=85,
        labels=["contact"],
    ),
    "すいりゅうれんだ": MoveData(
        type="みず",
        category="物理",
        pp=5,
        power=25,
        accuracy=100,
        critical_rank=3,
        labels=["contact", "punch"],
    ),
    "スケイルショット": MoveData(
        type="ドラゴン",
        category="物理",
        pp=20,
        power=25,
        accuracy=90,
    ),
    "ずつき": MoveData(
        labels=["secondary_effect"],
        type="ノーマル",
        category="物理",
        pp=15,
        power=70,
        accuracy=100,

        labels=["contact"],
    ),
    "すてみタックル": MoveData(
        type="ノーマル",
        category="物理",
        pp=15,
        power=120,
        accuracy=100,
        recoil_ratio=1/3,
        labels=["contact"],
    ),
    "ストーンエッジ": MoveData(
        type="いわ",
        category="物理",
        pp=5,
        power=100,
        accuracy=80,
        critical_rank=1,
    ),
    "すなじごく": MoveData(
        type="じめん",
        category="物理",
        pp=15,
        power=35,
        accuracy=85,
        labels=["bind"],
    ),
    "スパーク": MoveData(
        labels=["secondary_effect"],
        type="でんき",
        category="物理",
        pp=20,
        power=65,
        accuracy=100,

        labels=["contact"],
    ),
    "スマートホーン": MoveData(
        type="はがね",
        category="物理",
        pp=10,
        power=70,
        accuracy=0,
        labels=["contact"],
    ),
    "せいなるつるぎ": MoveData(
        type="かくとう",
        category="物理",
        pp=15,
        power=90,
        accuracy=100,
        labels=["contact", "slash"],
    ),
    "せいなるほのお": MoveData(
        labels=["secondary_effect"],
        type="ほのお",
        category="物理",
        pp=5,
        power=100,
        accuracy=95,

    ),
    "ソウルクラッシュ": MoveData(
        labels=["secondary_effect"],
        type="フェアリー",
        category="物理",
        pp=15,
        power=75,
        accuracy=100,
        labels=["contact"],
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
        labels=["contact", "slash"],
    ),
    "そらをとぶ": MoveData(
        type="ひこう",
        category="物理",
        pp=15,
        power=90,
        accuracy=95,
        labels=["contact"],
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                partial(v.charge_hidden_move, name="そらをとぶ"),
            )
        }
    ),
    "たいあたり": MoveData(
        type="ノーマル",
        category="物理",
        pp=35,
        power=40,
        accuracy=100,

        labels=["contact"],
    ),
    "だいばくはつ": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=250,
        accuracy=100,
        labels=["explosion"],
    ),
    "ダイビング": MoveData(
        type="みず",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                partial(v.charge_hidden_move, name="ダイビング"),
            )
        }
    ),
    "だいふんげき": MoveData(
        type="ほのお",
        category="物理",
        pp=10,
        power=120,
        accuracy=100,
    ),
    "ダイヤストーム": MoveData(
        labels=["secondary_effect"],
        type="いわ",
        category="物理",
        pp=5,
        power=100,
        accuracy=95,
    ),
    "たきのぼり": MoveData(
        labels=["secondary_effect"],
        type="みず",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,

        labels=["contact"],
    ),
    "ダストシュート": MoveData(
        labels=["secondary_effect"],
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
        labels=["contact"],
    ),
    "タネばくだん": MoveData(
        type="くさ",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,
        labels=["bullet"],
    ),
    "タネマシンガン": MoveData(
        type="くさ",
        category="物理",
        pp=30,
        power=25,
        accuracy=100,
        labels=["bullet"],
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        }
    ),
    "ダブルアタック": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=35,
        accuracy=90,
        labels=["contact"],
        multi_hit={
            "min": 2,
            "max": 2,
            "check_hit_each_time": False,
            "power_sequence": (),
        }
    ),
    "ダブルウイング": MoveData(
        type="ひこう",
        category="物理",
        pp=10,
        power=40,
        accuracy=90,
        labels=["contact"],
        multi_hit={
            "min": 2,
            "max": 2,
            "check_hit_each_time": False,
            "power_sequence": (),
        }
    ),
    "ダメおし": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=60,
        accuracy=100,
        labels=["contact"],
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
        labels=["contact"],
        handlers={
            Event.ON_MODIFY_DAMAGE: h.MoveHandler(
                h.level_fixed_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "ついばむ": MoveData(
        type="ひこう",
        category="物理",
        pp=20,
        power=60,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.ついばむ_berry_steal,
            )
        }
    ),
    "つけあがる": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=20,
        accuracy=100,
        labels=["contact"],
    ),
    "つじぎり": MoveData(
        type="あく",
        category="物理",
        pp=15,
        power=70,
        accuracy=100,
        critical_rank=1,
        labels=["contact", "slash"],
    ),
    "ツタこんぼう": MoveData(
        type="くさ",
        category="物理",
        pp=10,
        power=100,
        accuracy=100,
        critical_rank=1,
    ),
    "つつく": MoveData(
        type="ひこう",
        category="物理",
        pp=35,
        power=35,
        accuracy=100,
        labels=["contact"],
    ),
    "つっぱり": MoveData(
        type="かくとう",
        category="物理",
        pp=20,
        power=15,
        accuracy=100,
        labels=["contact"],
    ),
    "つのでつく": MoveData(
        type="ノーマル",
        category="物理",
        pp=25,
        power=65,
        accuracy=100,
        labels=["contact"],
    ),
    "つのドリル": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=0,
        accuracy=30,
        labels=["ohko", "contact"],
        handlers={
            Event.ON_CHECK_IMMUNE: h.MoveHandler(
                h.ohko_check_immune,
                subject_spec="defender:self",
            ),
            Event.ON_MODIFY_DAMAGE: h.MoveHandler(
                h.ohko_modify_damage,
                subject_spec="attacker:self",
            ),
        }
    ),
    "つばさでうつ": MoveData(
        type="ひこう",
        category="物理",
        pp=35,
        power=60,
        accuracy=100,
        labels=["contact"],
    ),
    "つばめがえし": MoveData(
        type="ひこう",
        category="物理",
        pp=20,
        power=60,
        accuracy=0,
        labels=["contact", "slash"],
    ),
    "つららおとし": MoveData(
        labels=["secondary_effect"],
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
    ),
    "つるのムチ": MoveData(
        type="くさ",
        category="物理",
        pp=25,
        power=45,
        accuracy=100,
        labels=["contact"],
    ),
    "であいがしら": MoveData(
        type="むし",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,
        priority=2,
        labels=["contact"],
    ),
    "デカハンマー": MoveData(
        type="はがね",
        category="物理",
        pp=5,
        power=160,
        accuracy=100,
    ),
    "でんこうせっか": MoveData(
        type="ノーマル",
        category="物理",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        labels=["contact"],
    ),
    "でんこうそうげき": MoveData(
        type="でんき",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,
        labels=["contact"],
    ),
    "どくづき": MoveData(
        labels=["secondary_effect"],
        type="どく",
        category="物理",
        pp=20,
        power=80,
        accuracy=100,

        labels=["contact"],
    ),
    "どくどくのキバ": MoveData(
        labels=["secondary_effect"],
        type="どく",
        category="物理",
        pp=15,
        power=50,
        accuracy=100,

        labels=["contact"],
    ),
    "どくばり": MoveData(
        labels=["secondary_effect"],
        type="どく",
        category="物理",
        pp=35,
        power=15,
        accuracy=100,
    ),
    "どくばりセンボン": MoveData(
        labels=["secondary_effect"],
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
        labels=["contact"],
    ),
    "ドゲザン": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=85,
        accuracy=0,
        labels=["contact", "slash"],
    ),
    "とっしん": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=90,
        accuracy=85,
        recoil_ratio=1/4,
        labels=["contact"],
    ),
    "とっておき": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=140,
        accuracy=100,
        labels=["contact"],
    ),
    "とどめばり": MoveData(
        type="むし",
        category="物理",
        pp=25,
        power=50,
        accuracy=100,
        labels=["contact"],
    ),
    "とびかかる": MoveData(
        labels=["secondary_effect"],
        type="むし",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "とびつく": MoveData(
        labels=["secondary_effect"],
        type="むし",
        category="物理",
        pp=20,
        power=50,
        accuracy=100,

        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "とびはねる": MoveData(
        labels=["secondary_effect"],
        type="ひこう",
        category="物理",
        pp=5,
        power=85,
        accuracy=85,

        labels=["contact"],
    ),
    "とびひざげり": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=130,
        accuracy=90,

        labels=["contact"],
    ),
    "ともえなげ": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=60,
        accuracy=90,
        priority=-6,
        labels=["contact"],
    ),
    "ドラゴンアロー": MoveData(
        type="ドラゴン",
        category="物理",
        pp=10,
        power=50,
        accuracy=100,
    ),
    "ドラゴンクロー": MoveData(
        type="ドラゴン",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,
        labels=["contact"],
    ),
    "ドラゴンダイブ": MoveData(
        labels=["secondary_effect"],
        type="ドラゴン",
        category="物理",
        pp=10,
        power=100,
        accuracy=75,
        labels=["minimize", "contact"],
    ),
    "ドラゴンテール": MoveData(
        type="ドラゴン",
        category="物理",
        pp=10,
        power=60,
        accuracy=90,
        priority=-6,
        labels=["contact"],
    ),
    "ドラゴンハンマー": MoveData(
        type="ドラゴン",
        category="物理",
        pp=15,
        power=90,
        accuracy=100,
        labels=["contact"],
    ),
    "ドラムアタック": MoveData(
        labels=["secondary_effect"],
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
        critical_rank=3,
    ),
    "トリプルアクセル": MoveData(
        type="こおり",
        category="物理",
        pp=10,
        power=20,
        accuracy=90,
        labels=["contact"],
        multi_hit={
            "min": 3,
            "max": 3,
            "check_hit_each_time": True,
            "power_sequence": (20, 40, 60),
        }
    ),
    "トリプルキック": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=10,
        accuracy=90,
        labels=["contact"],
        multi_hit={
            "min": 3,
            "max": 3,
            "check_hit_each_time": True,
            "power_sequence": (10, 20, 30),
        }
    ),
    "トリプルダイブ": MoveData(
        type="みず",
        category="物理",
        pp=10,
        power=30,
        accuracy=95,
        labels=["contact"],
        multi_hit={
            "min": 3,
            "max": 3,
            "check_hit_each_time": False,
            "power_sequence": (),
        }
    ),
    "ドリルくちばし": MoveData(
        type="ひこう",
        category="物理",
        pp=20,
        power=80,
        accuracy=100,
        labels=["contact"],
    ),
    "ドリルライナー": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=80,
        accuracy=95,
        critical_rank=1,
        labels=["contact"],
    ),
    "ドレインパンチ": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=75,
        accuracy=100,

        labels=["contact", "punch"],
    ),
    "トロピカルキック": MoveData(
        labels=["secondary_effect"],
        type="くさ",
        category="物理",
        pp=15,
        power=70,
        accuracy=100,

        labels=["contact"],
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
        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.どろぼう_steal_item,
            )
        }
    ),
    "とんぼがえり": MoveData(
        type="むし",
        category="物理",
        pp=20,
        power=70,
        accuracy=100,
        labels=["contact"],
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
    ),
    "にぎりつぶす": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=1,
        accuracy=100,
        labels=["contact"],
    ),
    "にどげり": MoveData(
        type="かくとう",
        category="物理",
        pp=30,
        power=30,
        accuracy=100,
        labels=["contact"],
        multi_hit={
            "min": 2,
            "max": 2,
            "check_hit_each_time": True,
            "power_sequence": (30, 30),
        }
    ),
    "ニトロチャージ": MoveData(
        labels=["secondary_effect"],
        type="ほのお",
        category="物理",
        pp=20,
        power=50,
        accuracy=100,

        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=1, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "ねこだまし": MoveData(
        labels=["secondary_effect"],
        type="ノーマル",
        category="物理",
        pp=10,
        power=40,
        accuracy=100,
        priority=3,
        labels=["contact"],
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
        labels=["contact", "slash"],
        multi_hit={
            "min": 10,
            "max": 10,
            "check_hit_each_time": True,
            "power_sequence": (),
        }
    ),
    "のしかかり": MoveData(
        labels=["secondary_effect"],
        type="ノーマル",
        category="物理",
        pp=15,
        power=85,
        accuracy=100,
        labels=["minimize", "contact"],
    ),
    "ハードプレス": MoveData(
        type="はがね",
        category="物理",
        pp=10,
        power=1,
        accuracy=100,
        labels=["contact"],
    ),
    "ハイパードリル": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=100,
        accuracy=100,
        labels=["contact"],
    ),
    "はいよるいちげき": MoveData(
        labels=["secondary_effect"],
        type="むし",
        category="物理",
        pp=10,
        power=70,
        accuracy=90,

        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "ばかぢから": MoveData(
        labels=["secondary_effect"],
        type="かくとう",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,

        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stats, stats={"A": -1, "B": -1}, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "はがねのつばさ": MoveData(
        labels=["secondary_effect"],
        type="はがね",
        category="物理",
        pp=25,
        power=70,
        accuracy=90,

        labels=["contact"],
    ),
    "ばくれつパンチ": MoveData(
        labels=["secondary_effect"],
        type="かくとう",
        category="物理",
        pp=5,
        power=100,
        accuracy=50,

        labels=["contact", "punch"],
    ),
    "ハサミギロチン": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=0,
        accuracy=30,
        labels=["ohko", "contact"],
        handlers={
            Event.ON_CHECK_IMMUNE: h.MoveHandler(
                h.ohko_check_immune,
                subject_spec="defender:self",
            ),
            Event.ON_MODIFY_DAMAGE: h.MoveHandler(
                h.ohko_modify_damage,
                subject_spec="attacker:self",
            ),
        }
    ),
    "はさむ": MoveData(
        type="ノーマル",
        category="物理",
        pp=30,
        power=55,
        accuracy=100,
        labels=["contact"],
    ),
    "はたきおとす": MoveData(
        type="あく",
        category="物理",
        pp=20,
        power=65,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                h.はたきおとす_power,
            ),
            Event.ON_HIT: h.MoveHandler(
                h.はたきおとす_remove_item,
            )
        }
    ),
    "はたく": MoveData(
        type="ノーマル",
        category="物理",
        pp=35,
        power=40,
        accuracy=100,
        labels=["contact"],
    ),
    "はっけい": MoveData(
        labels=["secondary_effect"],
        type="かくとう",
        category="物理",
        pp=10,
        power=60,
        accuracy=100,

        labels=["contact"],
    ),
    "はっぱカッター": MoveData(
        type="くさ",
        category="物理",
        pp=25,
        power=55,
        accuracy=95,
        critical_rank=1,
        labels=["slash"],
    ),
    "はなふぶき": MoveData(
        type="くさ",
        category="物理",
        pp=15,
        power=90,
        accuracy=100,
        labels=["wind"],
    ),
    "はやてがえし": MoveData(
        labels=["secondary_effect"],
        type="かくとう",
        category="物理",
        pp=15,
        power=65,
        accuracy=100,
        priority=3,
        labels=["contact"],
        handlers={
            Event.ON_CHECK_MOVE: h.MoveHandler(
                h.はやてがえし_check_move,
            ),
            Event.ON_HIT: h.MoveHandler(
                partial(common.apply_volatile, volatile="ひるみ", target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "バリアーラッシュ": MoveData(
        labels=["secondary_effect"],
        type="エスパー",
        category="物理",
        pp=10,
        power=70,
        accuracy=90,

        labels=["contact"],
    ),
    "バレットパンチ": MoveData(
        type="はがね",
        category="物理",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        labels=["contact", "punch"],
    ),
    "パワーウィップ": MoveData(
        type="くさ",
        category="物理",
        pp=10,
        power=120,
        accuracy=85,
        labels=["contact"],
    ),
    "パワフルエッジ": MoveData(
        type="いわ",
        category="物理",
        pp=5,
        power=95,
        accuracy=100,
        labels=["contact"],
    ),
    "ヒートスタンプ": MoveData(
        type="ほのお",
        category="物理",
        pp=10,
        power=1,
        accuracy=100,
        labels=["minimize", "contact"],
    ),
    "ひけん・ちえなみ": MoveData(
        type="あく",
        category="物理",
        pp=15,
        power=65,
        accuracy=90,
        labels=["contact"],
    ),
    "ひっかく": MoveData(
        type="ノーマル",
        category="物理",
        pp=35,
        power=40,
        accuracy=100,
        labels=["contact"],
    ),
    "ひょうざんおろし": MoveData(
        labels=["secondary_effect"],
        type="こおり",
        category="物理",
        pp=10,
        power=100,
        accuracy=85,
    ),
    "びりびりちくちく": MoveData(
        labels=["secondary_effect"],
        type="でんき",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,

        labels=["contact"],
    ),
    "ふいうち": MoveData(
        type="あく",
        category="物理",
        pp=5,
        power=70,
        accuracy=100,
        priority=1,
        labels=["contact"],
    ),
    "フェイタルクロー": MoveData(
        labels=["secondary_effect"],
        type="どく",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,

        labels=["contact"],
    ),
    "フェイント": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=30,
        accuracy=100,
        priority=2,
    ),
    "ふくろだたき": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=0,
        accuracy=100
    ),
    "ぶちかまし": MoveData(
        labels=["secondary_effect"],
        type="じめん",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,

        labels=["contact", "punch"],
    ),
    "ふみつけ": MoveData(
        labels=["secondary_effect"],
        type="ノーマル",
        category="物理",
        pp=20,
        power=65,
        accuracy=100,
        labels=["minimize", "contact"],
    ),
    "フライングプレス": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=100,
        accuracy=95,
        labels=["minimize", "contact"],
    ),
    "フリーズボルト": MoveData(
        labels=["secondary_effect"],
        type="こおり",
        category="物理",
        pp=5,
        power=140,
        accuracy=90,

    ),
    "ブリザードランス": MoveData(
        type="こおり",
        category="物理",
        pp=5,
        power=120,
        accuracy=100
    ),
    "フレアドライブ": MoveData(
        labels=["secondary_effect"],
        type="ほのお",
        category="物理",
        pp=15,
        power=120,
        accuracy=100,
        recoil_ratio=1/3,
        labels=["contact"],
    ),
    "ブレイククロー": MoveData(
        labels=["secondary_effect"],
        type="ノーマル",
        category="物理",
        pp=10,
        power=75,
        accuracy=95,

        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self", chance=0.5)
            )
        }
    ),
    "ブレイズキック": MoveData(
        labels=["secondary_effect"],
        type="ほのお",
        category="物理",
        pp=10,
        power=85,
        accuracy=90,
        critical_rank=1,
        labels=["contact"],
    ),
    "ブレイブバード": MoveData(
        type="ひこう",
        category="物理",
        pp=15,
        power=120,
        accuracy=100,
        recoil_ratio=1/3,
        labels=["contact"],
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
        labels=["contact", "punch"],
    ),
    "ぶんまわす": MoveData(
        type="あく",
        category="物理",
        pp=20,
        power=60,
        accuracy=100,
        labels=["contact"],
    ),
    "ヘビーボンバー": MoveData(
        type="はがね",
        category="物理",
        pp=10,
        power=1,
        accuracy=100,
        labels=["minimize", "contact"],
    ),
    "ホイールスピン": MoveData(
        labels=["secondary_effect"],
        type="はがね",
        category="物理",
        pp=5,
        power=100,
        accuracy=100,

        labels=["contact"],
    ),
    "ポイズンテール": MoveData(
        labels=["secondary_effect"],
        type="どく",
        category="物理",
        pp=25,
        power=50,
        accuracy=100,
        critical_rank=1,
        labels=["contact"],
    ),
    "ほうふく": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=0,
        accuracy=100,
        labels=["contact"],
    ),
    "ボーンラッシュ": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=25,
        accuracy=90,
    ),
    "ほしがる": MoveData(
        type="ノーマル",
        category="物理",
        pp=25,
        power=60,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.どろぼう_steal_item,
            )
        }
    ),
    "ほっぺすりすり": MoveData(
        labels=["secondary_effect"],
        type="でんき",
        category="物理",
        pp=20,
        power=20,
        accuracy=100,

        labels=["contact"],
    ),
    "ボディプレス": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,
        labels=["contact"],
    ),
    "ほのおのキバ": MoveData(
        labels=["secondary_effect"],
        type="ほのお",
        category="物理",
        pp=15,
        power=65,
        accuracy=95,

        labels=["contact"],
    ),
    "ほのおのパンチ": MoveData(
        labels=["secondary_effect"],
        type="ほのお",
        category="物理",
        pp=15,
        power=75,
        accuracy=100,

        labels=["contact", "punch"],
    ),
    "ほのおのムチ": MoveData(
        labels=["secondary_effect"],
        type="ほのお",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,

        labels=["contact"],
    ),
    "ポルターガイスト": MoveData(
        type="ゴースト",
        category="物理",
        pp=5,
        power=110,
        accuracy=90
    ),
    "ボルテッカー": MoveData(
        labels=["secondary_effect"],
        type="でんき",
        category="物理",
        pp=15,
        power=120,
        accuracy=100,
        recoil_ratio=1/3,
        labels=["contact"],
    ),
    "まきつく": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=15,
        accuracy=90,
        labels=["bind", "contact"],
    ),
    "マッハパンチ": MoveData(
        type="かくとう",
        category="物理",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        labels=["contact", "punch"],
    ),
    "ミサイルばり": MoveData(
        type="むし",
        category="物理",
        pp=20,
        power=25,
        accuracy=95,
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        }
    ),
    "みだれづき": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=15,
        accuracy=85,
        labels=["contact"],
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        }
    ),
    "みだれひっかき": MoveData(
        type="ノーマル",
        category="物理",
        pp=15,
        power=18,
        accuracy=80,
        labels=["contact"],
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        }
    ),
    "みねうち": MoveData(
        type="ノーマル",
        category="物理",
        pp=40,
        power=40,
        accuracy=100,
        labels=["contact"],
    ),
    "むしくい": MoveData(
        type="むし",
        category="物理",
        pp=20,
        power=60,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.ついばむ_berry_steal,
            )
        }
    ),
    "むねんのつるぎ": MoveData(
        type="ほのお",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,

        labels=["contact", "slash"],
    ),
    "メガトンキック": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=120,
        accuracy=75,
        labels=["contact"],
    ),
    "メガトンパンチ": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=80,
        accuracy=85,
        labels=["contact", "punch"],
    ),
    "メガホーン": MoveData(
        type="むし",
        category="物理",
        pp=10,
        power=120,
        accuracy=85,
        labels=["contact"],
    ),
    "メタルクロー": MoveData(
        labels=["secondary_effect"],
        type="はがね",
        category="物理",
        pp=35,
        power=50,
        accuracy=95,

        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=1, target_spec="attacker:self", source_spec="attacker:self", chance=0.1)
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
    ),
    "もろはのずつき": MoveData(
        type="いわ",
        category="物理",
        pp=5,
        power=150,
        accuracy=80,

        labels=["contact"],
    ),
    "やけっぱち": MoveData(
        type="ほのお",
        category="物理",
        pp=10,
        power=75,
        accuracy=100,
        labels=["contact"],
    ),
    "ゆきなだれ": MoveData(
        type="こおり",
        category="物理",
        pp=10,
        power=60,
        accuracy=100,
        priority=-4,
        labels=["contact"],
    ),
    "らいげき": MoveData(
        labels=["secondary_effect"],
        type="でんき",
        category="物理",
        pp=5,
        power=130,
        accuracy=85,

        labels=["contact"],
    ),
    "らいめいげり": MoveData(
        labels=["secondary_effect"],
        type="かくとう",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,

        labels=["contact"],
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
        critical_rank=1,
        labels=["contact", "slash"],
    ),
    "レイジングブル": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,
        labels=["contact"],
    ),
    "れいとうパンチ": MoveData(
        labels=["secondary_effect"],
        type="こおり",
        category="物理",
        pp=15,
        power=75,
        accuracy=100,

        labels=["contact", "punch"],
    ),
    "れんぞくぎり": MoveData(
        type="むし",
        category="物理",
        pp=20,
        power=40,
        accuracy=95,
        labels=["contact", "slash"],
    ),
    "ローキック": MoveData(
        labels=["secondary_effect"],
        type="かくとう",
        category="物理",
        pp=20,
        power=65,
        accuracy=100,

        labels=["contact"],
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
        labels=["bullet"],
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        }
    ),
    "ワイドブレイカー": MoveData(
        labels=["secondary_effect"],
        type="ドラゴン",
        category="物理",
        pp=15,
        power=60,
        accuracy=100,

        labels=["contact"],
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
        recoil_ratio=1/4,
        labels=["contact"],
    ),
    "１０まんボルト": MoveData(
        labels=["secondary_effect"],
        type="でんき",
        category="特殊",
        pp=15,
        power=90,
        accuracy=100
    ),
    "アーマーキャノン": MoveData(
        labels=["secondary_effect"],
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
        critical_rank=1,
    ),
    "あくのはどう": MoveData(
        labels=["secondary_effect"],
        type="あく",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,

        labels=["pulse"],
    ),
    "アシストパワー": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=20,
        accuracy=100
    ),
    "アシッドボム": MoveData(
        labels=["secondary_effect"],
        type="どく",
        category="特殊",
        pp=20,
        power=40,
        accuracy=100,

        labels=["bullet"],
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
    ),
    "いてつくしせん": MoveData(
        labels=["secondary_effect"],
        type="エスパー",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-1, target_spec="defender:self", source_spec="attacker:self", chance=0.1)
            )
        }
    ),
    "イナズマドライブ": MoveData(
        type="でんき",
        category="特殊",
        pp=5,
        power=100,
        accuracy=100,
        labels=["contact"],
    ),
    "いにしえのうた": MoveData(
        labels=["secondary_effect"],
        type="ノーマル",
        category="特殊",
        pp=10,
        power=75,
        accuracy=100,

        labels=["sound"],
    ),
    "いのちがけ": MoveData(
        type="かくとう",
        category="特殊",
        pp=5,
        power=0,
        accuracy=100,
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                h.いのちがけ_pay_hp,
                subject_spec="attacker:self",
            ),
            Event.ON_MODIFY_DAMAGE: h.MoveHandler(
                h.いのちがけ_modify_damage,
                subject_spec="attacker:self",
            ),
        }
    ),
    "いびき": MoveData(
        labels=["secondary_effect"],
        type="ノーマル",
        category="特殊",
        pp=15,
        power=50,
        accuracy=100,

        labels=["sound"],
    ),
    "ウェザーボール": MoveData(
        type="ノーマル",
        category="特殊",
        pp=10,
        power=50,
        accuracy=100,
        labels=["bullet"],
    ),
    "うずしお": MoveData(
        type="みず",
        category="特殊",
        pp=15,
        power=35,
        accuracy=85,
        labels=["bind"],
    ),
    "うたかたのアリア": MoveData(
        type="みず",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,
        labels=["sound"],
    ),
    "うらみつらみ": MoveData(
        labels=["secondary_effect"],
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
        critical_rank=1,
        labels=["slash", "wind"],
    ),
    "エアスラッシュ": MoveData(
        labels=["secondary_effect"],
        type="ひこう",
        category="特殊",
        pp=15,
        power=75,
        accuracy=95,

        labels=["slash"],
    ),
    "エアロブラスト": MoveData(
        type="ひこう",
        category="特殊",
        pp=5,
        power=100,
        accuracy=95,
        critical_rank=1,
        labels=["wind"],
    ),
    "エコーボイス": MoveData(
        type="ノーマル",
        category="特殊",
        pp=15,
        power=40,
        accuracy=100,
        labels=["sound"],
    ),
    "エナジーボール": MoveData(
        labels=["secondary_effect"],
        type="くさ",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        labels=["bullet"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-1, target_spec="defender:self", source_spec="attacker:self", chance=0.1)
            )
        }
    ),
    "エレキネット": MoveData(
        labels=["secondary_effect"],
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
        labels=["bullet"],
    ),
    "エレクトロビーム": MoveData(
        type="でんき",
        category="特殊",
        pp=10,
        power=130,
        accuracy=100,
    ),
    "オーバードライブ": MoveData(
        type="でんき",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,
        labels=["sound"],
    ),
    "オーバーヒート": MoveData(
        labels=["secondary_effect"],
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
        labels=["secondary_effect"],
        type="エスパー",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,
        critical_rank=1,
    ),
    "オーロラビーム": MoveData(
        labels=["secondary_effect"],
        type="こおり",
        category="特殊",
        pp=20,
        power=65,
        accuracy=100,
    ),
    "かえんほうしゃ": MoveData(
        labels=["secondary_effect"],
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
        labels=["wind"],
    ),
    "カタストロフィ": MoveData(
        type="あく",
        category="特殊",
        pp=10,
        power=0,
        accuracy=90,
        handlers={
            Event.ON_MODIFY_DAMAGE: h.MoveHandler(
                h.HP_ratio_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "かふんだんご": MoveData(
        type="むし",
        category="特殊",
        pp=15,
        power=90,
        accuracy=100,
        labels=["bullet"],
    ),
    "かみなり": MoveData(
        labels=["secondary_effect"],
        type="でんき",
        category="特殊",
        pp=10,
        power=110,
        accuracy=70,

        handlers={
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
                h.かみなり_accuracy,
                subject_spec="attacker:self"
            )
        }
    ),
    "かみなりあらし": MoveData(
        labels=["secondary_effect"],
        type="でんき",
        category="特殊",
        pp=10,
        power=100,
        accuracy=80,

        labels=["wind"],
    ),
    "きあいだま": MoveData(
        labels=["secondary_effect"],
        type="かくとう",
        category="特殊",
        pp=5,
        power=120,
        accuracy=70,

        labels=["bullet"],
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
        labels=["contact"],
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
        labels=["non_negoto"],
    ),
    "げんしのちから": MoveData(
        labels=["secondary_effect"],
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
        critical_rank=3,
    ),
    "コールドフレア": MoveData(
        labels=["secondary_effect"],
        type="こおり",
        category="特殊",
        pp=5,
        power=140,
        accuracy=90,

    ),
    "ゴールドラッシュ": MoveData(
        labels=["secondary_effect"],
        type="はがね",
        category="特殊",
        pp=5,
        power=120,
        accuracy=100,
    ),
    "こがらしあらし": MoveData(
        labels=["secondary_effect"],
        type="ひこう",
        category="特殊",
        pp=10,
        power=100,
        accuracy=80,

        labels=["wind"],
    ),
    "こごえるかぜ": MoveData(
        labels=["secondary_effect"],
        type="こおり",
        category="特殊",
        pp=15,
        power=55,
        accuracy=95,

        labels=["wind"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-1, target_spec="defender:self", source_spec="attacker:self")
            )
        }
    ),
    "こごえるせかい": MoveData(
        labels=["secondary_effect"],
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
        labels=["secondary_effect"],
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
        labels=["pulse"],
    ),
    "サイケこうせん": MoveData(
        labels=["secondary_effect"],
        type="エスパー",
        category="特殊",
        pp=20,
        power=65,
        accuracy=100,
    ),
    "サイコキネシス": MoveData(
        labels=["secondary_effect"],
        type="エスパー",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-1, target_spec="defender:self", source_spec="attacker:self", chance=0.1)
            )
        }
    ),
    "サイコショック": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,
    ),
    "サイコノイズ": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=75,
        accuracy=100,
        labels=["sound"],
    ),
    "サイコブースト": MoveData(
        labels=["secondary_effect"],
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
        labels=["non_negoto", "sound"],
        handlers={
            Event.ON_CHECK_MOVE: h.MoveHandler(
                v.さわぐ_on_apply,
            )
        }
    ),
    "サンダープリズン": MoveData(
        type="でんき",
        category="特殊",
        pp=15,
        power=80,
        accuracy=90,
        labels=["bind"],
    ),
    "シードフレア": MoveData(
        labels=["secondary_effect"],
        type="くさ",
        category="特殊",
        pp=5,
        power=120,
        accuracy=85,
    ),
    "シェルアームズ": MoveData(
        labels=["secondary_effect"],
        type="どく",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        labels=["contact"],
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
        labels=["secondary_effect"],
        type="くさ",
        category="特殊",
        pp=15,
        power=80,
        accuracy=90,

    ),
    "シャドーボール": MoveData(
        labels=["secondary_effect"],
        type="ゴースト",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,

        labels=["bullet"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-1, target_spec="defender:self", source_spec="attacker:self", chance=0.2)
            )
        }
    ),
    "シャドーレイ": MoveData(
        type="ゴースト",
        category="特殊",
        pp=5,
        power=100,
        accuracy=100,
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
        labels=["secondary_effect"],
        type="エスパー",
        category="特殊",
        pp=20,
        power=80,
        accuracy=100,
    ),
    "しんぴのちから": MoveData(
        labels=["secondary_effect"],
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
        labels=["slash"],
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
        labels=["secondary_effect"],
        type="ドラゴン",
        category="特殊",
        pp=5,
        power=110,
        accuracy=100,

        labels=["sound"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="attacker:self", source_spec="attacker:self")
            )
        }
    ),
    "スチームバースト": MoveData(
        labels=["secondary_effect"],
        type="みず",
        category="特殊",
        pp=5,
        power=110,
        accuracy=95,

    ),
    "スピードスター": MoveData(
        type="ノーマル",
        category="特殊",
        pp=20,
        power=60,
        accuracy=0
    ),
    "スモッグ": MoveData(
        labels=["secondary_effect"],
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
        labels=["ohko"],
        handlers={
            Event.ON_CHECK_IMMUNE: h.MoveHandler(
                h.ohko_check_immune,
                subject_spec="defender:self",
            ),
            Event.ON_MODIFY_DAMAGE: h.MoveHandler(
                h.ohko_modify_damage,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ソーラービーム": MoveData(
        type="くさ",
        category="特殊",
        pp=10,
        power=120,
        accuracy=100,
    ),
    "だいちのちから": MoveData(
        labels=["secondary_effect"],
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
        labels=["pulse"],
    ),
    "ダイマックスほう": MoveData(
        type="ドラゴン",
        category="特殊",
        pp=5,
        power=100,
        accuracy=100,
        labels=["non_encore", "non_negoto"],
    ),
    "だいもんじ": MoveData(
        labels=["secondary_effect"],
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
    ),
    "だくりゅう": MoveData(
        labels=["secondary_effect"],
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
        labels=["secondary_effect"],
        type="ドラゴン",
        category="特殊",
        pp=20,
        power=40,
        accuracy=100,

        labels=["wind"],
    ),
    "チャージビーム": MoveData(
        labels=["secondary_effect"],
        type="でんき",
        category="特殊",
        pp=10,
        power=50,
        accuracy=90,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=1, target_spec="attacker:self", source_spec="attacker:self", chance=0.7)
            )
        }
    ),
    "チャームボイス": MoveData(
        type="フェアリー",
        category="特殊",
        pp=15,
        power=40,
        accuracy=0,
        labels=["sound"],
    ),
    "ツインビーム": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=40,
        accuracy=100,
        multi_hit={
            "min": 2,
            "max": 2,
            "check_hit_each_time": False,
            "power_sequence": (),
        }
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
    ),
    "テラバースト": MoveData(
        type="ノーマル",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(
                h.テラバースト_check_move_type,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_MOVE_CATEGORY: h.MoveHandler(
                h.テラバースト_check_move_category,
                subject_spec="source:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                h.テラバースト_stellar_power,
                subject_spec="attacker:self",
            ),
            Event.ON_HIT: h.MoveHandler(
                h.テラバースト_stellar_stat_drop,
                subject_spec="attacker:self",
            ),
        }
    ),
    "でんきショック": MoveData(
        labels=["secondary_effect"],
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
        labels=["secondary_effect"],
        type="でんき",
        category="特殊",
        pp=5,
        power=120,
        accuracy=50,
        labels=["bullet"],
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
    ),
    "トライアタック": MoveData(
        labels=["secondary_effect"],
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

        labels=["contact"],
    ),
    "どろかけ": MoveData(
        labels=["secondary_effect"],
        type="じめん",
        category="特殊",
        pp=10,
        power=20,
        accuracy=100,
    ),
    "ナイトバースト": MoveData(
        labels=["secondary_effect"],
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
        accuracy=100,
        handlers={
            Event.ON_MODIFY_DAMAGE: h.MoveHandler(
                h.level_fixed_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "なみのり": MoveData(
        type="みず",
        category="特殊",
        pp=15,
        power=90,
        accuracy=100
    ),
    "ねっさのあらし": MoveData(
        labels=["secondary_effect"],
        type="じめん",
        category="特殊",
        pp=10,
        power=100,
        accuracy=80,

        labels=["wind"],
    ),
    "ねっさのだいち": MoveData(
        labels=["secondary_effect"],
        type="じめん",
        category="特殊",
        pp=10,
        power=70,
        accuracy=100,

    ),
    "ねっとう": MoveData(
        labels=["secondary_effect"],
        type="みず",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,

    ),
    "ねっぷう": MoveData(
        labels=["secondary_effect"],
        type="ほのお",
        category="特殊",
        pp=10,
        power=95,
        accuracy=90,
        labels=["wind"],
    ),
    "ねらいうち": MoveData(
        type="みず",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,
        critical_rank=1,
    ),
    "ねんりき": MoveData(
        labels=["secondary_effect"],
        type="エスパー",
        category="特殊",
        pp=25,
        power=50,
        accuracy=100,
    ),
    "バークアウト": MoveData(
        labels=["secondary_effect"],
        type="あく",
        category="特殊",
        pp=15,
        power=55,
        accuracy=95,

        labels=["sound"],
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
    ),
    "ハイドロカノン": MoveData(
        type="みず",
        category="特殊",
        pp=5,
        power=150,
        accuracy=90,
    ),
    "ハイドロスチーム": MoveData(
        type="みず",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,
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
        labels=["sound"],
    ),
    "はかいこうせん": MoveData(
        type="ノーマル",
        category="特殊",
        pp=5,
        power=150,
        accuracy=90,
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
        labels=["sound"],
    ),
    "はどうだん": MoveData(
        type="かくとう",
        category="特殊",
        pp=20,
        power=80,
        accuracy=0,
        labels=["bullet", "pulse"],
    ),
    "はなびらのまい": MoveData(
        type="くさ",
        category="特殊",
        pp=10,
        power=120,
        accuracy=100,
        labels=["contact", "dance"],
    ),
    "バブルこうせん": MoveData(
        labels=["secondary_effect"],
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
        labels=["secondary_effect"],
        type="フェアリー",
        category="特殊",
        pp=5,
        power=100,
        accuracy=80,

        labels=["wind"],
    ),
    "パワージェム": MoveData(
        type="いわ",
        category="特殊",
        pp=20,
        power=80,
        accuracy=100
    ),
    "ひのこ": MoveData(
        labels=["secondary_effect"],
        type="ほのお",
        category="特殊",
        pp=25,
        power=40,
        accuracy=100,
    ),
    "ひゃっきやこう": MoveData(
        labels=["secondary_effect"],
        type="ゴースト",
        category="特殊",
        pp=15,
        power=60,
        accuracy=100,
    ),
    "ひやみず": MoveData(
        labels=["secondary_effect"],
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
    ),
    "ぶきみなじゅもん": MoveData(
        type="エスパー",
        category="特殊",
        pp=5,
        power=80,
        accuracy=100,
        labels=["sound"],
    ),
    "ふぶき": MoveData(
        labels=["secondary_effect"],
        type="こおり",
        category="特殊",
        pp=5,
        power=110,
        accuracy=70,
        labels=["wind"],
        handlers={
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
                h.ふぶき_accuracy,
                subject_spec="attacker:self"
            )
        }
    ),
    "ブラストバーン": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=150,
        accuracy=90,
    ),
    "ブラッドムーン": MoveData(
        type="ノーマル",
        category="特殊",
        pp=5,
        power=140,
        accuracy=100,
    ),
    "フリーズドライ": MoveData(
        labels=["secondary_effect"],
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
    ),
    "フルールカノン": MoveData(
        labels=["secondary_effect"],
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
        labels=["secondary_effect"],
        type="ほのお",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,

        labels=["sound"],
    ),
    "ふんえん": MoveData(
        labels=["secondary_effect"],
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
    "ふしょくガス": MoveData(
        type="どく",
        category="変化",
        pp=40,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.ふしょくガス_remove_item,
            )
        }
    ),
    "ヘドロウェーブ": MoveData(
        labels=["secondary_effect"],
        type="どく",
        category="特殊",
        pp=10,
        power=95,
        accuracy=100,
    ),
    "ヘドロこうげき": MoveData(
        labels=["secondary_effect"],
        type="どく",
        category="特殊",
        pp=20,
        power=65,
        accuracy=100,
    ),
    "ヘドロばくだん": MoveData(
        labels=["secondary_effect"],
        type="どく",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        labels=["bullet"],
    ),
    "ベノムショック": MoveData(
        type="どく",
        category="特殊",
        pp=10,
        power=65,
        accuracy=100
    ),
    "ほうでん": MoveData(
        labels=["secondary_effect"],
        type="でんき",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,
    ),
    "ぼうふう": MoveData(
        labels=["secondary_effect"],
        type="ひこう",
        category="特殊",
        pp=10,
        power=110,
        accuracy=70,
        labels=["wind"],
        handlers={
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
                h.ぼうふう_accuracy,
                subject_spec="attacker:self"
            )
        }
    ),
    "ほのおのうず": MoveData(
        type="ほのお",
        category="特殊",
        pp=15,
        power=35,
        accuracy=85,
        labels=["bind"],
    ),
    "ほのおのちかい": MoveData(
        type="ほのお",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100
    ),
    "ほのおのまい": MoveData(
        labels=["secondary_effect"],
        type="ほのお",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,
        labels=["dance"],
    ),
    "ボルトチェンジ": MoveData(
        type="でんき",
        category="特殊",
        pp=20,
        power=70,
        accuracy=100,
    ),
    "マグマストーム": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=100,
        accuracy=75,
        labels=["bind"],
    ),
    "マジカルシャイン": MoveData(
        type="フェアリー",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100
    ),
    "マジカルフレイム": MoveData(
        labels=["secondary_effect"],
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
        labels=["secondary_effect"],
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
        labels=["bind", "contact"],
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
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        }
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
        labels=["explosion"],
    ),
    "ミストボール": MoveData(
        labels=["secondary_effect"],
        type="エスパー",
        category="特殊",
        pp=5,
        power=95,
        accuracy=100,

        labels=["bullet"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=-1, target_spec="defender:self", source_spec="attacker:self", chance=0.5)
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
        labels=["secondary_effect"],
        type="みず",
        category="特殊",
        pp=20,
        power=60,
        accuracy=100,

        labels=["pulse"],
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
        labels=["sound"],
    ),
    "ムーンフォース": MoveData(
        labels=["secondary_effect"],
        type="フェアリー",
        category="特殊",
        pp=15,
        power=95,
        accuracy=100,
    ),
    "むしのさざめき": MoveData(
        labels=["secondary_effect"],
        type="むし",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        labels=["sound"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-1, target_spec="defender:self", source_spec="attacker:self", chance=0.1)
            )
        }
    ),
    "むしのていこう": MoveData(
        labels=["secondary_effect"],
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
        accuracy=100,
        labels=["dance"],
    ),
    "メテオビーム": MoveData(
        type="いわ",
        category="特殊",
        pp=10,
        power=120,
        accuracy=90,
    ),
    "もえあがるいかり": MoveData(
        labels=["secondary_effect"],
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
        accuracy=100,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.やきつくす_remove_berry,
            )
        }
    ),
    "ゆめくい": MoveData(
        type="エスパー",
        category="特殊",
        pp=15,
        power=100,
        accuracy=100,
    ),
    "ようかいえき": MoveData(
        labels=["secondary_effect"],
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
        labels=["wind"],
    ),
    "ライジングボルト": MoveData(
        type="でんき",
        category="特殊",
        pp=20,
        power=70,
        accuracy=100
    ),
    "ラスターカノン": MoveData(
        labels=["secondary_effect"],
        type="はがね",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-1, target_spec="defender:self", source_spec="attacker:self", chance=0.1)
            )
        }
    ),
    "ラスターパージ": MoveData(
        labels=["secondary_effect"],
        type="エスパー",
        category="特殊",
        pp=5,
        power=95,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-1, target_spec="defender:self", source_spec="attacker:self", chance=0.5)
            )
        }
    ),
    "リーフストーム": MoveData(
        labels=["secondary_effect"],
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
        labels=["secondary_effect"],
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
        labels=["secondary_effect"],
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
        labels=["pulse"],
    ),
    "りんごさん": MoveData(
        labels=["secondary_effect"],
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
        labels=["sound"],
    ),
    "ルミナコリジョン": MoveData(
        labels=["secondary_effect"],
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
        labels=["secondary_effect"],
        type="こおり",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,
    ),
    "れんごく": MoveData(
        labels=["secondary_effect"],
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
        labels=["secondary_effect"],
        type="フェアリー",
        category="特殊",
        pp=10,
        power=90,
        accuracy=95,
    ),
    # -------------------------
    # 変化技
    # -------------------------
    "アクアリング": MoveData(
        type="みず",
        category="変化",
        pp=20,
        accuracy=0,
    ),
    "あくび": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "あくまのキッス": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=75,
    ),
    "あさのひざし": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        accuracy=0,
        labels=["heal"],
    ),
    "あまいかおり": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="EVA", v=-2, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "あまえる": MoveData(
        type="フェアリー",
        category="変化",
        pp=20,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=-2, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "あまごい": MoveData(
        type="みず",
        category="変化",
        pp=5,
        accuracy=0,
        target="field",
    ),
    "あやしいひかり": MoveData(
        type="ゴースト",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "アロマセラピー": MoveData(
        type="くさ",
        category="変化",
        pp=5,
        accuracy=0,
    ),
    "アロマミスト": MoveData(
        type="フェアリー",
        category="変化",
        pp=20,
        accuracy=100,
    ),
    "アンコール": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        accuracy=100,
        labels=["non_encore"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.apply_volatile, volatile="アンコール", target_spec="defender:self", source_spec="attacker:self", count=3),
            )
        }
    ),
    "いえき": MoveData(
        type="どく",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "いかりのこな": MoveData(
        type="むし",
        category="変化",
        pp=20,
        accuracy=0,
        priority=2,
    ),
    "いたみわけ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=0,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.いたみわけ_equalize_hp,
            )
        }
    ),
    "いちゃもん": MoveData(
        type="あく",
        category="変化",
        pp=15,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.apply_volatile, volatile="いちゃもん", target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "いとをはく": MoveData(
        type="むし",
        category="変化",
        pp=40,
        accuracy=95,
    ),
    "いのちのしずく": MoveData(
        type="みず",
        category="変化",
        pp=10,
        accuracy=0,
        labels=["heal"],
    ),
    "いばる": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        accuracy=85,
    ),
    "いやしのすず": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        accuracy=0,
        labels=["sound"],
    ),
    "いやしのねがい": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=0,
        labels=["heal"],
    ),
    "いやしのはどう": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=0,
        labels=["heal"],
    ),
    "いやなおと": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        accuracy=85,
        labels=["sound"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-2, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "うそなき": MoveData(
        type="あく",
        category="変化",
        pp=20,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-2, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "うたう": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        accuracy=55,
        labels=["sound"],
    ),
    "うつしえ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "うらみ": MoveData(
        type="ゴースト",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "エレキフィールド": MoveData(
        type="でんき",
        category="変化",
        pp=10,
        accuracy=0,
        target="field",
    ),
    "えんまく": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="ACC", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "おいかぜ": MoveData(
        type="ひこう",
        category="変化",
        pp=15,
        accuracy=0,
        target="field",
        labels=["wind"],
    ),
    "おいわい": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        accuracy=0,
        labels=["non_negoto"],
    ),
    "オーロラベール": MoveData(
        type="こおり",
        category="変化",
        pp=20,
        accuracy=0,
        target="field",
    ),
    "おかたづけ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "おきみやげ": MoveData(
        type="あく",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "おさきにどうぞ": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        accuracy=0,
    ),
    "おたけび": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=100,
        labels=["sound"],
    ),
    "おだてる": MoveData(
        type="あく",
        category="変化",
        pp=15,
        accuracy=100,
    ),
    "おちゃかい": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "おにび": MoveData(
        type="ほのお",
        category="変化",
        pp=15,
        accuracy=85,
    ),
    "ガードシェア": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "ガードスワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "かいでんぱ": MoveData(
        type="でんき",
        category="変化",
        pp=15,
        accuracy=100,
    ),
    "かいふくふうじ": MoveData(
        type="エスパー",
        category="変化",
        pp=15,
        accuracy=100,
    ),
    "かえんのまもり": MoveData(
        type="ほのお",
        category="変化",
        pp=10,
        accuracy=0,
        priority=4,
        target="self",
        handlers={
            Event.ON_CHECK_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="かえんのまもり", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "かげぶんしん": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        accuracy=0,
    ),
    "かたくなる": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=0,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=1, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "かなしばり": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=100,
    ),
    "からにこもる": MoveData(
        type="みず",
        category="変化",
        pp=40,
        accuracy=0,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=1, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "からをやぶる": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        accuracy=0,
    ),
    "きあいだめ": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=0,
    ),
    "ギアチェンジ": MoveData(
        type="はがね",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "キノコのほうし": MoveData(
        type="くさ",
        category="変化",
        pp=15,
        accuracy=100,
        labels=["powder"],
    ),
    "きりばらい": MoveData(
        type="ひこう",
        category="変化",
        pp=15,
        accuracy=0,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="EVA", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "きんぞくおん": MoveData(
        type="はがね",
        category="変化",
        pp=40,
        accuracy=85,
        labels=["sound"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-2, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "くすぐる": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=100,
    ),
    "グラスフィールド": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        accuracy=0,
        target="field",
    ),
    "くろいきり": MoveData(
        type="こおり",
        category="変化",
        pp=30,
        accuracy=0,
        target="field",
    ),
    "くろいまなざし": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        accuracy=100,
    ),
    "こうごうせい": MoveData(
        type="くさ",
        category="変化",
        pp=5,
        accuracy=0,
        labels=["heal"],
    ),
    "こうそくいどう": MoveData(
        type="エスパー",
        category="変化",
        pp=30,
        accuracy=0,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=2, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "コーチング": MoveData(
        type="かくとう",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "コートチェンジ": MoveData(
        type="ノーマル",
        category="変化",
        pp=100,
        accuracy=0,
    ),
    "コスモパワー": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        accuracy=0,
    ),
    "コットンガード": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        accuracy=0,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=3, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "このゆびとまれ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=0,
        priority=2,
    ),
    "こらえる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
        priority=4,
    ),
    "こわいかお": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-2, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "さいきのいのり": MoveData(
        type="ノーマル",
        category="変化",
        pp=0,
        accuracy=0,
        labels=["heal"],
    ),
    "サイコフィールド": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=0,
        target="field",
    ),
    "サイドチェンジ": MoveData(
        type="エスパー",
        category="変化",
        pp=15,
        accuracy=0,
        priority=2,
    ),
    "さいはい": MoveData(
        type="エスパー",
        category="変化",
        pp=15,
        accuracy=0,
    ),
    "さいみんじゅつ": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        accuracy=60,
    ),
    "さきおくり": MoveData(
        type="あく",
        category="変化",
        pp=15,
        accuracy=0,
    ),
    "さむいギャグ": MoveData(
        type="こおり",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "じこあんじ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "じこさいせい": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        accuracy=0,
        labels=["heal"],
    ),
    "しっぽきり": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "しっぽをふる": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "じばそうさ": MoveData(
        type="でんき",
        category="変化",
        pp=20,
        accuracy=0,
    ),
    "しびれごな": MoveData(
        type="くさ",
        category="変化",
        pp=30,
        accuracy=75,
        labels=["powder"],
    ),
    "ジャングルヒール": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        accuracy=0,
        labels=["heal"],
    ),
    "じゅうでん": MoveData(
        type="でんき",
        category="変化",
        pp=20,
        accuracy=0,
    ),
    "じゅうりょく": MoveData(
        type="エスパー",
        category="変化",
        pp=5,
        accuracy=0,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.activate_global_field, global_field="じゅうりょく", source_spec="attacker:self"),
            )
        }
    ),
    "しょうりのまい": MoveData(
        type="かくとう",
        category="変化",
        pp=10,
        accuracy=0,
        labels=["dance"],
    ),
    "しろいきり": MoveData(
        type="こおり",
        category="変化",
        pp=30,
        accuracy=0,
        target="field",
    ),
    "しんぴのまもり": MoveData(
        type="ノーマル",
        category="変化",
        pp=25,
        accuracy=0,
        target="field",
    ),
    "シンプルビーム": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        accuracy=100,
    ),
    "スキルスワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "スケッチ": MoveData(
        type="ノーマル",
        category="変化",
        pp=0,
        accuracy=100,
        labels=["non_encore", "non_negoto"],
    ),
    "すてゼリフ": MoveData(
        type="あく",
        category="変化",
        pp=20,
        accuracy=100,
        labels=["sound"],
    ),
    "ステルスロック": MoveData(
        type="いわ",
        category="変化",
        pp=20,
        accuracy=0,
        target="field",
    ),
    "すなあつめ": MoveData(
        type="じめん",
        category="変化",
        pp=5,
        accuracy=0,
        labels=["heal"],
    ),
    "すなあらし": MoveData(
        type="いわ",
        category="変化",
        pp=10,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.activate_weather, weather="すなあらし", source_spec="attacker:self"),
            )
        }
    ),
    "すなかけ": MoveData(
        type="じめん",
        category="変化",
        pp=15,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="ACC", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "スピードスワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "すりかえ": MoveData(
        type="あく",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.すりかえ_swap_items,
            )
        }
    ),
    "スレッドトラップ": MoveData(
        type="むし",
        category="変化",
        pp=10,
        accuracy=0,
        priority=4,
        target="self",

        handlers={
            Event.ON_CHECK_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="スレッドトラップ", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "せいちょう": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=0,
    ),
    "ソウルビート": MoveData(
        type="ドラゴン",
        category="変化",
        pp=100,
        accuracy=0,
        labels=["dance", "sound"],
    ),
    "ダークホール": MoveData(
        type="あく",
        category="変化",
        pp=10,
        accuracy=50,
    ),
    "タールショット": MoveData(
        type="いわ",
        category="変化",
        pp=15,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.apply_volatile, volatile="タールショット", target_spec="defender:self", source_spec="attacker:self"),
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "たくわえる": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=0,
        handlers={
        }
    ),
    "たてこもる": MoveData(
        type="はがね",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "タマゴうみ": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        accuracy=0,
        labels=["heal"],
    ),
    "ちいさくなる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,

        handlers={
            Event.ON_CHECK_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="ちいさくなる", target_spec="attacker:self", source_spec="attacker:self"),
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="EVA", v=2, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "ちからをすいとる": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        accuracy=100,
        labels=["heal"],
    ),
    "ちょうおんぱ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=55,
        labels=["sound"],
    ),
    "ちょうのまい": MoveData(
        type="むし",
        category="変化",
        pp=20,
        accuracy=0,
        labels=["dance"],
    ),
    "ちょうはつ": MoveData(
        type="あく",
        category="変化",
        pp=20,
        accuracy=100,
    ),
    "つきのひかり": MoveData(
        type="フェアリー",
        category="変化",
        pp=5,
        accuracy=0,
        labels=["heal"],
    ),
    "つぶらなひとみ": MoveData(
        type="フェアリー",
        category="変化",
        pp=30,
        accuracy=100,
        priority=1,
    ),
    "つぼをつく": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=0,
    ),
    "つめとぎ": MoveData(
        type="あく",
        category="変化",
        pp=15,
        accuracy=0,
    ),
    "つるぎのまい": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        target="self",
        labels=["dance"],
        handlers={
        }
    ),
    "テクスチャー": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=0,
    ),
    "テクスチャー２": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=0,
    ),
    "デコレーション": MoveData(
        type="フェアリー",
        category="変化",
        pp=15,
        accuracy=100,
    ),
    "てだすけ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=100,
        priority=5,
    ),
    "てっぺき": MoveData(
        type="はがね",
        category="変化",
        pp=15,
        accuracy=0,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=2, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "テレポート": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        accuracy=0,
        priority=-6,
    ),
    "てんしのキッス": MoveData(
        type="フェアリー",
        category="変化",
        pp=10,
        accuracy=75,
    ),
    "でんじは": MoveData(
        type="でんき",
        category="変化",
        pp=20,
        accuracy=90,
    ),
    "でんじふゆう": MoveData(
        type="でんき",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "とおせんぼう": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        accuracy=100,
    ),
    "トーチカ": MoveData(
        type="どく",
        category="変化",
        pp=10,
        accuracy=0,
        priority=4,
        target="self",

        handlers={
            Event.ON_CHECK_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="トーチカ", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "とおぼえ": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        accuracy=0,
        labels=["sound"],
    ),
    "どくガス": MoveData(
        type="どく",
        category="変化",
        pp=40,
        accuracy=90,
    ),
    "どくどく": MoveData(
        type="どく",
        category="変化",
        pp=10,
        accuracy=90,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.apply_ailment, ailment="もうどく", target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "どくのいと": MoveData(
        type="どく",
        category="変化",
        pp=20,
        accuracy=100,
    ),
    "どくのこな": MoveData(
        type="どく",
        category="変化",
        pp=35,
        accuracy=75,
        labels=["powder"],
    ),
    "どくびし": MoveData(
        type="どく",
        category="変化",
        pp=20,
        accuracy=0,
        target="field",
    ),
    "とぐろをまく": MoveData(
        type="どく",
        category="変化",
        pp=20,
        accuracy=0,
    ),
    "とける": MoveData(
        type="どく",
        category="変化",
        pp=20,
        accuracy=0,
    ),
    "ドラゴンエール": MoveData(
        type="ドラゴン",
        category="変化",
        pp=15,
        accuracy=100,
    ),
    "トリック": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.すりかえ_swap_items,
            )
        }
    ),
    "トリックルーム": MoveData(
        type="エスパー",
        category="変化",
        pp=5,
        accuracy=0,
        priority=-7,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.activate_global_field, global_field="トリックルーム", source_spec="attacker:self", toggle=True),
            )
        }
    ),
    "ドわすれ": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        accuracy=0,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=2, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "ないしょばなし": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=0,
        labels=["sound"],
    ),
    "なかまづくり": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        accuracy=100,
    ),
    "なかよくする": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=0,
    ),
    "なきごえ": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        accuracy=100,
        labels=["sound"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "なまける": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        accuracy=0,
        labels=["heal"],
    ),
    "なみだめ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=0,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "なやみのタネ": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "なりきり": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "ニードルガード": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        accuracy=0,
        priority=4,
    ),
    "にほんばれ": MoveData(
        type="ほのお",
        category="変化",
        pp=5,
        accuracy=0,
        target="field",
    ),
    "にらみつける": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=-1, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "ねがいごと": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
        target="field",
        labels=["heal"],
    ),
    "ねごと": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
        labels=["non_encore", "non_negoto"],
    ),
    "ねばねばネット": MoveData(
        type="むし",
        category="変化",
        pp=20,
        accuracy=0,
        target="field",
    ),
    "ねむりごな": MoveData(
        type="くさ",
        category="変化",
        pp=15,
        accuracy=75,
        labels=["powder"],
    ),
    "ねむる": MoveData(
        type="エスパー",
        category="変化",
        pp=5,
        accuracy=0,
        labels=["heal"],
    ),
    "ねをはる": MoveData(
        type="くさ",
        category="変化",
        pp=20,
        accuracy=0,
    ),
    "のみこむ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
        labels=["heal"],
    ),
    "のろい": MoveData(
        type="ゴースト",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "ハートスワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "はいすいのじん": MoveData(
        type="かくとう",
        category="変化",
        pp=5,
        accuracy=0,
    ),
    "ハッピータイム": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=0,
    ),
    "バトンタッチ": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        accuracy=0,
    ),
    "はねやすめ": MoveData(
        type="ひこう",
        category="変化",
        pp=5,
        accuracy=0,
        labels=["heal"],
    ),
    "はねる": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        labels=[]
    ),
    "ハバネロエキス": MoveData(
        type="くさ",
        category="変化",
        pp=15,
        accuracy=100,
    ),
    "はらだいこ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "パワーシェア": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "パワースワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "パワートリック": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
    ),
    "ひかりのかべ": MoveData(
        type="エスパー",
        category="変化",
        pp=30,
        accuracy=0,
        target="field",
    ),
    "ひっくりかえす": MoveData(
        type="あく",
        category="変化",
        pp=20,
        accuracy=100,
    ),
    "ビルドアップ": MoveData(
        type="かくとう",
        category="変化",
        pp=20,
        accuracy=0,
    ),
    "ファストガード": MoveData(
        type="かくとう",
        category="変化",
        pp=15,
        accuracy=0,
        priority=3,
    ),
    "ふういん": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=0,

        handlers={
            Event.ON_CHECK_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="ふういん", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "フェアリーロック": MoveData(
        type="フェアリー",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "フェザーダンス": MoveData(
        type="ひこう",
        category="変化",
        pp=15,
        accuracy=100,
        labels=["dance"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="A", v=-2, target_spec="defender:self", source_spec="attacker:self"),
            )
        }
    ),
    "ふきとばし": MoveData(
        type="ノーマル",
        category="特殊",
        pp=20,
        priority=-6,
        labels=["wind"],
        handlers={
            Event.ON_CHECK_IMMUNE: h.MoveHandler(
                h.check_blow_immune,
                priority=30,
            ),
            Event.ON_HIT: h.MoveHandler(h.blow),
        }
    ),
    "フラフラダンス": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=100,
        labels=["dance"],
    ),
    "フラワーヒール": MoveData(
        type="フェアリー",
        category="変化",
        pp=10,
        accuracy=0,
        labels=["heal"],
    ),
    "ふるいたてる": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=0,
    ),
    "ブレイブチャージ": MoveData(
        type="エスパー",
        category="変化",
        pp=15,
        accuracy=0,
    ),
    "へびにらみ": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=100,
    ),
    "へんしん": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=100,
        labels=["non_encore"],
    ),
    "ぼうぎょしれい": MoveData(
        type="むし",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "ほえる": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=0,
        priority=-6,
        labels=["sound"],
    ),
    "ほおばる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "ほたるび": MoveData(
        type="むし",
        category="変化",
        pp=20,
        accuracy=0,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=3, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "ほろびのうた": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        accuracy=0,
        labels=["sound"],
    ),
    "まきびし": MoveData(
        type="じめん",
        category="変化",
        pp=20,
        accuracy=0,
        target="field",
    ),
    "マジックルーム": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=0,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.activate_global_field, global_field="マジックルーム", source_spec="attacker:self", toggle=True),
            )
        }
    ),
    "まねっこ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=0,
        labels=["non_negoto"],
    ),
    "まほうのこな": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        accuracy=100,
    ),
    "まもる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
        priority=4,
        target="self",

        handlers={
            Event.ON_CHECK_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="まもる", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "まるくなる": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        accuracy=0,

        handlers={
            Event.ON_CHECK_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="まるくなる", target_spec="attacker:self", source_spec="attacker:self"),
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="B", v=1, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "みかづきのいのり": MoveData(
        type="エスパー",
        category="変化",
        pp=5,
        accuracy=0,
        labels=["heal"],
    ),
    "みかづきのまい": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=0,
        labels=["dance", "heal"],
    ),
    "みがわり": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
        handlers={
            Event.ON_CHECK_IMMUNE: h.MoveHandler(
                h.みがわり_can_use,
                priority=100,
            )
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.みがわり_apply,
            )
        }
    ),
    "みきり": MoveData(
        type="かくとう",
        category="変化",
        pp=5,
        accuracy=0,
        priority=4,
        target="self",

        handlers={
            Event.ON_CHECK_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="まもる", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "ミストフィールド": MoveData(
        type="フェアリー",
        category="変化",
        pp=10,
        accuracy=0,
        target="field",
    ),
    "みずびたし": MoveData(
        type="みず",
        category="変化",
        pp=20,
        accuracy=100,
    ),
    "みちづれ": MoveData(
        type="ゴースト",
        category="変化",
        pp=5,
        accuracy=0,

        handlers={
            Event.ON_CHECK_MOVE: h.MoveHandler(
                partial(common.apply_volatile, volatile="みちづれ", target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "ミラータイプ": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        accuracy=0,
    ),
    "ミルクのみ": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        accuracy=0,
        labels=["heal"],
    ),
    "みをけずる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "めいそう": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        accuracy=0,
    ),
    "メロメロ": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        accuracy=100,
    ),
    "ものまね": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
        labels=["non_encore", "non_negoto"],
    ),
    "もりののろい": MoveData(
        type="くさ",
        category="変化",
        pp=20,
        accuracy=100,
    ),
    "やどりぎのタネ": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        accuracy=90,
    ),
    "ゆきげしき": MoveData(
        type="こおり",
        category="変化",
        pp=10,
        accuracy=0,
        target="field",
    ),
    "ゆびをふる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
        labels=["non_negoto"],
    ),
    "リサイクル": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=0,
    ),
    "リフレクター": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        target="field",
        handlers={
        }
    ),
    "リフレッシュ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=0,
    ),
    "りゅうのまい": MoveData(
        type="ドラゴン",
        category="変化",
        pp=20,
        accuracy=0,
        labels=["dance"],
    ),
    "ロックオン": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        accuracy=0,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.apply_volatile, volatile="ロックオン", target_spec="defender:self", source_spec="attacker:self", count=2),
            )
        }
    ),
    "ロックカット": MoveData(
        type="いわ",
        category="変化",
        pp=20,
        accuracy=0,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="S", v=2, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "ワイドガード": MoveData(
        type="いわ",
        category="変化",
        pp=10,
        accuracy=0,
        priority=3,
    ),
    "わたほうし": MoveData(
        type="くさ",
        category="変化",
        pp=40,
        accuracy=100,
        labels=["powder"],
    ),
    "わるだくみ": MoveData(
        type="あく",
        category="変化",
        pp=20,
        accuracy=0,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="C", v=2, target_spec="attacker:self", source_spec="attacker:self"),
            )
        }
    ),
    "ワンダールーム": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=0,
        target="field",
        labels=[],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                partial(common.activate_global_field, global_field="ワンダールーム", source_spec="attacker:self", toggle=True),
            )
        }
    ),
    "あてみなげ": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=50,
        accuracy=100,
        priority=-1,
        labels=["contact"],
    ),
    "キングシールド": MoveData(
        type="はがね",
        category="変化",
        pp=10,
        accuracy=0,
        priority=4,
        target="self",

        handlers={
            Event.ON_CHECK_MOVE: h.MoveHandler(
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
    ),
}


common_setup()
