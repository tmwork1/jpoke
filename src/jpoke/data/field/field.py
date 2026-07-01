from ..models import FieldData
from .global_field import GLOBAL_FIELD
from .side_field import SIDE_FIELD
from .terrain import TERRAIN
from .weather import WEATHER


def common_setup():
    """共通のセットアップ処理"""
    for name in FIELDS:
        FIELDS[name].name = name


FIELDS: dict[str, FieldData] = {
    "": FieldData(),
    **WEATHER,
    **TERRAIN,
    **GLOBAL_FIELD,
    **SIDE_FIELD,
}


common_setup()
