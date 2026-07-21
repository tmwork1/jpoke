"""`Player` の派生方策実装を集約するパッケージ。

木探索フレームワークの `TreeSearchPlayer`（抽象基底）とミニマックス実装の
`MinimaxPlayer`、ランダム選択の `RandomPlayer`、最大ダメージ技を選ぶ
`MaxDamagePlayer`、標準入出力で対話的に操作する `CLIPlayer` など、
bot・探索コード・手動対戦から再利用される方策実装をここに置く。
リプレイ再生用の `ReplayPlayer` / `replay_battle()` は `jpoke.core.replay` を参照。
"""
from .tree_search_player import TreeSearchPlayer
from .minimax_player import MinimaxPlayer
from .random_player import RandomPlayer
from .max_damage_player import MaxDamagePlayer
from .cli_player import CLIPlayer

__all__ = ["TreeSearchPlayer", "MinimaxPlayer", "RandomPlayer", "MaxDamagePlayer", "CLIPlayer"]
