"""フィールド効果のカウントダウンをテストする。

tick_fields関数を使用して、各種フィールド効果のカウント減少が
正しく動作することを確認します。
"""
from jpoke import Pokemon
from test_utils import start_battle, tick_fields, assert_field_active, get_field_count

# 定数定義
DEFAULT_DURATION = 999


def test_tick_weather():
    """天候のカウントダウンテスト"""
    battle = start_battle(ally=[Pokemon("ピカチュウ")], weather=("はれ", DEFAULT_DURATION))

    # 初期状態検証
    assert_field_active(battle, 'weather', 'はれ', active=True)
    assert get_field_count(battle, 'weather', 'はれ') == DEFAULT_DURATION

    # 5カウント経過
    tick_fields(battle, ticks=5)
    assert_field_active(battle, 'weather', 'はれ', active=True)
    assert get_field_count(battle, 'weather', 'はれ') == DEFAULT_DURATION - 5

    # 残りカウント経過させて0にする
    tick_fields(battle, ticks=DEFAULT_DURATION - 5)
    assert_field_active(battle, 'weather', 'はれ', active=False)
    print("✓ 天候のカウントダウンテスト成功")


def test_tick_terrain():
    """地形のカウントダウンテスト"""
    battle = start_battle(ally=[Pokemon("ピカチュウ")], terrain=("エレキフィールド", DEFAULT_DURATION))

    # 初期状態検証
    assert_field_active(battle, 'terrain', 'エレキフィールド', active=True)
    assert get_field_count(battle, 'terrain', 'エレキフィールド') == DEFAULT_DURATION

    # 10カウント経過
    tick_fields(battle, ticks=10)
    assert_field_active(battle, 'terrain', 'エレキフィールド', active=True)
    assert get_field_count(battle, 'terrain', 'エレキフィールド') == DEFAULT_DURATION - 10

    # 残りカウント経過させて0にする
    tick_fields(battle, ticks=DEFAULT_DURATION - 10)
    assert_field_active(battle, 'terrain', 'エレキフィールド', active=False)
    print("✓ 地形のカウントダウンテスト成功")


def test_tick_side_field():
    """サイドフィールドのカウントダウンテスト"""
    battle = start_battle(ally=[Pokemon("ピカチュウ")], ally_side_field={"まきびし": 3})

    # 初期状態検証
    makibishi = battle.side_mgrs[0].fields["まきびし"]
    assert_field_active(battle, 'ally_side', 'まきびし', active=True)
    assert get_field_count(battle, 'ally_side', 'まきびし') == DEFAULT_DURATION
    assert makibishi.layers == 3, f"まきびしのレイヤー数が不正: expected 3, got {makibishi.layers}"

    # 100カウント経過
    tick_fields(battle, ticks=100)
    assert_field_active(battle, 'ally_side', 'まきびし', active=True)
    assert get_field_count(battle, 'ally_side', 'まきびし') == DEFAULT_DURATION - 100
    assert makibishi.layers == 3, "カウントダウンでレイヤー数が変化した"

    # 残りカウント経過させて0にする
    tick_fields(battle, ticks=DEFAULT_DURATION - 100)
    assert_field_active(battle, 'ally_side', 'まきびし', active=False)
    print("✓ サイドフィールドのカウントダウンテスト成功")


def test_tick_global_field():
    """グローバルフィールドのカウントダウンテスト"""
    initial_count = 50
    battle = start_battle(ally=[Pokemon("ピカチュウ")], global_field={"トリックルーム": initial_count})

    # 初期状態検証
    assert_field_active(battle, 'global', 'トリックルーム', active=True)
    assert get_field_count(battle, 'global', 'トリックルーム') == initial_count

    # 30カウント経過
    tick_fields(battle, ticks=30)
    assert_field_active(battle, 'global', 'トリックルーム', active=True)
    assert get_field_count(battle, 'global', 'トリックルーム') == initial_count - 30

    # 残りカウント経過させて0にする
    tick_fields(battle, ticks=initial_count - 30)
    assert_field_active(battle, 'global', 'トリックルーム', active=False)
    print("✓ グローバルフィールドのカウントダウンテスト成功")


def test_tick_multiple_fields():
    """複数フィールドの同時カウントダウンテスト"""
    battle = start_battle(
        ally=[Pokemon("ピカチュウ")],
        weather=("あめ", DEFAULT_DURATION),
        terrain=("グラスフィールド", DEFAULT_DURATION),
        ally_side_field={"ステルスロック": 1},
        foe_side_field={"どくびし": 2},
        global_field={"トリックルーム": 100}
    )

    # 初期カウント確認
    assert get_field_count(battle, 'weather', 'あめ') == DEFAULT_DURATION
    assert get_field_count(battle, 'terrain', 'グラスフィールド') == DEFAULT_DURATION
    assert get_field_count(battle, 'ally_side', 'ステルスロック') == DEFAULT_DURATION
    assert get_field_count(battle, 'foe_side', 'どくびし') == DEFAULT_DURATION
    assert get_field_count(battle, 'global', 'トリックルーム') == 100

    # 50カウント一括経過
    tick_fields(battle, ticks=50)

    # すべて減っている
    assert get_field_count(battle, 'weather', 'あめ') == DEFAULT_DURATION - 50
    assert get_field_count(battle, 'terrain', 'グラスフィールド') == DEFAULT_DURATION - 50
    assert get_field_count(battle, 'ally_side', 'ステルスロック') == DEFAULT_DURATION - 50
    assert get_field_count(battle, 'foe_side', 'どくびし') == DEFAULT_DURATION - 50
    assert get_field_count(battle, 'global', 'トリックルーム') == 50

    # さらに50カウント経過
    tick_fields(battle, ticks=50)

    # トリックルームだけ消える
    assert_field_active(battle, 'weather', 'あめ', active=True)
    assert_field_active(battle, 'terrain', 'グラスフィールド', active=True)
    assert_field_active(battle, 'ally_side', 'ステルスロック', active=True)
    assert_field_active(battle, 'foe_side', 'どくびし', active=True)
    assert_field_active(battle, 'global', 'トリックルーム', active=False)

    print("✓ 複数フィールド同時カウントダウンテスト成功")


if __name__ == "__main__":
    test_tick_weather()
    test_tick_terrain()
    test_tick_side_field()
    test_tick_global_field()
    test_tick_multiple_fields()
    print("\n全テスト成功！")
