
import asyncio
import importlib.util
import inspect
import sys
from pathlib import Path
from types import ModuleType

TEST_DIR = Path("tests")


def import_module_from_path(pyfile: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(pyfile.stem, pyfile)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {pyfile}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[pyfile.stem] = module
    spec.loader.exec_module(module)
    return module


async def run_test_callable(fn, module_name: str, file: Path):
    name = f"{module_name}.test"
    try:
        if inspect.iscoroutinefunction(fn):
            await fn()
        else:
            result = fn()
            # result が coroutine の場合も await
            if inspect.iscoroutine(result):
                await result
        print(f"[PASS] {name} ({file})")
        return True
    except Exception as e:
        print(f"[FAIL] {name} ({file}) -> {type(e).__name__}: {e}")
        return False


async def main(pattern: str = "*.py"):
    files = sorted(TEST_DIR.glob(pattern))
    if not files:
        print(f"No test files matched: {TEST_DIR}/{pattern}")
        return 1

    total = 0
    passed = 0
    for file in files:
        module = import_module_from_path(file)
        fn = getattr(module, "test", None)
        if fn is None:
            print(f"[SKIP] {file} (no test() found)")
            continue
        total += 1
        ok = await run_test_callable(fn, module_name=file.stem, file=file)
        passed += int(ok)

    print(f"\nSummary: {passed}/{total} passed")
    return 0 if passed == total else 1

if __name__ == "__main__":
    # 例: python run_tests.py  # tests/*.py を対象
    #    python run_tests.py tests_*.py  # パターン指定も可能
    pattern = sys.argv[1] if len(sys.argv) > 1 else "*.py"
    exit_code = asyncio.run(main(pattern))
    sys.exit(exit_code)
