"""状態異常を防ぐ特性のテスト"""
import test_utils as t
from jpoke.model import Pokemon


def test_めんえき():
    """めんえき特性でどく・もうどくを防ぐ"""
    battle = t.start_battle(
        ally=[Pokemon("ゴクリン", ability="めんえき")],
        foe=[Pokemon("ピカチュウ")]
    )
    mon = battle.actives[0]

    # デバッグ: 特性を確認
    print(f"特性: {mon.ability.name}")
    print(f"ハンドラー数: {len(mon.ability.data.handlers)}")

    # どく状態にしようとする
    print("どく付与を試行...")
    result = mon.apply_ailment(battle.events, "どく")
    print(f"どく付与結果: result={result}, ailment={mon.ailment.name}, is_active={mon.ailment.is_active}")
    assert not result, "めんえきでどくを防げなかった"
    assert not mon.ailment.is_active, "どく状態が付与されてしまった"

    # もうどく状態にしようとする
    result = mon.apply_ailment(battle.events, "もうどく")
    assert not result, "めんえきでもうどくを防げなかった"
    assert not mon.ailment.is_active, "もうどく状態が付与されてしまった"

    # 他の状態異常は通る
    print(f"まひ付与前: ailment={mon.ailment.name}, is_active={mon.ailment.is_active}")
    result = mon.apply_ailment(battle.events, "まひ")
    print(f"まひ付与後: result={result}, ailment={mon.ailment.name}, is_active={mon.ailment.is_active}")
    assert result, "めんえきでまひが防がれてしまった"
    assert mon.ailment.name == "まひ", "まひ状態が付与されなかった"
    print("✓ めんえき: どく・もうどくを防ぐことを確認")


def test_ふみん():
    """ふみん特性でねむりを防ぐ"""
    battle = t.start_battle(
        ally=[Pokemon("カビゴン", ability="ふみん")],
        foe=[Pokemon("ピカチュウ")]
    )
    mon = battle.actives[0]

    # ねむり状態にしようとする
    result = mon.apply_ailment(battle.events, "ねむり")
    assert not result, "ふみんでねむりを防げなかった"
    assert not mon.ailment.is_active, "ねむり状態が付与されてしまった"

    # 他の状態異常は通る
    result = mon.apply_ailment(battle.events, "まひ")
    assert result, "ふみんでまひが防がれてしまった"
    assert mon.ailment.name == "まひ", "まひ状態が付与されなかった"
    print("✓ ふみん: ねむりを防ぐことを確認")


def test_やるき():
    """やるき特性でねむりを防ぐ"""
    battle = t.start_battle(
        ally=[Pokemon("デリバード", ability="やるき")],
        foe=[Pokemon("ピカチュウ")]
    )
    mon = battle.actives[0]

    # ねむり状態にしようとする
    result = mon.apply_ailment(battle.events, "ねむり")
    assert not result, "やるきでねむりを防げなかった"
    assert not mon.ailment.is_active, "ねむり状態が付与されてしまった"
    print("✓ やるき: ねむりを防ぐことを確認")


def test_じゅうなん():
    """じゅうなん特性でまひを防ぐ"""
    battle = t.start_battle(
        ally=[Pokemon("マダツボミ", ability="じゅうなん")],
        foe=[Pokemon("ピカチュウ")]
    )
    mon = battle.actives[0]

    # まひ状態にしようとする
    result = mon.apply_ailment(battle.events, "まひ")
    assert not result, "じゅうなんでまひを防げなかった"
    assert not mon.ailment.is_active, "まひ状態が付与されてしまった"

    # 他の状態異常は通る
    result = mon.apply_ailment(battle.events, "どく")
    assert result, "じゅうなんでどくが防がれてしまった"
    assert mon.ailment.name == "どく", "どく状態が付与されなかった"
    print("✓ じゅうなん: まひを防ぐことを確認")


def test_みずのベール():
    """みずのベール特性でやけどを防ぐ"""
    battle = t.start_battle(
        ally=[Pokemon("ギャラドス", ability="みずのベール")],
        foe=[Pokemon("ピカチュウ")]
    )
    mon = battle.actives[0]

    # やけど状態にしようとする
    result = mon.apply_ailment(battle.events, "やけど")
    assert not result, "みずのベールでやけどを防げなかった"
    assert not mon.ailment.is_active, "やけど状態が付与されてしまった"

    # 他の状態異常は通る
    result = mon.apply_ailment(battle.events, "まひ")
    assert result, "みずのベールでまひが防がれてしまった"
    assert mon.ailment.name == "まひ", "まひ状態が付与されなかった"
    print("✓ みずのベール: やけどを防ぐことを確認")


def test_マグマのよろい():
    """マグマのよろい特性でこおりを防ぐ"""
    battle = t.start_battle(
        ally=[Pokemon("マグカルゴ", ability="マグマのよろい")],
        foe=[Pokemon("ピカチュウ")]
    )
    mon = battle.actives[0]

    # こおり状態にしようとする
    result = mon.apply_ailment(battle.events, "こおり")
    assert not result, "マグマのよろいでこおりを防げなかった"
    assert not mon.ailment.is_active, "こおり状態が付与されてしまった"

    # 他の状態異常は通る
    result = mon.apply_ailment(battle.events, "まひ")
    assert result, "マグマのよろいでまひが防がれてしまった"
    assert mon.ailment.name == "まひ", "まひ状態が付与されなかった"
    print("✓ マグマのよろい: こおりを防ぐことを確認")


if __name__ == "__main__":
    test_めんえき()
    test_ふみん()
    test_やるき()
    test_じゅうなん()
    test_みずのベール()
    test_マグマのよろい()
    print("\n✅ すべてのテストが成功しました！")
