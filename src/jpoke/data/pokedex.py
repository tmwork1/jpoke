import csv
import json
from importlib import resources
from jpoke.data.models import PokemonData
from jpoke.data.learnset import LEARNSETS
from jpoke.types import PokemonName, Regulation


def resource_path(*path_parts: str) -> str:
    """リソースファイルのパスを取得
    Args:
        path_parts: パスの各部分
    """
    return str(resources.files("jpoke").joinpath(*path_parts))


def _load_pokemon_regulations() -> dict[PokemonName, set[Regulation]]:
    """regulation/pokemon.csv からポケモンごとの使用可能レギュレーションを読み込む。"""
    regulation_path = resources.files("jpoke").joinpath("data", "regulation", "pokemon.csv")
    regulations_by_pokemon = {}

    with regulation_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None, "regulation/pokemon.csv のヘッダが読み取れません"
        regulation_names = [
            name
            for name in reader.fieldnames
            if name not in {"dex_no", "name", "implemented"}
        ]

        for row in reader:
            if row["implemented"] != "1":
                continue

            regulations_by_pokemon[row["name"]] = {
                regulation
                for regulation in regulation_names
                if row[regulation] == "1"
            }

    return regulations_by_pokemon


file = resource_path('data', 'ps-champ-ja', "pokedex.json")
with open(file, encoding='utf-8') as f:
    data = json.load(f)

pokemon_regulations = _load_pokemon_regulations()

POKEDEX: dict[PokemonName, PokemonData] = {
    name: PokemonData(name, entry, LEARNSETS.get(name)) for name, entry in data.items()
}

for name in pokemon_regulations:
    assert name in POKEDEX, f"regulation/pokemon.csv に未定義のポケモン名があります: {name}"

for name in POKEDEX:
    POKEDEX[name].regulations = set(pokemon_regulations.get(name, set()))


def get_pokemon_by_regulation(regulation: Regulation) -> list[PokemonName]:
    """指定レギュレーションで使用可能なポケモン名の一覧を返す（五十音順）。"""
    return sorted(name for name, data in POKEDEX.items() if regulation in data.regulations)
