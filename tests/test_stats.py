"""努力値システム（Champions仕様）のテスト"""
import pytest

from jpoke import Pokemon
from jpoke.model.stats import chmp_to_legacy_effort


def test_努力値_effortプロパティで設定と取得():
    mon = Pokemon("ピカチュウ")
    mon.effort = [0, 32, 1, 2, 31, 16]
    assert mon.effort == [0, 32, 1, 2, 31, 16]


def test_努力値_set_effortで単一インデックス設定():
    mon = Pokemon("ピカチュウ")
    mon.set_effort(1, 32)
    assert mon.effort[1] == 32


def test_努力値_ステータス再計算に反映される():
    mon = Pokemon("ピカチュウ", nature="いじっぱり")
    hp_before = mon.stats["hp"]
    atk_before = mon.stats["atk"]
    mon.set_effort(0, 32)
    mon.set_effort(1, 32)
    assert mon.stats["hp"] > hp_before
    assert mon.stats["atk"] > atk_before


@pytest.mark.parametrize(
    ("effort_chmp", "effort_sv"),
    [
        (0, 0),
        (1, 4),
        (2, 12),
        (3, 20),
        (31, 244),
        (32, 252),
    ]
)
def test_努力値変換_チャンピオンズからSV(effort_chmp: int, effort_sv: int):
    assert chmp_to_legacy_effort(effort_chmp) == effort_sv
