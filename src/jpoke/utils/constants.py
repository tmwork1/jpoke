"""ポケモンバトルで使用される定数を定義するモジュール。"""
from typing import get_args
from jpoke.types import Stat


STATS = list(get_args(Stat))

# 能力ランクの範囲
STAT_RANK_MIN = -6
STAT_RANK_MAX = 6

# クリティカルランクの範囲
CRITICAL_RANK_MIN = 0
CRITICAL_RANK_MAX = 3

# 固定小数点補正の基準値
FIXED_POINT_BASE = 4096

# PP消費の概念がない技（わるあがき・_こんらん等）に設定する番兵値
PP_INFINITE = 99999
