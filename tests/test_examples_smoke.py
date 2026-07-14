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

# スモークテストの目的は「エラーなく終了すること」の確認のみであり、README掲載用の
# 実測値を得ることではない。01_step_time_benchmark.py は既定（300バトル×最大100ターン）
# だとCPU負荷・実行時間が非常に大きく、CI環境やこのリポジトリのような並列実行環境下では
# OSによる強制終了（returncode=-1、stdout/stderrともに空）が間欠的に発生していた。
# スモーク目的には無関係な負荷のため、このスクリプトのみ試行回数を大幅に絞って実行する。
EXTRA_ARGS: dict[str, list[str]] = {
    "05_benchmark/01_step_time_benchmark.py": ["--n-battles", "5", "--max-turns", "20"],
}


@pytest.mark.parametrize("script_name", EXAMPLE_SCRIPTS)
def test_examples_エラーなく実行できる(script_name):
    script_path = EXAMPLES_DIR / script_name

    result = subprocess.run(
        [sys.executable, str(script_path), *EXTRA_ARGS.get(script_name, [])],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, result.stderr
