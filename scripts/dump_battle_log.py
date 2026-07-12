"""fuzz_battle.py と同じ手順（シード付き完全ランダムパーティ・RandomPlayer/
TreeSearchFuzzPlayer）で1バトルを実行し、成功・失敗を問わずチーム構成と
全ターンのバトルログをファイルに書き出すスクリプト。

fuzz_battle.py は未捕捉例外が出た場合のみレポートを書き出すが、こちらは
「例外は出ないが挙動がおかしい」ケースをサブエージェントにログレビューさせる
用途のため、正常終了時も含めて常にログを書き出す。

使い方:
    python scripts/dump_battle_log.py --seed 12345
    python scripts/dump_battle_log.py --seed 12345 --player tree_search --max-plies 1
    python scripts/dump_battle_log.py --seed 12345 --out .loop/log_review/seed_12345.log
"""
from __future__ import annotations

import argparse
from pathlib import Path
from random import Random

from jpoke import Battle

from fuzz_battle import PLAYER_DEFAULTS, _make_players
from fuzz_common import build_team, format_full_log, format_team, random_team_spec

_ROOT = Path(__file__).resolve().parent.parent


def run_and_dump(seed: int,
                  player_kind: str = "random",
                  max_turns: int = 100,
                  n_pokemon: int = 6,
                  max_plies: int = 1) -> str:
    """指定シードで1バトルを実行し、チーム構成・結果・全ターンログを整形して返す。"""
    master = Random(seed)
    team_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    decision_rngs = [Random(master.randrange(2**31)) for _ in range(2)]
    n_selected = master.randint(1, n_pokemon)

    team_specs = [random_team_spec(r, n_pokemon) for r in team_rngs]

    players = _make_players(player_kind, decision_rngs, max_plies)
    for player, spec in zip(players, team_specs):
        player.team = build_team(spec)

    battle = Battle(*players, n_selected=n_selected, seed=seed)

    battle.start()
    while battle.judge_winner() is None and battle.turn < max_turns:
        battle.step()

    winner = battle.judge_winner()

    parts = [
        f"seed: {seed}",
        f"player: {player_kind}",
        f"n_selected（seedから自動決定）: {n_selected}",
        f"終了ターン: {battle.turn}",
        f"勝者: {winner.username if winner else '（決着つかず）'}",
        "",
        "== Player1 team ==",
        format_team(team_specs[0]),
        "",
        "== Player2 team ==",
        format_team(team_specs[1]),
        "",
        "== battle log ==",
        format_full_log(battle),
    ]
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True, help="バトルのシード")
    parser.add_argument("--player", choices=list(PLAYER_DEFAULTS), default="random",
                        help="行動選択の方策（既定: random）")
    parser.add_argument("--max-turns", type=int, default=None,
                        help="1バトルの最大ターン数（既定はプレイヤーモデル依存）")
    parser.add_argument("--n-pokemon", type=int, default=None,
                        help="1チームの匹数（既定はプレイヤーモデル依存）")
    parser.add_argument("--max-plies", type=int, default=1,
                        help="木探索の先読み手数（player=tree_search のときのみ有効）")
    parser.add_argument("--out", type=str, default=None,
                        help="出力先ファイルパス（省略時は標準出力）")
    args = parser.parse_args()

    defaults = PLAYER_DEFAULTS[args.player]
    max_turns = args.max_turns if args.max_turns is not None else defaults["max_turns"]
    n_pokemon = args.n_pokemon if args.n_pokemon is not None else defaults["n_pokemon"]

    text = run_and_dump(
        args.seed, player_kind=args.player,
        max_turns=max_turns, n_pokemon=n_pokemon, max_plies=args.max_plies,
    )

    if args.out:
        out_path = _ROOT / args.out if not Path(args.out).is_absolute() else Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print(f"wrote: {out_path}")
    else:
        print(text)


if __name__ == "__main__":
    main()
