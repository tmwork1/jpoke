"""Command の種類を識別する方法と、交代・テラスタル・メガシンカを伴う技コマンドを
明示的に組み立てる方法を示す。

通常は battle.get_available_commands() から選ぶか、Player の既定方策（先頭のコマンドを
選ぶ）に任せれば十分だが、特定の交代先・テラスタル・メガシンカを指定したい場合は
Command.get_switch_command() / get_terastal_command() / get_megaevol_command() で
自分でコマンドを組み立て、battle.step({player: command, ...}) に直接渡せる。
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


def show_command_type_identification() -> None:
    """get_available_commands() が返す Command の種類を is_regular_move/is_terastal/
    is_switch で識別する。
    """
    player1 = CommandTypePrinter("Attacker")
    player1.add_pokemon("ピカチュウ", move_names=["でんこうせっか"], tera_type="ほのお")
    player1.add_pokemon("ライチュウ")
    player2 = Player("Defender")
    player2.add_pokemon("カビゴン", move_names=["たいあたり"])
    player2.add_pokemon("コラッタ")  # n_selectedを両陣営2に揃えるためのダミー

    battle = Battle(player1, player2, seed=1)
    battle.start()
    battle.step()


def show_explicit_switch_command() -> None:
    """Command.get_switch_command(index) にチーム内インデックスを渡してコマンドを組み立てる。"""
    player1 = Player("Attacker")
    player1.add_pokemon("ピカチュウ", move_names=["なきごえ"])
    player1.add_pokemon("コラッタ")  # n_selectedを両陣営2に揃えるためのダミー
    player2 = Player("Defender")
    player2.add_pokemon("ゼニガメ", move_names=["たいあたり"])
    player2.add_pokemon("ヒトカゲ")

    battle = Battle(player1, player2, seed=1)
    battle.start()
    bench = battle.get_team(player2)[1]
    switch_command = Command.get_switch_command(battle.get_team(player2).index(bench))
    battle.step({player1: Command.MOVE_0, player2: switch_command})
    print(f"交代後の場のポケモン: {battle.get_active(player2).name}")


def show_explicit_terastal_command() -> None:
    """Command.get_terastal_command(index) で「index番目の技を使いながらテラスタルする」
    コマンドを明示的に組み立てる。
    """
    player1 = Player("Attacker")
    player1.add_pokemon("ピカチュウ", move_names=["かみなり"], tera_type="ほのお")
    player2 = Player("Defender")
    player2.add_pokemon("カビゴン")

    battle = Battle(player1, player2, seed=1)
    battle.start()
    attacker = battle.get_active(player1)
    print(f"テラスタル前: is_terastallized={attacker.is_terastallized}, テラスタイプ={attacker.tera_type}")
    battle.step({player1: Command.get_terastal_command(0), player2: Command.MOVE_0})
    print(f"テラスタル後: is_terastallized={attacker.is_terastallized}, テラスタイプ={attacker.tera_type}")


def show_explicit_megaevol_command() -> None:
    """Command.get_megaevol_command(index) で「index番目の技を使いながらメガシンカする」
    コマンドを明示的に組み立てる。テラスタルと違い、対応するメガストーン（例: フシギバナイト）を
    持たせたポケモンでなければメガシンカできない（Pokemon.can_megaevolve()で判定可能）。
    """
    player1 = Player("Attacker")
    player1.add_pokemon("フシギバナ", item_name="フシギバナイト", move_names=["たいあたり"])
    player2 = Player("Defender")
    player2.add_pokemon("カビゴン")

    battle = Battle(player1, player2, seed=1)
    battle.start()
    attacker = battle.get_active(player1)
    print(f"メガシンカ前: {attacker.name}（can_megaevolve={attacker.can_megaevolve()}）")
    battle.step({player1: Command.get_megaevol_command(0), player2: Command.MOVE_0})
    print(f"メガシンカ後: {attacker.name}（megaevolved={attacker.megaevolved}）")


def main() -> None:
    show_command_type_identification()
    print("-" * 50)
    show_explicit_switch_command()
    print("-" * 50)
    show_explicit_terastal_command()
    print("-" * 50)
    show_explicit_megaevol_command()

    # 試してみよう: player1 のチーム構成を変えると、show_command_type_identification() で
    # 表示されるコマンドの種類・数がどう変わるか観察できる


if __name__ == "__main__":
    main()
