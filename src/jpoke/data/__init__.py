from .ability import ABILITIES
from .item import ITEMS
from .move import MOVES
from .field import FIELDS
from .ailment import AILMENTS
from .volatile import VOLATILES
from .pokedex import pokedex, get_season


# name メンバ変数を追加
for data in [
    ABILITIES, ITEMS, MOVES, FIELDS, AILMENTS, VOLATILES
]:
    for name, obj in data.items():
        if not isinstance(obj, dict):
            obj.name = name
