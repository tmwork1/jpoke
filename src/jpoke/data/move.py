"""技データ定義モジュール。

Note:
    このモジュール内の技定義はMOVES辞書内で五十音順に配置されています。
"""
from jpoke.enums import Event, LethalEvent
from jpoke.core import LethalHandler

from jpoke.handlers import move as h
from jpoke.handlers import move_attack as ha
from jpoke.handlers import move_status as hs
from jpoke.handlers import lethal as l

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
    "わるあがき": MoveData(
        type="",
        category="physical",
        pp=99999,
        power=40,
        flags={"contact", "non_encore", "non_onnen"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.わるあがき_self_damage,
            )
        }
    ),
    "_こんらん": MoveData(
        type="",
        category="physical",
        pp=99999,
        power=40,
    ),
    "10まんばりき": MoveData(
        type="じめん",
        category="physical",
        pp=10,
        power=95,
        accuracy=95,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "10まんボルト": MoveData(
        type="でんき",
        category="special",
        pp=15,
        power=90,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha._10まんボルト_apply_ailment_to_defender,
            )
        }
    ),
    "3ぼんのや": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=90,
        accuracy=100,
        critical_rank=1,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha._3ぼんのや_apply_flinch,
            )
        }
    ),
    "DDラリアット": MoveData(
        type="あく",
        category="physical",
        pp=10,
        power=85,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_DEF_RANK_MODIFIER: h.MoveHandler(
                ha.DDラリアット_ignore_def_rank,
                subject_spec="attacker:self",
            ),
        }
    ),
    "Gのちから": MoveData(
        type="くさ",
        category="physical",
        pp=10,
        power=80,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.Gのちから_gravity_boost,
                subject_spec="attacker:self",
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.Gのちから_lower_defender_def,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.Gのちから_lower_def)
        }
    ),
    "Vジェネレート": MoveData(
        type="ほのお",
        category="physical",
        pp=5,
        power=180,
        accuracy=80,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.Vジェネレート_reduce_defender_spd_spe,
            )
        }
    ),
    "アイアンテール": MoveData(
        type="はがね",
        category="physical",
        pp=15,
        power=100,
        accuracy=75,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アイアンテール_lower_defender_def,
            )
        }
    ),
    "アイアンヘッド": MoveData(
        type="はがね",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アイアンヘッド_apply_flinch,
            )
        }
    ),
    "アイアンローラー": MoveData(
        type="はがね",
        category="physical",
        pp=5,
        power=130,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.アイアンローラー_check_terrain,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アイアンローラー_clear_terrain,
                subject_spec="attacker:self",
                priority=180,
            ),
        }
    ),
    "アイススピナー": MoveData(
        type="こおり",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アイススピナー_clear_terrain,
                subject_spec="attacker:self",
                priority=180,
            ),
        }
    ),
    "アイスハンマー": MoveData(
        type="こおり",
        category="physical",
        pp=10,
        power=100,
        accuracy=90,
        flags={"contact", "punch", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アイスハンマー_reduce_attacker_spe,
            )
        }
    ),
    "あおいほのお": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=130,
        accuracy=85,
        handlers={},  # 追加効果なし
    ),
    "アクアカッター": MoveData(
        type="みず",
        category="physical",
        pp=20,
        power=70,
        accuracy=100,
        critical_rank=1,
        flags={"slash"},
        handlers={},  # 追加効果なし
    ),
    "アクアジェット": MoveData(
        type="みず",
        category="physical",
        pp=20,
        power=40,
        accuracy=100,
        priority=1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "アクアステップ": MoveData(
        type="みず",
        category="physical",
        pp=10,
        power=80,
        accuracy=100,
        flags={"contact", "dance", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アクアステップ_boost_attacker_spe,
            )
        }
    ),
    "アクアテール": MoveData(
        type="みず",
        category="physical",
        pp=12,
        power=90,
        accuracy=90,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "アクアブレイク": MoveData(
        type="みず",
        category="physical",
        pp=10,
        power=85,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アクアブレイク_lower_defender_def,
            )
        }
    ),
    "アクアリング": MoveData(
        type="みず",
        category="status",
        pp=20,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.アクアリング_apply,
            ),
        }
    ),
    "あくうせつだん": MoveData(
        type="ドラゴン",
        category="special",
        pp=5,
        power=100,
        accuracy=95,
        critical_rank=1,
        handlers={},  # 追加効果なし
    ),
    "アクセルブレイク": MoveData(
        type="かくとう",
        category="physical",
        pp=5,
        power=100,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.効果抜群時威力ブースト,
            )
        },
    ),
    "アクセルロック": MoveData(
        type="いわ",
        category="physical",
        pp=20,
        power=40,
        accuracy=100,
        priority=1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "あくのはどう": MoveData(
        type="あく",
        category="special",
        pp=15,
        power=80,
        accuracy=100,
        flags={"pulse", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.あくのはどう_apply_flinch,
            )
        }
    ),
    "あくび": MoveData(
        type="ノーマル",
        category="status",
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
        category="status",
        pp=10,
        accuracy=75,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あくまのキッス_apply_ailment_to_defender,
            ),
        }
    ),
    "アクロバット": MoveData(
        type="ひこう",
        category="physical",
        pp=15,
        power=55,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "あさのひざし": MoveData(
        type="ノーマル",
        category="status",
        pp=5,
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あさのひざし_heal_self,
            )
        }
    ),
    "アシストパワー": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=20,
        accuracy=100,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.アシストパワー_boost_power_by_rank,
                subject_spec="attacker:self",
            ),
        }
    ),
    "アシッドボム": MoveData(
        type="どく",
        category="special",
        pp=20,
        power=40,
        accuracy=100,
        flags={"bullet"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アシッドボム_sharply_reduce_defender_spd,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.アシッドボム_reduce_spd)
        }
    ),
    "アストラルビット": MoveData(
        type="ゴースト",
        category="special",
        pp=5,
        power=120,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "あてみなげ": MoveData(
        type="ノーマル",
        category="physical",
        pp=20,
        power=50,
        accuracy=100,
        priority=-1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "あなをほる": MoveData(
        type="じめん",
        category="physical",
        pp=10,
        power=80,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                lambda b, c, v: h.charge_into_volatile(b, c, v, "あなをほる"),
            ),
        }
    ),
    "あばれる": MoveData(
        type="ノーマル",
        category="physical",
        pp=10,
        power=120,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.あばれる_apply,
            ),
        }
    ),
    "アフロブレイク": MoveData(
        type="ノーマル",
        category="physical",
        pp=10,
        power=120,
        accuracy=100,
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アフロブレイク_recoil,
            )
        }
    ),
    "あまいかおり": MoveData(
        type="ノーマル",
        category="status",
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
        category="status",
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
        category="status",
        pp=5,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あまごい_activate_weather,
            ),
        }
    ),
    "あやしいかぜ": MoveData(
        type="ゴースト",
        category="special",
        pp=15,
        power=40,
        accuracy=100,
        flags={"wind", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.あやしいかぜ_boost_all_stats,
            )
        }
    ),
    "あやしいひかり": MoveData(
        type="ゴースト",
        category="status",
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
        category="status",
        pp=5,
        handlers={},  # TODO : 効果実装
    ),
    "アロマミスト": MoveData(
        type="フェアリー",
        category="status",
        pp=20,
        target="self",
        handlers={},  # 追加効果なし
    ),
    "あわ": MoveData(
        type="みず",
        category="special",
        pp=30,
        power=40,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.あわ_reduce_defender_spd,
            )
        }
    ),
    "あんこくきょうだ": MoveData(
        type="あく",
        category="physical",
        pp=5,
        power=75,
        accuracy=100,
        critical_rank=3,
        flags={"contact", "punch"},
        handlers={},  # 追加効果なし
    ),
    "アンコール": MoveData(
        type="ノーマル",
        category="status",
        pp=5,
        accuracy=100,
        flags={"non_encore"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.アンコール_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.アンコール_apply,
            )
        }
    ),
    "アーマーキャノン": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=120,
        accuracy=100,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アーマーキャノン_reduce_attacker_stats,
            )
        }
    ),
    "アームハンマー": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=100,
        accuracy=90,
        flags={"contact", "punch", "secondary_effect"},
        handlers={
             Event.ON_HIT: h.MoveHandler(
                 ha.アームハンマー_reduce_attacker_spe,
             )
        }
    ),
    "いえき": MoveData(
        type="どく",
        category="status",
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
    "イカサマ": MoveData(
        type="あく",
        category="physical",
        pp=15,
        power=95,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "いかりのこな": MoveData(
        type="むし",
        category="status",
        pp=20,
        priority=2,
        handlers={},  # 追加効果なし
    ),
    "いかりのまえば": MoveData(
        type="ノーマル",
        category="physical",
        pp=10,
        accuracy=90,
        flags={"contact"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.half_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "いじげんホール": MoveData(
        type="エスパー",
        category="special",
        pp=5,
        power=80,
        accuracy=None,
        flags={"unprotectable", "bypass_substitute"},
    ),
    "いじげんラッシュ": MoveData(
        type="あく",
        category="physical",
        pp=5,
        power=100,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.いじげんラッシュ_reduce_attacker_def,
            )
        }
    ),
    "いたみわけ": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いたみわけ_equalize_hp,
            )
        }
    ),
    "いちゃもん": MoveData(
        type="あく",
        category="status",
        pp=15,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いちゃもん_apply,
            ),
        }
    ),
    "いっちょうあがり": MoveData(
        type="ドラゴン",
        category="physical",
        pp=10,
        power=80,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "いてつくしせん": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: [
                h.MoveHandler(
                    ha.いてつくしせん_reduce_defender_spd,
                ),
                h.MoveHandler(
                    ha.いてつくしせん_apply_ailment_to_defender,
                ),
            ]
        }
    ),
    "いとをはく": MoveData(
        type="むし",
        category="status",
        pp=40,
        accuracy=95,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いとをはく_reduce_defender_spe,
            ),
        }
    ),
    "イナズマドライブ": MoveData(
        type="でんき",
        category="special",
        pp=5,
        power=100,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.効果抜群時威力ブースト,
            )
        },
    ),
    "いにしえのうた": MoveData(
        type="ノーマル",
        category="special",
        pp=10,
        power=75,
        accuracy=100,
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いにしえのうた_apply_ailment_to_defender,
            )
        }
    ),
    "いのちがけ": MoveData(
        type="かくとう",
        category="special",
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
    "いのちのしずく": MoveData(
        type="みず",
        category="status",
        pp=10,
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いのちのしずく_heal,
            ),
        }
    ),
    "いばる": MoveData(
        type="ノーマル",
        category="status",
        pp=15,
        accuracy=85,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いばる_apply,
            ),
        }
    ),
    "いびき": MoveData(
        type="ノーマル",
        category="special",
        pp=15,
        power=50,
        accuracy=100,
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いびき_apply_flinch,
            )
        }
    ),
    "いやしのすず": MoveData(
        type="ノーマル",
        category="status",
        pp=5,
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやしのすず_cure_ailment,
            ),
        }
    ),
    "いやしのねがい": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやしのねがい_apply,
            ),
        }
    ),
    "いやしのはどう": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやしのはどう_heal_defender,
            ),
        }
    ),
    "いやなおと": MoveData(
        type="ノーマル",
        category="status",
        pp=40,
        accuracy=85,
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやなおと_lower_defender_def,
            )
        }
    ),
    "いわおとし": MoveData(
        type="いわ",
        category="physical",
        pp=15,
        power=50,
        accuracy=90,
        handlers={},  # 追加効果なし
    ),
    "いわくだき": MoveData(
        type="かくとう",
        category="physical",
        pp=15,
        power=40,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いわくだき_lower_defender_def,
            )
        }
    ),
    "いわなだれ": MoveData(
        type="いわ",
        category="physical",
        pp=10,
        power=75,
        accuracy=90,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いわなだれ_apply_flinch,
            )
        }
    ),
    "インファイト": MoveData(
        type="かくとう",
        category="physical",
        pp=5,
        power=120,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.インファイト_reduce_defender_stats,
            )
        }
    ),
    "ウェザーボール": MoveData(
        type="ノーマル",
        category="special",
        pp=10,
        power=50,
        accuracy=100,
        flags={"bullet"},
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(
                ha.ウェザーボール_modify_move_type,
            ),
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ウェザーボール_power_modifier,
            ),
        },
    ),
    "ウェーブタックル": MoveData(
        type="みず",
        category="physical",
        pp=10,
        power=120,
        accuracy=100,
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ウェーブタックル_recoil,
            )
        }
    ),
    "うずしお": MoveData(
        type="みず",
        category="special",
        pp=15,
        power=35,
        accuracy=85,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "うそなき": MoveData(
        type="あく",
        category="status",
        pp=20,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.うそなき_reduce_defender_spe,
            )
        }
    ),
    "うたう": MoveData(
        type="ノーマル",
        category="status",
        pp=15,
        accuracy=55,
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.うたう_apply_sleep,
            ),
        }
    ),
    "うたかたのアリア": MoveData(
        type="みず",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        flags={"sound"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.うたかたのアリア_cure_defender_burn,
            )
        },
    ),
    "うちおとす": MoveData(
        type="いわ",
        category="physical",
        pp=15,
        power=50,
        accuracy=100,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.うちおとす_apply_grounded,
            )
        },
    ),
    "ウッドハンマー": MoveData(
        type="くさ",
        category="physical",
        pp=15,
        power=120,
        accuracy=100,
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ウッドハンマー_recoil,
            )
        }
    ),
    "ウッドホーン": MoveData(
        type="くさ",
        category="physical",
        pp=10,
        power=75,
        accuracy=100,
        flags={"contact", "heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.ウッドホーン_drain, priority=20)
        }
    ),
    "うっぷんばらし": MoveData(
        type="あく",
        category="physical",
        pp=5,
        power=75,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.うっぷんばらし_double_power_when_rank_dropped,
            ),
        }
    ),
    "うつしえ": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "うらみ": MoveData(
        type="ゴースト",
        category="status",
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
    "うらみつらみ": MoveData(
        type="ゴースト",
        category="special",
        pp=10,
        power=75,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.うらみつらみ_reduce_defender_atk,
            )
        }
    ),
    "エアカッター": MoveData(
        type="ひこう",
        category="special",
        pp=25,
        power=60,
        accuracy=95,
        critical_rank=1,
        flags={"slash", "wind"},
        handlers={},  # 追加効果なし
    ),
    "エアスラッシュ": MoveData(
        type="ひこう",
        category="special",
        pp=15,
        power=75,
        accuracy=95,
        flags={"slash", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.エアスラッシュ_apply_flinch,
            )
        }
    ),
    "エアロブラスト": MoveData(
        type="ひこう",
        category="special",
        pp=5,
        power=100,
        accuracy=95,
        critical_rank=1,
        flags={"wind"},
        handlers={},  # 追加効果なし
    ),
    "エコーボイス": MoveData(
        type="ノーマル",
        category="special",
        pp=15,
        power=40,
        accuracy=100,
        flags={"sound"},
        handlers={},  # 追加効果なし
    ),
    "えだづき": MoveData(
        type="くさ",
        category="physical",
        pp=40,
        power=40,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "エナジーボール": MoveData(
        type="くさ",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        flags={"bullet"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.エナジーボール_reduce_defender_spd,
            )
        }
    ),
    "エレキネット": MoveData(
        type="でんき",
        category="special",
        pp=15,
        power=55,
        accuracy=95,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.エレキネット_reduce_defender_spd,
            )
        }
    ),
    "エレキフィールド": MoveData(
        type="でんき",
        category="status",
        pp=10,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.エレキフィールド_activate_terrain,
            ),
        }
    ),
    "エレキボール": MoveData(
        type="でんき",
        category="special",
        pp=10,
        power=1,
        accuracy=100,
        flags={"bullet"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.エレキボール_calc_power,
            ),
        }
    ),
    "エレクトロビーム": MoveData(
        type="でんき",
        category="special",
        pp=12,
        power=130,
        accuracy=100,
        handlers={
            Event.ON_MOVE_CHARGE: [
                h.MoveHandler(
                    ha.エレクトロビーム_boost_spa,
                    priority=50,
                ),
                h.MoveHandler(
                    ha.エレクトロビーム_charge,
                ),
            ],
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_MOVE: LethalHandler(l.エレクトロビーム_boost_spa)
        }
    ),
    "えんまく": MoveData(
        type="ノーマル",
        category="status",
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
        category="status",
        pp=15,
        target="own_side",
        flags={"wind"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おいかぜ_set_side_field,
            ),
        }
    ),
    "おいわい": MoveData(
        type="ノーマル",
        category="status",
        pp=40,
        flags={"non_negoto"},
        handlers={},  # 追加効果なし
    ),
    "おかたづけ": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(hs.おかたづけ_cleanup),
        }
    ),
    "おきみやげ": MoveData(
        type="あく",
        category="status",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おきみやげ_apply,
            ),
        }
    ),
    "オクタンほう": MoveData(
        type="みず",
        category="special",
        pp=10,
        power=110,
        accuracy=85,
        flags={"bullet", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.オクタンほう_reduce_acc,
            )
        }
    ),
    "おさきにどうぞ": MoveData(
        type="ノーマル",
        category="status",
        pp=15,
        handlers={},  # 追加効果なし
    ),
    "おしゃべり": MoveData(
        type="ひこう",
        category="special",
        pp=15,
        power=65,
        accuracy=100,
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.おしゃべり_apply_confusion,
            )
        }
    ),
    "おたけび": MoveData(
        type="ノーマル",
        category="status",
        pp=30,
        accuracy=100,
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おたけび_modify_defender_stats,
            ),
        }
    ),
    "おだてる": MoveData(
        type="あく",
        category="status",
        pp=15,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おだてる_apply,
            ),
        }
    ),
    "おちゃかい": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        handlers={},  # 追加効果なし
    ),
    "おどろかす": MoveData(
        type="ゴースト",
        category="physical",
        pp=15,
        power=30,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.おどろかす_apply_flinch,
            )
        }
    ),
    "おにび": MoveData(
        type="ほのお",
        category="status",
        pp=15,
        accuracy=85,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おにび_apply_burn,
            ),
        }
    ),
    "おはかまいり": MoveData(
        type="ゴースト",
        category="physical",
        pp=10,
        power=50,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.おはかまいり_calc_power,
            ),
        }
    ),
    "オーバードライブ": MoveData(
        type="でんき",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        flags={"sound"},
        handlers={},  # 追加効果なし
    ),
    "オーバーヒート": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=130,
        accuracy=90,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.オーバーヒート_lower_attacker_spa,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.オーバーヒート_lower_attacker_spa)
        }
    ),
    "オーラウイング": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        critical_rank=1,
        flags={"secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.オーラウイング_boost_attacker_spe,
            )
        }
    ),
    "オーラぐるま": MoveData(
        type="でんき",
        category="physical",
        pp=10,
        power=110,
        accuracy=100,
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(
                ha.オーラぐるま_check_move_type,
            ),
        },
    ),
    "オーロラビーム": MoveData(
        type="こおり",
        category="special",
        pp=20,
        power=65,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.オーロラビーム_reduce_defender_atk,
            )
        }
    ),
    "オーロラベール": MoveData(
        type="こおり",
        category="status",
        pp=20,
        target="own_side",
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                hs.オーロラベール_check_weather,
                priority=30,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.オーロラベール_apply,
            ),
        }
    ),
    "かいでんぱ": MoveData(
        type="でんき",
        category="status",
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
        category="status",
        pp=15,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.かいふくふうじ_apply,
            ),
        }
    ),
    "かいりき": MoveData(
        type="ノーマル",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "カウンター": MoveData(
        type="かくとう",
        category="physical",
        pp=20,
        power=0,
        accuracy=100,
        priority=-5,
        flags={"contact"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.カウンター_can_use,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.カウンター_modify_damage,
                subject_spec="attacker:self",
            ),
        },
    ),
    "かえんぐるま": MoveData(
        type="ほのお",
        category="physical",
        pp=25,
        power=60,
        accuracy=100,
        flags={"contact", "secondary_effect", "thaw"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かえんぐるま_apply_burn,
            )
        }
    ),
    "かえんだん": MoveData(
        type="ほのお",
        category="special",
        pp=15,
        power=75,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かえんだん_apply_burn,
            )
        }
    ),
    "かえんのまもり": MoveData(
        type="ほのお",
        category="status",
        pp=10,
        priority=4,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.かえんのまもり_apply,
            ),
        }
    ),
    "かえんほうしゃ": MoveData(
        type="ほのお",
        category="special",
        pp=15,
        power=90,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かえんほうしゃ_apply_burn,
            )
        }
    ),
    "かえんボール": MoveData(
        type="ほのお",
        category="physical",
        pp=5,
        power=120,
        accuracy=90,
        flags={"bullet", "secondary_effect", "thaw"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かえんボール_apply_burn,
            )
        }
    ),
    "かかとおとし": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=120,
        accuracy=90,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かかとおとし_apply_confusion,
            ),
            Event.ON_MISS: h.MoveHandler(
                ha.かかとおとし_crash,
            ),
        }
    ),
    "かげうち": MoveData(
        type="ゴースト",
        category="physical",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "かげぬい": MoveData(
        type="ゴースト",
        category="physical",
        pp=10,
        power=80,
        accuracy=100,
        handlers={},  # 交代できない状態を付与する処理を実装
    ),
    "かげぶんしん": MoveData(
        type="ノーマル",
        category="status",
        pp=15,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.かげぶんしん_boost_attacker_evasion,
            ),
        }
    ),
    "かぜおこし": MoveData(
        type="ひこう",
        category="special",
        pp=35,
        power=40,
        accuracy=100,
        flags={"wind"},
        handlers={},  # 追加効果なし
    ),
    "かたきうち": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=70,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "かたくなる": MoveData(
        type="ノーマル",
        category="status",
        pp=30,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.かたくなる_modify_attacker_stats,
            )
        }
    ),
    "カタストロフィ": MoveData(
        type="あく",
        category="special",
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
    "かなしばり": MoveData(
        type="ノーマル",
        category="status",
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
    "かふんだんご": MoveData(
        type="むし",
        category="special",
        pp=15,
        power=90,
        accuracy=100,
        flags={"bullet", "heal"},
        handlers={},  # 追加効果なし
    ),
    "かみくだく": MoveData(
        type="あく",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"bite", "contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かみくだく_lower_defender_def,
            )
        }
    ),
    "かみつく": MoveData(
        type="あく",
        category="physical",
        pp=25,
        power=60,
        accuracy=100,
        flags={"bite", "contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かみつく_apply_flinch,
            )
        }
    ),
    "かみなり": MoveData(
        type="でんき",
        category="special",
        pp=10,
        power=110,
        accuracy=70,
        flags={"secondary_effect"},
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
        category="special",
        pp=10,
        power=100,
        accuracy=80,
        flags={"wind", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かみなりあらし_apply_ailment_to_defender,
            )
        }
    ),
    "かみなりのキバ": MoveData(
        type="でんき",
        category="physical",
        pp=15,
        power=65,
        accuracy=95,
        flags={"bite", "contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: [
                h.MoveHandler(ha.かみなりのキバ_apply_ailment_to_defender),
                h.MoveHandler(ha.かみなりのキバ_apply_flinch),
            ]
        }
    ),
    "かみなりパンチ": MoveData(
        type="でんき",
        category="physical",
        pp=15,
        power=75,
        accuracy=100,
        flags={"contact", "punch", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かみなりパンチ_apply_ailment_to_defender,
            )
        }
    ),
    "からげんき": MoveData(
        type="ノーマル",
        category="physical",
        pp=20,
        power=70,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.からげんき_double_power_when_ailment,
            ),
            Event.ON_CALC_BURN_MODIFIER: h.MoveHandler(
                ha.からげんき_ignore_burn_modifier,
                subject_spec="attacker:self",
            ),
        }
    ),
    "からにこもる": MoveData(
        type="みず",
        category="status",
        pp=40,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.からにこもる_modify_attacker_stats,
            )
        }
    ),
    "からみつく": MoveData(
        type="むし",
        category="special",
        pp=20,
        power=55,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.からみつく_reduce_defender_spd,
            )
        }
    ),
    "からをやぶる": MoveData(
        type="ノーマル",
        category="status",
        pp=15,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.からをやぶる_modify_attacker_stats,
            ),
        }
    ),
    "かわらわり": MoveData(
        type="かくとう",
        category="physical",
        pp=15,
        power=75,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.かわらわり_break_screens,
            ),
        },
    ),
    "がむしゃら": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=0,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.がむしゃら_modify_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "ガリョウテンセイ": MoveData(
        type="ひこう",
        category="physical",
        pp=5,
        power=120,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ガリョウテンセイ_reduce_defender_spd,
            )
        }
    ),
    "がんせきアックス": MoveData(
        type="いわ",
        category="physical",
        pp=15,
        power=65,
        accuracy=90,
        flags={"contact", "slash"},
        handlers={},  # TODO :
    ),
    "がんせきふうじ": MoveData(
        type="いわ",
        category="physical",
        pp=15,
        power=60,
        accuracy=95,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.がんせきふうじ_reduce_defender_spd,
            )
        }
    ),
    "がんせきほう": MoveData(
        type="いわ",
        category="physical",
        pp=5,
        power=150,
        accuracy=90,
        flags={"bullet"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.リチャージ_apply,
            )
        }
    ),
    "ガードシェア": MoveData(
        type="エスパー",
        category="status",
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
        category="status",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ガードスワップ_swap_ranks,
            ),
        }
    ),
    "きあいだま": MoveData(
        type="かくとう",
        category="special",
        pp=5,
        power=120,
        accuracy=70,
        flags={"bullet", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.きあいだま_reduce_defender_spd,
            )
        }
    ),
    "きあいだめ": MoveData(
        type="ノーマル",
        category="status",
        pp=30,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.きあいだめ_apply,
            ),
        }
    ),
    "きあいパンチ": MoveData(
        type="かくとう",
        category="physical",
        pp=20,
        power=150,
        accuracy=100,
        priority=-3,
        flags={"contact", "non_negoto", "punch"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.きあいパンチ_check_move,
                subject_spec="attacker:self",
            ),
        },
    ),
    "きしかいせい": MoveData(
        type="かくとう",
        category="physical",
        pp=15,
        power=1,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.きしかいせい_calc_power,
            ),
        }
    ),
    "キノコのほうし": MoveData(
        type="くさ",
        category="status",
        pp=15,
        accuracy=100,
        flags={"powder"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.キノコのほうし_apply_ailment_to_defender,
            ),
        }
    ),
    "きまぐレーザー": MoveData(
        type="ドラゴン",
        category="special",
        pp=5,
        power=80,
        accuracy=100,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.きまぐレーザー_maybe_double_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "きゅうけつ": MoveData(
        type="むし",
        category="physical",
        pp=10,
        power=80,
        accuracy=100,
        flags={"contact", "heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.きゅうけつ_drain, priority=20)
        }
    ),
    "きょけんとつげき": MoveData(
        type="ドラゴン",
        category="physical",
        pp=5,
        power=120,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "きょじゅうざん": MoveData(
        type="はがね",
        category="physical",
        pp=5,
        power=100,
        accuracy=100,
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "きょじゅうだん": MoveData(
        type="はがね",
        category="physical",
        pp=5,
        power=100,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "キラースピン": MoveData(
        type="どく",
        category="physical",
        pp=15,
        power=30,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.キラースピン_clear_field,
                priority=100,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.キラースピン_apply_ailment_to_defender,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.キラースピン_apply_どく)
        }
    ),
    "きりさく": MoveData(
        type="ノーマル",
        category="physical",
        pp=20,
        power=70,
        accuracy=100,
        critical_rank=1,
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "きりばらい": MoveData(
        type="ひこう",
        category="status",
        pp=15,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.きりばらい_defog,
            )
        }
    ),
    "キングシールド": MoveData(
        type="はがね",
        category="status",
        pp=10,
        priority=4,
        target="self",
        flags={"protect"},
        handlers={
            Event.ON_TRY_MOVE_2: h.MoveHandler(
                hs.まもる系_連続使用失敗チェック,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.キングシールド_apply,
            ),
        }
    ),
    "きんぞくおん": MoveData(
        type="はがね",
        category="status",
        pp=40,
        accuracy=85,
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.きんぞくおん_modify_defender_stats,
            )
        }
    ),
    "ギアチェンジ": MoveData(
        type="はがね",
        category="status",
        pp=10,
        handlers={},  # 追加効果なし
    ),
    "ギガインパクト": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=150,
        accuracy=90,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.リチャージ_apply,
            )
        }
    ),
    "ギガドレイン": MoveData(
        type="くさ",
        category="special",
        pp=10,
        power=75,
        accuracy=100,
        flags={"heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ギガドレイン_drain,
                priority=20,  # turn.md: ON_HIT priority 20 (HP吸収技による回復)
            )
        }
    ),
    "ぎんいろのかぜ": MoveData(
        type="こおり",
        category="special",
        pp=5,
        power=60,
        accuracy=100,
        flags={"wind", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ぎんいろのかぜ_boost_all_stats,
            )
        }
    ),
    "クイックターン": MoveData(
        type="みず",
        category="physical",
        pp=20,
        power=60,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.pivot)
        }
    ),
    "くさのちかい": MoveData(
        type="くさ",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "くさむすび": MoveData(
        type="くさ",
        category="special",
        pp=20,
        power=1,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.くさむすび_calc_power,
            ),
        }
    ),
    "くさわけ": MoveData(
        type="くさ",
        category="physical",
        pp=20,
        power=50,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.くさわけ_boost_attacker_spe,
            )
        }
    ),
    "くすぐる": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.くすぐる_modify_defender_stats,
            ),
        }
    ),
    "くちばしキャノン": MoveData(
        type="ひこう",
        category="physical",
        pp=15,
        power=120,
        accuracy=100,
        priority=-3,
        flags={"bullet", "non_negoto"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.くちばしキャノン_burn_contact_hitter,
                subject_spec="attacker:self",
                priority=100,
            ),
        }
    ),
    "くらいつく": MoveData(
        type="あく",
        category="physical",
        pp=10,
        power=80,
        accuracy=100,
        flags={"bite", "contact"},
        handlers={},  # 追加効果なし
    ),
    "クラブハンマー": MoveData(
        type="みず",
        category="physical",
        pp=10,
        power=100,
        accuracy=90,
        critical_rank=1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "クリアスモッグ": MoveData(
        type="どく",
        category="special",
        pp=15,
        power=50,
        accuracy=None,
        handlers={},  # 追加効果なし
    ),
    "くろいきり": MoveData(
        type="こおり",
        category="status",
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
        category="status",
        pp=5,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.くろいまなざし_apply,
            ),
        }
    ),
    "クロスサンダー": MoveData(
        type="でんき",
        category="physical",
        pp=5,
        power=100,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "クロスチョップ": MoveData(
        type="かくとう",
        category="physical",
        pp=5,
        power=100,
        accuracy=80,
        critical_rank=1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "クロスフレイム": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=100,
        accuracy=100,
        flags={"thaw"},
        handlers={},  # 追加効果なし
    ),
    "クロスポイズン": MoveData(
        type="どく",
        category="physical",
        pp=20,
        power=70,
        accuracy=100,
        critical_rank=1,
        flags={"contact", "slash", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.クロスポイズン_apply_ailment_to_defender,
            )
        }
    ),
    "クロロブラスト": MoveData(
        type="くさ",
        category="special",
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
    "グラススライダー": MoveData(
        type="くさ",
        category="physical",
        pp=20,
        power=55,
        accuracy=100,
        priority=1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "グラスフィールド": MoveData(
        type="くさ",
        category="status",
        pp=10,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.グラスフィールド_activate_terrain,
            ),
        }
    ),
    "グラスミキサー": MoveData(
        type="くさ",
        category="special",
        pp=10,
        power=60,
        accuracy=55,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.グラスミキサー_reduce_acc,
            )
        }
    ),
    "グロウパンチ": MoveData(
        type="かくとう",
        category="physical",
        pp=40,
        power=40,
        accuracy=100,
        flags={"contact", "punch", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.グロウパンチ_boost_attacker_A,
            )
        }
    ),
    "けたぐり": MoveData(
        type="かくとう",
        category="physical",
        pp=20,
        power=1,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.けたぐり_calc_power,
            ),
        }
    ),
    "げきりん": MoveData(
        type="ドラゴン",
        category="physical",
        pp=10,
        power=120,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.あばれる_apply,
            ),
        }
    ),
    "ゲップ": MoveData(
        type="どく",
        category="special",
        pp=10,
        power=120,
        accuracy=90,
        flags={"non_negoto"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.ゲップ_check_ate_berry,
                subject_spec="attacker:self",
                priority=30,
            )
        }
    ),
    "げんしのちから": MoveData(
        type="いわ",
        category="special",
        pp=5,
        power=60,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.げんしのちから_boost_all_stats,
            )
        }
    ),
    "こうげきしれい": MoveData(
        type="むし",
        category="physical",
        pp=15,
        power=90,
        accuracy=100,
        critical_rank=1,
        handlers={},  # 追加効果なし
    ),
    "こうごうせい": MoveData(
        type="くさ",
        category="status",
        pp=5,
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あさのひざし_heal_self,
            )
        }
    ),
    "こうそくいどう": MoveData(
        type="エスパー",
        category="status",
        pp=30,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.こうそくいどう_modify_attacker_stats,
            )
        }
    ),
    "こうそくスピン": MoveData(
        type="ノーマル",
        category="physical",
        pp=40,
        power=50,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_HIT: [
                h.MoveHandler(ha.こうそくスピン_clear_field, priority=100),
                h.MoveHandler(ha.こうそくスピン_boost_attacker_spe),
            ]
        }
    ),
    "こおりのいぶき": MoveData(
        type="こおり",
        category="special",
        pp=10,
        power=60,
        accuracy=90,
        critical_rank=3,
        handlers={},  # 追加効果なし
    ),
    "こおりのキバ": MoveData(
        type="こおり",
        category="physical",
        pp=15,
        power=65,
        accuracy=95,
        flags={"bite", "contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.こおりのキバ_apply_flinch_or_freeze,
            )
        }
    ),
    "こおりのつぶて": MoveData(
        type="こおり",
        category="physical",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        handlers={},  # 追加効果なし
    ),
    "こがらしあらし": MoveData(
        type="ひこう",
        category="special",
        pp=10,
        power=100,
        accuracy=80,
        flags={"wind", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.こがらしあらし_reduce_defender_spd,
            )
        }
    ),
    "こごえるかぜ": MoveData(
        type="こおり",
        category="special",
        pp=15,
        power=55,
        accuracy=95,
        flags={"wind"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.こごえるかぜ_reduce_defender_spd,
            )
        }
    ),
    "こごえるせかい": MoveData(
        type="こおり",
        category="special",
        pp=10,
        power=65,
        accuracy=95,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.こごえるせかい_reduce_defender_spd,
            )
        }
    ),
    "コスモパワー": MoveData(
        type="エスパー",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.コスモパワー_modify_attacker_stats,
            ),
        }
    ),
    "コットンガード": MoveData(
        type="くさ",
        category="status",
        pp=10,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.コットンガード_modify_attacker_stats,
            )
        }
    ),
    "こなゆき": MoveData(
        type="こおり",
        category="special",
        pp=25,
        power=40,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.こなゆき_apply_ailment_to_defender,
            )
        }
    ),
    "このは": MoveData(
        type="くさ",
        category="physical",
        pp=40,
        power=40,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "このゆびとまれ": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        priority=2,
        handlers={},  # 追加効果なし
    ),
    "コメットパンチ": MoveData(
        type="はがね",
        category="physical",
        pp=10,
        power=90,
        accuracy=90,
        flags={"contact", "punch", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.コメットパンチ_boost_attacker_A,
            )
        }
    ),
    "こらえる": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        priority=4,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.こらえる_apply,
            ),
        }
    ),
    "ころがる": MoveData(
        type="いわ",
        category="physical",
        pp=20,
        power=30,
        accuracy=90,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "こわいかお": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.こわいかお_modify_defender_stats,
            )
        }
    ),
    "こんげんのはどう": MoveData(
        type="みず",
        category="special",
        pp=10,
        power=110,
        accuracy=85,
        flags={"pulse"},
        handlers={},  # 追加効果なし
    ),
    "コーチング": MoveData(
        type="かくとう",
        category="status",
        pp=10,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "コートチェンジ": MoveData(
        type="ノーマル",
        category="status",
        pp=100,
        handlers={},  # 追加効果なし
    ),
    "コールドフレア": MoveData(
        type="こおり",
        category="special",
        pp=5,
        power=140,
        accuracy=90,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.コールドフレア_apply_ailment_to_defender,
            )
        }
    ),
    "ゴッドバード": MoveData(
        type="ひこう",
        category="physical",
        pp=5,
        power=140,
        accuracy=90,
        critical_rank=1,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ゴッドバード_apply_flinch,
            )
        }
    ),
    "ゴーストダイブ": MoveData(
        type="ゴースト",
        category="physical",
        pp=10,
        power=90,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "ゴールドラッシュ": MoveData(
        type="はがね",
        category="special",
        pp=5,
        power=120,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ゴールドラッシュ_lower_spa_C,
            )
        }
    ),
    "さいきのいのり": MoveData(
        type="ノーマル",
        category="status",
        pp=0,
        flags={"heal"},
        handlers={},  # 追加効果なし
    ),
    "サイケこうせん": MoveData(
        type="エスパー",
        category="special",
        pp=20,
        power=65,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.サイケこうせん_apply_confusion_to_defender,
            )
        }
    ),
    "サイコカッター": MoveData(
        type="エスパー",
        category="physical",
        pp=20,
        power=70,
        accuracy=100,
        critical_rank=1,
        flags={"slash"},
        handlers={},  # 追加効果なし
    ),
    "サイコキネシス": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.サイコキネシス_reduce_defender_spd,
            )
        }
    ),
    "サイコショック": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "サイコノイズ": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=75,
        accuracy=100,
        flags={"sound"},
        handlers={},  # 追加効果なし
    ),
    "サイコファング": MoveData(
        type="エスパー",
        category="physical",
        pp=10,
        power=85,
        accuracy=100,
        flags={"bite", "contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.サイコファング_break_screens,
            ),
        },
    ),
    "サイコフィールド": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.サイコフィールド_activate_terrain,
            ),
        }
    ),
    "サイコブレイク": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=100,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "サイコブレイド": MoveData(
        type="エスパー",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "サイコブースト": MoveData(
        type="エスパー",
        category="special",
        pp=5,
        power=140,
        accuracy=90,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.サイコブースト_sharply_lower_spa_C,
            )
        }
    ),
    "サイドチェンジ": MoveData(
        type="エスパー",
        category="status",
        pp=15,
        priority=2,
        handlers={},  # 追加効果なし
    ),
    "さいはい": MoveData(
        type="エスパー",
        category="status",
        pp=15,
        handlers={},  # 追加効果なし
    ),
    "さいみんじゅつ": MoveData(
        type="エスパー",
        category="status",
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
        category="status",
        pp=15,
        handlers={},  # 追加効果なし
    ),
    "さばきのつぶて": MoveData(
        type="ノーマル",
        category="special",
        pp=10,
        power=100,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "さむいギャグ": MoveData(
        type="こおり",
        category="status",
        pp=10,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.さむいギャグ_activate_weather_and_pivot,
            ),
        }
    ),
    "さわぐ": MoveData(
        type="ノーマル",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        flags={"non_negoto", "sound"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.さわぐ_apply,
            ),
        }
    ),
    "サンダーダイブ": MoveData(
        type="でんき",
        category="physical",
        pp=15,
        power=100,
        accuracy=95,
        flags={"minimize", "contact"},
        handlers={
            Event.ON_MISS: h.MoveHandler(
                ha.サンダーダイブ_crash,
            ),
        }
    ),
    "サンダープリズン": MoveData(
        type="でんき",
        category="special",
        pp=15,
        power=80,
        accuracy=90,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        }
    ),
    "シェルアームズ": MoveData(
        type="どく",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_MODIFY_MOVE_CATEGORY: h.MoveHandler(
                ha.シェルアームズ_modify_move_category,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シェルアームズ_apply_ailment_to_defender,
            )
        }
    ),
    "シェルブレード": MoveData(
        type="みず",
        category="physical",
        pp=10,
        power=75,
        accuracy=95,
        flags={"contact", "slash", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シェルブレード_lower_defender_def,
            )
        }
    ),
    "しおづけ": MoveData(
        type="いわ",
        category="physical",
        pp=15,
        power=40,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.しおづけ_apply_volatile_to_defender,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.しおづけ_apply_volatile)
        }
    ),
    "しおふき": MoveData(
        type="みず",
        category="special",
        pp=5,
        power=150,
        accuracy=100,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.しおふき_calc_power,
            ),
        }
    ),
    "しおみず": MoveData(
        type="みず",
        category="special",
        pp=10,
        power=65,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "シグナルビーム": MoveData(
        type="むし",
        category="special",
        pp=15,
        power=75,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シグナルビーム_apply_confusion_to_defender,
            )
        }
    ),
    "シザークロス": MoveData(
        type="むし",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "したでなめる": MoveData(
        type="ゴースト",
        category="physical",
        pp=30,
        power=30,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.したでなめる_apply_ailment_to_defender,
            )
        }
    ),
    "しっとのほのお": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=70,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.しっとのほのお_apply_ailment_to_defender,
            )
        }
    ),
    "しっぺがえし": MoveData(
        type="あく",
        category="physical",
        pp=10,
        power=50,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.しっぺがえし_double_power_when_second,
            ),
        }
    ),
    "しっぽきり": MoveData(
        type="ノーマル",
        category="status",
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
        category="status",
        pp=30,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.しっぽをふる_modify_defender_stats,
            )
        }
    ),
    "しねんのずつき": MoveData(
        type="エスパー",
        category="physical",
        pp=15,
        power=80,
        accuracy=90,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.しねんのずつき_apply_flinch,
            )
        }
    ),
    "しびれごな": MoveData(
        type="くさ",
        category="status",
        pp=30,
        accuracy=75,
        flags={"powder"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.しびれごな_apply_ailment_to_defender,
            ),
        }
    ),
    "しめつける": MoveData(
        type="ノーマル",
        category="physical",
        pp=20,
        power=15,
        accuracy=85,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "シャカシャカほう": MoveData(
        type="くさ",
        category="special",
        pp=15,
        power=80,
        accuracy=90,
        flags={"heal", "secondary_effect", "thaw"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.シャカシャカほう_drain, priority=20),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シャカシャカほう_apply_ailment_to_defender,
            )
        }
    ),
    "シャドークロー": MoveData(
        type="ゴースト",
        category="physical",
        pp=15,
        power=70,
        accuracy=100,
        critical_rank=1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "シャドーダイブ": MoveData(
        type="ゴースト",
        category="physical",
        pp=5,
        power=120,
        accuracy=100,
        flags={"contact", "unprotectable"},
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                lambda b, c, v: h.charge_into_volatile(b, c, v, "シャドーダイブ"),
            ),
        }
    ),
    "シャドーパンチ": MoveData(
        type="ゴースト",
        category="physical",
        pp=20,
        power=60,
        flags={"contact", "punch"},
        handlers={},  # 追加効果なし
    ),
    "シャドーボール": MoveData(
        type="ゴースト",
        category="special",
        pp=15,
        power=80,
        accuracy=100,
        flags={"bullet"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シャドーボール_reduce_defender_spd,
            )
        }
    ),
    "シャドーボーン": MoveData(
        type="ゴースト",
        category="physical",
        pp=10,
        power=85,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シャドーボーン_lower_defender_def,
            )
        }
    ),
    "シャドーレイ": MoveData(
        type="ゴースト",
        category="special",
        pp=5,
        power=100,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "しょうりのまい": MoveData(
        type="かくとう",
        category="status",
        pp=10,
        flags={"dance"},
        handlers={},  # 追加効果なし
    ),
    "しろいきり": MoveData(
        type="こおり",
        category="status",
        pp=30,
        target="field",
        handlers={},  # 追加効果なし
    ),
    "しんくうは": MoveData(
        type="かくとう",
        category="special",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        handlers={},  # 追加効果なし
    ),
    "しんそく": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=80,
        accuracy=100,
        priority=2,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "しんぴのちから": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=70,
        accuracy=90,
        flags={"secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.しんぴのちから_boost_spa_C,
            )
        }
    ),
    "しんぴのつるぎ": MoveData(
        type="かくとう",
        category="special",
        pp=10,
        power=85,
        accuracy=100,
        flags={"slash"},
        handlers={},  # 追加効果なし
    ),
    "しんぴのまもり": MoveData(
        type="ノーマル",
        category="status",
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
        category="status",
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
    "シードフレア": MoveData(
        type="くさ",
        category="special",
        pp=5,
        power=120,
        accuracy=85,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シードフレア_sharply_reduce_defender_spd,
            )
        }
    ),
    "ジェットパンチ": MoveData(
        type="みず",
        category="physical",
        pp=15,
        power=60,
        accuracy=100,
        priority=1,
        flags={"contact", "punch"},
        handlers={},  # 追加効果なし
    ),
    "じこあんじ": MoveData(
        type="ノーマル",
        category="status",
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
        category="status",
        pp=5,
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.じこさいせい_heal_self,
            )
        }
    ),
    "じごくぐるま": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=80,
        accuracy=80,
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.じごくぐるま_recoil,
            )
        }
    ),
    "じごくづき": MoveData(
        type="あく",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.じごくづき_apply_volatile_to_defender,
            )
        }
    ),
    "じしん": MoveData(
        type="じめん",
        category="physical",
        pp=10,
        power=100,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "じたばた": MoveData(
        type="ノーマル",
        category="physical",
        pp=15,
        power=1,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.じたばた_calc_power,
            ),
        }
    ),
    "じだんだ": MoveData(
        type="じめん",
        category="physical",
        pp=10,
        power=75,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "じならし": MoveData(
        type="じめん",
        category="physical",
        pp=20,
        power=60,
        accuracy=100,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.じならし_reduce_defender_spd,
            )
        }
    ),
    "じばく": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=200,
        accuracy=100,
        flags={"explosion"},
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.じばく_pay_hp,
                subject_spec="attacker:self",
            ),
        }
    ),
    "じばそうさ": MoveData(
        type="でんき",
        category="status",
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
    "ジャイロボール": MoveData(
        type="はがね",
        category="physical",
        pp=5,
        power=1,
        accuracy=100,
        flags={"bullet", "contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ジャイロボール_calc_power,
            ),
        }
    ),
    "じゃどくのくさり": MoveData(
        type="どく",
        category="physical",
        pp=10,
        power=100,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.じゃどくのくさり_apply_ailment_to_defender,
            )
        }
    ),
    "じゃれつく": MoveData(
        type="フェアリー",
        category="physical",
        pp=10,
        power=90,
        accuracy=90,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.じゃれつく_reduce_defender_atk,
            )
        }
    ),
    "ジャングルヒール": MoveData(
        type="くさ",
        category="status",
        pp=10,
        flags={"heal"},
        handlers={},  # 追加効果なし
    ),
    "じゅうでん": MoveData(
        type="でんき",
        category="status",
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
        category="status",
        pp=5,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.じゅうりょく_activate_global_field,
            ),
        }
    ),
    "じわれ": MoveData(
        type="じめん",
        category="physical",
        pp=5,
        accuracy=30,
        flags={"ohko"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.ohko_damage,
            ),
        }
    ),
    "じんつうりき": MoveData(
        type="エスパー",
        category="special",
        pp=20,
        power=80,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.じんつうりき_apply_flinch,
            )
        }
    ),
    "じんらい": MoveData(
        type="でんき",
        category="special",
        pp=5,
        power=70,
        accuracy=100,
        priority=1,
        handlers={},  # 追加効果なし
    ),
    "すいとる": MoveData(
        type="くさ",
        category="special",
        pp=25,
        power=20,
        accuracy=100,
        flags={"heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.すいとる_drain, priority=20)
        }
    ),
    "すいりゅうれんだ": MoveData(
        type="みず",
        category="physical",
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
        flags={"contact", "punch"},
        handlers={},  # 追加効果なし
    ),
    "スイープビンタ": MoveData(
        type="ノーマル",
        category="physical",
        pp=10,
        power=25,
        accuracy=85,
        flags={"contact"},
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "スキルスワップ": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        accuracy=100,
        flags={"bypass_substitute"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.スキルスワップ_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.スキルスワップ_swap_ability,
            ),
        }
    ),
    "スケイルショット": MoveData(
        type="ドラゴン",
        category="physical",
        pp=20,
        power=25,
        accuracy=90,
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.スケイルショット_apply_stat_change,
            )
        }
    ),
    "スケイルノイズ": MoveData(
        type="ドラゴン",
        category="special",
        pp=5,
        power=110,
        accuracy=100,
        flags={"sound"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.スケイルノイズ_reduce_attacker_def,
            )
        }
    ),
    "スケッチ": MoveData(
        type="ノーマル",
        category="status",
        pp=0,
        accuracy=100,
        flags={"non_encore", "non_negoto"},
        handlers={},  # 追加効果なし
    ),
    "スチームバースト": MoveData(
        type="みず",
        category="special",
        pp=5,
        power=110,
        accuracy=95,
        flags={"secondary_effect", "thaw"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.スチームバースト_apply_ailment_to_defender,
            )
        }
    ),
    "すてゼリフ": MoveData(
        type="あく",
        category="status",
        pp=20,
        accuracy=100,
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.すてゼリフ_modify_defender_stats_and_pivot,
            ),
        }
    ),
    "すてみタックル": MoveData(
        type="ノーマル",
        category="physical",
        pp=15,
        power=120,
        accuracy=100,
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.すてみタックル_recoil,
            )
        }
    ),
    "ステルスロック": MoveData(
        type="いわ",
        category="status",
        pp=20,
        target="foe_side",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ステルスロック_set_field,
            )
        }
    ),
    "ストーンエッジ": MoveData(
        type="いわ",
        category="physical",
        pp=5,
        power=100,
        accuracy=80,
        critical_rank=1,
        handlers={},  # 追加効果なし
    ),
    "すなあつめ": MoveData(
        type="じめん",
        category="status",
        pp=5,
        flags={"heal"},
        handlers={},  # 追加効果なし
    ),
    "すなあらし": MoveData(
        type="いわ",
        category="status",
        pp=10,
        target="field",
        flags={"wind"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.すなあらし_activate_weather,
            ),
        }
    ),
    "すなかけ": MoveData(
        type="じめん",
        category="status",
        pp=15,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.すなかけ_modify_defender_stats,
            )
        }
    ),
    "すなじごく": MoveData(
        type="じめん",
        category="physical",
        pp=15,
        power=35,
        accuracy=85,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "スパーク": MoveData(
        type="でんき",
        category="physical",
        pp=20,
        power=65,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.スパーク_apply_ailment_to_defender,
            )
        }
    ),
    "スピードスター": MoveData(
        type="ノーマル",
        category="special",
        pp=20,
        power=60,
        accuracy=None,
        handlers={},  # 追加効果なし
    ),
    "スピードスワップ": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.スピードスワップ_swap_speed,
            ),
        }
    ),
    "スマートホーン": MoveData(
        type="はがね",
        category="physical",
        pp=10,
        power=70,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "スモッグ": MoveData(
        type="どく",
        category="special",
        pp=20,
        power=30,
        accuracy=70,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.スモッグ_apply_ailment_to_defender,
            )
        }
    ),
    "すりかえ": MoveData(
        type="あく",
        category="status",
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
        category="status",
        pp=10,
        priority=4,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.スレッドトラップ_apply,
            ),
        }
    ),
    "ずつき": MoveData(
        type="ノーマル",
        category="physical",
        pp=15,
        power=70,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ずつき_apply_flinch,
            )
        }
    ),
    "せいちょう": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.せいちょう_modify_attacker_stats,
            ),
        }
    ),
    "せいなるつるぎ": MoveData(
        type="かくとう",
        category="physical",
        pp=15,
        power=90,
        accuracy=100,
        flags={"contact", "slash"},
        handlers={
            Event.ON_CALC_DEF_RANK_MODIFIER: h.MoveHandler(
                ha.せいなるつるぎ_ignore_def_rank,
                subject_spec="attacker:self",
            ),
        }
    ),
    "せいなるほのお": MoveData(
        type="ほのお",
        category="physical",
        pp=5,
        power=100,
        accuracy=95,
        flags={"secondary_effect", "thaw"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.せいなるほのお_apply_ailment_to_defender,
            )
        }
    ),
    "ぜったいれいど": MoveData(
        type="こおり",
        category="special",
        pp=5,
        power=0,
        accuracy=30,
        flags={"ohko"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.ohko_damage,
            ),
        }
    ),
    "そうでん": MoveData(
        type="でんき",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.そうでん_apply,
            ),
        }
    ),
    "ソウルクラッシュ": MoveData(
        type="フェアリー",
        category="physical",
        pp=15,
        power=75,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ソウルクラッシュ_lower_spa_C,
            )
        }
    ),
    "ソウルビート": MoveData(
        type="ドラゴン",
        category="status",
        pp=5,
        flags={"dance", "sound"},
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
    "そらをとぶ": MoveData(
        type="ひこう",
        category="physical",
        pp=15,
        power=90,
        accuracy=95,
        flags={"contact", "gravity_restricted"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                h.gravity_restricted_fail,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                lambda b, c, v: h.charge_into_volatile(b, c, v, "そらをとぶ"),
            ),
        }
    ),
    "ソーラービーム": MoveData(
        type="くさ",
        category="special",
        pp=10,
        power=120,
        accuracy=100,
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                ha.ソーラービーム_charge,
            ),
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ソーラービーム_halve_power,
            ),
        }
    ),
    "ソーラーブレード": MoveData(
        type="くさ",
        category="physical",
        pp=10,
        power=125,
        accuracy=100,
        flags={"contact", "slash"},
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                ha.ソーラーブレード_charge,
            ),
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ソーラービーム_halve_power,
            ),
        }
    ),
    "たいあたり": MoveData(
        type="ノーマル",
        category="physical",
        pp=35,
        power=40,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "タキオンカッター": MoveData(
        type="はがね",
        category="special",
        pp=10,
        power=50,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "たきのぼり": MoveData(
        type="みず",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.たきのぼり_apply_flinch,
            )
        }
    ),
    "たくわえる": MoveData(
        type="ノーマル",
        category="status",
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
    "たたきつける": MoveData(
        type="ノーマル",
        category="physical",
        pp=20,
        power=80,
        accuracy=75,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "たたりめ": MoveData(
        type="ゴースト",
        category="special",
        pp=10,
        power=65,
        accuracy=100,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.たたりめ_double_power_when_ailment,
            ),
        }
    ),
    "たつまき": MoveData(
        type="ドラゴン",
        category="special",
        pp=20,
        power=40,
        accuracy=100,
        flags={"wind", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.たつまき_apply_flinch,
            )
        }
    ),
    "たてこもる": MoveData(
        type="はがね",
        category="status",
        pp=10,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.たてこもる_modify_attacker_stats,
            ),
        }
    ),
    "タネばくだん": MoveData(
        type="くさ",
        category="physical",
        pp=16,
        power=80,
        accuracy=100,
        flags={"bullet"},
        handlers={},  # 追加効果なし
    ),
    "タネマシンガン": MoveData(
        type="くさ",
        category="physical",
        pp=30,
        power=25,
        accuracy=100,
        flags={"bullet"},
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "タマゴうみ": MoveData(
        type="ノーマル",
        category="status",
        pp=5,
        flags={"heal"},
        handlers={},  # 追加効果なし
    ),
    "タールショット": MoveData(
        type="いわ",
        category="status",
        pp=15,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.タールショット_apply,
            ),
        }
    ),
    "だいちのちから": MoveData(
        type="じめん",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.だいちのちから_reduce_defender_spd,
            )
        }
    ),
    "だいちのはどう": MoveData(
        type="ノーマル",
        category="special",
        pp=10,
        power=50,
        accuracy=100,
        flags={"pulse"},
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(
                ha.だいちのはどう_modify_move_type,
            ),
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.だいちのはどう_power_modifier,
            ),
        },
    ),
    "だいばくはつ": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=250,
        accuracy=100,
        flags={"explosion"},
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.だいばくはつ_pay_hp,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ダイビング": MoveData(
        type="みず",
        category="physical",
        pp=10,
        power=80,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                lambda b, c, v: h.charge_into_volatile(b, c, v, "ダイビング"),
            ),
        }
    ),
    "だいふんげき": MoveData(
        type="ほのお",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.あばれる_apply,
            ),
        }
    ),
    "ダイマックスほう": MoveData(
        type="ドラゴン",
        category="special",
        pp=5,
        power=100,
        accuracy=100,
        flags={"non_encore", "non_negoto"},
        handlers={},  # 追加効果なし
    ),
    "だいもんじ": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=110,
        accuracy=85,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.だいもんじ_apply_ailment_to_defender,
            )
        }
    ),
    "ダイヤストーム": MoveData(
        type="いわ",
        category="physical",
        pp=5,
        power=100,
        accuracy=95,
        flags={"secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ダイヤストーム_sharply_boost_defender_B,
            )
        }
    ),
    "だくりゅう": MoveData(
        type="みず",
        category="special",
        pp=10,
        power=90,
        accuracy=85,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.だくりゅう_reduce_acc,
            )
        }
    ),
    "ダストシュート": MoveData(
        type="どく",
        category="physical",
        pp=5,
        power=120,
        accuracy=80,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ダストシュート_apply_ailment_to_defender,
            )
        }
    ),
    "ダブルアタック": MoveData(
        type="ノーマル",
        category="physical",
        pp=10,
        power=35,
        accuracy=90,
        flags={"contact"},
        multi_hit={
            "min": 2,
            "max": 2,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "ダブルウイング": MoveData(
        type="ひこう",
        category="physical",
        pp=10,
        power=40,
        accuracy=90,
        flags={"contact"},
        multi_hit={
            "min": 2,
            "max": 2,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "ダブルニードル": MoveData(
        type="むし",
        category="physical",
        pp=20,
        power=25,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ダブルニードル_apply_ailment_to_defender,
            )
        }
    ),
    "ダブルパンツァー": MoveData(
        type="はがね",
        category="physical",
        pp=10,
        power=50,
        accuracy=100,
        flags={"contact", "punch", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ダブルパンツァー_apply_flinch,
            )
        }
    ),
    "ダメおし": MoveData(
        type="あく",
        category="physical",
        pp=10,
        power=60,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ダメおし_double_power_when_hit,
            ),
        }
    ),
    "だんがいのつるぎ": MoveData(
        type="じめん",
        category="physical",
        pp=10,
        power=120,
        accuracy=85,
        handlers={},  # 追加効果なし
    ),
    "ダークファイア": MoveData(
        type="ゴースト",
        category="special",
        pp=5,
        power=135,
        accuracy=85,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ダークファイア_apply_ailment_to_defender,
            )
        }
    ),
    "ダークホール": MoveData(
        type="あく",
        category="status",
        pp=10,
        accuracy=50,
        handlers={},  # 追加効果なし
    ),
    "ちいさくなる": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ちいさくなる_apply,
            )
        }
    ),
    "ちからをすいとる": MoveData(
        type="くさ",
        category="status",
        pp=10,
        accuracy=100,
        flags={"heal"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ちからをすいとる_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ちからをすいとる_apply,
            ),
        }
    ),
    "ちきゅうなげ": MoveData(
        type="かくとう",
        category="physical",
        pp=20,
        power=0,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.level_fixed_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "チャージビーム": MoveData(
        type="でんき",
        category="special",
        pp=10,
        power=50,
        accuracy=90,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.チャージビーム_boost_spa_C,
            )
        }
    ),
    "チャームボイス": MoveData(
        type="フェアリー",
        category="special",
        pp=15,
        power=40,
        flags={"sound"},
        handlers={},  # 追加効果なし
    ),
    "ちょうおんぱ": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        accuracy=55,
        flags={"sound"},
        handlers={},  # 追加効果なし
    ),
    "ちょうのまい": MoveData(
        type="むし",
        category="status",
        pp=20,
        flags={"dance"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ちょうのまい_modify_attacker_stats,
            ),
        }
    ),
    "ちょうはつ": MoveData(
        type="あく",
        category="status",
        pp=20,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ちょうはつ_apply,
            ),
        }
    ),
    "ついばむ": MoveData(
        type="ひこう",
        category="physical",
        pp=20,
        power=60,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.むしくい_steal_and_use_berry)
        }
    ),
    "ツインビーム": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=40,
        accuracy=100,
        multi_hit={
            "min": 2,
            "max": 2,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "つきのひかり": MoveData(
        type="フェアリー",
        category="status",
        pp=5,
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あさのひざし_heal_self,
            )
        }
    ),
    "つけあがる": MoveData(
        type="あく",
        category="physical",
        pp=10,
        power=20,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.つけあがる_calc_power,
            ),
        }
    ),
    "つじぎり": MoveData(
        type="あく",
        category="physical",
        pp=15,
        power=70,
        accuracy=100,
        critical_rank=1,
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "ツタこんぼう": MoveData(
        type="くさ",
        category="physical",
        pp=10,
        power=100,
        accuracy=100,
        critical_rank=1,
        handlers={},  # 追加効果なし
    ),
    "つっぱり": MoveData(
        type="かくとう",
        category="physical",
        pp=20,
        power=15,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "つつく": MoveData(
        type="ひこう",
        category="physical",
        pp=35,
        power=35,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "つのでつく": MoveData(
        type="ノーマル",
        category="physical",
        pp=25,
        power=65,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "つのドリル": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=0,
        accuracy=30,
        flags={"ohko", "contact"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.ohko_damage,
            ),
        }
    ),
    "つばさでうつ": MoveData(
        type="ひこう",
        category="physical",
        pp=35,
        power=60,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "つばめがえし": MoveData(
        type="ひこう",
        category="physical",
        pp=20,
        power=60,
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "つぶらなひとみ": MoveData(
        type="フェアリー",
        category="status",
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
        category="status",
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
        category="status",
        pp=15,
        handlers={},  # 追加効果なし
    ),
    "つららおとし": MoveData(
        type="こおり",
        category="physical",
        pp=10,
        power=85,
        accuracy=90,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.つららおとし_apply_flinch,
            )
        }
    ),
    "つららばり": MoveData(
        type="こおり",
        category="physical",
        pp=30,
        power=25,
        accuracy=100,
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "つるぎのまい": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        target="self",
        flags={"dance"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.つるぎのまい_modify_attacker_stats,
            ),
        }
    ),
    "つるのムチ": MoveData(
        type="くさ",
        category="physical",
        pp=25,
        power=45,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "テクスチャー": MoveData(
        type="ノーマル",
        category="status",
        pp=30,
        handlers={},  # 追加効果なし
    ),
    "テクスチャー２": MoveData(
        type="ノーマル",
        category="status",
        pp=30,
        handlers={},  # 追加効果なし
    ),
    "てだすけ": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        accuracy=100,
        priority=5,
        handlers={},  # 追加効果なし
    ),
    "てっていこうせん": MoveData(
        type="はがね",
        category="special",
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
    "てっぺき": MoveData(
        type="はがね",
        category="status",
        pp=15,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.てっぺき_modify_attacker_stats,
            )
        }
    ),
    "テラクラスター": MoveData(
        type="ノーマル",
        category="special",
        pp=5,
        power=120,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "テラバースト": MoveData(
        type="ノーマル",
        category="special",
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
    "テレポート": MoveData(
        type="エスパー",
        category="status",
        pp=20,
        priority=-6,
        handlers={},  # 追加効果なし
    ),
    "てんしのキッス": MoveData(
        type="フェアリー",
        category="status",
        pp=10,
        accuracy=75,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.てんしのキッス_apply,
            ),
        }
    ),
    "であいがしら": MoveData(
        type="むし",
        category="physical",
        pp=10,
        power=90,
        accuracy=100,
        priority=2,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "デカハンマー": MoveData(
        type="はがね",
        category="physical",
        pp=5,
        power=160,
        accuracy=100,
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.デカハンマー_apply_reuse_block,
                subject_spec="attacker:self",
                priority=50,
            ),
        }
    ),
    "デコレーション": MoveData(
        type="フェアリー",
        category="status",
        pp=15,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "デスウイング": MoveData(
        type="ひこう",
        category="physical",
        pp=10,
        power=90,
        accuracy=100,
        flags={"contact", "heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.デスウイング_drain,
            )
        }
    ),
    "でんきショック": MoveData(
        type="でんき",
        category="special",
        pp=30,
        power=40,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.でんきショック_apply_ailment_to_defender,
            )
        }
    ),
    "でんげきは": MoveData(
        type="でんき",
        category="special",
        pp=20,
        power=60,
        accuracy=None,
        handlers={},  # 追加効果なし
    ),
    "でんこうせっか": MoveData(
        type="ノーマル",
        category="physical",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "でんこうそうげき": MoveData(
        type="でんき",
        category="physical",
        pp=5,
        power=120,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "でんじは": MoveData(
        type="でんき",
        category="status",
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
        category="status",
        pp=10,
        flags={"gravity_restricted"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                h.gravity_restricted_fail,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.でんじふゆう_apply,
            ),
        }
    ),
    "でんじほう": MoveData(
        type="でんき",
        category="special",
        pp=5,
        power=120,
        accuracy=50,
        flags={"bullet", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.でんじほう_apply_ailment_to_defender,
            ),
        }
    ),
    "とおせんぼう": MoveData(
        type="ノーマル",
        category="status",
        pp=5,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.とおせんぼう_apply,
            ),
        }
    ),
    "とおぼえ": MoveData(
        type="ノーマル",
        category="status",
        pp=40,
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.とおぼえ_modify_attacker_stats,
            ),
        }
    ),
    "ときのほうこう": MoveData(
        type="ドラゴン",
        category="special",
        pp=5,
        power=150,
        accuracy=90,
        handlers={},  # 追加効果なし
    ),
    "とぐろをまく": MoveData(
        type="どく",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.とぐろをまく_modify_attacker_stats,
            ),
        }
    ),
    "とける": MoveData(
        type="どく",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.とける_modify_attacker_stats,
            ),
        }
    ),
    "とっしん": MoveData(
        type="ノーマル",
        category="physical",
        pp=20,
        power=90,
        accuracy=85,
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.とっしん_recoil,
            )
        }
    ),
    "とっておき": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=140,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "とどめばり": MoveData(
        type="むし",
        category="physical",
        pp=25,
        power=50,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.とどめばり_boost_attacker_atk,
                priority=100,
            )
        }
    ),
    "とびかかる": MoveData(
        type="むし",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.とびかかる_reduce_defender_atk,
            )
        }
    ),
    "とびげり": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=85,
        accuracy=90,
        flags={"contact", "gravity_restricted"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                h.gravity_restricted_fail,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_MISS: h.MoveHandler(
                ha.とびげり_crash,
            ),
        }
    ),
    "とびつく": MoveData(
        type="むし",
        category="physical",
        pp=20,
        power=50,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.とびつく_reduce_defender_atk,
            )
        }
    ),
    "とびはねる": MoveData(
        type="ひこう",
        category="physical",
        pp=5,
        power=85,
        accuracy=85,
        flags={"contact", "gravity_restricted", "secondary_effect"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                h.gravity_restricted_fail,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.とびはねる_apply_ailment_to_defender,
            )
        }
    ),
    "とびひざげり": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=130,
        accuracy=90,
        flags={"contact", "gravity_restricted"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                h.gravity_restricted_fail,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_MISS: h.MoveHandler(
                ha.とびひざげり_crash,
            ),
        }
    ),
    "ともえなげ": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=60,
        accuracy=90,
        priority=-6,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ともえなげ_force_switch,
            )
        }
    ),
    "トライアタック": MoveData(
        type="ノーマル",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.トライアタック_apply_ailment_to_defender,
            )
        }
    ),
    "トラップシェル": MoveData(
        type="はがね",
        category="special",
        pp=5,
        power=150,
        accuracy=100,
        priority=-5,
        flags={"non_negoto"},
        handlers={},  # 追加効果なし
    ),
    "トラバサミ": MoveData(
        type="はがね",
        category="physical",
        pp=16,
        power=35,
        accuracy=100,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "トリック": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.すりかえ_swap_items,
            )
        }
    ),
    "トリックフラワー": MoveData(
        type="くさ",
        category="physical",
        pp=10,
        power=70,
        critical_rank=3,
        handlers={},  # 追加効果なし
    ),
    "トリックルーム": MoveData(
        type="エスパー",
        category="status",
        pp=5,
        priority=-7,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.トリックルーム_activate_global_field,
            ),
        }
    ),
    "トリプルアクセル": MoveData(
        type="こおり",
        category="physical",
        pp=10,
        power=20,
        accuracy=90,
        flags={"contact", "check_hit_each_time"},
        multi_hit={
            "min": 3,
            "max": 3,
            "check_hit_each_time": True,
            "power_sequence": (20, 40, 60),
        },
        handlers={},  # 追加効果なし
    ),
    "トリプルキック": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=10,
        accuracy=90,
        flags={"contact"},
        multi_hit={
            "min": 3,
            "max": 3,
            "check_hit_each_time": True,
            "power_sequence": (10, 20, 30),
        },
        handlers={},  # 追加効果なし
    ),
    "トリプルダイブ": MoveData(
        type="みず",
        category="physical",
        pp=10,
        power=30,
        accuracy=95,
        flags={"contact"},
        multi_hit={
            "min": 3,
            "max": 3,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "トロピカルキック": MoveData(
        type="くさ",
        category="physical",
        pp=15,
        power=70,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.トロピカルキック_reduce_defender_atk,
            )
        }
    ),
    "とんぼがえり": MoveData(
        type="むし",
        category="physical",
        pp=20,
        power=70,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.pivot,
            )
        }
    ),
    "トーチカ": MoveData(
        type="どく",
        category="status",
        pp=10,
        priority=4,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.トーチカ_apply,
            ),
        }
    ),
    "どくガス": MoveData(
        type="どく",
        category="status",
        pp=40,
        accuracy=90,
        handlers={},  # TODO : 効果実装
    ),
    "どくづき": MoveData(
        type="どく",
        category="physical",
        pp=20,
        power=80,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どくづき_apply_ailment_to_defender,
            )
        }
    ),
    "どくどく": MoveData(
        type="どく",
        category="status",
        pp=10,
        accuracy=90,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.どくどく_apply_ailment_to_defender,
            ),
        }
    ),
    "どくどくのキバ": MoveData(
        type="どく",
        category="physical",
        pp=15,
        power=50,
        accuracy=100,
        flags={"bite", "contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どくどくのキバ_apply_ailment_to_defender,
            )
        }
    ),
    "どくのいと": MoveData(
        type="どく",
        category="status",
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
        category="status",
        pp=35,
        accuracy=75,
        flags={"powder"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.どくのこな_apply_ailment_to_defender,
            ),
        }
    ),
    "どくばり": MoveData(
        type="どく",
        category="physical",
        pp=35,
        power=15,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どくばり_apply_ailment_to_defender,
            )
        }
    ),
    "どくばりセンボン": MoveData(
        type="どく",
        category="physical",
        pp=10,
        power=60,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どくばりセンボン_apply_ailment_to_defender,
            )
        }
    ),
    "どくびし": MoveData(
        type="どく",
        category="status",
        pp=20,
        target="foe_side",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.どくびし_set_field,
            ),
        }
    ),
    "どげざつき": MoveData(
        type="あく",
        category="physical",
        pp=10,
        power=80,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "ドゲザン": MoveData(
        type="あく",
        category="physical",
        pp=10,
        power=85,
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "ドラゴンアロー": MoveData(
        type="ドラゴン",
        category="physical",
        pp=10,
        power=50,
        accuracy=100,
        multi_hit={
            "min": 2,
            "max": 2,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "ドラゴンエナジー": MoveData(
        type="ドラゴン",
        category="special",
        pp=5,
        power=150,
        accuracy=100,
        handlers={},  # TODO : 効果実装 (しおふきと同じ)
    ),
    "ドラゴンエール": MoveData(
        type="ドラゴン",
        category="status",
        pp=15,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "ドラゴンクロー": MoveData(
        type="ドラゴン",
        category="physical",
        pp=16,
        power=80,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "ドラゴンダイブ": MoveData(
        type="ドラゴン",
        category="physical",
        pp=10,
        power=100,
        accuracy=75,
        flags={"minimize", "contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ドラゴンダイブ_apply_flinch,
            )
        }
    ),
    "ドラゴンテール": MoveData(
        type="ドラゴン",
        category="physical",
        pp=10,
        power=60,
        accuracy=90,
        priority=-6,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ドラゴンテール_force_switch,
            )
        }
    ),
    "ドラゴンハンマー": MoveData(
        type="ドラゴン",
        category="physical",
        pp=15,
        power=90,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "ドラムアタック": MoveData(
        type="くさ",
        category="physical",
        pp=10,
        power=80,
        accuracy=100,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ドラムアタック_reduce_defender_spd,
            )
        }
    ),
    "ドリルくちばし": MoveData(
        type="ひこう",
        category="physical",
        pp=20,
        power=80,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "ドリルライナー": MoveData(
        type="じめん",
        category="physical",
        pp=10,
        power=80,
        accuracy=95,
        critical_rank=1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "ドレインキッス": MoveData(
        type="フェアリー",
        category="special",
        pp=10,
        power=50,
        accuracy=100,
        flags={"contact", "heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.ドレインキッス_drain, priority=20)
        }
    ),
    "ドレインパンチ": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=75,
        accuracy=100,
        flags={"contact", "punch", "heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.ドレインパンチ_drain, priority=20)
        }
    ),
    "どろかけ": MoveData(
        type="じめん",
        category="special",
        pp=10,
        power=20,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どろかけ_reduce_acc,
            )
        }
    ),
    "どろばくだん": MoveData(
        type="じめん",
        category="special",
        pp=10,
        power=65,
        accuracy=85,
        flags={"bullet", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どろばくだん_reduce_acc,
            )
        }
    ),
    "どろぼう": MoveData(
        type="あく",
        category="physical",
        pp=25,
        power=60,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.どろぼう_steal_item,
            )
        }
    ),
    "ドわすれ": MoveData(
        type="エスパー",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ドわすれ_modify_attacker_stats,
            )
        }
    ),
    "ないしょばなし": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        flags={"sound"},
        handlers={},  # TODO : 効果実装
    ),
    "ナイトバースト": MoveData(
        type="あく",
        category="special",
        pp=10,
        power=85,
        accuracy=95,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ナイトバースト_reduce_acc,
            )
        }
    ),
    "ナイトヘッド": MoveData(
        type="ゴースト",
        category="special",
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
    "なかまづくり": MoveData(
        type="ノーマル",
        category="status",
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
        category="status",
        pp=20,
        handlers={},  # TODO: 効果実装
    ),
    "なきごえ": MoveData(
        type="ノーマル",
        category="status",
        pp=40,
        accuracy=100,
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.なきごえ_modify_defender_stats,
            )
        }
    ),
    "なげつける": MoveData(
        type="あく",
        category="physical",
        pp=10,
        power=1,
        accuracy=100,
        handlers={},  # TODO: 効果実装
    ),
    "なまける": MoveData(
        type="ノーマル",
        category="status",
        pp=5,
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.なまける_heal_self,
            ),
        }
    ),
    "なみだめ": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.なみだめ_modify_defender_stats,
            )
        }
    ),
    "なみのり": MoveData(
        type="みず",
        category="special",
        pp=16,
        power=90,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "なやみのタネ": MoveData(
        type="くさ",
        category="status",
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
        category="status",
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
    "にぎりつぶす": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=1,
        accuracy=100,
        flags={"contact"},
        handlers={},  # TODO: 効果実装
    ),
    "ニトロチャージ": MoveData(
        type="ほのお",
        category="physical",
        pp=20,
        power=50,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ニトロチャージ_boost_attacker_spe,
            )
        }
    ),
    "にどげり": MoveData(
        type="かくとう",
        category="physical",
        pp=30,
        power=30,
        accuracy=100,
        flags={"contact"},
        multi_hit={
            "min": 2,
            "max": 2,
            "check_hit_each_time": True,
            "power_sequence": (30, 30),
        },
        handlers={},  # 追加効果なし
    ),
    "にほんばれ": MoveData(
        type="ほのお",
        category="status",
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
        category="status",
        pp=30,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.にらみつける_modify_defender_stats,
            )
        }
    ),
    "ニードルアーム": MoveData(
        type="くさ",
        category="physical",
        pp=15,
        power=60,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ニードルアーム_apply_flinch,
            )
        }
    ),
    "ニードルガード": MoveData(
        type="くさ",
        category="status",
        pp=10,
        priority=4,
        target="self",
        flags={"protect"},
        handlers={
            Event.ON_TRY_MOVE_2: h.MoveHandler(
                hs.まもる系_連続使用失敗チェック,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ニードルガード_apply,
            ),
        }
    ),
    "ねがいごと": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        target="field",
        flags={"heal"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ねがいごと_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ねがいごと_set_side_field,
            ),
        }
    ),
    "ねこだまし": MoveData(
        type="ノーマル",
        category="physical",
        pp=10,
        power=40,
        accuracy=100,
        priority=3,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねこだまし_apply_flinch,
            )
        }
    ),
    "ネコにこばん": MoveData(
        type="ノーマル",
        category="physical",
        pp=20,
        power=40,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "ねごと": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        flags={"non_encore", "non_negoto"},
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
    "ネズミざん": MoveData(
        type="ノーマル",
        category="physical",
        pp=10,
        power=20,
        accuracy=90,
        flags={"contact", "slash", "check_hit_each_time"},
        multi_hit={
            "min": 10,
            "max": 10,
            "check_hit_each_time": True,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "ねっさのあらし": MoveData(
        type="じめん",
        category="special",
        pp=10,
        power=100,
        accuracy=80,
        flags={"wind", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねっさのあらし_apply_ailment_to_defender,
            )
        }
    ),
    "ねっさのだいち": MoveData(
        type="じめん",
        category="special",
        pp=10,
        power=70,
        accuracy=100,
        flags={"secondary_effect", "thaw"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねっさのだいち_apply_ailment_to_defender,
            )
        }
    ),
    "ねっとう": MoveData(
        type="みず",
        category="special",
        pp=15,
        power=80,
        accuracy=100,
        flags={"secondary_effect", "thaw"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねっとう_apply_ailment_to_defender,
            )
        }
    ),
    "ねっぷう": MoveData(
        type="ほのお",
        category="special",
        pp=10,
        power=95,
        accuracy=90,
        flags={"wind", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねっぷう_apply_ailment_to_defender,
            )
        }
    ),
    "ねばねばネット": MoveData(
        type="むし",
        category="status",
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
        category="status",
        pp=15,
        accuracy=75,
        flags={"powder"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ねむりごな_apply_ailment_to_defender,
            ),
        }
    ),
    "ねむる": MoveData(
        type="エスパー",
        category="status",
        pp=5,
        flags={"heal"},
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
    "ねらいうち": MoveData(
        type="みず",
        category="special",
        pp=15,
        power=80,
        accuracy=100,
        critical_rank=1,
        handlers={},  # 追加効果なし
    ),
    "ねをはる": MoveData(
        type="くさ",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ねをはる_apply,
            ),
        }
    ),
    "ねんりき": MoveData(
        type="エスパー",
        category="special",
        pp=25,
        power=50,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねんりき_apply_confusion_to_defender,
            )
        }
    ),
    "のしかかり": MoveData(
        type="ノーマル",
        category="physical",
        pp=15,
        power=85,
        accuracy=100,
        flags={"minimize", "contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.のしかかり_apply_ailment_to_defender,
            )
        }
    ),
    "のみこむ": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        flags={"heal"},
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
        category="status",
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
    "はいすいのじん": MoveData(
        type="かくとう",
        category="status",
        pp=5,
        handlers={},  # TODO: 効果実装
    ),
    "ハイドロカノン": MoveData(
        type="みず",
        category="special",
        pp=5,
        power=150,
        accuracy=90,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.リチャージ_apply,
            )
        }
    ),
    "ハイドロスチーム": MoveData(
        type="みず",
        category="special",
        pp=15,
        power=80,
        accuracy=100,
        flags={"thaw"},
        handlers={},  # TODO: 効果実装
    ),
    "ハイドロポンプ": MoveData(
        type="みず",
        category="special",
        pp=8,
        power=110,
        accuracy=80,
        handlers={},  # 追加効果なし
    ),
    "ハイパードリル": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=100,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "ハイパーボイス": MoveData(
        type="ノーマル",
        category="special",
        pp=12,
        power=90,
        accuracy=100,
        flags={"sound"},
        handlers={},  # 追加効果なし
    ),
    "はいよるいちげき": MoveData(
        type="むし",
        category="physical",
        pp=10,
        power=70,
        accuracy=90,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.はいよるいちげき_lower_spa_C,
            )
        }
    ),
    "はかいこうせん": MoveData(
        type="ノーマル",
        category="special",
        pp=5,
        power=150,
        accuracy=90,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.リチャージ_apply,
            )
        }
    ),
    "はがねのつばさ": MoveData(
        type="はがね",
        category="physical",
        pp=25,
        power=70,
        accuracy=90,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.はがねのつばさ_boost_defender_B,
            )
        }
    ),
    "はきだす": MoveData(
        type="ノーマル",
        category="special",
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
    "ハサミギロチン": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=0,
        accuracy=30,
        flags={"ohko", "contact"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.ohko_damage,
            ),
        }
    ),
    "はさむ": MoveData(
        type="ノーマル",
        category="physical",
        pp=30,
        power=55,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "はたきおとす": MoveData(
        type="あく",
        category="physical",
        pp=20,
        power=65,
        accuracy=100,
        flags={"contact"},
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
        category="physical",
        pp=20,
        power=40,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "はっけい": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=60,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.はっけい_apply_ailment_to_defender,
            )
        }
    ),
    "はっぱカッター": MoveData(
        type="くさ",
        category="physical",
        pp=25,
        power=55,
        accuracy=95,
        critical_rank=1,
        flags={"slash"},
        handlers={},  # 追加効果なし
    ),
    "ハッピータイム": MoveData(
        type="ノーマル",
        category="status",
        pp=30,
        handlers={},  # 追加効果なし
    ),
    "はどうだん": MoveData(
        type="かくとう",
        category="special",
        pp=20,
        power=80,
        flags={"bullet", "pulse"},
        handlers={},  # 追加効果なし
    ),
    "はなびらのまい": MoveData(
        type="くさ",
        category="special",
        pp=10,
        power=120,
        accuracy=100,
        flags={"contact", "dance"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.あばれる_apply,
            ),
        }
    ),
    "はなふぶき": MoveData(
        type="くさ",
        category="physical",
        pp=16,
        power=90,
        accuracy=100,
        flags={"wind"},
        handlers={},  # 追加効果なし
    ),
    "はねやすめ": MoveData(
        type="ひこう",
        category="status",
        pp=5,
        flags={"heal"},
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
        category="status",
        pp=40,
        flags={"gravity_restricted"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                h.gravity_restricted_fail,
                subject_spec="attacker:self",
                priority=30,
            ),
        },
    ),
    "ハバネロエキス": MoveData(
        type="くさ",
        category="status",
        pp=15,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ハバネロエキス_apply,
            ),
        }
    ),
    "はめつのねがい": MoveData(
        type="はがね",
        category="special",
        pp=5,
        power=140,
        accuracy=100,
        handlers={},  # TODO: 効果実装
    ),
    "はめつのひかり": MoveData(
        type="ゴースト",
        category="special",
        pp=5,
        power=150,
        accuracy=100,
        flags={"recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.はめつのひかり_recoil,
            )
        }
    ),
    "はやてがえし": MoveData(
        type="かくとう",
        category="physical",
        pp=15,
        power=65,
        accuracy=100,
        priority=3,
        flags={"contact"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.はやてがえし_try_move,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.はやてがえし_apply_flinch,
            ),
        }
    ),
    "はらだいこ": MoveData(
        type="ノーマル",
        category="status",
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
    "はるのあらし": MoveData(
        type="フェアリー",
        category="special",
        pp=5,
        power=100,
        accuracy=80,
        flags={"wind", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.はるのあらし_reduce_defender_atk,
            )
        }
    ),
    "ハロウィン": MoveData(
        type="ゴースト",
        category="status",
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
    "ハートスタンプ": MoveData(
        type="エスパー",
        category="physical",
        pp=25,
        power=60,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ハートスタンプ_apply_flinch,
            )
        }
    ),
    "ハートスワップ": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        accuracy=100,
        handlers={},  # TODO: 効果実装
    ),
    "ハードプラント": MoveData(
        type="くさ",
        category="special",
        pp=5,
        power=150,
        accuracy=90,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.リチャージ_apply,
            )
        }
    ),
    "ハードプレス": MoveData(
        type="はがね",
        category="physical",
        pp=10,
        power=1,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ハードプレス_calc_power,
            ),
        }
    ),
    "ハードローラー": MoveData(
        type="ノーマル",
        category="physical",
        pp=10,
        power=100,
        accuracy=95,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ハードローラー_apply_flinch,
            )
        }
    ),
    "ばかぢから": MoveData(
        type="かくとう",
        category="physical",
        pp=5,
        power=120,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ばかぢから_reduce_attacker_def,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.ばかぢから_lower_atk)
        }
    ),
    "ばくおんぱ": MoveData(
        type="ノーマル",
        category="special",
        pp=12,
        power=140,
        accuracy=100,
        flags={"sound"},
        handlers={},  # 追加効果なし
    ),
    "ばくれつパンチ": MoveData(
        type="かくとう",
        category="physical",
        pp=5,
        power=100,
        accuracy=50,
        flags={"contact", "punch", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ばくれつパンチ_apply_confusion_to_defender,
            )
        }
    ),
    "バトンタッチ": MoveData(
        type="ノーマル",
        category="status",
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
    "バブルこうせん": MoveData(
        type="みず",
        category="special",
        pp=20,
        power=65,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.バブルこうせん_reduce_defender_spd,
            )
        }
    ),
    "バリアーラッシュ": MoveData(
        type="エスパー",
        category="physical",
        pp=10,
        power=70,
        accuracy=90,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.バリアーラッシュ_boost_defender_B,
            )
        }
    ),
    "バレットパンチ": MoveData(
        type="はがね",
        category="physical",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        flags={"contact", "punch"},
        handlers={},  # 追加効果なし
    ),
    "バークアウト": MoveData(
        type="あく",
        category="special",
        pp=15,
        power=55,
        accuracy=95,
        flags={"sound"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.バークアウト_lower_spa_C,
            )
        }
    ),
    "バーンアクセル": MoveData(
        type="ほのお",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.バーンアクセル_apply_ailment_to_defender,
            )
        }
    ),
    "パラボラチャージ": MoveData(
        type="でんき",
        category="special",
        pp=20,
        power=65,
        accuracy=100,
        flags={"heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.パラボラチャージ_drain, priority=20)
        }
    ),
    "パワフルエッジ": MoveData(
        type="いわ",
        category="physical",
        pp=5,
        power=95,
        accuracy=100,
        flags={"contact"},
        handlers={},  # TODO: 効果実装
    ),
    "パワーウィップ": MoveData(
        type="くさ",
        category="physical",
        pp=12,
        power=120,
        accuracy=85,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "パワーシェア": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.パワーシェア_equalize_stats,
            ),
        }
    ),
    "パワージェム": MoveData(
        type="いわ",
        category="special",
        pp=20,
        power=80,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "パワースワップ": MoveData(
        type="エスパー",
        category="status",
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
        category="status",
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
        category="status",
        pp=30,
        target="own_side",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ひかりのかべ_set_side_field,
            ),
        }
    ),
    "ひけん・ちえなみ": MoveData(
        type="あく",
        category="physical",
        pp=15,
        power=65,
        accuracy=90,
        flags={"contact"},
        handlers={},  # TODO: 効果実装
    ),
    "ひっかく": MoveData(
        type="ノーマル",
        category="physical",
        pp=35,
        power=40,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "ひっくりかえす": MoveData(
        type="あく",
        category="status",
        pp=20,
        accuracy=100,
        handlers={},  # TODO: 効果実装
    ),
    "ひっさつまえば": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=120,
        accuracy=90,
        flags={"bite", "contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ひっさつまえば_apply_flinch,
            )
        }
    ),
    "ひのこ": MoveData(
        type="ほのお",
        category="special",
        pp=25,
        power=40,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ひのこ_apply_ailment_to_defender,
            )
        }
    ),
    "ひゃっきやこう": MoveData(
        type="ゴースト",
        category="special",
        pp=15,
        power=60,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ひゃっきやこう_double_power_when_ailment,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ひゃっきやこう_apply_ailment_to_defender,
            )
        }
    ),
    "ひやみず": MoveData(
        type="みず",
        category="special",
        pp=20,
        power=50,
        accuracy=100,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ひやみず_reduce_defender_atk,
            )
        }
    ),
    "ひょうざんおろし": MoveData(
        type="こおり",
        category="physical",
        pp=10,
        power=100,
        accuracy=85,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ひょうざんおろし_apply_flinch,
            )
        }
    ),
    "ヒートスタンプ": MoveData(
        type="ほのお",
        category="physical",
        pp=10,
        power=1,
        accuracy=100,
        flags={"minimize", "contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ヒートスタンプ_calc_power,
            ),
        }
    ),
    "ビックリヘッド": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=130,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.ビックリヘッド_pay_hp,
                subject_spec="attacker:self",
            ),
        }
    ),
    "びりびりちくちく": MoveData(
        type="でんき",
        category="physical",
        pp=10,
        power=80,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.びりびりちくちく_apply_flinch,
            )
        }
    ),
    "ビルドアップ": MoveData(
        type="かくとう",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ビルドアップ_modify_attacker_stats,
            ),
        }
    ),
    "ピヨピヨパンチ": MoveData(
        type="ノーマル",
        category="physical",
        pp=15,
        power=70,
        accuracy=100,
        flags={"contact", "punch", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ピヨピヨパンチ_apply_confusion_to_defender,
            )
        }
    ),
    "ファストガード": MoveData(
        type="かくとう",
        category="status",
        pp=15,
        priority=3,
        handlers={},  # TODO: 効果実装
    ),
    "ふいうち": MoveData(
        type="あく",
        category="physical",
        pp=5,
        power=70,
        accuracy=100,
        priority=1,
        flags={"contact"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.ふいうち_try_move,
                priority=30,
            ),
        }
    ),
    "ふういん": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ふういん_apply,
            ),
        }
    ),
    "フェアリーロック": MoveData(
        type="フェアリー",
        category="status",
        pp=10,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.フェアリーロック_activate_global_field,
            ),
        }
    ),
    "フェイタルクロー": MoveData(
        type="どく",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.フェイタルクロー_apply_ailment_to_defender,
            )
        }
    ),
    "フェイント": MoveData(
        type="ノーマル",
        category="physical",
        pp=10,
        power=30,
        accuracy=100,
        priority=2,
        flags={"unprotectable"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.フェイント_remove_protect,
            )
        }
    ),
    "フェザーダンス": MoveData(
        type="ひこう",
        category="status",
        pp=15,
        accuracy=100,
        flags={"dance"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.フェザーダンス_modify_defender_stats,
            )
        }
    ),
    "フォトンゲイザー": MoveData(
        type="エスパー",
        category="special",
        pp=5,
        power=100,
        accuracy=100,
        handlers={},  # TODO: 効果実装
    ),
    "ふきとばし": MoveData(
        type="ノーマル",
        category="special",
        pp=20,
        priority=-6,
        flags={"wind"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.on_blow_apply,
                priority=30,
            ),
            Event.ON_HIT: h.MoveHandler(hs.blow),
        }
    ),
    "ふくろだたき": MoveData(
        type="あく",
        category="physical",
        pp=10,
        power=0,
        accuracy=100,
        handlers={},  # TODO: 効果実装
    ),
    "ふしょくガス": MoveData(
        type="どく",
        category="status",
        pp=40,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                ha.ふしょくガス_remove_item,
            )
        }
    ),
    "ふぶき": MoveData(
        type="こおり",
        category="special",
        pp=5,
        power=110,
        accuracy=70,
        flags={"wind", "secondary_effect"},
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
    "ふみつけ": MoveData(
        type="ノーマル",
        category="physical",
        pp=20,
        power=65,
        accuracy=100,
        flags={"minimize", "contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ふみつけ_apply_flinch,
            )
        }
    ),
    "フライングプレス": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=100,
        accuracy=95,
        flags={"contact", "gravity_restricted", "minimize"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                h.gravity_restricted_fail,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_CALC_DEF_TYPE_MODIFIER: h.MoveHandler(
                ha.フライングプレス_add_flying_type,
            ),
        }
    ),
    "フラフラダンス": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        accuracy=100,
        flags={"dance"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.フラフラダンス_apply,
            ),
        }
    ),
    "フラワーヒール": MoveData(
        type="フェアリー",
        category="status",
        pp=10,
        flags={"heal"},
        handlers={},  # TODO: 効果実装
    ),
    "フリーズドライ": MoveData(
        type="こおり",
        category="special",
        pp=20,
        power=70,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_CALC_DEF_TYPE_MODIFIER: h.MoveHandler(
                ha.フリーズドライ_water_effectiveness,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.フリーズドライ_apply_ailment_to_defender,
            )
        }
    ),
    "フリーズボルト": MoveData(
        type="こおり",
        category="physical",
        pp=5,
        power=140,
        accuracy=90,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.フリーズボルト_apply_ailment_to_defender,
            )
        }
    ),
    "ふるいたてる": MoveData(
        type="ノーマル",
        category="status",
        pp=30,
        handlers={},  # TODO: 効果実装
    ),
    "フルールカノン": MoveData(
        type="フェアリー",
        category="special",
        pp=5,
        power=130,
        accuracy=90,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.フルールカノン_sharply_lower_spa_C,
            )
        }
    ),
    "フレアソング": MoveData(
        type="ほのお",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.フレアソング_boost_spa_C,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.フレアソング_boost_spa)
        }
    ),
    "フレアドライブ": MoveData(
        type="ほのお",
        category="physical",
        pp=15,
        power=120,
        accuracy=100,
        flags={"contact", "recoil", "secondary_effect", "thaw"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.フレアドライブ_recoil,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.フレアドライブ_apply_ailment_to_defender,
            ),
        }
    ),
    "ふわふわフォール": MoveData(
        type="フェアリー",
        category="physical",
        pp=15,
        power=70,
        accuracy=95,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ふわふわフォール_apply_flinch,
            )
        }
    ),
    "ふんえん": MoveData(
        type="ほのお",
        category="special",
        pp=15,
        power=80,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ふんえん_apply_ailment_to_defender,
            )
        }
    ),
    "ふんか": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=150,
        accuracy=100,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ふんか_calc_power,
            ),
        }
    ),
    "ふんどのこぶし": MoveData(
        type="ゴースト",
        category="physical",
        pp=10,
        power=50,
        accuracy=100,
        flags={"contact", "punch"},
        handlers={},  # TODO: 効果実装
    ),
    "ぶきみなじゅもん": MoveData(
        type="エスパー",
        category="special",
        pp=5,
        power=80,
        accuracy=100,
        flags={"sound"},
        handlers={},  # TODO: 効果実装
    ),
    "ぶちかまし": MoveData(
        type="じめん",
        category="physical",
        pp=5,
        power=120,
        accuracy=100,
        flags={"contact", "punch", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ぶちかまし_reduce_defender_spd,
            )
        }
    ),
    "ブラストバーン": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=150,
        accuracy=90,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.リチャージ_apply,
            )
        }
    ),
    "ブラッドムーン": MoveData(
        type="ノーマル",
        category="special",
        pp=5,
        power=140,
        accuracy=100,
        handlers={},  # TODO: 効果実装
    ),
    "ブリザードランス": MoveData(
        type="こおり",
        category="physical",
        pp=5,
        power=120,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "ブレイククロー": MoveData(
        type="ノーマル",
        category="physical",
        pp=10,
        power=75,
        accuracy=95,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ブレイククロー_lower_defender_def,
            )
        }
    ),
    "ブレイズキック": MoveData(
        type="ほのお",
        category="physical",
        pp=10,
        power=85,
        accuracy=90,
        critical_rank=1,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ブレイズキック_apply_ailment_to_defender,
            )
        }
    ),
    "ブレイブチャージ": MoveData(
        type="エスパー",
        category="status",
        pp=15,
        handlers={},  # TODO: 効果実装
    ),
    "ブレイブバード": MoveData(
        type="ひこう",
        category="physical",
        pp=15,
        power=120,
        accuracy=100,
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ブレイブバード_recoil,
            )
        }
    ),
    "ぶんまわす": MoveData(
        type="あく",
        category="physical",
        pp=20,
        power=60,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "プリズムレーザー": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=160,
        accuracy=100,
        handlers={},  # TODO: 効果実装
    ),
    "プレゼント": MoveData(
        type="ノーマル",
        category="physical",
        pp=15,
        power=0,
        accuracy=90,
        handlers={},  # TODO: 効果実装
    ),
    "ヘドロウェーブ": MoveData(
        type="どく",
        category="special",
        pp=10,
        power=95,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ヘドロウェーブ_apply_ailment_to_defender,
            )
        }
    ),
    "ヘドロこうげき": MoveData(
        type="どく",
        category="special",
        pp=20,
        power=65,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ヘドロこうげき_apply_ailment_to_defender,
            )
        }
    ),
    "ヘドロばくだん": MoveData(
        type="どく",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        flags={"bullet", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ヘドロばくだん_apply_ailment_to_defender,
            )
        }
    ),
    "へびにらみ": MoveData(
        type="ノーマル",
        category="status",
        pp=30,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.へびにらみ_apply_ailment_to_defender,
            ),
        }
    ),
    "ヘビーボンバー": MoveData(
        type="はがね",
        category="physical",
        pp=10,
        power=1,
        accuracy=100,
        flags={"minimize", "contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ヘビーボンバー_calc_power,
            ),
        }
    ),
    "へんしん": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        accuracy=100,
        flags={"non_encore"},
        handlers={},  # 実装保留
    ),
    "ベノムショック": MoveData(
        type="どく",
        category="special",
        pp=10,
        power=65,
        accuracy=100,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ベノムショック_double_power_when_poisoned,
            ),
        }
    ),
    "ホイールスピン": MoveData(
        type="はがね",
        category="physical",
        pp=5,
        power=100,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ホイールスピン_sharply_reduce_attacker_spe,
            )
        }
    ),
    "ほうでん": MoveData(
        type="でんき",
        category="special",
        pp=15,
        power=80,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ほうでん_apply_ailment_to_defender,
            )
        }
    ),
    "ほうふく": MoveData(
        type="あく",
        category="physical",
        pp=10,
        power=0,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.ほうふく_check_can_use,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.ほうふく_modify_damage,
                subject_spec="attacker:self",
            ),
        },
    ),
    "ほえる": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        priority=-6,
        flags={"sound"},
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
        category="status",
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
    "ほしがる": MoveData(
        type="ノーマル",
        category="physical",
        pp=25,
        power=60,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.どろぼう_steal_item,
            )
        }
    ),
    "ほたるび": MoveData(
        type="むし",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ほたるび_modify_attacker_stats,
            )
        }
    ),
    "ほっぺすりすり": MoveData(
        type="でんき",
        category="physical",
        pp=20,
        power=20,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ほっぺすりすり_apply_ailment_to_defender,
            ),
        }
    ),
    "ホネこんぼう": MoveData(
        type="じめん",
        category="physical",
        pp=10,
        power=100,
        accuracy=85,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ホネこんぼう_apply_flinch,
            )
        }
    ),
    "ほのおのうず": MoveData(
        type="ほのお",
        category="special",
        pp=15,
        power=35,
        accuracy=85,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "ほのおのキバ": MoveData(
        type="ほのお",
        category="physical",
        pp=15,
        power=65,
        accuracy=95,
        flags={"bite", "contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ほのおのキバ_apply_flinch_or_burn,
            )
        }
    ),
    "ほのおのちかい": MoveData(
        type="ほのお",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "ほのおのパンチ": MoveData(
        type="ほのお",
        category="physical",
        pp=15,
        power=75,
        accuracy=100,
        flags={"contact", "punch", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ほのおのパンチ_apply_ailment_to_defender,
            )
        }
    ),
    "ほのおのまい": MoveData(
        type="ほのお",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        flags={"dance", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ほのおのまい_boost_spa_C,
            )
        }
    ),
    "ほのおのムチ": MoveData(
        type="ほのお",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ほのおのムチ_lower_defender_def,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.ほのおのムチ_lower_def)
        }
    ),
    "ほろびのうた": MoveData(
        type="ノーマル",
        category="status",
        pp=5,
        flags={"sound"},
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
    "ぼうぎょしれい": MoveData(
        type="むし",
        category="status",
        pp=10,
        handlers={},  # TODO: 効果実装
    ),
    "ぼうふう": MoveData(
        type="ひこう",
        category="special",
        pp=10,
        power=110,
        accuracy=70,
        flags={"wind", "secondary_effect"},
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
    "ボディプレス": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=80,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "ボルテッカー": MoveData(
        type="でんき",
        category="physical",
        pp=15,
        power=120,
        accuracy=100,
        flags={"contact", "recoil", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ボルテッカー_recoil,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ボルテッカー_apply_ailment_to_defender,
            )
        }
    ),
    "ボルトチェンジ": MoveData(
        type="でんき",
        category="special",
        pp=20,
        power=70,
        accuracy=100,
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.pivot)
        }
    ),
    "ボーンラッシュ": MoveData(
        type="じめん",
        category="physical",
        pp=10,
        power=25,
        accuracy=90,
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "ポイズンアクセル": MoveData(
        type="どく",
        category="physical",
        pp=20,
        power=70,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ポイズンアクセル_apply_ailment_to_defender,
            )
        }
    ),
    "ポイズンテール": MoveData(
        type="どく",
        category="physical",
        pp=25,
        power=50,
        accuracy=100,
        critical_rank=1,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ポイズンテール_apply_ailment_to_defender,
            )
        }
    ),
    "ポルターガイスト": MoveData(
        type="ゴースト",
        category="physical",
        pp=5,
        power=110,
        accuracy=90,
        handlers={},  # TODO: 効果実装
    ),
    "まきつく": MoveData(
        type="ノーマル",
        category="physical",
        pp=20,
        power=15,
        accuracy=90,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "まきびし": MoveData(
        type="じめん",
        category="status",
        pp=20,
        target="foe_side",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.まきびし_set_field,
            ),
        }
    ),
    "マグマストーム": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=100,
        accuracy=75,
        handlers={},  # TODO: 効果実装
    ),
    "マジカルアクセル": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=100,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.マジカルアクセル_apply_confusion_to_defender,
            )
        }
    ),
    "マジカルシャイン": MoveData(
        type="フェアリー",
        category="special",
        pp=12,
        power=80,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "マジカルフレイム": MoveData(
        type="ほのお",
        category="special",
        pp=10,
        power=75,
        accuracy=100,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.マジカルフレイム_lower_spa_C,
            )
        }
    ),
    "マジカルリーフ": MoveData(
        type="くさ",
        category="special",
        pp=20,
        power=60,
        accuracy=None,
        handlers={},  # 追加効果なし
    ),
    "マジックルーム": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.マジックルーム_activate_global_field,
            ),
        }
    ),
    "マッドショット": MoveData(
        type="じめん",
        category="special",
        pp=15,
        power=55,
        accuracy=95,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.マッドショット_reduce_defender_spd,
            )
        }
    ),
    "マッハパンチ": MoveData(
        type="かくとう",
        category="physical",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        flags={"contact", "punch"},
        handlers={},  # 追加効果なし
    ),
    "まとわりつく": MoveData(
        type="むし",
        category="special",
        pp=20,
        power=20,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "まねっこ": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        flags={"non_negoto"},
        handlers={},  # TODO: 効果実装
    ),
    "まほうのこな": MoveData(
        type="エスパー",
        category="status",
        pp=20,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "まもる": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        priority=4,
        target="self",
        flags={"protect"},
        handlers={
            Event.ON_TRY_MOVE_2: h.MoveHandler(
                hs.まもる系_連続使用失敗チェック,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.まもる_apply,
            ),
        }
    ),
    "まるくなる": MoveData(
        type="ノーマル",
        category="status",
        pp=40,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.まるくなる_apply,
            )
        }
    ),
    "まわしげり": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=85,
        accuracy=90,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.まわしげり_apply_flinch,
            )
        }
    ),
    "みかづきのいのり": MoveData(
        type="エスパー",
        category="status",
        pp=5,
        flags={"heal"},
        handlers={},  # TODO: 効果実装
    ),
    "みかづきのまい": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        flags={"dance", "heal"},
        handlers={},  # TODO: 効果実装
    ),
    "みがわり": MoveData(
        type="ノーマル",
        category="status",
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
        category="status",
        pp=5,
        priority=4,
        target="self",
        flags={"protect"},
        handlers={
            Event.ON_TRY_MOVE_2: h.MoveHandler(
                hs.まもる系_連続使用失敗チェック,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.みきり_apply,
            ),
        }
    ),
    "ミサイルばり": MoveData(
        type="むし",
        category="physical",
        pp=20,
        power=25,
        accuracy=95,
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "ミストバースト": MoveData(
        type="フェアリー",
        category="special",
        pp=5,
        power=100,
        accuracy=100,
        flags={"explosion"},
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.ミストバースト_pay_hp,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ミストフィールド": MoveData(
        type="フェアリー",
        category="status",
        pp=10,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ミストフィールド_activate_terrain,
            ),
        }
    ),
    "ミストボール": MoveData(
        type="エスパー",
        category="special",
        pp=5,
        power=95,
        accuracy=100,
        flags={"bullet"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ミストボール_lower_spa_C,
            )
        }
    ),
    "みずあめボム": MoveData(
        type="くさ",
        category="special",
        pp=10,
        power=60,
        accuracy=85,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.みずあめボム_apply_volatile_to_defender,
            )
        }
    ),
    "みずしゅりけん": MoveData(
        type="みず",
        category="special",
        pp=20,
        power=15,
        accuracy=100,
        priority=1,
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "みずでっぽう": MoveData(
        type="みず",
        category="special",
        pp=25,
        power=40,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "みずのちかい": MoveData(
        type="みず",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "みずのはどう": MoveData(
        type="みず",
        category="special",
        pp=20,
        power=60,
        accuracy=100,
        flags={"pulse", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.みずのはどう_apply_confusion_to_defender,
            )
        }
    ),
    "みずびたし": MoveData(
        type="みず",
        category="status",
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
    "みだれづき": MoveData(
        type="ノーマル",
        category="physical",
        pp=20,
        power=15,
        accuracy=85,
        flags={"contact"},
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "みだれひっかき": MoveData(
        type="ノーマル",
        category="physical",
        pp=15,
        power=18,
        accuracy=80,
        flags={"contact"},
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "みちづれ": MoveData(
        type="ゴースト",
        category="status",
        pp=5,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.みちづれ_apply,
            ),
        }
    ),
    "みねうち": MoveData(
        type="ノーマル",
        category="physical",
        pp=40,
        power=40,
        accuracy=100,
        flags={"contact"},
        handlers={},  # TODO: 効果実装
    ),
    "みらいよち": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=120,
        accuracy=100,
        handlers={},  # TODO: 効果実装
    ),
    "ミラーコート": MoveData(
        type="エスパー",
        category="special",
        pp=20,
        power=0,
        accuracy=100,
        priority=-5,
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.ミラーコート_check_can_use,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.ミラーコート_modify_damage,
                subject_spec="attacker:self",
            ),
        },
    ),
    "ミラーショット": MoveData(
        type="はがね",
        category="special",
        pp=10,
        power=65,
        accuracy=85,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ミラーショット_reduce_acc,
            )
        }
    ),
    "ミラータイプ": MoveData(
        type="ノーマル",
        category="status",
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
        category="status",
        pp=5,
        flags={"heal"},
        handlers={},  # TODO: 効果実装
    ),
    "みわくのボイス": MoveData(
        type="フェアリー",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.みわくのボイス_apply_confusion_to_defender,
            )
        }
    ),
    "みをけずる": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        handlers={},  # TODO: 効果実装
    ),
    "むしくい": MoveData(
        type="むし",
        category="physical",
        pp=20,
        power=60,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.むしくい_steal_and_use_berry)
        }
    ),
    "むしのさざめき": MoveData(
        type="むし",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        flags={"sound"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.むしのさざめき_reduce_defender_spd,
            )
        }
    ),
    "むしのていこう": MoveData(
        type="むし",
        category="special",
        pp=20,
        power=50,
        accuracy=100,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.むしのていこう_lower_spa_C,
            )
        }
    ),
    "むねんのつるぎ": MoveData(
        type="ほのお",
        category="physical",
        pp=10,
        power=90,
        accuracy=100,
        flags={"contact", "slash", "heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.むねんのつるぎ_drain, priority=20)
        }
    ),
    "ムーンフォース": MoveData(
        type="フェアリー",
        category="special",
        pp=15,
        power=95,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ムーンフォース_lower_spa_C,
            )
        }
    ),
    "めいそう": MoveData(
        type="エスパー",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.めいそう_modify_attacker_stats,
            ),
        }
    ),
    "メガトンキック": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=120,
        accuracy=75,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "メガトンパンチ": MoveData(
        type="ノーマル",
        category="physical",
        pp=20,
        power=80,
        accuracy=85,
        flags={"contact", "punch"},
        handlers={},  # 追加効果なし
    ),
    "メガドレイン": MoveData(
        type="くさ",
        category="special",
        pp=15,
        power=40,
        accuracy=100,
        flags={"heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.メガドレイン_drain, priority=20)
        }
    ),
    "メガホーン": MoveData(
        type="むし",
        category="physical",
        pp=12,
        power=120,
        accuracy=85,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "めざめるダンス": MoveData(
        type="ノーマル",
        category="special",
        pp=15,
        power=90,
        accuracy=100,
        flags={"dance"},
        handlers={},  # TODO: 効果実装
    ),
    "メタルクロー": MoveData(
        type="はがね",
        category="physical",
        pp=35,
        power=50,
        accuracy=95,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.メタルクロー_boost_attacker_A,
            )
        }
    ),
    "メタルバースト": MoveData(
        type="はがね",
        category="physical",
        pp=10,
        power=0,
        accuracy=100,
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.メタルバースト_check_can_use,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.メタルバースト_modify_damage,
                subject_spec="attacker:self",
            ),
        },
    ),
    "メテオドライブ": MoveData(
        type="はがね",
        category="physical",
        pp=5,
        power=100,
        accuracy=100,
        handlers={},  # TODO: 効果実装
    ),
    "メテオビーム": MoveData(
        type="いわ",
        category="special",
        pp=10,
        power=120,
        accuracy=90,
        handlers={
            Event.ON_MOVE_CHARGE: [
                h.MoveHandler(
                    ha.メテオビーム_boost_spa,
                    priority=50,
                ),
                h.MoveHandler(
                    ha.メテオビーム_charge,
                ),
            ],
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_MOVE: LethalHandler(
                l.メテオビーム_boost_spa,
            )
        }
    ),
    "メロメロ": MoveData(
        type="ノーマル",
        category="status",
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
    "もえあがるいかり": MoveData(
        type="あく",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.もえあがるいかり_apply_flinch,
            )
        }
    ),
    "もえつきる": MoveData(
        type="ほのお",
        category="special",
        pp=8,
        power=130,
        accuracy=100,
        flags={"thaw"},
        handlers={
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.もえつきる_thaw_attacker,
                priority=5,
            ),
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.もえつきる_fail_if_no_fire_type,
                subject_spec="attacker:self",
                priority=10,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.もえつきる_remove_fire_type,
                subject_spec="attacker:self",
                priority=180,
            ),
        }
    ),
    "ものまね": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        flags={"non_encore", "non_negoto"},
        handlers={},  # 実装保留
    ),
    "もりののろい": MoveData(
        type="くさ",
        category="status",
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
    "もろはのずつき": MoveData(
        type="いわ",
        category="physical",
        pp=5,
        power=150,
        accuracy=80,
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.もろはのずつき_recoil,
            )
        }
    ),
    "やきつくす": MoveData(
        type="ほのお",
        category="special",
        pp=15,
        power=60,
        accuracy=100,
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.やきつくす_remove_berry,
                subject_spec="attacker:self",
            )
        }
    ),
    "やけっぱち": MoveData(
        type="ほのお",
        category="physical",
        pp=10,
        power=75,
        accuracy=100,
        flags={"contact"},
        handlers={},  # TODO: 効果実装
    ),
    "やどりぎのタネ": MoveData(
        type="くさ",
        category="status",
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
    "やまあらし": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=60,
        accuracy=100,
        critical_rank=3,
        flags={"contact"},
        handlers={},  # TODO: 効果実装
    ),
    "ゆきげしき": MoveData(
        type="こおり",
        category="status",
        pp=10,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ゆきげしき_activate_weather,
            ),
        }
    ),
    "ゆきなだれ": MoveData(
        type="こおり",
        category="physical",
        pp=10,
        power=60,
        accuracy=100,
        priority=-4,
        flags={"contact"},
        handlers={},  # TODO: 効果実装
    ),
    "ゆびをふる": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
        flags={"non_negoto"},
        handlers={},  # TODO: 効果実装
    ),
    "ゆめくい": MoveData(
        type="エスパー",
        category="special",
        pp=15,
        power=100,
        accuracy=100,
        flags={"heal"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ゆめくい_check_sleep,
            ),
            Event.ON_HIT: h.MoveHandler(ha.ゆめくい_drain, priority=20)
        }
    ),
    "ようかいえき": MoveData(
        type="どく",
        category="special",
        pp=30,
        power=40,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ようかいえき_reduce_defender_spd,
            )
        }
    ),
    "ようせいのかぜ": MoveData(
        type="フェアリー",
        category="special",
        pp=30,
        power=40,
        accuracy=100,
        flags={"wind"},
        handlers={},  # 追加効果なし
    ),
    "らいげき": MoveData(
        type="でんき",
        category="physical",
        pp=5,
        power=130,
        accuracy=85,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.らいげき_apply_ailment_to_defender,
            )
        }
    ),
    "ライジングボルト": MoveData(
        type="でんき",
        category="special",
        pp=20,
        power=70,
        accuracy=100,
        handlers={},  # TODO: 効果実装
    ),
    "らいめいげり": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=90,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.らいめいげり_lower_defender_def,
            )
        }
    ),
    "ラスターカノン": MoveData(
        type="はがね",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ラスターカノン_reduce_defender_spd,
            )
        }
    ),
    "ラスターパージ": MoveData(
        type="エスパー",
        category="special",
        pp=5,
        power=95,
        accuracy=100,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ラスターパージ_reduce_defender_spd,
            )
        }
    ),
    "リサイクル": MoveData(
        type="ノーマル",
        category="status",
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
        category="status",
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
        category="status",
        pp=20,
        handlers={},  # TODO: 効果実装
    ),
    "りゅうせいぐん": MoveData(
        type="ドラゴン",
        category="special",
        pp=5,
        power=130,
        accuracy=90,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.りゅうせいぐん_sharply_lower_spa_C,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.りゅうせいぐん_lower_spa)
        }
    ),
    "りゅうのいぶき": MoveData(
        type="ドラゴン",
        category="special",
        pp=20,
        power=60,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.りゅうのいぶき_apply_ailment_to_defender,
            )
        }
    ),
    "りゅうのはどう": MoveData(
        type="ドラゴン",
        category="special",
        pp=12,
        power=85,
        accuracy=100,
        flags={"pulse"},
        handlers={},  # 追加効果なし
    ),
    "りゅうのまい": MoveData(
        type="ドラゴン",
        category="status",
        pp=20,
        flags={"dance"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.りゅうのまい_modify_attacker_stats,
            ),
        }
    ),
    "りんごさん": MoveData(
        type="くさ",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.りんごさん_reduce_defender_spd,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.りんごさん_lower_spd)
        }
    ),
    "りんしょう": MoveData(
        type="ノーマル",
        category="special",
        pp=15,
        power=60,
        accuracy=100,
        flags={"sound"},
        handlers={},  # 追加効果なし
    ),
    "リーフストーム": MoveData(
        type="くさ",
        category="special",
        pp=5,
        power=130,
        accuracy=90,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.リーフストーム_sharply_lower_spa_C,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.オーバーヒート_lower_attacker_spa)
        }
    ),
    "リーフブレード": MoveData(
        type="くさ",
        category="physical",
        pp=15,
        power=90,
        accuracy=100,
        critical_rank=1,
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "ルミナコリジョン": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ルミナコリジョン_sharply_reduce_defender_spd,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.ルミナコリジョン_lower_spd)
        }
    ),
    "レイジングブル": MoveData(
        type="ノーマル",
        category="physical",
        pp=10,
        power=90,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(
                ha.レイジングブル_modify_move_type,
            ),
            Event.ON_HIT: h.MoveHandler(
                ha.レイジングブル_break_screens,
            ),
        },
    ),
    "れいとうパンチ": MoveData(
        type="こおり",
        category="physical",
        pp=15,
        power=75,
        accuracy=100,
        flags={"contact", "punch", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.れいとうパンチ_apply_ailment_to_defender,
            )
        }
    ),
    "れいとうビーム": MoveData(
        type="こおり",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.れいとうビーム_apply_ailment_to_defender,
            )
        }
    ),
    "れんごく": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=100,
        accuracy=50,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.れんごく_apply_ailment_to_defender,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.れんごく_apply_やけど)
        }
    ),
    "れんぞくぎり": MoveData(
        type="むし",
        category="physical",
        pp=20,
        power=40,
        accuracy=95,
        flags={"contact", "slash"},
        handlers={},  # TODO: 効果実装
    ),
    "ロックオン": MoveData(
        type="ノーマル",
        category="status",
        pp=5,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ロックオン_apply,
            ),
        }
    ),
    "ロックカット": MoveData(
        type="いわ",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ロックカット_modify_attacker_stats,
            )
        }
    ),
    "ロッククライム": MoveData(
        type="ノーマル",
        category="physical",
        pp=20,
        power=90,
        accuracy=85,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ロッククライム_apply_confusion_to_defender,
            )
        }
    ),
    "ロックブラスト": MoveData(
        type="いわ",
        category="physical",
        pp=10,
        power=25,
        accuracy=90,
        flags={"bullet"},
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "ローキック": MoveData(
        type="かくとう",
        category="physical",
        pp=20,
        power=65,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ローキック_reduce_defender_spd,
            )
        }
    ),
    "ワイドガード": MoveData(
        type="いわ",
        category="status",
        pp=10,
        priority=3,
        handlers={},  # TODO: 効果実装
    ),
    "ワイドフォース": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        handlers={},  # TODO: 効果実装
    ),
    "ワイドブレイカー": MoveData(
        type="ドラゴン",
        category="physical",
        pp=15,
        power=60,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ワイドブレイカー_reduce_defender_atk,
            )
        }
    ),
    "ワイルドボルト": MoveData(
        type="でんき",
        category="physical",
        pp=15,
        power=90,
        accuracy=100,
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ワイルドボルト_recoil,
            )
        }
    ),
    "わたほうし": MoveData(
        type="くさ",
        category="status",
        pp=40,
        accuracy=100,
        flags={"powder"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.わたほうし_modify_defender_stats,
            ),
        }
    ),
    "わるだくみ": MoveData(
        type="あく",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.わるだくみ_modify_attacker_stats,
            )
        }
    ),
    "ワンダースチーム": MoveData(
        type="フェアリー",
        category="special",
        pp=10,
        power=90,
        accuracy=95,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ワンダースチーム_apply_confusion_to_defender,
            )
        }
    ),
    "ワンダールーム": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        target="field",
        flags=set(),
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ワンダールーム_activate_global_field,
            ),
        }
    ),
}


common_setup()
