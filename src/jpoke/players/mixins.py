"""`Player` 派生クラスに機能を混ぜ込む Mixin 集。

`TreeSearchPlayer`/`MinimaxPlayer` など `choose_selection` を独自実装しない
方策クラスに、`RandomPlayer` と同じランダム選出を混ぜ込みたい場合に使う。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jpoke.model import Pokemon

from jpoke import Battle


class RandomSelectionMixin:
    """選出（`choose_selection`）をランダムにする Mixin。

    `battle.decision_random`（行動選択専用の乱数系列）を使って選ぶため、
    `Battle(seed=...)` による対戦全体の再現性を壊さない
    （`battle.random` を使うとダメージ計算などの乱数系列がずれてしまう）。
    実装は `RandomPlayer.choose_selection` と完全に同一。

    継承順（MRO）に注意すること。`Player.choose_selection`（先頭 n 体を
    決定的に選ぶ既定実装）を上書きするため、本 Mixin を先に継承する必要がある。

    ```python
    class MyAI(RandomSelectionMixin, MinimaxPlayer):
        ...
    ```

    逆順（`class MyAI(MinimaxPlayer, RandomSelectionMixin)`）にすると MRO 上
    `Player.choose_selection` が先に解決され、本 Mixin の実装が使われない。
    """

    team: list[Pokemon]

    def choose_selection(self, battle: Battle) -> list[int]:
        """選出可能な `battle.n_selected` 匹を `battle.decision_random` でランダムに選ぶ。"""
        return battle.decision_random.sample(range(len(self.team)), battle.n_selected)
