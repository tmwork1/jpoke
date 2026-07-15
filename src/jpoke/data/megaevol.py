from jpoke.types import PokemonName, ItemName

from .pokedex import data as _pokedex_data


def _build_mega_stones() -> dict[ItemName, tuple[PokemonName, PokemonName]]:
    """pokedex.jsonのrequiredItem・forme・numから、メガストーンと(素のフォルム, メガ後の
    フォルム)の対応表を再構築する。

    同じアイテムでメガ後のフォルムが複数（性別違い等でpokedex.json側が分割されている場合）に
    分岐するものは、1アイテム=1フォルムというMEGA_STONESの前提に合わないため対象外とする
    （例: ニャオニクスナイト → メガニャオニクス(オス)/メガニャオニクス(メス) の両方）。
    """
    by_num: dict[int, list[tuple[PokemonName, dict]]] = {}
    for name, entry in _pokedex_data.items():
        by_num.setdefault(entry["num"], []).append((name, entry))

    mega_names_by_item: dict[ItemName, list[PokemonName]] = {}
    for name, entry in _pokedex_data.items():
        item = entry.get("requiredItem", "")
        if item and "Mega" in entry.get("forme", ""):
            mega_names_by_item.setdefault(item, []).append(name)

    mega_stones: dict[ItemName, tuple[PokemonName, PokemonName]] = {}
    for item, mega_names in mega_names_by_item.items():
        if len(mega_names) != 1:
            continue
        mega_name = mega_names[0]
        num = _pokedex_data[mega_name]["num"]
        pre_form = next(n for n, e in by_num[num] if e.get("forme", "") == "")
        mega_stones[item] = (pre_form, mega_name)

    return mega_stones


MEGA_STONES: dict[ItemName, tuple[PokemonName, PokemonName]] = _build_mega_stones()

MEGA_POKEMONS = frozenset(v[-1] for v in MEGA_STONES.values())
