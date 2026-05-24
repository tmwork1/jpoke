from __future__ import annotations

import ast
from pathlib import Path


TESTS_DIR = Path("tests")
OUTPUT_DIR = Path("docs/test")


def extract_parametrize_cases(
    decorator: ast.Call,
) -> list[str]:
    if len(decorator.args) < 2:
        return []

    arg_names_node = decorator.args[0]
    values_node = decorator.args[1]

    if not isinstance(arg_names_node, ast.Constant):
        return []

    if not isinstance(values_node, (ast.List, ast.Tuple)):
        return []

    arg_names = [
        s.strip()
        for s in arg_names_node.value.split(",")
    ]

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

        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue

            if not (
                isinstance(dec.func, ast.Attribute)
                and dec.func.attr == "parametrize"
            ):
                continue

            cases = extract_parametrize_cases(dec)

            for case in cases:
                names.append(
                    f"{base_name}({case})"
                )

            parametrized = True

        if not parametrized:
            names.append(base_name)

    return names


def write_markdown(
    output_path: Path,
    test_names: list[str],
) -> None:
    lines = [
        f"# {output_path.stem}",
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

    for test_file in TESTS_DIR.rglob("test_*.py"):
        relative = test_file.relative_to(TESTS_DIR)

        output_path = (
            OUTPUT_DIR
            / relative.with_suffix(".md")
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        test_names = extract_test_names(
            test_file
        )

        write_markdown(
            output_path,
            test_names,
        )

        print(f"generated: {output_path}")


if __name__ == "__main__":
    main()
