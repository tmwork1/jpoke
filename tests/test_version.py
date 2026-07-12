"""バージョン番号の二重管理チェック。

`jpoke.__version__` は `importlib.metadata` の import コストを避けるため
`pyproject.toml` の `version` とは独立したリテラルとして `src/jpoke/__init__.py`
に直書きしている。手動同期が前提のため、両者がズレていないかを検証する。
"""
import re
from pathlib import Path

import pytest

import jpoke

def _pyproject_version() -> str:
    """pyproject.toml の [project] version を正規表現で抽出する。

    プロジェクトは Python 3.10+ を対象としており `tomllib`（3.11+ 標準）を
    単体では使えないため、正規表現による軽量な抽出で代替する。
    """
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    text = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    assert match is not None, "pyproject.toml に version 行が見つからない"
    return match.group(1)


def test_バージョン番号がpyproject_tomlとsrc_jpoke初期化ファイルで一致している():
    """`pyproject.toml` の version と `jpoke.__version__` が一致することを確認する。

    `pyproject.toml` の version を上げる際は `src/jpoke/__init__.py` の
    `__version__` も同じ値に手動で揃える必要がある。このテストがズレを検知する。
    """
    assert jpoke.__version__ == _pyproject_version()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
