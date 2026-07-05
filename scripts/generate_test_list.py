from __future__ import annotations

import ast
import shutil
from pathlib import Path


TESTS_DIR = Path("tests")
OUTPUT_DIR = Path("docs/tests")


def extract_parametrize_cases(
    decorator: ast.Call,
) -> list[str]:
    if len(decorator.args) < 2:
        return []

    arg_names_node = decorator.args[0]
    values_node = decorator.args[1]

    arg_names: list[str] | None = None

    if isinstance(arg_names_node, ast.Constant) and isinstance(arg_names_node.value, str):
        # "a, b, c" 形式
        arg_names = [
            s.strip()
            for s in arg_names_node.value.split(",")
        ]
    elif isinstance(arg_names_node, (ast.Tuple, ast.List)):
        # ("a", "b", "c") 形式
        names = []
        for elt in arg_names_node.elts:
            if not (isinstance(elt, ast.Constant) and isinstance(elt.value, str)):
                names = None
                break
            names.append(elt.value)
        arg_names = names

    if arg_names is None:
        return []

    if not isinstance(values_node, (ast.List, ast.Tuple)):
        return []

    cases = []

    for elt in values_node.elts:
        try:
            value = ast.literal_eval(elt)
        except Exception:
            continue

        if not isinstance(value, tuple):
            value = (value,)

        parts = [
            f"{k}={v}"
            for k, v in zip(arg_names, value)
        ]

        cases.append(", ".join(parts))

    return cases


def extract_test_names(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    names = []

    for node in tree.body:
        if not (
            isinstance(node, ast.FunctionDef)
            and node.name.startswith("test_")
        ):
            continue

        base_name = node.name[5:]

        parametrized = False
        found_case = False

        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue

            if not (
                isinstance(dec.func, ast.Attribute)
                and dec.func.attr == "parametrize"
            ):
                continue

            parametrized = True
            cases = extract_parametrize_cases(dec)

            for case in cases:
                names.append(
                    f"{base_name}({case})"
                )
                found_case = True

        # parametrize はあるがケースを解析できなかった場合も、
        # テストが一覧から消えないようベース名を残す
        if not parametrized or not found_case:
            names.append(base_name)

    return names


def write_markdown(
    output_path: Path,
    title: str,
    test_names: list[str],
) -> None:
    lines = [
        f"# {title}",
        "",
        f"テスト数: {len(test_names)}",
        "",
    ]

    lines.extend(
        f"- [x] {name}"
        for name in test_names
    )

    lines.append("")

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # サブディレクトリごとにテストファイルをまとめる
    # tests/subdir/test_*.py → docs/tests/subdir.md（1ファイルに統合）
    # tests/test_*.py → docs/tests/test_xxx.md（個別出力）

    # サブディレクトリを収集
    subdirs: dict[Path, list[Path]] = {}
    top_level_files: list[Path] = []

    for test_file in sorted(TESTS_DIR.rglob("test_*.py")):
        relative = test_file.relative_to(TESTS_DIR)
        parts = relative.parts

        if len(parts) == 1:
            # tests/test_xxx.py（直下ファイル）
            top_level_files.append(test_file)
        else:
            # tests/subdir/test_xxx.py
            subdir = TESTS_DIR / parts[0]
            subdirs.setdefault(subdir, []).append(test_file)

    # 既存のサブディレクトリ出力（docs/tests/subdir/）を削除する
    for subdir in subdirs:
        old_output_subdir = OUTPUT_DIR / subdir.name
        if old_output_subdir.is_dir():
            shutil.rmtree(old_output_subdir)
            print(f"removed: {old_output_subdir}/")

    # サブディレクトリをまとめて1ファイルに出力
    for subdir, test_files in subdirs.items():
        all_names: list[str] = []
        for test_file in test_files:
            all_names.extend(extract_test_names(test_file))

        output_path = OUTPUT_DIR / f"{subdir.name}.md"

        write_markdown(
            output_path,
            title=subdir.name,
            test_names=all_names,
        )

        print(f"generated: {output_path}")

    # トップレベルファイルを個別出力
    generated_top_level: set[Path] = set()

    for test_file in top_level_files:
        relative = test_file.relative_to(TESTS_DIR)
        output_path = OUTPUT_DIR / relative.with_suffix(".md")

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        test_names = extract_test_names(test_file)

        write_markdown(
            output_path,
            title=output_path.stem,
            test_names=test_names,
        )

        generated_top_level.add(output_path)
        print(f"generated: {output_path}")

    # ソースが存在しないレガシーの docs/tests/test_*.md を削除する
    for legacy_md in OUTPUT_DIR.glob("test_*.md"):
        if legacy_md not in generated_top_level:
            legacy_md.unlink()
            print(f"removed legacy: {legacy_md}")


if __name__ == "__main__":
    main()
