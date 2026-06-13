#!/usr/bin/env python3
"""move_list.txt の内容を docs/spec/moves/_all_moves.md に反映する。

move_list.txt: 2行/技 (1行目: 技名/タイプ/分類/威力/命中/PP/接触/守る、2行目: 対象/効果)
_all_moves.md: 1行/技のTSV (技名/タイプ/分類/威力/命中/PP/接触/守る/対象/効果)
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "docs" / "champions" / "move_list.txt"
DST = ROOT / "docs" / "spec" / "moves" / "_all_moves.md"


def parse_move_list(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()

    # Skip until the data line (技名で始まる行の次)
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("名前\t"):
            start = i + 2  # skip "名前..." and "対象	効果" header
            break

    moves = []
    i = start
    while i < len(lines):
        line1 = lines[i].strip()
        if not line1:
            i += 1
            continue
        line2 = lines[i + 1].strip() if i + 1 < len(lines) else ""
        i += 2

        parts1 = line1.split("\t")
        parts2 = line2.split("\t")

        if len(parts1) < 6:
            continue

        name = parts1[0]
        type_ = parts1[1]
        category = parts1[2]
        power = parts1[3]
        accuracy = parts1[4]
        pp = parts1[5]
        contact = parts1[6] if len(parts1) > 6 else ""
        protect = parts1[7] if len(parts1) > 7 else ""
        target = parts2[0] if parts2 else ""
        effect = parts2[1] if len(parts2) > 1 else ""

        moves.append({
            "技名": name,
            "タイプ": type_,
            "分類": category,
            "威力": power,
            "命中": accuracy,
            "PP": pp,
            "接触": contact,
            "守る": protect,
            "対象": target,
            "効果": effect,
        })

    return moves


def main():
    moves = parse_move_list(SRC)

    cols = ["技名", "タイプ", "分類", "威力", "命中", "PP", "接触", "守る", "対象", "効果"]
    header = "\t".join(cols)
    rows = ["\t".join(m[c] for c in cols) for m in moves]

    content = header + "\n" + "\n".join(rows) + "\n"
    DST.write_text(content, encoding="utf-8")
    print(f"Written {len(moves)} moves to {DST}")


if __name__ == "__main__":
    main()
