"""技データ定義モジュール。

Note:
    このモジュール内の技定義はMOVES辞書内で五十音順に配置されています。
"""
from dataclasses import dataclass
from functools import partial

from jpoke.enums import Event
from jpoke.utils.type_defs import RoleSpec, AilmentName
from jpoke.core import Handler, HandlerReturn
from jpoke.handlers import common, move as h, volatile as v
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
    for name, obj in MOVES.items():
        MOVES[name].name = name

        # 共通ハンドラを追加
        MOVES[name].handlers[Event.ON_CONSUME_PP] = h.MoveHandler(
            h.consume_pp,
            subject_spec="attacker:self",
            log="always"
        )


# TODO: 追加効果が登録されているイベントを修正
# ON_PAY_HP : HPコスト消費
# ON_HIT : attackerのランク変動、hp吸収による回復など
# ON_DAMAGE_1 : defenderのランク変動など
# ON_DAMAGE_2 : 反動ダメージなど
# 詳細は docs/spec/turn_flow.md を参照

# TODO: 定義内の空行を削除
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
                partial(common.modify_hp, target_spec="attacker:self", r=-1/4),
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
        labels=["contact", "punch"],
        handlers={
             Event.ON_HIT: h.MoveHandler(
                 partial(common.modify_stat, stat="S", v=-1, target_spec="attacker:self", source_spec="attacker:self"
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
        labels=["contact"],
        handlers={
            Event.ON_DAMAGE_1: h.MoveHandler(
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

        labels=["contact"],
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
        labels=["contact"],
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
    ),
    "いじげんラッシュ": MoveData(
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
        type="ほのお",
        category="物理",
        pp=25,
        power=60,
        accuracy=100,

        labels=["contact"],
    ),
    "かえんボール": MoveData(
        type="ほのお",
        category="物理",
        pp=5,
        power=120,
        accuracy=90,

        labels=["bullet"],
    ),
    "かかとおとし": MoveData(
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
        type="あく",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,

        labels=["bite", "contact"],
    ),
    "かみつく": MoveData(
        type="あく",
        category="物理",
        pp=25,
        power=60,
        accuracy=100,

        labels=["bite", "contact"],
    ),
    "かみなりのキバ": MoveData(
        type="でんき",
        category="物理",
        pp=15,
        power=65,
        accuracy=95,

        labels=["contact"],
    ),
    "かみなりパンチ": MoveData(
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

        labels=["contact"],
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

        labels=["contact"],
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
        type="ほのお",
        category="物理",
        pp=5,
        power=100,
        accuracy=95,


    ),
    "ソウルクラッシュ": MoveData(
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

    ),
    "ダイビング": MoveData(
        type="みず",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,
        labels=["contact"],
    ),
    "だいふんげき": MoveData(
        type="ほのお",
        category="物理",
        pp=10,
        power=120,
        accuracy=100,
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

        labels=["contact"],
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
    ),
    "ダブルアタック": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=35,
        accuracy=90,
        labels=["contact"],
    ),
    "ダブルウイング": MoveData(
        type="ひこう",
        category="物理",
        pp=10,
        power=40,
        accuracy=90,
        labels=["contact"],
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
    ),
    "ついばむ": MoveData(
        type="ひこう",
        category="物理",
        pp=20,
        power=60,
        accuracy=100,
        labels=["contact"],
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
        labels=["contact"],
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
        type="どく",
        category="物理",
        pp=20,
        power=80,
        accuracy=100,

        labels=["contact"],
    ),
    "どくどくのキバ": MoveData(
        type="どく",
        category="物理",
        pp=15,
        power=50,
        accuracy=100,

        labels=["contact"],
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
        type="ドラゴン",
        category="物理",
        pp=10,
        power=100,
        accuracy=75,

        labels=["contact"],
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
    ),
    "トリプルキック": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=10,
        accuracy=90,
        labels=["contact"],
    ),
    "トリプルダイブ": MoveData(
        type="みず",
        category="物理",
        pp=10,
        power=30,
        accuracy=95,
        labels=["contact"],
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
    ),
    "ニトロチャージ": MoveData(
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
    ),
    "のしかかり": MoveData(
        type="ノーマル",
        category="物理",
        pp=15,
        power=85,
        accuracy=100,

        labels=["contact"],
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
        type="はがね",
        category="物理",
        pp=25,
        power=70,
        accuracy=90,

        labels=["contact"],
    ),
    "ばくれつパンチ": MoveData(
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
        labels=["contact"],
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
        type="かくとう",
        category="物理",
        pp=15,
        power=65,
        accuracy=100,
        priority=3,
        labels=["contact"],
    ),
    "バリアーラッシュ": MoveData(
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
        labels=["contact"],
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
        type="じめん",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,

        labels=["contact", "punch"],
    ),
    "ふみつけ": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=65,
        accuracy=100,

        labels=["contact"],
    ),
    "フライングプレス": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=100,
        accuracy=95,
        labels=["contact"],
    ),
    "フリーズボルト": MoveData(
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
        type="ほのお",
        category="物理",
        pp=15,
        power=120,
        accuracy=100,

        labels=["contact"],
    ),
    "ブレイククロー": MoveData(
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
        labels=["contact"],
    ),
    "ホイールスピン": MoveData(
        type="はがね",
        category="物理",
        pp=5,
        power=100,
        accuracy=100,

        labels=["contact"],
    ),
    "ポイズンテール": MoveData(
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
    ),
    "ほっぺすりすり": MoveData(
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
        type="ほのお",
        category="物理",
        pp=15,
        power=65,
        accuracy=95,

        labels=["contact"],
    ),
    "ほのおのパンチ": MoveData(
        type="ほのお",
        category="物理",
        pp=15,
        power=75,
        accuracy=100,

        labels=["contact", "punch"],
    ),
    "ほのおのムチ": MoveData(
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
        type="でんき",
        category="物理",
        pp=15,
        power=120,
        accuracy=100,

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

    ),
    "みだれづき": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=15,
        accuracy=85,
        labels=["contact"],
    ),
    "みだれひっかき": MoveData(
        type="ノーマル",
        category="物理",
        pp=15,
        power=18,
        accuracy=80,
        labels=["contact"],
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
        type="でんき",
        category="物理",
        pp=5,
        power=130,
        accuracy=85,

        labels=["contact"],
    ),
    "らいめいげり": MoveData(
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
    ),
    "ワイドブレイカー": MoveData(
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

        labels=["contact"],
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
        critical_rank=1,
    ),
    "あくのはどう": MoveData(
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
        accuracy=100
    ),
    "いびき": MoveData(
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
        critical_rank=1,
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
        labels=["wind"],
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
        labels=["bullet"],
    ),
    "かみなり": MoveData(
        type="でんき",
        category="特殊",
        pp=10,
        power=110,
        accuracy=70,

        handlers={
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
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

        labels=["wind"],
    ),
    "きあいだま": MoveData(
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
        type="こおり",
        category="特殊",
        pp=5,
        power=140,
        accuracy=90,


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

        labels=["wind"],
    ),
    "こごえるかぜ": MoveData(
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
        labels=["pulse"],
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
        labels=["bind"],
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
        type="くさ",
        category="特殊",
        pp=15,
        power=80,
        accuracy=90,


    ),
    "シャドーボール": MoveData(
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

    ),
    "ソーラービーム": MoveData(
        type="くさ",
        category="特殊",
        pp=10,
        power=120,
        accuracy=100,

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

        labels=["wind"],
    ),
    "チャージビーム": MoveData(
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

        labels=["wind"],
    ),
    "ねっさのだいち": MoveData(
        type="じめん",
        category="特殊",
        pp=10,
        power=70,
        accuracy=100,


    ),
    "ねっとう": MoveData(
        type="みず",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,


    ),
    "ねっぷう": MoveData(
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
        type="こおり",
        category="特殊",
        pp=5,
        power=110,
        accuracy=70,
        labels=["wind"],
        handlers={
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
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

    ),
    "ブラッドムーン": MoveData(
        type="ノーマル",
        category="特殊",
        pp=5,
        power=140,
        accuracy=100,

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

        labels=["sound"],
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
        labels=["wind"],
        handlers={
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
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

        labels=["sound"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                partial(common.modify_stat, stat="D", v=-1, target_spec="defender:self", source_spec="attacker:self", chance=0.1)
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
        labels=["pulse"],
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
        labels=["sound"],
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
    # -------------------------
    # 変化技
    # -------------------------
    "アクアリング": MoveData(
        type="みず",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "あくび": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "あくまのキッス": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=75,

    ),
    "あさのひざし": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        labels=["heal"],
    ),
    "あまいかおり": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,

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

    ),
    "あやしいひかり": MoveData(
        type="ゴースト",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

    ),
    "アロマセラピー": MoveData(
        type="くさ",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,

    ),
    "アロマミスト": MoveData(
        type="フェアリー",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,

    ),
    "アンコール": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=100,
        labels=["non_encore"],
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

    ),
    "いかりのこな": MoveData(
        type="むし",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        priority=2,

    ),
    "いたみわけ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "いちゃもん": MoveData(
        type="あく",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,

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

    ),
    "いのちのしずく": MoveData(
        type="みず",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        labels=["heal"],
    ),
    "いばる": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        power=0,
        accuracy=85,

    ),
    "いやしのすず": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        labels=["sound"],
    ),
    "いやしのねがい": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        labels=["heal"],
    ),
    "いやしのはどう": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        labels=["heal"],
    ),
    "いやなおと": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        power=0,
        accuracy=85,
        labels=["sound"],
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
        labels=["sound"],
    ),
    "うつしえ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

    ),
    "うらみ": MoveData(
        type="ゴースト",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "エレキフィールド": MoveData(
        type="でんき",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "えんまく": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,

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
        labels=["wind"],
    ),
    "おいわい": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        power=0,
        accuracy=0,
        labels=["non_negoto"],
    ),
    "オーロラベール": MoveData(
        type="こおり",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "おかたづけ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "おきみやげ": MoveData(
        type="あく",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

    ),
    "おさきにどうぞ": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,

    ),
    "おたけび": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=100,
        labels=["sound"],
    ),
    "おだてる": MoveData(
        type="あく",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,

    ),
    "おちゃかい": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "おにび": MoveData(
        type="ほのお",
        category="変化",
        pp=15,
        power=0,
        accuracy=85,

    ),
    "ガードシェア": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

    ),
    "ガードスワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

    ),
    "かいでんぱ": MoveData(
        type="でんき",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,

    ),
    "かいふくふうじ": MoveData(
        type="エスパー",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,

    ),
    "かえんのまもり": MoveData(
        type="ほのお",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        priority=4,

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

    ),
    "かたくなる": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,

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

    ),
    "からにこもる": MoveData(
        type="みず",
        category="変化",
        pp=40,
        power=0,
        accuracy=0,

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

    ),
    "きあいだめ": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,

    ),
    "ギアチェンジ": MoveData(
        type="はがね",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "キノコのほうし": MoveData(
        type="くさ",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        labels=["powder"],
    ),
    "きりばらい": MoveData(
        type="ひこう",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,

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
        labels=["sound"],
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

    ),
    "グラスフィールド": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "くろいきり": MoveData(
        type="こおり",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,

    ),
    "くろいまなざし": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=100,

    ),
    "こうごうせい": MoveData(
        type="くさ",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        labels=["heal"],
    ),
    "こうそくいどう": MoveData(
        type="エスパー",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,

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

    ),
    "コートチェンジ": MoveData(
        type="ノーマル",
        category="変化",
        pp=100,
        power=0,
        accuracy=0,

    ),
    "コスモパワー": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "コットンガード": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

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

    ),
    "こらえる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        priority=4,

    ),
    "こわいかお": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

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
        labels=["heal"],
    ),
    "サイコフィールド": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "サイドチェンジ": MoveData(
        type="エスパー",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        priority=2,

    ),
    "さいはい": MoveData(
        type="エスパー",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,

    ),
    "さいみんじゅつ": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        power=0,
        accuracy=60,

    ),
    "さきおくり": MoveData(
        type="あく",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,

    ),
    "さむいギャグ": MoveData(
        type="こおり",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "じこあんじ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

    ),
    "じこさいせい": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        labels=["heal"],
    ),
    "しっぽきり": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "しっぽをふる": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=100,

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

    ),
    "しびれごな": MoveData(
        type="くさ",
        category="変化",
        pp=30,
        power=0,
        accuracy=75,
        labels=["powder"],
    ),
    "ジャングルヒール": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        labels=["heal"],
    ),
    "じゅうでん": MoveData(
        type="でんき",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "じゅうりょく": MoveData(
        type="エスパー",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,

    ),
    "しょうりのまい": MoveData(
        type="かくとう",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        labels=["dance"],
    ),
    "しろいきり": MoveData(
        type="こおり",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,

    ),
    "しんぴのまもり": MoveData(
        type="ノーマル",
        category="変化",
        pp=25,
        power=0,
        accuracy=0,

    ),
    "シンプルビーム": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,

    ),
    "スキルスワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

    ),
    "スケッチ": MoveData(
        type="ノーマル",
        category="変化",
        pp=0,
        power=0,
        accuracy=100,
        labels=["non_encore", "non_negoto"],
    ),
    "すてゼリフ": MoveData(
        type="あく",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        labels=["sound"],
    ),
    "ステルスロック": MoveData(
        type="いわ",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "すなあつめ": MoveData(
        type="じめん",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        labels=["heal"],
    ),
    "すなあらし": MoveData(
        type="いわ",
        category="変化",
        pp=10,
        labels=["wind"],
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

    ),
    "すりかえ": MoveData(
        type="あく",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

    ),
    "スレッドトラップ": MoveData(
        type="むし",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        priority=4,

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

    ),
    "ソウルビート": MoveData(
        type="ドラゴン",
        category="変化",
        pp=100,
        power=0,
        accuracy=0,
        labels=["dance", "sound"],
    ),
    "ダークホール": MoveData(
        type="あく",
        category="変化",
        pp=10,
        power=0,
        accuracy=50,

    ),
    "タールショット": MoveData(
        type="いわ",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,

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

    ),
    "タマゴうみ": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        labels=["heal"],
    ),
    "ちいさくなる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

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
        labels=["heal"],
    ),
    "ちょうおんぱ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=55,
        labels=["sound"],
    ),
    "ちょうのまい": MoveData(
        type="むし",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        labels=["dance"],
    ),
    "ちょうはつ": MoveData(
        type="あく",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,

    ),
    "つきのひかり": MoveData(
        type="フェアリー",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        labels=["heal"],
    ),
    "つぶらなひとみ": MoveData(
        type="フェアリー",
        category="変化",
        pp=30,
        power=0,
        accuracy=100,
        priority=1,

    ),
    "つぼをつく": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,

    ),
    "つめとぎ": MoveData(
        type="あく",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,

    ),
    "つるぎのまい": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        labels=["dance"],
        handlers={
        }
    ),
    "テクスチャー": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,

    ),
    "テクスチャー２": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,

    ),
    "デコレーション": MoveData(
        type="フェアリー",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,

    ),
    "てだすけ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,
        priority=5,

    ),
    "てっぺき": MoveData(
        type="はがね",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,

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

    ),
    "てんしのキッス": MoveData(
        type="フェアリー",
        category="変化",
        pp=10,
        power=0,
        accuracy=75,

    ),
    "でんじは": MoveData(
        type="でんき",
        category="変化",
        pp=20,
        power=0,
        accuracy=90,

    ),
    "でんじふゆう": MoveData(
        type="でんき",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "とおせんぼう": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=100,

    ),
    "トーチカ": MoveData(
        type="どく",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        priority=4,

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
        labels=["sound"],
    ),
    "どくガス": MoveData(
        type="どく",
        category="変化",
        pp=40,
        power=0,
        accuracy=90,

    ),
    "どくどく": MoveData(
        type="どく",
        category="変化",
        pp=10,
        accuracy=90,

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

    ),
    "どくのこな": MoveData(
        type="どく",
        category="変化",
        pp=35,
        power=0,
        accuracy=75,
        labels=["powder"],
    ),
    "どくびし": MoveData(
        type="どく",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "とぐろをまく": MoveData(
        type="どく",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "とける": MoveData(
        type="どく",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "ドラゴンエール": MoveData(
        type="ドラゴン",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,

    ),
    "トリック": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

    ),
    "トリックルーム": MoveData(
        type="エスパー",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        priority=-7,

    ),
    "ドわすれ": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

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
        labels=["sound"],
    ),
    "なかまづくり": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,

    ),
    "なかよくする": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "なきごえ": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        power=0,
        accuracy=100,
        labels=["sound"],
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
        labels=["heal"],
    ),
    "なみだめ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

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

    ),
    "なりきり": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

    ),
    "ニードルガード": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        priority=4,

    ),
    "にほんばれ": MoveData(
        type="ほのお",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,

    ),
    "にらみつける": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=100,

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
        labels=["heal"],
    ),
    "ねごと": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        labels=["non_encore", "non_negoto"],
    ),
    "ねばねばネット": MoveData(
        type="むし",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "ねむりごな": MoveData(
        type="くさ",
        category="変化",
        pp=15,
        power=0,
        accuracy=75,
        labels=["powder"],
    ),
    "ねむる": MoveData(
        type="エスパー",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        labels=["heal"],
    ),
    "ねをはる": MoveData(
        type="くさ",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "のみこむ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        labels=["heal"],
    ),
    "のろい": MoveData(
        type="ゴースト",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "ハートスワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

    ),
    "はいすいのじん": MoveData(
        type="かくとう",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,

    ),
    "ハッピータイム": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,

    ),
    "バトンタッチ": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        power=0,
        accuracy=0,

    ),
    "はねやすめ": MoveData(
        type="ひこう",
        category="変化",
        pp=5,
        power=0,
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
        power=0,
        accuracy=100,

    ),
    "はらだいこ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "パワーシェア": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

    ),
    "パワースワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

    ),
    "パワートリック": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,

    ),
    "ひかりのかべ": MoveData(
        type="エスパー",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,

    ),
    "ひっくりかえす": MoveData(
        type="あく",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,

    ),
    "ビルドアップ": MoveData(
        type="かくとう",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "ファストガード": MoveData(
        type="かくとう",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,
        priority=3,

    ),
    "ふういん": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

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

    ),
    "フェザーダンス": MoveData(
        type="ひこう",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,
        labels=["dance"],
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
        labels=["wind"],
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
        labels=["dance"],
    ),
    "フラワーヒール": MoveData(
        type="フェアリー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        labels=["heal"],
    ),
    "ふるいたてる": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=0,

    ),
    "ブレイブチャージ": MoveData(
        type="エスパー",
        category="変化",
        pp=15,
        power=0,
        accuracy=0,

    ),
    "へびにらみ": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        power=0,
        accuracy=100,

    ),
    "へんしん": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=100,
        labels=["non_encore"],
    ),
    "ぼうぎょしれい": MoveData(
        type="むし",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "ほえる": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        priority=-6,
        labels=["sound"],
    ),
    "ほおばる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "ほたるび": MoveData(
        type="むし",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

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
        labels=["sound"],
    ),
    "まきびし": MoveData(
        type="じめん",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "マジックルーム": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "まねっこ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        labels=["non_negoto"],
    ),
    "まほうのこな": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,

    ),
    "まもる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        priority=4,

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
        labels=["heal"],
    ),
    "みかづきのまい": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        labels=["dance", "heal"],
    ),
    "みがわり": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

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

    ),
    "みずびたし": MoveData(
        type="みず",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,

    ),
    "みちづれ": MoveData(
        type="ゴースト",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,

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

    ),
    "ミルクのみ": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,
        labels=["heal"],
    ),
    "みをけずる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "めいそう": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "メロメロ": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        power=0,
        accuracy=100,

    ),
    "ものまね": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        labels=["non_encore", "non_negoto"],
    ),
    "もりののろい": MoveData(
        type="くさ",
        category="変化",
        pp=20,
        power=0,
        accuracy=100,

    ),
    "やどりぎのタネ": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        power=0,
        accuracy=90,

    ),
    "ゆきげしき": MoveData(
        type="こおり",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "ゆびをふる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,
        labels=["non_negoto"],
    ),
    "リサイクル": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        power=0,
        accuracy=0,

    ),
    "リフレクター": MoveData(
        type="エスパー",
        category="変化",
        pp=20,

        handlers={
        }
    ),
    "リフレッシュ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

    ),
    "りゅうのまい": MoveData(
        type="ドラゴン",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,
        labels=["dance"],
    ),
    "ロックオン": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        power=0,
        accuracy=0,

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

    ),
    "わたほうし": MoveData(
        type="くさ",
        category="変化",
        pp=40,
        power=0,
        accuracy=100,
        labels=["powder"],
    ),
    "わるだくみ": MoveData(
        type="あく",
        category="変化",
        pp=20,
        power=0,
        accuracy=0,

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
        labels=[]
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
        power=0,
        accuracy=0,
        priority=4,

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

    ),
}


common_setup()
