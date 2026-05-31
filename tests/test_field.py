"""フィールド効果ハンドラの単体テスト（天候・地形・サイドフィールド・グローバルフィールド）"""
import pytest
from jpoke import Battle, Pokemon
from jpoke.enums import Event
from jpoke.utils.type_defs import Weather, Terrain, GlobalField, SideField
from jpoke.core import EventContext
import test_utils as t


# ──────────────────────────────────────────────────────────────────
# はれ、あめ
# ──────────────────────────────────────────────────────────────────
# TODO : はれとあめの類似効果はパラメタライズでまとめる
def test_はれ_ほのお強化():
    """はれ: ほのお技威力1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 99),
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_はれ_みず弱化():
    """はれ: みず技威力0.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 99),
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.power_modifier


def test_あめ_みず強化():
    """あめ: みず技威力1.5倍"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        weather=("あめ", 99),
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_あめ_ほのお弱化():
    """あめ: ほのお技威力0.5倍"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        weather=("あめ", 99),
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.power_modifier


# ──────────────────────────────────────────────────────────────────
# すなあらし
# ──────────────────────────────────────────────────────────────────

def test_すなあらし_いわ特防強化():
    """すなあらし: いわタイプ特防1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["スピードスター"])],
        team1=[Pokemon("イシツブテ")],
        weather=("すなあらし", 99),
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.def_modifier


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


# TODO : じめん、はがねもすなあらしダメージを受けない。パラメタライズでまとめる
sandstorm_immune_types = ["いわ", "じめん", "はがね"]


def test_すなあらし_タイプ免疫():
    """すなあらし: いわ・じめん・はがねタイプはダメージを受けない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("イシツブテ")],
        weather=("すなあらし", 99),
    )
    t.end_turn(battle)
    actual_damages = [mon.max_hp - mon.hp for mon in battle.actives]
    expected_damages = [0, battle.actives[1].max_hp // 16]
    assert actual_damages == expected_damages, "Incorrect sandstorm damage applied"


@pytest.mark.parametrize(
    "ability_name",
    ["すなかき", "すながくれ", "すなのちから", "ぼうじん"]
)
def test_すなあらし_特性免疫(ability_name: str):
    """特定の特性を持つポケモンはすなあらしのダメージを受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability=ability_name)],
        team1=[Pokemon("ピカチュウ")],
        weather=("すなあらし", 999),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


# ──────────────────────────────────────────────────────────────────
# ゆき
# ──────────────────────────────────────────────────────────────────

def test_ゆき_こおり防御強化():
    """ゆき: こおりタイプ防御1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ユキワラシ")],
        weather=("ゆき", 99),
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.def_modifier


# ──────────────────────────────────────────────────────────────────
# おおひでり、おおあめ
# ──────────────────────────────────────────────────────────────────
# TODO : おおひでりとおおあめの類似効果はパラメタライズでまとめる
def test_おおひでり_ほのお強化():
    """おおひでり: ほのお技威力1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("おおひでり", 99),
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


def test_おおひでり_みず技を失敗させる():
    """おおひでり: みずタイプ技は攻撃・変化を問わず失敗する"""
    attack_battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("おおひでり", 99),
    )
    t.run_move(attack_battle, 0)
    assert attack_battle.move_executor.move_success is False

    status_battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", moves=["みずびたし"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("おおひでり", 99),
    )
    t.run_move(status_battle, 0)
    assert status_battle.move_executor.move_success is False


def test_おおひでり_ほのお技はブロックされない():
    """おおひでり: ほのお技はブロックされない"""
    battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("おおひでり", 99),
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True


def test_おおあめ_ほのお技を失敗させる():
    """おおあめ: ほのおタイプ技は攻撃・変化を問わず失敗する"""
    attack_battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ", moves=["ひのこ"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("おおあめ", 99),
    )
    t.run_move(attack_battle, 0)
    assert attack_battle.move_executor.move_success is False

    status_battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ", moves=["おにび"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("おおあめ", 99),
    )
    t.run_move(status_battle, 0)
    assert status_battle.move_executor.move_success is False


def test_おおあめ_みず技はブロックされない():
    """おおあめ: みず技はブロックされない"""
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("おおあめ", 99),
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True


def test_おおあめ_みず強化():
    """おおあめ: みず技威力1.5倍"""
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("おおあめ", 99),
    )
    t.run_move(battle, 0)
    assert 6144 == battle.damage_calculator.power_modifier


# TODO : みず技を弱化させるのではなく技の発動が失敗する。おおあめも同様。
def test_おおひでり_みず弱化():
    """おおひでり: みず技威力0.5倍"""
    pass


def test_おおあめ_ほのお弱化():
    """おおあめ: ほのお技威力0.5倍"""
    pass


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

# ──────────────────────────────────────────────────────────────────
# らんきりゅう
# ──────────────────────────────────────────────────────────────────

# TODO : いわ、こおりも弱点軽減する。パラメタライズでまとめる


def test_らんきりゅう_ひこう弱点半減():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        team1=[Pokemon("ピジョン")],
        weather=("らんきりゅう", 99),
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier


def test_らんきりゅう_ひこう以外は軽減しない():
    """らんきりゅう: ひこうタイプでなければ軽減しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        team1=[Pokemon("カビゴン")],
        weather=("らんきりゅう", 99),
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier

# TODO : 他の天候・強天候をすべて上書きすることを確認するテストを追加

# ──────────────────────────────────────────────────────────────────
# フィールド共通
# ──────────────────────────────────────────────────────────────────

# TODO : フィールドによるタイプ強化・弱化テストは、全フィールドをパラメタライズでまとめる。
# 浮いているポケモンに効果が適用されないテストは別関数にわける


def test_エレキフィールド_でんき強化():
    """エレキフィールド: でんき技威力1.3倍"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        terrain=("エレキフィールド", 99),
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier


def test_エレキフィールド_でんき強化は接地ポケモンのみ():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピジョン", moves=["でんきショック"])],
        terrain=("エレキフィールド", 99),
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_グラスフィールド_くさ強化():
    """グラスフィールド: くさ技威力1.3倍"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("フシギダネ", moves=["このは"])],
        terrain=("グラスフィールド", 99),
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier

    floating_battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピジョン", moves=["このは"])],
        terrain=("グラスフィールド", 99),
    )
    t.run_move(floating_battle, 0)
    assert 4096 == floating_battle.damage_calculator.power_modifier


def test_サイコフィールド_エスパー強化():
    """サイコフィールド: エスパー技威力1.3倍"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("フーディン", moves=["サイコキネシス"])],
        terrain=("サイコフィールド", 99),
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier

    floating_battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピジョン", moves=["サイコキネシス"])],
        terrain=("サイコフィールド", 99),
    )
    t.run_move(floating_battle, 0)
    assert 4096 == floating_battle.damage_calculator.power_modifier


def test_ミストフィールド_ドラゴン技弱化():
    """ミストフィールド: ドラゴン技威力0.5倍"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("カイリュー", moves=["りゅうのはどう"])],
        terrain=("ミストフィールド", 99),
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.power_modifier

# ──────────────────────────────────────────────────────────────────
# エレキフィールド
# ──────────────────────────────────────────────────────────────────
# TODO : 各テストに対し、非接地ポケモンに効果が適用されないテストを別関数で追加


def test_エレキフィールド_ねむり防止():
    """エレキフィールド: ねむり無効"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        terrain=("エレキフィールド", 99),
    )
    target = battle.actives[0]
    result = battle.ailment_manager.apply(target, "ねむり")
    assert not result, "エレキフィールド下でねむりが付与された"
    assert not target.ailment.is_active, "エレキフィールド下でねむり状態が付与された"

    floating_battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピジョン")],
        terrain=("エレキフィールド", 99),
    )
    floating_target = floating_battle.actives[0]
    assert floating_battle.ailment_manager.apply(floating_target, "ねむり")
    assert floating_target.ailment.is_active


def test_エレキフィールド_ねむけ防止():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        terrain=("エレキフィールド", 99),
    )
    target = battle.actives[0]
    assert not battle.volatile_manager.apply(target, "ねむけ", count=2)
    assert not target.has_volatile("ねむけ")

    floating_battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピジョン")],
        terrain=("エレキフィールド", 99),
    )
    floating_target = floating_battle.actives[0]
    assert floating_battle.volatile_manager.apply(floating_target, "ねむけ", count=2)
    assert floating_target.has_volatile("ねむけ")

# ──────────────────────────────────────────────────────────────────
# グラスフィールド
# ──────────────────────────────────────────────────────────────────
# TODO : 各テストに対し、非接地ポケモンに効果が適用されないテストを別関数で追加


def test_グラスフィールド_じしん弱化():
    """グラスフィールド: じしん威力0.5倍"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("サンドパン", moves=["じしん"])],
        terrain=("グラスフィールド", 99),
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.power_modifier


def test_グラスフィールド_じならし弱化():
    """グラスフィールド: じならし威力0.5倍"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("サンドパン", moves=["じならし"])],
        terrain=("グラスフィールド", 99),
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.power_modifier


def test_グラスフィールド_回復():
    """グラスフィールド: ターン終了時1/16回復"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        terrain=("グラスフィールド", 99),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1 + mon.max_hp // 16, "グラスフィールドの回復量が不正"

    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピジョン")],
        terrain=("グラスフィールド", 99),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1

# ──────────────────────────────────────────────────────────────────
# サイコフィールド
# ──────────────────────────────────────────────────────────────────
# TODO : 各テストに対し、非接地ポケモンに効果が適用されないテストを別関数で追加


def test_サイコフィールド_先制技無効():
    """サイコフィールド: 先制技無効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ")],
        terrain=("サイコフィールド", 99),
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False


def test_サイコフィールド_浮遊は先制技有効():
    """サイコフィールド: 浮遊相手には先制技が有効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        team1=[Pokemon("ピジョン")],
        terrain=("サイコフィールド", 99),
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True

# ──────────────────────────────────────────────────────────────────
# ミストフィールド
# ──────────────────────────────────────────────────────────────────
# TODO : 各テストに対し、非接地ポケモンに効果が適用されないテストを別関数で追加


def test_ミストフィールド_状態異常防止():
    """ミストフィールド: 状態異常無効化"""
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")],
                            terrain=("ミストフィールド", 99),
                            )
    assert not battle.ailment_manager.apply(battle.actives[0], "どく")


def test_ミストフィールド_混乱防止():
    """ミストフィールド: 混乱無効化"""
    # ミストフィールド下では混乱付与が失敗する
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")],
                            terrain=("ミストフィールド", 99),
                            )
    mon = battle.actives[0]
    result = battle.volatile_manager.apply(mon, "こんらん", count=3)
    assert not result, "ミストフィールド下で混乱が付与された"
    assert "こんらん" not in mon.volatiles, "混乱状態が追加されている"

# ──────────────────────────────────────────────────────────────────
# じゅうりょく
# ──────────────────────────────────────────────────────────────────


def test_じゅうりょく_命中補正():
    """じゅうりょく: 命中率5/3倍"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["でんじほう"])],
        team1=[Pokemon("ピカチュウ")],
        field={"じゅうりょく": 99}
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy * 5 // 3


def test_じゅうりょく_浮遊無効():
    """じゅうりょく: 浮遊状態を無効化"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピジョン")],
        field={"じゅうりょく": 99},
    )
    assert not battle.query_manager.is_floating(battle.actives[0])

# ──────────────────────────────────────────────────────────────────
# トリックルーム
# ──────────────────────────────────────────────────────────────────


def test_トリックルーム_素早さ逆順():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        field={"トリックルーム": 5},
    )
    t.reserve_command(battle)
    action_order = battle.calc_action_order()
    assert action_order[0] == battle.actives[0]


def test_トリックルーム_技優先度が優先():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
        field={"トリックルーム": 5},
    )
    t.reserve_command(battle)
    action_order = battle.calc_action_order()
    assert action_order[0] == battle.actives[1]

# ──────────────────────────────────────────────────────────────────
# マジックルーム
# ──────────────────────────────────────────────────────────────────


def test_マジックルーム_道具効果無効化():
    """マジックルーム: アイテム効果が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
        field={"マジックルーム": 99},
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1

# ──────────────────────────────────────────────────────────────────
# ワンダールーム
# ──────────────────────────────────────────────────────────────────


def test_ワンダールーム_物理技は特防側を参照():
    """ワンダールーム: 物理技の防御参照が特防側に入れ替わる"""
    normal = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    normal_defender = normal.actives[1]
    normal_defender.rank["B"] = 6
    normal_defender.rank["D"] = -6
    normal_ctx = EventContext(attacker=normal.actives[0], defender=normal_defender, move=normal.actives[0].moves[0])
    normal_def = normal.damage_calculator._calc_final_defense(normal_ctx)

    wonder = t.start_battle(
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        field={"ワンダールーム": 99},
    )
    wonder_defender = wonder.actives[1]
    wonder_defender.rank["B"] = 6
    wonder_defender.rank["D"] = -6
    wonder_ctx = EventContext(attacker=wonder.actives[0], defender=wonder_defender, move=wonder.actives[0].moves[0])
    wonder_def = wonder.damage_calculator._calc_final_defense(wonder_ctx)

    assert wonder_def < normal_def


def test_ワンダールーム_特殊技は防御側を参照():
    """ワンダールーム: 特殊技の防御参照が防御側に入れ替わる"""
    normal = t.start_battle(
        team0=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        team1=[Pokemon("ピカチュウ")],
    )
    normal_defender = normal.actives[1]
    normal_defender.rank["B"] = -6
    normal_defender.rank["D"] = 6
    normal_ctx = EventContext(attacker=normal.actives[0], defender=normal_defender, move=normal.actives[0].moves[0])
    normal_def = normal.damage_calculator._calc_final_defense(normal_ctx)

    wonder = t.start_battle(
        team0=[Pokemon("ゼニガメ", moves=["みずでっぽう"])],
        team1=[Pokemon("ピカチュウ")],
        field={"ワンダールーム": 99},
    )
    wonder_defender = wonder.actives[1]
    wonder_defender.rank["B"] = -6
    wonder_defender.rank["D"] = 6
    wonder_ctx = EventContext(attacker=wonder.actives[0], defender=wonder_defender, move=wonder.actives[0].moves[0])
    wonder_def = wonder.damage_calculator._calc_final_defense(wonder_ctx)

    assert wonder_def < normal_def

# ──────────────────────────────────────────────────────────────────
# リフレクター、ひかりのかべ、オーロラベール
# ──────────────────────────────────────────────────────────────────
# TODO : ダメージ軽減テストをパラメタライズでまとめる。


def test_リフレクター_物理半減():
    """リフレクター: 物理技ダメージ軽減"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        side1={"リフレクター": 5},
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


def test_リフレクター_特殊軽減なし():
    """リフレクター: 特殊技が軽減されないことを確認"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        side1={"リフレクター": 5},
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_ひかりのかべ_特殊半減():
    """ひかりのかべ: 特殊技ダメージ軽減"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        side1={"ひかりのかべ": 5},
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


def test_ひかりのかべ_物理軽減なし():
    """ひかりのかべ: 物理技が軽減されないことを確認"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        side1={"ひかりのかべ": 5},
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_オーロラベール_物理半減():
    """オーロラベール: ダメージ0.5倍"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        side1={"オーロラベール": 1},
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


def test_オーロラベール_特殊半減():
    """オーロラベール: ダメージ0.5倍"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        side1={"オーロラベール": 1},
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier

# TODO : 急所による軽減無効テストもパラメタライズでまとめる


def test_リフレクター_急所では軽減されない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        side1={"リフレクター": 5},
    )
    ctx = EventContext(
        attacker=battle.actives[0],
        defender=battle.actives[1],
        move=battle.actives[0].moves[0],
    )
    ctx.critical = True
    assert battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, 4096) == 4096


def test_ひかりのかべ_急所では軽減されない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["でんきショック"])],
        side1={"ひかりのかべ": 5},
    )
    ctx = EventContext(
        attacker=battle.actives[0],
        defender=battle.actives[1],
        move=battle.actives[0].moves[0],
    )
    ctx.critical = True
    assert battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, 4096) == 4096


def test_オーロラベール_急所では軽減されない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", moves=["たいあたり"])],
        side1={"オーロラベール": 1},
    )
    ctx = EventContext(
        attacker=battle.actives[0],
        defender=battle.actives[1],
        move=battle.actives[0].moves[0],
    )
    ctx.critical = True
    assert battle.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, 4096) == 4096

# ──────────────────────────────────────────────────────────────────
# しんぴのまもり
# ──────────────────────────────────────────────────────────────────
# TODO : パラメタライズでまとめる
# TODO : 状態異常防止と混乱防止は別関数でテストする


def test_しんぴのまもり():
    """しんぴのまもり: 状態異常防止"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        side0={"しんぴのまもり": 1},
    )
    target = battle.actives[0]

    assert not battle.ailment_manager.apply(target, "どく")
    assert not target.ailment.is_active
    assert not battle.volatile_manager.apply(target, "こんらん", count=3)
    assert not target.has_volatile("こんらん")

# ──────────────────────────────────────────────────────────────────
# しろいきり
# ──────────────────────────────────────────────────────────────────


def test_しろいきり_能力低下防止():
    """しろいきり: 能力ランク低下を防ぐ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        side0={"しろいきり": 1},
    )
    target, source = battle.actives
    assert not battle.modify_stat(target, "A", -1, source=source)


def test_しろいきり_自発的な能力低下は防げない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        side0={"しろいきり": 1},
    )
    target = battle.actives[0]
    assert battle.modify_stat(target, "A", -1, source=target)
    assert target.rank["A"] == -1

# ──────────────────────────────────────────────────────────────────
# おいかぜ
# ──────────────────────────────────────────────────────────────────


def test_おいかぜ():
    """おいかぜ: 実効すばやさ2倍"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        side0={"おいかぜ": 1},
    )
    mon = battle.actives[0]
    assert battle.calc_effective_speed(mon) == 2 * mon.stats["S"]

# ──────────────────────────────────────────────────────────────────
# ねがいごと
# ──────────────────────────────────────────────────────────────────


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
    mon.hp = 1

    heal = 20
    field.heal = heal

    t.end_turn(battle)
    assert mon.hp == 1, "No wish heal occurred"
    assert field.count == 1, "Wish field count did not decrease"

    t.end_turn(battle)
    assert mon.hp == 1 + heal, "Wish heal amount is incorrect"
    assert not field.is_active, "Wish field did not deactivate"


# ──────────────────────────────────────────────────────────────────
# まきびし
# ──────────────────────────────────────────────────────────────────

# TODO : パラメタライズでまとめる

def test_まきびし_1層():
    """まきびし: 交代時1/8ダメージ（1層）"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        side0={"まきびし": 1},
    )
    active = t.run_switch(battle, 0, 1)
    expected_damage = active.max_hp // 8
    actual_damage = active.max_hp - active.hp
    assert expected_damage == actual_damage, "Damage is incorrect"


def test_まきびし_2層():
    """まきびし: 交代時1/6ダメージ（2層）"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        side0={"まきびし": 2},
    )
    active = t.run_switch(battle, 0, 1)
    expected_damage = active.max_hp // 6
    actual_damage = active.max_hp - active.hp
    assert expected_damage == actual_damage, "Makibishi x2 damage is incorrect"


def test_まきびし_3層():
    """まきびし: 3層で1/4ダメージ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        side0={"まきびし": 3},
    )
    active = t.run_switch(battle, 0, 1)
    expected_damage = active.max_hp // 4
    actual_damage = active.max_hp - active.hp
    assert expected_damage == actual_damage, "Damage is incorrect"


def test_まきびし_浮いているポケモンはダメージを受けない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ピジョン")],
        side0={"まきびし": 3},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.hp == active.max_hp

# ──────────────────────────────────────────────────────────────────
# どくびし
# ──────────────────────────────────────────────────────────────────


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


def test_どくびし_浮いているポケモンには効かない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ピジョン")],
        side0={"どくびし": 2},
    )
    active = t.run_switch(battle, 0, 1)
    assert not active.ailment.is_active


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

# ──────────────────────────────────────────────────────────────────
# ステルスロック
# ──────────────────────────────────────────────────────────────────


def test_ステルスロック_x1():
    """ステルスロック: 1倍ダメージ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        side0={"ステルスロック": 1},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.hp == active.max_hp - active.max_hp // 8


def test_ステルスロック_x4():
    """ステルスロック: 交代時タイプ相性ダメージ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("リザードン")],
        side0={"ステルスロック": 1},
    )
    active = t.run_switch(battle, 0, 1)
    actual_damage = active.max_hp - active.hp
    assert actual_damage == active.max_hp // 2

# ──────────────────────────────────────────────────────────────────
# ねばねばネット
# ──────────────────────────────────────────────────────────────────


def test_ねばねばネット():
    """ねばねばネット: 交代時素早さ-1"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        side0={"ねばねばネット": 1},
    )
    before_rank = battle.players[0].team[1].rank["S"]
    active = t.run_switch(battle, 0, 1)
    after_rank = active.rank["S"]
    assert after_rank == before_rank - 1, "Speed rank not decreased"


def test_ねばねばネット_浮いているポケモンには効かない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ"), Pokemon("ピジョン")],
        side0={"ねばねばネット": 1},
    )
    active = t.run_switch(battle, 0, 1)
    assert active.rank["S"] == 0

# ──────────────────────────────────────────────────────────────────
# カウントダウン
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "field",
    ["はれ", "あめ", "すなあらし", "ゆき"]
)
def test_天候カウント減少(field: Weather):
    """カウントダウンテスト"""
    event = Event.ON_TURN_END
    initial_duration = 2
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        weather=(field, initial_duration)
    )
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


@pytest.mark.parametrize(
    "field",
    ["エレキフィールド", "グラスフィールド", "サイコフィールド", "ミストフィールド"]
)
def test_地形カウント減少(field: Terrain):
    """カウントダウンテスト"""
    event = Event.ON_TURN_END
    initial_duration = 2
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        terrain=(field, initial_duration)
    )
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


@pytest.mark.parametrize(
    "field",
    ["じゅうりょく", "トリックルーム", "マジックルーム", "ワンダールーム"]
)
def test_全体フィールドカウント減少(field: GlobalField):
    """カウントダウンテスト"""
    event = Event.ON_TURN_END
    initial_duration = 2
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        field={field: initial_duration}
    )
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


@pytest.mark.parametrize(
    "field",
    ["リフレクター", "ひかりのかべ", "オーロラベール", "しんぴのまもり", "しろいきり", "おいかぜ"]
)
def test_サイドフィールドカウント減少(field: SideField):
    """カウントダウンテスト"""
    event = Event.ON_TURN_END
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
    battle.events.emit(event)
    assert all(f.count == initial_duration - 1 for f in fields)
    # カウントダウン確認
    battle.events.emit(event)
    assert all(f.count == initial_duration - 2 for f in fields)
    assert all(not f.is_active for f in fields)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
