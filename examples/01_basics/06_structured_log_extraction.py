"""構造化ログ（EventLog）から特定の種類のイベントだけを抽出する方法を扱う。

`print_logs()` / `get_log_lines()` は表示用に文字列化済みのログだが、
`get_event_logs(turn)` は LogCode 付きの EventLog をそのまま返すので、
プログラムで特定の種類のイベントだけを集計・抽出したいときに使う。
"""
from __future__ import annotations

from jpoke import Battle
from jpoke.enums import LogCode
from jpoke.players import RandomPlayer


def show_critical_hit_logs(battle: Battle) -> None:
    """急所に当たったログだけを抽出して表示する。

    リスト内包表記でも書けるが、ここでは何が繰り返されているか分かりやすいように
    普通の for 文で書く。
    """
    critical_hits: list[tuple[int, str, str | None]] = []

    # 1段目: 1ターン目から最終ターンまで、ターン番号を1つずつ見ていく
    for t in range(1, battle.turn + 1):
        # get_event_logs(t) は {Player: [EventLog, ...]} という辞書を返す。
        # .items() は辞書からキー（ここでは player）と値（ここでは logs）を
        # ペアで取り出すためのメソッド
        turn_logs = battle.get_event_logs(t)

        # 2段目: そのターンに行動した各プレイヤー（player）と、
        # そのプレイヤー側で発生したログのリスト（logs）を見ていく
        for player, logs in turn_logs.items():
            # 3段目: そのプレイヤー側で発生したログを1件ずつ見ていく
            for log in logs:
                if log.log is LogCode.CRITICAL_HIT:
                    critical_hits.append((t, player.username, log.pokemon))

    if critical_hits:
        print("急所に当たったログ:")
        for t, username, pokemon in critical_hits:
            print(f"  ターン{t} {username}側の{pokemon}")
    else:
        print("このseedでは急所は発生しなかった")


def show_logcode_variety() -> None:
    """LogCode にはこの他にも数十種類の値がある。代表的なものだけ紹介し、
    残りは一覧で確認する方法を示す。
    """
    print("代表的な LogCode:")
    print(f"  {LogCode.CRITICAL_HIT}: 急所に当たった")
    print(f"  {LogCode.ABILITY_TRIGGERED}: 特性が発動した")
    print(f"  {LogCode.AILMENT_APPLIED}: 状態異常が付与された")
    print(f"  {LogCode.HP_CHANGED}: HPが変化した")
    print(f"  {LogCode.MOVE_MISSED}: 技が外れた")

    # 全種類を確認したい場合は list(LogCode) で列挙できる
    print(f"\nLogCode は全部で{len(list(LogCode))}種類ある。全種類を確認するには:")
    print("  from jpoke.enums import LogCode")
    print("  for code in LogCode:")
    print("      print(code)")


def main() -> None:
    player1 = RandomPlayer("Team A")
    player1.add_pokemon("ピカチュウ", move_names=["かみなり"])
    player1.add_pokemon("ヒトカゲ", move_names=["かえんほうしゃ"])
    player1.add_pokemon("フシギダネ", move_names=["ギガドレイン"])

    player2 = RandomPlayer("Team B")
    player2.add_pokemon("ゼニガメ", move_names=["なみのり"])
    player2.add_pokemon("コラッタ", move_names=["すてみタックル"])
    player2.add_pokemon("ピッピ", move_names=["ムーンフォース"])

    battle = Battle(player1, player2, seed=1)
    battle.start()
    battle.play_out(max_turns=30)

    show_critical_hit_logs(battle)
    print("-" * 50)
    show_logcode_variety()

    # 試してみよう: LogCode.CRITICAL_HIT を別の LogCode（例: LogCode.ABILITY_TRIGGERED）に
    # 変えると、抽出できるイベントの種類がどう変わるか確認できる


if __name__ == "__main__":
    main()
