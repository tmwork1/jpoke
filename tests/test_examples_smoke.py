"""examples/ 配下のサンプルスクリプトのスモークテスト。

`pip install jpoke` した一般ユーザーがそのまま実行できることを保証するため、
各サンプルを実際にサブプロセスとして起動し、エラーなく終了する（returncode == 0）
ことだけを確認する。壊れたサンプルが放置されるのを防ぐ目的。
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = ROOT / "examples"

EXAMPLE_SCRIPTS = sorted(
    p.relative_to(EXAMPLES_DIR).as_posix() for p in EXAMPLES_DIR.glob("**/*.py")
)


@pytest.mark.parametrize("script_name", EXAMPLE_SCRIPTS)
def test_examples_エラーなく実行できる(script_name):
    script_path = EXAMPLES_DIR / script_name

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, result.stderr
