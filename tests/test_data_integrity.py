"""データ定義（data/）の整合性テスト。

フラグの typo は実行時に「フラグが立っていない」扱いで静かに間違うため、
全データのフラグが Literal 型に定義済みであることを機械的に検証する。
"""
from typing import get_args

import pytest

from jpoke.data import ABILITIES, MOVES
from jpoke.types import AbilityFlag, MoveFlag


def test_技データ_flagsが全てMoveFlagに定義されている():
    """MOVES の flags に MoveFlag（types/literals.py）未定義の文字列がないことを確認する。"""
    valid = set(get_args(MoveFlag))
    errors = []
    for name, data in MOVES.items():
        unknown = set(data.flags) - valid
        if unknown:
            errors.append(f"{name}: {sorted(unknown)}")
    assert not errors, "MoveFlag に未定義のフラグ:\n" + "\n".join(errors)


def test_特性データ_flagsが全てAbilityFlagに定義されている():
    """ABILITIES の flags に AbilityFlag（types/literals.py）未定義の文字列がないことを確認する。"""
    valid = set(get_args(AbilityFlag))
    errors = []
    for name, data in ABILITIES.items():
        unknown = set(data.flags) - valid
        if unknown:
            errors.append(f"{name}: {sorted(unknown)}")
    assert not errors, "AbilityFlag に未定義のフラグ:\n" + "\n".join(errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
