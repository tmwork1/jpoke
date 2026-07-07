"""技データ定義モジュール（さ行のエントリ）。

`data/move.py` から分割された、MOVES辞書の一部を定義する。
分割・並び替えは scripts/sort_data/sort_moves.py が行うため、手編集時も
五十音順を維持すること。
"""
from jpoke.enums import Event, LethalEvent
from jpoke.core import LethalHandler
from jpoke.types import MoveName

from jpoke.handlers import move as h
from jpoke.handlers import move_attack as ha
from jpoke.handlers import move_status as hs
from jpoke.handlers import lethal as l

from ..models import MoveData


MOVES_SA: dict[MoveName, MoveData] = {
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
        pp=12,
        power=90,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.サイコキネシス_lower_defender_spd,
            )
        }
    ),
    "サイコショック": MoveData(
        type="エスパー",
        category="special",
        pp=12,
        power=80,
        accuracy=100,
        flags={"physical_damage"},
        handlers={},  # 追加効果なし
    ),
    "サイコノイズ": MoveData(
        type="エスパー",
        category="special",
        pp=12,
        power=75,
        accuracy=100,
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.サイコノイズ_apply_volatile_to_defender,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.サイコノイズ_apply_volatile)
        }
    ),
    "サイコファング": MoveData(
        type="エスパー",
        category="physical",
        pp=12,
        power=85,
        accuracy=100,
        flags={"bite", "contact"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                ha.サイコファング_break_screens,
                priority=30,
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
        flags={"physical_damage"},
        handlers={},  # 追加効果なし
    ),
    "サイコブレイド": MoveData(
        type="エスパー",
        category="physical",
        pp=16,
        power=80,
        accuracy=100,
        flags={"contact", "slash"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.サイコブレイド_calc_power,
                subject_spec="attacker:self",
            ),
        },
    ),
    "サイコブースト": MoveData(
        type="エスパー",
        category="special",
        pp=8,
        power=140,
        accuracy=90,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.サイコブースト_sharply_lower_spa_C,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.サイコブースト_lower_spa)
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
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(
                ha.さばきのつぶて_modify_move_type,
            ),
        },
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
        pp=16,
        power=100,
        accuracy=95,
        flags={"minimize", "contact", "recoil"},
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
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "シェルアームズ": MoveData(
        type="どく",
        category="special",
        pp=12,
        power=90,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_MODIFY_MOVE_CATEGORY: h.MoveHandler(
                ha.シェルアームズ_modify_move_category,
            ),
            Event.ON_CHECK_CONTACT: h.MoveHandler(
                ha.シェルアームズ_check_contact,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シェルアームズ_apply_poison_to_defender,
            )
        }
    ),
    "シェルブレード": MoveData(
        type="みず",
        category="physical",
        pp=12,
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
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.しおみず_double_power_if_defender_hp_half_or_less,
            ),
        }
    ),
    "シザークロス": MoveData(
        type="むし",
        category="physical",
        pp=16,
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
                ha.したでなめる_apply_paralysis_to_defender,
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
                ha.しっとのほのお_apply_burn_to_defender,
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
        pp=16,
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
        pp=16,
        power=80,
        accuracy=90,
        flags={"heal", "secondary_effect", "thaw"},
        handlers={
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.シャカシャカほう_thaw_attacker,
                priority=5,
            ),
            Event.ON_HIT: h.MoveHandler(ha.シャカシャカほう_drain, priority=20),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シャカシャカほう_apply_burn_to_defender,
            )
        }
    ),
    "シャドークロー": MoveData(
        type="ゴースト",
        category="physical",
        pp=16,
        power=70,
        accuracy=100,
        critical_rank=1,
        flags={"contact", "slash"},
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
        pp=16,
        power=80,
        accuracy=100,
        flags={"bullet", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シャドーボール_lower_defender_spd,
            )
        }
    ),
    "シャドーレイ": MoveData(
        type="ゴースト",
        category="special",
        pp=5,
        power=100,
        accuracy=100,
        flags={"ignore_ability"},
        handlers={
            Event.ON_BEGIN_MOVE: h.MoveHandler(
                ha.シャドーレイ_disable_defender_ability,
            ),
            Event.ON_END_MOVE: h.MoveHandler(
                ha.シャドーレイ_restore_defender_ability,
            ),
        },
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
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.しんぴのちから_boost_spa)
        }
    ),
    "しんぴのつるぎ": MoveData(
        type="かくとう",
        category="special",
        pp=10,
        power=85,
        accuracy=100,
        flags={"slash", "physical_damage"},
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
                ha.シードフレア_sharply_lower_defender_spd,
            )
        }
    ),
    "ジェットパンチ": MoveData(
        type="みず",
        category="physical",
        pp=16,
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
        pp=20,
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
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
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
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.じだんだ_calc_power,
                subject_spec="attacker:self",
            ),
        },
    ),
    "じならし": MoveData(
        type="じめん",
        category="physical",
        pp=20,
        power=60,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.じならし_lower_defender_spd,
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
        pp=8,
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
        category="special",
        pp=5,
        power=100,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.じゃどくのくさり_apply_toxic_to_defender,
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
                ha.じゃれつく_lower_defender_atk,
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
        power=0,
        accuracy=30,
        flags={"ohko"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.ohko_damage,
                priority=90,
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
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.じんらい_try_move,
                priority=30,
            ),
        }
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
        pp=12,
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
        pp=8,
        power=110,
        accuracy=100,
        flags={"sound"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.スケイルノイズ_lower_attacker_def,
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
        pp=8,
        power=110,
        accuracy=95,
        flags={"secondary_effect", "thaw"},
        handlers={
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.スチームバースト_thaw_attacker,
                priority=5,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.スチームバースト_apply_burn_to_defender,
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
        pp=8,
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
                ha.スパーク_apply_paralysis_to_defender,
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
        pp=12,
        power=70,
        accuracy=None,  # 必中
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
                ha.スモッグ_apply_poison_to_defender,
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
        flags={"protect"},
        handlers={
            Event.ON_TRY_MOVE_2: h.MoveHandler(
                hs.まもる系_連続使用失敗チェック,
            ),
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
            Event.ON_GET_STAT_RANK: h.MoveHandler(
                ha.せいなるつるぎ_ignore_evasion,
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
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.せいなるほのお_thaw_attacker,
                priority=5,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.せいなるほのお_apply_burn_to_defender,
            ),
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
            Event.ON_TRY_MOVE_2: h.MoveHandler(
                ha.ぜったいれいど_check_ice_immunity,
                priority=120,
            ),
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
                ha.ぜったいれいど_modify_accuracy,
            ),
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.ohko_damage,
                priority=90,
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
        pp=12,
        power=120,
        accuracy=100,
        handlers={
            Event.ON_MOVE_CHARGE: [
                h.MoveHandler(
                    ha.ソーラービーム_weather_skip,
                    priority=90,
                ),
                h.MoveHandler(
                    ha.ソーラービーム_charge,
                ),
            ],
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
            Event.ON_MOVE_CHARGE: [
                h.MoveHandler(
                    ha.ソーラーブレード_weather_skip,
                    priority=90,
                ),
                h.MoveHandler(
                    ha.ソーラーブレード_charge,
                ),
            ],
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ソーラービーム_halve_power,
            ),
        }
    ),
}
