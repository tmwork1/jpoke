"""jpoke で学べること: 3体チーム・複数選出・複数ターンにわたるバトルの進め方。

n_selected=3 で3体を選出し、瀕死になったポケモンが交代コマンドで控えと入れ替わる様子を
ターンごとに battle.print_logs() で確認しながら決着まで進める。先頭のポケモンが瀕死になると、
以降のターンでは自動的に控えへの交代コマンドが要求される。両陣営とも RandomPlayer を使うため、
交代コマンドの選択肢が複数あるときはランダムに選ばれる。
"""
from __future__ import annotations

from jpoke import Battle
from jpoke.players import RandomPlayer


def main() -> None:
    player1 = RandomPlayer("Team A")
    player1.add_pokemon("ピカチュウ", move_names=["かみなり"])
    player1.add_pokemon("ヒトカゲ", move_names=["かえんほうしゃ"])
    player1.add_pokemon("フシギダネ", move_names=["ギガドレイン"])

    player2 = RandomPlayer("Team B")
    player2.add_pokemon("ゼニガメ", move_names=["なみのり"])
    player2.add_pokemon("コラッタ", move_names=["すてみタックル"])
    player2.add_pokemon("ピッピ", move_names=["ムーンフォース"])

    # n_selected: 省略時は min(3, チームの手持ち数) が自動設定される（ここでは3）
    battle = Battle(player1, player2, seed=1)
    battle.start()

    max_turns = 30
    # TODO: battle.finished(max_turn=30)のように、ターン上限を指定してfinished判定できるようにする
    while not battle.finished and battle.turn < max_turns:
        battle.step()
        battle.print_logs()
        print("-" * 50)

    winner = battle.winner
    print(f"勝者: {winner.username if winner else '引き分け（ターン上限）'}")

    # 試してみよう: player1/player2 のチーム構成や技を変えて、
    # どのポケモンが先に瀕死になり交代が起きるか観察できる


if __name__ == "__main__":
    main()
