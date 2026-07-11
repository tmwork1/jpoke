"""Battle対戦オプション（メガシンカ/テラスタル可否・急所モード・ダメージ乱数モード・命中率固定・効果確率フィルタ）のテスト"""
import pytest

from jpoke import Pokemon
from jpoke.core import EventContext
from jpoke.enums import Command

from . import test_utils as t


def test_ダブルバトル_複数対象になり得る技はダメージ0_75倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハイパーボイス"])],
        team1=[Pokemon("ピカチュウ")],
        double_battle=True,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 3072


def test_ダブルバトルでも単体技は複数対象補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        double_battle=True,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 4096


def test_ダブルバトルで壁と複数対象補正が重複する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハイパーボイス"])],
        team1=[Pokemon("ピカチュウ")],
        side1={"ひかりのかべ": 5},
        double_battle=True,
    )
    t.fix_random(battle, 0.999)  # 急所になると壁の軽減が無視されるため固定
    t.run_move(battle, 0)
    # 0.75倍(3072) と 2/3倍(2732) の重複補正
    assert battle.damage_calculator.damage_modifier == 2049


def test_ダブルバトルで壁の軽減率が2_3倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        side1={"リフレクター": 5},
        double_battle=True,
    )
    t.fix_random(battle, 0.999)  # 急所になると壁の軽減が無視されるため固定
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 2732


def test_ダブルバトルのテラクラスターはステラテラスタル時のみ複数対象補正():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", tera_type="ステラ", move_names=["テラクラスター"])],
        team1=[Pokemon("ピカチュウ")],
        double_battle=True,
    )
    attacker, defender = battle.actives

    # テラスタル前は補正なし
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 4096

    # ステラテラスタル後は0.75倍
    attacker.terastallize()
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 3072


def test_ダブルバトル無効なら壁の軽減率は従来通り1_2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        side1={"リフレクター": 5},
        double_battle=False,
    )
    t.fix_random(battle, 0.999)  # 急所になると壁の軽減が無視されるため固定
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 2048


def test_ダブルバトル無効なら複数対象技も等倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハイパーボイス"])],
        team1=[Pokemon("ピカチュウ")],
        double_battle=False,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 4096


@pytest.mark.parametrize(
    ("damage_roll",),
    [("平均",), ("最大",), ("最小",)],
)
def test_ダメージ乱数モード(damage_roll: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        damage_roll=damage_roll,
    )
    attacker, defender = battle.actives
    damages = battle.calc_damages(attacker, defender, "たいあたり", critical=False)
    rolled = battle.roll_damage(attacker, defender, "たいあたり", critical=False)

    match damage_roll:
        case "平均":
            from jpoke.utils.math import round_half_down
            assert rolled == round_half_down(sum(damages) / len(damages))
        case "最大":
            assert rolled == max(damages)
        case "最小":
            assert rolled == min(damages)


def test_テラスタル不可オプションでコマンドが出ない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        terastal=False,
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    assert Command.TERASTAL_0 not in commands


def test_デフォルトではメガシンカ_テラスタルのコマンドが出る():
    battle = t.start_battle(
        team0=[Pokemon("リザードン", item_name="リザードナイトX")],
        team1=[Pokemon("ピカチュウ")],
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    assert Command.MEGAEVOL_0 in commands
    assert Command.TERASTAL_0 in commands


def test_メガシンカ不可オプションでコマンドが出ない():
    battle = t.start_battle(
        team0=[Pokemon("リザードン", item_name="リザードナイトX")],
        team1=[Pokemon("ピカチュウ")],
        mega_evolution=False,
    )
    player = battle.players[0]
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player)
    assert Command.MEGAEVOL_0 not in commands


def test_効果確率フィルタ_閾値以上は通常通り():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        effect_chance_threshold=0.5,
    )
    mon = battle.actives[0]
    ctx = EventContext(source=mon)
    chance = battle.resolve_secondary_chance(ctx, 0.5)
    assert chance == 0.5


def test_効果確率フィルタ_閾値未満は発生しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        effect_chance_threshold=0.5,
    )
    mon = battle.actives[0]
    ctx = EventContext(source=mon)
    t.fix_random(battle, 0.0)  # 乱数を最小に固定しても発生しないことを確認
    chance = battle.resolve_secondary_chance(ctx, 0.3)
    assert chance == 0.0


def test_命中率固定_閾値以上は必中になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハイドロポンプ"])],  # 命中80
        team1=[Pokemon("ピカチュウ")],
        accuracy_fix_threshold=80,
    )
    t.fix_random(battle, 0.999)  # 通常計算なら外れる乱数
    t.run_move(battle, 0)
    assert battle.move_executor.move_missed is False


def test_命中率固定_閾値未満は通常通り外れうる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハイドロポンプ"])],  # 命中80
        team1=[Pokemon("ピカチュウ")],
        accuracy_fix_threshold=81,
    )
    t.fix_random(battle, 0.999)  # 通常計算なら外れる乱数
    t.run_move(battle, 0)
    assert battle.move_executor.move_missed is True


def test_確定のみモードで確定急所技は急所になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あんこくきょうだ"])],
        team1=[Pokemon("ピカチュウ")],
        critical_mode="確定のみ",
    )
    t.fix_random(battle, 0.999)  # 乱数を最大寄りに固定しても急所になることを確認
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_確定のみモードで通常技はランク補正があっても急所にならない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="きょううん", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        critical_mode="確定のみ",
    )
    # 1/24(ランク0) < 0.05 < 1/8(きょううんによるランク1) となる値に固定し、
    # ランク補正を経由していれば急所になるがそうでなければならないことを確認する
    t.fix_random(battle, 0.05)
    t.run_move(battle, 0)
    assert battle.move_executor.critical_rank == 0
    assert battle.move_executor.critical is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
