"""テスト全体で共有するpytest設定・ヘルパー。"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def resolve_subprocess_python(*required_modules: str) -> str:
    """`subprocess.run` で子プロセスを起動する際に使うインタプリタを解決する。

    pytest自体は `pyproject.toml` の `pythonpath` 設定により `sys.path` 経由で
    `jpoke` をimportできるため、どのインタプリタで起動されてもテスト収集自体は
    成功する。しかし `subprocess.run([sys.executable, ...])` で起動する子プロセスは
    この恩恵を受けず、`sys.executable` が指す実際のインタプリタに `required_modules`
    が実インストールされている必要がある（Bashセッションによっては `python` の
    解決先がぶれ、`papermill`/`jpoke` 未インストールのシステムPythonで
    `sys.executable` が解決されることがある）。

    リポジトリ直下に `.venv` があり、かつそちらに `required_modules` がすべて
    インストール済みならそちらを優先する（開発者のセットアップを尊重する）。
    見つからない・使えない場合は従来どおり `sys.executable` にフォールバックする
    （`.venv` を持たないCI環境はこちらを使う）。
    """
    venv_python = ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / (
        "python.exe" if os.name == "nt" else "python"
    )
    if venv_python.exists():
        check_script = "; ".join(f"import {name}" for name in required_modules) or "pass"
        check = subprocess.run([str(venv_python), "-c", check_script], capture_output=True)
        if check.returncode == 0:
            return str(venv_python)
    return sys.executable
