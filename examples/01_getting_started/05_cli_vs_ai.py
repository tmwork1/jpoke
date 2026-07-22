"""CLIPlayer とAIを対戦させるスクリプト。

`python examples/01_getting_started/05_cli_vs_ai.py` で実行し、標準入力から
コマンドを入力しながらAI（`jpoke.players.MaxDamagePlayer`、最大ダメージの技を
選ぶだけの単純な方策）相手に対戦できる。標準入力を使う対話型のサンプルのため、
他の01_getting_started配下と異なりColab非対応（.ipynbではなく.py）。
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
