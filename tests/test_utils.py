"""テストヘルパーの薄い再エクスポート層。

実体は `jpoke.testing`（本体パッケージへ昇格済み）に移設した。既存テストコードの
`from . import test_utils as t` / `from .. import test_utils as t` という参照パターンを
壊さないための後方互換シムとして残している。新規コードは `jpoke.testing` を直接
参照してよい。
"""
from jpoke.testing import (
    CustomPlayer,
    start_battle,
    reserve_command,
    build_context,
    run_move,
    run_switch,
    can_switch,
    change_item,
    end_turn,
    apply_ailment,
    get_action_order,
    fix_damage,
    fix_random,
    calc_lethal,
    calc_move_priority,
)

__all__ = [
    "CustomPlayer",
    "start_battle",
    "reserve_command",
    "build_context",
    "run_move",
    "run_switch",
    "can_switch",
    "change_item",
    "end_turn",
    "apply_ailment",
    "get_action_order",
    "fix_damage",
    "fix_random",
    "calc_lethal",
    "calc_move_priority",
]
