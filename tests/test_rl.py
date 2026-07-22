"""jpoke.rl の単体テスト。"""
from jpoke import Battle, Player, Pokemon
from jpoke.enums import Command
from jpoke.players import RandomPlayer
from jpoke.rl import (
    ACTION_COMMANDS,
    ACTION_SPACE_SIZE,
    RewardWeights,
    RLBattleEnv,
    action_to_command,
    calc_state_value,
    command_to_action,
    embed_battle_basic,
    get_action_mask,
)
import pytest

def _make_team(n: int = 2) -> list[Pokemon]:
    names = ["ヒトカゲ", "ゼニガメ", "フシギダネ", "コラッタ", "ポッポ"]
    return [Pokemon(name, item_name="", move_names=["たいあたり"]) for name in names[:n]]


def test_action_commandsに特殊コマンドが含まれない():
    assert Command.STRUGGLE not in ACTION_COMMANDS
    assert Command.FORCED not in ACTION_COMMANDS
    assert len(ACTION_COMMANDS) == ACTION_SPACE_SIZE


def test_calc_state_valueが勝利時にvictory分を加算する():
    player1 = Player(username="Player1")
    player1.team = _make_team(1)
    player2 = Player(username="Player2")
    player2.team = _make_team(1)

    battle = Battle(player1, player2, n_selected=1, seed=1)
    battle.start()
    battle.modify_hp(battle.get_team(player2)[0], r=-1.0)

    assert battle.finished  # judge_winner()を経由してwinnerを確定させる
    weights = RewardWeights(victory=1.0)
    value = calc_state_value(battle, player1, weights)

    assert value == pytest.approx(1.0)


def test_calc_state_valueが瀕死_HP割合_状態異常_勝敗の重みを反映する():
    """poke-envのreward_computing_helperと同じ考え方: fainted/hp/status/victoryの
    重み付けで盤面を評価する。評価対象の生成ロジックはtree_search_playerとは独立に
    実装しているため（論点4）、手計算した期待値と突き合わせて確認する。
    """
    player1 = Player(username="Player1")
    player1.team = _make_team(3)
    player2 = Player(username="Player2")
    player2.team = _make_team(3)

    battle = Battle(player1, player2, n_selected=3, seed=1)
    battle.start()

    # player1の1体目を瀕死にする（HP割合合計・瀕死カウントの両方に影響）
    battle.modify_hp(battle.get_team(player1)[0], r=-1.0)
    # player2の2体目に状態異常を付与する
    battle.set_ailment(battle.get_team(player2)[1], "やけど")

    weights = RewardWeights(fainted=1.0, hp=1.0, status=0.5, victory=1.0)
    value = calc_state_value(battle, player1, weights)

    player_hp = sum(mon.hp_fraction for mon in battle.get_team(player1) if not mon.fainted)
    opponent_hp = sum(mon.hp_fraction for mon in battle.get_team(player2) if not mon.fainted)
    expected = (player_hp - opponent_hp) * weights.hp
    expected -= weights.fainted  # player1の瀕死1体分
    expected += weights.status  # player2のやけど1体分

    assert value == pytest.approx(expected)
    assert value == pytest.approx(-1.5)


def test_command_to_actionとaction_to_commandが相互変換できる():
    for command in ACTION_COMMANDS:
        action = command_to_action(command)
        assert 0 <= action < ACTION_SPACE_SIZE
        assert action_to_command(action) == command


def test_embed_battle_basicが期待する長さのベクトルを返す():
    player1 = RandomPlayer(username="Player1")
    player1.team = _make_team(2)
    player2 = RandomPlayer(username="Player2")
    player2.team = _make_team(2)

    battle = Battle(player1, player2, n_selected=2, seed=1)
    battle.start()

    features = embed_battle_basic(battle, player1)

    assert len(features) == (2 + 2) * 3  # (自分+相手)の体数 × [HP割合, 瀕死, 状態異常]
    assert all(0.0 <= v <= 1.0 for v in features)


def test_get_action_maskがavailable_commandsと一致する():
    player1 = RandomPlayer(username="Player1")
    player1.team = _make_team()
    player2 = RandomPlayer(username="Player2")
    player2.team = _make_team()

    battle = Battle(player1, player2, n_selected=2, seed=1)
    battle.start()

    mask = get_action_mask(battle, player1)
    with battle.phase_context("action"):
        available = set(battle.available_commands(player1))

    assert mask == [1 if c in available else 0 for c in ACTION_COMMANDS]
    assert sum(mask) == len(available)


def test_rlbattleenvのreset_stepが最後まで例外なく完走する():
    learner = RandomPlayer(username="Learner")
    learner.team = _make_team()
    opponent = RandomPlayer(username="Opponent")
    opponent.team = _make_team()

    env = RLBattleEnv(learner, opponent, max_turns=5, n_selected=2, seed=1)
    action_mask, info = env.reset()

    assert len(action_mask) == ACTION_SPACE_SIZE
    assert info == {}

    terminated = truncated = False
    n_steps = 0
    while not (terminated or truncated):
        action = next(a for a, legal in enumerate(action_mask) if legal)
        action_mask, reward, terminated, truncated, info = env.step(action)
        n_steps += 1
        assert n_steps <= 5

    assert terminated or truncated


def test_rlbattleenvのstepが不正な行動を拒否する():
    learner = RandomPlayer(username="Learner")
    learner.team = _make_team()
    opponent = RandomPlayer(username="Opponent")
    opponent.team = _make_team()

    env = RLBattleEnv(learner, opponent, n_selected=2, seed=1)
    action_mask, _ = env.reset()

    illegal_action = next(a for a, legal in enumerate(action_mask) if not legal)
    with pytest.raises(ValueError):
        env.step(illegal_action)


def test_rlbattleenvのstepが決着ターンにvictory報酬を反映する():
    """battle.finished（judge_winner()経由でwinnerを確定させる副作用を持つ）を
    calc_state_value()より先に呼ばないと、決着した当のターンではwon()/lost()が
    まだ古いwinner（None）を見てvictory分が反映されない回帰を防ぐ。
    """
    learner = Player(username="Learner")
    learner.team = [Pokemon("カビゴン", item_name="", move_names=["たいあたり"])]
    opponent = Player(username="Opponent")
    opponent.team = [Pokemon("ポッポ", item_name="", move_names=["たいあたり"])]

    env = RLBattleEnv(learner, opponent, n_selected=1, seed=1, damage_roll="max")
    env.reset()

    # 相手をHP1にしておき、次の攻撃で確実に瀕死にする
    target = env.battle.get_team(opponent)[0]
    env.battle.modify_hp(target, v=-(target.hp - 1))

    action = command_to_action(Command.MOVE_0)
    _, reward, terminated, _, _ = env.step(action)

    assert terminated
    assert reward == pytest.approx(RewardWeights().victory)
