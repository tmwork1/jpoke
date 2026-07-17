"""技データ定義モジュール（ま行のエントリ）。

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


MOVES_MA: dict[MoveName, MoveData] = {
    "まきつく": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "まきびし": MoveData(
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
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "マジカルアクセル": MoveData(
        type="フェアリー",
        category="physical",
        pp=12,
        power=100,
        accuracy=100,
        flags={"non_copycat", "non_encore", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.マジカルアクセル_apply_confusion_to_defender,
            )
        }
    ),
    "マジカルシャイン": MoveData(
        flags={"spread"},
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            )
        },
    ),
    "マジカルフレイム": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.マジカルフレイム_lower_defender_spa,
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
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.マジックルーム_activate_global_field,
            ),
        }
    ),
    "マッドショット": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.マッドショット_lower_defender_spe,
            )
        }
    ),
    "マッハパンチ": MoveData(
        flags={"contact", "punch"},
        handlers={},  # 追加効果なし
    ),
    "まとわりつく": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "まねっこ": MoveData(
        flags={"non_negoto", "non_copycat"},  # まねっこ自身はまねっこでコピー不可
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(hs.まねっこ_can_use, allow_fainted_subject=True),
            Event.ON_STATUS_HIT: h.MoveHandler(hs.まねっこ_execute, allow_fainted_subject=True),
            Event.ON_MODIFY_PP_CONSUMED: h.MoveHandler(hs.まねっこ_suppress_pp, allow_fainted_subject=True),
        },
    ),
    "まほうのこな": MoveData(
        flags={"powder"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.まほうのこな_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.まほうのこな_apply,
            ),
        }
    ),
    "まもる": MoveData(
        flags={"protect", "non_copycat"},  # まねっこでコピー不可
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
        target="self",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.まるくなる_apply,
            )
        }
    ),
    "みかづきのいのり": MoveData(
        type="エスパー",
        category="status",
        pp=5,
        target="self",
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(hs.みかづきのいのり_apply),
        },
    ),
    "みかづきのまい": MoveData(
        type="エスパー",
        category="status",
        pp=10,
        target="self",
        flags={"dance", "heal"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(hs.みかづきのまい_can_apply),
            Event.ON_STATUS_HIT: h.MoveHandler(hs.みかづきのまい_apply),
        },
    ),
    "みがわり": MoveData(
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
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "ミストバースト": MoveData(
        flags={"explosion", "spread"},
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.ミストバースト_pay_hp,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ミストバースト_calc_power,
                subject_spec="attacker:self",
                allow_fainted_subject=True,  # ON_PAY_HPのHP全消費で使用者が先に瀕死になっても威力計算は行う
            ),
        }
    ),
    "ミストフィールド": MoveData(
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
        flags={"bullet", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ミストボール_lower_defender_spa,
            )
        }
    ),
    "みずあめボム": MoveData(
        flags={"bullet", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.みずあめボム_apply_volatile_to_defender,
            )
        }
    ),
    "みずしゅりけん": MoveData(
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
        flags={"pulse", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.みずのはどう_apply_confusion_to_defender,
            )
        }
    ),
    "みずびたし": MoveData(
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
        pp=8,  # champions基準（.internal/champions/move_list.txt）。旧値5はSV本家基準の移行漏れ。
        flags={"non_copycat"},
        handlers={
            # 第七世代以降: みちづれを成功させた直後にもう一度使うと必ず失敗する
            # （.internal/spec/moves/みちづれ.md「第七世代以降」節）。
            # まもる/みきりの連続使用失敗チェックと同じ ON_TRY_MOVE_2・優先度未指定パターン。
            Event.ON_TRY_MOVE_2: h.MoveHandler(
                hs.みちづれ_連続使用失敗チェック,
            ),
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
        handlers={
            # .internal/spec/turn.md Event.ON_MODIFY_DAMAGE: 60番（みねうち・てかげん）。
            # がんじょう/きあいのタスキ/きあいのハチマキ（いずれもpriority=100）より
            # 先に発動させることで、みねうちのHP1残し効果が優先され、
            # これらの特性・持ち物が誤って発動・消費されないようにする。
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.みねうち_modify_damage,
                priority=60,
            ),
        },
    ),
    "みらいよち": MoveData(
        flags={"unprotectable"},
        handlers={
            Event.ON_MOVE_CHARGE: h.MoveHandler(
                ha.みらいよち_charge,
            ),
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.みらいよち_fail_check,
                priority=30,
            ),
        },
    ),
    "ミラーコート": MoveData(
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
                ha.ミラーショット_lower_defender_accuracy,
            )
        }
    ),
    "ミラータイプ": MoveData(
        flags={"unreflectable", "bypass_substitute"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ミラータイプ_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ミラータイプ_apply,
            ),
        }
    ),
    "ミルクのみ": MoveData(
        type="ノーマル",
        category="status",
        pp=8,
        target="self",
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ミルクのみ_self_heal,
            ),
        },
    ),
    "みわくのボイス": MoveData(
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.みわくのボイス_apply_confusion_to_defender,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.みわくのボイス_apply_confusion_to_defender)
        }
    ),
    "みをけずる": MoveData(
        type="ノーマル",
        category="status",
        pp=12,
        target="self",
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.みをけずる_can_apply,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.みをけずる_apply,
            ),
        }
    ),
    "むしくい": MoveData(
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
    "むしのさざめき": MoveData(
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.むしのさざめき_lower_defender_spd,
            )
        }
    ),
    "むしのていこう": MoveData(
        flags={"secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.むしのていこう_lower_defender_spa,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "むねんのつるぎ": MoveData(
        flags={"contact", "slash", "heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.むねんのつるぎ_drain, priority=20)
        }
    ),
    "ムーンフォース": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ムーンフォース_lower_defender_spa,
            )
        }
    ),
    "めいそう": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.めいそう_boost_attacker_spa_spd,
            ),
        }
    ),
    "メガトンキック": MoveData(
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
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(ha.めざめるダンス_modify_type),
        },
    ),
    "メタルクロー": MoveData(
        type="はがね",
        category="physical",
        pp=35,
        power=50,
        accuracy=95,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.メタルクロー_boost_attacker_atk,
            )
        }
    ),
    "メタルバースト": MoveData(
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
        flags={"contact", "ignore_ability"},
        handlers={
            Event.ON_BEGIN_MOVE: h.MoveHandler(
                ha.メテオドライブ_disable_defender_ability,
            ),
            Event.ON_END_MOVE: h.MoveHandler(
                ha.メテオドライブ_restore_defender_ability,
            ),
        },
    ),
    "メテオビーム": MoveData(
        flags={"non_negoto"},
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
            Event.ON_MODIFY_PP_CONSUMED: h.MoveHandler(
                lambda b, c, v: h.suppress_pp_on_charge_continuation(b, c, v, "メテオビーム"),
            ),
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_MOVE: LethalHandler(
                l.メテオビーム_boost_spa,
            )
        }
    ),
    "メロメロ": MoveData(
        flags={"bypass_substitute"},
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
        flags={"secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.もえあがるいかり_apply_flinch,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "もえつきる": MoveData(
        flags={"thaw", "self_thaw"},
        handlers={
            Event.ON_TRY_ACTION: [
                h.MoveHandler(
                    ha.もえつきる_thaw_attacker,
                    priority=170,
                ),
                h.MoveHandler(
                    ha.もえつきる_fail_if_no_fire_type,
                    subject_spec="attacker:self",
                    priority=15,
                ),
            ],
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
        pp=10,  # champions/move_list.txtに記載なし。Gen9本家基準の値をそのまま採用
                # （おしゃべり・テラクラスター・ダイマックスほう等、Championsに記載のない技と同様）。
        flags={"non_encore", "non_negoto", "non_copycat", "unreflectable"},
        # 実装保留: 相手が直前に使用した技を技スロットごと一時的にコピーし、交代/ひんし/
        # バトル終了で元に戻す技コピー機構が必要なため対応を見送る。
        # 詳細は .internal/plan/moves/ものまね.md 参照（前例: へんしん・スケッチ・ゆびをふる）。
        handlers={},
    ),
    "もりののろい": MoveData(
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
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.もろはのずつき_recoil,
            )
        }
    ),
}
