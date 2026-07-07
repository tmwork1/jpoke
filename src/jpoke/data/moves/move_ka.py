"""技データ定義モジュール（か行のエントリ）。

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


MOVES_KA: dict[MoveName, MoveData] = {
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
        flags={"contact", "non_copycat"},  # まねっこでコピー不可（第四世代以降）
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
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.かえんぐるま_thaw_attacker,
                priority=5,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かえんぐるま_apply_burn_to_defender,
            ),
        }
    ),
    "かえんだん": MoveData(
        type="ほのお",
        category="special",
        pp=5,
        power=100,
        accuracy=100,
        flags={"bullet", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かえんだん_apply_burn_to_defender,
            )
        }
    ),
    "かえんのまもり": MoveData(
        type="ほのお",
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
                hs.かえんのまもり_apply,
            ),
        }
    ),
    "かえんほうしゃ": MoveData(
        type="ほのお",
        category="special",
        pp=16,
        power=90,
        accuracy=100,
        flags={"secondary_effect", "thaw"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かえんほうしゃ_apply_burn_to_defender,
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
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.かえんボール_thaw_attacker,
                priority=5,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かえんボール_apply_burn_to_defender,
            )
        }
    ),
    "かかとおとし": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=120,
        accuracy=90,
        flags={"contact", "recoil", "secondary_effect"},
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
        pp=12,
        power=90,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かげぬい_apply_no_escape,
            )
        },
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
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.かたきうち_calc_power,
            ),
        }
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
        flags={"fixed_damage"},
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.half_damage,
                subject_spec="attacker:self",
                priority=15,
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
        flags={"bullet"},
        handlers={},  # 追加効果なし（シングルバトルでは味方が存在しないため常に相手が対象）
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
                ha.かみなり_apply_paralysis_to_defender,
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
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
                ha.かみなりあらし_accuracy,
                subject_spec="attacker:self"
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.かみなりあらし_apply_paralysis_to_defender,
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
                h.MoveHandler(ha.かみなりのキバ_apply_paralysis_to_defender),
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
                ha.かみなりパンチ_apply_paralysis_to_defender,
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
        type="ノーマル",
        category="physical",
        pp=35,
        power=10,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.からみつく_lower_defender_spd,
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
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                ha.かわらわり_break_screens,
                priority=30,
            ),
        },
    ),
    "がむしゃら": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=0,
        accuracy=100,
        flags={"contact", "fixed_damage"},
        handlers={
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.がむしゃら_can_use,
                subject_spec="attacker:self",
                priority=30,
            ),
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.がむしゃら_modify_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "ガリョウテンセイ": MoveData(
        type="ひこう",
        category="physical",
        pp=8,
        power=120,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ガリョウテンセイ_lower_attacker_stats,
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
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.がんせきアックス_set_stealth_rock,
            ),
        },
    ),
    "がんせきふうじ": MoveData(
        type="いわ",
        category="physical",
        pp=15,
        power=60,
        accuracy=95,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.がんせきふうじ_lower_defender_spd,
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
                ha.きあいだま_lower_defender_spd,
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
            Event.ON_MODIFY_PP_CONSUMED: h.MoveHandler(
                ha.きあいパンチ_suppress_pp_on_fail,
                subject_spec="attacker:self",
            ),
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.きあいパンチ_check_move,
                subject_spec="attacker:self",
                priority=30,
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
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.きょけんとつげき_apply_self_volatile,
            ),
        }
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
        flags={"contact", "non_copycat"},  # まねっこでコピー不可
        handlers={},  # 追加効果なし
    ),
    "キラースピン": MoveData(
        type="どく",
        category="physical",
        pp=16,
        power=30,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.キラースピン_clear_field,
                priority=100,
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.キラースピン_apply_poison_to_defender,
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
        pp=8,
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
        pp=12,
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
        type="むし",
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
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.くちばしキャノン_burn_contact_hitter,
                subject_spec="attacker:self",
                priority=5,
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
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.くらいつく_apply_no_escape,
            )
        },
    ),
    "クラブハンマー": MoveData(
        type="みず",
        category="physical",
        pp=12,
        power=100,
        accuracy=95,
        critical_rank=1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "クリアスモッグ": MoveData(
        type="どく",
        category="special",
        pp=16,
        power=50,
        accuracy=None,
        handlers={
            # docs/spec/turn.md の Event.ON_DAMAGE priority=10「クリアスモッグによるランクリセット」に対応
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.クリアスモッグ_reset_defender_rank,
                priority=10,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.クリアスモッグ_reset_defender_rank)
        }
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
        pp=8,
        power=100,
        accuracy=100,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.クロスサンダー_calc_power,
                subject_spec="attacker:self",
            ),
            Event.ON_HIT: h.MoveHandler(
                ha.クロスサンダー_record_hit,
                subject_spec="attacker:self",
            ),
        },
    ),
    "クロスチョップ": MoveData(
        type="かくとう",
        category="physical",
        pp=8,
        power=100,
        accuracy=80,
        critical_rank=1,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "クロスフレイム": MoveData(
        type="ほのお",
        category="special",
        pp=8,
        power=100,
        accuracy=100,
        flags={"thaw"},
        handlers={
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.クロスフレイム_thaw_attacker,
                priority=5,
            ),
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.クロスフレイム_calc_power,
                subject_spec="attacker:self",
            ),
            Event.ON_HIT: h.MoveHandler(
                ha.クロスフレイム_record_hit,
                subject_spec="attacker:self",
            ),
        },
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
                ha.クロスポイズン_apply_poison_to_defender,
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
                ha.グラスミキサー_lower_acc,
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
            Event.ON_DAMAGE_HIT: [
                h.MoveHandler(ha.こおりのキバ_apply_freeze),
                h.MoveHandler(ha.こおりのキバ_apply_flinch),
            ]
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
            Event.ON_MODIFY_ACCURACY: h.MoveHandler(
                ha.こがらしあらし_accuracy,
                subject_spec="attacker:self"
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.こがらしあらし_lower_defender_spd,
            )
        }
    ),
    "こごえるかぜ": MoveData(
        type="こおり",
        category="special",
        pp=16,
        power=55,
        accuracy=95,
        flags={"wind", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.こごえるかぜ_lower_defender_spd,
            )
        }
    ),
    "こごえるせかい": MoveData(
        type="こおり",
        category="special",
        pp=10,
        power=65,
        accuracy=95,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.こごえるせかい_lower_defender_spd,
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
                ha.こなゆき_apply_freeze_to_defender,
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
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ころがる_apply,
            ),
        }
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
                ha.コールドフレア_apply_burn_to_defender,
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
}
