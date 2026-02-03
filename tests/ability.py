from jpoke import Pokemon
import test_utils as t


def test_neutral_ability_switch():
    """ニュートラル: 交代可能"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ") for _ in range(2)]
    )
    assert t.can_switch(battle, 1), "ニュートラル: 交代失敗"


def test_trap_ability_prevents_switch():
    """ありじごく: 交代防止"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ありじごく")],
        foe=[Pokemon("ピカチュウ") for _ in range(2)]
    )
    assert not t.can_switch(battle, 1), "ありじごく: 交代防止失敗"


def test_trap_ability_flying_type_immune():
    """ありじごく: 飛行タイプに無効"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ありじごく")],
        foe=[Pokemon("リザードン") for _ in range(2)]
    )
    assert t.can_switch(battle, 1), "ありじごく: 飛行タイプ無効失敗"


def test_trap_ability_ghost_type_immune():
    """ありじごく: ゴーストタイプに無効"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ありじごく")],
        foe=[Pokemon("ゲンガー") for _ in range(2)]
    )
    assert t.can_switch(battle, 1), "ありじごく: ゴーストタイプ無効失敗"


def test_shadow_tag_prevents_switch():
    """かげふみ: 交代防止"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かげふみ")],
        foe=[Pokemon("ピカチュウ") for _ in range(2)]
    )
    assert not t.can_switch(battle, 1), "かげふみ: 交代防止失敗"


def test_shadow_tag_vs_shadow_tag_ineffective():
    """かげふみ: かげふみ相手には無効"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かげふみ")],
        foe=[Pokemon("ピカチュウ", ability="かげふみ") for _ in range(2)]
    )
    assert t.can_switch(battle, 1), "かげふみ: かげふみ相手無効失敗"


def test_magnet_pull_prevents_switch():
    """じりょく: 交代防止"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="じりょく")],
        foe=[Pokemon("ハッサム") for _ in range(2)]
    )
    assert not t.can_switch(battle, 1), "じりょく: 交代防止失敗"


def test_magnet_pull_non_steel_type_immune():
    """じりょく: はがねタイプ以外に無効"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="じりょく")],
        foe=[Pokemon("ピカチュウ") for _ in range(2)]
    )
    assert t.can_switch(battle, 1), "じりょく: はがねタイプ以外無効失敗"


def test_intimidate_attack_reduction():
    """いかく: 攻撃低下"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="いかく")]
    )
    assert battle.actives[0].ability.revealed, "いかく: 特性発動失敗"
    assert battle.actives[1].rank["A"] == -1, "いかく: 攻撃低下失敗"


def test_moxie_stat_boost():
    """かちき: 能力上昇"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かちき")]
    )
    battle.modify_stat(battle.actives[0], "S", -1, source=battle.actives[1])
    assert battle.actives[0].ability.revealed, "かちき: 特性発動失敗"
    assert battle.actives[0].rank["C"] == 2, "かちき: 能力上昇失敗"


def test_moxie_self_stat_change_no_effect():
    """かちき: 自分の能力ダウンでは発動しない"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かちき")]
    )
    battle.modify_stat(battle.actives[0], "A", -1, source=battle.actives[0])
    assert not battle.actives[0].ability.revealed, "かちき: 自分のダウンで発動してはいけない"


def test_moxie_vs_intimidate():
    """かちき: 相手のいかくで発動"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="かちき")],
        foe=[Pokemon("ピカチュウ", ability="いかく")]
    )
    assert battle.actives[0].ability.revealed, "かちき: いかくで発動失敗"


def test_aroma_veil_nervous():
    """きんちょうかん: 緊張状態"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="きんちょうかん")]
    )
    assert battle.actives[0].ability.revealed, "きんちょうかん: 特性発動失敗"
    assert battle.actives[1].is_nervous(battle.events), "きんちょうかん: 緊張失敗"
    assert not battle.actives[0].is_nervous(battle.events), "きんちょうかん: 自分も緊張してはいけない"


def test_grass_surge_sets_terrain():
    """グラスメイカー: 地形設定"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="グラスメイカー")]
    )
    assert battle.actives[0].ability.revealed, "グラスメイカー: 特性発動失敗"
    assert battle.terrain == "グラスフィールド", "グラスメイカー: 地形設定失敗"
    assert battle.terrain.count == 5, "グラスメイカー: 地形ターン数失敗"


def test_insomnia_prevents_sleep():
    """ぜったいねむり: ねむり状態を防止"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", ability="ぜったいねむり")]
    )
    assert battle.actives[0].ability.revealed, "ぜったいねむり: 特性発動失敗"
    assert battle.actives[0].ailment == "ねむり", "ぜったいねむり: ねむり適用失敗"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
