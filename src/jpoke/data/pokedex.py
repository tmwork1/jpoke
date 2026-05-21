import json
from importlib import resources
from jpoke.data.models import PokemonData


def resource_path(*path_parts: str) -> str:
    """リソースファイルのパスを取得
    Args:
        path_parts: パスの各部分
    """
    return str(resources.files("jpoke").joinpath(*path_parts))


pokedex: dict[str, PokemonData] = {}


def init():
    """ポケモン図鑑データを初期化する関数。
    zukan.jsonからデータを読み込み、pokedex辞書にPokemonDataオブジェクトとして格納します。
    """
    file = resource_path('data', "zukan.json")
    with open(file, encoding='utf-8') as f:
        data = json.load(f)

    global pokedex
    for d in data.values():
        pokedex[d["alias"]] = PokemonData(d)


init()
