"""技データ定義モジュール（あ行のエントリ）。

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


MOVES_A: dict[MoveName, MoveData] = {
    "アイアンテール": MoveData(
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アイアンテール_lower_defender_def,
            )
        }
    ),
    "アイアンヘッド": MoveData(
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アイアンヘッド_apply_flinch,
            )
        }
    ),
    "アイアンローラー": MoveData(
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
            Event.ON_HIT: h.MoveHandler(
                ha.アイアンローラー_clear_terrain_on_zero_damage,
                subject_spec="attacker:self",
                priority=180,
            ),
        }
    ),
    "アイススピナー": MoveData(
        flags={"contact"},
        handlers={
            # ON_HIT: いのちのたまの反動（priority=160、Event.ON_HIT で実装）より後に
            # 実行し、反動で使用者がひんしになった場合の除外判定を成立させるため
            # priority=180 とする（`.internal/plan/moves/アイススピナー.md` 参照）。
            Event.ON_HIT: h.MoveHandler(
                ha.アイススピナー_clear_terrain_on_zero_damage_hit,
                subject_spec="attacker:self",
                priority=180,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アイススピナー_clear_terrain,
                subject_spec="attacker:self",
                priority=180,
                allow_fainted_subject=False,  # いのちのたまの反動等で自身がひんしになった場合はフィールドを解除しない
            ),
        }
    ),
    "アイスハンマー": MoveData(
        flags={"contact", "punch"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アイスハンマー_lower_attacker_spe,
            )
        }
    ),
    "あおいほのお": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=130,
        accuracy=85,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.あおいほのお_apply_burn_to_defender,
            )
        }
    ),
    "アクアカッター": MoveData(
        flags={"slash"},
        handlers={},  # 追加効果なし
    ),
    "アクアジェット": MoveData(
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "アクアステップ": MoveData(
        flags={"contact", "dance", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アクアステップ_boost_attacker_spe,
            )
        }
    ),
    "アクアテール": MoveData(
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "アクアブレイク": MoveData(
        flags={"contact", "secondary_effect"},
        handlers={
            # みずがため等（priority=20）より先に発動させる必要があるため priority=10
            # を明示（.internal/spec/turn.md ON_DAMAGE priority=10「追加効果（特殊なもの除く）」、
            # .internal/spec/abilities/みずがため.md「アクアブレイク/シェルブレードを受けた場合、
            # 追加効果の後にみずがためが発動する」）
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アクアブレイク_lower_defender_def,
                priority=10,
            )
        }
    ),
    "アクアリング": MoveData(
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
        crit_ratio=1,
        handlers={},  # 追加効果なし
    ),
    "アクセルブレイク": MoveData(
        type="かくとう",
        category="physical",
        pp=8,
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
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "あくのはどう": MoveData(
        flags={"pulse", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.あくのはどう_apply_flinch,
            )
        }
    ),
    "あくび": MoveData(
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
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.アクロバット_double_power_when_no_item,
            ),
        },
    ),
    "あさのひざし": MoveData(
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あさのひざし_heal_self,
            )
        }
    ),
    "アシストパワー": MoveData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.アシストパワー_boost_power_by_rank,
                subject_spec="attacker:self",
            ),
        }
    ),
    "アシッドボム": MoveData(
        flags={"bullet"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.アシッドボム_sharply_lower_defender_spd,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.アシッドボム_reduce_spd)
        }
    ),
    "アストラルビット": MoveData(
        type="ゴースト",
        category="special",
        pp=8,
        power=120,
        accuracy=100,
        flags={"spread"},
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            )
        },
    ),
    "あてみなげ": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=70,
        accuracy=None,
        priority=-1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "あなをほる": MoveData(
        flags={"contact", "non_negoto"},
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                lambda b, c, v: h.charge_into_volatile(b, c, v, "あなをほる"),
            ),
            Event.ON_MODIFY_PP_CONSUMED: h.MoveHandler(
                lambda b, c, v: h.suppress_pp_on_charge_continuation(b, c, v, "あなをほる"),
            ),
        }
    ),
    "あばれる": MoveData(
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
        pp=15,
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
        flags={"spread"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あまいかおり_lower_defender_evasion,
            )
        }
    ),
    "あまえる": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あまえる_lower_defender_atk,
            )
        }
    ),
    "あまごい": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.あまごい_activate_weather,
            ),
        }
    ),
    "あやしいかぜ": MoveData(
        type="ゴースト",
        category="special",
        pp=5,
        power=60,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.あやしいかぜ_boost_all_stats,
            )
        }
    ),
    "あやしいひかり": MoveData(
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
        target="own_side",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.アロマセラピー_cure_team_ailment,
            ),
        },
    ),
    "アロマミスト": MoveData(
        flags={"no_effect_in_singles"},  # 味方専用（target=adjacentAlly、自分には使えない）。シングルでは対象不在
        handlers={},  # 追加効果なし
    ),
    "あわ": MoveData(
        type="みず",
        category="special",
        pp=30,
        power=40,
        accuracy=100,
        flags={"secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.あわ_lower_defender_spe,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "あんこくきょうだ": MoveData(
        type="あく",
        category="physical",
        pp=5,
        power=75,
        accuracy=100,
        crit_ratio=3,
        flags={"contact", "punch"},
        handlers={},  # 追加効果なし
    ),
    "アンコール": MoveData(
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
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アーマーキャノン_lower_attacker_def_spd,
            )
        }
    ),
    "アームハンマー": MoveData(
        flags={"contact", "punch"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.アームハンマー_lower_attacker_spe,
            )
        }
    ),
    "いえき": MoveData(
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
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "いかりのこな": MoveData(
        flags={"non_copycat", "no_effect_in_singles"},  # シングルは対象が元々1体のみでリダイレクト効果が無意味
        handlers={},  # 追加効果なし
    ),
    "いかりのまえば": MoveData(
        flags={"contact", "fixed_damage"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.half_damage,
                subject_spec="attacker:self",
                priority=15,
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
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.いじげんホール_remove_protect,
            )
        }
    ),
    "いじげんラッシュ": MoveData(
        type="あく",
        category="physical",
        pp=5,
        power=100,
        accuracy=None,
        flags={"unprotectable", "bypass_substitute"},
        handlers={
            Event.ON_HIT: [
                h.MoveHandler(ha.いじげんラッシュ_remove_protect),
                h.MoveHandler(ha.いじげんラッシュ_lower_attacker_def),
            ]
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.いじげんラッシュ_lower_attacker_def)
        }
    ),
    "いたみわけ": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いたみわけ_equalize_hp,
            )
        }
    ),
    "いちゃもん": MoveData(
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
        flags={"secondary_effect"},  # 追加効果自体は無いが、ちからずく対象技として扱われる（.internal/spec/abilities/ちからずく.md参照）
        handlers={},  # しれいとう連携のランクアップはダブル専用のため対象外（実装しない）
    ),
    "いてつくしせん": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いてつくしせん_apply_freeze_to_defender,
            ),
        }
    ),
    "いとをはく": MoveData(
        flags={"spread"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いとをはく_lower_defender_spe,
            ),
        }
    ),
    "イナズマドライブ": MoveData(
        type="でんき",
        category="special",
        pp=8,
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
        flags={"sound", "secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いにしえのうた_apply_sleep_to_defender,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "いのちがけ": MoveData(
        flags={"fixed_damage"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.いのちがけ_modify_damage,
                subject_spec="attacker:self",
                priority=15,
            ),
        }
    ),
    "いのちのしずく": MoveData(
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いのちのしずく_heal,
            ),
        }
    ),
    "いばる": MoveData(
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.いばる_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いばる_apply,
            ),
        }
    ),
    "いびき": MoveData(
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.いびき_check_sleep,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いびき_apply_flinch,
            )
        }
    ),
    "いやしのすず": MoveData(
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやしのすず_cure_ailment,
            ),
        }
    ),
    "いやしのねがい": MoveData(
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやしのねがい_apply,
            ),
        }
    ),
    "いやしのはどう": MoveData(
        flags={"heal", "pulse"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.いやしのはどう_heal_defender,
            ),
        }
    ),
    "いやなおと": MoveData(
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
        flags={"secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.いわなだれ_apply_flinch,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "インファイト": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.インファイト_lower_attacker_def_spd,
            )
        }
    ),
    "ウェザーボール": MoveData(
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
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ウェーブタックル_recoil,
            )
        }
    ),
    "うずしお": MoveData(
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "うそなき": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.うそなき_lower_defender_spd,
            )
        }
    ),
    "うたう": MoveData(
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.うたう_apply_sleep,
            ),
        }
    ),
    "うたかたのアリア": MoveData(
        flags={"sound", "secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.うたかたのアリア_cure_defender_burn,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.うたかたのアリア_cure_defender_burn)
        }
    ),
    "うちおとす": MoveData(
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.うちおとす_apply_grounded,
            )
        },
    ),
    "ウッドハンマー": MoveData(
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ウッドハンマー_recoil,
            )
        }
    ),
    "ウッドホーン": MoveData(
        flags={"contact", "heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.ウッドホーン_drain, priority=20)
        }
    ),
    "うっぷんばらし": MoveData(
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
        flags={"unprotectable", "unreflectable"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.うつしえ_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.うつしえ_change_ability,
            ),
        }
    ),
    "うらみ": MoveData(
        flags={"bypass_substitute"},
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
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.うらみつらみ_lower_defender_atk,
            )
        }
    ),
    "エアカッター": MoveData(
        flags={"slash", "wind", "spread"},
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            )
        },
    ),
    "エアスラッシュ": MoveData(
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
        crit_ratio=1,
        flags={"wind"},
        handlers={},  # 追加効果なし
    ),
    "エコーボイス": MoveData(
        type="ノーマル",
        category="special",
        pp=16,
        power=40,
        accuracy=100,
        flags={"sound"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.エコーボイス_apply_chain_power,
                priority=50,
            ),
        }
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
        flags={"bullet", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.エナジーボール_lower_defender_spd,
            )
        }
    ),
    "エレキネット": MoveData(
        flags={"secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.エレキネット_lower_defender_spe,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "エレキフィールド": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.エレキフィールド_activate_terrain,
            ),
        }
    ),
    "エレキボール": MoveData(
        power=1,
        flags={"bullet"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.エレキボール_calc_power,
            ),
        }
    ),
    "エレクトロビーム": MoveData(
        flags={"non_negoto"},
        handlers={
            Event.ON_MOVE_CHARGE: [
                h.MoveHandler(
                    ha.エレクトロビーム_boost_spa,
                    priority=50,
                ),
                h.MoveHandler(
                    ha.エレクトロビーム_weather_skip,
                    priority=90,
                ),
                h.MoveHandler(
                    ha.エレクトロビーム_charge,
                ),
            ],
            Event.ON_MODIFY_PP_CONSUMED: h.MoveHandler(
                lambda b, c, v: h.suppress_pp_on_charge_continuation(b, c, v, "エレクトロビーム"),
            ),
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
                hs.えんまく_lower_defender_accuracy,
            )
        }
    ),
    "おいかぜ": MoveData(
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
        target="self",
        flags={"non_negoto", "non_copycat", "no_effect_in_singles"},  # まねっこでコピー不可
        handlers={},  # 効果のないわざ（戦闘上の効果なし）
    ),
    "おかたづけ": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(hs.おかたづけ_cleanup),
        }
    ),
    "おきみやげ": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おきみやげ_apply,
            ),
        }
    ),
    "おさきにどうぞ": MoveData(
        flags={"no_effect_in_singles"},  # 行動順操作技。シングルは行動者が2体のみで順序が変わらない
        handlers={},  # ダブル専用（本プロジェクトはシングルバトル専用のため対象外）
    ),
    "おしゃべり": MoveData(
        type="ひこう",
        category="special",
        pp=20,
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
        flags={"sound"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おたけび_lower_defender_atk_spa,
            ),
        }
    ),
    "おだてる": MoveData(
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.おだてる_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おだてる_apply,
            ),
        }
    ),
    "おちゃかい": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おちゃかい_force_consume_berries,
            ),
        }
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.おにび_apply_burn,
            ),
        }
    ),
    "おはかまいり": MoveData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.おはかまいり_calc_power,
            ),
        }
    ),
    "オーバードライブ": MoveData(
        type="でんき",
        category="special",
        pp=12,
        power=80,
        accuracy=100,
        flags={"sound", "spread"},
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            )
        },
    ),
    "オーバーヒート": MoveData(
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
        pp=12,
        power=80,
        accuracy=100,
        crit_ratio=1,
        flags={"secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.オーラウイング_boost_attacker_spe,
            )
        }
    ),
    "オーラぐるま": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(
                ha.オーラぐるま_check_move_type,
            ),
            Event.ON_HIT: h.MoveHandler(
                ha.オーラぐるま_boost_attacker_spe,
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
                ha.オーロラビーム_lower_defender_atk,
            )
        }
    ),
    "オーロラベール": MoveData(
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
}
