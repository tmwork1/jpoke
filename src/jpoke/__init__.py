"""jpokeパッケージ - ポケモンバトルシミュレータ。

バトル、プレイヤー、ポケモン、技、特性、アイテムなどの主要クラスと、
ポケモン図鑑データを提供します。
"""
from .core import Battle, Player
from .model import Pokemon, Ability, Item, Move
from .data import POKEDEX

# pyproject.toml の version と手動で一致させること（tests/test_version.py で検証）
__version__ = "0.1.0"

__all__ = [
    "Battle",
    "Player",
    "Pokemon",
    "Ability",
    "Item",
    "Move",
    "POKEDEX",
]
