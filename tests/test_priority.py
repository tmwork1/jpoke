"""優先度システムのテスト。

優先度の範囲（-7～+5）、計算、行動順への適用を検証。
"""

import pytest
from jpoke import Battle, Pokemon
from jpoke.enums import Command
from test_utils import start_battle


def test_positive_priority():
    """優先度プラスの技は優先度0の技より先に行動する。"""
    battle = start_battle(
        ally=[Pokemon("フシギダネ", moves=["しんそく"])]
    )
    for player in battle.players:
        player.init_turn()
        player.reserve_command(Command.MOVE_0)
    order = battle.determine_action_order()
    assert order[0] == battle.actives[0], "Incorrect action order"


def test_negative_priority():
    """優先度-6の技は優先度0の技より後に行動する。"""
    battle = start_battle(
        ally=[Pokemon("ゲンガー", moves=["あてみなげ"])]
    )
    for player in battle.players:
        player.init_turn()
        player.reserve_command(Command.MOVE_0)
    order = battle.determine_action_order()
    assert order[-1] == battle.actives[0], "Incorrect action order"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
