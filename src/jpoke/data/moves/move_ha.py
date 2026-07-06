"""技データ定義モジュール（は行のエントリ）。

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


MOVES_HA: dict[MoveName, MoveData] = {
    "はいすいのじん": MoveData(
        type="かくとう",
        category="status",
        pp=5,
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
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ハイドロスチーム_power_modifier,
            ),
        },
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
        flags={"contact", "unprotectable"},
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
                ha.はがねのつばさ_boost_attacker_B,
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
            # docs/spec/turn.md ON_DAMAGE: 「100 はたきおとす等のアイテム効果」
            # くっつきバリの転移判定（priority=30）より後に発動する必要があるため ON_DAMAGE_HIT を使用する。
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.はたきおとす_remove_item,
            )
        }
    ),
    "はたく": MoveData(
        type="ノーマル",
        category="physical",
        pp=35,
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
                ha.はるのあらし_lower_defender_atk,
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ハートスワップ_swap_ranks,
            ),
        }
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
                ha.ばかぢから_lower_attacker_def,
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
                ha.バブルこうせん_lower_defender_spd,
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
        flags={"contact", "non_copycat", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.バーンアクセル_apply_burn_to_defender,
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
        flags={"contact", "unprotectable", "slash"},
        handlers={},  # 追加効果なし
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
        pp=16,
        power=65,
        accuracy=90,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ひけん・ちえなみ_set_spikes,
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
        type="あく",
        category="status",
        pp=20,
        accuracy=100,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ひっくりかえす_invert_ranks,
            ),
        },
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
                ha.ひのこ_apply_burn_to_defender,
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
                ha.ひゃっきやこう_apply_burn_to_defender,
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
                ha.ひやみず_lower_defender_atk,
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
        target="self",
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
        pp=12,
        power=1,
        accuracy=100,
        multi_hit={"min": 1, "max": 6, "check_hit_each_time": False, "power_sequence": ()},
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
                ha.ふぶき_apply_freeze_to_defender,
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.フラワーヒール_heal_defender,
            ),
        }
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
                ha.フリーズドライ_apply_freeze_to_defender,
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
                ha.フリーズボルト_apply_paralysis_to_defender,
            )
        }
    ),
    "ふるいたてる": MoveData(
        type="ノーマル",
        category="status",
        pp=30,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ふるいたてる_modify_attacker_stats,
            ),
        }
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
                ha.フレアドライブ_apply_burn_to_defender,
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
                ha.ふんえん_apply_burn_to_defender,
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
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ふんどのこぶし_calc_power,
            ),
        }
    ),
    "ぶきみなじゅもん": MoveData(
        type="エスパー",
        category="special",
        pp=8,
        power=80,
        accuracy=100,
        flags={"sound"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ぶきみなじゅもん_reduce_defender_pp,
            )
        }
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
                ha.ぶちかまし_lower_defender_spd,
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
        type="どく",
        category="special",
        pp=10,
        power=95,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ヘドロウェーブ_apply_poison_to_defender,
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
                ha.ヘドロこうげき_apply_poison_to_defender,
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
                ha.ヘドロばくだん_apply_poison_to_defender,
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
                ha.ホイールスピン_sharply_lower_attacker_spe,
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
                ha.ほうでん_apply_paralysis_to_defender,
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
            # docs/spec/turn.md ON_DAMAGE: 「100 はたきおとす等のアイテム効果」
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
                ha.ほっぺすりすり_apply_paralysis_to_defender,
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
                ha.ほのおのパンチ_apply_burn_to_defender,
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ぼうぎょしれい_modify_attacker_stats,
            ),
        }
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
                ha.ボルテッカー_apply_paralysis_to_defender,
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
        flags={"contact", "non_copycat", "secondary_effect"},
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
        critical_rank=1,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ポイズンテール_apply_poison_to_defender,
            )
        }
    ),
    "ポルターガイスト": MoveData(
        type="ゴースト",
        category="physical",
        pp=5,
        power=110,
        accuracy=90,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                ha.ポルターガイスト_check_item,
                priority=130,
            ),
        },
    ),
}
