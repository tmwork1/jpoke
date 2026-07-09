"""技データ定義モジュール（た行のエントリ）。

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


MOVES_TA: dict[MoveName, MoveData] = {
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
        accuracy=None,
        flags={"slash"},
        multi_hit={
            "min": 2,
            "max": 2,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
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
        target="self",
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
        pp=12,
        target="self",
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
        pp=20,
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
        pp=8,
        target="self",
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.タマゴうみ_heal_self,
            )
        }
    ),
    "タールショット": MoveData(
        type="いわ",
        category="status",
        pp=20,
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
                ha.だいちのちから_lower_defender_spd,
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
        pp=12,
        power=80,
        accuracy=100,
        flags={"contact", "non_negoto"},
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                lambda b, c, v: h.charge_into_volatile(b, c, v, "ダイビング"),
            ),
        }
    ),
    "だいふんげき": MoveData(
        type="ほのお",
        category="physical",
        pp=10,
        power=120,
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
        flags={"non_copycat", "non_encore", "non_negoto"},
        handlers={},  # 追加効果なし
    ),
    "だいもんじ": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=110,
        accuracy=85,
        flags={"secondary_effect", "thaw"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.だいもんじ_apply_burn_to_defender,
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
                ha.だくりゅう_lower_acc,
            )
        }
    ),
    "ダストシュート": MoveData(
        type="どく",
        category="physical",
        pp=8,
        power=120,
        accuracy=80,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ダストシュート_apply_poison_to_defender,
            )
        }
    ),
    "ダブルアタック": MoveData(
        type="ノーマル",
        category="physical",
        pp=12,  # チャンピオンズ基準（docs/champions/move_list.txt）。第9世代本家基準は10
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
        pp=12,
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
    "ダメおし": MoveData(
        type="あく",
        category="physical",
        pp=12,
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
        pp=12,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ちいさくなる_apply,
            )
        }
    ),
    "ちからをすいとる": MoveData(
        type="くさ",
        category="status",
        pp=12,
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
        flags={"contact", "fixed_damage"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.level_fixed_damage,
                subject_spec="attacker:self",
                priority=15,
            )
        }
    ),
    "チャージビーム": MoveData(
        type="でんき",
        category="special",
        pp=12,
        power=50,
        accuracy=90,
        flags={"secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.チャージビーム_boost_spa_C,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.チャージビーム_boost_spa)
        }
    ),
    "チャームボイス": MoveData(
        type="フェアリー",
        category="special",
        pp=16,
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ちょうおんぱ_apply,
            ),
        }
    ),
    "ちょうのまい": MoveData(
        type="むし",
        category="status",
        pp=20,
        target="self",
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
        flags={"bypass_substitute"},
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
        pp=12,
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
        pp=8,
        target="self",
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
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(
                ha.ツタこんぼう_modify_move_type,
            ),
        },
    ),
    "つっぱり": MoveData(
        type="かくとう",
        category="physical",
        pp=20,
        power=15,
        accuracy=100,
        flags={"contact"},
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
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
                priority=90,
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
        pp=20,
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
        pp=20,
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
        pp=16,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.つめとぎ_modify_attacker_stats,
            ),
        }
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
        pp=20,
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
        target="self",
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.テクスチャー_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.テクスチャー_apply,
            ),
        }
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
        priority=5,
        handlers={},  # ダブル専用（本プロジェクトはシングルバトル専用のため対象外）
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
        pp=16,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.てっぺき_modify_attacker_stats,
            )
        }
    ),
    "テラクラスター": MoveData(
        type="ノーマル",
        category="special",
        pp=8,
        power=120,
        accuracy=100,
        flags={"non_copycat"},  # まねっこ/ものまね/スケッチでコピー不可（ものまね/スケッチは未実装）
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(
                ha.テラクラスター_modify_move_type,
            ),
            Event.ON_MODIFY_MOVE_CATEGORY: h.MoveHandler(
                ha.テラクラスター_modify_move_category,
            ),
        },
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
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.テラバースト_lower_attacker_atk_spa)
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
        pp=12,
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
        power=100,
        accuracy=100,
        priority=2,
        flags={"contact"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.であいがしら_check_first_turn,
                subject_spec="attacker:self",
                priority=30,
            ),
        },
    ),
    "デカハンマー": MoveData(
        type="はがね",
        category="physical",
        pp=8,
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
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        flags={"heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.デスウイング_drain,
                priority=20,  # turn.md: ON_HIT priority 20 (HP吸収技による回復)
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
                ha.でんきショック_apply_paralysis_to_defender,
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
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.でんこうそうげき_fail_if_no_electric_type,
                subject_spec="attacker:self",
                priority=10,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.でんこうそうげき_remove_electric_type,
                subject_spec="attacker:self",
                priority=180,
            ),
        }
    ),
    "でんじは": MoveData(
        type="でんき",
        category="status",
        pp=20,
        accuracy=90,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.でんじは_can_apply,
                priority=130,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.でんじは_apply_ailment_to_defender,
            ),
        }
    ),
    "でんじふゆう": MoveData(
        type="でんき",
        category="status",
        pp=12,
        target="self",
        flags={"gravity_restricted"},
        handlers={
            Event.ON_TRY_MOVE_1: [
                h.MoveHandler(
                    h.gravity_restricted_fail,
                    subject_spec="attacker:self",
                    priority=30,
                ),
                h.MoveHandler(
                    hs.でんじふゆう_check_can_use,
                    subject_spec="attacker:self",
                    priority=30,
                ),
            ],
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
                ha.でんじほう_apply_paralysis_to_defender,
            ),
        }
    ),
    "とおせんぼう": MoveData(
        type="ノーマル",
        category="status",
        pp=8,
        accuracy=None,  # 必中
        flags={"unprotectable"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.とおせんぼう_apply,
            ),
        }
    ),
    "とおぼえ": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        target="self",
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
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.リチャージ_apply,
            )
        }
    ),
    "とぐろをまく": MoveData(
        type="どく",
        category="status",
        pp=20,
        target="self",
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
        target="self",
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
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.とっておき_check_used_all_moves,
                subject_spec="attacker:self",
                priority=30,
            ),
        },
    ),
    "とどめばり": MoveData(
        type="むし",
        category="physical",
        pp=25,
        power=50,
        accuracy=100,
        flags={"contact"},
        handlers={
            # ON_MOVE_KOは相手をひんしにしたときのみ発火するため、ばけのかわの
            # フォルムチェンジ消費ダメージでひんしになった場合も効果が発動する。
            # じしんかじょう等のKOトリガー特性（同じくON_MOVE_KOかつ優先度100）より
            # 先にこの技の効果が発動するよう、優先度を低く設定する。
            Event.ON_MOVE_KO: h.MoveHandler(
                ha.とどめばり_boost_attacker_atk,
                priority=50,
            )
        }
    ),
    "とびかかる": MoveData(
        type="むし",
        category="physical",
        pp=15,
        power=80,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.とびかかる_lower_defender_atk,
            )
        }
    ),
    "とびげり": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=100,
        accuracy=95,
        flags={"contact", "gravity_restricted", "recoil"},
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
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.とびつく_lower_defender_spd,
            )
        }
    ),
    "とびはねる": MoveData(
        type="ひこう",
        category="physical",
        pp=8,
        power=85,
        accuracy=85,
        flags={"contact", "gravity_restricted", "secondary_effect", "non_negoto"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                h.gravity_restricted_fail,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                lambda b, c, v: h.charge_into_volatile(b, c, v, "そらをとぶ"),
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.とびはねる_apply_paralysis_to_defender,
            )
        }
    ),
    "とびひざげり": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=130,
        accuracy=90,
        flags={"contact", "gravity_restricted", "recoil"},
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
        pp=12,
        power=60,
        accuracy=90,
        priority=-6,
        flags={"contact", "non_copycat"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ともえなげ_force_switch,
            )
        }
    ),
    "トライアタック": MoveData(
        type="ノーマル",
        category="special",
        pp=12,
        power=80,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.トライアタック_apply_ailment_to_defender,
            )
        }
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
        pp=12,
        accuracy=100,
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
    "トリックフラワー": MoveData(
        type="くさ",
        category="physical",
        pp=12,
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
        pp=12,
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
        pp=12,
        power=10,
        accuracy=90,
        flags={"contact", "check_hit_each_time"},
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
        pp=16,
        power=85,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.トロピカルキック_lower_defender_atk,
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
        flags={"protect"},
        handlers={
            Event.ON_TRY_MOVE_2: h.MoveHandler(
                hs.まもる系_連続使用失敗チェック,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.トーチカ_apply,
            ),
        }
    ),
    "どくガス": MoveData(
        type="どく",
        category="status",
        pp=20,  # championsのPP圧縮則により導出（move_list.txtに単独項目なし）。Gen9本家は40
        accuracy=90,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.どくガス_apply_ailment_to_defender,
            ),
        }
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
                ha.どくづき_apply_poison_to_defender,
            )
        }
    ),
    "どくどく": MoveData(
        type="どく",
        category="status",
        pp=12,
        accuracy=90,
        handlers={
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
                hs.どくどく_accuracy,
                subject_spec="attacker:self",
            ),
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
                ha.どくどくのキバ_apply_toxic_to_defender,
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
        pp=20,
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
                ha.どくばり_apply_poison_to_defender,
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
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.どくばりセンボン_double_power_when_poisoned,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どくばりセンボン_apply_poison_to_defender,
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
        pp=12,
        power=85,
        accuracy=None,
        critical_rank=1,
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "ドラゴンアロー": MoveData(
        type="ドラゴン",
        category="physical",
        pp=12,
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
        pp=8,
        power=150,
        accuracy=100,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ドラゴンエナジー_calc_power,
            ),
        }
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
        critical_rank=1,
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "ドラゴンダイブ": MoveData(
        type="ドラゴン",
        category="physical",
        pp=12,
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
        pp=12,
        power=60,
        accuracy=90,
        priority=-6,
        flags={"contact", "non_copycat"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ドラゴンテール_force_switch,
            )
        }
    ),
    "ドラゴンハンマー": MoveData(
        type="ドラゴン",
        category="physical",
        pp=16,
        power=90,
        accuracy=100,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "ドラムアタック": MoveData(
        type="くさ",
        category="physical",
        pp=12,
        power=80,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ドラムアタック_lower_defender_spd,
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
        pp=12,
        power=80,
        accuracy=95,
        critical_rank=1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "ドレインキッス": MoveData(
        type="フェアリー",
        category="special",
        pp=12,
        power=50,
        accuracy=100,
        flags={"contact", "heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ドレインキッス_drain,
                priority=20,  # turn.md: ON_HIT priority 20 (HP吸収技による回復)
            )
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
        pp=12,
        power=20,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どろかけ_lower_acc,
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
                ha.どろばくだん_lower_acc,
            )
        }
    ),
    "どろぼう": MoveData(
        type="あく",
        category="physical",
        pp=20,  # champions基準（docs/champions/move_list.txt）。旧値25はSV本家基準の移行漏れ。
        power=60,
        accuracy=100,
        flags={"contact", "non_copycat"},
        handlers={
            # docs/spec/turn.md ON_DAMAGE: 「100 はたきおとす等のアイテム効果」
            # くっつきバリの転移判定（priority=30）より後に発動する必要があるため ON_DAMAGE_HIT を使用する。
            Event.ON_DAMAGE_HIT: h.MoveHandler(
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
}
