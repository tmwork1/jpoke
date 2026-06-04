"""技データ定義モジュール。

Note:
    このモジュール内の技定義はMOVES辞書内で五十音順に配置されています。
"""
from jpoke.enums import Event
from jpoke.handlers import common, move as h
from .models import MoveData


def common_setup() -> None:
    """
    全ての技に共通ハンドラを追加する。

    この関数は、MOVESディクショナリ内の全てのMoveDataに対して、
    呼び出しタイミング: モジュール初期化時（ファイル末尾）

    Note:
        dictインスタンスはスキップされます（MoveDataオブジェクトのみ処理）
    """
    for name, data in MOVES.items():
        data.name = name


MOVES: dict[str, MoveData] = {
    # -------------------------
    # 攻撃技
    # -------------------------
    "わるあがき": MoveData(
        type="",
        category="物理",
        pp=99999,
        power=40,
        labels=["contact", "non_encore"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.わるあがき_self_damage,
            )
        }
    ),
    "こんらん": MoveData(
        type="",
        category="物理",
        pp=99999,
        power=40,
    ),
    "10まんばりき": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=95,
        accuracy=95,
        labels=["contact"],
    ),
    "3ぼんのや": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,
        critical_rank=1,

    ),
    "DDラリアット": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=85,
        accuracy=100,
        labels=["contact"],
    ),
    "Gのちから": MoveData(
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
                 h.アームハンマー_modify_attacker_stats,
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                h.アイアンテール_modify_defender_stats,
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
        type="こおり",
        category="物理",
        pp=10,
        power=100,
        accuracy=90,
        labels=["contact", "punch", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.アイスハンマー_modify_attacker_stats,
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
        labels=["contact", "dance", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.アクアステップ_modify_attacker_stats,
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
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.アクアブレイク_modify_defender_stats,
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
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                h.HP_ratio_damage,
                subject_spec="attacker:self",
            )
        }
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
                h.いわくだき_modify_defender_stats,
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
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.インファイト_modify_attacker_stats,
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
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(
                h.オーラぐるま_check_move_type,
                subject_spec="source:self",
            ),
        },
    ),
    "おどろかす": MoveData(
        type="ゴースト",
        category="物理",
        pp=15,
        power=30,
        accuracy=100,
        labels=["contact", "secondary_effect"],
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
        labels=["contact", "secondary_effect"],
    ),
    "かえんボール": MoveData(
        type="ほのお",
        category="物理",
        pp=5,
        power=120,
        accuracy=90,
        labels=["bullet", "secondary_effect"],
    ),
    "かかとおとし": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=120,
        accuracy=90,
        labels=["contact", "secondary_effect"],
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
        labels=["bite", "contact", "secondary_effect"],
    ),
    "かみつく": MoveData(
        type="あく",
        category="物理",
        pp=25,
        power=60,
        accuracy=100,
        labels=["bite", "contact", "secondary_effect"],
    ),
    "かみなりのキバ": MoveData(
        type="でんき",
        category="物理",
        pp=15,
        power=65,
        accuracy=95,
        labels=["contact", "secondary_effect"],
    ),
    "かみなりパンチ": MoveData(
        type="でんき",
        category="物理",
        pp=15,
        power=75,
        accuracy=100,
        labels=["contact", "punch", "secondary_effect"],
    ),
    "がむしゃら": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=0,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
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
        type="ひこう",
        category="物理",
        pp=5,
        power=120,
        accuracy=100,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.ガリョウテンセイ_modify_attacker_stats,
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
                h.がんせきふうじ_modify_defender_stats,
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
            Event.ON_TRY_MOVE_1: h.MoveHandler(
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
        type="どく",
        category="物理",
        pp=15,
        power=30,
        accuracy=100,
        labels=["contact", "secondary_effect"],
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
        handlers={
            Event.ON_HIT: h.MoveHandler(h.pivot)
        }
    ),
    "くさわけ": MoveData(
        type="くさ",
        category="物理",
        pp=20,
        power=50,
        accuracy=100,
        labels=["contact", "secondary_effect"],
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
        labels=["contact", "slash", "secondary_effect"],
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
        labels=["contact", "secondary_effect"],
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
        labels=["contact", "secondary_effect"],
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
        labels=["contact", "punch", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.コメットパンチ_modify_attacker_stats,
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
        type="みず",
        category="物理",
        pp=10,
        power=75,
        accuracy=95,
        labels=["contact", "slash", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.シェルブレード_modify_defender_stats,
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
        labels=["contact", "secondary_effect"],
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
                h.じならし_modify_defender_stats,
            )
        }
    ),
    "しねんのずつき": MoveData(
        type="エスパー",
        category="物理",
        pp=15,
        power=80,
        accuracy=90,
        labels=["contact", "secondary_effect"],
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
        labels=["contact"],
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
        }
    ),
    "シャドーパンチ": MoveData(
        type="ゴースト",
        category="物理",
        pp=20,
        power=60,

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
        labels=["ohko"],
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                h.ohko_modify_damage,
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
        multi_hit={"min": 3, "max": 3},
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
                h.ソウルクラッシュ_modify_defender_stats,
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
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
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
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                h.ohko_modify_damage,
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

        labels=["contact"],
    ),
    "ドゲザン": MoveData(
        type="あく",
        category="物理",
        pp=10,
        power=85,

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
                h.とびかかる_modify_defender_stats,
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
                h.とびつく_modify_defender_stats,
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

        type="くさ",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.ドラムアタック_modify_defender_stats,
            )
        }
    ),
    "トリックフラワー": MoveData(
        type="くさ",
        category="物理",
        pp=10,
        power=70,
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

        type="くさ",
        category="物理",
        pp=15,
        power=70,
        accuracy=100,

        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.トロピカルキック_modify_defender_stats,
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

        type="ほのお",
        category="物理",
        pp=20,
        power=50,
        accuracy=100,

        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.ニトロチャージ_modify_attacker_stats,
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
        multi_hit={
            "min": 10,
            "max": 10,
            "check_hit_each_time": True,
            "power_sequence": (),
        }
    ),
    "のしかかり": MoveData(

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

        type="むし",
        category="物理",
        pp=10,
        power=70,
        accuracy=90,

        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.はいよるいちげき_modify_defender_stats,
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
                h.ばかぢから_modify_attacker_stats,
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
        labels=["ohko", "contact"],
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                h.ohko_modify_damage,
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
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                h.はやてがえし_try_move,
            ),
            Event.ON_HIT: h.MoveHandler(
                h.はやてがえし_apply_volatile_to_defender,
            ),
        }
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
                h.ブレイククロー_modify_defender_stats,
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
        labels=["minimize", "contact"],
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
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.どろぼう_steal_item,
            )
        }
    ),
    "ほっぺすりすり": MoveData(
        type="でんき",
        category="物理",
        pp=20,
        power=20,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                h.ほっぺすりすり_apply_ailment_to_defender,
            ),
        }
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
        labels=["contact"],
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

        type="はがね",
        category="物理",
        pp=35,
        power=50,
        accuracy=95,

        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.メタルクロー_modify_attacker_stats,
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
                h.らいめいげり_modify_defender_stats,
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
                h.ローキック_modify_defender_stats,
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

        type="ドラゴン",
        category="物理",
        pp=15,
        power=60,
        accuracy=100,

        labels=["contact"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.ワイドブレイカー_modify_defender_stats,
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
    "10まんボルト": MoveData(

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
                h.アーマーキャノン_modify_attacker_stats,
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
                h.アシッドボム_modify_defender_stats,
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
                h.いてつくしせん_modify_defender_stats,
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
        accuracy=100,
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                h.いのちがけ_pay_hp,
                subject_spec="attacker:self",
            ),
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                h.いのちがけ_modify_damage,
                subject_spec="attacker:self",
            ),
        }
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
                h.エナジーボール_modify_defender_stats,
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
                h.エレキネット_modify_defender_stats,
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
                h.オーバーヒート_modify_attacker_stats,
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
        accuracy=90,
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
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
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.ギガドレイン_heal_attacker,
            )
        }
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
        accuracy=None
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
                h.こごえるかぜ_modify_defender_stats,
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
                h.こごえるせかい_modify_defender_stats,
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
                h.サイコキネシス_modify_defender_stats,
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
                h.サイコブースト_modify_attacker_stats,
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
        }
    ),
    "サンダープリズン": MoveData(
        type="でんき",
        category="特殊",
        pp=15,
        power=80,
        accuracy=90,

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
                h.シャドーボール_modify_defender_stats,
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
                h.スケイルノイズ_modify_attacker_stats,
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
        accuracy=None
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
        labels=["ohko"],
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                h.ohko_modify_damage,
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
                h.チャージビーム_modify_attacker_stats,
            )
        }
    ),
    "チャームボイス": MoveData(
        type="フェアリー",
        category="特殊",
        pp=15,
        power=40,

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
                h.テラバースト_modify_move_type,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_MOVE_CATEGORY: h.MoveHandler(
                h.テラバースト_modify_move_category,
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
        accuracy=None
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
                h.でんじほう_apply_ailment_to_defender,
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
        accuracy=100,
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
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
                h.バークアウト_modify_defender_stats,
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
                h.ひやみず_modify_defender_stats,
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
                h.フルールカノン_modify_attacker_stats,
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
        handlers={
            Event.ON_HIT: h.MoveHandler(h.pivot)
        }
    ),
    "マグマストーム": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=100,
        accuracy=75,

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
                h.マジカルフレイム_modify_defender_stats,
            )
        }
    ),
    "マジカルリーフ": MoveData(
        type="くさ",
        category="特殊",
        pp=20,
        power=60,
        accuracy=None
    ),
    "マッドショット": MoveData(

        type="じめん",
        category="特殊",
        pp=15,
        power=55,
        accuracy=95,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.マッドショット_modify_defender_stats,
            )
        }
    ),
    "まとわりつく": MoveData(
        type="むし",
        category="特殊",
        pp=20,
        power=20,
        accuracy=100,
        labels=["contact"],
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

        type="エスパー",
        category="特殊",
        pp=5,
        power=95,
        accuracy=100,

        labels=["bullet"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                h.ミストボール_modify_defender_stats,
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
                h.むしのさざめき_modify_defender_stats,
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
                h.むしのていこう_modify_defender_stats,
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
                h.ラスターカノン_modify_defender_stats,
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
                h.ラスターパージ_modify_defender_stats,
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
                h.リーフストーム_modify_attacker_stats,
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
                h.りゅうせいぐん_modify_attacker_stats,
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
                h.ルミナコリジョン_modify_defender_stats,
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

    ),
    "あくび": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,

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

        labels=["heal"],
    ),
    "あまいかおり": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.あまいかおり_modify_defender_stats,
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
                h.あまえる_modify_attacker_stats,
            )
        }
    ),
    "あまごい": MoveData(
        type="みず",
        category="変化",
        pp=5,

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
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                h.アンコール_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.アンコール_apply,
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

        priority=2,
    ),
    "いたみわけ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,


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
                h.いちゃもん_apply_volatile_to_defender,
            ),
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

        labels=["sound"],
    ),
    "いやしのねがい": MoveData(
        type="エスパー",
        category="変化",
        pp=10,

        labels=["heal"],
    ),
    "いやしのはどう": MoveData(
        type="エスパー",
        category="変化",
        pp=10,

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
                h.いやなおと_modify_defender_stats,
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
                h.うそなき_modify_defender_stats,
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

    ),
    "エレキフィールド": MoveData(
        type="でんき",
        category="変化",
        pp=10,

        target="field",
    ),
    "えんまく": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.えんまく_modify_defender_stats,
            )
        }
    ),
    "おいかぜ": MoveData(
        type="ひこう",
        category="変化",
        pp=15,

        target="field",
        labels=["wind"],
    ),
    "おいわい": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,

        labels=["non_negoto"],
    ),
    "オーロラベール": MoveData(
        type="こおり",
        category="変化",
        pp=20,

        target="field",
    ),
    "おかたづけ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,

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

    ),
    "おにび": MoveData(
        type="ほのお",
        category="変化",
        pp=15,
        accuracy=85,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.おにび_apply_ailment_to_defender,
            ),
        }
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

        priority=4,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.かえんのまもり_apply_volatile_to_attacker,
            ),
        }
    ),
    "かげぶんしん": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,

    ),
    "かたくなる": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.かたくなる_modify_attacker_stats,
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


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.からにこもる_modify_attacker_stats,
            )
        }
    ),
    "からをやぶる": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,

    ),
    "きあいだめ": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,

    ),
    "ギアチェンジ": MoveData(
        type="はがね",
        category="変化",
        pp=10,

    ),
    "キノコのほうし": MoveData(
        type="くさ",
        category="変化",
        pp=15,
        accuracy=100,
        labels=["powder"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.キノコのほうし_apply_ailment_to_defender,
            ),
        }
    ),
    "きりばらい": MoveData(
        type="ひこう",
        category="変化",
        pp=15,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.きりばらい_modify_defender_stats,
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
                h.きんぞくおん_modify_defender_stats,
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

        target="field",
    ),
    "くろいきり": MoveData(
        type="こおり",
        category="変化",
        pp=30,

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

        labels=["heal"],
    ),
    "こうそくいどう": MoveData(
        type="エスパー",
        category="変化",
        pp=30,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.こうそくいどう_modify_attacker_stats,
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

    ),
    "コスモパワー": MoveData(
        type="エスパー",
        category="変化",
        pp=20,

    ),
    "コットンガード": MoveData(
        type="くさ",
        category="変化",
        pp=10,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.コットンガード_modify_attacker_stats,
            )
        }
    ),
    "このゆびとまれ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,

        priority=2,
    ),
    "こらえる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,

        priority=4,
    ),
    "こわいかお": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.こわいかお_modify_defender_stats,
            )
        }
    ),
    "さいきのいのり": MoveData(
        type="ノーマル",
        category="変化",
        pp=0,

        labels=["heal"],
    ),
    "サイコフィールド": MoveData(
        type="エスパー",
        category="変化",
        pp=10,

        target="field",
    ),
    "サイドチェンジ": MoveData(
        type="エスパー",
        category="変化",
        pp=15,

        priority=2,
    ),
    "さいはい": MoveData(
        type="エスパー",
        category="変化",
        pp=15,

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

    ),
    "さむいギャグ": MoveData(
        type="こおり",
        category="変化",
        pp=10,

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

        labels=["heal"],
    ),
    "しっぽきり": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,

    ),
    "しっぽをふる": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.しっぽをふる_modify_defender_stats,
            )
        }
    ),
    "じばそうさ": MoveData(
        type="でんき",
        category="変化",
        pp=20,

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

        labels=["heal"],
    ),
    "じゅうでん": MoveData(
        type="でんき",
        category="変化",
        pp=20,

    ),
    "じゅうりょく": MoveData(
        type="エスパー",
        category="変化",
        pp=5,

        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.じゅうりょく_activate_global_field,
            ),
        }
    ),
    "しょうりのまい": MoveData(
        type="かくとう",
        category="変化",
        pp=10,

        labels=["dance"],
    ),
    "しろいきり": MoveData(
        type="こおり",
        category="変化",
        pp=30,

        target="field",
    ),
    "しんぴのまもり": MoveData(
        type="ノーマル",
        category="変化",
        pp=25,

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

        target="field",
    ),
    "すなあつめ": MoveData(
        type="じめん",
        category="変化",
        pp=5,

        labels=["heal"],
    ),
    "すなあらし": MoveData(
        type="いわ",
        category="変化",
        pp=10,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.すなあらし_activate_weather,
            ),
        }
    ),
    "すなかけ": MoveData(
        type="じめん",
        category="変化",
        pp=15,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.すなかけ_modify_defender_stats,
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

        priority=4,
        target="self",

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.スレッドトラップ_apply_volatile_to_attacker,
            ),
        }
    ),
    "せいちょう": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,

    ),
    "ソウルビート": MoveData(
        type="ドラゴン",
        category="変化",
        pp=100,

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
                h.タールショット_apply_volatile_to_defender,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.タールショット_modify_defender_stats,
            )
        }
    ),
    "たくわえる": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,

        handlers={
        }
    ),
    "たてこもる": MoveData(
        type="はがね",
        category="変化",
        pp=10,

    ),
    "タマゴうみ": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,

        labels=["heal"],
    ),
    "ちいさくなる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.ちいさくなる_apply,
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

    ),
    "つめとぎ": MoveData(
        type="あく",
        category="変化",
        pp=15,

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

    ),
    "テクスチャー２": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,

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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.てっぺき_modify_attacker_stats,
            )
        }
    ),
    "テレポート": MoveData(
        type="エスパー",
        category="変化",
        pp=20,

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

        priority=4,
        target="self",

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.トーチカ_apply_volatile_to_attacker,
            ),
        }
    ),
    "とおぼえ": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,

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
                h.どくどく_apply_ailment_to_defender,
            ),
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.どくのこな_apply_ailment_to_defender,
            ),
        }
    ),
    "どくびし": MoveData(
        type="どく",
        category="変化",
        pp=20,

        target="field",
    ),
    "とぐろをまく": MoveData(
        type="どく",
        category="変化",
        pp=20,

    ),
    "とける": MoveData(
        type="どく",
        category="変化",
        pp=20,

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

        priority=-7,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.トリックルーム_activate_global_field,
            ),
        }
    ),
    "ドわすれ": MoveData(
        type="エスパー",
        category="変化",
        pp=20,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.ドわすれ_modify_attacker_stats,
            )
        }
    ),
    "ないしょばなし": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,

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

    ),
    "なきごえ": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        accuracy=100,
        labels=["sound"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.なきごえ_modify_defender_stats,
            )
        }
    ),
    "なまける": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,

        labels=["heal"],
    ),
    "なみだめ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.なみだめ_modify_defender_stats,
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

        priority=4,
    ),
    "にほんばれ": MoveData(
        type="ほのお",
        category="変化",
        pp=5,

        target="field",
    ),
    "にらみつける": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.にらみつける_modify_defender_stats,
            )
        }
    ),
    "ねがいごと": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,

        target="field",
        labels=["heal"],
    ),
    "ねごと": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,

        labels=["non_encore", "non_negoto"],
    ),
    "ねばねばネット": MoveData(
        type="むし",
        category="変化",
        pp=20,

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

        labels=["heal"],
    ),
    "ねをはる": MoveData(
        type="くさ",
        category="変化",
        pp=20,

    ),
    "のみこむ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,

        labels=["heal"],
    ),
    "のろい": MoveData(
        type="ゴースト",
        category="変化",
        pp=10,

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

    ),
    "ハッピータイム": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,

    ),
    "バトンタッチ": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,

    ),
    "はねやすめ": MoveData(
        type="ひこう",
        category="変化",
        pp=5,

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

    ),
    "ファストガード": MoveData(
        type="かくとう",
        category="変化",
        pp=15,

        priority=3,
    ),
    "ふういん": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.ふういん_apply_volatile_to_attacker,
            ),
        }
    ),
    "フェアリーロック": MoveData(
        type="フェアリー",
        category="変化",
        pp=10,

    ),
    "フェザーダンス": MoveData(
        type="ひこう",
        category="変化",
        pp=15,
        accuracy=100,
        labels=["dance"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.フェザーダンス_modify_defender_stats,
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
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                h.on_blow_apply,
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

        labels=["heal"],
    ),
    "ふるいたてる": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,

    ),
    "ブレイブチャージ": MoveData(
        type="エスパー",
        category="変化",
        pp=15,

    ),
    "へびにらみ": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.へびにらみ_apply_ailment_to_defender,
            ),
        }
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

    ),
    "ほえる": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,

        priority=-6,
        labels=["sound"],
    ),
    "ほおばる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,

    ),
    "ほたるび": MoveData(
        type="むし",
        category="変化",
        pp=20,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.ほたるび_modify_attacker_stats,
            )
        }
    ),
    "ほろびのうた": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,

        labels=["sound"],
    ),
    "まきびし": MoveData(
        type="じめん",
        category="変化",
        pp=20,

        target="field",
    ),
    "マジックルーム": MoveData(
        type="エスパー",
        category="変化",
        pp=10,

        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.マジックルーム_activate_global_field,
            ),
        }
    ),
    "まねっこ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,

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

        priority=4,
        target="self",

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.まもる_apply_volatile_to_attacker,
            ),
        }
    ),
    "まるくなる": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.まるくなる_apply,
            )
        }
    ),
    "みかづきのいのり": MoveData(
        type="エスパー",
        category="変化",
        pp=5,

        labels=["heal"],
    ),
    "みかづきのまい": MoveData(
        type="エスパー",
        category="変化",
        pp=10,

        labels=["dance", "heal"],
    ),
    "みがわり": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,

        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                h.みがわり_check,
                priority=100,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.みがわり_apply,
            )
        }
    ),
    "みきり": MoveData(
        type="かくとう",
        category="変化",
        pp=5,

        priority=4,
        target="self",

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.みきり_apply_volatile_to_attacker,
            ),
        }
    ),
    "ミストフィールド": MoveData(
        type="フェアリー",
        category="変化",
        pp=10,

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


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.みちづれ_apply_volatile_to_attacker,
            ),
        }
    ),
    "ミラータイプ": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,

    ),
    "ミルクのみ": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,

        labels=["heal"],
    ),
    "みをけずる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,

    ),
    "めいそう": MoveData(
        type="エスパー",
        category="変化",
        pp=20,

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

        target="field",
    ),
    "ゆびをふる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,

        labels=["non_negoto"],
    ),
    "リサイクル": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,

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

    ),
    "りゅうのまい": MoveData(
        type="ドラゴン",
        category="変化",
        pp=20,

        labels=["dance"],
    ),
    "ロックオン": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.ロックオン_apply_volatile_to_defender,
            ),
        }
    ),
    "ロックカット": MoveData(
        type="いわ",
        category="変化",
        pp=20,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.ロックカット_modify_attacker_stats,
            )
        }
    ),
    "ワイドガード": MoveData(
        type="いわ",
        category="変化",
        pp=10,

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


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.わるだくみ_modify_attacker_stats,
            )
        }
    ),
    "ワンダールーム": MoveData(
        type="エスパー",
        category="変化",
        pp=10,

        target="field",
        labels=[],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.ワンダールーム_activate_global_field,
            ),
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
        priority=4,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                h.キングシールド_apply_volatile_to_attacker,
            ),
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
