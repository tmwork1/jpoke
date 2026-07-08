"""技データ定義モジュール（ま行のエントリ）。

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


MOVES_MA: dict[MoveName, MoveData] = {
    "まきつく": MoveData(
        type="ノーマル",
        category="physical",
        pp=20,
        power=15,
        accuracy=90,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "まきびし": MoveData(
        type="じめん",
        category="status",
        pp=20,
        target="foe_side",
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
        type="フェアリー",
        category="special",
        pp=12,
        power=80,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "マジカルフレイム": MoveData(
        type="ほのお",
        category="special",
        pp=10,
        power=75,
        accuracy=100,
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.マジカルフレイム_lower_spa_C,
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
        type="エスパー",
        category="status",
        pp=10,
        target="field",
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.マジックルーム_activate_global_field,
            ),
        }
    ),
    "マッドショット": MoveData(
        type="じめん",
        category="special",
        pp=16,
        power=55,
        accuracy=95,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.マッドショット_lower_defender_spd,
            )
        }
    ),
    "マッハパンチ": MoveData(
        type="かくとう",
        category="physical",
        pp=30,
        power=40,
        accuracy=100,
        priority=1,
        flags={"contact", "punch"},
        handlers={},  # 追加効果なし
    ),
    "まとわりつく": MoveData(
        type="むし",
        category="special",
        pp=20,
        power=20,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.apply_bind_to_defender)
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l._apply_bind)
        }
    ),
    "まねっこ": MoveData(
        type="ノーマル",
        category="status",
        pp=20,
        flags={"non_negoto", "non_copycat"},  # まねっこ自身はまねっこでコピー不可
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(hs.まねっこ_can_use),
            Event.ON_STATUS_HIT: h.MoveHandler(hs.まねっこ_execute),
        },
    ),
    "まほうのこな": MoveData(
        type="エスパー",
        category="status",
        pp=20,
        accuracy=100,
        handlers={},  # 追加効果なし
    ),
    "まもる": MoveData(
        type="ノーマル",
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
                hs.まもる_apply,
            ),
        }
    ),
    "まるくなる": MoveData(
        type="ノーマル",
        category="status",
        pp=40,
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
            Event.ON_STATUS_HIT: h.MoveHandler(hs.みかづきのまい_apply),
        },
    ),
    "みがわり": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
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
        type="かくとう",
        category="status",
        pp=5,
        priority=4,
        target="self",
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
        type="むし",
        category="physical",
        pp=20,
        power=25,
        accuracy=95,
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "ミストバースト": MoveData(
        type="フェアリー",
        category="special",
        pp=5,
        power=100,
        accuracy=100,
        flags={"explosion"},
        handlers={
            Event.ON_PAY_HP: h.MoveHandler(
                ha.ミストバースト_pay_hp,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ミストフィールド": MoveData(
        type="フェアリー",
        category="status",
        pp=10,
        target="field",
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
        flags={"bullet"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ミストボール_lower_spa_C,
            )
        }
    ),
    "みずあめボム": MoveData(
        type="くさ",
        category="special",
        pp=10,
        power=60,
        accuracy=90,
        flags={"bullet", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.みずあめボム_apply_volatile_to_defender,
            )
        }
    ),
    "みずしゅりけん": MoveData(
        type="みず",
        category="special",
        pp=20,
        power=15,
        accuracy=100,
        priority=1,
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
        type="みず",
        category="special",
        pp=20,
        power=60,
        accuracy=100,
        flags={"pulse", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.みずのはどう_apply_confusion_to_defender,
            )
        }
    ),
    "みずびたし": MoveData(
        type="みず",
        category="status",
        pp=20,
        accuracy=100,
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
        type="ゴースト",
        category="status",
        pp=5,
        handlers={
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
            # docs/spec/turn.md Event.ON_MODIFY_DAMAGE: 60番（みねうち・てかげん）。
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
        type="エスパー",
        category="special",
        pp=10,
        power=120,
        accuracy=100,
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
        type="エスパー",
        category="special",
        pp=20,
        power=0,
        accuracy=100,
        priority=-5,
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
                ha.ミラーショット_lower_acc,
            )
        }
    ),
    "ミラータイプ": MoveData(
        type="ノーマル",
        category="status",
        pp=15,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ミラータイプ_can_apply,
                priority=130,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ミラータイプ_apply,
            ),
        }
    ),
    "ミルクのみ": MoveData(
        type="ノーマル",
        category="status",
        pp=5,
        flags={"heal"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ミルクのみ_self_heal,
            ),
        },
    ),
    "みわくのボイス": MoveData(
        type="フェアリー",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.みわくのボイス_apply_confusion_to_defender,
            )
        }
    ),
    "みをけずる": MoveData(
        type="ノーマル",
        category="status",
        pp=10,
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
        type="むし",
        category="physical",
        pp=20,
        power=60,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.むしくい_steal_and_use_berry)
        }
    ),
    "むしのさざめき": MoveData(
        type="むし",
        category="special",
        pp=10,
        power=90,
        accuracy=100,
        flags={"sound", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.むしのさざめき_lower_defender_spd,
            )
        }
    ),
    "むしのていこう": MoveData(
        type="むし",
        category="special",
        pp=20,
        power=50,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.むしのていこう_lower_spa_C,
            )
        }
    ),
    "むねんのつるぎ": MoveData(
        type="ほのお",
        category="physical",
        pp=10,
        power=90,
        accuracy=100,
        flags={"contact", "slash", "heal"},
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.むねんのつるぎ_drain, priority=20)
        }
    ),
    "ムーンフォース": MoveData(
        type="フェアリー",
        category="special",
        pp=15,
        power=95,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ムーンフォース_lower_spa_C,
            )
        }
    ),
    "めいそう": MoveData(
        type="エスパー",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.めいそう_modify_attacker_stats,
            ),
        }
    ),
    "メガトンキック": MoveData(
        type="ノーマル",
        category="physical",
        pp=5,
        power=120,
        accuracy=75,
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
        type="むし",
        category="physical",
        pp=12,
        power=120,
        accuracy=85,
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
        flags={"contact"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.メタルクロー_boost_attacker_A,
            )
        }
    ),
    "メタルバースト": MoveData(
        type="はがね",
        category="physical",
        pp=10,
        power=0,
        accuracy=100,
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
        type="いわ",
        category="special",
        pp=10,
        power=120,
        accuracy=90,
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
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_MOVE: LethalHandler(
                l.メテオビーム_boost_spa,
            )
        }
    ),
    "メロメロ": MoveData(
        type="ノーマル",
        category="status",
        pp=15,
        accuracy=100,
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
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.もえあがるいかり_apply_flinch,
            )
        }
    ),
    "もえつきる": MoveData(
        type="ほのお",
        category="special",
        pp=8,
        power=130,
        accuracy=100,
        flags={"thaw"},
        handlers={
            Event.ON_TRY_ACTION: h.MoveHandler(
                ha.もえつきる_thaw_attacker,
                priority=5,
            ),
            Event.ON_TRY_MOVE_1: h.MoveHandler(
                ha.もえつきる_fail_if_no_fire_type,
                subject_spec="attacker:self",
                priority=10,
            ),
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
        pp=10,
        flags={"non_encore", "non_negoto"},
        handlers={},  # 実装保留
    ),
    "もりののろい": MoveData(
        type="くさ",
        category="status",
        pp=20,
        accuracy=100,
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
        type="いわ",
        category="physical",
        pp=5,
        power=150,
        accuracy=80,
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.もろはのずつき_recoil,
            )
        }
    ),
}
