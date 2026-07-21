"""`Player` の派生方策実装を集約するパッケージ。

木探索フレームワークの `TreeSearchPlayer`（抽象基底）とミニマックス実装の
`MinimaxPlayer`、ランダム選択の `RandomPlayer`、最大ダメージ技を選ぶ
`MaxDamagePlayer` など、bot・探索コードから再利用される方策実装をここに置く。
リプレイ再生用の `ReplayPlayer` / `replay_battle()` は `jpoke.core.replay` を参照。
"""
from .tree_search_player import TreeSearchPlayer
from .minimax_player import MinimaxPlayer
from .random_player import RandomPlayer
from .max_damage_player import MaxDamagePlayer

__all__ = ["TreeSearchPlayer", "MinimaxPlayer", "RandomPlayer", "MaxDamagePlayer"]
