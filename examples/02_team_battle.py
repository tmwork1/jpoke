"""jpoke で学べること: 3体チーム・複数選出・複数ターンにわたるバトルの進め方。

n_selected=3 で3体を選出し、瀕死になったポケモンが交代コマンドで控えと入れ替わる様子を
ターンごとに battle.print_logs() で確認しながら決着まで進める。
"""
from __future__ import annotations

from jpoke import Battle, Player, Pokemon


def main() -> None:
    player1 = Player("Team A")
    player1.team = [
        Pokemon("ピカチュウ", move_names=["かみなり"]),
        Pokemon("ヒトカゲ", move_names=["かえんほうしゃ"]),
        Pokemon("フシギダネ", move_names=["つるのムチ"]),
    ]

    player2 = Player("Team B")
    player2.team = [
        Pokemon("ゼニガメ", move_names=["ハイドロポンプ"]),
        Pokemon("コラッタ", move_names=["たいあたり"]),
        Pokemon("カビゴン", move_names=["のしかかり"]),
    ]

    # n_selected: 3体チームすべてを選出する
    battle = Battle((player1, player2), n_selected=3, seed=1)
    battle.start()

    max_turns = 30
    while battle.judge_winner() is None and battle.turn < max_turns:
        battle.step()
        # このターンのログを表示（先頭のポケモンが瀕死になると、以降のターンでは
        # 自動的に控えへの交代コマンドが要求される。既定の Player.choose_command()
        # は利用可能なコマンドの先頭を選ぶだけなので、交代も自動的に処理される）
        battle.print_logs()
        print("-" * 50)

    winner = battle.judge_winner()
    if winner is None:
        print(f"結果: 決着つかず（{max_turns}ターン経過）")
    else:
        print(f"結果: {winner.username} 勝利（{battle.turn}ターン）")


if __name__ == "__main__":
    main()
