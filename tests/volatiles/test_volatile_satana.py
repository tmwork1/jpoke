"""揮発性状態ハンドラの単体テスト（サ〜ノ行）"""
import pytest
from jpoke import Move, Pokemon
from jpoke.enums import Command
from .. import test_utils as t

minimize_enhance_moves = [
    "ふみつけ", "のしかかり", "ドラゴンダイブ", "ヒートスタンプ", "ヘビーボンバー",
    "フライングプレス", "サンダーダイブ"
]


def test_さわぐ_さわぎだしでねむりを起こす():
    """さわぐ: さわぎだしたとき、場のねむり状態のポケモンが目を覚ます"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さわぐ"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("ねむり", 3),
        accuracy=100,
    )
    foe = battle.actives[1]
    assert foe.ailment.name == "ねむり"
    t.run_move(battle, 0)
    assert not foe.ailment.is_active


def test_さわぐ_技固定():
    """さわぐ: Command.FORCED が返り、解決後の技がさわぐになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さわぐ", "たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "さわぐ", count=2, move_name="さわぐ")
    with battle.phase_context("action"):
        assert battle.get_available_commands(battle.players[0]) == [Command.FORCED]
    move = battle.command_manager.resolve_move_from_command(battle.players[0], Command.FORCED)
    assert move.name == "さわぐ"


@pytest.mark.parametrize("volatile_name", ["さわぐ", "さわがしい"])
def test_さわぐさわがしい_ねむけからねむりへの移行を防ぐ(volatile_name):
    """さわぐ/さわがしい: ねむけ終了時にねむり状態への移行を防ぐ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={volatile_name: 2, "ねむけ": 1}
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert not mon.has_volatile("ねむけ")
    assert not mon.ailment.is_active


@pytest.mark.parametrize("volatile_name", ["さわぐ", "さわがしい"])
def test_さわぐさわがしい_ねむけは防がない(volatile_name):
    """さわぐ/さわがしい: ねむけ状態の付与は防がない（第五世代以降）"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={volatile_name: 2}
    )
    assert battle.volatile_manager.apply(battle.actives[0], "ねむけ", count=2)


@pytest.mark.parametrize("volatile_name", ["さわぐ", "さわがしい"])
def test_さわぐさわがしい_ねむりを防ぐ(volatile_name):
    """さわぐ/さわがしい: ねむり状態の付与を防ぐ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={volatile_name: 2}
    )
    assert not battle.ailment_manager.apply(battle.actives[0], "ねむり")


def test_さわぐ交代時_さわがしいを解除する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"さわぐ": 2},
        volatile1={"さわがしい": 2},
    )
    t.run_switch(battle, 0, 1)
    assert not battle.actives[1].has_volatile("さわがしい")


def test_さわぐ技使用_揮発性状態を付与する():
    """さわぐ: 技使用命中時にさわぐ揮発性状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さわぐ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    assert not mon.has_volatile("さわぐ")
    t.run_move(battle, 0)
    assert mon.has_volatile("さわぐ")
    assert mon.volatiles["さわぐ"].count == 3


def test_さわぐ終了時_さわがしいを解除する():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")],
        volatile0={"さわぐ": 1},
        volatile1={"さわがしい": 2},
    )
    t.end_turn(battle)
    assert not battle.actives[0].has_volatile("さわぐ")
    assert not battle.actives[1].has_volatile("さわがしい")


@pytest.mark.parametrize(
    "pokemon, expected_frac",
    [
        ("ピカチュウ", 16),
        ("ゼニガメ", 8),
        ("コイル", 8),
        ("エンペルト", 8),
    ]
)
def test_しおづけ_ターン終了時ダメージ(pokemon, expected_frac):
    """しおづけ: Champions仕様のターン終了時ダメージ（通常1/16、みず・はがね1/8）"""
    battle = t.start_battle(
        team0=[Pokemon(pokemon)],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"しおづけ": 1}
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.max_hp - mon.hp == mon.max_hp // expected_frac


def test_しおづけ_マジックガードでダメージ無効():
    """しおづけ: マジックガード特性を持つポケモンはダメージを受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"しおづけ": 1}
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


def test_しおづけ_交代で解除():
    """しおづけ: 交代するとしおづけ状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"しおづけ": 1}
    )
    mon = battle.actives[0]
    assert mon.has_volatile("しおづけ")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("しおづけ")


def test_シャドーダイブ_まもる中の相手にダメージを与えられる():
    """シャドーダイブはまもる状態を貫通する（unprotectable ラベル）"""
    battle = t.start_battle(
        team0=[Pokemon("ドガース", move_names=["シャドーダイブ"])],
        team1=[Pokemon("ドガース")],
    )
    defender = battle.actives[1]
    initial_hp = defender.hp
    battle.volatile_manager.apply(defender, "まもる", count=1)
    # 溜めターン
    t.run_move(battle, 0)
    assert battle.actives[0].has_volatile("シャドーダイブ")
    # 攻撃ターン（まもる状態の相手に攻撃）
    t.run_move(battle, 0)
    assert not battle.actives[0].has_volatile("シャドーダイブ")
    assert battle.move_executor.move_success
    assert defender.hp < initial_hp


def test_じごくづき_コマンド制限():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うたう", "たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"じごくづき": 2}
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    assert all(cmd.index != 0 for cmd in commands)


def test_じごくづき_ターン経過で解除():
    n_turn = 1
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"じごくづき": n_turn}
    )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("じごくづき")
        t.end_turn(battle)
    assert not mon.has_volatile("じごくづき")


def test_じごくづき_実行ブロック():
    """じごくづき: 音技の実行をブロックする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うたう"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"じごくづき": 2}
    )
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success


def test_じゅうでん_でんき技強化():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        volatile0={"じゅうでん": 1}
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.power_modifier
    assert not battle.actives[0].has_volatile("じゅうでん")


def test_じゅうでん_交代で解除():
    """じゅうでん: 交代するとじゅうでん状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"じゅうでん": 1}
    )
    mon = battle.actives[0]
    assert mon.has_volatile("じゅうでん")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("じゅうでん")


def test_じゅうでん_非でんき技では残る():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile0={"じゅうでん": 1}
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier
    assert battle.actives[0].has_volatile("じゅうでん")


def test_スレッドトラップ_接触技で素早さを下げる():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "スレッドトラップ", count=1)
    t.run_move(battle, 0)
    assert battle.actives[0].rank["spe"] == -1


def test_スレッドトラップ_非接触では素早さが下がらない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "スレッドトラップ", count=1)
    t.run_move(battle, 0)
    assert battle.actives[0].rank["spe"] == 0


def test_そうでん_ターン終了時に状態が解除される():
    """そうでん: ターン終了時（ON_TURN_END）にそうでん状態が自動で解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "そうでん")
    assert attacker.has_volatile("そうでん")

    t.end_turn(battle)

    assert not attacker.has_volatile("そうでん")


def test_そうでん_めざめるダンスに対してもでんきタイプが優先される():
    """そうでん: 使用者のタイプを参照するめざめるダンスに対しても、でんきタイプ変換が優先される"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["めざめるダンス"])],  # タイプ1=くさ
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "そうでん")
    t.run_move(battle, 0)

    assert battle.move_executor.move_type == "でんき"


def test_そうでん_わるあがきはでんきタイプに変換されない():
    """そうでん: そうでん状態でもわるあがきはでんきタイプに変換されない（タイプは空文字のまま）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "そうでん")
    battle.run_move(attacker, Move("わるあがき"))

    assert battle.move_executor.move_type == ""


def test_そうでん_状態中の攻撃技がでんきタイプになる():
    """そうでん: そうでん状態で使う攻撃技はでんきタイプに変換される"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["そうでん"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "そうでん")
    assert attacker.has_volatile("そうでん")
    t.run_move(battle, 0)

    assert battle.move_executor.move_type == "でんき"


def test_そらをとぶ_うちおとすが命中する():
    """そらをとぶ状態でもうちおとすは命中する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["うちおとす"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "そらをとぶ", count=1)
    t.run_move(battle, 0)
    assert battle.move_executor.move_success


@pytest.mark.parametrize("boost_move_name", ["かぜおこし", "たつまき"])
def test_そらをとぶ_かぜおこしたつまきの威力が2倍になる(boost_move_name):
    """そらをとぶ状態の相手にかぜおこし・たつまきを使うと威力補正が2倍（8192）になる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=[boost_move_name])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "そらをとぶ", count=1)
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_そらをとぶ_ぼうふうが命中する():
    """そらをとぶ状態でもぼうふうは命中する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ぼうふう"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "そらをとぶ", count=1)
    t.run_move(battle, 0)
    assert battle.move_executor.move_success


def test_タールショット_ほのお以外は変化しない():
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")],
                            team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
                            volatile1={"タールショット": 1}
                            )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier


def test_タールショット_ほのお半減ポケモンが等倍になる():
    """タールショット状態のほのおタイプポケモンに対してほのお技が等倍になる（半減→等倍）"""
    # ヒトカゲはほのおタイプ（ほのお半減）なのでタールショット後は等倍(4096)になる
    battle = t.start_battle(
        team1=[Pokemon("ヒトカゲ")],
        team0=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
        volatile1={"タールショット": 1}
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier


def test_タールショット_ほのお弱点付与():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["ひのこ"])],
        volatile1={"タールショット": 1}
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.def_type_modifier


def test_ダイビング_その他技は威力2倍にならない():
    """ダイビング状態でないときはなみのりの威力補正なし（power_modifier=4096）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["なみのり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


@pytest.mark.parametrize("boost_move_name", ["なみのり", "うずしお"])
def test_ダイビング_なみのりうずしおは威力2倍(boost_move_name):
    """ダイビング状態の相手になみのり・うずしおを使うと威力2倍"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=[boost_move_name])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "ダイビング", count=1)
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


@pytest.mark.parametrize("move_name", minimize_enhance_moves)
def test_ちいさくなる_minimize技が必中化して威力2倍(move_name):
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        volatile1={"ちいさくなる": 1}
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None
    assert 8192 == battle.damage_calculator.power_modifier


def test_ちいさくなる_対象外技には影響しない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        volatile1={"ちいさくなる": 1}
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy
    assert 4096 == battle.damage_calculator.power_modifier


def test_ちょうはつ_すでにちょうはつ状態の相手には効果なし():
    """ちょうはつ技: 相手がすでにちょうはつ状態の場合は効果がない（カウントが更新されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうはつ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        volatile1={"ちょうはつ": 3},
    )
    # すでにちょうはつ状態（count=3）のまま変化しないことを確認
    defender = battle.actives[1]
    assert defender.has_volatile("ちょうはつ")
    t.run_move(battle, 0)
    # volatile_manager.apply は既存状態があると False を返しカウントは更新されない
    assert defender.volatiles["ちょうはつ"].count == 3


def test_ちょうはつ_ターン経過で解除():
    n_turn = 1
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ちょうはつ": n_turn}
    )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("ちょうはつ")
        t.end_turn(battle)
    assert not mon.has_volatile("ちょうはつ")


def test_ちょうはつ_変化技は使えない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["ひかりのかべ"])],
        volatile0={"ちょうはつ": 3},
    )
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success


def test_ちょうはつ_技を使うと相手がちょうはつ状態になる():
    """ちょうはつ技: 命中すると相手にちょうはつ状態を付与する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ちょうはつ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_volatile("ちょうはつ")


def test_ちょうはつ_攻撃技は使える():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile0={"ちょうはつ": 3},
    )
    t.run_move(battle, 0)
    assert battle.move_executor.action_success


def test_でんじふゆう_じめん技を無効化する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["じしん"])],
        volatile0={"でんじふゆう": 5},
    )
    assert battle.query.is_floating(battle.actives[0])

    t.run_move(battle, 1)
    assert battle.damage_calculator.def_type_modifier is None
    assert battle.actives[0].hp == battle.actives[0].max_hp


def test_でんじふゆう_ターン経過で解除():
    n_turn = 1
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"でんじふゆう": n_turn},
    )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("でんじふゆう")
        t.end_turn(battle)
    assert not mon.has_volatile("でんじふゆう")


def test_とくせいなし_特性が無効になる():
    """とくせいなし: 特性が無効になり技が効く"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="ちくでん")],
        volatile1={"とくせいなし": 5},
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_とくせいなし_解除後は特性が有効になる():
    """とくせいなし: 解除後は特性が有効に戻る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="ちくでん")],
        volatile1={"とくせいなし": 5},
    )
    defender = battle.actives[1]
    battle.volatile_manager.remove(defender, "とくせいなし")
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp


def test_トーチカ_接触技で毒を付与():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "トーチカ", count=1)
    t.run_move(battle, 0)
    assert battle.actives[0].has_ailment("どく")


def test_トーチカ_非接触では毒にならない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "トーチカ", count=1)
    t.run_move(battle, 0)
    assert not battle.actives[0].ailment.is_active


def test_にげられない_ゴーストタイプは交代できる():
    # ゴーストタイプはにげられない状態の効果を無視して交代できる
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"にげられない": 1},
    )
    assert battle.query.can_switch(battle.players[0])


def test_にげられない_交代不可():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"にげられない": 1},
    )
    # 交代コマンドが利用不可
    assert not battle.query.can_switch(battle.players[0])


def test_にげられない_発生源が交代すると解除():
    """にげられない: 状態を与えた相手（発生源）が交代すると、自分のにげられない状態も解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("コラッタ")],
        volatile1={"にげられない": 1},
    )
    t.run_switch(battle, 0, 1)
    assert not battle.actives[1].has_volatile("にげられない")


def test_ねむけ_ターン経過でねむりになる():
    """ねむけ: count=2 でターン終了×2回後にねむり状態になる"""
    n_turn = 2
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ねむけ": n_turn}
    )
    mon = battle.actives[0]
    for _ in range(n_turn):
        assert mon.has_volatile("ねむけ")
        assert not mon.has_ailment("ねむり")
        t.end_turn(battle)
    assert not mon.has_volatile("ねむけ")
    assert mon.has_ailment("ねむり")


def test_ねむけ_交代でねむけ状態がリセットされる():
    """ねむけ: 交代すると揮発性状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ねむけ": 2}
    )
    mon = battle.actives[0]
    assert mon.has_volatile("ねむけ")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("ねむけ")


def test_ねむけ_交代でねむり状態にならない():
    """ねむけ: 交代によってねむけが解除されても眠り状態（Ailment）にはならない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ねむけ": 2}
    )
    mon = battle.actives[0]
    assert mon.has_volatile("ねむけ")
    assert not mon.ailment.is_active
    t.run_switch(battle, 0, 1)
    # 交代後もねむり状態になっていない
    assert not mon.ailment.is_active
    # 交代先ポケモンもねむり状態にならない
    new_mon = battle.actives[0]
    assert not new_mon.ailment.is_active


def test_ねをはる_かいふくふうじ中は回復しない():
    """ねをはる: かいふくふうじ状態ではターン終了時の回復がブロックされる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ねをはる": 1, "かいふくふうじ": 1}
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_ねをはる_交代不可():
    """ねをはる: 通常ポケモンは交代できない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ねをはる": 1},
    )
    assert not battle.query.can_switch(battle.players[0])


def test_ねをはる_回復():
    """ねをはる: ターン終了時に最大HPの1/16回復する"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ねをはる": 1}
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1 + mon.max_hp // 16


def test_ねをはる_浮遊無効():
    """ねをはる: 浮遊しているポケモンでも地面にいる扱いになる"""
    battle = t.start_battle(
        team0=[Pokemon("ポッポ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ねをはる": 1},
    )
    assert not battle.query.is_floating(battle.actives[0])


def test_のろい_ダメージ():
    """のろい: ターン終了時ダメージ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"のろい": 1}
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    damage = mon.max_hp - mon.hp
    assert damage == mon.max_hp // 4


def test_のろい_マジックガードでダメージ無効():
    """のろい: マジックガード特性を持つポケモンはダメージを受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"のろい": 1}
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


def test_のろい_交代で解除():
    """のろい: 交代するとのろい状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"のろい": 1}
    )
    mon = battle.actives[0]
    assert mon.has_volatile("のろい")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("のろい")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
