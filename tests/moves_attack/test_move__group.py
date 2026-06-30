"""攻撃技ハンドラの単体テスト（グループ）。"""

import pytest
from jpoke import Pokemon
from jpoke.enums import Command
from .. import test_utils as t


@pytest.mark.parametrize("move_name", [
    "クロロブラスト",
    "てっていこうせん",
    "ビックリヘッド",
])
def test_HPコスト技グループ_最大HPの半分を消費する(move_name: str):
    """HPコスト技グループ: 技使用前に自分の最大HPの1/2 を消費する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=[move_name])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    expected_cost = max(1, attacker.max_hp // 2)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_cost


@pytest.mark.parametrize("move_name", [
    "かかとおとし",
    "サンダーダイブ",
    "とびげり",
    "とびひざげり",
])
def test_crash技グループ_外れたとき最大HPの半分を失う(move_name: str):
    """crash技グループ: 技が外れると自分の最大HPの1/2 のダメージを受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=[move_name])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    expected_damage = max(1, attacker.max_hp // 2)
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_damage


@pytest.mark.parametrize(("move_name", "heal_ratio"), [
    ("ウッドホーン",    0.5),
    ("ギガドレイン",    0.5),
    ("きゅうけつ",      0.5),
    ("シャカシャカほう", 0.5),
    ("すいとる",        0.5),
    ("デスウイング",    0.75),
    ("ドレインキッス",  0.75),
    ("ドレインパンチ",  0.5),
    ("パラボラチャージ", 0.5),
    ("むねんのつるぎ",  0.5),
    ("メガドレイン",    0.5),
    ("ゆめくい",        0.5),
])
def test_drain技グループ_回復量が与ダメのheal_ratio倍になる(move_name: str, heal_ratio: float):
    """drain技グループ: 回復量は int(与えたダメージ * heal_ratio) で計算される。

    ゆめくいは相手がねむり状態（ailment1）でないと失敗するため全技に ailment1 を設定している。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=[move_name])],
        team1=[Pokemon("カビゴン")],
        ailment1=("ねむり", 3),
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_damage(battle, 100)
    attacker.hp = 1
    t.run_move(battle, 0)
    expected_heal = int(100 * heal_ratio)
    assert attacker.hp == 1 + expected_heal


@pytest.mark.parametrize(("move_name", "recoil_ratio"), [
    ("アフロブレイク",  1/4),
    ("ウェーブタックル", 1/3),
    ("ウッドハンマー",  1/3),
    ("じごくぐるま",   1/4),
    ("すてみタックル", 1/3),
    ("とっしん",       1/4),
    ("はめつのひかり", 1/2),
    ("フレアドライブ", 1/3),
    ("ブレイブバード", 1/3),
    ("ボルテッカー",   1/3),
    ("もろはのずつき", 1/2),
    ("ワイルドボルト", 1/4),
])
def test_recoil技グループ_反動量が与ダメのrecoil_ratio倍になる(move_name: str, recoil_ratio: float):
    """recoil技グループ: 反動量は max(1, int(与えたダメージ * recoil_ratio)) で計算される。

    team1 にフシギバナ（くさ/どく）を使用する理由:
    - はめつのひかり（ゴースト）はノーマル系への免疫を回避するため
    - じごくぐるま（かくとう）はゴースト系への免疫を回避するため
    - ボルテッカー/ワイルドボルト（でんき）はじめん系への免疫を回避するため
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=[move_name])],
        team1=[Pokemon("フシギバナ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_damage(battle, 100)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    expected_recoil = max(1, int(100 * recoil_ratio))
    assert attacker.hp == hp_before - expected_recoil


def test_ダブルアタック_2回ヒットする():
    """ダブルアタック: 必ず2回ヒットする固定2回攻撃技である。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ダブルアタック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hits_taken == 2


def test_ダブルウイング_2回ヒットする():
    """ダブルウイング: 必ず2回ヒットする固定2回攻撃技である。"""
    battle = t.start_battle(
        team0=[Pokemon("ファイヤー", move_names=["ダブルウイング"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hits_taken == 2


def test_ツインビーム_2回ヒットする():
    """ツインビーム: 必ず2回ヒットする固定2回特殊攻撃技である。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ツインビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hits_taken == 2


@pytest.mark.parametrize(
    ("move_name", "foe_name"),
    [
        ("つのドリル", "ゴース"),
        # ("じわれ", "ピジョン"),
    ],
)
def test_一撃必殺技_タイプ相性で無効化される(move_name: str, foe_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon(foe_name)],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].hp == battle.actives[1].max_hp


def test_一撃必殺技_命中時は相手を一撃で倒す():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つのドリル"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].hp == 0


def test_一撃必殺技_外した時はダメージを与えない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つのドリル"])],
        team1=[Pokemon("ピカチュウ", move_names=["はねる"])],
        accuracy=0,
    )
    before_foe_hp = battle.actives[1].hp

    t.reserve_command(battle,
                      command0=Command.MOVE_0,
                      command1=Command.MOVE_0)
    battle.step()

    assert battle.actives[1].hp == before_foe_hp


@pytest.mark.parametrize("move_name", [
    "じばく",
    "だいばくはつ",
    "ミストバースト",
])
def test_自爆技グループ_使用後に攻撃者がひんしになる(move_name: str):
    """自爆技グループ: ON_PAY_HP で現在HPを全消費し、技使用後に使用者がひんし状態になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=[move_name])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == 0
    assert not attacker.alive
