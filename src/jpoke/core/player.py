"""プレイヤークラスとプレイヤー管理機能。

バトルに参加するプレイヤーの情報と、コマンドの予約・管理を行います。
選出、交代、行動の選択などプレイヤー固有の処理を提供します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from jpoke.enums import Command


class Player:
    """バトルプレイヤーを表すクラス。

    Attributes:
        username: プレイヤー名
        team: ポケモンチームのリスト（最大6匹）
        n_finished_battles: 対戦数
        n_won_battles: 勝利数
        rating: レーティング値
    """

    def __init__(self, username: str = ""):
        """Playerインスタンスを初期化する。

        Args:
            username: プレイヤー名（デフォルトは空文字列）
        """
        self.username = username

        self.team: list[Pokemon] = []
        self.n_finished_battles: int = 0
        self.n_won_battles: int = 0
        self.rating: float = 1500

    def choose_selection(self, battle: Battle) -> list[int]:
        """選出番号を返す

        デフォルト実装では先頭から順番に選出する。

        Args:
            battle: バトルオブジェクト

        Returns:
            選択された選出番号のリスト
        """
        n = battle.n_selected
        return list(range(n))

    def choose_command(self, battle: Battle) -> Command:
        """コマンドを選択する。

        デフォルト実装では利用可能な行動コマンドの最初の1つを返す。

        Args:
            battle: バトルオブジェクト

        Returns:
            選択された行動コマンド
        """
        commands = battle.get_available_commands(self)
        return commands[0]
