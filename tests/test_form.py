"""Pokemon.set_form()（フォルムチェンジ）のテスト"""
import pytest

from jpoke import Pokemon


def test_set_form_hp_policyでresetを指定すると被ダメージ状態でも満タンになる():
    mon = Pokemon("ジガルデ(50%)")
    mon.hp = mon.max_hp - 10  # このテストに限り直接代入で被ダメージ状態を作る

    mon.set_form("ジガルデ(10%)", hp_policy="reset")

    assert mon.hp == mon.max_hp


def test_set_form_keep_absoluteが既定で被ダメージ絶対量が維持される():
    """既定のhp_policy="keep_absolute"では、最大HPが変化するフォルム変化でも
    被ダメージの絶対量（max_hp - hp）が維持される。"""
    mon = Pokemon("ジガルデ(50%)")
    mon.hp = mon.max_hp - 10  # このテストに限り直接代入で被ダメージ状態を作る
    max_hp_before = mon.max_hp

    mon.set_form("ジガルデ(10%)")  # HP種族値が108→54に大きく減少するフォルム

    assert mon.max_hp != max_hp_before
    assert mon.max_hp - mon.hp == 10


def test_set_form_set_default_abilityにTrueを指定すると変更先の先頭特性にリセットされる():
    mon = Pokemon("ジガルデ(50%)", ability_name="オーラブレイク")

    mon.set_form("ジガルデ(パーフェクト)", set_default_ability=True)

    assert mon.ability.name == "スワームチェンジ"
    assert mon.base_ability == "スワームチェンジ"


def test_set_form_set_default_abilityを指定しない場合は特性が維持される():
    """set_default_abilityの既定はFalseで、フォルム変化前の特性がそのまま維持される
    （変更先の候補特性一覧に含まれるかどうかに関わらず変更されない）。"""
    mon = Pokemon("ジガルデ(50%)", ability_name="オーラブレイク")

    # ジガルデ(パーフェクト)の特性候補はスワームチェンジのみで、オーラブレイクは含まれない
    mon.set_form("ジガルデ(パーフェクト)")

    assert mon.ability.name == "オーラブレイク"
    assert mon.base_ability == "オーラブレイク"


def test_set_form_同じフォルムを指定すると何も変更されずFalseが返る():
    mon = Pokemon("ロトム")
    types_before = list(mon.types)
    stats_before = dict(mon.stats)

    result = mon.set_form("ロトム")

    assert result is False
    assert mon.name == "ロトム"
    assert mon.types == types_before
    assert mon.stats == stats_before


def test_set_form_異なるフォルムを指定すると種族値タイプが切り替わりTrueが返る():
    """set_formはエイリアス指定でフォルムを切り替え、種族値・タイプは変更先のものに
    差し替わる（ロトム→ヒートロトム: でんき/ゴースト → でんき/ほのお）。"""
    mon = Pokemon("ロトム")

    result = mon.set_form("ヒートロトム")

    assert result is True
    assert mon.name == "ヒートロトム"
    assert mon.types == ["でんき", "ほのお"]
    # ぼうぎょ種族値がロトム(60)からヒートロトム(107)に切り替わっている
    assert mon.stats["def"] > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
