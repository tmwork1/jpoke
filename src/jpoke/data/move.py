"""技データ定義モジュール。

Note:
    このモジュール内の技定義はMOVES辞書内で五十音順に配置されています。
"""
from jpoke.enums import Event
from jpoke.handlers import move as h
from jpoke.handlers import move_attack as ha
from jpoke.handlers import move_status as hs
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
        labels=["contact", "non_encore", "non_onnen"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.わるあがき_self_damage,
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha._3ぼんのや_apply_volatile_to_defender,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.Gのちから_modify_defender_stats,
            )
        }
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
                 ha.アームハンマー_modify_attacker_stats,
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
                ha.アイアンテール_modify_defender_stats,
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
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アイアンヘッド_apply_volatile_to_defender,
            )
        }
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
                ha.アイスハンマー_modify_attacker_stats,
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
                ha.アクアステップ_modify_attacker_stats,
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アクアブレイク_modify_defender_stats,
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
    "アフロブレイク": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=120,
        accuracy=100,
        labels=["contact", "recoil"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アフロブレイク_recoil,
            )
        }
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
                lambda b, c, v: h.charge_into_volatile(b, c, v, "あなをほる"),
            ),
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
            Event.ON_HIT: h.MoveHandler(
                ha.あばれる_apply,
            ),
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
                ha.half_damage,
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.いじげんラッシュ_modify_attacker_stats,
            )
        }
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いわくだき_modify_defender_stats,
            )
        }
    ),
    "いわなだれ": MoveData(
        type="いわ",
        category="物理",
        pp=10,
        power=75,
        accuracy=90,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いわなだれ_apply_volatile_to_defender,
            )
        }
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
                ha.インファイト_modify_attacker_stats,
            )
        }
    ),
    "ウェーブタックル": MoveData(
        type="みず",
        category="物理",
        pp=10,
        power=120,
        accuracy=100,
        labels=["contact", "recoil"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ウェーブタックル_recoil,
            )
        }
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
        labels=["contact", "recoil"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ウッドハンマー_recoil,
            )
        }
    ),
    "ウッドホーン": MoveData(
        type="くさ",
        category="物理",
        pp=10,
        power=75,
        accuracy=100,

        labels=["contact", "heal"],
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.ウッドホーン_heal_attacker)
        }
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
                ha.オーラぐるま_check_move_type,
            ),
        },
    ),
    "おしゃべり": MoveData(
        type="ひこう",
        category="特殊",
        pp=15,
        power=65,
        accuracy=100,
        labels=["sound", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.おしゃべり_apply_confusion_to_defender,
            )
        }
    ),
    "おどろかす": MoveData(
        type="ゴースト",
        category="物理",
        pp=15,
        power=30,
        accuracy=100,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.おどろかす_apply_volatile_to_defender,
            )
        }
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
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かえんぐるま_apply_ailment_to_defender,
            )
        }
    ),
    "かえんだん": MoveData(
        type="ほのお",
        category="特殊",
        pp=15,
        power=75,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かえんだん_apply_ailment_to_defender,
            )
        }
    ),
    "かえんボール": MoveData(
        type="ほのお",
        category="物理",
        pp=5,
        power=120,
        accuracy=90,
        labels=["bullet", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かえんボール_apply_ailment_to_defender,
            )
        }
    ),
    "かかとおとし": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=120,
        accuracy=90,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かかとおとし_apply_confusion_to_defender,
            ),
            Event.ON_MISS: h.MoveHandler(
                ha.かかとおとし_crash,
            ),
        }
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
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かみくだく_modify_defender_stats,
            )
        }
    ),
    "かみつく": MoveData(
        type="あく",
        category="物理",
        pp=25,
        power=60,
        accuracy=100,
        labels=["bite", "contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かみつく_apply_volatile_to_defender,
            )
        }
    ),
    "かみなりのキバ": MoveData(
        type="でんき",
        category="物理",
        pp=15,
        power=65,
        accuracy=95,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: [
                h.MoveHandler(ha.かみなりのキバ_apply_ailment_to_defender),
                h.MoveHandler(ha.かみなりのキバ_apply_volatile_to_defender),
            ]
        }
    ),
    "かみなりパンチ": MoveData(
        type="でんき",
        category="物理",
        pp=15,
        power=75,
        accuracy=100,
        labels=["contact", "punch", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かみなりパンチ_apply_ailment_to_defender,
            )
        }
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
                ha.がむしゃら_modify_damage,
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
                ha.ガリョウテンセイ_modify_attacker_stats,
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.がんせきふうじ_modify_defender_stats,
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
                ha.きあいパンチ_check_move,
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
        labels=["contact", "heal"],
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.きゅうけつ_heal_attacker)
        }
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
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.キラースピン_apply_ailment_to_defender,
            )
        }
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
            Event.ON_HIT: h.MoveHandler(ha.pivot)
        }
    ),
    "くさわけ": MoveData(
        type="くさ",
        category="物理",
        pp=20,
        power=50,
        accuracy=100,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.くさわけ_modify_attacker_stats,
            )
        }
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
    "グロウパンチ": MoveData(
        type="かくとう",
        category="物理",
        pp=40,
        power=40,
        accuracy=100,
        labels=["contact", "punch", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.グロウパンチ_modify_attacker_stats,
            )
        }
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
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.クロスポイズン_apply_ailment_to_defender,
            )
        }
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
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.こうそくスピン_modify_attacker_stats,
            )
        }
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
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.こおりのキバ_apply_flinch_or_freeze,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ゴッドバード_apply_volatile_to_defender,
            )
        }
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
                ha.コメットパンチ_modify_attacker_stats,
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
        handlers={
            Event.ON_MISS: h.MoveHandler(
                ha.サンダーダイブ_crash,
            ),
        }
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シェルブレード_modify_defender_stats,
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
    "じごくぐるま": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=80,
        accuracy=80,
        labels=["contact", "recoil"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.じごくぐるま_recoil,
            )
        }
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
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.したでなめる_apply_ailment_to_defender,
            )
        }
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.じならし_modify_defender_stats,
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
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.しねんのずつき_apply_volatile_to_defender,
            )
        }
    ),
    "じばく": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=200,
        accuracy=100,
        labels=["explosion"],
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.じばく_pay_hp,
                subject_spec="attacker:self",
            ),
        }
    ),
    "しめつける": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=15,
        accuracy=85,
        labels=["contact"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        }
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
        labels=["contact", "unprotectable"],
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                lambda b, c, v: h.charge_into_volatile(b, c, v, "シャドーダイブ"),
            ),
        }
    ),
    "シャドーパンチ": MoveData(
        type="ゴースト",
        category="物理",
        pp=20,
        power=60,

        labels=["contact", "punch"],
    ),
    "じゃどくのくさり": MoveData(
        type="どく",
        category="物理",
        pp=10,
        power=100,
        accuracy=100,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.じゃどくのくさり_apply_ailment_to_defender,
            )
        }
    ),
    "じゃれつく": MoveData(

        type="フェアリー",
        category="物理",
        pp=10,
        power=90,
        accuracy=90,

        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.じゃれつく_modify_defender_stats,
            )
        }
    ),
    "じわれ": MoveData(
        type="じめん",
        category="物理",
        pp=5,
        accuracy=30,
        labels=["ohko"],
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.ohko_damage,
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
        multi_hit={
            "min": 3,
            "max": 3,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
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

        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ずつき_apply_volatile_to_defender,
            )
        }
    ),
    "すてみタックル": MoveData(
        type="ノーマル",
        category="物理",
        pp=15,
        power=120,
        accuracy=100,
        labels=["contact", "recoil"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.すてみタックル_recoil,
            )
        }
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
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        }
    ),
    "スパーク": MoveData(

        type="でんき",
        category="物理",
        pp=20,
        power=65,
        accuracy=100,

        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.スパーク_apply_ailment_to_defender,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.せいなるほのお_apply_ailment_to_defender,
            )
        }
    ),
    "ソウルクラッシュ": MoveData(

        type="フェアリー",
        category="物理",
        pp=15,
        power=75,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ソウルクラッシュ_modify_defender_stats,
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
                lambda b, c, v: h.charge_into_volatile(b, c, v, "そらをとぶ"),
            ),
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
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.だいばくはつ_pay_hp,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ダークファイア": MoveData(
        # TODO : 本編に登場しないのですべての文書から削除
        type="ゴースト",
        category="特殊",
        pp=5,
        power=135,
        accuracy=85,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ダークファイア_apply_ailment_to_defender,
            )
        }
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
                lambda b, c, v: h.charge_into_volatile(b, c, v, "ダイビング"),
            ),
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ダイヤストーム_modify_attacker_stats,
            )
        }
    ),
    "たきのぼり": MoveData(

        type="みず",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,

        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.たきのぼり_apply_volatile_to_defender,
            )
        }
    ),
    "ダストシュート": MoveData(

        type="どく",
        category="物理",
        pp=5,
        power=120,
        accuracy=80,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ダストシュート_apply_ailment_to_defender,
            )
        }
    ),
    "ダブルニードル": MoveData(
        type="むし",
        category="物理",
        pp=20,
        power=25,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ダブルニードル_apply_ailment_to_defender,
            )
        }
    ),
    "ダブルパンツァー": MoveData(
        type="はがね",
        category="物理",
        pp=10,
        power=50,
        accuracy=100,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ダブルパンツァー_apply_volatile_to_defender,
            )
        }
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
                ha.level_fixed_damage,
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
                ha.ohko_damage,
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.つららおとし_apply_volatile_to_defender,
            )
        }
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
    "デスウイング": MoveData(
        type="ひこう",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,
        labels=["contact", "heal"],
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.デスウイング_heal_attacker)
        }
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

        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どくづき_apply_ailment_to_defender,
            )
        }
    ),
    "どくどくのキバ": MoveData(

        type="どく",
        category="物理",
        pp=15,
        power=50,
        accuracy=100,

        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どくどくのキバ_apply_ailment_to_defender,
            )
        }
    ),
    "どくばり": MoveData(

        type="どく",
        category="物理",
        pp=35,
        power=15,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どくばり_apply_ailment_to_defender,
            )
        }
    ),
    "どくばりセンボン": MoveData(

        type="どく",
        category="物理",
        pp=10,
        power=60,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どくばりセンボン_apply_ailment_to_defender,
            )
        }
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
        labels=["contact", "recoil"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.とっしん_recoil,
            )
        }
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.とびかかる_modify_defender_stats,
            )
        }
    ),
    "とびげり": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=85,
        accuracy=90,
        labels=["contact"],
        handlers={
            Event.ON_MISS: h.MoveHandler(
                ha.とびげり_crash,
            ),
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.とびつく_modify_defender_stats,
            )
        }
    ),
    "とびはねる": MoveData(

        type="ひこう",
        category="物理",
        pp=5,
        power=85,
        accuracy=85,

        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.とびはねる_apply_ailment_to_defender,
            )
        }
    ),
    "とびひざげり": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=130,
        accuracy=90,
        labels=["contact"],
        handlers={
            Event.ON_MISS: h.MoveHandler(
                ha.とびひざげり_crash,
            ),
        }
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
        labels=["minimize", "contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ドラゴンダイブ_apply_volatile_to_defender,
            )
        }
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ドラムアタック_modify_defender_stats,
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
        labels=["contact", "punch", "heal"],
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.ドレインパンチ_heal_attacker)
        }
    ),
    "トロピカルキック": MoveData(
        type="くさ",
        category="物理",
        pp=15,
        power=70,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.トロピカルキック_modify_defender_stats,
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
                ha.どろぼう_steal_item,
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
            Event.ON_HIT: h.MoveHandler(ha.pivot)
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
    "ニードルアーム": MoveData(
        type="くさ",
        category="物理",
        pp=15,
        power=60,
        accuracy=100,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ニードルアーム_apply_volatile_to_defender,
            )
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
                ha.ニトロチャージ_modify_attacker_stats,
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
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねこだまし_apply_volatile_to_defender,
            )
        }
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
        labels=["minimize", "contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.のしかかり_apply_ailment_to_defender,
            )
        }
    ),
    "ハートスタンプ": MoveData(
        type="エスパー",
        category="物理",
        pp=25,
        power=60,
        accuracy=100,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ハートスタンプ_apply_volatile_to_defender,
            )
        }
    ),
    "ハードプレス": MoveData(
        type="はがね",
        category="物理",
        pp=10,
        power=1,
        accuracy=100,
        labels=["contact"],
    ),
    "ハードローラー": MoveData(
        type="ノーマル",
        category="物理",
        pp=10,
        power=100,
        accuracy=95,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ハードローラー_apply_volatile_to_defender,
            )
        }
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

        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.はいよるいちげき_modify_defender_stats,
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
                ha.ばかぢから_modify_attacker_stats,
            )
        }
    ),
    "はがねのつばさ": MoveData(
        type="はがね",
        category="物理",
        pp=25,
        power=70,
        accuracy=90,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.はがねのつばさ_modify_attacker_stats,
            )
        }
    ),
    "ばくれつパンチ": MoveData(

        type="かくとう",
        category="物理",
        pp=5,
        power=100,
        accuracy=50,

        labels=["contact", "punch", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ばくれつパンチ_apply_confusion_to_defender,
            )
        }
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
                ha.ohko_damage,
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
                ha.はたきおとす_power,
            ),
            Event.ON_HIT: h.MoveHandler(
                ha.はたきおとす_remove_item,
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

        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.はっけい_apply_ailment_to_defender,
            )
        }
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
                ha.はやてがえし_try_move,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.はやてがえし_apply,
            ),
        }
    ),
    "バリアーラッシュ": MoveData(
        type="エスパー",
        category="物理",
        pp=10,
        power=70,
        accuracy=90,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.バリアーラッシュ_modify_attacker_stats,
            )
        }
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
    "ひっさつまえば": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=120,
        accuracy=90,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ひっさつまえば_apply_volatile_to_defender,
            )
        }
    ),
    "ひょうざんおろし": MoveData(

        type="こおり",
        category="物理",
        pp=10,
        power=100,
        accuracy=85,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ひょうざんおろし_apply_volatile_to_defender,
            )
        }
    ),
    "ピヨピヨパンチ": MoveData(
        type="ノーマル",
        category="物理",
        pp=15,
        power=70,
        accuracy=100,
        labels=["contact", "punch", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ピヨピヨパンチ_apply_confusion_to_defender,
            )
        }
    ),
    "ビックリヘッド": MoveData(
        type="ノーマル",
        category="物理",
        pp=5,
        power=130,
        accuracy=100,
        labels=["contact"],
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.ビックリヘッド_pay_hp,
                subject_spec="attacker:self",
            ),
        }
    ),
    "びりびりちくちく": MoveData(

        type="でんき",
        category="物理",
        pp=10,
        power=80,
        accuracy=100,

        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.びりびりちくちく_apply_volatile_to_defender,
            )
        }
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

        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.フェイタルクロー_apply_ailment_to_defender,
            )
        }
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
        labels=["contact", "punch", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ぶちかまし_modify_attacker_stats,
            )
        }
    ),
    "ふみつけ": MoveData(

        type="ノーマル",
        category="物理",
        pp=20,
        power=65,
        accuracy=100,
        labels=["minimize", "contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ふみつけ_apply_volatile_to_defender,
            )
        }
    ),
    "ふわふわフォール": MoveData(
        type="フェアリー",
        category="物理",
        pp=15,
        power=70,
        accuracy=95,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ふわふわフォール_apply_volatile_to_defender,
            )
        }
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

        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.フリーズボルト_apply_ailment_to_defender,
            )
        }
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
        labels=["contact", "recoil", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.フレアドライブ_recoil,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.フレアドライブ_apply_ailment_to_defender,
            ),
        }
    ),
    "ブレイククロー": MoveData(

        type="ノーマル",
        category="物理",
        pp=10,
        power=75,
        accuracy=95,

        labels=["contact"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ブレイククロー_modify_defender_stats,
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
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ブレイズキック_apply_ailment_to_defender,
            )
        }
    ),
    "ブレイブバード": MoveData(
        type="ひこう",
        category="物理",
        pp=15,
        power=120,
        accuracy=100,
        labels=["contact", "recoil"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ブレイブバード_recoil,
            )
        }
    ),
    "Vジェネレート": MoveData(
        type="ほのお",
        category="物理",
        pp=5,
        power=180,
        accuracy=80,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.Vジェネレート_modify_attacker_stats,
            )
        }
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
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ホイールスピン_modify_attacker_stats,
            )
        }
    ),
    "ポイズンアクセル": MoveData(
        type="どく",
        category="物理",
        pp=20,
        power=70,
        accuracy=100,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ポイズンアクセル_apply_ailment_to_defender,
            )
        }
    ),
    "ポイズンテール": MoveData(

        type="どく",
        category="物理",
        pp=25,
        power=50,
        accuracy=100,
        critical_rank=1,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ポイズンテール_apply_ailment_to_defender,
            )
        }
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
                ha.どろぼう_steal_item,
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
                ha.ほっぺすりすり_apply_ailment_to_defender,
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
    "ホネこんぼう": MoveData(
        type="じめん",
        category="物理",
        pp=10,
        power=100,
        accuracy=85,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ホネこんぼう_apply_volatile_to_defender,
            )
        }
    ),
    "ほのおのキバ": MoveData(
        type="ほのお",
        category="物理",
        pp=15,
        power=65,
        accuracy=95,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ほのおのキバ_apply_flinch_or_burn,
            )
        }
    ),
    "ほのおのパンチ": MoveData(
        type="ほのお",
        category="物理",
        pp=15,
        power=75,
        accuracy=100,
        labels=["contact", "punch", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ほのおのパンチ_apply_ailment_to_defender,
            )
        }
    ),
    "ほのおのムチ": MoveData(

        type="ほのお",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,

        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ほのおのムチ_modify_defender_stats,
            )
        }
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
        labels=["contact", "recoil", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ボルテッカー_recoil,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ボルテッカー_apply_ailment_to_defender,
            )
        }
    ),
    "まきつく": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=15,
        accuracy=90,
        labels=["contact"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        }
    ),
    "まわしげり": MoveData(
        type="かくとう",
        category="物理",
        pp=10,
        power=85,
        accuracy=90,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.まわしげり_apply_volatile_to_defender,
            )
        }
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

        labels=["contact", "slash", "heal"],
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.むねんのつるぎ_heal_attacker)
        }
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
                ha.メタルクロー_modify_attacker_stats,
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
        labels=["contact", "recoil"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.もろはのずつき_recoil,
            )
        }
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

        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.らいげき_apply_ailment_to_defender,
            )
        }
    ),
    "らいめいげり": MoveData(

        type="かくとう",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,

        labels=["contact"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.らいめいげり_modify_defender_stats,
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
        labels=["contact", "punch", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.れいとうパンチ_apply_ailment_to_defender,
            )
        }
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ローキック_modify_defender_stats,
            )
        }
    ),
    "ロッククライム": MoveData(
        type="ノーマル",
        category="物理",
        pp=20,
        power=90,
        accuracy=85,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ロッククライム_apply_confusion_to_defender,
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ワイドブレイカー_modify_defender_stats,
            )
        }
    ),
    "ワイルドボルト": MoveData(
        type="でんき",
        category="物理",
        pp=15,
        power=90,
        accuracy=100,
        labels=["contact", "recoil"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ワイルドボルト_recoil,
            )
        }
    ),
    "10まんボルト": MoveData(

        type="でんき",
        category="特殊",
        pp=15,
        power=90,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha._10まんボルト_apply_ailment_to_defender,
            )
        }
    ),
    "アーマーキャノン": MoveData(

        type="ほのお",
        category="特殊",
        pp=5,
        power=120,
        accuracy=100,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アーマーキャノン_modify_attacker_stats,
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

        labels=["pulse", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.あくのはどう_apply_volatile_to_defender,
            )
        }
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アシッドボム_modify_defender_stats,
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
    "あやしいかぜ": MoveData(
        type="ゴースト",
        category="特殊",
        pp=15,
        power=40,
        accuracy=100,
        labels=["wind", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.あやしいかぜ_modify_attacker_stats,
            )
        }
    ),
    "あわ": MoveData(
        type="みず",
        category="特殊",
        pp=30,
        power=40,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.あわ_modify_defender_stats,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: [
                h.MoveHandler(
                    ha.いてつくしせん_modify_defender_stats,
                ),
                h.MoveHandler(
                    ha.いてつくしせん_apply_ailment_to_defender,
                ),
            ]
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
                ha.いのちがけ_pay_hp,
                subject_spec="attacker:self",
            ),
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.いのちがけ_modify_damage,
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

        labels=["sound", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いびき_apply_volatile_to_defender,
            )
        }
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
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.うらみつらみ_modify_defender_stats,
            )
        }
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

        labels=["slash", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.エアスラッシュ_apply_volatile_to_defender,
            )
        }
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.エナジーボール_modify_defender_stats,
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.エレキネット_modify_defender_stats,
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
                ha.オーバーヒート_modify_attacker_stats,
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.オーラウイング_modify_attacker_stats,
            )
        }
    ),
    "オーロラビーム": MoveData(

        type="こおり",
        category="特殊",
        pp=20,
        power=65,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.オーロラビーム_modify_defender_stats,
            )
        }
    ),
    "かえんほうしゃ": MoveData(
        type="ほのお",
        category="特殊",
        pp=15,
        power=90,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かえんほうしゃ_apply_ailment_to_defender,
            )
        }
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
                ha.half_damage,
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
        labels=["bullet", "heal"],
    ),
    "からみつく": MoveData(
        type="むし",
        category="特殊",
        pp=20,
        power=55,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.からみつく_modify_defender_stats,
            )
        }
    ),
    "かみなり": MoveData(

        type="でんき",
        category="特殊",
        pp=10,
        power=110,
        accuracy=70,

        labels=["secondary_effect"],
        handlers={
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
                ha.かみなり_accuracy,
                subject_spec="attacker:self"
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かみなり_apply_ailment_to_defender,
            ),
        }
    ),
    "かみなりあらし": MoveData(
        type="でんき",
        category="特殊",
        pp=10,
        power=100,
        accuracy=80,
        labels=["wind", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かみなりあらし_apply_ailment_to_defender,
            )
        }
    ),
    "きあいだま": MoveData(

        type="かくとう",
        category="特殊",
        pp=5,
        power=120,
        accuracy=70,

        labels=["bullet", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.きあいだま_modify_defender_stats,
            )
        }
    ),
    "ギガドレイン": MoveData(
        type="くさ",
        category="特殊",
        pp=10,
        power=75,
        accuracy=100,
        labels=["heal"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ギガドレイン_heal_attacker,
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
    "ぎんいろのかぜ": MoveData(
        type="こおり",
        category="特殊",
        pp=5,
        power=60,
        accuracy=100,
        labels=["wind", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ぎんいろのかぜ_modify_attacker_stats,
            )
        }
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
    "グラスミキサー": MoveData(
        type="くさ",
        category="特殊",
        pp=10,
        power=60,
        accuracy=55,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.グラスミキサー_modify_defender_stats,
            )
        }
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
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.クロロブラスト_pay_hp,
                subject_spec="attacker:self",
            ),
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.げんしのちから_modify_attacker_stats,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.コールドフレア_apply_ailment_to_defender,
            )
        }
    ),
    "ゴールドラッシュ": MoveData(
        type="はがね",
        category="特殊",
        pp=5,
        power=120,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ゴールドラッシュ_modify_attacker_stats,
            )
        }
    ),
    "こがらしあらし": MoveData(
        type="ひこう",
        category="特殊",
        pp=10,
        power=100,
        accuracy=80,
        labels=["wind", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.こがらしあらし_modify_defender_stats,
            )
        }
    ),
    "こごえるかぜ": MoveData(

        type="こおり",
        category="特殊",
        pp=15,
        power=55,
        accuracy=95,

        labels=["wind"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.こごえるかぜ_modify_defender_stats,
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.こごえるせかい_modify_defender_stats,
            )
        }
    ),
    "こなゆき": MoveData(

        type="こおり",
        category="特殊",
        pp=25,
        power=40,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.こなゆき_apply_ailment_to_defender,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.サイケこうせん_apply_confusion_to_defender,
            )
        }
    ),
    "サイコキネシス": MoveData(

        type="エスパー",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.サイコキネシス_modify_defender_stats,
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
                ha.サイコブースト_modify_attacker_stats,
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
            Event.ON_HIT: h.MoveHandler(
                ha.さわぐ_apply,
            ),
        }
    ),
    "サンダープリズン": MoveData(
        type="でんき",
        category="特殊",
        pp=15,
        power=80,
        accuracy=90,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        }
    ),
    "シードフレア": MoveData(

        type="くさ",
        category="特殊",
        pp=5,
        power=120,
        accuracy=85,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シードフレア_modify_defender_stats,
            )
        }
    ),
    "シェルアームズ": MoveData(
        # TODO : 補正込み実数値でAのほうがCより高いときに物理技としてダメージ計算する効果を追加
        type="どく",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シェルアームズ_apply_ailment_to_defender,
            )
        }
    ),
    "シグナルビーム": MoveData(
        type="むし",
        category="特殊",
        pp=15,
        power=75,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シグナルビーム_apply_confusion_to_defender,
            )
        }
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
        labels=["heal", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.シャカシャカほう_heal_attacker),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シャカシャカほう_apply_ailment_to_defender,
            )
        }
    ),
    "シャドーボール": MoveData(

        type="ゴースト",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,

        labels=["bullet"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シャドーボール_modify_defender_stats,
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.じんつうりき_apply_volatile_to_defender,
            )
        }
    ),
    "しんぴのちから": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=70,
        accuracy=90,
        labels=["secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.しんぴのちから_modify_attacker_stats,
            )
        }
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
        labels=["heal"],
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.すいとる_heal_attacker)
        }
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
                ha.スケイルノイズ_modify_attacker_stats,
            )
        }
    ),
    "スチームバースト": MoveData(
        type="みず",
        category="特殊",
        pp=5,
        power=110,
        accuracy=95,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.スチームバースト_apply_ailment_to_defender,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.スモッグ_apply_ailment_to_defender,
            )
        }
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
                ha.ohko_damage,
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.だいちのちから_modify_defender_stats,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.だいもんじ_apply_ailment_to_defender,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.だくりゅう_modify_defender_stats,
            )
        }
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

        labels=["wind", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.たつまき_apply_volatile_to_defender,
            )
        }
    ),
    "チャージビーム": MoveData(

        type="でんき",
        category="特殊",
        pp=10,
        power=50,
        accuracy=90,

        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.チャージビーム_modify_attacker_stats,
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
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.てっていこうせん_pay_hp,
                subject_spec="attacker:self",
            ),
        }
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
                ha.テラバースト_modify_move_type,
            ),
            Event.ON_MODIFY_MOVE_CATEGORY: h.MoveHandler(
                ha.テラバースト_modify_move_category,
            ),
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.テラバースト_stellar_power,
            ),
            Event.ON_HIT: h.MoveHandler(
                ha.テラバースト_stellar_stat_drop,
            ),
        }
    ),
    "でんきショック": MoveData(

        type="でんき",
        category="特殊",
        pp=30,
        power=40,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.でんきショック_apply_ailment_to_defender,
            )
        }
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
        labels=["bullet", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.でんじほう_apply_ailment_to_defender,
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
        labels=["contact", "heal"],
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.ドレインキッス_heal_attacker)
        }
    ),
    "どろかけ": MoveData(

        type="じめん",
        category="特殊",
        pp=10,
        power=20,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どろかけ_modify_defender_stats,
            )
        }
    ),
    "ナイトバースト": MoveData(

        type="あく",
        category="特殊",
        pp=10,
        power=85,
        accuracy=95,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ナイトバースト_modify_defender_stats,
            )
        }
    ),
    "ナイトヘッド": MoveData(
        type="ゴースト",
        category="特殊",
        pp=15,
        power=0,
        accuracy=100,
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.level_fixed_damage,
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
        labels=["wind", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねっさのあらし_apply_ailment_to_defender,
            )
        }
    ),
    "ねっさのだいち": MoveData(
        type="じめん",
        category="特殊",
        pp=10,
        power=70,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねっさのだいち_apply_ailment_to_defender,
            )
        }
    ),
    "ねっとう": MoveData(
        type="みず",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねっとう_apply_ailment_to_defender,
            )
        }
    ),
    "ねっぷう": MoveData(
        type="ほのお",
        category="特殊",
        pp=10,
        power=95,
        accuracy=90,
        labels=["wind", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねっぷう_apply_ailment_to_defender,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねんりき_apply_confusion_to_defender,
            )
        }
    ),
    "バークアウト": MoveData(

        type="あく",
        category="特殊",
        pp=15,
        power=55,
        accuracy=95,

        labels=["sound"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.バークアウト_modify_defender_stats,
            )
        }
    ),
    "バーンアクセル": MoveData(
        type="ほのお",
        category="物理",
        pp=15,
        power=80,
        accuracy=100,
        labels=["contact", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.バーンアクセル_apply_ailment_to_defender,
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
        accuracy=100,
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                hs.はきだす_check_can_use,
                priority=30,
            ),
            Event.ON_BEGIN_MOVE: h.MoveHandler(
                hs.はきだす_set_power,
            ),
            Event.ON_HIT: h.MoveHandler(
                hs.はきだす_apply_after,
            ),
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.バブルこうせん_modify_defender_stats,
            )
        }
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
        labels=["heal"],
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.パラボラチャージ_heal_attacker)
        }
    ),
    "はめつのひかり": MoveData(
        type="ゴースト",
        category="特殊",
        pp=5,
        power=150,
        accuracy=100,
        labels=["recoil"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.はめつのひかり_recoil,
            )
        }
    ),
    "はるのあらし": MoveData(

        type="フェアリー",
        category="特殊",
        pp=5,
        power=100,
        accuracy=80,

        labels=["wind", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.はるのあらし_modify_defender_stats,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ひのこ_apply_ailment_to_defender,
            )
        }
    ),
    "ひゃっきやこう": MoveData(
        # TODO : 相手が状態異常のとき威力が2倍になる処理も実装
        type="ゴースト",
        category="特殊",
        pp=15,
        power=60,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ひゃっきやこう_apply_ailment_to_defender,
            )
        }
    ),
    "ひやみず": MoveData(

        type="みず",
        category="特殊",
        pp=20,
        power=50,
        accuracy=100,

        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ひやみず_modify_defender_stats,
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
        labels=["wind", "secondary_effect"],
        handlers={
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
                ha.ふぶき_accuracy,
                subject_spec="attacker:self"
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ふぶき_apply_ailment_to_defender,
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
        # TODO : こおり状態付与の追加効果はチャンピオンズから廃止
        # TODO : みずタイプに対して効果抜群になる処理を実装
        type="こおり",
        category="特殊",
        pp=20,
        power=70,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.フリーズドライ_apply_ailment_to_defender,
            )
        }
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
                ha.フルールカノン_modify_attacker_stats,
            )
        }
    ),
    "フレアソング": MoveData(
        type="ほのお",
        category="特殊",
        pp=10,
        power=80,
        accuracy=100,
        labels=["sound", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.フレアソング_modify_attacker_stats,
            )
        }
    ),
    "ふんえん": MoveData(
        type="ほのお",
        category="特殊",
        pp=15,
        power=80,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ふんえん_apply_ailment_to_defender,
            )
        }
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
                ha.ふしょくガス_remove_item,
            )
        }
    ),
    "ヘドロウェーブ": MoveData(

        type="どく",
        category="特殊",
        pp=10,
        power=95,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ヘドロウェーブ_apply_ailment_to_defender,
            )
        }
    ),
    "ヘドロこうげき": MoveData(

        type="どく",
        category="特殊",
        pp=20,
        power=65,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ヘドロこうげき_apply_ailment_to_defender,
            )
        }
    ),
    "ヘドロばくだん": MoveData(

        type="どく",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        labels=["bullet", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ヘドロばくだん_apply_ailment_to_defender,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ほうでん_apply_ailment_to_defender,
            )
        }
    ),
    "ぼうふう": MoveData(

        type="ひこう",
        category="特殊",
        pp=10,
        power=110,
        accuracy=70,
        labels=["wind", "secondary_effect"],
        handlers={
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
                ha.ぼうふう_accuracy,
                subject_spec="attacker:self"
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ぼうふう_apply_confusion_to_defender,
            )
        }
    ),
    "ほのおのうず": MoveData(
        type="ほのお",
        category="特殊",
        pp=15,
        power=35,
        accuracy=85,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        }
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
        labels=["dance", "secondary_effect"],
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ほのおのまい_modify_attacker_stats,
            )
        }
    ),
    "ボルトチェンジ": MoveData(
        type="でんき",
        category="特殊",
        pp=20,
        power=70,
        accuracy=100,
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.pivot)
        }
    ),
    "マグマストーム": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=100,
        accuracy=75,

    ),
    "マジカルアクセル": MoveData(
        type="エスパー",
        category="特殊",
        pp=10,
        power=100,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.マジカルアクセル_apply_confusion_to_defender,
            )
        }
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.マジカルフレイム_modify_defender_stats,
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.マッドショット_modify_defender_stats,
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
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        }
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
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.ミストバースト_pay_hp,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ミストボール": MoveData(

        type="エスパー",
        category="特殊",
        pp=5,
        power=95,
        accuracy=100,

        labels=["bullet"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ミストボール_modify_defender_stats,
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

        labels=["pulse", "secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.みずのはどう_apply_confusion_to_defender,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ムーンフォース_modify_defender_stats,
            )
        }
    ),
    "むしのさざめき": MoveData(

        type="むし",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,

        labels=["sound"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.むしのさざめき_modify_defender_stats,
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.むしのていこう_modify_defender_stats,
            )
        }
    ),
    "メガドレイン": MoveData(
        type="くさ",
        category="特殊",
        pp=15,
        power=40,
        accuracy=100,
        labels=["heal"],
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.メガドレイン_heal_attacker)
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.もえあがるいかり_apply_volatile_to_defender,
            )
        }
    ),
    "やきつくす": MoveData(
        type="ほのお",
        category="特殊",
        pp=15,
        power=60,
        accuracy=100,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.やきつくす_remove_berry,
            )
        }
    ),
    "ゆめくい": MoveData(
        type="エスパー",
        category="特殊",
        pp=15,
        power=100,
        accuracy=100,
        labels=["heal"],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ゆめくい_check_sleep,
            ),
            Event.ON_HIT: h.MoveHandler(ha.ゆめくい_heal_attacker)
        }
    ),
    "ようかいえき": MoveData(

        type="どく",
        category="特殊",
        pp=30,
        power=40,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ようかいえき_modify_defender_stats,
            )
        }
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ラスターカノン_modify_defender_stats,
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ラスターパージ_modify_defender_stats,
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
                ha.リーフストーム_modify_attacker_stats,
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
                ha.りゅうせいぐん_modify_attacker_stats,
            )
        }
    ),
    "りゅうのいぶき": MoveData(

        type="ドラゴン",
        category="特殊",
        pp=20,
        power=60,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.りゅうのいぶき_apply_ailment_to_defender,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.りんごさん_modify_defender_stats,
            )
        }
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
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ルミナコリジョン_modify_defender_stats,
            )
        }
    ),
    "れいとうビーム": MoveData(

        type="こおり",
        category="特殊",
        pp=10,
        power=90,
        accuracy=100,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.れいとうビーム_apply_ailment_to_defender,
            )
        }
    ),
    "れんごく": MoveData(
        type="ほのお",
        category="特殊",
        pp=5,
        power=100,
        accuracy=50,
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.れんごく_apply_ailment_to_defender,
            )
        }
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
        labels=["secondary_effect"],
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ワンダースチーム_apply_confusion_to_defender,
            )
        }
    ),
    # -------------------------
    # 変化技
    # -------------------------
    "アクアリング": MoveData(
        type="みず",
        category="変化",
        pp=20,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.アクアリング_apply,
            ),
        }
    ),
    "あくび": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.あくび_can_apply,
                priority=130,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あくび_apply,
            ),
        }
    ),
    "あくまのキッス": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=75,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あくまのキッス_apply_ailment_to_defender,
            ),
        }
    ),
    "あさのひざし": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        labels=["heal"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あさのひざし_heal_self,
            )
        }
    ),
    "あまいかおり": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あまいかおり_modify_defender_stats,
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
                hs.あまえる_modify_defender_stats,
            )
        }
    ),
    "あまごい": MoveData(
        type="みず",
        category="変化",
        pp=5,

        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あまごい_activate_weather,
            ),
        }
    ),
    "あやしいひかり": MoveData(
        type="ゴースト",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あやしいひかり_apply,
            ),
        }
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
        target="self",
    ),
    "アンコール": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        accuracy=100,
        labels=["non_encore"],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.アンコール_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.アンコール_apply,
            )
        }
    ),
    "いえき": MoveData(
        type="どく",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.いえき_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いえき_apply,
            ),
        }
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
                hs.いたみわけ_equalize_hp,
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
                hs.いちゃもん_apply,
            ),
        }
    ),
    "いとをはく": MoveData(
        type="むし",
        category="変化",
        pp=40,
        accuracy=95,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いとをはく_modify_defender_stats,
            ),
        }
    ),
    "いのちのしずく": MoveData(
        type="みず",
        category="変化",
        pp=10,
        labels=["heal"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いのちのしずく_heal_self,
            ),
        }
    ),
    "いばる": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        accuracy=85,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いばる_modify_defender_stats_and_apply_volatile,
            ),
        }
    ),
    "いやしのすず": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        labels=["sound"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやしのすず_cure_team_ailment,
            ),
        }
    ),
    "いやしのねがい": MoveData(
        type="エスパー",
        category="変化",
        pp=10,

        labels=["heal"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやしのねがい_faint_and_set_side_field,
            ),
        }
    ),
    "いやしのはどう": MoveData(
        type="エスパー",
        category="変化",
        pp=10,

        labels=["heal"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやしのはどう_heal_defender,
            ),
        }
    ),
    "いやなおと": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        accuracy=85,
        labels=["sound"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやなおと_modify_defender_stats,
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
                hs.うそなき_modify_defender_stats,
            )
        }
    ),
    "うたう": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        accuracy=55,
        labels=["sound"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.うたう_apply_ailment_to_defender,
            ),
        }
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
        accuracy=100,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.うらみ_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.うらみ_deplete_pp,
            ),
        }
    ),
    "エレキフィールド": MoveData(
        type="でんき",
        category="変化",
        pp=10,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.エレキフィールド_activate_terrain,
            ),
        }
    ),
    "えんまく": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.えんまく_modify_defender_stats,
            )
        }
    ),
    "おいかぜ": MoveData(
        type="ひこう",
        category="変化",
        pp=15,
        target="own_side",
        labels=["wind"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おいかぜ_set_side_field,
            ),
        }
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
        target="own_side",
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                hs.オーロラベール_check_weather,
                priority=30,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.オーロラベール_set_side_field,
            ),
        }
    ),
    "おかたづけ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(hs.おかたづけ_cleanup),
        }
    ),
    "おきみやげ": MoveData(
        type="あく",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おきみやげ_faint_and_modify_defender_stats,
            ),
        }
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おたけび_modify_defender_stats,
            ),
        }
    ),
    "おだてる": MoveData(
        type="あく",
        category="変化",
        pp=15,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おだてる_modify_defender_stats_and_apply_volatile,
            ),
        }
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
                hs.おにび_apply_ailment_to_defender,
            ),
        }
    ),
    "ガードシェア": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ガードシェア_equalize_stats,
            ),
        }
    ),
    "ガードスワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ガードスワップ_swap_ranks,
            ),
        }
    ),
    "かいでんぱ": MoveData(
        type="でんき",
        category="変化",
        pp=15,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.かいでんぱ_modify_defender_stats,
            ),
        }
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
                hs.かえんのまもり_apply,
            ),
        }
    ),
    "かげぶんしん": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.かげぶんしん_modify_attacker_stats,
            ),
        }
    ),
    "かたくなる": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.かたくなる_modify_attacker_stats,
            )
        }
    ),
    "かなしばり": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: [
                h.MoveHandler(
                    hs.かなしばり_can_apply,
                ),
                h.MoveHandler(
                    hs.かなしばり_apply,
                ),
            ],
        }
    ),
    "からにこもる": MoveData(
        type="みず",
        category="変化",
        pp=40,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.からにこもる_modify_attacker_stats,
            )
        }
    ),
    "からをやぶる": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.からをやぶる_modify_attacker_stats,
            ),
        }
    ),
    "きあいだめ": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.きあいだめ_apply,
            ),
        }
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
                hs.キノコのほうし_apply_ailment_to_defender,
            ),
        }
    ),
    "きりばらい": MoveData(
        type="ひこう",
        category="変化",
        pp=15,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.きりばらい_defog,
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
                hs.きんぞくおん_modify_defender_stats,
            )
        }
    ),
    "くすぐる": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.くすぐる_modify_defender_stats,
            ),
        }
    ),
    "グラスフィールド": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.グラスフィールド_activate_terrain,
            ),
        }
    ),
    "くろいきり": MoveData(
        type="こおり",
        category="変化",
        pp=30,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.くろいきり_reset_all_ranks,
            ),
        }
    ),
    "くろいまなざし": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.くろいまなざし_apply,
            ),
        }
    ),
    "こうごうせい": MoveData(
        type="くさ",
        category="変化",
        pp=5,
        labels=["heal"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あさのひざし_heal_self,
            )
        }
    ),
    "こうそくいどう": MoveData(
        type="エスパー",
        category="変化",
        pp=30,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.こうそくいどう_modify_attacker_stats,
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.コスモパワー_modify_attacker_stats,
            ),
        }
    ),
    "コットンガード": MoveData(
        type="くさ",
        category="変化",
        pp=10,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.コットンガード_modify_attacker_stats,
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
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.こらえる_apply,
            ),
        }
    ),
    "こわいかお": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.こわいかお_modify_defender_stats,
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.サイコフィールド_activate_terrain,
            ),
        }
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.さいみんじゅつ_apply_ailment_to_defender,
            ),
        }
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
        target="field",
        labels=["non_yubi"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.さむいギャグ_activate_weather_and_pivot,
            ),
        }
    ),
    "じこあんじ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.じこあんじ_copy_ranks,
            ),
        }
    ),
    "じこさいせい": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,

        labels=["heal"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.じこさいせい_heal_self,
            )
        }
    ),
    "しっぽきり": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.しっぽきり_check,
                priority=100,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.しっぽきり_apply,
            ),
        }
    ),
    "しっぽをふる": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.しっぽをふる_modify_defender_stats,
            )
        }
    ),
    "じばそうさ": MoveData(
        type="でんき",
        category="変化",
        pp=20,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.じばそうさ_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.じばそうさ_modify_attacker_stats,
            ),
        }
    ),
    "しびれごな": MoveData(
        type="くさ",
        category="変化",
        pp=30,
        accuracy=75,
        labels=["powder"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.しびれごな_apply_ailment_to_defender,
            ),
        }
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
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.じゅうでん_apply,
            ),
        }
    ),
    "じゅうりょく": MoveData(
        type="エスパー",
        category="変化",
        pp=5,

        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.じゅうりょく_activate_global_field,
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
        target="own_side",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.しんぴのまもり_set_side_field,
            ),
        }
    ),
    "シンプルビーム": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        accuracy=100,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.シンプルビーム_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.シンプルビーム_change_ability,
            ),
        }
    ),
    "スキルスワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
        labels=["bypass_substitute"],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.スキルスワップ_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.スキルスワップ_swap_ability,
            ),
        }
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.すてゼリフ_modify_defender_stats_and_pivot,
            ),
        }
    ),
    "ステルスロック": MoveData(
        type="いわ",
        category="変化",
        pp=20,

        target="foe_side",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ステルスロック_set_field,
            )
        }
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
                hs.すなあらし_activate_weather,
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
                hs.すなかけ_modify_defender_stats,
            )
        }
    ),
    "スピードスワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.スピードスワップ_swap_speed,
            ),
        }
    ),
    "すりかえ": MoveData(
        type="あく",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.すりかえ_swap_items,
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
                hs.スレッドトラップ_apply,
            ),
        }
    ),
    "せいちょう": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.せいちょう_modify_attacker_stats,
            ),
        }
    ),
    "ソウルビート": MoveData(
        type="ドラゴン",
        category="変化",
        pp=5,
        labels=["dance", "sound"],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ソウルビート_check,
                priority=100,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ソウルビート_pay_hp_and_modify_attacker_stats,
            ),
        }
    ),
    "そうでん": MoveData(
        type="でんき",
        category="変化",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.そうでん_apply,
            ),
        }
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
                hs.タールショット_apply,
            ),
        }
    ),
    "たくわえる": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                hs.たくわえる_check_can_use,
                priority=30,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.たくわえる_apply,
            ),
        }
    ),
    "たてこもる": MoveData(
        type="はがね",
        category="変化",
        pp=10,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.たてこもる_modify_attacker_stats,
            ),
        }
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
                hs.ちいさくなる_apply,
            )
        }
    ),
    "ちからをすいとる": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        accuracy=100,
        labels=["heal"],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ちからをすいとる_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ちからをすいとる_apply,
            ),
        }
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ちょうのまい_modify_attacker_stats,
            ),
        }
    ),
    "ちょうはつ": MoveData(
        type="あく",
        category="変化",
        pp=20,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ちょうはつ_apply,
            ),
        }
    ),
    "つきのひかり": MoveData(
        type="フェアリー",
        category="変化",
        pp=5,
        labels=["heal"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あさのひざし_heal_self,
            )
        }
    ),
    "つぶらなひとみ": MoveData(
        type="フェアリー",
        category="変化",
        pp=30,
        accuracy=100,
        priority=1,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.つぶらなひとみ_modify_defender_stats,
            ),
        }
    ),
    "つぼをつく": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.つぼをつく_modify_attacker_stats,
            ),
        }
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
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.つるぎのまい_modify_attacker_stats,
            ),
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
                hs.てっぺき_modify_attacker_stats,
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.てんしのキッス_apply,
            ),
        }
    ),
    "でんじは": MoveData(
        type="でんき",
        category="変化",
        pp=20,
        accuracy=90,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.でんじは_apply_ailment_to_defender,
            ),
        }
    ),
    "でんじふゆう": MoveData(
        type="でんき",
        category="変化",
        pp=10,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.でんじふゆう_apply,
            ),
        }
    ),
    "とおせんぼう": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.とおせんぼう_apply,
            ),
        }
    ),
    "トーチカ": MoveData(
        type="どく",
        category="変化",
        pp=10,

        priority=4,
        target="self",

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.トーチカ_apply,
            ),
        }
    ),
    "とおぼえ": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        labels=["sound"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.とおぼえ_modify_attacker_stats,
            ),
        }
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
                hs.どくどく_apply_ailment_to_defender,
            ),
        }
    ),
    "どくのいと": MoveData(
        type="どく",
        category="変化",
        pp=20,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.どくのいと_apply,
            ),
        }
    ),
    "どくのこな": MoveData(
        type="どく",
        category="変化",
        pp=35,
        accuracy=75,
        labels=["powder"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.どくのこな_apply_ailment_to_defender,
            ),
        }
    ),
    "どくびし": MoveData(
        type="どく",
        category="変化",
        pp=20,
        target="foe_side",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.どくびし_set_field,
            ),
        }
    ),
    "とぐろをまく": MoveData(
        type="どく",
        category="変化",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.とぐろをまく_modify_attacker_stats,
            ),
        }
    ),
    "とける": MoveData(
        type="どく",
        category="変化",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.とける_modify_attacker_stats,
            ),
        }
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
                hs.すりかえ_swap_items,
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
                hs.トリックルーム_activate_global_field,
            ),
        }
    ),
    "ドわすれ": MoveData(
        type="エスパー",
        category="変化",
        pp=20,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ドわすれ_modify_attacker_stats,
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
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.なかまづくり_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.なかまづくり_change_defender_ability,
            ),
        }
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
                hs.なきごえ_modify_defender_stats,
            )
        }
    ),
    "なまける": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        labels=["heal"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.なまける_heal_self,
            ),
        }
    ),
    "なみだめ": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.なみだめ_modify_defender_stats,
            )
        }
    ),
    "なやみのタネ": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.なやみのタネ_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.なやみのタネ_change_ability,
            ),
        }
    ),
    "なりきり": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.なりきり_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.なりきり_change_ability,
            ),
        }
    ),
    "ニードルガード": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        priority=4,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ニードルガード_apply,
            ),
        }
    ),
    "にほんばれ": MoveData(
        type="ほのお",
        category="変化",
        pp=5,

        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.にほんばれ_activate_weather,
            ),
        }
    ),
    "にらみつける": MoveData(
        type="ノーマル",
        category="変化",
        pp=30,
        accuracy=100,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.にらみつける_modify_defender_stats,
            )
        }
    ),
    "ねがいごと": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        target="field",
        labels=["heal"],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ねがいごと_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ねがいごと_set_side_field,
            ),
        }
    ),
    "ねごと": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,

        labels=["non_encore", "non_negoto"],
        handlers={
            Event.ON_TRY_ACTION: h.MoveHandler(
                hs.ねごと_check_sleep,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_MODIFY_PP_CONSUMED: h.MoveHandler(
                hs.ねごと_suppress_pp,
                subject_spec="attacker:self",
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ねごと_select_and_execute,
                subject_spec="attacker:self",
            ),
        },
    ),
    "ねばねばネット": MoveData(
        type="むし",
        category="変化",
        pp=20,
        target="foe_side",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ねばねばネット_set_side_field,
            ),
        }
    ),
    "ねむりごな": MoveData(
        type="くさ",
        category="変化",
        pp=15,
        accuracy=75,
        labels=["powder"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ねむりごな_apply_ailment_to_defender,
            ),
        }
    ),
    "ねむる": MoveData(
        type="エスパー",
        category="変化",
        pp=5,

        labels=["heal"],
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                hs.ねむる_check,
                priority=30,
            ),
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ねむる_check_apply,
                priority=100,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ねむる_apply,
            ),
        }
    ),
    "ねをはる": MoveData(
        type="くさ",
        category="変化",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ねをはる_apply,
            ),
        }
    ),
    "のみこむ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        labels=["heal"],
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                hs.のみこむ_check_can_use,
                priority=30,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.のみこむ_apply,
            ),
        }
    ),
    "のろい": MoveData(
        type="ゴースト",
        category="変化",
        pp=10,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.のろい_can_apply,
                subject_spec="attacker:self",
                priority=100,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.のろい_apply,
            ),
        }
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
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.バトンタッチ_check,
                priority=100,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.バトンタッチ_apply,
            ),
        }
    ),
    "はねやすめ": MoveData(
        type="ひこう",
        category="変化",
        pp=5,
        labels=["heal"],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.はねやすめ_check,
                subject_spec="attacker:self",
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.はねやすめ_heal_and_remove_flying,
                subject_spec="attacker:self",
            ),
        }
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ハバネロエキス_apply,
            ),
        }
    ),
    "ハロウィン": MoveData(
        type="ゴースト",
        category="変化",
        pp=20,
        accuracy=100,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ハロウィン_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ハロウィン_apply,
            ),
        }
    ),
    "はらだいこ": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.はらだいこ_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.はらだいこ_apply,
            ),
        }
    ),
    "パワーシェア": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.パワーシェア_equalize_stats,
            ),
        }
    ),
    "パワースワップ": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.パワースワップ_swap_ranks,
            ),
        }
    ),
    "パワートリック": MoveData(
        type="エスパー",
        category="変化",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.パワートリック_swap_stats,
            ),
        }
    ),
    "ひかりのかべ": MoveData(
        type="エスパー",
        category="変化",
        pp=30,
        target="own_side",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ひかりのかべ_set_side_field,
            ),
        }
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ビルドアップ_modify_attacker_stats,
            ),
        }
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
                hs.ふういん_apply,
            ),
        }
    ),
    "フェアリーロック": MoveData(
        type="フェアリー",
        category="変化",
        pp=10,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.フェアリーロック_activate_global_field,
            ),
        }
    ),
    "フェザーダンス": MoveData(
        type="ひこう",
        category="変化",
        pp=15,
        accuracy=100,
        labels=["dance"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.フェザーダンス_modify_defender_stats,
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
                hs.on_blow_apply,
                priority=30,
            ),
            Event.ON_HIT: h.MoveHandler(hs.blow),
        }
    ),
    "フラフラダンス": MoveData(
        type="ノーマル",
        category="変化",
        pp=20,
        accuracy=100,
        labels=["dance"],
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.フラフラダンス_apply,
            ),
        }
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
                hs.へびにらみ_apply_ailment_to_defender,
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
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.on_blow_apply,
                priority=30,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(hs.blow),
        }
    ),
    "ほおばる": MoveData(
        type="ノーマル",
        category="変化",
        pp=10,
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                hs.ほおばる_check_has_berry,
                priority=30,
            ),
            Event.ON_TRY_MOVE_2: h.MoveHandler(
                hs.ほおばる_check_defense_max,
                priority=130,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ほおばる_consume_berry_and_boost,
            ),
        }
    ),
    "ほたるび": MoveData(
        type="むし",
        category="変化",
        pp=20,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ほたるび_modify_attacker_stats,
            )
        }
    ),
    "ほろびのうた": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        labels=["sound"],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ほろびのうた_can_apply,
                priority=130,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ほろびのうた_apply,
            ),
        }
    ),
    "まきびし": MoveData(
        type="じめん",
        category="変化",
        pp=20,
        target="foe_side",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.まきびし_set_field,
            ),
        }
    ),
    "マジックルーム": MoveData(
        type="エスパー",
        category="変化",
        pp=10,

        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.マジックルーム_activate_global_field,
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
                hs.まもる_apply,
            ),
        }
    ),
    "まるくなる": MoveData(
        type="ノーマル",
        category="変化",
        pp=40,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.まるくなる_apply,
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
                hs.みがわり_check,
                priority=100,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.みがわり_apply,
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
                hs.みきり_apply,
            ),
        }
    ),
    "ミストフィールド": MoveData(
        type="フェアリー",
        category="変化",
        pp=10,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ミストフィールド_activate_terrain,
            ),
        }
    ),
    "みずびたし": MoveData(
        type="みず",
        category="変化",
        pp=20,
        accuracy=100,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.みずびたし_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.みずびたし_apply,
            ),
        }
    ),
    "みちづれ": MoveData(
        type="ゴースト",
        category="変化",
        pp=5,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.みちづれ_apply,
            ),
        }
    ),
    "ミラータイプ": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ミラータイプ_can_apply,
                priority=130,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ミラータイプ_apply,
            ),
        }
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.めいそう_modify_attacker_stats,
            ),
        }
    ),
    "メロメロ": MoveData(
        type="ノーマル",
        category="変化",
        pp=15,
        accuracy=100,
        handlers={
            Event.ON_TRY_MOVE_2: h.MoveHandler(
                hs.メロメロ_check_gender,
                priority=120,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.メロメロ_apply,
            ),
        }
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
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.もりののろい_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.もりののろい_apply,
            ),
        }
    ),
    "やどりぎのタネ": MoveData(
        type="くさ",
        category="変化",
        pp=10,
        accuracy=90,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.やどりぎのタネ_can_apply,
                priority=130,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.やどりぎのタネ_apply,
            ),
        }
    ),
    "ゆきげしき": MoveData(
        type="こおり",
        category="変化",
        pp=10,

        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ゆきげしき_activate_weather,
            ),
        }
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
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.リサイクル_can_apply,
                priority=100,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.リサイクル_restore_item,
            ),
        }
    ),
    "リフレクター": MoveData(
        type="エスパー",
        category="変化",
        pp=20,
        target="own_side",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.リフレクター_set_side_field,
            ),
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.りゅうのまい_modify_attacker_stats,
            ),
        }
    ),
    "ロックオン": MoveData(
        type="ノーマル",
        category="変化",
        pp=5,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ロックオン_apply,
            ),
        }
    ),
    "ロックカット": MoveData(
        type="いわ",
        category="変化",
        pp=20,

        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ロックカット_modify_attacker_stats,
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.わたほうし_modify_defender_stats,
            ),
        }
    ),
    "わるだくみ": MoveData(
        type="あく",
        category="変化",
        pp=20,


        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.わるだくみ_modify_attacker_stats,
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
                hs.ワンダールーム_activate_global_field,
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
                hs.キングシールド_apply,
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
