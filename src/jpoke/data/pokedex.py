import json
from importlib import resources
from jpoke.data.models import PokemonData
from jpoke.types import PokemonName


def resource_path(*path_parts: str) -> str:
    """リソースファイルのパスを取得
    Args:
        path_parts: パスの各部分
    """
    return str(resources.files("jpoke").joinpath(*path_parts))


file = resource_path('data', "pokedex.json")
with open(file, encoding='utf-8') as f:
    data = json.load(f)

POKEDEX: dict[PokemonName, PokemonData] = {
    name: PokemonData(name, entry) for name, entry in data.items()
}
