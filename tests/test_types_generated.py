"""AbilityName・ItemName・MoveName・PokemonName の Literal 定義、および
それらを生成する scripts/generate_literals/generate_*_literal.py に関するテスト。

Note:
    これらは Literal 型（実行時の型ヒント）であり、typing.get_args() で
    実際の要素タプルを取得して検証する。
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import get_args

import pytest

from jpoke.data.ability import ABILITIES
from jpoke.data.item import ITEMS
from jpoke.data.megaevol import MEGA_STONES
from jpoke.data.move import MOVES
from jpoke.types import AbilityName, ItemName, MoveName, PokemonName

ROOT = Path(__file__).resolve().parent.parent
POKEDEX_JSON = ROOT / "src/jpoke/data/pokedex.json"

GENERATE_SCRIPTS = [
    ("generate_ability_literal.py", "src/jpoke/types/ability.py"),
    ("generate_item_literal.py", "src/jpoke/types/item.py"),
    ("generate_move_literal.py", "src/jpoke/types/move.py"),
    ("generate_pokemon_literal.py", "src/jpoke/types/pokemon.py"),
]


def test_abilityname_件数がABILITIES辞書と一致する():
    assert len(get_args(AbilityName)) == len(ABILITIES)


def test_abilityname_既知の特性名を含む():
    values = get_args(AbilityName)
    for name in ("", "いかく", "ふゆう", "ものひろい"):
        assert name in values


@pytest.mark.parametrize("script_name, type_file", GENERATE_SCRIPTS)
def test_generateliteralスクリプト_再実行しても差分が出ない(script_name, type_file):
    """生成スクリプトが冪等であることを確認する（既に最新化済みの状態を前提とする）。"""
    script_path = ROOT / "scripts" / "generate_literals" / script_name
    target_path = ROOT / type_file
    before = target_path.read_text(encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, result.stderr

    after = target_path.read_text(encoding="utf-8")
    assert before == after
    assert "変更なし" in result.stdout


def test_itemname_メガストーン名を含む():
    # メガストーンは data/item.py の ITEMS 辞書リテラルには含まれず、
    # data/megaevol.py の MEGA_STONES から実行時に追加される
    values = get_args(ItemName)
    for name in MEGA_STONES:
        assert name in values


def test_itemname_件数が実行時ITEMS辞書と一致する():
    # ITEMS はモジュール読み込み時に common_setup() でメガストーンが追加されるため、
    # 実行時の ITEMS 辞書（メガストーン込み）と件数が一致する必要がある
    assert len(get_args(ItemName)) == len(ITEMS)


def test_itemname_既知のアイテム名を含む():
    values = get_args(ItemName)
    for name in ("", "いのちのたま", "こだわりスカーフ", "たべのこし"):
        assert name in values


def test_movename_件数がMOVES辞書と一致する():
    assert len(get_args(MoveName)) == len(MOVES)


def test_movename_既知の技名を含む():
    values = get_args(MoveName)
    for name in ("わるあがき", "10まんボルト", "じしん", "はかいこうせん"):
        assert name in values


def test_pokemonname_件数がpokedexのユニーク名数と一致する():
    pokedex = json.loads(POKEDEX_JSON.read_text(encoding="utf-8"))
    unique_names = {entry["name"] for entry in pokedex.values()}
    assert len(get_args(PokemonName)) == len(unique_names)


def test_pokemonname_既知のポケモン名を含む():
    values = get_args(PokemonName)
    for name in ("フシギダネ", "ピカチュウ", "ミュウツー"):
        assert name in values
