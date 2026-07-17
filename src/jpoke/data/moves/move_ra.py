"""技データ定義モジュール（ら行のエントリ）。

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


MOVES_RA: dict[MoveName, MoveData] = {
    "らいげき": MoveData(
        type="でんき",
        category="physical",
        pp=5,
        power=130,
        accuracy=85,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.らいげき_apply_paralysis_to_defender,
            )
        }
    ),
    "ライジングボルト": MoveData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ライジングボルト_calc_power,
                subject_spec="attacker:self",
            ),
        },
    ),
    "らいめいげり": MoveData(
        type="かくとう",
        category="physical",
        pp=10,
        power=90,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.らいめいげり_lower_defender_def,
            )
        }
    ),
    "ラスターカノン": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ラスターカノン_lower_defender_spd,
            )
        }
    ),
    "ラスターパージ": MoveData(
        type="エスパー",
        category="special",
        pp=8,
        power=95,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ラスターパージ_lower_defender_spd,
            )
        }
    ),
    "リサイクル": MoveData(
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.リサイクル_can_apply,
                priority=100,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.リサイクル_restore_item,
            ),
        }
    ),
    "リフレクター": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.リフレクター_set_side_field,
            ),
        }
    ),
    "りゅうせいぐん": MoveData(
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.りゅうせいぐん_sharply_lower_attacker_spa,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.りゅうせいぐん_lower_spa)
        }
    ),
    "りゅうのいぶき": MoveData(
        type="ドラゴン",
        category="special",
        pp=20,
        power=60,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.りゅうのいぶき_apply_paralysis_to_defender,
            )
        }
    ),
    "りゅうのはどう": MoveData(
        flags={"pulse"},
        handlers={},  # 追加効果なし
    ),
    "りゅうのまい": MoveData(
        flags={"dance"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.りゅうのまい_boost_attacker_atk_spe,
            ),
        }
    ),
    "りんごさん": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.りんごさん_lower_defender_spd,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.りんごさん_lower_spd)
        }
    ),
    "りんしょう": MoveData(
        flags={"sound"},
        handlers={
            Event.ON_BEGIN_MOVE: h.MoveHandler(
                ha.りんしょう_apply_chain_power,
            ),
        }
    ),
    "リーフストーム": MoveData(
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.リーフストーム_sharply_lower_attacker_spa,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.オーバーヒート_lower_attacker_spa)
        }
    ),
    "リーフブレード": MoveData(
        flags={"contact", "slash"},
        handlers={},  # 追加効果なし
    ),
    "ルミナコリジョン": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ルミナコリジョン_sharply_lower_defender_spd,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.ルミナコリジョン_lower_spd)
        }
    ),
    "レイジングブル": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.MoveHandler(
                ha.レイジングブル_modify_move_type,
            ),
            Event.ON_HIT: h.MoveHandler(
                ha.レイジングブル_break_screens,
            ),
        },
    ),
    "れいとうパンチ": MoveData(
        flags={"contact", "punch", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.れいとうパンチ_apply_freeze_to_defender,
            )
        }
    ),
    "れいとうビーム": MoveData(
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.れいとうビーム_apply_freeze_to_defender,
            )
        }
    ),
    "れんごく": MoveData(
        flags={"secondary_effect", "thaw"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.れんごく_apply_burn_to_defender,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.れんごく_apply_やけど)
        }
    ),
    "れんぞくぎり": MoveData(
        type="むし",
        category="physical",
        pp=20,
        power=40,
        accuracy=95,
        flags={"contact", "slash"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.れんぞくぎり_calc_power,
                subject_spec="attacker:self",
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.れんぞくぎり_apply_count,
                subject_spec="attacker:self",
            ),
            Event.ON_MISS: h.MoveHandler(
                ha.れんぞくぎり_reset_on_miss,
                subject_spec="attacker:self",
            ),
        },
    ),
    "ロックオン": MoveData(
        # マジックコートで跳ね返されない
        flags={"unreflectable"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ロックオン_apply,
            ),
        }
    ),
    "ロックカット": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ロックカット_boost_attacker_spe,
            )
        }
    ),
    "ロッククライム": MoveData(
        type="ノーマル",
        category="physical",
        pp=20,
        power=90,
        accuracy=85,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ロッククライム_apply_confusion_to_defender,
            )
        }
    ),
    "ロックブラスト": MoveData(
        pp=12,  # チャンピオンズ基準（.internal/champions/move_list.txt）。第9世代本家基準は10
        flags={"bullet"},
        multi_hit={
            "min": 2,
            "max": 5,
            "check_hit_each_time": False,
            "power_sequence": (),
        },
        handlers={},  # 追加効果なし
    ),
    "ローキック": MoveData(
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ローキック_lower_defender_spe,
            )
        }
    ),
}
