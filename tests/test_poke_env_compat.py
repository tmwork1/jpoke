"""poke-env 互換化（docs/poke-env/compat_plan.md）のクロスカッティングなテスト。

Phase 3（property追加）・Phase 4（変換テーブル）・Phase 5（`Player.battle_against`）を対象とする。
特定の特性・技・アイテムに紐づかない横断的な互換性テストのため、トップレベルに配置する。
"""
from typing import get_args

import pytest

from jpoke.core import Player
from jpoke.core.player import MAX_TURNS
from jpoke.model import Pokemon, Move
from jpoke.types import (
    AilmentName, GlobalFieldName, Nature, SideFieldName, TerrainName, Type, WeatherName,
)
from jpoke.types.poke_env import (
    GLOBAL_FIELD_MAP, NATURE_MAP, SIDE_CONDITION_MAP, STATUS_MAP, STAT_INDEX,
    TERRAIN_MAP, TYPE_MAP, WEATHER_MAP, evs_from_poke_env, stats_from_poke_env,
)

from . import test_utils as t
import jpoke.core.player as player_module

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
        n_selected=1, accuracy_fix_threshold=0, damage_roll="最小",
        mega_evolution=False, terastal=False,
    )

    assert winner.n_finished_battles == 3
    assert winner.n_won_battles == 3
    assert loser.n_finished_battles == 3
    assert loser.n_won_battles == 0


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
        n_selected=1, accuracy_fix_threshold=0, damage_roll="最小",
        mega_evolution=False, terastal=False,
    )

    assert winner.n_finished_battles == 1
    assert winner.n_won_battles == 1
    assert winner.win_rate == pytest.approx(1.0)
    assert loser.n_finished_battles == 1
    assert loser.n_won_battles == 0
    assert loser.n_lost_battles == 1


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


def test_battle_finishedとwonとlostは決着後に更新される():
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス", level=100, move_names=["じしん"])],
        team1=[Pokemon("コイキング", level=1, move_names=["はねる"])],
        accuracy=100,
        damage_roll="最小",
    )
    player0, player1 = battle.players

    assert battle.finished is False
    assert battle.won(player0) is False
    assert battle.lost(player0) is False

    t.run_move(battle, atk_idx=0)

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

    t.run_move(battle, atk_idx=0)

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
