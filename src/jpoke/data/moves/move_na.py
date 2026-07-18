"""技データ定義モジュール（な行のエントリ）。

`data/move.py` から分割された、MOVES辞書の一部を定義する。
分割・並び替えは scripts/sort_data/sort_moves.py が行うため、手編集時も
五十音順を維持すること。
"""
from jpoke.enums import Event, LethalEvent
from jpoke.core.lethal import LethalHandler
from jpoke.types import MoveName

from jpoke.handlers import move as h
from jpoke.handlers import move_attack as ha
from jpoke.handlers import move_status as hs
from jpoke.handlers import lethal as l

from ..models import MoveData


MOVES_NA: dict[MoveName, MoveData] = {
    "ないしょばなし": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        accuracy=None,  # 必中
        flags={"sound", "unprotectable"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ないしょばなし_lower_defender_spa,
            )
        }
    ),
    "ナイトバースト": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ナイトバースト_lower_defender_accuracy,
            )
        }
    ),
    "ナイトヘッド": MoveData(
        flags={"fixed_damage"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.level_fixed_damage,
                subject_spec="attacker:self",
                priority=15,
            )
        }
    ),
    "なかまづくり": MoveData(
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
        accuracy=None,  # 必中
        flags={"unprotectable", "bypass_substitute"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.なかよくする_lower_defender_atk,
            )
        }
    ),
    "なきごえ": MoveData(
        type="ノーマル",
        category="status",
        pp=40,
        accuracy=100,
        flags={"sound", "spread"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.なきごえ_lower_defender_atk,
            )
        }
    ),
    "なげつける": MoveData(
        power=1,
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.なげつける_check_item,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_HIT: [
                # .internal/spec/turn.md ON_HIT: 追加効果は明記された優先度がないため、
                # 同一ハンドラであるアイテム消費(priority=100)より前に発動するよう
                # priority=90を明示する（消費前にctx.attacker.item.base_nameを参照するため）。
                h.MoveHandler(
                    ha.なげつける_apply_item_effect,
                    priority=90,
                ),
                # .internal/spec/turn.md ON_HIT: 「100 なげつける使用者のアイテム消費」。
                # いのちのたまの反動(priority=160)より前にアイテムを失わせることで、
                # 一次情報の「いのちのたまを投げた際は反動を受けない」を再現する。
                h.MoveHandler(
                    ha.なげつける_consume_item,
                    priority=100,
                ),
            ],
            # 命中しなかった場合やまもる・特性による無効化などON_HITに到達しない
            # 失敗パターンでも、一次情報の通りどうぐは消費されるため保険としてON_MOVE_ENDでも消費する
            # （なげつける_consume_itemは冪等なため、ON_HITで既に消費済みの場合は何もしない）。
            Event.ON_MOVE_END: h.MoveHandler(
                ha.なげつける_consume_item,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.なげつける_apply_item_effect)
        },
    ),
    "なまける": MoveData(
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.なまける_heal_self,
            ),
        }
    ),
    "なみだめ": MoveData(
        accuracy=None,  # 必中
        flags={"unprotectable"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.なみだめ_lower_defender_atk_spa,
            )
        }
    ),
    "なみのり": MoveData(
        flags={"spread"},
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            )
        },
    ),
    "なやみのタネ": MoveData(
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
        accuracy=None,  # 必中
        flags={"unprotectable", "unreflectable", "bypass_substitute"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.なりきり_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.なりきり_change_ability,
            ),
            # ごりむちゅうの ON_MOVE_END ハンドラ（デフォルト優先度100）より
            # 後に発動させ、自身の効果で入手したごりむちゅうによるロックを解除する。
            Event.ON_MOVE_END: h.MoveHandler(
                hs.ごりむちゅう_release_lock_on_ability_change,
                priority=110,
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
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.にぎりつぶす_calc_power,
            ),
        }
    ),
    "ニトロチャージ": MoveData(
        flags={"contact", "secondary_effect"},
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
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "にほんばれ": MoveData(
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
        flags={"spread"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.にらみつける_lower_defender_def,
            )
        }
    ),
    "ニードルガード": MoveData(
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
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.ねこだまし_check_first_turn,
                subject_spec="attacker:self",
                priority=30,
            ),
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
        flags={"non_encore", "non_negoto"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
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
        flags={"wind", "secondary_effect", "spread"},
        handlers={
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
                ha.ねっさのあらし_accuracy,
                subject_spec="attacker:self"
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねっさのあらし_apply_burn_to_defender,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "ねっさのだいち": MoveData(
        flags={"secondary_effect", "thaw", "self_thaw"},
        handlers={
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.ねっさのだいち_thaw_attacker,
                priority=170,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねっさのだいち_apply_burn_to_defender,
            )
        }
    ),
    "ねっとう": MoveData(
        flags={"secondary_effect", "thaw", "self_thaw"},
        handlers={
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.ねっとう_thaw_attacker,
                priority=170,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねっとう_apply_burn_to_defender,
            )
        }
    ),
    "ねっぷう": MoveData(
        flags={"wind", "secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ねっぷう_apply_burn_to_defender,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "ねばねばネット": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ねばねばネット_set_side_field,
            ),
        }
    ),
    "ねむりごな": MoveData(
        pp=16,  # champions基準（move_list.txt）。Gen9本家は15
        flags={"powder"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ねむりごな_apply_ailment_to_defender,
            ),
        }
    ),
    "ねむる": MoveData(
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
        crit_ratio=1,
        handlers={},  # 追加効果なし
    ),
    "ねをはる": MoveData(
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
        flags={"minimize", "contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.のしかかり_apply_paralysis_to_defender,
            )
        }
    ),
    "のみこむ": MoveData(
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
        # まもる・ダイウォールを無視し、マジックコートで跳ね返されず、みがわりを貫通する
        flags={"unprotectable", "unreflectable", "bypass_substitute"},
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
}
