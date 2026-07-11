"""jpoke で学べること: 3体チーム・複数選出・複数ターンにわたるバトルの進め方。

n_selected=3 で3体を選出し、瀕死になったポケモンが交代コマンドで控えと入れ替わる様子を
ターンごとに battle.print_logs() で確認しながら決着まで進める。先頭のポケモンが瀕死になると、
以降のターンでは自動的に控えへの交代コマンドが要求される。既定の Player.choose_command() は
利用可能なコマンドの先頭を選ぶだけなので、交代も自動的に処理される。
"""
from __future__ import annotations

# TODO: RandomPlayer を使う。
from jpoke import Battle, Player


# TODO: 技名を入力するときにひらがなも受け付けると、型ヒントの予測変換が効きやすくて親切かもしれない（例: "ぎがどれいん" → "ギガドレイン"）

def main() -> None:
    player1 = Player("Team A")
    player1.add_pokemon("ピカチュウ", move_names=["かみなり"])
    player1.add_pokemon("ヒトカゲ", move_names=["かえんほうしゃ"])
    player1.add_pokemon("フシギダネ", move_names=["ギガドレイン"])

    player2 = Player("Team B")
    player2.add_pokemon("ゼニガメ", move_names=["なみのり"])
    player2.add_pokemon("コラッタ", move_names=["すてみタックル"])
    player2.add_pokemon("ピッピ", move_names=["ムーンフォース"])

    # n_selected: 省略時は min(3, チームの手持ち数) が自動設定される（ここでは3）
    battle = Battle((player1, player2), seed=1)
    battle.start()

    max_turns = 30
    while not battle.finished and battle.turn < max_turns:
        battle.step()
        # このターンのログを表示
        battle.print_logs()
        print("-" * 50)

    winner = battle.winner
    if winner is None:
        print(f"結果: 決着つかず（{max_turns}ターン経過）")
    else:
        print(f"結果: {winner.username} 勝利（{battle.turn}ターン）")

    # 試してみよう: player1/player2 のチーム構成や技を変えて、
    # どのポケモンが先に瀕死になり交代が起きるか観察できる


if __name__ == "__main__":
    main()
