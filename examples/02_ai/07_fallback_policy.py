"""TreeSearchPlayer.fallback() をオーバーライドして、
探索できない局面での代替方策をカスタマイズする方法を示す。

fallback() は (1) 相手の合法手が未公開で estimate_opponent でも推定できない
局面（実対戦の初手など）、(2) 探索中に発生した割り込み交代（瀕死交代等）による
choose_command() の再入時、の2箇所で使われる（tree_search_player.py のdocstring
参照）。既定は battle.decision_random.choice() による完全ランダム選択だが、
ここでは「攻撃技があれば優先する」という軽量なヒューリスティックに差し替える
最小例を示す。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command
from jpoke.players.tree_search_player import TreeSearchPlayer


class AttackPreferringFallbackPlayer(TreeSearchPlayer):
    """fallback時（探索できない局面）は攻撃技を優先するAI（fallback()の拡張例）。"""

    def fallback(self, battle: Battle) -> Command:
        commands = battle.get_available_commands(self)

        def is_attack(command: Command) -> bool:
            # is_regular_move はメガシンカ/テラスタル変種や交代を除いた
            # 「通常の技コマンド」かどうかの判定であり、変化技（まもる等）も
            # 含む点に注意（01_custom_player.py参照）。攻撃技かどうかは
            # command_to_move() で技を引きmove.is_attackで判定する
            return command.is_regular_move and battle.command_to_move(self, command).is_attack

        attack_commands = [c for c in commands if is_attack(c)]
        if attack_commands:
            return attack_commands[0]
        # 攻撃技がない場合は既定のランダム選択に委譲する
        return super().fallback(battle)


def main() -> None:
    ai_player = AttackPreferringFallbackPlayer("FallbackAI", max_plies=1, max_nodes=50)
    ai_player.add_pokemon("カビゴン", move_names=["まもる", "のしかかり"])

    opponent_player = Player("Opponent")
    opponent_player.add_pokemon("カビゴン", move_names=["のしかかり"])

    battle = Battle(ai_player, opponent_player, seed=1)
    battle.start()

    # 1ターン目: 相手の技が未公開でestimate_opponentも未実装のためfallback()に
    # 委譲される。既定のランダム選択なら「まもる」も等確率で選ばれ得るが、この
    # 実装では攻撃技「のしかかり」が優先して選ばれる
    battle.step()
    active = battle.get_active(ai_player)
    print(f"1ターン目にFallbackAIが選んだ技: {active.last_move.name if active.last_move else None}")
    battle.print_logs()

    # 試してみよう: fallback() を既定実装のまま（オーバーライドせず）
    # 何度か実行すると、1ターン目の選択が「まもる」「のしかかり」でばらつくのに対し、
    # このサンプルでは常に「のしかかり」が選ばれ続けることを比較できる


if __name__ == "__main__":
    main()
