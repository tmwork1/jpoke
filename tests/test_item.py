"""持ち物ハンドラの単体テスト"""
import math
from types import SimpleNamespace
from jpoke import Pokemon
from jpoke.core.event import EventContext
from jpoke.utils.enums import Event
from jpoke.data import ITEMS
import test_utils as t


def test_いのちのたま():
    """いのちのたま: 攻撃技でダメージ"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", item="いのちのたま", moves=["たいあたり"])],
        turn=1
    )
    assert battle.actives[0].item.revealed
    assert battle.actives[0].hp == math.ceil(battle.actives[0].max_hp * 7/8)


def test_いのちのたま_変化技では発動しない():
    """いのちのたま: 変化技では発動しない"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", item="いのちのたま", moves=["はねる"])],
        turn=1
    )
    assert not battle.actives[0].item.revealed


def test_きれいなぬけがら():
    """きれいなぬけがら: 交代防止無効"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", item="きれいなぬけがら") for _ in range(2)],
        foe=[Pokemon("ピカチュウ", ability="かげふみ")],
    )
    assert t.can_switch(battle, 0)


def test_さらさらいわ():
    """さらさらいわ: 天候延長"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", item="さらさらいわ")],
    )
    battle.weather_mgr.activate("すなあらし", 5, source=battle.actives[0])
    assert battle.weather.count == 8


def test_だっしゅつパック():
    """だっしゅつパック: 能力ダウンで交代"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", item="だっしゅつパック"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", ability="いかく")],
    )
    assert battle.players[0].active_idx != 0
    assert battle.players[0].team[0].item.revealed
    assert not battle.players[0].team[0].item._enabled


def test_だっしゅつパック_能力上昇では発動しない():
    """だっしゅつパック: 能力上昇では発動しない"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", item="だっしゅつパック", moves=["つるぎのまい"]), Pokemon("ライチュウ")],
        turn=1,
    )
    assert not battle.players[0].team[0].item.revealed


def test_だっしゅつボタン():
    """だっしゅつボタン: ダメージを受けて交代"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", item="だっしゅつボタン"), Pokemon("ライチュウ")],
        foe=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        turn=1,
    )
    assert battle.players[0].active_idx != 0
    assert battle.players[0].team[0].item.revealed
    assert not battle.players[0].team[0].item._enabled


def test_たべのこし():
    """たべのこし: ターン終了時回復"""
    mon = Pokemon("ピカチュウ", item="たべのこし")
    battle = t.start_battle(ally=[mon], turn=1)
    assert not battle.actives[0].item.revealed
    mon._hp = 1  # テスト用に内部変数を直接変更
    battle.events.emit(Event.ON_TURN_END_2, EventContext(source=battle.actives[0]), None)
    assert battle.actives[0].item.revealed
    assert battle.actives[0].hp == 1 + mon.max_hp // 16


def _dummy_move(type_name: str) -> SimpleNamespace:
    return SimpleNamespace(type=type_name, name="ダミー")


def test_タイプ強化アイテム():
    """タイプ強化アイテム: 対応タイプ威力補正"""
    base_value = 4096
    for item_name, data in ITEMS.items():
        if not data.power_modifier_by_type:
            continue

        type_name, modifier = next(iter(data.power_modifier_by_type.items()))
        battle = t.start_battle(
            ally=[Pokemon("ピカチュウ", item=item_name)],
            foe=[Pokemon("ピカチュウ")],
        )
        ctx = EventContext(
            attacker=battle.actives[0],
            defender=battle.actives[1],
            move=_dummy_move(type_name),
        )
        actual = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, base_value)
        expected = base_value * modifier
        assert abs(actual - expected) < 0.01, f"{item_name}: expected {expected}, got {actual}"


def test_タイプ半減実():
    """タイプ半減実: 対応タイプの被ダメージ補正"""
    base_value = 4096
    for item_name, data in ITEMS.items():
        if not data.damage_modifier_by_type:
            continue

        type_name, modifier = next(iter(data.damage_modifier_by_type.items()))
        battle = t.start_battle(
            ally=[Pokemon("ピカチュウ", item=item_name)],
            foe=[Pokemon("ピカチュウ")],
        )
        ctx = EventContext(
            attacker=battle.actives[0],
            defender=battle.actives[1],
            move=_dummy_move(type_name),
        )
        actual = battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, base_value)
        expected = base_value * modifier
        assert abs(actual - expected) < 0.01, f"{item_name}: expected {expected}, got {actual}"
        assert battle.actives[0].item.revealed, f"{item_name}: アイテムが公開されていない"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
