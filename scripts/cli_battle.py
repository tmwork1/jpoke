"""CLIPlayer でAI相手に対話的に対戦するスクリプト。

`python scripts/cli_battle.py` で実行し、選出・行動コマンドの入力を
標準入力から求められる。相手は `MaxDamagePlayer`（最大ダメージ技を選ぶ
だけの単純なAI）。
"""
from __future__ import annotations

from jpoke import Battle
from jpoke.players import CLIPlayer, MaxDamagePlayer


def build_teams() -> tuple[CLIPlayer, MaxDamagePlayer]:
    """デモ用の3vs3チームを構築する。"""
    human = CLIPlayer("あなた")
    human.add_pokemon("ピカチュウ", moves=["でんこうせっか", "かみなり", "でんじは"])
    human.add_pokemon("フシギダネ", moves=["たいあたり", "やどりぎのタネ"])
    human.add_pokemon("ゼニガメ", moves=["みずでっぽう", "からにこもる"])

    ai = MaxDamagePlayer("AI")
    ai.add_pokemon("ヒトカゲ", moves=["ひのこ", "ひっかく"])
    ai.add_pokemon("コラッタ", moves=["たいあたり", "でんこうせっか"])
    ai.add_pokemon("ポッポ", moves=["つつく", "かぜおこし"])

    return human, ai


def main() -> None:
    human, ai = build_teams()
    battle = Battle(human, ai, n_selected=2, seed=1)
    battle.play_out(max_turns=100)

    print("=" * 50)
    if battle.winner is None:
        print("結果: 引き分け（ターン上限）")
    else:
        print(f"結果: {battle.winner.username} の勝利！")
    print("=" * 50)
    battle.print_logs("all")


if __name__ == "__main__":
    main()
