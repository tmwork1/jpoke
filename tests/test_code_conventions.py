"""コーディング規約（CLAUDE.md）の機械的な検証テスト。

`Pokemon.hp` への直接代入は禁止で、必ず `battle.modify_hp(...)` 等を経由する規約になっている。
実行時に property 化するとテストのセットアップ代入（`mon.hp = ...`）を壊すため、
代わりに src/jpoke 配下のソースを静的に走査して違反を検出する。
"""
import re
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parent.parent / "src" / "jpoke"

# 直接代入が許可されているファイル（相対パス、"/" 区切り）
# - model/pokemon.py: hp の実体を保持するクラス自身の実装
#   （__init__ の初期化、update_stats/set_form でのフォルム変化時のダメージ量維持、
#     modify_hp 内部実装）
# - core/status_manager.py: battle.modify_hp() の実装箇所
# - core/lethal.py: 致死率計算用のスクラッチ状態操作。イベント発火・ログ記録・
#   ひんし判定を意図的に伴わない「仮定計算」のための一時的な hp 書き換え
#   （計算後に元の値へ復元する、または hp_dist から参照用の値を反映するだけ）であり、
#   実バトル進行のHP変化ではないため battle.modify_hp() を経由しない
ALLOWED_FILES = {
    "model/pokemon.py",
    "core/status_manager.py",
    "core/lethal.py",
}

# `.hp = ` 形式の直接代入を検出する（`==` `!=` `<=` `>=` は除外する）
DIRECT_ASSIGNMENT_PATTERN = re.compile(r"(?<![=!<>])\.hp\s*=(?!=)")

def _iter_python_files():
    for path in SRC_ROOT.rglob("*.py"):
        yield path


def test_hp直接代入がallowlist外のファイルに存在しない():
    """src/jpoke 配下で `.hp = ...` の直接代入が許可ファイル以外に無いことを確認する。

    許可ファイル以外で見つかった場合は `battle.modify_hp(...)` 経由に直す必要がある。
    """
    violations = []
    for path in _iter_python_files():
        rel_path = path.relative_to(SRC_ROOT).as_posix()
        if rel_path in ALLOWED_FILES:
            continue

        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if DIRECT_ASSIGNMENT_PATTERN.search(line):
                violations.append(f"{rel_path}:{lineno}: {line.strip()}")

    assert not violations, (
        "hp への直接代入を検出（battle.modify_hp(...) 経由に修正すること）:\n"
        + "\n".join(violations)
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
