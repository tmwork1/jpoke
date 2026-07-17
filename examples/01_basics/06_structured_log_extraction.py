"""LogCode の種類を確認する方法を扱う。

`print_logs()` / `get_log_lines()` は表示用に文字列化済みのログだが、プログラムで
特定の種類のイベントだけを集計・抽出したい場合は `battle.get_event_logs(turn)` が
返す LogCode 付きの EventLog を見る。
"""
from __future__ import annotations

from jpoke import Battle
from jpoke.enums import LogCode
from jpoke.players import RandomPlayer


def show_logcode_variety() -> None:
    """LogCode には数十種類の値がある。代表的なものだけ紹介し、残りは一覧で確認する
    方法を示す。
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
    player2 = RandomPlayer("Team B")
    player2.add_pokemon("ゼニガメ", move_names=["なみのり"])

    battle = Battle(player1, player2, seed=1)
    battle.start()
    battle.play_out(max_turns=30)

    show_logcode_variety()

    # 試してみよう: battle.get_event_logs(1) を呼び、返ってくる EventLog の
    # .log（LogCode）や .pokemon を確認すると、構造化ログの中身を具体的に観察できる


if __name__ == "__main__":
    main()
