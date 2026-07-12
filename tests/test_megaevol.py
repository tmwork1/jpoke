"""ダメージ計算のタイプ補正テスト"""
import pytest

from jpoke.data import MEGA_STONES
from jpoke.model import Pokemon
from jpoke.enums import Command

from . import test_utils as t

stones = list(MEGA_STONES.keys())
normal_names = [x[0] for x in MEGA_STONES.values()]
mega_names = [x[-1] for x in MEGA_STONES.values()]

stone_normal_mega = list(zip(stones, normal_names, mega_names))


def test_megaevolve_戻り値はNone():
    """Pokemon.megaevolve()はフォルムを切り替えるだけの内部メソッドであり、
    戻り値は常にNone（成功/失敗を示すbool値ではない）。"""
    battle = t.start_battle(
        team0=[Pokemon("バンギラス", item_name="バンギラスナイト")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    result = mon.megaevolve()
    assert result is None
    assert mon.name == "メガバンギラス"


def test_megaevolved_繰り返し判定しても結果が変わらない():
    """MEGA_POKEMONSがジェネレータ式に戻ると、in判定を繰り返すうちに
    非メガシンカ形の判定（イテレータ消費）を経て以後megaevolvedが常にFalseを返す
    退行バグが再発する。frozenset化により何度呼び出しても結果が安定することを確認する"""
    battle = t.start_battle(
        team0=[Pokemon("バンギラス", item_name="バンギラスナイト")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.reserve_command(battle, Command.MEGAEVOL_0)
    battle.step()

    mon = battle.actives[0]
    assert mon.name == "メガバンギラス"
    # 非メガシンカ形を含め繰り返し判定しても、メガシンカ形の判定結果が変わらないこと
    for _ in range(3):
        assert battle.actives[1].megaevolved is False
    assert mon.megaevolved is True


@pytest.mark.parametrize(
    ("stone", "normal_name", "mega_name"),
    stone_normal_mega[:1]
)
def test_メガシンカ_コマンドが追加される(stone: str, normal_name: str, mega_name: str):
    battle = t.start_battle(
        team0=[Pokemon(normal_name, item_name=stone)],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    assert Command.MEGAEVOL_0 in commands


@pytest.mark.parametrize(
    ("stone", "normal_name", "mega_name"),
    stone_normal_mega
)
def test_メガシンカ_フォルムが変わる(stone: str, normal_name: str, mega_name: str):
    battle = t.start_battle(
        team0=[Pokemon(normal_name, item_name=stone)],
        team1=[Pokemon("ピカチュウ")],
    )
    t.reserve_command(battle, Command.MEGAEVOL_0)
    battle.step()

    mon = battle.actives[0]
    assert mon.name == mega_name
    assert mon.ability.name == mon.data.abilities[0]


def test_メガシンカ_直後に特性が起動する():
    battle = t.start_battle(
        team0=[Pokemon("バンギラス", item_name="バンギラスナイト")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.weather.name == ""

    t.reserve_command(battle, Command.MEGAEVOL_0)
    battle.step()

    mon = battle.actives[0]
    assert mon.name == "メガバンギラス"
    assert mon.ability.name == "すなおこし"
    assert battle.weather.name == "すなあらし"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
