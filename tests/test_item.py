"""アイテムハンドラの単体テスト"""
import math
from types import SimpleNamespace
from typing import cast
from jpoke import Pokemon
from jpoke.core import AttackContext, EventContext
from jpoke.enums import Event
from jpoke.data import ITEMS
from jpoke.model import Move
from . import test_utils as t

def _dummy_move(type_name: str) -> Move:
    return cast(Move, SimpleNamespace(type=type_name, name="ダミー"))


def test_いしずえのめん_物理技強化():
    """いしずえのめん: 物理技の攻撃補正1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(いしずえ)", item_name="いしずえのめん", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4915


def test_いしずえのめん_特殊技は補正なし():
    """いしずえのめん: 特殊技には攻撃補正がない"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(いしずえ)", item_name="いしずえのめん", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_いどのめん_物理技強化():
    """いどのめん: 物理技の攻撃補正1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(いど)", item_name="いどのめん", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4915


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


def test_かまどのめん_物理技強化():
    """かまどのめん: 物理技の攻撃補正1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(かまど)", item_name="かまどのめん", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4915


def test_きれいなぬけがら():
    """きれいなぬけがら: 交代防止無効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="きれいなぬけがら"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="かげふみ")],
    )
    assert battle.can_switch(battle.players[0])


def test_こだわりスカーフ_交代でロック解除():
    """こだわりスカーフ: 交代するとこだわりロックが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりスカーフ", move_names=["たいあたり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.has_volatile("こだわり")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("こだわり")


def test_こだわりスカーフ_技ロック():
    """こだわりスカーフ: 技使用後にこだわりロック"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりスカーフ", move_names=["たいあたり", "でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.has_volatile("こだわり")
    assert mon.volatiles["こだわり"].move_name == "たいあたり"


def test_こだわりスカーフ_素早さ強化():
    """こだわりスカーフ: 素早さ1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりスカーフ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    base_speed = mon.stats["S"]
    assert battle.calc_effective_speed(mon) == base_speed * 6144 // 4096


def test_こだわりハチマキ_技ロック():
    """こだわりハチマキ: 技使用後にこだわりロック"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりハチマキ", move_names=["たいあたり", "でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.has_volatile("こだわり")
    assert mon.volatiles["こだわり"].move_name == "たいあたり"


def test_こだわりハチマキ_物理技強化():
    """こだわりハチマキ: 物理技の攻撃補正1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりハチマキ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 6144


def test_こだわりハチマキ_特殊技は補正なし():
    """こだわりハチマキ: 特殊技には攻撃補正がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりハチマキ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_こだわりメガネ_技ロック():
    """こだわりメガネ: 技使用後にこだわりロック"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりメガネ", move_names=["でんきショック", "たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.has_volatile("こだわり")
    assert mon.volatiles["こだわり"].move_name == "でんきショック"


def test_こだわりメガネ_物理技は補正なし():
    """こだわりメガネ: 物理技には攻撃補正がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりメガネ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096


def test_こだわりメガネ_特殊技強化():
    """こだわりメガネ: 特殊技の攻撃補正1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりメガネ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 6144


def test_さらさらいわ():
    """さらさらいわ: 天候延長"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="さらさらいわ")],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.weather_manager.apply("すなあらし", 5, source=battle.actives[0])
    assert battle.raw_weather.count == 8


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
        battle.actives[0].moves[0] = _dummy_move(type_name)  # テスト用に内部変数を直接変更
        t.run_move(battle, 0)
        assert battle.damage_calculator.damage_modifier == 2048 * modifier


def test_タイプ強化アイテム():
    """タイプ強化アイテム: 対応タイプ威力補正"""
    base_value = 4096
    for item_name, data in ITEMS.items():
        if not data.power_modifier_by_type:
            continue

        type_, modifier = next(iter(data.power_modifier_by_type.items()))
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", item_name=item_name)],
            team1=[Pokemon("ピカチュウ")],
        )
        battle.actives[0].moves[0] = _dummy_move(type_)  # テスト用に内部変数を直接変更
        t.run_move(battle, 0)
        assert battle.damage_calculator.power_modifier == 6144


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


def test_メトロノーム_初回は補正なし():
    """メトロノーム: 同じ技の初回使用は威力補正なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_メトロノーム_別技でリセット():
    """メトロノーム: 違う技を使うとカウントリセット"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり", "でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.metronome_count = 3
    mon.metronome_move_name = "たいあたり"
    t.run_move(battle, 0, 1)
    assert mon.metronome_count == 1
    assert mon.metronome_move_name == "でんきショック"


def test_メトロノーム_最大2倍():
    """メトロノーム: 6回目以降は威力2倍（上限）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.metronome_count = 5
    mon.metronome_move_name = "たいあたり"
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8191


def test_メトロノーム_連続使用で威力増加():
    """メトロノーム: 2回目連続使用で威力1.2倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.metronome_count = 1
    mon.metronome_move_name = "たいあたり"
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
