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

    def choose_command_poke_env_style(self, battle: Battle) -> Command:
        """poke-env経験者向け: choose_command() と同じ判断の代替実装（未使用）。

        choose_command() に渡される battle は観測用コピーで、battle.observer が
        呼び出し元プレイヤー自身に設定されているため、poke-env互換プロパティ
        （battle.active_pokemon / battle.opponent_active_pokemon / battle.available_moves /
        battle.available_switches / battle.side_conditions / battle.team）がそのまま
        自分視点の情報として使える。get_available_commands() + command_to_move() の
        組み合わせをこちらに置き換えても同じ結果になる

        補足: poke-envではPlayer.choose_move()がcreate_order(move)で作った
        BattleOrderを返す仕様だが、jpokeのCommandは技・交代等の選択肢を表す
        単純なEnum値であり、コマンド生成専用のクラスは存在しない。本メソッドは
        あくまで比較用の未使用コードのため、戻り値の型を合わせる対応はしていない
        """
        moves = battle.available_moves  # get_available_commands()を技だけ取り出しMoveに変換したもの
        if not moves:
            # わるあがきのみの場合。available_moves はこのときわるあがきを1件返す。
            # battle.is_struggle_only(self) で判定できる（get_available_commands(self)[0] は
            # 交代コマンドが同時に存在すると先頭に来てしまい誤ってそちらを返すことがある）
            assert battle.is_struggle_only(self)
            return Command.STRUGGLE
        move_commands = [c for c in battle.get_available_commands(self) if c.is_regular_move]
        # lambda i: ... は def で名前を付けるまでもない使い捨ての関数をその場で書く記法。
        # ここでは「インデックスiを受け取り、対応する技の威力（変化技なら0）を返す」関数を
        # key に渡し、moves の中で最も威力が高い技のインデックスを求めている
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
