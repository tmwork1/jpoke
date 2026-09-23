"""Battle.calc_move_base_power / calc_move_power による威力問い合わせのテスト。"""
from __future__ import annotations

from jpoke import Pokemon

from . import test_utils as t


def test_calc_move_powerでMove状態を復元する():
    """問い合わせ後に基礎威力・タイプ・分類・ハンドラ登録を残さない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["はきだす"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 2},
    )
    attacker, defender = battle.actives
    move = attacker.moves[0]
    original = (move.base_power, move.type, move.category)
    assert battle.calc_move_power(attacker, defender, move) == 200
    assert (move.base_power, move.type, move.category) == original
    assert all(event not in battle.events.handlers for event in move.data.handlers)


def test_calc_move_powerでテラスタルの威力60底上げを反映する():
    """テラスタイプ一致の低威力技は60に底上げされる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", tera_type="ノーマル", move_names=["でんこうせっか", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    attacker.terastallize()
    assert battle.calc_move_power(attacker, defender, "たいあたり") == 60
    # 優先度+1の技は底上げ対象外
    assert battle.calc_move_power(attacker, defender, "でんこうせっか") == 40


def test_calc_move_powerで固定威力技はデータ値を返す():
    """補正のない技はデータ上の威力をそのまま返す。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["のしかかり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    assert battle.calc_move_power(attacker, defender, attacker.moves[0]) == 85


def test_calc_move_powerで変化技は0を返す():
    """威力を持たない技は0。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["のろい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    assert battle.calc_move_power(attacker, defender, "のろい") == 0


def test_calc_move_powerで特性と持ち物の補正を反映する():
    """てつのこぶし+パンチグローブの乗算補正を含めた最終威力を返す。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", ability_name="てつのこぶし", item_name="パンチグローブ",
                       move_names=["ドレインパンチ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    # 75 × 1.2 × 1.1 = 99
    assert battle.calc_move_power(attacker, defender, "ドレインパンチ") == 99


def test_calc_move_powerで相手依存の威力変動を反映する():
    """けたぐりは相手の体重で威力が決まる（カビゴン460kg→120）。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["けたぐり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    assert battle.calc_move_power(attacker, defender, "けたぐり") == 120


def test_アクロバット_calc_move_base_powerで道具の有無を反映する():
    """道具を持っていないとき基礎威力は110、持っているときは55のまま。"""
    battle_no_item = t.start_battle(
        team0=[Pokemon("チルタリス", move_names=["アクロバット"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker_no_item, defender_no_item = battle_no_item.actives
    assert battle_no_item.calc_move_base_power(attacker_no_item, defender_no_item, "アクロバット") == 110

    battle_item = t.start_battle(
        team0=[Pokemon("チルタリス", item_name="たべのこし", move_names=["アクロバット"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker_item, defender_item = battle_item.actives
    assert battle_item.calc_move_base_power(attacker_item, defender_item, "アクロバット") == 55


def test_アシストパワー_calc_move_base_powerでランク上昇を反映する():
    """正ランク合計3段階のとき基礎威力80（20 + 20*3）。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["アシストパワー"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    battle.modify_stats(attacker, {"atk": 2, "def": 1}, source=attacker)
    assert battle.calc_move_base_power(attacker, defender, "アシストパワー") == 80


def test_ウェザーボール_calc_move_base_powerで天候を反映する():
    """天候が有効なとき基礎威力は100、天候がないときは50のまま。"""
    battle_weather = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ウェザーボール"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    attacker_weather, defender_weather = battle_weather.actives
    assert battle_weather.calc_move_base_power(attacker_weather, defender_weather, "ウェザーボール") == 100

    battle_none = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ウェザーボール"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker_none, defender_none = battle_none.actives
    assert battle_none.calc_move_base_power(attacker_none, defender_none, "ウェザーボール") == 50


def test_エコーボイス_calc_move_powerで連続使用の威力を副作用なしに返す():
    """前ターンに使用済みなら80を返し、問い合わせ自体は使用として記録されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["エコーボイス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    assert battle.calc_move_power(attacker, defender, "エコーボイス") == 40
    t.run_move(battle, 0)
    battle.turn += 1
    assert battle.calc_move_power(attacker, defender, "エコーボイス") == 80
    assert battle.calc_move_power(attacker, defender, "エコーボイス") == 80
    # 問い合わせでは使用記録が更新されない
    assert battle.echoed_voice_last_turn == battle.turn - 1
    assert battle.echoed_voice_power == 40
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 80


def test_けたぐり_calc_move_base_powerで持ち物補正を含まない():
    """カビゴン相手の基礎威力は120で、くろおびの1.2倍補正は含まない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", item_name="くろおび", move_names=["けたぐり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    assert battle.calc_move_base_power(attacker, defender, "けたぐり") == 120
    assert battle.calc_move_power(attacker, defender, "けたぐり") == 144


def test_ころがる_calc_move_base_powerで連続命中回数を反映する():
    """揮発状態count=2のとき基礎威力は120（30 × 2^2）、揮発状態がなければ30のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("イシツブテ", move_names=["ころがる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    assert battle.calc_move_base_power(attacker, defender, "ころがる") == 30

    battle.volatile_manager.apply(attacker, "ころがる", count=2, source=attacker, move_name="ころがる")
    assert battle.calc_move_base_power(attacker, defender, "ころがる") == 120


def test_だいちのはどう_calc_move_base_powerでフィールドを反映する():
    """接地かつフィールドありのとき基礎威力は100、フィールドがないときは50のまま。"""
    battle_terrain = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいちのはどう"])],
        team1=[Pokemon("カビゴン")],
        terrain=("エレキフィールド", 5),
    )
    attacker_terrain, defender_terrain = battle_terrain.actives
    assert battle_terrain.calc_move_base_power(attacker_terrain, defender_terrain, "だいちのはどう") == 100

    battle_none = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいちのはどう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker_none, defender_none = battle_none.actives
    assert battle_none.calc_move_base_power(attacker_none, defender_none, "だいちのはどう") == 50


def test_テラバースト_calc_move_base_powerでステラテラスタル時に100を返す():
    """ステラテラスタル中は基礎威力100、テラスタルしていなければ80のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", tera_type="ステラ", move_names=["テラバースト"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    assert battle.calc_move_base_power(attacker, defender, "テラバースト") == 80

    attacker.terastallize()
    assert battle.calc_move_base_power(attacker, defender, "テラバースト") == 100


def test_なげつける_calc_move_powerで持ち物の威力を返す():
    """くろいてっきゅうなら130、持ち物なしなら0。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="くろいてっきゅう", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン", move_names=["なげつける"])],
    )
    attacker, defender = battle.actives
    assert battle.calc_move_power(attacker, defender, "なげつける") == 130
    assert battle.calc_move_power(defender, attacker, "なげつける") == 0


def test_のろい_calc_move_base_powerで変化技は0を返す():
    """威力を持たない変化技は0。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["のろい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    assert battle.calc_move_base_power(attacker, defender, "のろい") == 0


def test_はきだす_calc_move_base_powerでMove状態を復元する():
    """たくわえ2回の基礎威力200を返し、技の可変状態とハンドラ登録を残さない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["はきだす"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 2},
    )
    attacker, defender = battle.actives
    move = attacker.moves[0]
    original = (move.base_power, move.type, move.category)
    assert battle.calc_move_base_power(attacker, defender, move) == 200
    assert (move.base_power, move.type, move.category) == original
    assert all(event not in battle.events.handlers for event in move.data.handlers)


def test_はきだす_calc_move_powerでたくわえ回数を反映する():
    """たくわえ回数×100。回数0なら0。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["はきだす"])],
        team1=[Pokemon("カビゴン", move_names=["はきだす"])],
        volatile0={"たくわえる": 3},
    )
    attacker, defender = battle.actives
    assert battle.calc_move_power(attacker, defender, "はきだす") == 300
    assert battle.calc_move_power(defender, attacker, "はきだす") == 0


def test_りんしょう_calc_move_powerで同ターン使用済みの威力を副作用なしに返す():
    """同じターンに使用済みなら120を返し、問い合わせ自体は使用として記録されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["りんしょう"])],
        team1=[Pokemon("カビゴン", move_names=["りんしょう"])],
        accuracy=100,
    )
    attacker, defender = battle.actives
    assert battle.calc_move_power(attacker, defender, "りんしょう") == 60
    assert battle.round_used_turn != battle.turn
    t.run_move(battle, 1)
    assert battle.calc_move_power(attacker, defender, "りんしょう") == 120
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 120
