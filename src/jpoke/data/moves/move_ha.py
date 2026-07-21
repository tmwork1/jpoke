"""技データ定義モジュール（は行のエントリ）。

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


MOVES_HA: dict[MoveName, MoveData] = {
    "はいすいのじん": MoveData(
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                hs.はいすいのじん_can_apply,
                priority=30,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.はいすいのじん_apply,
            ),
        },
    ),
    "ハイドロカノン": MoveData(
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.リチャージ_apply,
            )
        }
    ),
    "ハイドロスチーム": MoveData(
        type="みず",
        category="special",
        pp=16,
        power=80,
        accuracy=100,
        flags={"thaw", "self_thaw"},
        handlers={
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.ハイドロスチーム_thaw_attacker,
                priority=170,
            ),
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ハイドロスチーム_power_modifier,
            ),
        },
    ),
    "ハイドロポンプ": MoveData(
        handlers={},  # 追加効果なし
    ),
    "ハイパードリル": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=100,
        accuracy=100,
        flags={"contact", "unprotectable"},
        handlers={},  # 追加効果なし
    ),
    "ハイパーボイス": MoveData(
        flags={"sound", "spread"},
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            )
        },
    ),
    "はいよるいちげき": MoveData(
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.はいよるいちげき_lower_defender_spa,
            )
        }
    ),
    "はかいこうせん": MoveData(
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.リチャージ_apply,
            )
        }
    ),
    "はがねのつばさ": MoveData(
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.はがねのつばさ_boost_attacker_def,
            )
        }
    ),
    "はきだす": MoveData(
        handlers={
            Event.ON_TRY_MOVE_1: [
                h.MoveHandler(
                    ha.はきだす_check_can_use,
                    priority=30,
                ),
                h.MoveHandler(
                    ha.はきだす_set_power,
                ),
            ],
            Event.ON_END_MOVE: h.MoveHandler(
                ha.はきだす_apply_after,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.はきだす_reset_stockpile)
        }
    ),
    "ハサミギロチン": MoveData(
        flags={"ohko", "contact"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.ohko_damage,
                priority=90,
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
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.はたきおとす_power,
            ),
            # .internal/spec/turn.md ON_DAMAGE: 「100 はたきおとす等のアイテム効果」
            # くっつきバリの転移判定（priority=30）より後に発動する必要があるため ON_DAMAGE_HIT を使用する。
            # TODO: ON_DAMAGE_HIT は modify_hp（ON_HP_CHANGEDによるオボンのみ等の自動発動）より
            # 後に発火するため、相手がHPしきい値回復きのみを持っている場合、はたきおとすで
            # 奪う前にきのみが発動してしまう。.internal/spec/moves/はたきおとす.md「持ち物との発動順序」
            # の「はたきおとすの効果が優先される」規定（きのみは奪われる前に発動しない）に反する。
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.はたきおとす_remove_item,
            )
        }
    ),
    "はたく": MoveData(
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
                ha.はっけい_apply_paralysis_to_defender,
            )
        }
    ),
    "はっぱカッター": MoveData(
        type="くさ",
        category="physical",
        pp=25,
        power=55,
        accuracy=95,
        crit_ratio=1,
        flags={"slash", "spread"},
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            )
        },
    ),
    "ハッピータイム": MoveData(
        type="ノーマル",
        category="status",
        pp=30,
        target="own_side",
        handlers={},  # 効果のないわざ（戦闘上の効果なし）
    ),
    "はどうだん": MoveData(
        accuracy=None,  # 必中
        flags={"bullet", "pulse"},
        handlers={},  # 追加効果なし
    ),
    "はなびらのまい": MoveData(
        flags={"contact", "dance"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.あばれる_apply,
            ),
        }
    ),
    "はなふぶき": MoveData(
        flags={"wind", "spread"},
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            )
        },
    ),
    "はねやすめ": MoveData(
        flags={"heal"},
        handlers={
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
        target="self",
        flags={"gravity_restricted", "no_effect_in_singles"},  # 公式に戦闘上の効果を持たない技
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                h.gravity_restricted_fail,
                subject_spec="attacker:self",
                priority=30,
            ),
        },
    ),
    "ハバネロエキス": MoveData(
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
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                ha.はめつのねがい_charge,
            ),
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.はめつのねがい_fail_check,
                priority=30,
            ),
        },
    ),
    "はめつのひかり": MoveData(
        flags={"recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.はめつのひかり_recoil,
            )
        }
    ),
    "はやてがえし": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.はやてがえし_try_move,
                priority=30,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.はやてがえし_apply_flinch,
            ),
        }
    ),
    "はらだいこ": MoveData(
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
        flags={"wind", "secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.はるのあらし_lower_defender_atk,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "ハロウィン": MoveData(
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ハロウィン_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ハロウィン_apply,
            ),
        }
    ),
    "ハートスワップ": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        accuracy=None,  # 必中
        # マジックコートで跳ね返されず、みがわりを貫通する
        flags={"unreflectable", "bypass_substitute"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ハートスワップ_swap_ranks,
            ),
        }
    ),
    "ハードプラント": MoveData(
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.リチャージ_apply,
            )
        }
    ),
    "ハードプレス": MoveData(
        power=1,
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ハードプレス_calc_power,
            ),
        }
    ),
    "ばかぢから": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ばかぢから_lower_attacker_atk_def,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.ばかぢから_lower_atk_def)
        }
    ),
    "ばくおんぱ": MoveData(
        flags={"sound", "spread"},
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            )
        },
    ),
    "ばくれつパンチ": MoveData(
        flags={"contact", "punch", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ばくれつパンチ_apply_confusion_to_defender,
            )
        }
    ),
    "バトンタッチ": MoveData(
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
                ha.バブルこうせん_lower_defender_spe,
            )
        }
    ),
    "バリアーラッシュ": MoveData(
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.バリアーラッシュ_boost_attacker_def,
            )
        }
    ),
    "バレットパンチ": MoveData(
        flags={"contact", "punch"},
        handlers={},  # 追加効果なし
    ),
    "バークアウト": MoveData(
        flags={"secondary_effect", "sound", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.バークアウト_lower_defender_spa,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
        # リーサル計算は対象外（追加効果は defender の『とくこう』を下げるのみで、
        # バークアウト自身は特殊技のためダメージ計算は defender の『とくぼう』を参照する。
        # defender.boosts["spa"] は calc_damages に一切影響しないため、Gのちから等と異なり
        # lethal_handlers を実装しても後続ヒットのダメージ分布は変化しない。
        # 同様の理由でひやみず・うらみつらみ・がんせきふうじ・だいちのちから等も n/a。
    ),
    "バーンアクセル": MoveData(
        type="ほのお",
        category="physical",
        pp=12,
        power=80,
        accuracy=100,
        flags={"non_copycat", "non_encore", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.バーンアクセル_apply_burn_to_defender,
            )
        }
    ),
    "パラボラチャージ": MoveData(
        flags={"heal", "spread"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.パラボラチャージ_drain, priority=20),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "パワフルエッジ": MoveData(
        type="いわ",
        category="physical",
        pp=5,
        power=95,
        accuracy=100,
        flags={"contact", "unprotectable", "slash"},
        handlers={},  # 追加効果なし
    ),
    "パワーウィップ": MoveData(
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "パワーシェア": MoveData(
        accuracy=None,  # 必中
        # マジックコートで跳ね返されない
        flags={"unreflectable"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.パワーシェア_equalize_stats,
            ),
        }
    ),
    "パワーシフト": MoveData(
        # パワートリックと完全に同一効果（自分のこうげき・ぼうぎょの実数値を入れ替える）のため
        # ハンドラ関数を共有する。
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.パワートリック_swap_stats,
            ),
        }
    ),
    "パワージェム": MoveData(
        handlers={},  # 追加効果なし
    ),
    "パワースワップ": MoveData(
        accuracy=None,  # 必中
        # マジックコートで跳ね返されず、みがわりを貫通する
        flags={"unreflectable", "bypass_substitute"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.パワースワップ_swap_ranks,
            ),
        }
    ),
    "パワートリック": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.パワートリック_swap_stats,
            ),
        }
    ),
    "ひかりのかべ": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ひかりのかべ_set_side_field,
            ),
        }
    ),
    "ひけん・ちえなみ": MoveData(
        flags={"contact", "slash", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ひけんちえなみ_set_spikes,
            ),
        },
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
        accuracy=None,  # 必中
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ひっくりかえす_invert_ranks,
            ),
        },
    ),
    "ひのこ": MoveData(
        type="ほのお",
        category="special",
        pp=25,
        power=40,
        accuracy=100,
        flags={"secondary_effect", "thaw"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ひのこ_apply_burn_to_defender,
            )
        }
    ),
    "ひゃっきやこう": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ひゃっきやこう_double_power_when_ailment,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ひゃっきやこう_apply_burn_to_defender,
            )
        }
    ),
    "ひやみず": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ひやみず_lower_defender_atk,
            )
        }
    ),
    "ひょうざんおろし": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ひょうざんおろし_apply_flinch,
            )
        }
    ),
    "ヒートスタンプ": MoveData(
        power=1,
        flags={"minimize", "contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ヒートスタンプ_calc_power,
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ビルドアップ_boost_attacker_atk_def,
            ),
        }
    ),
    "ファストガード": MoveData(
        pp=16,  # champions基準（.internal/champions/move_list.txt）。Gen9本家は15
        flags={"protect"},
        handlers={
            Event.ON_TRY_MOVE_2: h.MoveHandler(
                hs.まもる系_連続使用失敗チェック,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ファストガード_apply,
            ),
        }
    ),
    "ふいうち": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.ふいうち_try_move,
                priority=30,
            ),
        }
    ),
    "ふういん": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ふういん_apply,
            ),
        }
    ),
    "フェアリーロック": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.フェアリーロック_activate_global_field,
            ),
        }
    ),
    "フェイタルクロー": MoveData(
        flags={"contact", "secondary_effect", "slash"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.フェイタルクロー_apply_ailment_to_defender,
            )
        }
    ),
    "フェイント": MoveData(
        flags={"unprotectable", "non_copycat"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.フェイント_remove_protect,
            )
        }
    ),
    "フェザーダンス": MoveData(
        flags={"dance"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.フェザーダンス_lower_defender_atk,
            )
        }
    ),
    "フォトンゲイザー": MoveData(
        type="エスパー",
        category="special",
        pp=5,
        power=100,
        accuracy=100,
        flags={"ignore_ability"},
        handlers={
            Event.ON_MODIFY_MOVE_CATEGORY: h.MoveHandler(
                ha.フォトンゲイザー_modify_move_category,
            ),
            Event.ON_BEGIN_MOVE: h.MoveHandler(
                ha.フォトンゲイザー_disable_defender_ability,
            ),
            Event.ON_END_MOVE: h.MoveHandler(
                ha.フォトンゲイザー_restore_defender_ability,
            ),
        },
    ),
    "ふきとばし": MoveData(
        flags={"wind", "unprotectable", "bypass_substitute", "non_copycat"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: [
                h.MoveHandler(
                    hs.on_blow_apply,
                    priority=30,
                ),
                h.MoveHandler(
                    hs.on_blow_check_switch_target,
                    priority=100,
                ),
            ],
            Event.ON_STATUS_HIT: h.MoveHandler(hs.blow),
        }
    ),
    "ふくろだたき": MoveData(
        power=1,
        multi_hit={"min": 1, "max": 6,
                   "check_hit_each_time": False, "power_sequence": ()},
        handlers={
            Event.ON_MODIFY_HIT_COUNT: h.MoveHandler(
                ha.ふくろだたき_hit_count,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ふくろだたき_calc_power,
                subject_spec="attacker:self",
            ),
        },
    ),
    "ふしょくガス": MoveData(
        flags={"spread"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ふしょくガス_remove_item,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "ふぶき": MoveData(
        flags={"wind", "secondary_effect", "spread"},
        handlers={
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
                ha.ふぶき_accuracy,
                subject_spec="attacker:self"
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ふぶき_apply_freeze_to_defender,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
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
        flags={"dance", "unreflectable", "spread"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.フラフラダンス_apply,
            ),
        }
    ),
    "フラワーヒール": MoveData(
        type="フェアリー",
        category="status",
        pp=12,
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.フラワーヒール_heal_defender,
            ),
        }
    ),
    "フリーズドライ": MoveData(
        handlers={
            Event.ON_CALC_DEF_TYPE_MODIFIER: h.MoveHandler(
                ha.フリーズドライ_water_effectiveness,
            ),
        }
    ),
    "フリーズボルト": MoveData(
        type="こおり",
        category="physical",
        pp=5,
        power=140,
        accuracy=90,
        flags={"secondary_effect", "non_negoto"},
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                lambda b, c, v: h.charge_into_volatile(b, c, v, "フリーズボルト"),
            ),
            Event.ON_MODIFY_PP_CONSUMED: h.MoveHandler(
                lambda b, c, v: h.suppress_pp_on_charge_continuation(
                    b, c, v, "フリーズボルト"),
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.フリーズボルト_apply_paralysis_to_defender,
            )
        }
    ),
    "ふるいたてる": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ふるいたてる_boost_attacker_atk_spa,
            ),
        }
    ),
    "フルールカノン": MoveData(
        type="フェアリー",
        category="special",
        pp=8,
        power=130,
        accuracy=90,
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.フルールカノン_sharply_lower_attacker_spa,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.フルールカノン_lower_spa)
        }
    ),
    "フレアソング": MoveData(
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.フレアソング_boost_attacker_spa,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.フレアソング_boost_spa)
        }
    ),
    "フレアドライブ": MoveData(
        flags={"contact", "recoil", "secondary_effect", "thaw", "self_thaw"},
        handlers={
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.フレアドライブ_thaw_attacker,
                priority=170,
            ),
            Event.ON_HIT: h.MoveHandler(
                ha.フレアドライブ_recoil,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.フレアドライブ_apply_burn_to_defender,
            ),
        }
    ),
    "ふんえん": MoveData(
        flags={"secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ふんえん_apply_burn_to_defender,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "ふんか": MoveData(
        flags={"spread"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ふんか_calc_power,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "ふんどのこぶし": MoveData(
        flags={"contact", "punch"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ふんどのこぶし_calc_power,
            ),
        }
    ),
    "ぶきみなじゅもん": MoveData(
        # PP減少効果自体に確率判定は無いが、ちからずく対象技として
        # 明記されている技のため secondary_effect フラグを設定する
        # （.internal/spec/abilities/ちからずく.md参照）。
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ぶきみなじゅもん_reduce_defender_pp,
            )
        }
    ),
    "ぶちかまし": MoveData(
        flags={"contact", "punch"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ぶちかまし_lower_attacker_def_spd,
            )
        }
    ),
    "ブラストバーン": MoveData(
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
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.ブラッドムーン_apply_reuse_block,
                subject_spec="attacker:self",
                priority=50,
            ),
        }
    ),
    "ブリザードランス": MoveData(
        type="こおり",
        category="physical",
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
    "ブレイククロー": MoveData(
        flags={"contact", "secondary_effect", "slash"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ブレイククロー_lower_defender_def,
            )
        }
    ),
    "ブレイズキック": MoveData(
        flags={"contact", "secondary_effect", "thaw"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ブレイズキック_apply_burn_to_defender,
            )
        }
    ),
    "ブレイブチャージ": MoveData(
        type="エスパー",
        category="status",
        pp=15,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ブレイブチャージ_apply,
            ),
        },
    ),
    "ブレイブバード": MoveData(
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ブレイブバード_recoil,
            )
        }
    ),
    "ぶんまわす": MoveData(
        flags={"contact", "spread"},
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            )
        },
    ),
    "プリズムレーザー": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=160,
        accuracy=100,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.リチャージ_apply,
            )
        }
    ),
    "プレゼント": MoveData(
        type="ノーマル",
        category="physical",
        pp=15,
        power=0,
        accuracy=90,
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(ha.プレゼント_roll_outcome),
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(ha.プレゼント_check_heal_full),
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(ha.プレゼント_apply_heal),
        },
    ),
    "ヘドロウェーブ": MoveData(
        flags={"secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ヘドロウェーブ_apply_poison_to_defender,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
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
                ha.ヘドロこうげき_apply_poison_to_defender,
            )
        }
    ),
    "ヘドロばくだん": MoveData(
        flags={"bullet", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ヘドロばくだん_apply_poison_to_defender,
            )
        }
    ),
    "へびにらみ": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.へびにらみ_apply_ailment_to_defender,
            ),
        }
    ),
    "ヘビーボンバー": MoveData(
        power=1,
        flags={"minimize", "contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ヘビーボンバー_calc_power,
            ),
        }
    ),
    "へんしん": MoveData(
        pp=12,  # champions基準（.internal/champions/move_list.txt）。旧値10はSV本家基準の移行漏れ。
        # accuracy省略=必中。潜伏中の相手への失敗はHIDDEN_MOVE_ALLOWED_MOVES側で処理される。
        flags={"non_encore", "non_copycat", "unprotectable", "unreflectable"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.へんしん_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.へんしん_apply,
            ),
        },
    ),
    "ベノムショック": MoveData(
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
        # 自分のランクを下げる確定効果はちからずくの対象外（アームハンマー等と同様）。
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ホイールスピン_sharply_lower_attacker_spe,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(
                l.ホイールスピン_sharply_lower_attacker_spe)
        }
    ),
    "ほうでん": MoveData(
        flags={"secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ほうでん_apply_paralysis_to_defender,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "ほうふく": MoveData(
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
        flags={"sound", "unprotectable", "non_copycat"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: [
                h.MoveHandler(
                    hs.on_blow_apply,
                    priority=30,
                ),
                h.MoveHandler(
                    hs.on_blow_check_switch_target,
                    priority=100,
                ),
            ],
            Event.ON_STATUS_HIT: h.MoveHandler(hs.blow),
        }
    ),
    "ほおばる": MoveData(
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
    "ほたるび": MoveData(
        type="むし",
        category="status",
        pp=20,
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ほたるび_boost_attacker_spa,
            )
        }
    ),
    "ほっぺすりすり": MoveData(
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ほっぺすりすり_apply_paralysis_to_defender,
            ),
        }
    ),
    "ほのおのうず": MoveData(
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "ほのおのキバ": MoveData(
        flags={"bite", "contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: [
                h.MoveHandler(ha.ほのおのキバ_apply_burn_to_defender),
                h.MoveHandler(ha.ほのおのキバ_apply_flinch),
            ]
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
        flags={"contact", "punch", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ほのおのパンチ_apply_burn_to_defender,
            )
        }
    ),
    "ほのおのまい": MoveData(
        flags={"dance", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ほのおのまい_boost_attacker_spa,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.ほのおのまい_boost_spa)
        }
    ),
    "ほのおのムチ": MoveData(
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
        # target: ps-champ-jaは"all"（jpoke縮約でfield）だが、実際は「全体の場が対象の技」
        # ではなく「使用者自身や隣り合っていないポケモンも含め、姿を隠しているポケモンには
        # 当たらない・ロックオン/ノーガードが効く」という、相手単体を対象とする技と同じ
        # 命中判定・特性相互作用（ちょすい等のみずタイプ変化技吸収、サイコフィールドの
        # 先制技ブロック等）を持つ（.internal/spec/moves/ほろびのうた.md 技の仕様節）。
        # そのためtarget="foe"のまま維持し、まもる無効はunprotectableフラグ、
        # マジックコート/マジックミラー無効はunreflectableフラグで個別に表現する。
        target="foe",
        flags={"sound", "unprotectable", "unreflectable"},
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
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ぼうぎょしれい_boost_attacker_def_spd,
            ),
        }
    ),
    "ぼうふう": MoveData(
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
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "ボルテッカー": MoveData(
        flags={"contact", "recoil", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ボルテッカー_recoil,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ボルテッカー_apply_paralysis_to_defender,
            )
        }
    ),
    "ボルトチェンジ": MoveData(
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.pivot)
        }
    ),
    "ボーンラッシュ": MoveData(
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
        pp=12,
        power=100,
        accuracy=100,
        flags={"non_copycat", "non_encore", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ポイズンアクセル_apply_poison_to_defender,
            )
        }
    ),
    "ポイズンテール": MoveData(
        type="どく",
        category="physical",
        pp=25,
        power=50,
        accuracy=100,
        crit_ratio=1,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ポイズンテール_apply_poison_to_defender,
            )
        }
    ),
    "ポルターガイスト": MoveData(
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                ha.ポルターガイスト_check_item,
                priority=130,
            ),
        },
    ),
}
