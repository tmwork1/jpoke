"""優先度システムのテスト。

優先度の範囲（-7～+5）、計算、行動順への適用を検証。
"""

import pytest
from jpoke import Battle, Pokemon
from jpoke.enums import Command
import test_utils as t


def test_正の優先度():
    """優先度プラスの技は優先度0の技より先に行動する。"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("フシギダネ", moves=["しんそく"])]
                            )
    t.reserve_command(battle)
    order = battle.determine_action_order()
    assert order[0] == battle.actives[0], "Incorrect action order"


def test_負の優先度():
    """優先度-6の技は優先度0の技より後に行動する。"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ゲンガー", moves=["あてみなげ"])]
                            )
    t.reserve_command(battle)
    order = battle.determine_action_order()
    assert order[-1] == battle.actives[0], "Incorrect action order"


def test_あとだし_同優先度で最後に行動():
    """あとだし: 同優先度の技に対して最後に行動する。"""
    # ヤミラミ(あとだし, S低い)をallyに設定、foeはピカチュウ(S高い)
    battle = t.start_battle(
        ally=[Pokemon("ヤミラミ", ability="あとだし")],
        foe=[Pokemon("ピカチュウ")],
    )
    t.reserve_command(battle)
    order = battle.determine_action_order()
    assert order[-1] == battle.actives[0], "あとだし所持者が同優先度で最後に行動しない"


def test_あとだし_高優先度技は先攻():
    """あとだし: 相手より優先度が高い技を使用した場合は先攻になる。"""
    battle = t.start_battle(
        ally=[Pokemon("ヤミラミ", ability="あとだし", moves=["でんこうせっか"])],
        foe=[Pokemon("ピカチュウ")],
    )
    t.reserve_command(battle)
    order = battle.determine_action_order()
    assert order[0] == battle.actives[0], "あとだし所持者が高優先度技で先攻にならない"


def test_あとだし_トリックルームでも後攻():
    """あとだし: トリックルーム状態でも最後に行動する（素早さ逆転の影響を受けない）。"""
    battle = t.start_battle(
        ally=[Pokemon("ヤミラミ", ability="あとだし")],
        foe=[Pokemon("ピカチュウ")],
        global_field={"トリックルーム": 5},
    )
    t.reserve_command(battle)
    order = battle.determine_action_order()
    assert order[-1] == battle.actives[0], "あとだし所持者がトリックルームで後攻にならない"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
