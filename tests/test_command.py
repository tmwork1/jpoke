"""Command enum・コマンド解決の回帰テスト。

対象範囲外（ダイマックス・Zワザ）に対応する GIGAMAX_*/ZMOVE_* コマンドが、
`docs/api/README.md` の注記通り「候補として提示されず、明示的に渡してもわるあがき
扱いになる」ことを検証する。将来この挙動が変わった場合にドキュメントの追従漏れに
気づけるようにするための軽量な回帰テスト。

また `Command.is_type()` が `docs/api/README.md` の Command 章「インスタンス
プロパティ・メソッド」表の記載通りに動作することも検証する。

さらに `Battle.is_struggle_only()` が、`get_available_commands(player)[0]` による
わるあがき判定の罠（技コマンドが無くても交代可能な控えがいると交代コマンドが
先頭に来てしまう）を回避して正しく判定できることも検証する。
"""
import pytest

from jpoke.model import Pokemon
from jpoke.enums import Command

from . import test_utils as t


def test_GIGAMAXコマンド_明示的に渡すとわるあがきになる():
    """command_to_move()にGIGAMAX_*を明示的に渡しても、わるあがき扱いになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("コラッタ")],
    )
    player = battle.players[0]
    move = battle.command_to_move(player, Command.GIGAMAX_0)
    assert move.name == "わるあがき"


def test_GIGAMAXコマンド_行動候補に含まれない():
    """get_available_commands()はGIGAMAX_*を選択肢として返さない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("コラッタ")],
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.available_commands(player)
    assert not any(cmd.is_gigamax for cmd in commands)


def test_ZMOVEコマンド_明示的に渡すとわるあがきになる():
    """command_to_move()にZMOVE_*を明示的に渡しても、わるあがき扱いになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("コラッタ")],
    )
    player = battle.players[0]
    move = battle.command_to_move(player, Command.ZMOVE_0)
    assert move.name == "わるあがき"


def test_ZMOVEコマンド_行動候補に含まれない():
    """get_available_commands()はZMOVE_*を選択肢として返さない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("コラッタ")],
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.available_commands(player)
    assert not any(cmd.is_zmove for cmd in commands)


def test_is_struggle_only_FORCEDが優先される場合はFalse():
    """Command.FORCEDのみが返る強制行動中は、わるあがきの選択肢自体が
    存在しないためFalseを返す。"""
    battle = t.start_battle(
        team0=[Pokemon("ディグダ", move_names=["あなをほる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    # 1ターン目: あなをほるでチャージに入る
    t.run_move(battle, 0)

    with battle.phase_context("action"):
        assert battle.available_commands(player) == [Command.FORCED]
        assert not battle.is_struggle_only(player)


def test_is_struggle_only_かなしばりで全ての技が封じられた場合はTrue():
    """かなしばり等ON_MODIFY_COMMAND_OPTIONSハンドラで技コマンドが全て
    潰される場合でも正しくTrueを返す。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("コラッタ", move_names=["かなしばり"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # attackerが事前にたいあたりを使ったことにする
    t.run_move(battle, 0)
    # defender（コラッタ）がかなしばりを使いattackerの唯一の技を封じる
    t.run_move(battle, 1)
    assert attacker.has_volatile("かなしばり")

    player = battle.players[0]
    with battle.phase_context("action"):
        assert battle.is_struggle_only(player)


def test_is_struggle_only_こだわりで変化技に固定されちょうはつを受けた場合はTrue():
    """seed_619 turn12 の回帰テスト。

    こだわり系アイテムで変化技1つに固定されたポケモンがちょうはつを受けると、
    こだわりのON_MODIFY_COMMAND_OPTIONS（固定技以外を除外）とちょうはつの
    ON_MODIFY_COMMAND_OPTIONS（変化技を除外）が両方効いて選択可能な技コマンドが
    ゼロになり、わるあがきにフォールバックする必要がある。
    修正前はちょうはつにON_MODIFY_COMMAND_OPTIONSハンドラが無かったため、
    固定された変化技のコマンドが除外されずPP消費もダメージ機会も無いままターンが
    浪費されていた。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="こだわりメガネ", move_names=["てっぺき", "でんこうせっか"])],
        team1=[Pokemon("コラッタ", move_names=["ちょうはつ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # attackerが事前に変化技（てっぺき）を使い、こだわりでその技に固定される
    t.run_move(battle, 0)
    assert attacker.has_volatile("こだわり")
    # defender（コラッタ）がちょうはつを使いattackerを変化技封じ状態にする
    t.run_move(battle, 1)
    assert attacker.has_volatile("ちょうはつ")

    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.available_commands(player)
        assert Command.STRUGGLE in commands
        assert not any(cmd.is_move and cmd is not Command.STRUGGLE for cmd in commands)
        assert battle.is_struggle_only(player)


def test_is_struggle_only_ちょうはつで変化技しか使えない場合はTrue():
    """こだわり等の固定が無くても、変化技しか覚えていないポケモンがちょうはつを
    受けた場合は同様にわるあがきにフォールバックする必要がある。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["てっぺき"])],
        team1=[Pokemon("コラッタ")],
        volatile0={"ちょうはつ": 3},
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.available_commands(player)
        assert Command.STRUGGLE in commands
        assert battle.is_struggle_only(player)


def test_is_struggle_only_交代可能な控えがいても正しくTrueを返す():
    """技コマンドが1つも無くても交代可能な控えがいる場合、
    get_available_commands(player)[0] は交代コマンドを返してしまう
    （わるあがきのみと誤認する罠）が、is_struggle_only()は交代コマンドの有無に
    関わらず正しくTrueを返す。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"]), Pokemon("コラッタ")],
        team1=[Pokemon("ゼニガメ")],
    )
    player = battle.players[0]
    battle.actives[0].moves[0].modify_pp(-99)

    with battle.phase_context("action"):
        commands = battle.available_commands(player)
        # 罠の再現: 交代コマンドが先頭に来てSTRUGGLEではない
        assert commands[0].is_switch
        assert Command.STRUGGLE in commands
        # is_struggle_only()は罠の影響を受けず正しく判定する
        assert battle.is_struggle_only(player)


def test_is_struggle_only_技コマンドがある場合はFalse():
    """使用可能な技が残っている通常時はFalseを返す。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("コラッタ")],
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        assert not battle.is_struggle_only(player)


def test_is_struggle_only_技のPPが尽き交代先もいない場合はTrue():
    """技のPPが尽き控えもいない場合、get_available_commands()[0]もSTRUGGLEとなる
    単純なケースでTrueを返すことを確認する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[Pokemon("コラッタ")],
    )
    player = battle.players[0]
    battle.actives[0].moves[0].modify_pp(-99)

    with battle.phase_context("action"):
        commands = battle.available_commands(player)
        assert commands == [Command.STRUGGLE]
        assert battle.is_struggle_only(player)


def test_is_switch_プロパティとしてコマンド種別ごとに真偽を返す():
    """is_regular_move/is_terastal等と同様に@propertyとして実装されており、
    括弧を付けずに参照するだけで交代コマンドかどうかの真偽値を返す。
    """
    assert Command.SWITCH_0.is_switch
    assert Command.SWITCH_9.is_switch
    assert not Command.MOVE_0.is_switch
    assert not Command.TERASTAL_0.is_switch
    assert not Command.MEGAEVOL_0.is_switch
    assert not Command.GIGAMAX_0.is_switch
    assert not Command.ZMOVE_0.is_switch
    assert not Command.STRUGGLE.is_switch
    assert not Command.FORCED.is_switch
    # bound methodではなくboolを返すこと（真偽反転が機能することで確認）
    assert isinstance(Command.SWITCH_0.is_switch, bool)
    assert not (not Command.SWITCH_0.is_switch)


def test_is_type_Noneを渡すと偽を返す():
    """command_typeにNoneを渡した場合は種別を問わず偽になる。"""
    assert not Command.MOVE_0.is_type(None)
    assert not Command.SWITCH_0.is_type(None)


def test_is_type_anyを指定すると全てのコマンドが真になる():
    """docs/api/README.mdのCommand章の記載通り、"any"は種別を問わず真を返す。"""
    assert Command.MOVE_0.is_type("any")
    assert Command.SWITCH_0.is_type("any")
    assert Command.TERASTAL_0.is_type("any")
    assert Command.STRUGGLE.is_type("any")
    assert Command.FORCED.is_type("any")


def test_is_type_moveを指定すると技系コマンドのみ真になる():
    """"move"は通常技コマンドに加え、テラスタル・メガシンカ・ダイマックス・Zワザを
    伴う技コマンドも真になる（is_regular_moveは通常技コマンドのみ）。
    わるあがき・強制行動コマンドもresolve_move_from_command()で技に解決されるため
    真になる。
    """
    assert Command.MOVE_0.is_move
    assert Command.TERASTAL_0.is_move
    assert Command.MEGAEVOL_0.is_move
    assert Command.GIGAMAX_0.is_move
    assert Command.ZMOVE_0.is_move
    assert Command.STRUGGLE.is_move
    assert Command.FORCED.is_move
    assert not Command.SWITCH_0.is_move


def test_is_type_switchを指定すると交代コマンドのみ真になる():
    """"switch"はSWITCH_*コマンドのみ真になる。"""
    assert Command.SWITCH_0.is_switch
    assert not Command.MOVE_0.is_switch
    assert not Command.STRUGGLE.is_switch


def test_ちょうはつ_コマンド選択後に受けても行動前ならブロックされる():
    """複数の技選択肢がある中で変化技をコマンド選択した場合、選択時点では
    ON_MODIFY_COMMAND_OPTIONSによる除外は起きない（他に技があるため）。
    その後、行動前に相手より速い相手からちょうはつを受けた場合は、引き続き
    ON_TRY_ACTIONで行動がブロックされる（わるあがきへのフォールバックはしない）
    ことを確認する回帰テスト。ON_MODIFY_COMMAND_OPTIONSハンドラの追加が
    既存のON_TRY_ACTION側の挙動を壊していないことを検証する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ひかりのかべ", "たいあたり"])],
        team1=[Pokemon("サンダース", move_names=["ちょうはつ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    assert move.name == "ひかりのかべ"
    max_pp = move.pp

    # attacker（カビゴン）は変化技（ひかりのかべ）を選択、defender（サンダース）は
    # ちょうはつを選択。defenderの方が速いため、attackerの行動前にちょうはつが付与される。
    t.reserve_command(battle, command0=Command.MOVE_0, command1=Command.MOVE_0)
    battle.step()

    assert attacker.has_volatile("ちょうはつ")
    # ON_TRY_ACTIONでブロックされ、PPは消費されない（わるあがきにもフォールバックしない）
    assert move.pp == max_pp
    assert battle.move_executor.action_success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
