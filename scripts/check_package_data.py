#!/usr/bin/env python3
"""src/jpoke/data 配下のデータファイルがビルド済みwheelに漏れなく同梱されているか検証するスクリプト。

想定される使い方（CI）:
    python -m build -w .
    pip install dist/*.whl
    python scripts/check_package_data.py

`pip install` した環境に対して実行する（importする jpoke はインストール済みのものを指す）。
pyproject.toml の [tool.setuptools.package-data] のパターン漏れで、実行時に
importlib.resources 経由で読むデータファイルが同梱されない事故を検出する。
"""
import sys
from pathlib import Path

_EXCLUDE_SUFFIXES = {".py", ".pyc"}
_EXCLUDE_DIR_NAMES = {"__pycache__"}


def _collect_data_files(root: Path) -> set[str]:
    files = set()
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if path.suffix in _EXCLUDE_SUFFIXES:
            continue
        if _EXCLUDE_DIR_NAMES & set(path.relative_to(root).parts):
            continue
        files.add(path.relative_to(root).as_posix())
    return files


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    source_dir = repo_root / "src" / "jpoke" / "data"

    import jpoke  # インストール済み（wheel由来）のパッケージを解決する

    installed_dir = Path(jpoke.__file__).resolve().parent / "data"

    source_files = _collect_data_files(source_dir)
    installed_files = _collect_data_files(installed_dir)

    missing = sorted(source_files - installed_files)
    if missing:
        print("以下のデータファイルがビルド済みパッケージに同梱されていません:")
        for f in missing:
            print(f"  - {f}")
        print("pyproject.toml の [tool.setuptools.package-data] を確認してください。")
        return 1

    print(f"OK: {len(source_files)} 件のデータファイルすべてが同梱されています。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
