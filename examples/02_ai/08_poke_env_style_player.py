"""poke-env経験者向け: poke-env互換プロパティを使った choose_command() の実装方法を示す。

01_custom_player.py の StrongestMovePlayer は get_available_commands() +
command_to_move() の組み合わせで実装していたが、choose_command() に渡される battle は
観測用コピーで battle.observer が呼び出し元プレイヤー自身に設定されているため、
poke-env互換プロパティ（battle.active_pokemon / battle.opponent_active_pokemon /
battle.available_moves / battle.available_switches / battle.side_conditions /
battle.team）がそのまま自分視点の情報として使える。

補足: poke-envではPlayer.choose_move()がcreate_order(move)で作ったBattleOrderを
返す仕様だが、jpokeのCommandは技・交代等の選択肢を表す単純なEnum値であり、
コマンド生成専用のクラスは存在しない。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command


class PokeEnvStylePlayer(Player):
    """poke-env互換プロパティを使い、最も威力の高い技を選ぶプレイヤー。"""

    def choose_command(self, battle: Battle) -> Command:
        moves = battle.available_moves  # get_available_commands()を技だけ取り出しMoveに変換したもの
        if not moves:
            # わるあがきのみの場合。available_moves はこのときわるあがきを1件返す。
            # battle.is_struggle_only(self) で判定できる（get_available_commands(self)[0] は
            # 交代コマンドが同時に存在すると先頭に来てしまい誤ってそちらを返すことがある）
            assert battle.is_struggle_only(self)
            return Command.STRUGGLE
        move_commands = [c for c in battle.get_available_commands(self) if c.is_regular_move]
        best_index = max(
            range(len(moves)),
            key=lambda i: moves[i].base_power if moves[i].is_attack else 0,
        )
        return move_commands[best_index]


def main() -> None:
    player1 = PokeEnvStylePlayer("PokeEnvStylePlayer")
    player1.add_pokemon("ピカチュウ", move_names=["でんこうせっか", "かみなり", "なきごえ"])

    player2 = Player("Player 2")
    player2.add_pokemon("フシギダネ", move_names=["たいあたり"])

    battle = Battle(player1, player2, seed=1)
    battle.start()

    winner = battle.play_out(max_turns=100)
    print(f"勝者: {winner.username if winner else '引き分け（ターン上限）'}")

    active = battle.get_active(player1)
    print(f"最終ターンの技: {active.last_move.name if active.last_move else None}")


if __name__ == "__main__":
    main()
