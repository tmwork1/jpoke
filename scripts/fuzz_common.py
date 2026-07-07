"""fuzz_battle.py のチーム生成・失敗レポート機能。

完全ランダムなポケモン・性別・性格・レベル・テラスタイプ・個体値・努力値・
特性・持ち物・技（1〜10個）で組んだパーティを生成し、バトル実行結果を
再現可能な形でレポートファイルに書き出す部分は行動選択の方策
（random / tree_search）に依存しないため、ここにまとめる。
方策の切り替えは fuzz_battle.py の --player 引数で行う。
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from pathlib import Path
from random import Random
from typing import Callable
from typing import get_args

from jpoke import Battle, Pokemon
from jpoke.data.pokedex import POKEDEX
from jpoke.data.ability import ABILITIES
from jpoke.data.item import ITEMS
from jpoke.data.move import MOVES
from jpoke.types import Gender, Nature, Type

GENDERS = list(get_args(Gender))
NATURES = list(get_args(Nature))
TERA_TYPES = [t for t in get_args(Type) if t]
MAX_MOVES = 10

# src/jpoke 配下のファイルのみを signature 算出の対象にする
# （呼び出し元スクリプト自身や標準ライブラリのフレームは原因箇所として扱わない）
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
        mon.set_indiv(s["indiv"])
        mon.set_effort(s["effort"], hp_policy="reset")  # 新規構築なので満タンにする
        team.append(mon)
    return team


def format_full_log(battle: Battle) -> str:
    """battle.print_logs() と同じ整形ロジックで、全ターン分のログをテキスト化する。"""
    lines = []
    for log in battle.event_logger.logs:
        player = battle.players[log.idx]
        pokemon = getattr(log.payload, "pokemon", "") if log.payload else ""
        lines.append(f"Turn {log.turn} : {player.name} : {pokemon} : {log.render()}")
    return "\n".join(lines)


def failure_signature(exc: Exception) -> str:
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


def format_team(spec: list[dict]) -> str:
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


def write_failure_report(result: FuzzResult, failure_dir: Path, repro_cmd: str) -> Path:
    """失敗結果を再現可能な形でレポートファイルに書き出す（.log は git 管理外）。"""
    failure_dir.mkdir(parents=True, exist_ok=True)
    path = failure_dir / f"seed_{result.seed}.log"

    parts = [
        f"再現コマンド: {repro_cmd}",
        f"signature: {result.signature}",
        f"n_selected（seedから自動決定）: {result.n_selected}",
        f"failed at turn: {result.turn}",
        "",
        "== Player1 team ==",
        format_team(result.teams[0]),
        "",
        "== Player2 team ==",
        format_team(result.teams[1]),
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


def search(run_fn: Callable[..., FuzzResult],
           start_seed: int,
           count: int,
           **kwargs) -> FuzzResult | None:
    """start_seed から count 件分シードを進めて run_fn を実行し、
    最初の失敗を返す（全部okならNone）。
    """
    for seed in range(start_seed, start_seed + count):
        result = run_fn(seed, **kwargs)
        if not result.ok:
            return result
    return None
