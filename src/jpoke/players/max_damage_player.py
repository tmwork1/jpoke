"""最大ダメージの技を選ぶだけのプレイヤー。"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command


class MaxDamagePlayer(Player):
    """自分の場のポケモンが繰り出せる技のうち、相手の場のポケモンに与える
    最低保証ダメージ（乱数下振れ）が最大になる技を選ぶプレイヤー。

    比較対象・ベースラインとして使う単純な方策実装。技以外のコマンド
    （交代等）は候補にせず、常に技コマンドの中から選ぶ。選出は
    `Player.choose_selection()`（既定実装、先頭から順に選出）のまま。
    """

    def choose_command(self, battle: Battle) -> Command:
        """利用可能なコマンドのうち、最大ダメージを与える技コマンドを選ぶ。"""
        commands = battle.available_commands(self)
        return max(commands, key=lambda command: self._damage(battle, command))

    def _damage(self, battle: Battle, command: Command) -> int:
        """コマンドが技でない場合は選ばれないよう -1 を返す。"""
        if not command.is_move:
            return -1

        move = battle.command_to_move(self, command)
        opponent = battle.opponent(self)
        damages = battle.calc_damages(
            attacker=battle.get_active(self),
            defender=battle.get_active(opponent),
            move=move,
            critical=move.guaranteed_crit,  # 確定急所を考慮する
        )
        return damages[0]  # 0: 最低ダメージ
