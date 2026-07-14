"""fuzz_battle.py のチーム生成・失敗レポート機能。

完全ランダムなポケモン・性別・性格・レベル・テラスタイプ・個体値・努力値・
特性・持ち物・技（1〜10個）で組んだパーティを生成し、バトル実行結果を
再現可能な形でレポートファイルに書き出す部分は行動選択の方策
（random / tree_search）に依存しないため、ここにまとめる。
方策の切り替えは fuzz_battle.py の --player 引数で行う。
"""

from __future__ import annotations

import os
import traceback
from dataclasses import dataclass, field
from functools import lru_cache, partial
from multiprocessing import Pool
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
_PACKAGE_ROOT = str(Path(__file__).resolve().parent.parent.parent / "src" / "jpoke")


@lru_cache(maxsize=None)
def _inducing_pools() -> tuple[list[str], list[str], list[str]]:
    """状態異常/揮発性状態/場の状態を誘発する特性・アイテム・技名のプールを返す
    （sorted済みのlist。frozenset由来だがhash順は再現性がないため、rng.choice/
    rng.sampleに渡す前に必ずsortして決定的な順序にする）。

    `effect_bias` が指定されたときのみ呼ばれる（`scripts/fuzz/effect_bias.py` の
    静的解析結果を遅延importする。fuzz_battle.py/replay_fuzz_battle.py は
    effect_bias=0.0 のまま使うためこの関数は呼ばれず、既存の挙動に影響しない）。
    """
    import effect_bias
    return (
        sorted(effect_bias.inducing_ability_names()),
        sorted(effect_bias.inducing_item_names()),
        sorted(effect_bias.inducing_move_names()),
    )


def _biased_choice(rng: Random, all_names: list[str], inducing_names: list[str],
                    effect_bias: float) -> str:
    """effect_biasの確率で誘発系プールから、それ以外はall_namesから一様に1つ選ぶ。

    effect_bias<=0またはinducing_namesが空の場合は必ず `rng.choice(all_names)` の
    1回のみを呼ぶ（既存スクリプトと完全に同じrng消費・同じ挙動になる）。
    """
    if inducing_names and effect_bias > 0 and rng.random() < effect_bias:
        return rng.choice(inducing_names)
    return rng.choice(all_names)


def _biased_move_sample(rng: Random, move_names: list[str], inducing_moves: list[str],
                         n_moves: int, effect_bias: float) -> list[str]:
    """技をn_moves個、重複なく選ぶ。effect_bias>0のとき、誘発系の技プールから
    優先的に選ばれる技の数を確率的に増やす。

    effect_bias<=0またはinducing_movesが空の場合は `rng.sample(move_names, n_moves)`
    の1回のみを呼ぶ（既存スクリプトと完全に同じrng消費・同じ挙動になる）。
    """
    if not inducing_moves or effect_bias <= 0:
        return rng.sample(move_names, n_moves)

    pool_size = min(n_moves, len(inducing_moves))
    n_biased = min(sum(1 for _ in range(n_moves) if rng.random() < effect_bias), pool_size)

    biased = rng.sample(inducing_moves, n_biased) if n_biased else []
    remaining_pool = [m for m in move_names if m not in biased]
    remaining = rng.sample(remaining_pool, n_moves - n_biased)

    result = biased + remaining
    rng.shuffle(result)
    return result


def random_team_spec(rng: Random, n_pokemon: int = 6, effect_bias: float = 0.0) -> list[dict]:
    """ランダムな6匹分のポケモン構成（種族・性別・性格・レベル・テラスタイプ・
    個体値・努力値・特性・持ち物・技）を生成する。技数は1〜MAX_MOVES匹ごとにランダム。

    Args:
        effect_bias: 0.0〜1.0。0より大きい場合、状態異常・揮発性状態・場の状態を
            誘発する特性・持ち物・技（`scripts/fuzz/effect_bias.py` が
            `src/jpoke/handlers`・`src/jpoke/data` の実装を静的解析して機械的に
            判定した集合）が選ばれる確率を高める。fuzz_log_battle.py 専用のオプトイン
            引数で、既定値0.0では一切影響せず、fuzz_battle.py・replay_fuzz_battle.py
            の既存の再現性（同じseedに対する完全に同一のチーム生成）を変更しない。
    """
    pokemon_names = list(POKEDEX.keys())
    ability_names = list(ABILITIES.keys())
    item_names = list(ITEMS.keys())
    # "_"始まりはこんらん自傷などエンジン内部専用の技で、実際のポケモンは覚えられない
    move_names = [name for name in MOVES if not name.startswith("_")]

    inducing_abilities: list[str] = []
    inducing_items: list[str] = []
    inducing_moves: list[str] = []
    if effect_bias > 0:
        inducing_abilities, inducing_items, inducing_moves = _inducing_pools()

    specs = []
    for _ in range(n_pokemon):
        n_moves = rng.randint(1, min(MAX_MOVES, len(move_names)))
        specs.append({
            "name": rng.choice(pokemon_names),
            "gender": rng.choice(GENDERS),
            "nature": rng.choice(NATURES),
            "level": rng.randint(1, 100),
            "tera_type": rng.choice(TERA_TYPES),
            "ivs": [rng.randint(0, 31) for _ in range(6)],
            "evs": [rng.randint(0, 32) for _ in range(6)],  # チャンピオンズ仕様（0~32刻み、合計制限なし）
            "ability": _biased_choice(rng, ability_names, inducing_abilities, effect_bias),
            "item": _biased_choice(rng, item_names, inducing_items, effect_bias),
            "moves": _biased_move_sample(rng, move_names, inducing_moves, n_moves, effect_bias),
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
        mon.set_ivs(s["ivs"])
        mon.set_evs(s["evs"], hp_policy="reset")  # 新規構築なので満タンにする
        team.append(mon)
    return team


def format_full_log(battle: Battle) -> str:
    """battle.print_logs() と同じ整形ロジックで、全ターン分のログをテキスト化する。"""
    lines = []
    for log in battle.event_logger.logs:
        player = battle.players[log.idx]
        lines.append(f"Turn {log.turn} : {player.username} : {log.pokemon or ''} : {log.render()}")
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
            f"テラス:{mon['tera_type']} 個体値:{mon['ivs']} 努力値:{mon['evs']}) "
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


def parallel_search(run_fn: Callable[..., FuzzResult],
                     start_seed: int,
                     count: int,
                     workers: int | None = None,
                     **kwargs) -> list[FuzzResult]:
    """start_seed から count 件分のシードを worker プロセスに分散して実行し、
    失敗した結果を seed 昇順で全て返す（打ち切らず必ず count 件すべて実行する）。
    """
    seeds = range(start_seed, start_seed + count)
    if workers is None:
        workers = min(count, os.cpu_count() or 4)
    worker = partial(run_fn, **kwargs)
    with Pool(workers) as pool:
        results = pool.map(worker, seeds)
    return [r for r in results if not r.ok]
