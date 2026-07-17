"""examples/ 配下のサンプルのスモークテスト。

`pip install jpoke` した一般ユーザーがそのまま実行できることを保証するため、
各サンプルを実際にサブプロセスとして起動し、エラーなく終了する（returncode == 0）
ことだけを確認する。壊れたサンプルが放置されるのを防ぐ目的。

サンプルの大半はGoogle Colabで開けるJupyter Notebook（`.ipynb`）化されており、
papermillでノートブックとして実行して確認する。重い処理・並列処理を含み
notebook化していないもの（`04_research/03,04` のnash系2本）だけは、従来どおり
`.py` をサブプロセスで実行する。
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = ROOT / "examples"

NOTEBOOK_EXAMPLES = sorted(
    p.relative_to(EXAMPLES_DIR).as_posix() for p in EXAMPLES_DIR.glob("**/*.ipynb")
)
PY_EXAMPLES = sorted(
    p.relative_to(EXAMPLES_DIR).as_posix() for p in EXAMPLES_DIR.glob("**/*.py")
)

# スモークテストの目的は「エラーなく終了すること」の確認のみであり、README掲載用の
# 実測値を得ることではない。01_step_time_benchmark.ipynb は既定（300バトル×最大100ターン）
# だとCPU負荷・実行時間が非常に大きく、CI環境やこのリポジトリのような並列実行環境下では
# OSによる強制終了が間欠的に発生していた。スモーク目的には無関係な負荷のため、この
# ノートブックのみ papermill の parameters セルへのパラメータ差し替えで試行回数を絞る。
NOTEBOOK_PARAMETERS: dict[str, dict[str, int]] = {
    "05_benchmark/01_step_time_benchmark.ipynb": {"n_battles": 5, "max_turns": 20},
}


@pytest.mark.parametrize("notebook_name", NOTEBOOK_EXAMPLES)
def test_notebook_examples_エラーなく実行できる(notebook_name, tmp_path):
    notebook_path = EXAMPLES_DIR / notebook_name
    output_path = tmp_path / "output.ipynb"

    extra_params = []
    for key, value in NOTEBOOK_PARAMETERS.get(notebook_name, {}).items():
        extra_params += ["-p", key, str(value)]

    result = subprocess.run(
        [sys.executable, "-m", "papermill", str(notebook_path), str(output_path), *extra_params],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("script_name", PY_EXAMPLES)
def test_py_examples_エラーなく実行できる(script_name):
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
