"""かがくへんかガス: 特性無効化のパラメタライズテスト"""
from __future__ import annotations

import pytest

from jpoke import Pokemon

from .. import test_utils as t

# ガス非適用（gas_proof）の特性 → enabled=True
# ガスで無効化される特性 → enabled=False
# spec/ability_list.md の「ガス非適用」列を参照


@pytest.mark.parametrize("ability_name, expected_enabled", [
    # ガス非適用（かがくへんかガスで無効化されない）
    ("ARシステム",       True),
    ("アイスフェイス",   True),
    ("うのミサイル",     True),
    ("かがくへんかガス", True),
    ("ぎょぐん",         True),
    ("じんばいったい",   True),
    ("スワームチェンジ", True),
    ("ぜったいねむり",   True),
    ("ダルマモード",     True),
    ("テラスチェンジ",   True),
    ("ばけのかわ",       True),
    ("バトルスイッチ",   True),
    ("マイティチェンジ", True),
    ("マルチタイプ",     True),
    ("リミットシールド", True),
    # ガスで無効化される特性
    ("アイスボディ",   False),
    ("いかく",         False),
    ("かたやぶり",     False),
    ("すなおこし",     False),
    ("てんねん",       False),
    ("マジックガード", False),
])
def test_かがくへんかガス_特性無効化(ability_name: str, expected_enabled: bool):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
    )
    assert battle.actives[0].ability.enabled == expected_enabled


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
