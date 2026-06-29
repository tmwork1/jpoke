import json
from importlib import resources
from jpoke.handlers.models import PokemonData


def resource_path(*path_parts: str) -> str:
    """リソースファイルのパスを取得
    Args:
        path_parts: パスの各部分
    """
    return str(resources.files("jpoke").joinpath(*path_parts))


file = resource_path('data', "pokedex.json")
with open(file, encoding='utf-8') as f:
    data = json.load(f)

POKEDEX: dict[str, PokemonData] = {
    d["name"]: PokemonData(d) for d in data.values()
}
