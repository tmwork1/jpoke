"""プレイヤークラスとプレイヤー管理機能。

バトルに参加するプレイヤーの情報と、コマンドの予約・管理を行います。
選出、交代、行動の選択などプレイヤー固有の処理を提供します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from jpoke.enums import Command, Interrupt
from jpoke.utils import fast_copy


class Player:
    """バトルプレイヤーを表すクラス。

    プレイヤーのポケモンチーム、現在の場のポケモン、
    予約されたコマンド、割り込み状態などを管理します。

    Attributes:
        MAX_RESERVED: 予約可能な最大コマンド数
        name: プレイヤー名
        team: ポケモンチームのリスト（最大6匹）
        n_game: 対戦数
        n_won: 勝利数
        rating: レーティング値
        selection_idxes: 選出したポケモンのインデックスリスト
        active_idx: 現在場に出ているポケモンのインデックス
        interrupt: 割り込みフラグ（交代が必要な状態）
        reserved_commands: 予約されたコマンドのリスト
        has_switched: 今ターンに交代したかどうか
    """

    def __init__(self, name: str = ""):
        """Playerインスタンスを初期化する。

        Args:
            name: プレイヤー名（デフォルトは空文字列）
        """
        self.name = name

        self.team: list[Pokemon] = []
        self.n_game: int = 0
        self.n_won: int = 0
        self.rating: float = 1500

    def choose_selection_commands(self, battle: Battle) -> list[Command]:
        """選出コマンドを選択する。

        デフォルト実装では利用可能な選出コマンドからチームサイズ分を返す。

        Args:
            battle: バトルオブジェクト

        Returns:
            選択された選出コマンドのリスト
        """
        n = len(self.team)
        return battle.get_available_selection_commands(self)[:n]

    def choose_action_command(self, battle: Battle) -> Command:
        """行動コマンドを選択する。

        デフォルト実装では利用可能な行動コマンドの最初の1つを返す。

        Args:
            battle: バトルオブジェクト

        Returns:
            選択された行動コマンド
        """
        return battle.get_available_action_commands(self)[0]

    def choose_switch_command(self, battle: Battle) -> Command:
        """交代コマンドを選択する。

        デフォルト実装では利用可能な交代コマンドの最初の1つを返す。

        Args:
            battle: バトルオブジェクト

        Returns:
            選択された交代コマンド
        """
        return battle.get_available_switch_commands(self)[0]
