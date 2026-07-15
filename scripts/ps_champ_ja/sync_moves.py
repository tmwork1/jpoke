"""ps-champ-ja (https://github.com/tmwork1/ps-champ-ja) の data_jp/moves.json を
src/jpoke/data/ps_champ_moves.json にそのまま配置し、ps-champ-jaでカバーされる技について
src/jpoke/data/moves/move_*.py 内の静的パラメータ（type/category/pp/accuracy/priority、
および可変威力・必ず急所センチネル以外のpower/crit_ratio）のリテラル指定を削除する。

削除後は起動時に data/move.py の common_setup() が data/ps_champ_moves.json から
これらの値を読み込むため、move_*.py側との二重保持が無くなる。

対象外:
    - move_symbol.py の擬似技（わるあがき等）
    - ps-champ-jaに存在しない技（716件中216件、既存のリテラル値を維持）
    - power=1（可変威力センチネル）・crit_ratio=3（必ず急所センチネル）を持つ技は
      当該フィールドのみ削除せず残す
    - target（常にソース側の指定を優先するため削除しない）
"""
import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
PS_CHAMP_MOVES_SOURCE = ROOT / "ps-champ-ja/data_jp/moves.json"
SNAPSHOT_PATH = ROOT / "src/jpoke/data/ps_champ_moves.json"
MOVES_DIR = ROOT / "src/jpoke/data/moves"

NAME_ANCHOR = re.compile(r'^\s*"([^"]+)":\s*MoveData\(\s*$')
# 削除対象キーワード引数（power/crit_ratioはセンチネル値の行だけ残す）
STRIPPABLE = re.compile(r'^\s*(type|category|pp|accuracy|priority)=.*,\s*$')
POWER_LINE = re.compile(r'^\s*power=(.*),\s*$')
CRIT_LINE = re.compile(r'^\s*crit_ratio=(.*),\s*$')
CRITICAL_RANK_LINE = re.compile(r'^(\s*)critical_rank=(.*,\s*)$')


def sync_snapshot() -> dict:
    with open(PS_CHAMP_MOVES_SOURCE, encoding="utf-8") as f:
        data = json.load(f)
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return data


def strip_file(path: Path, ps_champ: dict) -> tuple[list[str], int]:
    """move_*.pyの各`"<name>": MoveData(...)`ブロックを走査する。

    括弧の対応関係で深さを追跡し、**MoveData(...)の直接の引数（深さ1）だけ**を
    ストリップ対象にする。`handlers={...}`内の`h.MoveHandler(..., priority=N)`等、
    深さ2以上にネストした同名キーワード引数（ハンドラの発火優先度等）は
    MoveDataの静的パラメータとは無関係なので誤って削除しないようにする。
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    out: list[str] = []
    removed = 0

    i = 0
    current_name: str | None = None
    covered = False
    depth = 0

    while i < len(lines):
        line = lines[i]

        m = NAME_ANCHOR.match(line)
        if m is not None:
            current_name = m.group(1)
            covered = current_name in ps_champ
            depth = 1  # MoveData( の直後（このカッコ自体で深さ1に入る）
            out.append(line)
            i += 1
            continue

        if current_name is not None and depth > 0:
            depth_before_this_line = depth

            crm = CRITICAL_RANK_LINE.match(line)
            if crm is not None:
                line = f"{crm.group(1)}crit_ratio={crm.group(2)}"

            if covered and depth_before_this_line == 1:
                if STRIPPABLE.match(line):
                    removed += 1
                    depth += line.count("(") - line.count(")")
                    i += 1
                    continue
                pm = POWER_LINE.match(line)
                if pm is not None and pm.group(1).strip() != "1":
                    removed += 1
                    depth += line.count("(") - line.count(")")
                    i += 1
                    continue
                cm = CRIT_LINE.match(line)
                if cm is not None and cm.group(1).strip() != "3":
                    removed += 1
                    depth += line.count("(") - line.count(")")
                    i += 1
                    continue

            depth += line.count("(") - line.count(")")
            out.append(line)
            if depth <= 0:
                current_name = None
            i += 1
            continue

        out.append(line)
        i += 1

    return out, removed


def main():
    ps_champ = sync_snapshot()
    print(f"ps_champ_moves.json 更新: {len(ps_champ)}件")

    total_removed = 0
    for path_str in sorted(glob.glob(str(MOVES_DIR / "move_*.py"))):
        path = Path(path_str)
        if path.name == "move_symbol.py":
            continue

        new_lines, removed = strip_file(path, ps_champ)
        if removed:
            path.write_text("\n".join(new_lines), encoding="utf-8")
            print(f"{path.name}: {removed}行削除")
        total_removed += removed

    print(f"合計: {total_removed}行削除")


if __name__ == "__main__":
    main()
