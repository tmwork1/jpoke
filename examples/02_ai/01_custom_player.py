"""Player を継承した自作方策（AI）の最小実装を示す。

choose_command をオーバーライドし、「最も威力の高い技を選ぶ」という単純な
ヒューリスティックのプレイヤーを作る。
AI開発ユースケースの最初のステップとして、Player のカスタム方法だけに絞った例。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command


class StrongestMovePlayer(Player):
    """毎ターン、利用可能な技の中から最も威力の高い技を選ぶプレイヤー。"""

    def choose_command(self, battle: Battle) -> Command:
        """利用可能なコマンドの中から、最も威力の高い技コマンドを選ぶ。

        メガシンカ・テラスタルを伴う技コマンドも対象に含める。交代・わるあがき等の
        技以外のコマンドは最低優先度として扱い、通常は選ばれない。
        """
        commands = battle.get_available_commands(self)

        def move_power(command: Command) -> int:
            # is_type("move") は通常技に加えメガシンカ・テラスタルコマンドも含む
            # （is_regular_move だと通常技コマンドのみになり、メガシンカ・テラスタルを
            # 伴う技コマンドが除外されてしまう）
            # is_type() は "move"/"switch"/"any" のどの種別かも判定できる汎用メソッド
            # （Command.switch_commands() 等の内部実装にも使われている）なので、
            # is_move() のような技専用の名前への改名はしていない
            if not command.is_type("move"):
                return -1
            move = battle.command_to_move(self, command)
            # 変化技は base_power が None。move.is_attack で判定する
            return move.base_power if move.is_attack else 0

        # key=move_power は「commands の各要素を move_power() に通した結果を
        # 比較キーにして最大の要素を選ぶ」という意味。ここでは威力が最大の
        # コマンドを選ぶ（move_power() 自体は変更しない）
        return max(commands, key=move_power)


def main() -> None:
    player1 = StrongestMovePlayer("StrongestMovePlayer")
    player1.add_pokemon("ピカチュウ", move_names=["でんこうせっか", "かみなり", "なきごえ"])

    player2 = Player("Player 2")
    player2.add_pokemon("フシギダネ", move_names=["たいあたり"])

    battle = Battle(player1, player2, seed=1)
    battle.start()

    winner = battle.play_out(max_turns=100)
    print(f"勝者: {winner.username if winner else '引き分け（ターン上限）'}")
    battle.print_logs("all")
    print("-" * 50)  # print_logs() の出力とその後のprint()を視覚的に区切る

    # StrongestMovePlayer は威力110の「かみなり」を選び続けるはず
    # （威力40の「でんこうせっか」・変化技の「なきごえ」より優先される）。
    # player1.team はコンストラクタ時点のスナップショットで対戦中は更新されないため、
    # 対戦中の状態を見るには battle.get_active() で対戦中のインスタンスを取得する
    active = battle.get_active(player1)
    print(f"最終ターンの技: {active.last_move.name if active.last_move else None}")

    # 試してみよう: move_power() に「相手のタイプ相性が悪い技は除外する」といった
    # 条件を加えると、より賢い方策に発展させられる


if __name__ == "__main__":
    main()
