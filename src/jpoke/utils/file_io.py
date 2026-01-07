import requests
import jaconv
from importlib import resources
import Levenshtein
import json
import os
from datetime import datetime

from . import text as strut


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def resource_path(*path_parts: str):
    return resources.files("jpoke").joinpath(*path_parts)


def download(url: str, dst) -> bool:
    try:
        print(f"Downloading {url} ... ", end="")
        res = requests.get(url, timeout=10)
        with open(dst, 'w', encoding='utf-8') as fout:
            fout.write(res.text)
        print("Done")
        return True
    except Exception:
        print(f"Failed to download {url}")
        return False


def find_most_similar(str_list, s, ignore_dakuten=False):
    """最も似ている要素を返す"""
    if s in str_list:
        return s

    s1 = jaconv.hira2kata(s)
    if ignore_dakuten:
        s1 = strut.remove_dakuten(s1)
        str_list = list(map(strut.remove_dakuten, str_list))

    distances = [Levenshtein.distance(s1, jaconv.hira2kata(s)) for s in str_list]

    return str_list[distances.index(min(distances))]


LAST_UPDATE_LOG = str(resource_path("data", "last_update.json"))


def load_last_update(file: str) -> str:
    """JSONから最終更新日を読み込む"""
    if not os.path.exists(LAST_UPDATE_LOG):
        return ""
    with open(LAST_UPDATE_LOG, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get(file, "")


def save_last_update(file: str):
    """最終更新日をJSONに保存"""
    data = {}
    if os.path.exists(LAST_UPDATE_LOG):
        with open(LAST_UPDATE_LOG, encoding="utf-8") as f:
            data = json.load(f)
    data[file] = today()
    with open(LAST_UPDATE_LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def needs_update(file: str) -> bool:
    """今日更新済みか確認"""
    if not os.path.exists(file):
        return True
    else:
        return load_last_update(file) != today()
