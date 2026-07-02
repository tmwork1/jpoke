# TODO : 既存のpokedex.jsonを上書きしてしまわないように、存在しない場合のみ実行できるようにする。生成処理をmain()にまとめるとよい。

"""pokedex.json を生成するスクリプト。
zukan.json は、ポケモンの図鑑データを含む JSONファイルである。
このスクリプトは、zukan.json から必要なキーのみを抽出し、pokedex.json を生成する。
"""
import json


INPUT_PATH = "src/jpoke/data/zukan.json"
OUTPUT_PATH = "src/jpoke/data/pokedex.json"

KEEP_KEYS = {
    "alias",
    "weight",
    "height",
    "type-1",
    "type-2",
    "ability-1",
    "ability-2",
    "ability-3",
    "hp",
    "atk",
    "def",
    "spa",
    "spd",
    "spe",
}

RENAME_DICT = {
    "alias": "name",
}

FLOAT_KEYS = ["weight", "height"]

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

filtered = {}

for pokemon_id, pokemon_data in data.items():
    new_data = {}

    for key, value in pokemon_data.items():
        if key not in KEEP_KEYS:
            continue

        if key in FLOAT_KEYS and isinstance(value, str) and value != "":
            if "," in value:
                value = value.replace(",", "")
            value = float(value)

        new_key = RENAME_DICT.get(key, key)
        new_data[new_key] = value

    filtered[pokemon_id] = new_data

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(filtered, f, ensure_ascii=False, indent=4)
