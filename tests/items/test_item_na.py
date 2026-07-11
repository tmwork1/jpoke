"""アイテムハンドラの単体テスト"""
import pytest
from jpoke import Pokemon
from .. import test_utils as t


def test_ナゾのみ_ダメージ固定技では発動しない():
    """ナゾのみ: タイプ相性上は弱点でもダメージ固定技（一撃必殺技を除く）では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ちきゅうなげ"])],
        team1=[Pokemon("カビゴン", item_name="ナゾのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    hp_before = foe.hp
    t.run_move(battle, 0)
    assert foe.hp < hp_before
    assert foe.has_item()


def test_ナゾのみ_一撃必殺技を耐えたときは発動する():
    """ナゾのみ: 弱点タイプの一撃必殺技をこらえるで耐えた場合は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ゴース", move_names=["じわれ"])],
        team1=[Pokemon("ピカチュウ", item_name="ナゾのみ")],
        volatile1={"こらえる": 1},
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.hp == 1 + foe.max_hp // 4
    assert not foe.has_item()


def test_ナゾのみ_効果抜群でHP回復():
    """ナゾのみ: 効果抜群のダメージを受けたときHPを25%回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ゼニガメ", item_name="ナゾのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.fix_damage(battle, 50)
    t.run_move(battle, 0)
    assert foe.hp == foe.max_hp - 50 + foe.max_hp // 4
    assert not foe.has_item()


def test_ナゾのみ_等倍では発動しない():
    """ナゾのみ: 等倍の攻撃では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="ナゾのみ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.fix_damage(battle, 10)
    t.run_move(battle, 0)
    assert foe.hp == foe.max_hp - 10
    assert foe.has_item()


def test_ナナシのみ_こおり付与直後に即時回復する():
    """ナナシのみ: こおり付与直後（ON_APPLY_AILMENT）にターン終了を待たず即座に回復し消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン", item_name="ナナシのみ")],
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "こおり", source=battle.actives[0])
    assert not defender.ailment.is_active
    assert not defender.has_item()


def test_ナモのみ_どろぼうから奪われない():
    """ナモのみ: 効果バツグンのどろぼうを受けた場合、先に消費されるため奪われない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どろぼう"])],
        team1=[Pokemon("エーフィ", item_name="ナモのみ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.has_item()  # ナモのみの効果で消費済み
    assert not attacker.has_item()  # どろぼうでの奪取は失敗する


def test_ナモのみ_はたきおとすで威力補正を保ったままダメージ半減():
    """ナモのみ: 効果抜群のはたきおとすを受けても威力1.5倍は維持されたままダメージが半減する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はたきおとす"])],
        team1=[Pokemon("エーフィ", item_name="ナモのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144  # 威力1.5倍は維持される
    assert battle.damage_calculator.damage_modifier == 2048  # ダメージは半減される
    assert not defender.has_item()  # ナモのみの効果で消費済み（はたきおとすの除去は不発）


def test_ねばりのかぎづめ_なしでは通常ターン():
    """ねばりのかぎづめなし: まきつくでバインド状態の継続ターンが4か5になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まきつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.has_volatile("バインド")
    assert foe.volatiles["バインド"].count in {4, 5}


def test_ねばりのかぎづめ_バインドターン固定():
    """ねばりのかぎづめ: まきつくでバインド状態の継続ターンが7ターンに固定される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まきつく"], item_name="ねばりのかぎづめ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.has_volatile("バインド")
    assert foe.volatiles["バインド"].count == 7


def test_ねばりのかぎづめ_付与後の入手では延びない():
    """ねばりのかぎづめ: バインド付与後に入手しても継続ターンは延びない（付与時に確定）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まきつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    t.change_item(battle, mon, "ねばりのかぎづめ")
    assert foe.has_volatile("バインド")
    assert foe.volatiles["バインド"].count in {4, 5}


def test_ねばりのかぎづめ_付与後の喪失では減らない():
    """ねばりのかぎづめ: バインド付与後にアイテムを失っても継続ターンは減らない（付与時に確定）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まきつく"], item_name="ねばりのかぎづめ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    t.change_item(battle, mon, "")
    assert foe.has_volatile("バインド")
    assert foe.volatiles["バインド"].count == 7


def test_ねらいのまと_タイプ免疫を無効化():
    """ねらいのまと: タイプ相性による免疫（0倍）を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ゲンガー", item_name="ねらいのまと")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.hp < foe.max_hp


def test_ねらいのまと_ぶきようで効果が無効化される():
    """ねらいのまと: 特性ぶきようによりアイテム効果が失われ、通常どおり無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ゲンガー", item_name="ねらいのまと", ability_name="ぶきよう")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.hp == foe.max_hp


def test_ねらいのまと_浮遊による無効化には効果がない():
    """ねらいのまと: 浮遊（特性ふゆう）によるじめん技無効化（フリーフォール）には効果が及ばない"""
    battle = t.start_battle(
        team0=[Pokemon("ダグトリオ", move_names=["じしん"])],
        team1=[Pokemon("フワンテ", item_name="ねらいのまと", ability_name="ふゆう")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.hp == foe.max_hp


def test_ねらいのまと_複合タイプで無効化以外の相性は維持される():
    """ねらいのまと: 複合タイプの場合、無効化タイプ以外の相性補正（弱点等）はそのまま反映される

    ノーマル・エスパータイプのキリンリキがゴーストタイプの技を受けた場合、
    ゴースト→ノーマルの無効化はなくなるが、ゴースト→エスパーの効果抜群(2倍)はそのまま活きる。
    """
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["シャドーボール"])],
        team1=[Pokemon("キリンリキ", item_name="ねらいのまと")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == 4096 * 2


def test_のどスプレー_いやしのすずが不発のときは発動しない():
    """のどスプレー: いやしのすずで治療対象がおらず技が不発になったときは発動・消費しない"""
    battle = t.start_battle(
        team0=[Pokemon("プリン", item_name="のどスプレー", move_names=["いやしのすず"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert not mon.ailment.is_active
    t.run_move(battle, 0)
    assert mon.boosts["spa"] == 0
    assert mon.has_item()


def test_のどスプレー_とくこうランクが最大のとき発動しない():
    """のどスプレー: すでにとくこうランクが最大まで上がっているときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("プリン", item_name="のどスプレー", move_names=["ハイパーボイス"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.boosts["spa"] = 6
    t.run_move(battle, 0)
    assert mon.boosts["spa"] == 6
    assert mon.has_item()


def test_のどスプレー_技が外れたときは発動しない():
    """のどスプレー: 音技が外れたときは発動・消費しない"""
    battle = t.start_battle(
        team0=[Pokemon("プリン", item_name="のどスプレー", move_names=["ハイパーボイス"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=0,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.boosts["spa"] == 0
    assert mon.has_item()


def test_のどスプレー_非音技では発動しない():
    """のどスプレー: 音技以外では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("プリン", item_name="のどスプレー", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.boosts["spa"] == 0
    assert mon.has_item()


def test_のどスプレー_音技使用後にC上昇():
    """のどスプレー: 音技使用後にとくこう+1"""
    battle = t.start_battle(
        team0=[Pokemon("プリン", item_name="のどスプレー", move_names=["ハイパーボイス"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    assert mon.boosts["spa"] == 1
    assert not mon.has_item()


def test_ノーマルジュエル_なげつけるが失敗しアイテムを消費しない():
    """ノーマルジュエル: なげつけるを使用しても失敗し、アイテムを消費しない（投げられないアイテム）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ノーマルジュエル", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert mon.has_item()


def test_ノーマルジュエル_ノーマル技威力1_3倍():
    """ノーマルジュエル: ノーマル技の威力を1.3倍（5325/4096倍）にする（消費）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ノーマルジュエル", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 5325
    assert not mon.has_item()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
