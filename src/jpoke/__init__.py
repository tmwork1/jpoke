"""jpokeパッケージ - ポケモンバトルシミュレータ。

バトル、プレイヤー、ポケモン、技、特性、アイテムなどの主要クラスと、
ポケモン図鑑データを提供します。
"""
from .core import Battle, Player
from .enums import Command
from .model import Pokemon, Ability, Item, Move
from .data import POKEDEX, get_pokemon_by_regulation, get_items_by_regulation
from .utils import (
    get_pokeapi_url,
    get_pokemon_image_url,
    get_item_image_url,
    get_type_image_url,
    get_tera_type_image_url,
    download_pokemon_image,
    download_item_image,
)

# pyproject.toml の version と手動で一致させること（tests/test_version.py で検証）
__version__ = "0.2.0"

__all__ = [
    "Battle",
    "Player",
    "Command",
    "Pokemon",
    "Ability",
    "Item",
    "Move",
    "POKEDEX",
    "get_pokemon_by_regulation",
    "get_items_by_regulation",
    "get_pokeapi_url",
    "get_pokemon_image_url",
    "get_item_image_url",
    "get_type_image_url",
    "get_tera_type_image_url",
    "download_pokemon_image",
    "download_item_image",
]
