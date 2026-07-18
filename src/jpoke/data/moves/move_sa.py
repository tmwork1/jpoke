"""技データ定義モジュール（さ行のエントリ）。

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


MOVES_SA: dict[MoveName, MoveData] = {
    "さいきのいのり": MoveData(
        type="ノーマル",
        category="status",
        pp=1,
        target="self",
        flags={"heal"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.さいきのいのり_check,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.さいきのいのり_revive,
            ),
        }
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
        flags={"slash"},
        handlers={},  # 追加効果なし
    ),
    "サイコキネシス": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.サイコキネシス_lower_defender_spd,
            )
        }
    ),
    "サイコショック": MoveData(
        flags={"physical_damage"},
        handlers={},  # 追加効果なし
    ),
    "サイコノイズ": MoveData(
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
        flags={"bite", "contact"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                ha.サイコファング_break_screens,
                priority=30,
            ),
        },
    ),
    "サイコフィールド": MoveData(
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
                ha.サイコブースト_sharply_lower_attacker_spa,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.サイコブースト_lower_spa)
        }
    ),
    "サイドチェンジ": MoveData(
        flags={"no_effect_in_singles"},  # 味方と位置を交代する技（Ally Switch）。シングルでは味方が不在で不発
        handlers={},  # ダブル専用（本プロジェクトはシングルバトル専用のため対象外）
    ),
    "さいはい": MoveData(
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.さいはい_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.さいはい_instruct,
            ),
        }
    ),
    "さいみんじゅつ": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.さいみんじゅつ_apply_ailment_to_defender,
            ),
        }
    ),
    "さきおくり": MoveData(
        flags={"no_effect_in_singles"},  # 行動順操作技。シングルは行動者が2体のみで順序が変わらない
        handlers={},  # ダブル専用（本プロジェクトはシングルバトル専用のため対象外）
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.さむいギャグ_activate_weather_and_pivot,
            ),
        }
    ),
    "さわぐ": MoveData(
        flags={"non_negoto", "sound"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.さわぐ_apply,
            ),
        }
    ),
    "サンダーダイブ": MoveData(
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
        flags={"secondary_effect"},
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
        flags={"contact", "slash", "secondary_effect"},
        handlers={
            # みずがため等（priority=20）より先に発動させる必要があるため priority=10
            # を明示（.internal/spec/turn.md ON_DAMAGE priority=10「追加効果（特殊なもの除く）」、
            # .internal/spec/abilities/みずがため.md「アクアブレイク/シェルブレードを受けた場合、
            # 追加効果の後にみずがためが発動する」）
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シェルブレード_lower_defender_def,
                priority=10,
            )
        }
    ),
    "しおづけ": MoveData(
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
        flags={"spread"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.しおふき_calc_power,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
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
        flags={"secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.しっとのほのお_apply_burn_to_defender,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.しっとのほのお_apply_burn_to_defender)
        }
    ),
    "しっぺがえし": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.しっぺがえし_double_power_when_second,
            ),
        }
    ),
    "しっぽきり": MoveData(
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
        flags={"spread"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.しっぽをふる_lower_defender_def,
            )
        }
    ),
    "しねんのずつき": MoveData(
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.しねんのずつき_apply_flinch,
            )
        }
    ),
    "しびれごな": MoveData(
        flags={"powder"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.しびれごな_apply_ailment_to_defender,
            ),
        }
    ),
    "しめつける": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "シャカシャカほう": MoveData(
        flags={"heal", "secondary_effect", "thaw", "self_thaw", "spread"},
        handlers={
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.シャカシャカほう_thaw_attacker,
                priority=170,
            ),
            Event.ON_HIT: h.MoveHandler(ha.シャカシャカほう_drain, priority=20),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.シャカシャカほう_apply_burn_to_defender,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "シャドークロー": MoveData(
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "シャドーダイブ": MoveData(
        type="ゴースト",
        category="physical",
        pp=5,
        power=120,
        accuracy=100,
        flags={"contact", "unprotectable", "non_negoto"},
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                lambda b, c, v: h.charge_into_volatile(b, c, v, "シャドーダイブ"),
            ),
            Event.ON_MODIFY_PP_CONSUMED: h.MoveHandler(
                lambda b, c, v: h.suppress_pp_on_charge_continuation(b, c, v, "シャドーダイブ"),
            ),
        }
    ),
    "シャドーパンチ": MoveData(
        flags={"contact", "punch"},
        handlers={},  # 追加効果なし
    ),
    "シャドーボール": MoveData(
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
        target="self",
        flags={"dance"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.しょうりのまい_modify_attacker_stats,
            ),
        },
    ),
    "しろいきり": MoveData(
        type="こおり",
        category="status",
        pp=30,
        target="own_side",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.しろいきり_set_side_field,
            ),
        },
    ),
    "しんくうは": MoveData(
        handlers={},  # 追加効果なし
    ),
    "しんそく": MoveData(
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
                ha.しんぴのちから_boost_attacker_spa,
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.しんぴのまもり_set_side_field,
            ),
        }
    ),
    "シンプルビーム": MoveData(
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
        flags={"contact", "punch"},
        handlers={},  # 追加効果なし
    ),
    "じこあんじ": MoveData(
        flags={"unprotectable", "unreflectable", "bypass_substitute"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.じこあんじ_copy_ranks,
            ),
        }
    ),
    "じこさいせい": MoveData(
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
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.じごくづき_apply_volatile_to_defender,
            )
        }
    ),
    "じしん": MoveData(
        flags={"spread"},
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            )
        },
    ),
    "じたばた": MoveData(
        power=1,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.じたばた_calc_power,
            ),
        }
    ),
    "じだんだ": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.じだんだ_calc_power,
                subject_spec="attacker:self",
            ),
        },
    ),
    "じならし": MoveData(
        flags={"secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.じならし_lower_defender_spe,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "じばく": MoveData(
        flags={"explosion", "spread"},
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.じばく_pay_hp,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "じばそうさ": MoveData(
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.じばそうさ_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.じばそうさ_boost_attacker_def_spd,
            ),
        }
    ),
    "ジャイロボール": MoveData(
        power=1,
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
        target="self",
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(hs.ジャングルヒール_apply),
        },
    ),
    "じゅうでん": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.じゅうでん_apply,
            ),
        }
    ),
    "じゅうりょく": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.じゅうりょく_activate_global_field,
            ),
        }
    ),
    "じわれ": MoveData(
        flags={"ohko"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.ohko_damage,
                priority=90,
            ),
        }
    ),
    "じんつうりき": MoveData(
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
        crit_ratio=3,
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
        accuracy=None,  # 必中（命中判定自体が行われない）
        # まもるで防がれ、みがわりを貫通し、マジックコートで跳ね返されない
        flags={"bypass_substitute", "unreflectable"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.スキルスワップ_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.スキルスワップ_swap_ability,
            ),
            # ごりむちゅうの ON_MOVE_END ハンドラ（デフォルト優先度100）より
            # 後に発動させ、自身の効果で入手したごりむちゅうによるロックを解除する。
            Event.ON_MOVE_END: h.MoveHandler(
                hs.ごりむちゅう_release_lock_on_ability_change,
                priority=110,
            ),
        }
    ),
    "スケイルショット": MoveData(
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
        flags={"sound", "spread"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.スケイルノイズ_lower_attacker_def,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "スケッチ": MoveData(
        type="ノーマル",
        category="status",
        pp=1,  # champions/moves.mdに記載なし。Gen9本家基準の値をそのまま採用
               # （ものまね・ゆびをふる等、Championsに記載のない技コピー系の技と同様）。
        # accuracy省略=必中。潜伏中の相手への失敗はHIDDEN_MOVE_ALLOWED_MOVES側で処理される。
        flags={"non_encore", "non_negoto", "non_copycat", "unprotectable", "unreflectable"},
        # 実装保留: 相手が最後に使った技を技スロットへ恒久的に追加する技コピー機構
        # （ものまねの一時差し替えより復元条件が複雑）が必要なため対応を見送る。
        # 詳細は .internal/plan/moves/スケッチ.md 参照（前例: へんしん・ものまね・ゆびをふる）。
        handlers={},
    ),
    "スチームバースト": MoveData(
        type="みず",
        category="special",
        pp=8,
        power=110,
        accuracy=95,
        flags={"secondary_effect", "thaw", "self_thaw"},
        handlers={
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.スチームバースト_thaw_attacker,
                priority=170,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.スチームバースト_apply_burn_to_defender,
            )
        }
    ),
    "すてゼリフ": MoveData(
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.すてゼリフ_modify_defender_stats_and_pivot,
            ),
        }
    ),
    "すてみタックル": MoveData(
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.すてみタックル_recoil,
            )
        }
    ),
    "ステルスロック": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ステルスロック_set_field,
            )
        }
    ),
    "ストーンエッジ": MoveData(
        handlers={},  # 追加効果なし
    ),
    "すなあつめ": MoveData(
        type="じめん",
        category="status",
        pp=8,
        target="self",
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.すなあつめ_heal_self,
            )
        }
    ),
    "すなあらし": MoveData(
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
                hs.すなかけ_lower_defender_accuracy,
            )
        }
    ),
    "すなじごく": MoveData(
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
        flags={"spread"},
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            )
        },
    ),
    "スピードスワップ": MoveData(
        accuracy=None,  # 必中
        # マジックコートで跳ね返されず、みがわりを貫通する
        flags={"unreflectable", "bypass_substitute"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.スピードスワップ_swap_speed,
            ),
        }
    ),
    "スマートホーン": MoveData(
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
        flags={"unreflectable", "non_copycat"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.すりかえ_swap_items,
            ),
            # こだわり系アイテムの ON_MOVE_END ハンドラ（デフォルト優先度100）より
            # 後に発動させ、自身の効果で入手したこだわり系アイテムによるロックを解除する。
            Event.ON_MOVE_END: h.MoveHandler(
                hs.すりかえ_release_choice_lock,
                priority=110,
            ),
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.せいちょう_boost_attacker_atk_spa,
            ),
        }
    ),
    "せいなるつるぎ": MoveData(
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
        flags={"secondary_effect", "thaw", "self_thaw"},
        handlers={
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.せいなるほのお_thaw_attacker,
                priority=170,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.せいなるほのお_apply_burn_to_defender,
            ),
        }
    ),
    "ぜったいれいど": MoveData(
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
        flags={"unreflectable"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                hs.そうでん_try_move,
                priority=30,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.そうでん_apply,
            ),
        }
    ),
    "ソウルクラッシュ": MoveData(
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ソウルクラッシュ_lower_defender_spa,
            )
        }
    ),
    "ソウルビート": MoveData(
        flags={"dance", "sound"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ソウルビート_check,
                priority=100,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ソウルビート_pay_hp_and_boost_all_stats,
            ),
        }
    ),
    "そらをとぶ": MoveData(
        flags={"contact", "gravity_restricted", "non_negoto"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                h.gravity_restricted_fail,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                lambda b, c, v: h.charge_into_volatile(b, c, v, "そらをとぶ"),
            ),
            Event.ON_MODIFY_PP_CONSUMED: h.MoveHandler(
                lambda b, c, v: h.suppress_pp_on_charge_continuation(b, c, v, "そらをとぶ"),
            ),
        }
    ),
    "ソーラービーム": MoveData(
        flags={"non_negoto"},
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
            Event.ON_MODIFY_PP_CONSUMED: h.MoveHandler(
                lambda b, c, v: h.suppress_pp_on_charge_continuation(b, c, v, "ソーラービーム"),
            ),
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ソーラービーム_halve_power,
            ),
        }
    ),
    "ソーラーブレード": MoveData(
        flags={"contact", "slash", "non_negoto"},
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
            Event.ON_MODIFY_PP_CONSUMED: h.MoveHandler(
                lambda b, c, v: h.suppress_pp_on_charge_continuation(b, c, v, "ソーラーブレード"),
            ),
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ソーラービーム_halve_power,
            ),
        }
    ),
}
