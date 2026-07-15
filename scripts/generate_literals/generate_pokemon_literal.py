#!/usr/bin/env python3
"""PokemonName の Literal 定義を data/pokedex.json から自動生成するスクリプト。

使い方:
    python scripts/generate_literals/generate_pokemon_literal.py

処理内容:
- src/jpoke/data/pokedex.json を json.load で読み込み、各エントリのキー（ポケモン名）を
  定義順のまま抽出する
- src/jpoke/types/pokemon.py 内の `PokemonName = Literal[...]` の
  複数行ブロックを、抽出した名前から再構築した内容（1行1要素）で置換する
- 冪等に実行できる（再実行しても同じ結果になる）
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
POKEDEX_JSON = ROOT / "src/jpoke/data/pokedex.json"
TYPE_DEFS_PY = ROOT / "src/jpoke/types/pokemon.py"

GENERATED_COMMENT = (
    "    # 自動生成: python scripts/generate_literals/generate_pokemon_literal.py で更新"
    "（元: src/jpoke/data/pokedex.json）"
)


def extract_pokemon_names(target: Path) -> list[str]:
    """pokedex.jsonの各エントリのキー(ポケモン名)を定義順に抽出する（重複除去）。"""
    data = json.loads(target.read_text(encoding="utf-8"))

    names = []
    seen = set()
    for name in data.keys():
        if not isinstance(name, str):
            print("エラー: キーが文字列ではありません", file=sys.stderr)
            sys.exit(1)

        if name in seen:
            continue
        seen.add(name)
        names.append(name)

    return names


def build_literal_block(names: list[str]) -> list[str]:
    """PokemonName = Literal[...] 形式の複数行ブロックを生成する。"""
    lines = ["PokemonName = Literal[", GENERATED_COMMENT]
    lines.extend(f'    "{n}",' for n in names)
    lines.append("]")
    return lines


def update_literal_file(target: Path, new_block: list[str]) -> None:
    """types/pokemon.py内のPokemonName定義ブロックを置換する。"""
    content = target.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=False)

    start_index = -1
    for i, line in enumerate(lines):
        if line == "PokemonName = Literal[":
            start_index = i
            break

    if start_index == -1:
        print("エラー: PokemonName定義ブロックが見つかりません", file=sys.stderr)
        sys.exit(1)

    end_index = -1
    for i in range(start_index + 1, len(lines)):
        if lines[i] == "]":
            end_index = i
            break

    if end_index == -1:
        print("エラー: PokemonName定義ブロックの終端が見つかりません", file=sys.stderr)
        sys.exit(1)

    current_block = lines[start_index:end_index + 1]
    if current_block == new_block:
        print("変更なし: PokemonName定義は既に最新です")
        return

    lines[start_index:end_index + 1] = new_block
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"更新: {target} の {start_index + 1}〜{start_index + len(new_block)} 行目")


def main() -> None:
    names = extract_pokemon_names(POKEDEX_JSON)
    print(f"抽出した名前数: {len(names)}")

    new_block = build_literal_block(names)
    update_literal_file(TYPE_DEFS_PY, new_block)


if __name__ == "__main__":
    main()
