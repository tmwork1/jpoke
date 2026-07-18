"""技データ定義モジュール（や行のエントリ）。

`data/move.py` から分割された、MOVES辞書の一部を定義する。
分割・並び替えは scripts/sort_data/sort_moves.py が行うため、手編集時も
五十音順を維持すること。
"""
from jpoke.enums import Event
from jpoke.types import MoveName

from jpoke.handlers import move as h
from jpoke.handlers import move_attack as ha
from jpoke.handlers import move_status as hs

from ..models import MoveData


MOVES_YA: dict[MoveName, MoveData] = {
    "やきつくす": MoveData(
        type="ほのお",
        category="special",
        pp=15,
        power=60,
        accuracy=100,
        flags={"spread"},
        handlers={
            # .internal/spec/turn.md では Event.ON_DAMAGE 優先度30に記載されているが、
            # HP回復ピンチきのみ（オボンのみ等）はダメージ反映時のON_HP_CHANGEDで
            # 発動判定されるため、それより前のEvent.ON_MODIFY_MOVE_DAMAGE
            # （roll_damage後・modify_hp前）で焼却しないと燃やす前に回復してしまう。
            # 詳細は .internal/plan/moves/やきつくす.md を参照。
            Event.ON_MODIFY_MOVE_DAMAGE: h.MoveHandler(
                ha.やきつくす_burn_item,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "やけっぱち": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.やけっぱち_calc_power,
                subject_spec="attacker:self",
            ),
        },
    ),
    "やどりぎのタネ": MoveData(
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.やどりぎのタネ_can_apply,
                priority=130,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.やどりぎのタネ_apply,
            ),
        }
    ),
    "やまあらし": MoveData(
        crit_ratio=3,
        flags={"contact"},
        handlers={},  # 常に急所に当たる（crit_ratio=3）
    ),
    "ゆきげしき": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ゆきげしき_activate_weather,
            ),
        }
    ),
    "ゆきなだれ": MoveData(
        flags={"contact"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ゆきなだれ_calc_power,
                subject_spec="attacker:self",
            ),
        },
    ),
    "ゆびをふる": MoveData(
        type="ノーマル",
        category="status",
        pp=10,  # champions_move_list.txtに記載なし。第9世代の値を採用（.internal/plan/moves/ゆびをふる.md参照）
        flags={"non_negoto", "non_copycat"},  # まねっこでコピー不可（第二世代以降一貫して×）
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ゆびをふる_select_and_execute,
            ),
            Event.ON_MODIFY_PP_CONSUMED: h.MoveHandler(
                hs.ゆびをふる_suppress_pp,
            ),
        },
    ),
    "ゆめくい": MoveData(
        type="エスパー",
        category="special",
        pp=15,
        power=100,
        accuracy=100,
        flags={"heal"},
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.MoveHandler(
                hs.ゆめくい_check_sleep,
            ),
            Event.ON_HIT: h.MoveHandler(ha.ゆめくい_drain, priority=20)
        }
    ),
    "ようかいえき": MoveData(
        type="どく",
        category="special",
        pp=30,
        power=40,
        accuracy=100,
        flags={"secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ようかいえき_lower_defender_spd,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "ようせいのかぜ": MoveData(
        type="フェアリー",
        category="special",
        pp=30,
        power=40,
        accuracy=100,
        flags={"wind"},
        handlers={},  # 追加効果なし
    ),
}
