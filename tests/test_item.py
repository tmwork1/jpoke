"""アイテムハンドラの単体テスト"""
import math
from types import SimpleNamespace
from jpoke import Pokemon
from jpoke.core import EventContext
from jpoke.enums import Event
from jpoke.data import ITEMS
import test_utils as t


# ──────────────────────────────────────────────────────────────────
# いのちのたま
# ──────────────────────────────────────────────────────────────────

def test_いのちのたま():
    """いのちのたま: 攻撃技で反動ダメージ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="いのちのたま", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    attacker = battle.actives[0]
    assert attacker.hp == math.ceil(attacker.max_hp * 7/8)
    assert attacker.item.revealed


def test_いのちのたま_変化技では発動しない():
    """いのちのたま: 変化技では発動しない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", item_name="いのちのたま", move_names=["はねる"])],
    )
    t.run_move(battle, 0)
    assert not battle.actives[0].item.revealed


# ──────────────────────────────────────────────────────────────────
# きれいなぬけがら
# ──────────────────────────────────────────────────────────────────
def test_きれいなぬけがら():
    """きれいなぬけがら: 交代防止無効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きれいなぬけがら"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かげふみ")],
    )
    assert battle.can_switch(battle.players[0])

# ──────────────────────────────────────────────────────────────────
# 天候石
# さらさらいわ
# ──────────────────────────────────────────────────────────────────


def test_さらさらいわ():
    """さらさらいわ: 天候延長"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="さらさらいわ")],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.weather_manager.apply("すなあらし", 5, source=battle.actives[0])
    assert battle.raw_weather.count == 8


# ──────────────────────────────────────────────────────────────────
# だっしゅつパック
# ──────────────────────────────────────────────────────────────────
def test_だっしゅつパック_0ターン目にいかくで交代():
    """だっしゅつパック: 能力ダウンで交代"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつパック"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    state = battle._player_states[0]
    ejected_mon = state.team[0]
    assert state.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


def test_だっしゅつパック_能力上昇では発動しない():
    """だっしゅつパック: 能力上昇では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつパック", move_names=["つるぎのまい"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    state = battle._player_states[0]
    mon = state.team[0]
    assert state.active_index == 0
    assert not mon.item.revealed
    assert mon.has_item()

# ──────────────────────────────────────────────────────────────────
# だっしゅつボタン
# ──────────────────────────────────────────────────────────────────


def test_だっしゅつボタン():
    """だっしゅつボタン: ダメージを受けて交代"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="だっしゅつボタン"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    player = battle.players[0]
    print(battle.get_available_switch_commands(player))
    state = battle._player_states[0]
    ejected_mon = battle.actives[0]
    battle.advance_turn()
    assert state.active_index == 1
    assert ejected_mon.item.revealed
    assert not ejected_mon.has_item()


# ──────────────────────────────────────────────────────────────────
# たべのこし
# ──────────────────────────────────────────────────────────────────
def test_たべのこし():
    """たべのこし: ターン終了時回復"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", item_name="たべのこし")],
    )
    mon = battle.actives[0]
    # HPが満タンのときは回復しない
    battle.events.emit(Event.ON_TURN_END)
    battle.print_logs()
    assert not mon.item.revealed

    mon.hp = 1  # テスト用に内部変数を直接変更
    battle.events.emit(Event.ON_TURN_END)
    assert mon.item.revealed
    assert mon.hp == 1 + mon.max_hp // 16


def _dummy_move(type_name: str) -> SimpleNamespace:
    return SimpleNamespace(type=type_name, name="ダミー")


# ──────────────────────────────────────────────────────────────────
# タイプ強化アイテム
# ──────────────────────────────────────────────────────────────────


def test_タイプ強化アイテム():
    """タイプ強化アイテム: 対応タイプ威力補正"""
    base_value = 4096
    for item_name, data in ITEMS.items():
        if not data.power_modifier_by_type:
            continue

        type_name, modifier = next(iter(data.power_modifier_by_type.items()))
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", item_name=item_name)],
            team1=[Pokemon("ピカチュウ")],
        )
        ctx = EventContext(
            attacker=battle.actives[0],
            defender=battle.actives[1],
            move=_dummy_move(type_name),
        )
        actual = battle.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, base_value)
        expected = base_value * modifier
        assert abs(actual - expected) < 0.01, f"{item_name}: expected {expected}, got {actual}"


# ──────────────────────────────────────────────────────────────────
# タイプ半減実
# ──────────────────────────────────────────────────────────────────

def test_タイプ半減実():
    """タイプ半減実: 対応タイプの被ダメージ補正"""
    base_value = 4096
    for item_name, data in ITEMS.items():
        if not data.damage_modifier_by_type:
            continue

        type_name, modifier = next(iter(data.damage_modifier_by_type.items()))
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", item_name=item_name)],
            team1=[Pokemon("ピカチュウ")],
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
