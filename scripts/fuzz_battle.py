"""
完全ランダムなポケモン・性別・性格・レベル・テラスタイプ・個体値・努力値・
特性・持ち物・技（1〜10個）で組んだパーティ同士を戦わせ、未捕捉例外を検出する
バグ出し用スクリプト。

乱数シード（int）1つだけで、チーム構成・選出数・選出・行動選択まで完全に再現できる。

使い方:
    # 単発再現モード
    python scripts/fuzz_battle.py --seed 12345

    # バッチ探索モード（失敗が出るまでシードを進める）
    python scripts/fuzz_battle.py --search --start-seed 0 --count 200
"""

from __future__ import annotations

import argparse
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from random import Random
from typing import get_args

from jpoke import Battle, Player, Pokemon
from jpoke.data.pokedex import POKEDEX
from jpoke.data.ability import ABILITIES
from jpoke.data.item import ITEMS
from jpoke.data.move import MOVES
from jpoke.enums import Command
from jpoke.types import Gender, Nature, Type

GENDERS = list(get_args(Gender))
NATURES = list(get_args(Nature))
TERA_TYPES = [t for t in get_args(Type) if t]
MAX_MOVES = 10

FAILURE_DIR = Path(__file__).resolve().parent.parent / ".loop" / "fuzz_failures"

# src/jpoke 配下のファイルのみを signature 算出の対象にする
# （fuzz_battle.py 自身や標準ライブラリのフレームは原因箇所として扱わない）
_PACKAGE_ROOT = str(Path(__file__).resolve().parent.parent / "src" / "jpoke")


def random_team_spec(rng: Random, n_pokemon: int = 6) -> list[dict]:
    """ランダムな6匹分のポケモン構成（種族・性別・性格・レベル・テラスタイプ・
    個体値・努力値・特性・持ち物・技）を生成する。技数は1〜MAX_MOVES匹ごとにランダム。
    """
    pokemon_names = list(POKEDEX.keys())
    ability_names = list(ABILITIES.keys())
    item_names = list(ITEMS.keys())
    # "_"始まりはこんらん自傷などエンジン内部専用の技で、実際のポケモンは覚えられない
    move_names = [name for name in MOVES if not name.startswith("_")]

    specs = []
    for _ in range(n_pokemon):
        n_moves = rng.randint(1, min(MAX_MOVES, len(move_names)))
        specs.append({
            "name": rng.choice(pokemon_names),
            "gender": rng.choice(GENDERS),
            "nature": rng.choice(NATURES),
            "level": rng.randint(1, 100),
            "tera_type": rng.choice(TERA_TYPES),
            "indiv": [rng.randint(0, 31) for _ in range(6)],
            "effort": [rng.randint(0, 32) for _ in range(6)],  # チャンピオンズ仕様（0~32刻み、合計制限なし）
            "ability": rng.choice(ability_names),
            "item": rng.choice(item_names),
            "moves": rng.sample(move_names, n_moves),
        })
    return specs


def build_team(spec: list[dict]) -> list[Pokemon]:
    """team spec から Pokemon インスタンスのリストを構築する。"""
    team = []
    for s in spec:
        mon = Pokemon(
            s["name"],
            gender=s["gender"],
            nature=s["nature"],
            level=s["level"],
            ability_name=s["ability"],
            item_name=s["item"],
            move_names=s["moves"],
            tera_type=s["tera_type"],
        )
        mon.indiv = s["indiv"]
        mon.effort = s["effort"]
        mon.update_stats()
        mon.hp = mon.max_hp
        team.append(mon)
    return team


class RandomPlayer(Player):
    """自前の乱数生成器で選出・行動をランダムに選ぶプレイヤー。

    battle.random は choose_selection/choose_command 呼び出し時点で
    deepcopy された Observation のものであり、実バトルの乱数列とは
    別物に分岐してしまうため使わない（シードからの再現性が壊れる）。
    """

    def __init__(self, name: str, rng: Random):
        super().__init__(name)
        self.rng = rng

    def choose_selection(self, battle: Battle) -> list[int]:
        n = min(battle.n_selected, len(self.team))
        return self.rng.sample(range(len(self.team)), n)

    def choose_command(self, battle: Battle) -> Command:
        commands = battle.get_available_commands(self)
        return self.rng.choice(commands)


def format_full_log(battle: Battle) -> str:
    """battle.print_logs() と同じ整形ロジックで、全ターン分のログをテキスト化する。"""
    lines = []
    for log in battle.event_logger.logs:
        player = battle.players[log.idx]
        pokemon = log.payload.get("pokemon", "") if log.payload else ""
        lines.append(f"Turn {log.turn} : {player.name} : {pokemon} : {log.render()}")
    return "\n".join(lines)


def _failure_signature(exc: Exception) -> str:
    """例外の重複判定用シグネチャを作る（src/jpoke 配下で最も深いフレームを使う）。"""
    frames = [
        f for f in traceback.extract_tb(exc.__traceback__)
        if f.filename.startswith(_PACKAGE_ROOT)
    ]
    frame = frames[-1] if frames else traceback.extract_tb(exc.__traceback__)[-1]
    rel_file = Path(frame.filename).name
    return f"{type(exc).__name__}@{rel_file}:{frame.name}:{frame.lineno}"


@dataclass
class FuzzResult:
    seed: int
    ok: bool
    turn: int = 0
    winner: str | None = None
    n_selected: int = 3
    max_turns: int = 100
    n_pokemon: int = 6
    teams: list[list[dict]] = field(default_factory=list)
    error: str | None = None
    signature: str | None = None
    traceback_text: str | None = None
    log_text: str | None = None


def run_fuzz_battle(seed: int,
                     max_turns: int = 100,
                     n_pokemon: int = 6) -> FuzzResult:
    """指定シードで1バトルを実行する。未捕捉例外を検知して結果にまとめる。

    選出数（n_selected、1〜n_pokemon）・各匹の技数（1〜MAX_MOVES）を含め、
    チーム構成は全てシードから決まる（CLI 引数では指定しない＝seedだけで完全に再現できる）。
    """
    master = Random(seed)
    team_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    decision_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    n_selected = master.randint(1, n_pokemon)

    team_specs = [random_team_spec(r, n_pokemon) for r in team_rngs]

    players = [RandomPlayer(f"Player{i + 1}", decision_rngs[i]) for i in range(2)]
    for player, spec in zip(players, team_specs):
        player.team = build_team(spec)

    battle = Battle(tuple(players), n_selected=n_selected, seed=seed)

    try:
        battle.start()
        while battle.judge_winner() is None and battle.turn < max_turns:
            battle.step()
    except Exception as e:
        return FuzzResult(
            seed=seed, ok=False, turn=battle.turn,
            n_selected=n_selected, max_turns=max_turns,
            n_pokemon=n_pokemon,
            teams=team_specs,
            error=f"{type(e).__name__}: {e}",
            signature=_failure_signature(e),
            traceback_text=traceback.format_exc(),
            log_text=format_full_log(battle),
        )

    winner = battle.judge_winner()
    return FuzzResult(
        seed=seed, ok=True, turn=battle.turn,
        winner=winner.name if winner else None,
        n_selected=n_selected, max_turns=max_turns,
        n_pokemon=n_pokemon,
        teams=team_specs,
    )


def _format_team(spec: list[dict]) -> str:
    lines = []
    for mon in spec:
        moves = "・".join(mon["moves"])
        gender = mon["gender"] or "不明"
        lines.append(
            f"  - {mon['name']} (性別:{gender} 性格:{mon['nature']} Lv{mon['level']} "
            f"テラス:{mon['tera_type']} 個体値:{mon['indiv']} 努力値:{mon['effort']}) "
            f"特性:{mon['ability']} 持ち物:{mon['item']} 技:{moves}"
        )
    return "\n".join(lines)


def write_failure_report(result: FuzzResult) -> Path:
    """失敗結果を再現可能な形でレポートファイルに書き出す（.log は git 管理外）。"""
    FAILURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FAILURE_DIR / f"seed_{result.seed}.log"

    repro_cmd = (
        f"python scripts/fuzz_battle.py --seed {result.seed} "
        f"--max-turns {result.max_turns} --n-pokemon {result.n_pokemon}"
    )

    parts = [
        f"再現コマンド: {repro_cmd}",
        f"signature: {result.signature}",
        f"n_selected（seedから自動決定）: {result.n_selected}",
        f"failed at turn: {result.turn}",
        "",
        "== Player1 team ==",
        _format_team(result.teams[0]),
        "",
        "== Player2 team ==",
        _format_team(result.teams[1]),
        "",
        "== error ==",
        result.error or "",
        "",
        "== traceback ==",
        result.traceback_text or "",
        "",
        "== battle log ==",
        result.log_text or "",
    ]

    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def search(start_seed: int, count: int, **kwargs) -> FuzzResult | None:
    """start_seed から count 件分シードを進めて実行し、最初の失敗を返す（全部okならNone）。"""
    for seed in range(start_seed, start_seed + count):
        result = run_fuzz_battle(seed, **kwargs)
        if not result.ok:
            return result
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, help="単発再現モードのシード")
    parser.add_argument("--search", action="store_true", help="バッチ探索モード")
    parser.add_argument("--start-seed", type=int, default=0, help="探索開始シード")
    parser.add_argument("--count", type=int, default=100, help="探索するバトル数")
    parser.add_argument("--max-turns", type=int, default=100)
    parser.add_argument("--n-pokemon", type=int, default=6)
    args = parser.parse_args()

    kwargs = dict(
        max_turns=args.max_turns,
        n_pokemon=args.n_pokemon,
    )

    if args.search:
        result = search(args.start_seed, args.count, **kwargs)
        if result is None:
            print(f"OK: {args.count}件すべて成功（seed {args.start_seed}〜{args.start_seed + args.count - 1}）")
            sys.exit(0)
        path = write_failure_report(result)
        print(f"FAIL: seed={result.seed} signature={result.signature}")
        print(f"report: {path}")
        sys.exit(1)

    if args.seed is None:
        parser.error("--seed か --search のいずれかを指定してください。")

    result = run_fuzz_battle(args.seed, **kwargs)
    if result.ok:
        print(f"OK: seed={result.seed} turn={result.turn} winner={result.winner}")
        sys.exit(0)

    path = write_failure_report(result)
    print(f"FAIL: seed={result.seed} signature={result.signature}")
    print(result.error)
    print(f"report: {path}")
    sys.exit(1)


if __name__ == "__main__":
    main()
