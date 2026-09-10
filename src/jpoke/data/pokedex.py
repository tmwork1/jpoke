import csv
import json
import typing
from importlib import resources
from jpoke.data.models import PokemonData
from jpoke.data.learnset import LEARNSETS
from jpoke.types import MoveName, PokemonName, Regulation


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


def _load_move_bans() -> dict[PokemonName, dict[Regulation, frozenset[MoveName]]]:
    """regulation/move_ban.csv から種族ごとの使用禁止技を読み込む。"""
    regulation_path = resources.files("jpoke").joinpath("data", "regulation", "move_ban.csv")
    bans_by_pokemon: dict[PokemonName, dict[Regulation, set[MoveName]]] = {}

    with regulation_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None, "regulation/move_ban.csv のヘッダが読み取れません"
        regulation_names = [
            name for name in reader.fieldnames if name not in {"species", "move"}
        ]

        for row in reader:
            move = row["move"]
            assert move in typing.get_args(MoveName), f"regulation/move_ban.csv に未定義の技名があります: {move}"
            bans = bans_by_pokemon.setdefault(row["species"], {})
            for regulation in regulation_names:
                if row[regulation] == "1":
                    bans.setdefault(regulation, set()).add(move)

    return {
        species: {regulation: frozenset(moves) for regulation, moves in bans.items()}
        for species, bans in bans_by_pokemon.items()
    }


file = resource_path('data', 'ps-champ-ja', "pokedex.json")
with open(file, encoding='utf-8') as f:
    data = json.load(f)

pokemon_regulations = _load_pokemon_regulations()
move_bans = _load_move_bans()

POKEDEX: dict[PokemonName, PokemonData] = {
    name: PokemonData(name, entry, LEARNSETS.get(name)) for name, entry in data.items()
}

for name in pokemon_regulations:
    assert name in POKEDEX, f"regulation/pokemon.csv に未定義のポケモン名があります: {name}"

for name in POKEDEX:
    POKEDEX[name].regulations = set(pokemon_regulations.get(name, set()))

for name in move_bans:
    assert name in POKEDEX, f"regulation/move_ban.csv に未定義のポケモン名があります: {name}"

for name in POKEDEX:
    POKEDEX[name].banned_moves = dict(move_bans.get(name, {}))


def get_pokemon_by_regulation(regulation: Regulation) -> list[PokemonName]:
    """指定レギュレーションで使用可能なポケモン名の一覧を返す（五十音順）。"""
    return sorted(name for name, data in POKEDEX.items() if regulation in data.regulations)


def get_banned_moves(species: PokemonName, regulation: Regulation) -> frozenset[MoveName]:
    """指定の種族が指定のレギュレーションで使用を禁止されている技の集合を返す。"""
    return POKEDEX[species].banned_moves.get(regulation, frozenset())
