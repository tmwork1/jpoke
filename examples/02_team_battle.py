"""jpoke で学べること: 3体チーム・複数選出・複数ターンにわたるバトルの進め方。

n_selected=3 で3体を選出し、瀕死になったポケモンが交代コマンドで控えと入れ替わる様子を
ターンごとに battle.print_logs() で確認しながら決着まで進める。先頭のポケモンが瀕死になると、
以降のターンでは自動的に控えへの交代コマンドが要求される。両陣営とも RandomPlayer を使うため、
交代コマンドの選択肢が複数あるときはランダムに選ばれる。
"""
from __future__ import annotations

from jpoke import Battle
from jpoke.enums import LogCode
from jpoke.players import RandomPlayer


# TODO: 技名を入力するときにひらがなも受け付けると、型ヒントの予測変換が効きやすくて親切かもしれない（例: "ぎがどれいん" → "ギガドレイン"）

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

    # print_logs/get_log_lines は文字列化済みログだが、get_event_logs(turn) は
    # LogCode付きの構造化ログ（EventLog）をそのまま返す。特定の種類のイベント
    # （ここでは急所発生）だけをプログラムで抽出したい場合に使う
    print("-" * 50)
    critical_hits = [
        (t, player.username, log.pokemon)
        for t in range(1, battle.turn + 1)
        for player, logs in battle.get_event_logs(t).items()
        for log in logs
        if log.log is LogCode.CRITICAL_HIT
    ]
    if critical_hits:
        print("急所に当たったログ:")
        for t, username, pokemon in critical_hits:
            print(f"  ターン{t} {username}側の{pokemon}")
    else:
        print("このseedでは急所は発生しなかった")

    # 試してみよう: player1/player2 のチーム構成や技を変えて、
    # どのポケモンが先に瀕死になり交代が起きるか観察できる


if __name__ == "__main__":
    main()
