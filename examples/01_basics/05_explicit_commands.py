"""battle.get_available_commands() が返す Command の種類を識別する方法を示す。

通常は get_available_commands() から選ぶか、Player の既定方策（先頭のコマンドを選ぶ）に
任せれば十分だが、コマンドの種類（技・テラスタルを伴う技・交代等）を明示的に判定したい
場合は is_regular_move / is_terastal / is_switch 等のプロパティを使う。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command


class CommandTypePrinter(Player):
    """choose_command()の直前に、利用可能なコマンドの種類を表示するデバッグ用サブクラス。

    battle.get_available_commands() は phase="action"/"switch" のときだけ呼べるため、
    choose_command() の中（battle.step() 実行中）から呼ぶ。
    """

    def choose_command(self, battle: Battle) -> Command:
        for command in battle.get_available_commands(self):
            if command.is_regular_move:
                kind = "技"
            elif command.is_terastal:
                kind = "テラスタルを伴う技"
            elif command.is_switch:
                kind = "交代"
            else:
                kind = "その他"
            print(f"{command}: {kind}")
        return super().choose_command(battle)


def main() -> None:
    player1 = CommandTypePrinter("Attacker")
    player1.add_pokemon("ピカチュウ", move_names=["でんこうせっか"], tera_type="ほのお")
    player1.add_pokemon("ライチュウ")
    player2 = Player("Defender")
    player2.add_pokemon("カビゴン", move_names=["たいあたり"])
    player2.add_pokemon("コラッタ")  # n_selectedを両陣営2に揃えるためのダミー

    battle = Battle(player1, player2, seed=1)
    battle.start()
    battle.step()

    # 試してみよう: player1 のチーム構成やテラスタイプ指定を変えると、
    # 表示されるコマンドの種類・数がどう変わるか観察できる


if __name__ == "__main__":
    main()
