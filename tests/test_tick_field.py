"""フィールド効果のカウントダウンをテストする。

tick_fields関数を使用して、各種フィールド効果のカウント減少が
正しく動作することを確認します。
"""
import pytest

from jpoke.utils.type_defs import Weather, Terrain, GlobalField, SideField
from jpoke.enums import Event
from jpoke.model import Pokemon
from test_utils import start_battle


@pytest.mark.parametrize("field", ["はれ", "あめ", "すなあらし", "ゆき"])
def test_天候カウント減少(field: Weather):
    """カウントダウンテスト"""
    event = Event.ON_TURN_END_1
    initial_duration = 2
    battle = start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")], weather=(field, initial_duration))
    field = battle.raw_weather
    # 初期カウント確認
    assert field.count == initial_duration
    # カウントダウン確認
    battle.events.emit(event)
    assert field.count == initial_duration - 1, f"{field.name} count is incorrect"
    # カウントダウン確認
    battle.events.emit(event)
    assert field.count == initial_duration - 2, f"{field.name} count is incorrect"
    assert not field.is_active, f"{field.name} should be inactive"


@pytest.mark.parametrize("field", ["エレキフィールド", "グラスフィールド", "サイコフィールド", "ミストフィールド"])
def test_地形カウント減少(field: Terrain):
    """カウントダウンテスト"""
    event = Event.ON_TURN_END_4
    initial_duration = 2
    battle = start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")], terrain=(field, initial_duration))
    field = battle.terrain
    # 初期カウント確認
    assert field.count == initial_duration
    # カウントダウン確認
    battle.events.emit(event)
    assert field.count == initial_duration - 1, f"{field.name} count is incorrect"
    # カウントダウン確認
    battle.events.emit(event)
    assert field.count == initial_duration - 2, f"{field.name} count is incorrect"
    assert not field.is_active, f"{field.name} should be inactive"


@pytest.mark.parametrize("field", ["じゅうりょく", "トリックルーム", "マジックルーム", "ワンダールーム"])
def test_全体フィールドカウント減少(field: GlobalField):
    """カウントダウンテスト"""
    event = Event.ON_TURN_END_4
    initial_duration = 2
    battle = start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")], global_field={field: initial_duration})
    field = battle.get_global_field(field)
    # 初期カウント確認
    assert field.count == initial_duration
    # カウントダウン確認
    battle.events.emit(event)
    assert field.count == initial_duration - 1, f"{field.name} count is incorrect"
    # カウントダウン確認
    battle.events.emit(event)
    assert field.count == initial_duration - 2, f"{field.name} count is incorrect"
    assert not field.is_active, f"{field.name} should be inactive"


@pytest.mark.parametrize("field", [
    "リフレクター", "ひかりのかべ", "オーロラベール", "しんぴのまもり", "しろいきり", "おいかぜ"
])
def test_サイドフィールドカウント減少(field: SideField):
    """カウントダウンテスト"""
    event = Event.ON_TURN_END_4
    initial_duration = 2
    battle = start_battle(foe=[Pokemon("ピカチュウ")], ally=[Pokemon("ピカチュウ")],
                          ally_side_field={field: initial_duration},
                          foe_side_field={field: initial_duration},
                          )
    fields = [
        battle.get_side_field(player, field) for player in battle.players
    ]
    # 初期カウント確認
    assert all(f.count == initial_duration for f in fields)
    # カウントダウン確認
    battle.events.emit(event)
    assert all(f.count == initial_duration - 1 for f in fields)
    # カウントダウン確認
    battle.events.emit(event)
    assert all(f.count == initial_duration - 2 for f in fields)
    assert all(not f.is_active for f in fields)


if __name__ == "__main__":
    pytest.main([__file__])
