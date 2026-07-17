"""技データ定義モジュール（わ行のエントリ）。

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


MOVES_WA: dict[MoveName, MoveData] = {
    "ワイドガード": MoveData(
        pp=12,  # champions基準（.internal/champions/move_list.txt 970行目）。Gen9本家は10
        target="own_side",  # 味方の場が対象。foe/foe_side ではないためマジックコート等の対象外になる
        flags={"protect"},  # まもる系共通の連続使用失敗チェック対象（.internal/spec/moves/ワイドガード.md参照）
        handlers={
            Event.ON_TRY_MOVE_2: h.MoveHandler(
                hs.まもる系_連続使用失敗チェック,
            ),
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ワイドガード_apply,
            ),
        },
    ),
    "ワイドフォース": MoveData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ワイドフォース_calc_power,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        },
    ),
    "ワイドブレイカー": MoveData(
        flags={"contact", "secondary_effect", "spread"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ワイドブレイカー_lower_defender_atk,
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(
                ha.reduce_damage_in_double_battle,
            ),
        }
    ),
    "ワイルドボルト": MoveData(
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ワイルドボルト_recoil,
            )
        }
    ),
    "わたほうし": MoveData(
        flags={"powder", "spread"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.わたほうし_lower_defender_spe,
            ),
        }
    ),
    "わるだくみ": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.わるだくみ_boost_attacker_spa,
            )
        }
    ),
    "ワンダースチーム": MoveData(
        type="フェアリー",
        category="special",
        pp=10,
        power=90,
        accuracy=95,
        flags={"secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ワンダースチーム_apply_confusion_to_defender,
            )
        }
    ),
    "ワンダールーム": MoveData(
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ワンダールーム_activate_global_field,
            ),
        }
    ),
}
