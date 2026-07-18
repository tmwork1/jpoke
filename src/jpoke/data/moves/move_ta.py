"""技データ定義モジュール（た行のエントリ）。

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
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.たきのぼり_apply_flinch,
            )
        }
    ),
    "たくわえる": MoveData(
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
        flags={"wind", "secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.たつまき_apply_flinch,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "たてこもる": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.たてこもる_boost_attacker_def,
            ),
        }
    ),
    "タネばくだん": MoveData(
        flags={"bullet"},
        handlers={},  # 追加効果なし
    ),
    "タネマシンガン": MoveData(
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
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.だいちのちから_lower_defender_spd,
            )
        }
    ),
    "だいちのはどう": MoveData(
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
        flags={"explosion", "spread"},
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.だいばくはつ_pay_hp,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "ダイビング": MoveData(
        flags={"contact", "non_negoto"},
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                lambda b, c, v: h.charge_into_volatile(b, c, v, "ダイビング"),
            ),
            Event.ON_MODIFY_PP_CONSUMED: h.MoveHandler(
                lambda b, c, v: h.suppress_pp_on_charge_continuation(b, c, v, "ダイビング"),
            ),
        }
    ),
    "だいふんげき": MoveData(
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
        flags={"secondary_effect", "spread"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ダイヤストーム_sharply_boost_attacker_def,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "だくりゅう": MoveData(
        flags={"secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.だくりゅう_lower_defender_accuracy,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "ダストシュート": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ダストシュート_apply_poison_to_defender,
            )
        }
    ),
    "ダブルアタック": MoveData(
        pp=12,  # チャンピオンズ基準（.internal/champions/move_list.txt）。第9世代本家基準は10
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
        flags={"spread"},
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            )
        },
    ),
    "ダークホール": MoveData(
        type="あく",
        category="status",
        pp=10,
        accuracy=50,
        flags={"spread"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                hs.ダークホール_check_species,
                priority=30,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ダークホール_apply_sleep,
            ),
        }
    ),
    "ちいさくなる": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ちいさくなる_apply,
            )
        }
    ),
    "ちからをすいとる": MoveData(
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
        flags={"secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.チャージビーム_boost_attacker_spa,
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
        flags={"sound", "spread"},
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            )
        },
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
        flags={"dance"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ちょうのまい_modify_attacker_stats,
            ),
        }
    ),
    "ちょうはつ": MoveData(
        flags={"bypass_substitute"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ちょうはつ_apply,
            ),
        }
    ),
    "ついばむ": MoveData(
        flags={"contact"},
        handlers={
            # HP反映（Event.ON_HP_CHANGED発火）前に奪取するため、被弾側自身のHP閾値
            # きのみ（オボンのみ等）より確実に先行させる必要がある。がんじょう・
            # きあいのタスキ等のHP1残し補正（priority=100）より後の110で実行する
            # （.internal/plan/moves/むしくい.md「Priority根拠」参照）。
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.むしくい_steal_and_use_berry,
                priority=110,
            )
        }
    ),
    "ツインビーム": MoveData(
        multi_hit={
            "min": 2,
            "max": 2,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "つきのひかり": MoveData(
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あさのひざし_heal_self,
            )
        }
    ),
    "つけあがる": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.つけあがる_calc_power,
            ),
        }
    ),
    "つじぎり": MoveData(
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "ツタこんぼう": MoveData(
        type="くさ",
        category="physical",
        pp=10,
        power=100,
        accuracy=100,
        crit_ratio=1,
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
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "つぶらなひとみ": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.つぶらなひとみ_lower_defender_atk,
            ),
        }
    ),
    "つぼをつく": MoveData(
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
                hs.つめとぎ_boost_attacker_atk_accuracy,
            ),
        }
    ),
    "つららおとし": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.つららおとし_apply_flinch,
            )
        }
    ),
    "つららばり": MoveData(
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "つるぎのまい": MoveData(
        flags={"dance"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.つるぎのまい_boost_attacker_atk,
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
        flags={"unprotectable", "unreflectable", "bypass_substitute"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.テクスチャー2_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.テクスチャー2_apply,
            ),
        }
    ),
    "てだすけ": MoveData(
        flags={"no_effect_in_singles"},  # 味方専用（target=adjacentAlly）。シングルでは対象不在
        handlers={},  # ダブル専用（本プロジェクトはシングルバトル専用のため対象外）
    ),
    "てっていこうせん": MoveData(
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.てっていこうせん_pay_hp,
                subject_spec="attacker:self",
            ),
        }
    ),
    "てっぺき": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.てっぺき_boost_attacker_def,
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
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.テラクラスター_reduce_damage,
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
        target="self",
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                hs.テレポート_check,
                priority=30,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.テレポート_apply,
            ),
        },
    ),
    "てんしのキッス": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.てんしのキッス_apply,
            ),
        }
    ),
    "であいがしら": MoveData(
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
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.デカハンマー_apply_reuse_block,
                subject_spec="attacker:self",
                priority=50,
            ),
        }
    ),
    "デコレーション": MoveData(
        flags={"unprotectable", "unreflectable"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.デコレーション_boost_defender_atk_spa,
            ),
        }
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
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.でんこうそうげき_fail_if_no_electric_type,
                subject_spec="attacker:self",
                priority=15,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.でんこうそうげき_remove_electric_type,
                subject_spec="attacker:self",
                priority=180,
            ),
        }
    ),
    "でんじは": MoveData(
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
        flags={"bullet", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.でんじほう_apply_paralysis_to_defender,
            ),
        }
    ),
    "とおせんぼう": MoveData(
        accuracy=None,  # 必中
        flags={"unprotectable"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.とおせんぼう_apply,
            ),
        }
    ),
    "とおぼえ": MoveData(
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.とおぼえ_boost_attacker_atk,
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.とぐろをまく_modify_attacker_stats,
            ),
        }
    ),
    "とける": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.とける_boost_attacker_def,
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
        flags={"contact"},
        handlers={
            # ON_MOVE_KOは相手をひんしにしたときのみ発火するため、ばけのかわの
            # フォルムチェンジ消費ダメージでひんしになった場合も効果が発動する。
            # じしんかじょう等のKOトリガー特性（同じくON_MOVE_KOかつ優先度100）より
            # 先にこの技の効果が発動するよう、優先度を低く設定する。
            Event.ON_MOVE_KO: h.MoveHandler(
                ha.とどめばり_boost_attacker_atk,
                priority=50,
                allow_fainted_subject=True,  # HPコスト技等で自身が瀕死になっても、撃破時(ON_MOVE_KO)の効果は発動する
            )
        }
    ),
    "とびかかる": MoveData(
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
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.とびつく_lower_defender_spe,
            )
        }
    ),
    "とびはねる": MoveData(
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
            Event.ON_MODIFY_PP_CONSUMED: h.MoveHandler(
                lambda b, c, v: h.suppress_pp_on_charge_continuation(b, c, v, "そらをとぶ"),
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.とびはねる_apply_paralysis_to_defender,
            )
        }
    ),
    "とびひざげり": MoveData(
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
        flags={"contact", "non_copycat"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ともえなげ_force_switch,
            )
        }
    ),
    "トライアタック": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.トライアタック_apply_ailment_to_defender,
            )
        }
    ),
    "トラバサミ": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "トリック": MoveData(
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
        crit_ratio=3,
        handlers={},  # 追加効果なし
    ),
    "トリックルーム": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.トリックルーム_activate_global_field,
            ),
        }
    ),
    "トリプルアクセル": MoveData(
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
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.トロピカルキック_lower_defender_atk,
            )
        }
    ),
    "とんぼがえり": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.pivot,
            )
        }
    ),
    "トーチカ": MoveData(
        pp=8,  # champions基準（.internal/champions/move_list.txt）。Gen9本家は10
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
        flags={"spread"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.どくガス_apply_ailment_to_defender,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "どくづき": MoveData(
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どくづき_apply_poison_to_defender,
            )
        }
    ),
    "どくどく": MoveData(
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
        flags={"bite", "contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どくどくのキバ_apply_toxic_to_defender,
            )
        }
    ),
    "どくのいと": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.どくのいと_apply,
            ),
        }
    ),
    "どくのこな": MoveData(
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
        # 直接攻撃技のため"contact"フラグが必要（キングシールド等の接触判定に影響する。
        # fuzzログ seed=2049で発見: 欠落によりキングシールドの反撃デバフが発動しなかった）
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どくばり_apply_poison_to_defender,
            )
        }
    ),
    "どくばりセンボン": MoveData(
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
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "ドラゴンアロー": MoveData(
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
        flags={"spread"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ドラゴンエナジー_calc_power,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "ドラゴンエール": MoveData(
        flags={"sound", "no_effect_in_singles"},  # 味方専用（target=adjacentAlly）。シングルでは対象不在
        handlers={},  # ダブル専用（本プロジェクトはシングルバトル専用のため対象外）
    ),
    "ドラゴンクロー": MoveData(
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "ドラゴンダイブ": MoveData(
        flags={"minimize", "contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ドラゴンダイブ_apply_flinch,
            )
        }
    ),
    "ドラゴンテール": MoveData(
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
                ha.ドラムアタック_lower_defender_spe,
            )
        }
    ),
    "ドリルくちばし": MoveData(
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "ドリルライナー": MoveData(
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "ドレインキッス": MoveData(
        flags={"contact", "heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ドレインキッス_drain,
                priority=20,  # turn.md: ON_HIT priority 20 (HP吸収技による回復)
            )
        }
    ),
    "ドレインパンチ": MoveData(
        flags={"contact", "punch", "heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ドレインパンチ_drain,
                priority=20,  # turn.md: ON_HIT priority 20 (HP吸収技による回復)
            )
        }
    ),
    "どろかけ": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どろかけ_lower_defender_accuracy,
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
                ha.どろばくだん_lower_defender_accuracy,
            )
        }
    ),
    "どろぼう": MoveData(
        pp=20,  # champions基準（.internal/champions/move_list.txt）。旧値25はSV本家基準の移行漏れ。
        flags={"contact", "non_copycat"},
        handlers={
            # .internal/spec/turn.md ON_DAMAGE: 「100 はたきおとす等のアイテム効果」
            # くっつきバリの転移判定（priority=30）より後に発動する必要があるため ON_DAMAGE_HIT を使用する。
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.どろぼう_steal_item,
            )
        }
    ),
    "ドわすれ": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ドわすれ_boost_attacker_spd,
            )
        }
    ),
}
