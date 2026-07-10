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
        type="いわ",
        category="status",
        pp=12,  # champions基準（docs/champions/move_list.txt 970行目）。Gen9本家は10
        priority=3,
        target="own_side",  # 味方の場が対象。foe/foe_side ではないためマジックコート等の対象外になる
        handlers={},  # 本プロジェクトはシングルバトル専用で、本技が防ぐ「複数対象の技」を区別する
        # ターゲット種別（相手全体・自分以外全体）を技データ上でモデル化していないため、
        # 現状は防御対象となる技が存在せず実質効果なし。詳細はdocs/spec/moves/ワイドガード.md参照
    ),
    "ワイドフォース": MoveData(
        type="エスパー",
        category="special",
        pp=10,
        power=80,
        accuracy=100,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.MoveHandler(
                ha.ワイドフォース_calc_power,
                subject_spec="attacker:self",
            ),
        },
    ),
    "ワイドブレイカー": MoveData(
        type="ドラゴン",
        category="physical",
        pp=16,
        power=60,
        accuracy=100,
        flags={"contact", "secondary_effect"},
        handlers={
            Event.ON_DAMAGE_HIT: h.MoveHandler(
                ha.ワイドブレイカー_lower_defender_atk,
            )
        }
    ),
    "ワイルドボルト": MoveData(
        type="でんき",
        category="physical",
        pp=16,
        power=90,
        accuracy=100,
        flags={"contact", "recoil"},
        handlers={
            Event.ON_HIT: h.MoveHandler(
                ha.ワイルドボルト_recoil,
            )
        }
    ),
    "わたほうし": MoveData(
        type="くさ",
        category="status",
        pp=20,
        accuracy=100,
        flags={"powder"},
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.わたほうし_modify_defender_stats,
            ),
        }
    ),
    "わるだくみ": MoveData(
        type="あく",
        category="status",
        pp=20,
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.わるだくみ_modify_attacker_stats,
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
        type="エスパー",
        category="status",
        pp=10,
        target="field",
        flags=set(),
        handlers={
            Event.ON_STATUS_HIT: h.MoveHandler(
                hs.ワンダールーム_activate_global_field,
            ),
        }
    ),
}
