# TODO: このサンプルは削除すべき
"""jpoke で学べること: 設置技（サイドフィールド効果）と交代誘発技の効果、
交代・テラスタル・メガシンカコマンドを明示的に組み立てる方法、わるあがき（PP切れ）の挙動。

これまでのサンプルは battle.get_available_commands() から選ぶか、Player の既定方策
（先頭のコマンドを選ぶ）に任せていた。ここでは Command.get_switch_command() /
get_terastal_command() / get_megaevol_command() で自分でコマンドを組み立て、
battle.step({player: command, ...}) に直接渡す方法を示す。

Warning:
    ここで示す battle.step() へのコマンド注入は木探索（TreeSearchPlayerの読み筋展開等）
    向けの仕組みで、不正なコマンドに対するフォールバック等は整備されていない。
    Playerの行動そのものを恒常的に制御したい場合は、この方法ではなく Player を
    継承して choose_command() をオーバーライドすべき（02_ai/01_custom_player.py 参照）。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command


def show_entry_hazard_and_explicit_switch() -> None:
    """ステルスロックを設置したサイドに、交代コマンドを明示的に組み立てて交代する。"""
    attacker_player = Player("Attacker")
    attacker_player.add_pokemon("ピカチュウ", move_names=["なきごえ"])
    attacker_player.add_pokemon("コラッタ")  # n_selectedを両陣営2に揃えるためのダミー

    defender_player = Player("Defender")
    defender_player.add_pokemon("ゼニガメ", move_names=["たいあたり"])
    defender_player.add_pokemon("ヒトカゲ")  # ほのおタイプはいわタイプに2倍弱い

    battle = Battle(attacker_player, defender_player, seed=1)
    battle.start()
    # activate_side_field() は技を介さずサイドフィールド効果を直接発動する検証用API
    battle.activate_side_field(defender_player, "ステルスロック", 1)

    bench = battle.get_team(defender_player)[1]
    hp_before = bench.hp
    # Command.get_switch_command(index) にチーム内インデックスを渡してコマンドを組み立てる
    switch_command = Command.get_switch_command(battle.get_team(defender_player).index(bench))
    battle.step({attacker_player: Command.MOVE_0, defender_player: switch_command})

    print(
        f"ステルスロックを設置したサイドに{bench.name}が交代出場: "
        f"HP {hp_before} → {bench.hp}（いわタイプ弱点で通常の2倍ダメージ）"
    )


def show_switch_inducing_move() -> None:
    """とんぼがえり等の交代誘発技は、命中してダメージを与えた直後、同じstep()内で
    使用者側の強制交代（Interrupt.PIVOT）を解決する。交代先は使用者の既定方策
    （Playerの場合は先頭の生存個体）に従う。
    """
    attacker_player = Player("Attacker")
    attacker_player.add_pokemon("ピカチュウ", move_names=["とんぼがえり"])
    attacker_player.add_pokemon("ライチュウ")
    defender_player = Player("Defender")
    defender_player.add_pokemon("カビゴン", move_names=["たいあたり"])
    defender_player.add_pokemon("コラッタ")  # n_selectedを両陣営2に揃えるためのダミー

    battle = Battle(attacker_player, defender_player, seed=1, accuracy_fix_threshold=0)
    battle.start()
    before = battle.get_active(attacker_player)
    battle.step({attacker_player: Command.MOVE_0, defender_player: Command.MOVE_0})
    after = battle.get_active(attacker_player)
    print(f"とんぼがえり使用後、同じstep()内で{before.name} → {after.name}に交代済み")


def show_struggle_when_out_of_pp() -> None:
    """全ての技のPPが0になると、コマンド候補はStruggle（わるあがき）だけになる。"""

    class ShowCommandsPlayer(Player):
        """choose_command()内でbattle.get_available_commands()を確認し表示する。

        コマンド候補・選択理由をデバッグ的に確認したいときは、既定方策をこのように
        オーバーライドしてbattle.get_available_commands(self)を覗くのが手早い
        （02_ai/02のTreeSearchPlayer.evaluate_commands()はより発展的な読み筋確認手段）。
        """

        def choose_command(self, battle: Battle) -> Command:
            commands = battle.get_available_commands(self)
            print(f"コマンド候補: {commands}")
            return commands[0]

    player1 = ShowCommandsPlayer("Attacker")
    player1.add_pokemon("ピカチュウ", move_names=["たいあたり"])
    player2 = Player("Defender")
    player2.add_pokemon("カビゴン")

    battle = Battle(player1, player2, seed=1)
    battle.start()
    mon = battle.get_active(player1)
    # Move.modify_pp() でPPを直接操作できる（Move.pp は公開属性）
    mon.moves[0].modify_pp(-99)
    hp_before = mon.hp
    battle.step()
    print(f"わるあがき使用後、{mon.name}のHP: {hp_before} → {mon.hp}（最大HPの1/4を反動で失う）")


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
    show_entry_hazard_and_explicit_switch()
    print("-" * 50)
    show_switch_inducing_move()
    print("-" * 50)
    show_struggle_when_out_of_pp()
    print("-" * 50)
    show_explicit_terastal_command()
    print("-" * 50)
    show_explicit_megaevol_command()

    # 試してみよう: ステルスロックをまきびしに変えたり、交代先のタイプ相性を変えたりすると
    # 設置技のダメージ・効果がどう変わるか比較できる


if __name__ == "__main__":
    main()
