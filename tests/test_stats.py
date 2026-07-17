"""努力値システム（Champions仕様）のテスト"""
import pytest

from jpoke import Player, Pokemon
from jpoke.model.stats import chmp_to_legacy_effort


def test_add_pokemonでevsとivsを省略すると既定値のまま():
    player = Player("p")
    mon = player.add_pokemon("ピカチュウ")

    assert mon.evs == [0, 0, 0, 0, 0, 0]
    assert mon.ivs == [31, 31, 31, 31, 31, 31]


def test_add_pokemonでevsをdict指定すると指定ステータスのみ反映される():
    player = Player("p")
    mon = player.add_pokemon("ピカチュウ", evs={"atk": 32, "spe": 16})

    assert mon.evs == [0, 32, 0, 0, 0, 16]


def test_add_pokemonでevs指定時に生成直後のhpが満タンで追従する():
    """hp_policy既定値keep_absoluteは被ダメージ量（生成直後は0）を維持するため、
    evsでHP実数値が変化してもポケモン生成直後は常に満タンのHPで返る。"""
    player = Player("p")
    mon = player.add_pokemon("ピカチュウ", evs={"hp": 32})

    assert mon.max_hp != Pokemon("ピカチュウ").max_hp
    assert mon.hp == mon.max_hp


def test_add_pokemonでivsをdict指定すると指定ステータスのみ反映される():
    player = Player("p")
    mon = player.add_pokemon("ピカチュウ", ivs={"spa": 0})

    assert mon.ivs == [31, 31, 31, 0, 31, 31]


def test_ステータス実数値設定_set_statsで6項目に満たない辞書を渡すと他のステータスは変化しない():
    mon = Pokemon("ピカチュウ")
    ref = Pokemon("ピカチュウ")
    ref.set_evs([0, 0, 0, 0, 0, 32])
    target_spe = ref.stats["spe"]
    before = dict(mon.stats)

    mon.set_stats({"spe": target_spe})

    assert mon.stats["spe"] == target_spe
    for key in ("hp", "atk", "def", "spa", "spd"):
        assert mon.stats[key] == before[key]


def test_ステータス実数値設定_set_statsでキー順が典型順と異なる辞書でも正しく反映される():
    """set_statsは辞書のキーで対象ステータスを引くため、キー順が
    典型順（hp, atk, def, spa, spd, spe）と異なっても正しく反映される。"""
    mon = Pokemon("ピカチュウ")
    ref = Pokemon("ピカチュウ")
    ref.set_evs([0, 32, 20, 0, 0, 0])
    target_def = ref.stats["def"]
    target_atk = ref.stats["atk"]
    hp_before = mon.stats["hp"]
    spa_before = mon.stats["spa"]

    mon.set_stats({"def": target_def, "atk": target_atk})  # 典型順（atk→def）と逆順

    assert mon.stats["def"] == target_def
    assert mon.stats["atk"] == target_atk
    assert mon.stats["hp"] == hp_before
    assert mon.stats["spa"] == spa_before


@pytest.mark.parametrize(
    ("level", "iv_hp", "ev_hp"),
    [
        (1, 0, 0),
        (43, 31, 0),
        (50, 0, 32),
        (100, 31, 32),
    ]
)
def test_ヌケニンはレベル個体値努力値に関わらずHP実数値が常に1固定(level: int, iv_hp: int, ev_hp: int):
    """fuzzログ seed=2040で発見: 種族値HP=1のヌケニンが通常式で計算され
    Lv43でHP81になっていた。calc_hp()のbase==1固定分岐を回帰検証する。"""
    mon = Pokemon("ヌケニン", level=level)
    mon.set_ivs({"hp": iv_hp})
    mon.set_evs({"hp": ev_hp})

    assert mon.max_hp == 1
    assert mon.hp == 1


def test_個体値_set_ivsでdict指定すると指定ステータスのみ更新し未指定分は既存値を維持する():
    mon = Pokemon("ピカチュウ")  # 既定値は全て31

    mon.set_ivs({"atk": 0, "spe": 20})

    assert mon.ivs == [31, 0, 31, 31, 31, 20]


def test_個体値_set_ivsでdict指定後にステータスが再計算される():
    mon = Pokemon("ピカチュウ", nature="いじっぱり")
    atk_before = mon.stats["atk"]

    mon.set_ivs({"atk": 0})

    assert mon.stats["atk"] < atk_before


def test_個体値_set_ivsでlist指定すると全体を置き換える():
    mon = Pokemon("ピカチュウ")

    mon.set_ivs([0, 1, 2, 3, 4, 5])

    assert mon.ivs == [0, 1, 2, 3, 4, 5]


def test_個体値_set_ivsのdict部分更新が他インスタンスのivsに影響しない():
    """_ivsは可変listで保持されるため、あるインスタンスへのdict部分更新が
    別インスタンス（同じ既定値から生成）の_ivsを共有・破壊していないか確認する。"""
    mon_a = Pokemon("ピカチュウ")
    mon_b = Pokemon("ピカチュウ")

    mon_a.set_ivs({"atk": 0})

    assert mon_a.ivs[1] == 0
    assert mon_b.ivs[1] == 31
    assert mon_a.ivs is not mon_b.ivs


def test_努力値_keep_ratioを指定するとHP割合が維持される():
    mon = Pokemon("ピカチュウ")
    max_hp_before = mon.max_hp
    mon.hp = max_hp_before // 2  # このテストに限り直接代入で被ダメージ状態を作る
    ratio_before = mon.hp / mon.max_hp

    mon.set_evs([32, 0, 0, 0, 0, 0], hp_policy="keep_ratio")  # HP実数値が変わるように調整

    assert mon.max_hp != max_hp_before
    assert abs(mon.hp / mon.max_hp - ratio_before) < 0.01


def test_努力値_resetを指定すると被ダメージ状態でも満タンになる():
    mon = Pokemon("ピカチュウ")
    mon.hp = mon.max_hp - 10  # このテストに限り直接代入で被ダメージ状態を作る

    mon.set_evs([32, 0, 0, 0, 0, 0], hp_policy="reset")  # HP実数値が変わるように調整

    assert mon.hp == mon.max_hp


def test_努力値_set_evs_atで単一インデックス設定():
    mon = Pokemon("ピカチュウ")
    mon.set_evs_at(1, 32)
    assert mon.evs[1] == 32


def test_努力値_set_evsでdict指定すると指定ステータスのみ更新し未指定分は既存値を維持する():
    mon = Pokemon("ピカチュウ")
    mon.set_evs([1, 2, 3, 4, 5, 6])

    mon.set_evs({"hp": 32, "def": 10})

    assert mon.evs == [32, 2, 10, 4, 5, 6]


def test_努力値_set_evsで設定と取得():
    mon = Pokemon("ピカチュウ")
    mon.set_evs([0, 32, 1, 2, 31, 16])
    assert mon.evs == [0, 32, 1, 2, 31, 16]


def test_努力値_set_evsのdict部分更新が他インスタンスのevsに影響しない():
    mon_a = Pokemon("ピカチュウ")
    mon_b = Pokemon("ピカチュウ")

    mon_a.set_evs({"hp": 32})

    assert mon_a.evs[0] == 32
    assert mon_b.evs[0] == 0
    assert mon_a.evs is not mon_b.evs


def test_努力値_ステータス再計算に反映される():
    mon = Pokemon("ピカチュウ", nature="いじっぱり")
    hp_before = mon.stats["hp"]
    atk_before = mon.stats["atk"]
    mon.set_evs_at(0, 32)
    mon.set_evs_at(1, 32)
    assert mon.stats["hp"] > hp_before
    assert mon.stats["atk"] > atk_before


def test_努力値_ダメージ中にset_evsすると被ダメージ絶対量が維持される():
    mon = Pokemon("ピカチュウ")
    max_hp_before = mon.max_hp
    mon.hp = max_hp_before - 10  # このテストに限り直接代入で被ダメージ状態を作る
    mon.set_evs([32, 0, 0, 0, 0, 0])  # HP実数値が変わるように調整

    assert mon.max_hp != max_hp_before
    assert mon.max_hp - mon.hp == 10


def test_努力値_未ダメージ状態でset_evsしてもhpは満タンのまま():
    """hp_policy既定のkeep_absoluteは被ダメージ0を保持するため、未使用ポケモンは常に満タンで再構築される。"""
    mon = Pokemon("ピカチュウ")
    mon.set_evs([32, 0, 0, 0, 0, 0])  # HP実数値が変わるように調整
    assert mon.hp == mon.max_hp


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
