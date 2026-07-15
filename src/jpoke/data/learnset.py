import json
from importlib import resources

from jpoke.types import MoveName, PokemonName


def resource_path(*path_parts: str) -> str:
    """リソースファイルのパスを取得
    Args:
        path_parts: パスの各部分
    """
    return str(resources.files("jpoke").joinpath(*path_parts))


file = resource_path('data', 'ps-champ-ja', "learnsets.json")
with open(file, encoding='utf-8') as f:
    data = json.load(f)

LEARNSETS: dict[PokemonName, frozenset[MoveName]] = {
    name: frozenset(moves) for name, moves in data.items()
}
