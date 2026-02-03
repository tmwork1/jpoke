import sys
import pytest
from pathlib import Path

# カレントディレクトリがどこであってもテストが実行できるようにする
TEST_DIR = Path(__file__).parent


def main(pattern: str = "*.py"):
    """Run pytest on test files matching the pattern.

    Args:
        pattern: Glob pattern for test files (default: "*.py")

    Returns:
        pytest exit code
    """
    # デフォルトでは全テストファイル（test_*.py と *_test.py）を実行
    test_files = []
    for py_file in TEST_DIR.glob(pattern):
        if py_file.stem not in ["run", "test_utils", "__pycache__"]:
            test_files.append(py_file)

    # パターンが指定されていない場合は全テストファイルを対象
    if not test_files or pattern == "*.py":
        test_files = []
        for py_file in TEST_DIR.glob("*.py"):
            if py_file.stem not in ["run", "test_utils"]:
                test_files.append(py_file)

    if not test_files:
        print(f"No test files matched: {TEST_DIR}/{pattern}")
        return 1

    # pytest で実行
    # -v: 詳細出力
    # -x: 最初のエラーで停止
    # -s: print文の出力を表示
    args = ["-v", "-s"] + [str(f) for f in sorted(test_files)]
    exit_code = pytest.main(args)
    return exit_code


if __name__ == "__main__":
    # 例: python run.py  # 全テスト実行
    #    python run.py test_*.py  # パターン指定
    pattern = sys.argv[1] if len(sys.argv) > 1 else "*.py"
    exit_code = main(pattern)
    sys.exit(exit_code)
