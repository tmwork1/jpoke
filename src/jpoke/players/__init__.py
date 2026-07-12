"""`Player` の派生方策実装を集約するパッケージ。

木探索ベースの `TreeSearchPlayer`、ランダム選択の `RandomPlayer` など、
bot・探索コードから再利用される方策実装をここに置く。
リプレイ再生用の `ReplayPlayer` / `replay_battle()` は `jpoke.core.replay` を参照。
"""
from .tree_search_player import TreeSearchPlayer
from .random_player import RandomPlayer

__all__ = ["TreeSearchPlayer", "RandomPlayer"]
