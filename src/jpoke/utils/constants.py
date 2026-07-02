# TODO : 定数化すべきものをコード全体から切り出す

"""ポケモンバトルで使用される定数を定義するモジュール。"""
from typing import get_args
from jpoke.types import Stat


STATS = list(get_args(Stat))
