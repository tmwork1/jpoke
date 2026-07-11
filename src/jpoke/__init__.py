"""jpokeパッケージ - ポケモンバトルシミュレータ。

バトル、プレイヤー、ポケモン、技、特性、アイテムなどの主要クラスと、
ポケモン図鑑データを提供します。
"""
from importlib.metadata import version as _version

from .core import Battle, Player
from .model import Pokemon, Ability, Item, Move
from .data import POKEDEX

__version__ = _version("jpoke")

__all__ = [
    "Battle",
    "Player",
    "Pokemon",
    "Ability",
    "Item",
    "Move",
    "POKEDEX",
]
