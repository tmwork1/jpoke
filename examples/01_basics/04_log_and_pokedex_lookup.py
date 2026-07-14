"""jpoke で学べること: 構造化ログからの特定イベント抽出、ポケモンが持てる特性の確認。

03の3体チームバトルと同じ対戦を題材に、対戦後の調べ物によく使う2つの手段を示す。
"""
# TODO: POKEDX の使い方だけでひとつのサンプルにまとめる
# TODO: LogCode の使い方も単一のサンプルにして、すべての LogCode を列挙して説明する

from __future__ import annotations

from jpoke import Battle
from jpoke.data import POKEDEX
from jpoke.enums import LogCode
from jpoke.players import RandomPlayer


def show_critical_hit_logs(battle: Battle) -> None:
    """print_logs/get_log_lines は文字列化済みログだが、get_event_logs(turn) は
    LogCode付きの構造化ログ（EventLog）をそのまま返す。特定の種類のイベント
    （ここでは急所発生）だけをプログラムで抽出したい場合に使う。
    """
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


def show_pokedex_abilities() -> None:
    """ポケモンごとに持てる特性は POKEDEX[name].abilities で確認できる
    （通常特性1・2・隠れ特性の順）。ability_name を省略しても特性は自動設定されず、
    空文字のままになる点に注意。
    """
    print(f"ライチュウが持てる特性: {POKEDEX['ライチュウ'].abilities}")


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
    while not battle.finished and battle.turn < 30:
        battle.step()

    show_critical_hit_logs(battle)
    print("-" * 50)
    show_pokedex_abilities()

    # 試してみよう: LogCode.CRITICAL_HIT を別の LogCode（例: LogCode.ABILITY_TRIGGERED）に
    # 変えると、抽出できるイベントの種類がどう変わるか確認できる


if __name__ == "__main__":
    main()
