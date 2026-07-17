"""技データ定義モジュール（記号・英数字のエントリ）。

`data/move.py` から分割された、MOVES辞書の一部を定義する。
分割・並び替えは scripts/sort_data/sort_moves.py が行うため、手編集時も
五十音順を維持すること。
"""
from jpoke.enums import Event, LethalEvent
from jpoke.core.lethal import LethalHandler
from jpoke.types import MoveName
from jpoke.utils.constants import PP_INFINITE

from jpoke.handlers import move as h
from jpoke.handlers import move_attack as ha
from jpoke.handlers import lethal as l

from ..models import MoveData


MOVES_SYMBOL: dict[MoveName, MoveData] = {
    "わるあがき": MoveData(
        type="",
        category="physical",
        pp=PP_INFINITE,
        power=50,
        flags={"contact", "non_encore", "non_onnen", "non_copycat"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.わるあがき_self_damage,
            )
        }
    ),
    "_こんらん": MoveData(
        type="",
        category="physical",
        pp=PP_INFINITE,
        power=40,
    ),
    "10まんばりき": MoveData(
        type="じめん",
        category="physical",
        pp=12,
        power=95,
        accuracy=95,
        flags={"contact"},
        handlers={},  # 追加効果なし
    ),
    "10まんボルト": MoveData(
        type="でんき",
        category="special",
        pp=16,
        power=90,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha._10まんボルト_apply_paralysis_to_defender,
            )
        }
    ),
    "3ぼんのや": MoveData(
        type="かくとう",
        category="physical",
        pp=12,
        power=90,
        accuracy=100,
        crit_ratio=1,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: [
                h.MoveHandler(
                    ha._3ぼんのや_lower_defender_def,
                ),
                h.MoveHandler(
                    ha._3ぼんのや_apply_flinch,
                ),
            ]
        }
    ),
    "DDラリアット": MoveData(
        type="あく",
        category="physical",
        pp=12,
        power=85,
        accuracy=100,
        flags={"contact"},
        handlers={
            Event.ON_CALC_DEF_RANK_MODIFIER: h.MoveHandler(
                ha.DDラリアット_ignore_def_rank,
                subject_spec="attacker:self",
            ),
        }
    ),
    "Gのちから": MoveData(
        type="くさ",
        category="physical",
        pp=12,
        power=90,
        accuracy=100,
        flags={"secondary_effect"},
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.Gのちから_gravity_boost,
                subject_spec="attacker:self",
            ),
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.Gのちから_lower_defender_def,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.Gのちから_lower_def)
        }
    ),
    "Vジェネレート": MoveData(
        type="ほのお",
        category="physical",
        pp=5,
        power=180,
        accuracy=95,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.Vジェネレート_lower_attacker_def_spd_spe,
            )
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(l.Vジェネレート_lower_attacker_def_spd_spe)
        }
    ),
}
