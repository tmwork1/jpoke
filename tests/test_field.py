"""フィールド効果ハンドラの単体テスト（天候・地形・サイドフィールド・グローバルフィールド）"""
import pytest
from jpoke import Battle, Pokemon
from jpoke.types import WeatherName, TerrainName, GlobalFieldName, SideFieldName
from jpoke.core import AttackContext
from . import test_utils as t


@pytest.mark.parametrize("weather,pokemon_name,move_name,expected", [
    ("あめ", "ゼニガメ", "みずでっぽう", 4096),
    ("あめ", "ヒトカゲ", "ひのこ", 4096),
    ("はれ", "ヒトカゲ", "ひのこ", 4096),
    ("はれ", "ゼニガメ", "みずでっぽう", 4096),
])
def test_あめはれ_ばんのうがさ防御側は補正なし(weather: WeatherName, pokemon_name: str, move_name: str, expected: int):
    """あめ/はれ: 防御側がばんのうがさを持つ場合は威力補正を受けない"""
    battle = t.start_battle(
        team0=[Pokemon(pokemon_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", item_name="ばんのうがさ")],
        weather=(weather, 99),
    )
    t.run_move(battle, 0)
    assert expected == battle.damage_calculator.power_modifier


def test_いやしのねがい_HP減少ポケモンの交代で全回復しフィールドが解除される():
    """いやしのねがい: 場に出たポケモンのHPが減っている（状態異常なし）場合、HP が全回復してフィールドが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
        side0={"いやしのねがい": 1},
    )
    bench = battle.player_states[battle.players[0]].team[1]
    bench.hp = 1
    assert not bench.ailment.is_active

    active = t.run_switch(battle, 0, 1)

    assert active is bench
    assert active.hp == active.max_hp
    assert not battle.get_side(active).get("いやしのねがい").is_active


def test_エレキフィールド_ねむけ防止():
    """エレキフィールド: 接地ポケモンへのねむけは無効"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        terrain=("エレキフィールド", 99),
    )
    target = battle.actives[0]
    assert not battle.volatile_manager.apply(target, "ねむけ", count=2)
    assert not target.has_volatile("ねむけ")


def test_エレキフィールド_ねむり防止():
    """エレキフィールド: 接地ポケモンへのねむりは無効"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        terrain=("エレキフィールド", 99),
    )
    target = battle.actives[0]
    result = battle.ailment_manager.apply(target, "ねむり")
    assert not result, "エレキフィールド下でねむりが付与された"
    assert not target.ailment.is_active, "エレキフィールド下でねむり状態が付与された"


def test_エレキフィールド_ねむる失敗():
    """エレキフィールド: 接地ポケモンのねむるは失敗しHPも回復しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        terrain=("エレキフィールド", 99),
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    hp_before = mon.hp
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False, "ねむるが失敗しなかった"
    assert mon.hp == hp_before, "ねむる失敗なのにHPが回復した"
    assert not mon.ailment.is_active, "ねむる失敗なのにねむり状態になった"


def test_エレキフィールド_非接地はねむけ防止されない():
    """エレキフィールド: 浮遊ポケモンへのねむけは防止されない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピジョン")],
        terrain=("エレキフィールド", 99),
    )
    target = battle.actives[0]
    assert battle.volatile_manager.apply(target, "ねむけ", count=2)
    assert target.has_volatile("ねむけ")


def test_エレキフィールド_非接地はねむり防止されない():
    """エレキフィールド: 浮遊ポケモンへのねむりは防止されない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピジョン")],
        terrain=("エレキフィールド", 99),
    )
    target = battle.actives[0]
    assert battle.ailment_manager.apply(target, "ねむり")
    assert target.ailment.is_active


def test_エレキフィールド_非接地はねむる使用可能():
    """エレキフィールド: 浮遊ポケモンのねむるは失敗しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピジョン", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        terrain=("エレキフィールド", 99),
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True, "浮遊ポケモンのねむるが失敗した"
    assert mon.hp == mon.max_hp, "浮遊ポケモンのねむるでHPが回復しなかった"
    assert mon.ailment.name == "ねむり", "浮遊ポケモンのねむるでねむり状態にならなかった"


def test_おいかぜ():
    """おいかぜ: 実効すばやさ2倍"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        side0={"おいかぜ": 1},
    )
    mon = battle.actives[0]
    assert battle.speed_calculator.calc_effective_speed(mon) == 2 * mon.stats["spe"]


def test_おいかぜ_相手サイドには補正なし():
    """おいかぜ: 自陣営のみ効果を受け、相手のすばやさは変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        side0={"おいかぜ": 1},
    )
    own = battle.actives[0]
    foe = battle.actives[1]
    # 自分は2倍
    assert battle.speed_calculator.calc_effective_speed(own) == 2 * own.stats["spe"]
    # 相手は補正なし
    assert battle.speed_calculator.calc_effective_speed(foe) == foe.stats["spe"]


def test_おおあめ_こおりが付与される():
    """おおあめ: こおり防止効果はなく、こおり状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        weather=("おおあめ", 99),
    )
    target = battle.actives[0]
    result = battle.ailment_manager.apply(target, "こおり")
    assert result, "おおあめ中にこおりが付与されなかった"
    assert target.ailment.name == "こおり", "おおあめ中にこおり状態にならなかった"


def test_オーロラベール_ひかりのかべとは重複しない():
    """オーロラベール: ひかりのかべが有効でも特殊技ダメージ軽減は重複しない（1/2 のまま）"""
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", move_names=["みずでっぽう"])],
        team1=[Pokemon("ピカチュウ")],
        side1={"オーロラベール": 5, "ひかりのかべ": 5},
    )
    t.run_move(battle, 0)
    # どちらか一方の壁だけが適用され、damage_modifier は 2048（1/2）のまま
    assert battle.damage_calculator.damage_modifier == 2048


def test_オーロラベール_リフレクターとは重複しない():
    """オーロラベール: リフレクターが有効でも物理技ダメージ軽減は重複しない（1/2 のまま）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        side1={"オーロラベール": 5, "リフレクター": 5},
    )
    t.run_move(battle, 0)
    # リフレクターが適用済みのため オーロラベール の追加軽減はなし（2048 のまま）
    assert battle.damage_calculator.damage_modifier == 2048


def test_グラスフィールド_かいふくふうじで回復しない():
    """グラスフィールド: かいふくふうじ状態のポケモンはターン終了時に回復しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("グラスフィールド", 99),
        volatile0={"かいふくふうじ": 3},
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1, "かいふくふうじ状態でグラスフィールドの回復が発生した"


def test_グラスフィールド_じしん弱化():
    """グラスフィールド: じしん威力0.5倍"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("サンドパン", move_names=["じしん"])],
        terrain=("グラスフィールド", 99),
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.power_modifier


def test_グラスフィールド_じならし弱化():
    """グラスフィールド: じならし威力0.5倍"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("サンドパン", move_names=["じならし"])],
        terrain=("グラスフィールド", 99),
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.power_modifier


def test_グラスフィールド_回復():
    """グラスフィールド: 接地ポケモンはターン終了時1/16回復"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("グラスフィールド", 99),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1 + mon.max_hp // 16, "グラスフィールドの回復量が不正"


def test_グラスフィールド_非接地は回復しない():
    """グラスフィールド: 浮遊ポケモンはターン終了時に回復しない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピジョン")],
        terrain=("グラスフィールド", 99),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_サイコフィールド_優先度0技は有効():
    """サイコフィールド: 優先度0の技は接地ポケモンにも有効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        terrain=("サイコフィールド", 99),
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True


def test_サイコフィールド_先制技無効():
    """サイコフィールド: 接地ポケモンへの先制技無効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ")],
        terrain=("サイコフィールド", 99),
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False


def test_サイコフィールド_浮遊は先制技有効():
    """サイコフィールド: 浮遊相手には先制技が有効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("ピジョン")],
        terrain=("サイコフィールド", 99),
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True


@pytest.mark.parametrize("side_field,move_name,expected", [
    ("リフレクター", "たいあたり", 2048),
    ("リフレクター", "でんきショック", 4096),
    ("ひかりのかべ", "でんきショック", 2048),
    ("ひかりのかべ", "たいあたり", 4096),
    ("オーロラベール", "たいあたり", 2048),
    ("オーロラベール", "でんきショック", 2048),
])
def test_サイドフィールド_ダメージ軽減(side_field: SideFieldName, move_name: str, expected: int):
    """リフレクター/ひかりのかべ/オーロラベール: ダメージ軽減"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        side1={side_field: 5},
    )
    t.run_move(battle, 0)
    assert expected == battle.damage_calculator.damage_modifier


@pytest.mark.parametrize("side_field,move_name", [
    ("リフレクター", "たいあたり"),
    ("ひかりのかべ", "でんきショック"),
    ("オーロラベール", "たいあたり"),
])
def test_サイドフィールド_急所では軽減されない(side_field: SideFieldName, move_name: str):
    """リフレクター/ひかりのかべ/オーロラベール: 急所では軽減されない（damage_modifier が等倍）"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        side1={side_field: 5},
        accuracy=100,
    )
    # 乱数を 0.0 に固定して急所を確実に発生させる
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    # 急所のときはスクリーンが無視されるため damage_modifier が 4096（等倍）
    assert battle.move_executor.critical is True
    assert battle.damage_calculator.damage_modifier == 4096


@pytest.mark.parametrize(
    "field",
    ["リフレクター", "ひかりのかべ", "オーロラベール", "しんぴのまもり", "しろいきり", "おいかぜ"]
)
def test_サイドフィールドカウント減少(field: SideFieldName):
    """カウントダウンテスト"""
    initial_duration = 2
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        side0={field: initial_duration},
        side1={field: initial_duration},
    )
    fields = [battle.get_side(ply).get(field) for ply in battle.players]
    # 初期カウント確認
    assert all(f.count == initial_duration for f in fields)
    # カウントダウン確認
    t.end_turn(battle)
    assert all(f.count == initial_duration - 1 for f in fields)
    # カウントダウン確認
    t.end_turn(battle)
    assert all(f.count == initial_duration - 2 for f in fields)
    assert all(not f.is_active for f in fields)


def test_しろいきり_すりぬけは能力低下防止を貫通する():
    """しろいきり: すりぬけ特性を持つポケモンによる能力低下は防げない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すりぬけ")],
        team1=[Pokemon("ピカチュウ")],
        side1={"しろいきり": 1},
    )
    source = battle.actives[0]
    target = battle.actives[1]
    assert battle.modify_stats(target, {"atk": -1}, source=source)
    assert target.rank["atk"] == -1


def test_しろいきり_能力低下防止():
    """しろいきり: 能力ランク低下を防ぐ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        side0={"しろいきり": 1},
    )
    target, source = battle.actives
    assert not battle.modify_stats(target, {"atk": -1}, source=source)


def test_しろいきり_自発的な能力低下は防げない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        side0={"しろいきり": 1},
    )
    target = battle.actives[0]
    assert battle.modify_stats(target, {"atk": -1}, source=target)
    assert target.rank["atk"] == -1


def test_しんぴのまもり_ねむけ防止():
    """しんぴのまもり: ねむけ付与を防ぐ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        side0={"しんぴのまもり": 1},
    )
    target, source = battle.actives
    assert not battle.volatile_manager.apply(target, "ねむけ", source=source)
    assert not target.has_volatile("ねむけ")


def test_しんぴのまもり_ねむるは防がない():
    """しんぴのまもり: 自分が使うねむるによるねむり付与は防がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        side0={"しんぴのまもり": 5},
    )
    mon = battle.actives[0]
    # HPを減らしてねむるの失敗条件（HP満タン）を回避
    battle.modify_hp(mon, r=-0.5)
    assert battle.ailment_manager.apply(mon, "ねむり", count=3, source=mon)
    assert mon.has_ailment("ねむり")


def test_しんぴのまもり_混乱防止():
    """しんぴのまもり: 混乱付与を防ぐ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        side0={"しんぴのまもり": 1},
    )
    target = battle.actives[0]
    assert not battle.volatile_manager.apply(target, "こんらん", count=3)
    assert not target.has_volatile("こんらん")


def test_しんぴのまもり_状態異常防止():
    """しんぴのまもり: 状態異常付与を防ぐ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        side0={"しんぴのまもり": 1},
    )
    target = battle.actives[0]
    assert not battle.ailment_manager.apply(target, "どく")
    assert not target.ailment.is_active


def test_じゅうりょく_Gのちから強化():
    """じゅうりょく: Gのちからの威力が1.5倍（6144/4096）になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["Gのちから"])],
        team1=[Pokemon("ピカチュウ")],
        field={"じゅうりょく": 99},
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144


@pytest.mark.parametrize("move_name", [
    "そらをとぶ",
    "でんじふゆう",
    "とびげり",
    "とびはねる",
    "とびひざげり",
    "はねる",
    "フライングプレス",
])
def test_じゅうりょく_使用禁止技ブロック(move_name: str):
    """じゅうりょく: gravity_restrictedフラグを持つ全7技はじゅうりょく中に失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        field={"じゅうりょく": 99},
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


def test_じゅうりょく_命中補正():
    """じゅうりょく: 命中率が6840/4096倍になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんじほう"])],
        team1=[Pokemon("ピカチュウ")],
        field={"じゅうりょく": 99}
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy * 6840 // 4096


def test_じゅうりょく_浮遊無効():
    """じゅうりょく: ひこうタイプポケモンが接地状態になる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピジョン")],
        field={"じゅうりょく": 99},
    )
    assert not battle.query.is_floating(battle.actives[0])


def test_じゅうりょく_発動時にそらをとぶ解除():
    """じゅうりょく: 発動時にそらをとぶ揮発性状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["そらをとぶ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "そらをとぶ")
    assert mon.has_volatile("そらをとぶ")
    battle.global_manager.activate("じゅうりょく", 5)
    assert not mon.has_volatile("そらをとぶ")


def test_じゅうりょく_発動時にでんじふゆう解除():
    """じゅうりょく: 発動時にでんじふゆう揮発性状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "でんじふゆう")
    assert mon.has_volatile("でんじふゆう")
    battle.global_manager.activate("じゅうりょく", 5)
    assert not mon.has_volatile("でんじふゆう")


def test_ステルスロック_x1():
    """ステルスロック: 1倍ダメージ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        side0={"ステルスロック": 1},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.hp == active.max_hp - active.max_hp // 8


def test_ステルスロック_x1_2():
    """ステルスロック: ×1/2耐性ポケモン（カイリキー）は最大HPの1/16ダメージ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カイリキー")],
        team1=[Pokemon("ピカチュウ")],
        side0={"ステルスロック": 1},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.max_hp - active.hp == max(1, active.max_hp // 16)


def test_ステルスロック_x1_4():
    """ステルスロック: ×1/4耐性ポケモン（ルカリオ）は最大HPの1/32ダメージ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ルカリオ")],
        team1=[Pokemon("ピカチュウ")],
        side0={"ステルスロック": 1},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.max_hp - active.hp == max(1, active.max_hp // 32)


def test_ステルスロック_x4():
    """ステルスロック: ×4弱点ポケモン（リザードン）は最大HPの1/2ダメージ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("リザードン")],
        side0={"ステルスロック": 1},
    )
    active = t.run_switch(battle, 0, 1)
    actual_damage = active.max_hp - active.hp
    assert actual_damage == active.max_hp // 2


def test_ステルスロック_マジックガード無効():
    """ステルスロック: マジックガードを持つポケモンはダメージを受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
        side0={"ステルスロック": 1},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.hp == active.max_hp


def test_すなあらし_いわ特防強化():
    """すなあらし: いわタイプ特防1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スピードスター"])],
        team1=[Pokemon("イシツブテ")],
        weather=("すなあらし", 99),
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.def_modifier


def test_すなあらし_エアロックでいわ特防強化が無効化される():
    """すなあらし: エアロックで天候効果が無効化されている間はいわ特防1.5倍が適用されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スピードスター"])],
        team1=[Pokemon("イシツブテ", ability_name="エアロック")],
        weather=("すなあらし", 99),
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_modifier


@pytest.mark.parametrize("pokemon_name", ["イシツブテ", "サンドパン", "コイル"])
def test_すなあらし_タイプ免疫(pokemon_name: str):
    """すなあらし: いわ・じめん・はがねタイプはダメージを受けない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon(pokemon_name)],
        weather=("すなあらし", 99),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


def test_すなあらし_ダメージ():
    """すなあらし: ターン終了時ダメージ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        weather=("すなあらし", 99)
    )
    t.end_turn(battle)
    actual_damages = [mon.max_hp - mon.hp for mon in battle.actives]
    expected_damages = [mon.max_hp // 16 for mon in battle.actives]
    assert actual_damages == expected_damages, "Incorrect sandstorm damage applied"


@pytest.mark.parametrize(
    "ability_name",
    ["すなかき", "すながくれ", "すなのちから", "ぼうじん"]
)
def test_すなあらし_特性免疫(ability_name: str):
    """特定の特性を持つポケモンはすなあらしのダメージを受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ")],
        weather=("すなあらし", 999),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


def test_トリックルーム_再使用で解除():
    """トリックルーム: 発動中に再度使用するとフィールドが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", move_names=["トリックルーム"])],
        team1=[Pokemon("ピカチュウ")],
        field={"トリックルーム": 5},
    )
    field = battle.global_manager.fields["トリックルーム"]
    assert field.is_active
    t.run_move(battle, 0)
    assert not field.is_active


def test_トリックルーム_技優先度が優先():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        field={"トリックルーム": 5},
    )

    action_order = t.get_action_order(battle)
    assert action_order[0] == battle.actives[1]


def test_トリックルーム_素早さ逆順():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        field={"トリックルーム": 5},
    )

    action_order = t.get_action_order(battle)
    assert action_order[0] == battle.actives[0]


def test_どくびし_1層():
    """どくびし: 交代時どく状態付与（1層）"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        side0={"どくびし": 1},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.ailment.name == "どく", "Poison status not applied"


def test_どくびし_2層():
    """どくびし: 2層でもうどく状態付与"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        side0={"どくびし": 2},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.ailment.name == "もうどく", "Badly poison status not applied"


def test_どくびし_どくタイプが着地すると解除される():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("フシギダネ")],
        side0={"どくびし": 2},
    )
    active = t.run_switch(battle, 0, 1)
    field = battle.get_side(battle.players[0]).get("どくびし")
    assert not field.is_active
    assert field.count == 0
    assert not active.ailment.is_active


def test_どくびし_どくタイプはあつぞこブーツでも解除する():
    """どくびし: どくタイプはあつぞこブーツを持っていてもどくびしを消滅させる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("フシギダネ", item_name="あつぞこブーツ")],
        side0={"どくびし": 2},
    )
    active = t.run_switch(battle, 0, 1)
    field = battle.get_side(battle.players[0]).get("どくびし")
    assert not field.is_active
    assert field.count == 0
    assert not active.ailment.is_active


def test_どくびし_はがねタイプには効かない():
    """どくびし: はがねタイプのポケモンは毒状態にならない（フィールドは消滅しない）"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ニャース(ガラル)")],
        side0={"どくびし": 2},
    )
    active = t.run_switch(battle, 0, 1)
    field = battle.get_side(battle.players[0]).get("どくびし")
    assert field.is_active
    assert not active.ailment.is_active


def test_どくびし_浮いているポケモンには効かない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ピジョン")],
        side0={"どくびし": 2},
    )
    active = t.run_switch(battle, 0, 1)
    assert not active.ailment.is_active


def test_ねがいごと_かいふくふうじ中は回復しない():
    """ねがいごと: かいふくふうじ状態のポケモンはねがいごとによる回復を受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        side0={"ねがいごと": 2},
        volatile0={"かいふくふうじ": 3},
    )
    field = battle.get_side(battle.players[0]).get("ねがいごと")
    mon = battle.actives[0]
    # HPを削ってから回復されないことを確認
    battle.modify_hp(mon, v=-(mon.hp - 1))
    hp_before = mon.hp
    field.heal = 20

    t.end_turn(battle)
    t.end_turn(battle)

    assert mon.hp == hp_before, "かいふくふうじ状態でねがいごとの回復が発生した"
    assert not field.is_active


def test_ねがいごと_交代後は現在の場のポケモンが回復する():
    """ねがいごと: 使用者が交代しても同ポジションの現在のポケモンが回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ヤドラン")],
        team1=[Pokemon("カビゴン")],
        side0={"ねがいごと": 2},
    )
    field = battle.get_side(battle.players[0]).get("ねがいごと")
    heal = 30
    field.heal = heal

    teammate = battle.player_states[battle.players[0]].team[1]

    # 交代先（ヤドラン）のHPを削っておく
    battle.modify_hp(teammate, v=-heal)
    hp_teammate_before = teammate.hp

    # 使用者を交代させる
    t.run_switch(battle, 0, 1)
    assert battle.actives[0] is teammate

    # ターン終了 × 2
    t.end_turn(battle)
    t.end_turn(battle)

    # 交代後のポケモン（ヤドラン）が回復していること
    assert teammate.hp == hp_teammate_before + heal
    assert not field.is_active


def test_ねがいごと_回復と解除():
    """ねがいごと: ターン終了時回復と解除"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        side0={"ねがいごと": 2},
    )
    field = battle.get_side(battle.players[0]).get("ねがいごと")

    # HPを減らして回復確認
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-(mon.hp - 1))

    heal = 20
    field.heal = heal

    t.end_turn(battle)
    assert mon.hp == 1, "No wish heal occurred"
    assert field.count == 1, "Wish field count did not decrease"

    t.end_turn(battle)
    assert mon.hp == 1 + heal, "Wish heal amount is incorrect"
    assert not field.is_active, "Wish field did not deactivate"


def test_ねばねばネット():
    """ねばねばネット: 交代時素早さ-1"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        side0={"ねばねばネット": 1},
    )
    before_rank = battle.players[0].team[1].rank["spe"]
    active = t.run_switch(battle, 0, 1)
    after_rank = active.rank["spe"]
    assert after_rank == before_rank - 1, "Speed rank not decreased"


def test_ねばねばネット_あつぞこブーツで無効():
    """ねばねばネット: あつぞこブーツを持つポケモンはすばやさが下がらない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", item_name="あつぞこブーツ")],
        side0={"ねばねばネット": 1},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.rank["spe"] == 0, "あつぞこブーツ持ちはねばねばネットの影響を受けない"


def test_ねばねばネット_あまのじゃくは1段階上がる():
    """ねばねばネット: あまのじゃく持ちのポケモンはすばやさが1段階上がる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", ability_name="あまのじゃく")],
        side0={"ねばねばネット": 1},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.rank["spe"] == 1, "あまのじゃく持ちはすばやさが上がる"


def test_ねばねばネット_たんじゅんは2段階下がる():
    """ねばねばネット: たんじゅん持ちのポケモンはすばやさが2段階下がる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", ability_name="たんじゅん")],
        side0={"ねばねばネット": 1},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.rank["spe"] == -2, "たんじゅん持ちはすばやさが2段階下がる"


def test_ねばねばネット_浮いているポケモンには効かない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ピジョン")],
        side0={"ねばねばネット": 1},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.rank["spe"] == 0


def test_はれ_こおり防止():
    """はれ: こおり状態の付与を防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 99),
    )
    target = battle.actives[0]
    result = battle.ailment_manager.apply(target, "こおり")
    assert not result, "はれ中にこおりが付与された"
    assert not target.ailment.is_active, "はれ中にこおり状態になった"


@pytest.mark.parametrize("weather,pokemon_name,move_name,expected", [
    ("はれ", "ヒトカゲ", "ひのこ", 6144),
    ("はれ", "ゼニガメ", "みずでっぽう", 2048),
    ("あめ", "ゼニガメ", "みずでっぽう", 6144),
    ("あめ", "ヒトカゲ", "ひのこ", 2048),
])
def test_はれあめ_タイプ威力補正(weather: WeatherName, pokemon_name: str, move_name: str, expected: int):
    """はれ/あめ: ほのお・みず技威力補正"""
    battle = t.start_battle(
        team0=[Pokemon(pokemon_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather, 99),
    )
    t.run_move(battle, 0)
    assert expected == battle.damage_calculator.power_modifier


@pytest.mark.parametrize("weather,pokemon_name,move_name", [
    ("はれ", "ヒトカゲ", "ひのこ"),
    ("はれ", "ゼニガメ", "みずでっぽう"),
    ("あめ", "ゼニガメ", "みずでっぽう"),
    ("あめ", "ヒトカゲ", "ひのこ"),
])
def test_はれあめ_ばんのうがさ防御側は威力補正無効(weather: WeatherName, pokemon_name: str, move_name: str):
    """はれ/あめ: 防御側がばんのうがさを持つ場合は威力補正が無効"""
    battle = t.start_battle(
        team0=[Pokemon(pokemon_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", item_name="ばんのうがさ")],
        weather=(weather, 99),
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_ひかりのかべ_すりぬけは軽減を貫通する():
    """ひかりのかべ: すりぬけ特性を持つ攻撃側はひかりのかべを無視する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すりぬけ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        side1={"ひかりのかべ": 5},
    )
    t.run_move(battle, 0)
    # すりぬけ特性のため damage_modifier が 4096（等倍、軽減なし）
    assert battle.damage_calculator.damage_modifier == 4096


@pytest.mark.parametrize("terrain,attacker_name,defender_name,move_name,expected", [
    ("エレキフィールド", "ピカチュウ", "ピカチュウ", "でんきショック", 5325),
    ("グラスフィールド", "フシギダネ", "ピカチュウ", "このは", 5325),
    ("サイコフィールド", "フーディン", "ピカチュウ", "サイコキネシス", 5325),
    ("ミストフィールド", "カイリュー", "ピカチュウ", "りゅうのはどう", 2048),
])
def test_フィールド_タイプ威力補正(
    terrain: TerrainName, attacker_name: str, defender_name: str, move_name: str, expected: int
):
    """各フィールド: 接地ポケモンへのタイプ威力補正"""
    battle = t.start_battle(
        team0=[Pokemon(attacker_name, move_names=[move_name])],
        team1=[Pokemon(defender_name)],
        terrain=(terrain, 99),
    )
    t.run_move(battle, 0)
    assert expected == battle.damage_calculator.power_modifier


@pytest.mark.parametrize("terrain,attacker_name,defender_name,move_name", [
    ("エレキフィールド", "ピジョン", "ピカチュウ", "でんきショック"),
    ("グラスフィールド", "ピジョン", "ピカチュウ", "このは"),
    ("サイコフィールド", "ピジョン", "ピカチュウ", "サイコキネシス"),
    ("ミストフィールド", "カイリュー", "ピジョン", "りゅうのはどう"),
])
def test_フィールド_浮遊ポケモンは補正を受けない(
    terrain: TerrainName, attacker_name: str, defender_name: str, move_name: str
):
    """各フィールド: 浮遊ポケモンにはタイプ威力補正が適用されない"""
    battle = t.start_battle(
        team0=[Pokemon(attacker_name, move_names=[move_name])],
        team1=[Pokemon(defender_name)],
        terrain=(terrain, 99),
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_フェアリーロック_ゴーストタイプも交代できない():
    """フェアリーロック: ゴーストタイプのポケモンも交代できない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert not t.can_switch(battle, 0)


def test_フェアリーロック_ターン終了でフィールドが解除される():
    """フェアリーロック: ターン終了後にグローバルフィールドが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.global_manager.fields["フェアリーロック"].is_active

    t.end_turn(battle)
    assert not battle.global_manager.fields["フェアリーロック"].is_active


def test_フェアリーロック_発動済みは失敗する():
    """フェアリーロック: すでにフェアリーロック状態の場合は activate が False を返しフィールドのカウントは変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"])],
        team1=[Pokemon("カビゴン")],
        field={"フェアリーロック": 1},
        accuracy=100,
    )
    field = battle.global_manager.fields["フェアリーロック"]
    count_before = field.count
    t.run_move(battle, 0)
    # 再発動不可のためカウントは変わらない
    assert field.count == count_before


def test_フェアリーロック_相手側も交代できない():
    """フェアリーロック: フェアリーロック中は相手側のポケモンも交代できない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert not t.can_switch(battle, 1)


def test_フェアリーロック_解除後は交代できる():
    """フェアリーロック: フィールド解除後は双方が交代できるようになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    t.end_turn(battle)

    assert t.can_switch(battle, 0)
    assert t.can_switch(battle, 1)


def test_まきびし_あつぞこブーツで無効():
    """まきびし: あつぞこブーツを持つポケモンはダメージを受けない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", item_name="あつぞこブーツ")],
        side0={"まきびし": 3},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.hp == active.max_hp


@pytest.mark.parametrize("layers,divisor", [(1, 8), (2, 6), (3, 4)])
def test_まきびし_ダメージ(layers: int, divisor: int):
    """まきびし: 層別交代時ダメージ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        side0={"まきびし": layers},
    )
    active = t.run_switch(battle, 0, 1)
    expected_damage = active.max_hp // divisor
    actual_damage = active.max_hp - active.hp
    assert expected_damage == actual_damage, f"まきびし{layers}層のダメージが不正"


def test_まきびし_マジックガードで無効():
    """まきびし: マジックガードを持つポケモンはダメージを受けない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ", ability_name="マジックガード")],
        side0={"まきびし": 3},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.hp == active.max_hp


def test_まきびし_浮いているポケモンはダメージを受けない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ピジョン")],
        side0={"まきびし": 3},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.hp == active.max_hp


def test_マジックルーム_交代後も道具無効():
    """マジックルーム: 交代で場に出たポケモンのアイテムも無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
        field={"マジックルーム": 99},
    )
    # 2番目のポケモンに交代する
    t.run_switch(battle, 0, 1)
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    # マジックルーム中はたべのこしが発動しない
    assert mon.hp == 1


def test_マジックルーム_再発動で即解除():
    """マジックルーム: 発動中に再度使用するとフィールドが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["マジックルーム"])],
        team1=[Pokemon("ピカチュウ")],
        field={"マジックルーム": 5},
    )
    field = battle.global_manager.fields["マジックルーム"]
    assert field.is_active
    t.run_move(battle, 0)
    assert not field.is_active


def test_マジックルーム_道具効果無効化():
    """マジックルーム: アイテム効果が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
        field={"マジックルーム": 99},
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_みかづきのまい_全快ポケモンの交代では消費されず次の回復対象で発動する():
    """みかづきのまい: HP・状態異常・PPすべて満タンのポケモンが交代してきても
    フィールドは保留され続け、回復対象を持つ次のポケモンが出た時に発動する"""
    battle = t.start_battle(
        team0=[
            Pokemon("クレセリア"),
            Pokemon("ピカチュウ"),
            Pokemon("カビゴン", move_names=["たいあたり"]),
        ],
        team1=[Pokemon("カビゴン")],
        side0={"みかづきのまい": 1},
    )
    full_bench = battle.player_states[battle.players[0]].team[1]
    assert full_bench.hp == full_bench.max_hp
    assert not full_bench.ailment.is_active

    active = t.run_switch(battle, 0, 1)

    assert active is full_bench
    # HP・状態異常・PPすべて満タンなので消費されずフィールドは保留され続ける
    assert battle.get_side(active).get("みかづきのまい").is_active

    heal_target = battle.player_states[battle.players[0]].team[2]
    heal_target.moves[0].pp = 0

    active = t.run_switch(battle, 0, 2)

    assert active is heal_target
    assert active.moves[0].pp == active.moves[0].data.pp
    assert not battle.get_side(active).get("みかづきのまい").is_active


def test_ミストフィールド_ねむる失敗():
    """ミストフィールド: 接地ポケモンのねむるは失敗しHPも回復しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        terrain=("ミストフィールド", 99),
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    hp_before = mon.hp
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False, "ねむるが失敗しなかった"
    assert mon.hp == hp_before, "ねむる失敗なのにHPが回復した"
    assert not mon.ailment.is_active, "ねむる失敗なのにねむり状態になった"


def test_ミストフィールド_混乱防止():
    """ミストフィールド: 接地ポケモンへの混乱無効化"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")],
                            terrain=("ミストフィールド", 99),
                            )
    mon = battle.actives[0]
    result = battle.volatile_manager.apply(mon, "こんらん", count=3)
    assert not result, "ミストフィールド下で混乱が付与された"
    assert "こんらん" not in mon.volatiles, "混乱状態が追加されている"


def test_ミストフィールド_状態異常防止():
    """ミストフィールド: 接地ポケモンへの状態異常無効化"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")],
                            terrain=("ミストフィールド", 99),
                            )
    assert not battle.ailment_manager.apply(battle.actives[0], "どく")


def test_ミストフィールド_非接地は混乱防止されない():
    """ミストフィールド: 浮遊ポケモンへの混乱は防止されない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピジョン")],
        terrain=("ミストフィールド", 99),
    )
    mon = battle.actives[0]
    result = battle.volatile_manager.apply(mon, "こんらん", count=3)
    assert result
    assert "こんらん" in mon.volatiles


def test_ミストフィールド_非接地は状態異常防止されない():
    """ミストフィールド: 浮遊ポケモンへの状態異常は防止されない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピジョン")],
        terrain=("ミストフィールド", 99),
    )
    target = battle.actives[0]
    assert battle.ailment_manager.apply(target, "どく")
    assert target.ailment.is_active


def test_ゆき_エアロックでこおり防御強化が無効化される():
    """ゆき: エアロックで天候効果が無効化されている間はこおり防御1.5倍が適用されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ユキワラシ", ability_name="エアロック")],
        weather=("ゆき", 99),
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_modifier


def test_ゆき_こおり防御強化():
    """ゆき: こおりタイプ防御1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ユキワラシ")],
        weather=("ゆき", 99),
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.def_modifier


def test_らんきりゅう_ひこう以外は軽減しない():
    """らんきりゅう: ひこうタイプでなければ軽減しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン")],
        weather=("らんきりゅう", 99),
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier


@pytest.mark.parametrize("move_name", ["でんきショック", "アクセルロック", "アイススピナー"])
def test_らんきりゅう_ひこう弱点半減(move_name: str):
    """らんきりゅう: でんき・いわ・こおり技のひこうタイプへの弱点を1倍に軽減する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピジョン")],
        weather=("らんきりゅう", 99),
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier


@pytest.mark.parametrize("weather", ["はれ", "あめ", "すなあらし", "ゆき", "おおひでり", "おおあめ"])
def test_らんきりゅう_全天候を上書き(weather: WeatherName):
    """らんきりゅう: 通常天候・強天候を問わず上書きできる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather, 99),
    )
    result = battle.weather_manager.apply("らんきりゅう", 5)
    assert result is True
    assert battle.raw_weather.name == "らんきりゅう"


@pytest.mark.parametrize("weather", ["おおひでり", "おおあめ"])
def test_らんきりゅう_強天候に上書きされない(weather: WeatherName):
    """らんきりゅう: 強天候（おおひでり・おおあめ）による上書きも失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        weather=("らんきりゅう", 99),
    )
    result = battle.weather_manager.apply(weather, 99)
    assert result is False
    assert battle.raw_weather.name == "らんきりゅう"


@pytest.mark.parametrize("weather", ["はれ", "あめ", "すなあらし", "ゆき"])
def test_らんきりゅう_通常天候に上書きされない(weather: WeatherName):
    """らんきりゅう: 通常天候（はれ・あめ等）による上書きは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        weather=("らんきりゅう", 99),
    )
    result = battle.weather_manager.apply(weather, 5)
    assert result is False
    assert battle.raw_weather.name == "らんきりゅう"


def test_リフレクター_すりぬけは軽減を貫通する():
    """リフレクター: すりぬけ特性を持つ攻撃側はリフレクターを無視する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すりぬけ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        side1={"リフレクター": 5},
    )
    t.run_move(battle, 0)
    # すりぬけ特性のため damage_modifier が 4096（等倍、軽減なし）
    assert battle.damage_calculator.damage_modifier == 4096


def test_ワンダールーム_再使用で解除():
    """ワンダールーム: 発動中に再度使用するとフィールドが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", move_names=["ワンダールーム"])],
        team1=[Pokemon("ピカチュウ")],
        field={"ワンダールーム": 5},
    )
    field = battle.global_manager.fields["ワンダールーム"]
    assert field.is_active
    t.run_move(battle, 0)
    assert not field.is_active


def test_ワンダールーム_物理技は特防側を参照():
    """ワンダールーム: 物理技の防御参照が特防側に入れ替わる"""
    normal = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    normal_defender = normal.actives[1]
    normal_defender.rank["def"] = 6
    normal_defender.rank["spd"] = -6
    normal_ctx = AttackContext(attacker=normal.actives[0], defender=normal_defender, move=normal.actives[0].moves[0])
    normal_def = normal.damage_calculator._calc_final_defense(normal_ctx)

    wonder = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        field={"ワンダールーム": 99},
    )
    wonder_defender = wonder.actives[1]
    wonder_defender.rank["def"] = 6
    wonder_defender.rank["spd"] = -6
    wonder_ctx = AttackContext(attacker=wonder.actives[0], defender=wonder_defender, move=wonder.actives[0].moves[0])
    wonder_def = wonder.damage_calculator._calc_final_defense(wonder_ctx)

    assert wonder_def < normal_def


def test_ワンダールーム_物理技は特防実数値を使用():
    """ワンダールーム: 物理技の防御計算が特防実数値を使う（ランクは0で検証）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        field={"ワンダールーム": 99},
    )
    defender = battle.actives[1]
    ctx = AttackContext(
        attacker=battle.actives[0],
        defender=defender,
        move=battle.actives[0].moves[0],
    )
    expected = defender.stats["spd"]
    actual = battle.damage_calculator._calc_final_defense(ctx)
    assert actual == expected, f"物理技がB実数値({defender.stats['B']})ではなくD実数値({expected})を参照するはず"


def test_ワンダールーム_特殊技は防御側を参照():
    """ワンダールーム: 特殊技の防御参照が防御側に入れ替わる"""
    normal = t.start_battle(
        team0=[Pokemon("ゼニガメ", move_names=["みずでっぽう"])],
        team1=[Pokemon("ピカチュウ")],
    )
    normal_defender = normal.actives[1]
    normal_defender.rank["def"] = -6
    normal_defender.rank["spd"] = 6
    normal_ctx = AttackContext(attacker=normal.actives[0], defender=normal_defender, move=normal.actives[0].moves[0])
    normal_def = normal.damage_calculator._calc_final_defense(normal_ctx)

    wonder = t.start_battle(
        team0=[Pokemon("ゼニガメ", move_names=["みずでっぽう"])],
        team1=[Pokemon("ピカチュウ")],
        field={"ワンダールーム": 99},
    )
    wonder_defender = wonder.actives[1]
    wonder_defender.rank["def"] = -6
    wonder_defender.rank["spd"] = 6
    wonder_ctx = AttackContext(attacker=wonder.actives[0], defender=wonder_defender, move=wonder.actives[0].moves[0])
    wonder_def = wonder.damage_calculator._calc_final_defense(wonder_ctx)

    assert wonder_def < normal_def


def test_ワンダールーム_特殊技は防御実数値を使用():
    """ワンダールーム: 特殊技の防御計算が防御実数値を使う（ランクは0で検証）"""
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", move_names=["みずでっぽう"])],
        team1=[Pokemon("ピカチュウ")],
        field={"ワンダールーム": 99},
    )
    defender = battle.actives[1]
    ctx = AttackContext(
        attacker=battle.actives[0],
        defender=defender,
        move=battle.actives[0].moves[0],
    )
    expected = defender.stats["def"]
    actual = battle.damage_calculator._calc_final_defense(ctx)
    assert actual == expected, f"特殊技がD実数値({defender.stats['D']})ではなくB実数値({expected})を参照するはず"


@pytest.mark.parametrize(
    "field_name",
    ["じゅうりょく", "トリックルーム", "マジックルーム", "ワンダールーム"]
)
def test_全体フィールドカウント減少(field_name: GlobalFieldName):
    """カウントダウンテスト"""
    initial_duration = 2
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        field={field_name: initial_duration}
    )
    field = battle.get_global_field(field_name)
    # 初期カウント確認
    assert field.count == initial_duration
    # カウントダウン確認
    t.end_turn(battle)
    assert field.count == initial_duration - 1, f"{field.name} count is incorrect"
    # カウントダウン確認
    t.end_turn(battle)
    assert field.count == initial_duration - 2, f"{field.name} count is incorrect"
    assert not field.is_active, f"{field.name} should be inactive"


@pytest.mark.parametrize(
    "terrain_name",
    ["エレキフィールド", "グラスフィールド", "サイコフィールド", "ミストフィールド"]
)
def test_地形カウント減少(terrain_name: TerrainName):
    """カウントダウンテスト"""
    initial_duration = 2
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        terrain=(terrain_name, initial_duration)
    )
    field = battle.terrain
    # 初期カウント確認
    assert field.count == initial_duration
    # カウントダウン確認
    t.end_turn(battle)
    assert field.count == initial_duration - 1, f"{field.name} count is incorrect"
    # カウントダウン確認
    t.end_turn(battle)
    assert field.count == initial_duration - 2, f"{field.name} count is incorrect"
    assert not field.is_active, f"{field.name} should be inactive"


@pytest.mark.parametrize(
    "weather_name",
    ["はれ", "あめ", "すなあらし", "ゆき"]
)
def test_天候カウント減少(weather_name: WeatherName):
    """カウントダウンテスト"""
    initial_duration = 2
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        weather=(weather_name, initial_duration)
    )
    field = battle.raw_weather
    # 初期カウント確認
    assert field.count == initial_duration
    # カウントダウン確認
    t.end_turn(battle)
    assert field.count == initial_duration - 1, f"{field.name} count is incorrect"
    # カウントダウン確認
    t.end_turn(battle)
    assert field.count == initial_duration - 2, f"{field.name} count is incorrect"
    assert not field.is_active, f"{field.name} should be inactive"


@pytest.mark.parametrize("weather,pokemon_name,move_name", [
    ("おおひでり", "ゼニガメ", "みずでっぽう"),
    ("おおひでり", "ゼニガメ", "みずびたし"),
    ("おおあめ", "ヒトカゲ", "ひのこ"),
    ("おおあめ", "ヒトカゲ", "おにび"),
])
def test_強天候_反対タイプ技は失敗(weather: WeatherName, pokemon_name: str, move_name: str):
    """おおひでり/おおあめ: 反対タイプ技は攻撃・変化を問わず失敗する"""
    battle = t.start_battle(
        team0=[Pokemon(pokemon_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather, 99),
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False


@pytest.mark.parametrize("weather,pokemon_name,move_name", [
    ("おおひでり", "ヒトカゲ", "ひのこ"),
    ("おおあめ", "ゼニガメ", "みずでっぽう"),
])
def test_強天候_同タイプ技はブロックされない(weather: WeatherName, pokemon_name: str, move_name: str):
    """おおひでり/おおあめ: 対応タイプ技はブロックされない"""
    battle = t.start_battle(
        team0=[Pokemon(pokemon_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather, 99),
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True


@pytest.mark.parametrize("weather,pokemon_name,move_name", [
    ("おおひでり", "ヒトカゲ", "ひのこ"),
    ("おおあめ", "ゼニガメ", "みずでっぽう"),
])
def test_強天候_同タイプ技は威力強化(weather: WeatherName, pokemon_name: str, move_name: str):
    """おおひでり/おおあめ: 対応タイプ技威力1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon(pokemon_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather, 99),
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_強天候中は通常天候で上書きできない():
    """おおひでり中に通常天候(はれ)を発動しようとしても上書きされない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        weather=("おおひでり", 99),
    )
    result = battle.weather_manager.apply("はれ", 5)
    assert result is False
    assert battle.raw_weather.name == "おおひでり"


def test_強天候同士は上書きできる():
    """おおひでり中におおあめを発動すると上書きされる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        weather=("おおひでり", 99),
    )
    result = battle.weather_manager.apply("おおあめ", 99)
    assert result is True
    assert battle.raw_weather.name == "おおあめ"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
