"""poke-env 互換化（.internal/poke-env/compat_plan.md）のクロスカッティングなテスト。

Phase 3（property追加）・Phase 4（変換テーブル）・Phase 5（`Player.battle_against`）を対象とする。
特定の特性・技・アイテムに紐づかない横断的な互換性テストのため、トップレベルに配置する。
"""
import os
import subprocess
from pathlib import Path
from typing import get_args

import pytest

from jpoke.core import Battle, Player
from jpoke.core.player import MAX_TURNS
from jpoke.model import Pokemon, Move
from jpoke.players import RandomPlayer
from jpoke.types import (
    AilmentName, GlobalFieldName, Nature, SideFieldName, TerrainName, Type, WeatherName,
)
from jpoke.types.poke_env import (
    GLOBAL_FIELD_MAP, NATURE_MAP, SIDE_CONDITION_MAP, STATUS_MAP, STAT_INDEX,
    TERRAIN_MAP, TYPE_MAP, WEATHER_MAP, evs_from_poke_env, stats_from_poke_env,
)

from . import test_utils as t
from .conftest import resolve_subprocess_python
import jpoke.core.player as player_module

ROOT = Path(__file__).resolve().parent.parent
# subprocessで起動する子プロセス用のインタプリタ。sys.executableにjpokeが
# 入っていない環境でも、リポジトリ直下の.venvにjpokeが入っていればそちらを優先する。
PYTHON = resolve_subprocess_python("jpoke")

# ── Phase 3: Pokemon のproperty ──────────────────────────────────────

# ── Phase 3: Move のproperty ──────────────────────────────────────

# ── Phase 3: Player のproperty ──────────────────────────────────────

# ── Phase 3: Battle のproperty ──────────────────────────────────────

# ── Phase 4: 変換テーブル・変換関数 ──────────────────────────────────

# ── Phase 5: Player.battle_against() ─────────────────────────────────


def test_battle_active_pokemonとopponent_active_pokemonはobserver未設定時場の先頭2匹を返す():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[Pokemon("ゼニガメ")],
    )

    assert battle.observer is None
    assert battle.active_pokemon is battle.actives[0]
    assert battle.opponent_active_pokemon is battle.actives[1]


def test_battle_active_pokemonとopponent_active_pokemonはobserver視点で取得できる():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[Pokemon("ゼニガメ")],
    )
    observer, _ = battle.players

    obs = battle.build_observation(observer)

    assert obs.active_pokemon.name == "フシギダネ"
    assert obs.opponent_active_pokemon.name == "ゼニガメ"


def test_battle_against_n_battlesを複数指定すると回数分戦績が積み上がる():
    """n_battlesで指定した回数だけ対戦が繰り返され、戦績が回数分積み上がることを確認する。"""
    winner = Player("Winner")
    winner.team = [Pokemon("ガブリアス", level=100, move_names=["じしん"])]
    loser = Player("Loser")
    loser.team = [Pokemon("コイキング", level=1, move_names=["はねる"])]

    winner.battle_against(
        loser, n_battles=3,
        n_selected=1, accuracy_fix_threshold=0, damage_roll="min",
        mega_evolution=False, terastal=False,
    )

    assert winner.n_finished_battles == 3
    assert winner.n_won_battles == 3
    assert loser.n_finished_battles == 3
    assert loser.n_won_battles == 0


def test_battle_against_on_battle_endはターン上限で未決着の対戦でも呼ばれる(monkeypatch):
    """ターン上限（MAX_TURNS）に達し戦績にカウントされなかった対戦
    （winner is None）でも on_battle_end は呼ばれることを確認する。"""
    monkeypatch.setattr(player_module, "MAX_TURNS", 2)

    p0 = Player("p0")
    p0.team = [Pokemon("メタモン", move_names=["へんしん"])]
    p1 = Player("p1")
    p1.team = [Pokemon("メタモン", move_names=["へんしん"])]

    received: list[Battle] = []
    p0.battle_against(
        p1, n_battles=1, n_selected=1, accuracy_fix_threshold=0,
        on_battle_end=received.append,
    )

    assert len(received) == 1
    assert received[0].finished is False
    assert p0.n_finished_battles == 0


def test_battle_against_on_battle_endは各対戦ごとにbattleを渡して呼ばれる():
    """on_battle_end指定時、n_battles回の各対戦終了直後に呼ばれ、それぞれ
    開始済み（play_out済み）のBattleインスタンスが渡されることを確認する。"""
    winner = Player("Winner")
    winner.team = [Pokemon("ガブリアス", level=100, move_names=["じしん"])]
    loser = Player("Loser")
    loser.team = [Pokemon("コイキング", level=1, move_names=["はねる"])]

    received: list[Battle] = []
    winner.battle_against(
        loser, n_battles=3,
        n_selected=1, accuracy_fix_threshold=0, damage_roll="min",
        mega_evolution=False, terastal=False,
        on_battle_end=received.append,
    )

    assert len(received) == 3
    assert len(set(id(b) for b in received)) == 3  # 全て別インスタンス
    for battle in received:
        assert isinstance(battle, Battle)
        assert battle.finished is True


def test_battle_against_on_battle_end未指定時は従来通り呼ばれず戦績のみ更新される():
    """on_battle_end省略時（デフォルトNone）は、コールバックが呼ばれないだけで
    battle_against() 自体の戦績更新の挙動は変わらないことを確認する。"""
    winner = Player("Winner")
    winner.team = [Pokemon("ガブリアス", level=100, move_names=["じしん"])]
    loser = Player("Loser")
    loser.team = [Pokemon("コイキング", level=1, move_names=["はねる"])]

    winner.battle_against(
        loser, n_battles=2,
        n_selected=1, accuracy_fix_threshold=0, damage_roll="min",
        mega_evolution=False, terastal=False,
    )

    assert winner.n_finished_battles == 2
    assert winner.n_won_battles == 2


def test_battle_against_ターン上限で決着しない対戦は戦績にカウントされない(monkeypatch):
    """MAX_TURNSに達しても決着しない対戦は不成立として扱われ、n_finished_battlesも増加しないことを確認する。"""
    monkeypatch.setattr(player_module, "MAX_TURNS", 2)

    p0 = Player("p0")
    p0.team = [Pokemon("メタモン", move_names=["へんしん"])]
    p1 = Player("p1")
    p1.team = [Pokemon("メタモン", move_names=["へんしん"])]

    p0.battle_against(p1, n_battles=1, n_selected=1, accuracy_fix_threshold=0)

    assert p0.n_finished_battles == 0
    assert p0.n_won_battles == 0
    assert p1.n_finished_battles == 0
    assert p1.n_won_battles == 0


def test_battle_against_勝敗が戦績に反映される():
    """battle_against() の1戦の結果が双方のPlayerの戦績プロパティに正しく反映されることを確認する。"""
    winner = Player("Winner")
    winner.team = [Pokemon("ガブリアス", level=100, move_names=["じしん"])]
    loser = Player("Loser")
    loser.team = [Pokemon("コイキング", level=1, move_names=["はねる"])]

    winner.battle_against(
        loser, n_battles=1,
        n_selected=1, accuracy_fix_threshold=0, damage_roll="min",
        mega_evolution=False, terastal=False,
    )

    assert winner.n_finished_battles == 1
    assert winner.n_won_battles == 1
    assert winner.win_rate == pytest.approx(1.0)
    assert loser.n_finished_battles == 1
    assert loser.n_won_battles == 0
    assert loser.n_lost_battles == 1


def test_battle_against_複数opponent指定時はon_battle_endがopponent数times_n_battles回呼ばれる():
    """opponentsを複数指定した場合、on_battle_endは各opponentとのn_battles回すべて、
    合計 len(opponents) * n_battles 回呼ばれることを確認する。"""
    winner = Player("Winner")
    winner.team = [Pokemon("ガブリアス", level=100, move_names=["じしん"])]
    loser1 = Player("Loser1")
    loser1.team = [Pokemon("コイキング", level=1, move_names=["はねる"])]
    loser2 = Player("Loser2")
    loser2.team = [Pokemon("コイキング", level=1, move_names=["はねる"])]

    received: list[Battle] = []
    winner.battle_against(
        loser1, loser2, n_battles=2,
        n_selected=1, accuracy_fix_threshold=0, damage_roll="min",
        mega_evolution=False, terastal=False,
        on_battle_end=received.append,
    )

    assert len(received) == 4  # 2 opponents * n_battles=2
    opponents_seen = {tuple(sorted(p.username for p in b.players)) for b in received}
    assert opponents_seen == {("Loser1", "Winner"), ("Loser2", "Winner")}


def test_battle_available_movesはobserverが選択可能な技をmoveで返す():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["たいあたり", "はっぱカッター"])],
        team1=[Pokemon("ゼニガメ")],
    )
    observer, _ = battle.players

    with battle.phase_context("action"):
        obs = battle.build_observation(observer)
        names = {move.name for move in obs.available_moves}

    assert names == {"たいあたり", "はっぱカッター"}


def test_battle_available_movesは技のppが尽きるとわるあがきのみになる():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["たいあたり"])],
        team1=[Pokemon("ゼニガメ")],
    )
    observer, _ = battle.players
    battle.actives[0].moves[0].modify_pp(-99)

    with battle.phase_context("action"):
        obs = battle.build_observation(observer)
        names = [move.name for move in obs.available_moves]

    assert names == ["わるあがき"]


def test_battle_available_switchesはobserverの交代先候補をpokemonで返す():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ"), Pokemon("ヒトカゲ")],
        team1=[Pokemon("ゼニガメ")],
    )
    observer, _ = battle.players

    with battle.phase_context("action"):
        obs = battle.build_observation(observer)
        names = [mon.name for mon in obs.available_switches]

    assert names == ["ヒトカゲ"]


def test_battle_decision_randomの種はpythonhashseedに依存しない():
    """`Battle.decision_random` の種の派生式が `PYTHONHASHSEED` に依存しないことを、
    異なる `PYTHONHASHSEED` を設定した2つのサブプロセスで同一の `Battle(seed=...)`
    を作り、`decision_random.getstate()` が完全に一致することで確認する。

    修正前は種の派生式が `hash((seed, "decision")) & 0xFFFFFFFF` だった。`str` を
    含む `tuple` の `hash()` は `str` のハッシュが `PYTHONHASHSEED` によって
    プロセスごとにランダム化される影響を受けるため、同じ `seed` を指定しても
    `decision_random` の初期状態がプロセスを跨ぐと再現しなかった
    （`RandomPlayer.choose_command()` 等が消費する乱数列のため、コマンド選択の
    再現実験・CI比較が壊れうる問題があった）。
    """
    script = (
        "from jpoke.core import Battle, Player\n"
        "p0 = Player('p0'); p1 = Player('p1')\n"
        "battle = Battle(p0, p1, seed=12345)\n"
        "print(battle.decision_random.getstate())\n"
    )

    def run_with_hashseed(hashseed: str) -> str:
        result = subprocess.run(
            [PYTHON, "-c", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONHASHSEED": hashseed},
        )
        assert result.returncode == 0, result.stderr
        return result.stdout.strip()

    state_a = run_with_hashseed("0")
    state_b = run_with_hashseed("12345")

    assert state_a == state_b
    assert state_a != ""


def test_battle_finishedとwonとlostは決着後に更新される():
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス", level=100, move_names=["じしん"])],
        team1=[Pokemon("コイキング", level=1, move_names=["はねる"])],
        accuracy=100,
        damage_roll="min",
    )
    player0, player1 = battle.players

    assert battle.finished is False
    assert battle.won(player0) is False
    assert battle.lost(player0) is False

    t.run_move(battle, player_idx=0)

    assert battle.finished is True
    assert battle.won(player0) is True
    assert battle.lost(player0) is False
    assert battle.won(player1) is False
    assert battle.lost(player1) is True


def test_battle_side_conditionsはobserver未設定時は空辞書():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[Pokemon("ゼニガメ")],
        side0={"リフレクター": 5},
    )

    assert battle.side_conditions == {}


def test_battle_side_conditionsはobserver視点のサイドフィールド状態を返す():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[Pokemon("ゼニガメ")],
        side0={"リフレクター": 5},
    )
    observer, _ = battle.players

    obs = battle.build_observation(observer)

    assert obs.side_conditions["リフレクター"].is_active


def test_battle_teamはobserver視点のチームリストを返す():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ"), Pokemon("ヒトカゲ")],
        team1=[Pokemon("ゼニガメ")],
    )
    observer, _ = battle.players

    assert battle.team == []  # observer未設定時は空

    obs = battle.build_observation(observer)

    assert [mon.name for mon in obs.team] == ["フシギダネ", "ヒトカゲ"]


def test_evs_from_poke_envの戻り値はpokemonのset_evsにそのまま渡せる():
    mon = Pokemon("ピカチュウ")
    d = {"hp": 252, "atk": 252, "def": 4, "spa": 0, "spd": 0, "spe": 0}

    mon.set_evs(evs_from_poke_env(d))

    assert mon.evs == [32, 32, 1, 0, 0, 0]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 0),
        (3, 0),    # 4未満は0扱い
        (4, 1),
        (11, 1),
        (12, 2),
        (252, 32),  # 最大値
    ]
)
def test_evs_from_poke_envはchampions形式の努力値に変換する(value: int, expected: int):
    d = {"hp": value, "atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0}
    assert evs_from_poke_env(d)[0] == expected


def test_max_turnsは100():
    assert MAX_TURNS == 100


def test_move_current_ppとmax_ppはppとdata_ppのエイリアス():
    move = Move("たいあたり")
    move.modify_pp(-1)

    assert move.current_pp == move.pp
    assert move.max_pp == move.data.pp


@pytest.mark.parametrize(
    ("move_name", "expected"),
    [
        ("たいあたり", 1.0),        # 通常技（1回ヒット）
        ("タキオンカッター", 2.0),  # min=max=2の固定複数回技
        ("ミサイルばり", 3.1),      # min=2,max=5の分布技（poke-envの期待値と同値）
    ]
)
def test_move_expected_hitsは技のヒット回数分布に応じた期待値を返す(move_name: str, expected: float):
    move = Move(move_name)
    assert move.expected_hits == pytest.approx(expected)


def test_observationのdecision_randomは共有されrandomは独立している():
    """`build_observation()` が返す観測用コピー（sim）について、行動選択専用の
    `decision_random` は本体 `battle.decision_random` と同一オブジェクトを共有する
    一方、ゲーム進行用の `random` はdeepcopyされた独立インスタンスのままであることを
    確認する。

    `decision_random` を共有するのは、技を使わず交代だけが選ばれ続けるターンでも
    本体側の乱数状態を確実に進め、次のターンも同じ乱数状態から観測用コピーが作られて
    同じ選択が繰り返される無限交代ループを防ぐため（`examples/01_basics/03_team_battle.py` の
    seed=1,2,3,5 で再現していた重大バグ）。

    一方 `random` を独立させたまま（本体と共有しない）にしているのは、これを共有すると
    `Player.choose_command(sim)` 内で方策が `sim.random` を直接触った場合に、本来は
    その後の技実行（ダメージロール・命中判定・急所判定等）で消費されるはずの乱数列を
    行動選択の時点で先取り・消費できてしまい、「これから打つ技が急所に当たるか」を
    打つ前に知った上で行動を選べるチート的先読みが可能になってしまうため
    （PR #45 で `random` を共有した際に発覚した設計上の欠陥）。
    """
    p0 = RandomPlayer("p0")
    p0.add_pokemon("ピカチュウ", move_names=["でんきショック"])
    p1 = RandomPlayer("p1")
    p1.add_pokemon("ゼニガメ", move_names=["みずでっぽう"])

    battle = Battle(p0, p1, seed=1)
    battle.start()

    sim = battle.build_observation(p0)

    assert sim.random is not battle.random
    assert sim.decision_random is battle.decision_random


def test_player_n_lost_battlesは対戦数から勝利数と引き分け数を引いた値():
    player = Player("p")
    player.n_finished_battles = 5
    player.n_won_battles = 2

    assert player.n_lost_battles == 3


def test_player_n_tied_battlesは常に0():
    player = Player("p")
    assert player.n_tied_battles == 0


def test_player_win_rateは勝利数を対戦数で割った値():
    player = Player("p")
    player.n_finished_battles = 4
    player.n_won_battles = 3

    assert player.win_rate == pytest.approx(0.75)


def test_player_win_rateは対戦数0のときゼロ除算にならず0を返す():
    player = Player("p")
    assert player.win_rate == 0.0


def test_pokemon_current_hpとcurrent_hp_fractionはhpとhp_fractionのエイリアス():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[Pokemon("ゼニガメ")],
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-10)

    assert mon.current_hp == mon.hp
    assert mon.current_hp_fraction == pytest.approx(mon.hp_fraction)


def test_pokemon_effectsはvolatilesのエイリアス():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[Pokemon("ゼニガメ")],
        volatile0={"こんらん": 3},
    )
    mon = battle.actives[0]

    assert "こんらん" in mon.effects
    assert mon.effects is mon.volatiles


def test_pokemon_first_turnは登場直後True行動後False():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["たいあたり"])],
        team1=[Pokemon("ゼニガメ")],
    )
    mon = battle.actives[0]

    assert mon.first_turn is True

    t.run_move(battle, player_idx=0)

    assert mon.first_turn is False


def test_pokemon_statusはailment_nameのエイリアス():
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[Pokemon("ゼニガメ")],
        ailment0=("やけど", None),
    )
    mon = battle.actives[0]

    assert mon.status == "やけど"
    assert mon.status == mon.ailment.name


def test_randomplayerが選ぶコマンドは常にget_available_commandsに含まれる():
    """RandomPlayer.choose_command() の戻り値が、選択時点の合法手
    （battle.get_available_commands()）に必ず含まれることを確認する。

    choose_command()の呼び出し前後で合法手が変化しないことを保証するため、
    RandomPlayerを継承したクラスで呼び出し直前の合法手を記録し、実際の対戦
    （battle.step()）を通じて検証する。
    """
    class _RecordingRandomPlayer(RandomPlayer):
        def __init__(self, username: str):
            super().__init__(username)
            self.checked: list[bool] = []

        def choose_command(self, battle: "Battle"):
            available = battle.available_commands(self)
            command = super().choose_command(battle)
            self.checked.append(command in available)
            return command

    p0 = _RecordingRandomPlayer("p0")
    p0.add_pokemon("ピカチュウ", move_names=["でんきショック", "でんこうせっか", "アイアンテール"])
    p1 = _RecordingRandomPlayer("p1")
    p1.add_pokemon("ゼニガメ", move_names=["みずでっぽう", "たいあたり"])

    battle = Battle(p0, p1, seed=1)
    battle.start()

    for _ in range(5):
        if battle.judge_winner() is not None:
            break
        battle.step()

    assert p0.checked and all(p0.checked)
    assert p1.checked and all(p1.checked)


def test_randomplayerは同じseedで対戦すると同じコマンド列を再現する():
    """RandomPlayer は battle.decision_random（Battle(seed=...) に紐づく行動選択専用の
    乱数系列）を使って選ぶため、同じseedで対戦を最初からやり直すと同じコマンド列
    （battle.command_log）を再現できることを確認する。グローバルなrandomモジュールに
    依存していればプロセス内の他の乱数消費と競合してこの再現性が崩れるため、
    battle.decision_random を使っている（＝Battle(seed=...)による再現性を壊さない）
    ことの検証になる。
    """
    def run(seed: int) -> list:
        p0 = RandomPlayer("p0")
        p0.add_pokemon("ピカチュウ", move_names=["でんきショック", "でんこうせっか", "アイアンテール"])
        p1 = RandomPlayer("p1")
        p1.add_pokemon("ゼニガメ", move_names=["みずでっぽう", "たいあたり"])

        battle = Battle(p0, p1, seed=seed)
        battle.start()
        for _ in range(5):
            if battle.judge_winner() is not None:
                break
            battle.step()
        return list(battle.command_log)

    log_a = run(12345)
    log_b = run(12345)

    assert log_a == log_b
    assert len(log_a) > 0


def test_stat_indexはhpからspeまでの6ステータスを網羅する():
    assert STAT_INDEX == {"hp": 0, "atk": 1, "def": 2, "spa": 3, "spd": 4, "spe": 5}


def test_stats_from_poke_envは欠けているキーを0扱いにする():
    assert stats_from_poke_env({"hp": 100}) == [100, 0, 0, 0, 0, 0]


def test_stats_from_poke_envは辞書をhp_atk_def_spa_spd_spe順のリストに変換する():
    d = {"hp": 100, "atk": 50, "def": 60, "spa": 70, "spd": 80, "spe": 90}
    assert stats_from_poke_env(d) == [100, 50, 60, 70, 80, 90]


@pytest.mark.parametrize(
    ("map_values", "literal_type"),
    [
        (set(TYPE_MAP.values()), Type),
        (set(STATUS_MAP.values()), AilmentName),
        (set(WEATHER_MAP.values()), WeatherName),
        (set(TERRAIN_MAP.values()), TerrainName),
        (set(GLOBAL_FIELD_MAP.values()), GlobalFieldName),
        (set(SIDE_CONDITION_MAP.values()), SideFieldName),
        (set(NATURE_MAP.values()), Nature),
    ]
)
def test_変換マップの値は対応するliteral型の値に含まれる(map_values: set[str], literal_type):
    assert map_values <= set(get_args(literal_type))


def test_無限交代ループの再現条件下でもコマンドが技を含んで決着する():
    """バグ報告の再現条件（3体チーム・両陣営RandomPlayer）で無限交代ループが解消し、
    技コマンドが実際に選ばれた上で規定ターン数以内に決着することを確認する
    （`.internal/api_feedback/pre_loop/04_sonnet_investigation.md` 4度目のレビュー指摘の回帰テスト）。

    修正前は `seed=1,2,3,5` で技コマンドが一度も選ばれないまま交代コマンドだけが
    ターン上限まで選ばれ続けた。
    """
    for seed in (1, 2, 3, 5):
        p0 = RandomPlayer("Team A")
        p0.add_pokemon("ピカチュウ", move_names=["かみなり"])
        p0.add_pokemon("ヒトカゲ", move_names=["かえんほうしゃ"])
        p0.add_pokemon("フシギダネ", move_names=["ギガドレイン"])

        p1 = RandomPlayer("Team B")
        p1.add_pokemon("ゼニガメ", move_names=["なみのり"])
        p1.add_pokemon("コラッタ", move_names=["すてみタックル"])
        p1.add_pokemon("ピッピ", move_names=["ムーンフォース"])

        battle = Battle(p0, p1, seed=seed)
        battle.start()

        max_turns = 30
        while not battle.finished and battle.turn < max_turns:
            battle.step()

        move_used = any(
            rec.command.is_move for rec in battle.command_log
        )
        assert move_used, f"seed={seed}: 技コマンドが一度も選ばれなかった"
        assert battle.finished, f"seed={seed}: {max_turns}ターン以内に決着しなかった"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
