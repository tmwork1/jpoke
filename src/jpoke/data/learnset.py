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

# ps-champ-ja由来の生データ（フィルタなし）。シングルバトルで戦闘に影響しない技の除外は
# Pokemon.learnset側で行う（data.move.MOVESへの依存はdata.pokedex経由の循環インポートに
# なるため、ここでは行えない）。
LEARNSETS: dict[PokemonName, list[MoveName]] = {
    name: sorted(moves) for name, moves in data.items()
}
