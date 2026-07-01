"""ポケモンバトルで使用される定数を定義するモジュール。"""
from typing import get_args
from jpoke.types import Stat


STATS = list(get_args(Stat))
