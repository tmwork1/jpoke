import requests
from importlib import resources
import json
import os
from datetime import datetime


def resource_path(*path_parts: str) -> str:
    """リソースファイルのパスを取得
    Args:
        path_parts: パスの各部分
    """
    return str(resources.files("jpoke").joinpath(*path_parts))


# 定数
DOWNLOAD_TIMEOUT = 10  # ダウンロードのタイムアウト秒数
UPDATE_LOGFILE = resource_path("data", "last_update.json")


def get_current_date(fmt: str = "%Y-%m-%d") -> str:
    return datetime.now().strftime(fmt)


def download(url: str, dst: str) -> bool:
    try:
        print(f"Downloading {url} ... ", end="")
        res = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
        with open(dst, 'w', encoding='utf-8') as fout:
            fout.write(res.text)
        print("Done")
        return True
    except (requests.RequestException, OSError, IOError) as e:
        print(f"Failed to download {url}: {e}")
        return False


def load_update_log(file: str) -> str:
    """JSONから最終更新日を読み込む"""
    if not os.path.exists(UPDATE_LOGFILE):
        return ""
    with open(UPDATE_LOGFILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get(file, "")


def save_update_log(file: str):
    """最終更新日をJSONに保存"""
    data = {}
    if os.path.exists(UPDATE_LOGFILE):
        with open(UPDATE_LOGFILE, encoding="utf-8") as f:
            data = json.load(f)
    data[file] = get_current_date()
    with open(UPDATE_LOGFILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def needs_update(file: str) -> bool:
    """今日更新済みか確認"""
    if not os.path.exists(file):
        return True
    else:
        return load_update_log(file) != get_current_date()
