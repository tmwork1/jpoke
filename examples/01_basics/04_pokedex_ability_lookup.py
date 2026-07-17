"""POKEDEX を使って、ポケモンが持てる特性・覚えられる技を確認する方法を扱う。

バトルを実行せず、`jpoke.data.POKEDEX` という静的なデータだけで完結する
一番手軽な調べ物の例。
"""
from __future__ import annotations

from jpoke.data import POKEDEX


def show_pokedex_abilities() -> None:
    """ポケモンごとに持てる特性は POKEDEX[name].abilities で確認できる
    （通常特性1・2・隠れ特性の順のリスト。持てる特性が1つや2つしかない
    ポケモンでは、存在しない枠は含まれず短いリストになる）。
    """
    for name in ("ライチュウ", "フシギバナ", "ピカチュウ"):
        print(f"{name}が持てる特性: {POKEDEX[name].abilities}")


def show_pokedex_learnset() -> None:
    """ポケモンが覚えられる技の集合は POKEDEX[name].learnset で確認できる
    （frozenset[MoveName]。技数が多く順序も保証されないため、ここでは件数と
    sorted()した先頭数件だけ表示する）。
    """
    for name in ("ライチュウ", "フシギバナ", "ピカチュウ"):
        learnset = POKEDEX[name].learnset
        print(f"{name}が覚えられる技: {len(learnset)}種類（例: {sorted(learnset)[:5]}）")


def main() -> None:
    show_pokedex_abilities()
    show_pokedex_learnset()

    # 注意: add_pokemon(ability_name=...) を省略した場合、特性は自動設定されず
    # Pokemon.ability は空文字のままになる（POKEDEX の情報を見て手動で指定する必要がある）

    # 試してみよう: show_pokedex_abilities() / show_pokedex_learnset() 内のポケモン名を
    # 別の名前に変えて、通常特性・隠れ特性や覚えられる技がそれぞれ何になるか確認できる


if __name__ == "__main__":
    main()
