import json
from importlib import resources
from jpoke.data.models import PokemonData


def resource_path(*path_parts: str) -> str:
    """リソースファイルのパスを取得
    Args:
        path_parts: パスの各部分
    """
    return str(resources.files("jpoke").joinpath(*path_parts))


POKEDEX: dict[str, PokemonData] = {}


def init():
    """ポケモン図鑑データを初期化する関数。
    pokedex.jsonからデータを読み込み、POKEDEX辞書にPokemonDataオブジェクトとして格納します。
    """
    file = resource_path('data', "pokedex.json")
    with open(file, encoding='utf-8') as f:
        data = json.load(f)

    global POKEDEX
    for d in data.values():
        POKEDEX[d["name"]] = PokemonData(d)


init()
