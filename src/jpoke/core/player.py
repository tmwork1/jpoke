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

# poke-env 互換の battle_against() でターン上限に使う既定値。
# scripts/fuzz_battle.py の "random" プリセット（max_turns=100）を参考にした値。
MAX_TURNS = 100


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

    # ── poke-env 互換 ───────────────────────────────────────────

    @property
    def n_tied_battles(self) -> int:
        """poke-env 互換: 引き分け数。jpoke に引き分けは存在しないため常に0。"""
        return 0

    @property
    def n_lost_battles(self) -> int:
        """poke-env 互換: 敗北数。"""
        return self.n_finished_battles - self.n_won_battles - self.n_tied_battles

    @property
    def win_rate(self) -> float:
        """poke-env 互換: 勝率。poke-env と異なりゼロ除算を防ぐガード付き。"""
        if self.n_finished_battles == 0:
            return 0.0
        return self.n_won_battles / self.n_finished_battles

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

    def battle_against(self, *opponents: "Player", n_battles: int = 1, **battle_kwargs) -> None:
        """poke-env 互換: 各 opponent と n_battles 回ずつ対戦し、双方の戦績を更新する。

        poke-env と同じシグネチャ。ただしネットワーク I/O がないため同期メソッド
        （await / asyncio.run は不要）。

        Args:
            *opponents: 対戦相手のPlayerインスタンス（複数指定可）
            n_battles: 各opponentと対戦する回数（デフォルト1）
            **battle_kwargs: `Battle.__init__` へ素通しするキーワード引数
                （`n_selected`, `seed`, `mega_evolution` 等）。poke-envにはない
                jpoke独自の拡張。再現可能な対戦を組みたい場合は `seed` を指定する

        Note:
            ターン数が `MAX_TURNS` に達しても決着しない対戦は、勝者を強制的に
            決めず（`tod_score()` 等によるダメージレース判定は行わない）、
            戦績に一切数えない（`n_finished_battles` もインクリメントしない）。
            対戦の成立・不成立を戦績に反映する方が、引き分けを持たない
            jpokeの仕様（`n_tied_battles` は常に0）と整合するための判断。
        """
        # Battleをモジュールトップレベルでimportすると、battle.pyがPlayerを
        # importしているため循環importになる。関数内での遅延importで回避する。
        from .battle import Battle

        for opponent in opponents:
            for _ in range(n_battles):
                battle = Battle((self, opponent), **battle_kwargs)
                battle.start()
                while battle.judge_winner() is None and battle.turn < MAX_TURNS:
                    battle.step()
                winner = battle.judge_winner()
                if winner is None:
                    # ターン上限で決着しなかった対戦は不成立として戦績に数えない
                    continue
                for player in (self, opponent):
                    player.n_finished_battles += 1
                    if winner is player:
                        player.n_won_battles += 1
