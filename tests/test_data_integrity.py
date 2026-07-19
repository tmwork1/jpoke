"""データ定義（data/）の整合性テスト。

フラグの typo は実行時に「フラグが立っていない」扱いで静かに間違うため、
全データのフラグが Literal 型に定義済みであることを機械的に検証する。
"""
import csv
from importlib import resources
from typing import get_args

import pytest

from jpoke.data import ABILITIES, MOVES, POKEDEX
from jpoke.data.item import ITEMS
from jpoke.model.pokemon import Pokemon
from jpoke.types import AbilityFlag, MoveFlag


def test_技データ_flagsが全てMoveFlagに定義されている():
    """MOVES の flags に MoveFlag（types/literals.py）未定義の文字列がないことを確認する。"""
    valid = set(get_args(MoveFlag))
    errors = []
    for name, data in MOVES.items():
        unknown = set(data.flags) - valid
        if unknown:
            errors.append(f"{name}: {sorted(unknown)}")
    assert not errors, "MoveFlag に未定義のフラグ:\n" + "\n".join(errors)


def test_技データ_no_effect_in_singlesの技はPokemonのlearnsetから除外される():
    """no_effect_in_singlesフラグを持つ技（味方専用で対象不在・公式無効果技等）が、
    Pokemon.learnset（実戦で使う覚えられる技の集合）に一切含まれないことを確認する。
    """
    no_effect_moves = {name for name, data in MOVES.items() if "no_effect_in_singles" in data.flags}
    assert no_effect_moves, "no_effect_in_singlesフラグを持つ技が1件も無い（フラグ定義の確認漏れ）"

    errors = []
    for name in POKEDEX:
        leaked = Pokemon(name).learnset & no_effect_moves
        if leaked:
            errors.append(f"{name}: {sorted(leaked)}")
    assert not errors, "learnsetから除外されていない技:\n" + "\n".join(errors)


def test_特性データ_flagsが全てAbilityFlagに定義されている():
    """ABILITIES の flags に AbilityFlag（types/literals.py）未定義の文字列がないことを確認する。"""
    valid = set(get_args(AbilityFlag))
    errors = []
    for name, data in ABILITIES.items():
        unknown = set(data.flags) - valid
        if unknown:
            errors.append(f"{name}: {sorted(unknown)}")
    assert not errors, "AbilityFlag に未定義のフラグ:\n" + "\n".join(errors)


def test_アイテムのレギュレーションCSVがITEMSへ反映される():
    """regulation/item.csv の内容と ItemData.regulations が全件一致することを確認する。"""
    regulation_path = resources.files("jpoke").joinpath("data", "regulation", "item.csv")

    with regulation_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None
        regulation_names = [
            name
            for name in reader.fieldnames
            if name not in {"name", "implemented"}
        ]
        expected = {}

        for row in reader:
            if row["implemented"] != "1":
                continue

            expected[row["name"]] = {
                name
                for name in regulation_names
                if row[name] == "1"
            }

    unknown_items = set(expected) - set(ITEMS)
    assert not unknown_items, f"regulation/item.csv に未定義のアイテム名があります: {sorted(unknown_items)}"

    errors = []
    for name, data in ITEMS.items():
        actual = data.regulations
        expected_regulations = expected.get(name, set())
        if actual != expected_regulations:
            errors.append(f"{name}: actual={sorted(actual)}, expected={sorted(expected_regulations)}")

    assert not errors, "ItemData.regulations と regulation/item.csv が一致しません:\n" + "\n".join(errors)


def test_ポケモンのレギュレーションCSVがPOKEDEXへ反映される():
    """regulation/pokemon.csv の内容と PokemonData.regulations が全件一致することを確認する。"""
    regulation_path = resources.files("jpoke").joinpath("data", "regulation", "pokemon.csv")

    with regulation_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None
        regulation_names = [
            name
            for name in reader.fieldnames
            if name not in {"dex_no", "name", "implemented"}
        ]
        expected = {}

        for row in reader:
            if row["implemented"] != "1":
                continue

            expected[row["name"]] = {
                name
                for name in regulation_names
                if row[name] == "1"
            }

    unknown_pokemon = set(expected) - set(POKEDEX)
    assert not unknown_pokemon, f"regulation/pokemon.csv に未定義のポケモン名があります: {sorted(unknown_pokemon)}"

    errors = []
    for name, data in POKEDEX.items():
        actual = data.regulations
        expected_regulations = expected.get(name, set())
        if actual != expected_regulations:
            errors.append(f"{name}: actual={sorted(actual)}, expected={sorted(expected_regulations)}")

    assert not errors, "PokemonData.regulations と regulation/pokemon.csv が一致しません:\n" + "\n".join(errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
