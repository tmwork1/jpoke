"""jpoke で学べること: Player を継承した自作方策（AI）の最小実装。

choose_command をオーバーライドし、「最も威力の高い技を選ぶ」という単純な
ヒューリスティックのプレイヤーを作る。技で早く相手を倒せるほど反撃を受ける
ターンが減り、結果として自分のHP割合を高く保ちやすい、という発想の入口。
AI開発ユースケースの最初のステップとして、Player のカスタム方法だけに絞った例。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command


class StrongestMovePlayer(Player):
    """毎ターン、利用可能な技の中から最も威力の高い技を選ぶプレイヤー。"""

    def choose_command(self, battle: Battle) -> Command:
        commands = battle.get_available_commands(self)

        def move_power(command: Command) -> int:
            # 技コマンド以外（交代・わるあがき等）は最低優先度として扱う
            if not command.is_regular_move:
                return -1
            move = battle.command_to_move(self, command)
            # 変化技は base_power が None。move.is_attack で判定する
            return move.base_power if move.is_attack else 0

        return max(commands, key=move_power)

    def choose_command_poke_env_style(self, battle: Battle) -> Command:
        """poke-env経験者向け: choose_command() と同じ判断の代替実装（未使用）。

        choose_command() に渡される battle は観測用コピーで、battle.observer が
        呼び出し元プレイヤー自身に設定されているため、poke-env互換プロパティ
        （battle.active_pokemon / battle.opponent_active_pokemon / battle.available_moves /
        battle.available_switches / battle.side_conditions / battle.team）がそのまま
        自分視点の情報として使える。get_available_commands() + command_to_move() の
        組み合わせをこちらに置き換えても同じ結果になる
        """
        moves = battle.available_moves  # get_available_commands()を技だけ取り出しMoveに変換したもの
        if not moves:
            # わるあがきのみの場合。available_moves はこのときわるあがきを1件返す
            return battle.get_available_commands(self)[0]
        move_commands = [c for c in battle.get_available_commands(self) if c.is_regular_move]
        best_index = max(
            range(len(moves)),
            key=lambda i: moves[i].base_power if moves[i].is_attack else 0,
        )
        return move_commands[best_index]


def main() -> None:
    player1 = StrongestMovePlayer("StrongestMovePlayer")
    player1.add_pokemon("ピカチュウ", move_names=["でんこうせっか", "かみなり", "なきごえ"])

    player2 = Player("Player 2")
    player2.add_pokemon("フシギダネ", move_names=["たいあたり"])

    battle = Battle(player1, player2, seed=1)
    battle.start()

    while battle.judge_winner() is None and battle.turn < 100:
        battle.step()

    winner = battle.judge_winner()
    print(f"勝者: {winner.username if winner else '引き分け（ターン上限）'}")
    battle.print_logs()

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
