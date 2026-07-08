"""変化技ハンドラの単体テスト（は行・ビ行）。"""

import pytest
from jpoke import Pokemon
from jpoke.enums import Interrupt
from .. import test_utils as t


def test_はいすいのじん_2回目の使用で失敗する():
    """はいすいのじん: はいすいのじん起因でにげられない状態の場合、2回目は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["はいすいのじん"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    # 1回目は成功
    t.run_move(battle, 0)
    assert mon.rank["atk"] == 1

    # 2回目はにげられない（はいすいのじん起因）でガード → 失敗
    t.run_move(battle, 0)
    assert mon.rank["atk"] == 1  # ランクは変化しない


def test_はいすいのじん_すでにとらわれている場合はにげられないを再付与しない():
    """はいすいのじん: すでにとらわれている場合はにげられないvolatileを重ねて付与しない"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["はいすいのじん"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"にげられない": 3},  # 他起因のにげられない（move_name=""）
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)

    # にげられないはそのまま（move_nameは上書きされない）
    assert mon.has_volatile("にげられない")
    assert mon.volatiles["にげられない"].move_name == ""  # はいすいのじんで上書きされない


def test_はいすいのじん_にげられない状態が付与される():
    """はいすいのじん: 使用後に自分がにげられない状態（はいすいのじん起因）になる"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["はいすいのじん"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)

    assert mon.has_volatile("にげられない")
    assert mon.volatiles["にげられない"].move_name == "はいすいのじん"


def test_はいすいのじん_他起因のにげられない状態では失敗しない():
    """はいすいのじん: 他の要因によるにげられない状態では失敗せず、ランクが上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["はいすいのじん"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"にげられない": 3},  # move_name="" の他起因にげられない
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)

    # 失敗しないのでランクが上がる
    assert mon.rank["atk"] == 1
    assert mon.rank["def"] == 1
    assert mon.rank["spa"] == 1
    assert mon.rank["spd"] == 1
    assert mon.rank["spe"] == 1


def test_はいすいのじん_全5能力が1段階ずつ上がる():
    """はいすいのじん: 使用後にこうげき・ぼうぎょ・とくこう・とくぼう・すばやさが+1ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["はいすいのじん"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)

    assert mon.rank["atk"] == 1
    assert mon.rank["def"] == 1
    assert mon.rank["spa"] == 1
    assert mon.rank["spd"] == 1
    assert mon.rank["spe"] == 1


def test_はいすいのじん_全5能力が最大のとき失敗する():
    """はいすいのじん: すべての能力ランクが+6のとき失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["はいすいのじん"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    for stat in ("atk", "def", "spa", "spd", "spe"):
        mon.rank[stat] = 6
    t.run_move(battle, 0)

    # 失敗のためランクは変化しない
    for stat in ("atk", "def", "spa", "spd", "spe"):
        assert mon.rank[stat] == 6


def test_はねやすめ_HPが半分回復する():
    """はねやすめ: 使用後に最大HPの1/2が回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ムクホーク", move_names=["はねやすめ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    # HPを削る
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    hp_before = mon.hp
    expected_heal = mon.max_hp // 2

    t.run_move(battle, 0)

    assert mon.hp == hp_before + expected_heal


def test_はねやすめ_HP満タン時は失敗する():
    """はねやすめ: HPが満タンのときは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ムクホーク", move_names=["はねやすめ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    assert mon.hp == mon.max_hp

    t.run_move(battle, 0)

    # 失敗のため volatile が付与されない
    assert not mon.has_volatile("はねやすめ")
    assert mon.hp == mon.max_hp


def test_はねやすめ_volatile中はひこうタイプが除外される():
    """はねやすめ: volatile 付与中はひこうタイプが types から除外される"""
    battle = t.start_battle(
        team0=[Pokemon("ムクホーク", move_names=["はねやすめ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    assert mon.has_type("ひこう")  # 通常時はひこうタイプを持つ

    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    t.run_move(battle, 0)

    assert mon.has_volatile("はねやすめ")
    assert not mon.has_type("ひこう")  # volatile 中はひこうタイプが除外される


def test_はねやすめ_ターン終了でvolatileが解除される():
    """はねやすめ: ターン終了時に volatile が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ムクホーク", move_names=["はねやすめ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    t.run_move(battle, 0)

    assert mon.has_volatile("はねやすめ")

    t.end_turn(battle)

    assert not mon.has_volatile("はねやすめ")


def test_はねやすめ_ターン終了でひこうタイプが復帰する():
    """はねやすめ: ターン終了時にひこうタイプが復帰する"""
    battle = t.start_battle(
        team0=[Pokemon("ムクホーク", move_names=["はねやすめ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    t.run_move(battle, 0)

    assert not mon.has_type("ひこう")  # volatile 中はひこうタイプが除外される

    # ターン終了でひこうタイプが復帰する
    t.end_turn(battle)

    assert mon.has_type("ひこう")


def test_はねやすめ_テラスタル中はひこうタイプが除外されない():
    """はねやすめ: テラスタル中はひこうタイプを除去しない"""
    battle = t.start_battle(
        team0=[Pokemon("ムクホーク", move_names=["はねやすめ"], tera_type="ひこう")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    # テラスタル状態にする
    mon.terastallized = True
    assert mon.has_type("ひこう")

    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    t.run_move(battle, 0)

    # テラスタル中は volatile が付与されない（タイプ除去なし）
    assert not mon.has_volatile("はねやすめ")
    # ひこうタイプが除外されていない
    assert mon.has_type("ひこう")


def test_はねやすめ_ひこうタイプを持たないポケモンはvolatile付与されない():
    """はねやすめ: ひこうタイプを持たないポケモンが使用しても volatile は付与されない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["はねやすめ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))

    t.run_move(battle, 0)

    # ひこうタイプを持たないのでvolatileは付与されない
    assert not mon.has_volatile("はねやすめ")


def test_はねやすめ_ひこうタイプ持ちにvoltatile付与される():
    """はねやすめ: ひこうタイプ持ちが使用するとはねやすめ volatile が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ムクホーク", move_names=["はねやすめ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))

    t.run_move(battle, 0)

    assert mon.has_volatile("はねやすめ")


def test_はねやすめ_交代後にremoved_typesがリセットされる():
    """はねやすめ: 交代後に removed_types がリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ムクホーク", move_names=["はねやすめ"]), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    t.run_move(battle, 0)

    assert not mon.has_type("ひこう")  # volatile 中はひこうタイプ除外

    # 交代するとリセットされる
    t.run_switch(battle, 0, 1)

    assert mon.has_type("ひこう")  # 交代後はひこうタイプが復帰
    assert not mon.has_volatile("はねやすめ")


@pytest.mark.parametrize(
    "atk_init,def_init,atk_exp,def_exp",
    [
        # 通常: A+2、B-2
        (0, 0, 2, -2),
        # こうげき上限: Aはキャップ、Bは-2
        (6, 0, 6, -2),
        # ぼうぎょ下限: Bはフロア、Aは+2
        (0, -6, 2, -6),
        # 両方限界: どちらも変化できないので失敗（変化なし）
        (6, -6, 6, -6),
        # こうげき上限まで1段階: Aはキャップぴったり、Bは-2
        (5, 0, 6, -2),
        # ぼうぎょ下限まで1段階: Bは下限ぴったり、Aは+2
        (0, -5, 2, -6),
        # 逆側の極端: どちらも変化する
        (-6, 6, -4, 4),
    ],
)
def test_ハバネロエキス_発動前後のランク変化(atk_init, def_init, atk_exp, def_exp):
    """ハバネロエキス: 発動前後のこうげき・ぼうぎょランクの変化を網羅的に確認する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハバネロエキス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["atk"] = atk_init
    defender.rank["def"] = def_init
    t.run_move(battle, 0)

    assert defender.rank["atk"] == atk_exp
    assert defender.rank["def"] == def_exp


def test_はらだいこ_こうげきすでに最大なら失敗():
    """はらだいこ: こうげきランクがすでに+6なら失敗し、HPは消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はらだいこ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["atk"] = 6
    hp_before = attacker.hp
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 6
    assert attacker.hp == hp_before


def test_はらだいこ_こうげき最大化しHP半分消費():
    """はらだいこ: こうげきランクが+6になり最大HPの半分が消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はらだいこ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 6
    assert attacker.hp == max_hp - (max_hp // 2)


def test_ハートスタンプ_ひるみが発動する():
    """ハートスタンプ: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピクシー", move_names=["ハートスタンプ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ハートスワップ_すべての能力ランクが入れ替わる():
    """ハートスワップ: 攻撃者と防御者のすべての能力ランクが互いに入れ替わること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハートスワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 攻撃者のこうげき+2、防御者のぼうぎょ-1 を設定
    attacker.rank["atk"] = 2
    defender.rank["def"] = -1
    t.run_move(battle, 0)

    # スワップ後: 攻撃者は防御者のランクを受け取る
    assert attacker.rank["atk"] == 0
    assert attacker.rank["def"] == -1
    # スワップ後: 防御者は攻撃者のランクを受け取る
    assert defender.rank["atk"] == 2
    assert defender.rank["def"] == 0


def test_ハートスワップ_全ランクゼロのとき変化なし():
    """ハートスワップ: 両者のランクがすべて0のとき入れ替えても変化なし"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハートスワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    for stat in ("atk", "def", "spa", "spd", "spe", "accuracy", "evasion"):
        assert attacker.rank[stat] == 0
        assert defender.rank[stat] == 0


def test_バトンタッチ_とらわれ状態でも使用できる():
    """バトンタッチ: にげられない状態でも技が失敗せず PIVOT が設定される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile0={"にげられない": 3},
        accuracy=100,
    )
    player = battle.players[0]
    t.run_move(battle, 0)

    # とらわれ状態でもバトンタッチは失敗しない
    assert battle.player_states[player].interrupt == Interrupt.PIVOT


def test_バトンタッチ_みがわりとそのHPが交代先に引き継がれる():
    """バトンタッチ: みがわり状態とそのHPが交代先ポケモンに引き継がれる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # みがわりを手動で付与してHPを設定
    battle.volatile_manager.apply(attacker, "みがわり", hp=50)

    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    new_mon = battle.actives[0]
    assert new_mon.has_volatile("みがわり")
    assert new_mon.volatiles["みがわり"].hp == 50


def test_バトンタッチ_ランクが交代先に引き継がれる():
    """バトンタッチ: 能力ランク変化が交代先ポケモンに引き継がれる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.rank["atk"] = 3
    attacker.rank["spe"] = 2

    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    new_mon = battle.actives[0]
    assert new_mon.rank["atk"] == 3
    assert new_mon.rank["spe"] == 2


@pytest.mark.parametrize("volatile_name", [
    "アクアリング",
    "きゅうしょアップ",
    "こんらん",
    "しおづけ",
    "じゅうでん",
    "ちいさくなる",
    "ちょうはつ",
    "たくわえる",
    "でんじふゆう",
    "ねをはる",
    "まるくなる",
    "やどりぎのタネ",
])
def test_バトンタッチ_引き継ぎ対象volatileが交代先に引き継がれる(volatile_name):
    """バトンタッチ: 引き継ぎ対象の揮発性状態が交代先ポケモンに引き継がれる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile0={volatile_name: 3},
        accuracy=100,
    )
    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    new_mon = battle.actives[0]
    assert new_mon.has_volatile(volatile_name)


@pytest.mark.parametrize("volatile_name", [
    "にげられない",
    "バインド",
    "ねむけ",
    "のろい",
    "おんねん",
    "いちゃもん",
    "ふういん",
    "あめまみれ",
    "タールショット",
    "みちづれ",
])
def test_バトンタッチ_引き継ぎ対象外volatileは交代先に引き継がれない(volatile_name):
    """バトンタッチ: 引き継ぎ対象外の揮発性状態は交代先ポケモンに引き継がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile0={volatile_name: 3},
        accuracy=100,
    )
    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    new_mon = battle.actives[0]
    assert not new_mon.has_volatile(volatile_name)


def test_バトンタッチ_控えがいない場合は失敗する():
    """バトンタッチ: 控えにポケモンがいない場合は技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    t.run_move(battle, 0)

    # 控えがいないので失敗し、PIVOT は設定されない
    assert battle.player_states[player].interrupt == Interrupt.NONE


@pytest.mark.parametrize("attacker_name, defender_name", [
    # A合計奇数（切り捨てあり）、C合計奇数（切り捨てあり）
    ("ピカチュウ", "カビゴン"),
    # A合計偶数（切り捨てなし）、C合計偶数（切り捨てなし）
    ("イーブイ", "ラプラス"),
    # A合計偶数（切り捨てなし）、C合計奇数（切り捨てあり）: フシギダネA=69 vs ピカチュウA=75→sum=144, C=85 vs C=70→sum=155
    ("フシギダネ", "ピカチュウ"),
    # A合計奇数（切り捨てあり）、C合計偶数（切り捨てなし）: コイルA=55 vs カビゴンA=130→sum=185, C=115 vs C=85→sum=200
    ("コイル", "カビゴン"),
])
def test_パワーシェア_こうげきとくこうが平均化される(attacker_name: str, defender_name: str):
    """パワーシェア: 使用者と相手のこうげき・とくこう実数値が平均値（切り捨て）になること"""
    battle = t.start_battle(
        team0=[Pokemon(attacker_name, move_names=["パワーシェア"])],
        team1=[Pokemon(defender_name)],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 使用前の平均値を計算（A=インデックス1、C=インデックス3）
    expected_a = (attacker._stats_manager.stats[1] + defender._stats_manager.stats[1]) // 2
    expected_c = (attacker._stats_manager.stats[3] + defender._stats_manager.stats[3]) // 2
    t.run_move(battle, 0)

    assert attacker._stats_manager.stats[1] == expected_a
    assert defender._stats_manager.stats[1] == expected_a
    assert attacker._stats_manager.stats[3] == expected_c
    assert defender._stats_manager.stats[3] == expected_c


def test_パワーシェア_ぼうぎょとくぼうは変化しない():
    """パワーシェア: ぼうぎょ・とくぼうの実数値は変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワーシェア"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    atk_b_before = attacker._stats_manager.stats[2]
    atk_d_before = attacker._stats_manager.stats[4]
    def_b_before = defender._stats_manager.stats[2]
    def_d_before = defender._stats_manager.stats[4]
    t.run_move(battle, 0)

    assert attacker._stats_manager.stats[2] == atk_b_before
    assert attacker._stats_manager.stats[4] == atk_d_before
    assert defender._stats_manager.stats[2] == def_b_before
    assert defender._stats_manager.stats[4] == def_d_before


def test_パワーシェア_ランク変化は変更されない():
    """パワーシェア: 実数値のみを平均化し、能力ランクは変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワーシェア"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 0
    assert attacker.rank["spa"] == 0
    assert defender.rank["atk"] == 0
    assert defender.rank["spa"] == 0


def test_パワースワップ_ACランクが双方で入れ替わる():
    """パワースワップ: 使用者と相手のこうげき・とくこうランクが互いに入れ替わること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワースワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 事前にランクを変更しておく
    attacker.rank["atk"] = 2
    attacker.rank["spa"] = -1
    defender.rank["atk"] = -3
    defender.rank["spa"] = 1
    t.run_move(battle, 0)

    # 入れ替わった後のランクを確認
    assert attacker.rank["atk"] == -3
    assert attacker.rank["spa"] == 1
    assert defender.rank["atk"] == 2
    assert defender.rank["spa"] == -1


def test_パワースワップ_BDランクは変化しない():
    """パワースワップ: ぼうぎょ・とくぼうのランクは変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワースワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.rank["def"] = 3
    attacker.rank["spd"] = 2
    defender.rank["def"] = -1
    defender.rank["spd"] = -2
    t.run_move(battle, 0)

    # ぼうぎょ・とくぼうは変化しない
    assert attacker.rank["def"] == 3
    assert attacker.rank["spd"] == 2
    assert defender.rank["def"] == -1
    assert defender.rank["spd"] == -2


def test_パワースワップ_双方ともランク0のとき変化なし():
    """パワースワップ: 双方のこうげき・とくこうランクがともに0の場合は入れ替え後も0のまま"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワースワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 0
    assert attacker.rank["spa"] == 0
    assert defender.rank["atk"] == 0
    assert defender.rank["spa"] == 0


def test_パワースワップ_実数値は変化しない():
    """パワースワップ: ランク変化のみを入れ替え、こうげき・とくこうの実数値は変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワースワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    atk_a_before = attacker._stats_manager.stats[1]
    atk_c_before = attacker._stats_manager.stats[3]
    def_a_before = defender._stats_manager.stats[1]
    def_c_before = defender._stats_manager.stats[3]
    t.run_move(battle, 0)

    assert attacker._stats_manager.stats[1] == atk_a_before
    assert attacker._stats_manager.stats[3] == atk_c_before
    assert defender._stats_manager.stats[1] == def_a_before
    assert defender._stats_manager.stats[3] == def_c_before


def test_パワートリック_2回使用で元の値に戻る():
    """パワートリック: 2回使用するとこうげきとぼうぎょの実数値が元に戻ること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワートリック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    atk_original = mon._stats_manager.stats[1]
    def_original = mon._stats_manager.stats[2]

    t.run_move(battle, 0)
    t.run_move(battle, 0)

    assert mon._stats_manager.stats[1] == atk_original
    assert mon._stats_manager.stats[2] == def_original


def test_パワートリック_こうげきとぼうぎょが入れ替わる():
    """パワートリック: 使用後にこうげきとぼうぎょの実数値が入れ替わること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワートリック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    atk_before = mon._stats_manager.stats[1]
    def_before = mon._stats_manager.stats[2]

    t.run_move(battle, 0)

    assert mon._stats_manager.stats[1] == def_before
    assert mon._stats_manager.stats[2] == atk_before


def test_パワートリック_ランクは変化しない():
    """パワートリック: 実数値のみを入れ替え、こうげき・ぼうぎょのランクは変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワートリック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.rank["atk"] = 2
    mon.rank["def"] = -1

    t.run_move(battle, 0)

    assert mon.rank["atk"] == 2
    assert mon.rank["def"] == -1


def test_パワートリック_相手の実数値は変化しない():
    """パワートリック: 使用者の入れ替えのみで、相手のこうげき・ぼうぎょ実数値は変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワートリック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    def_atk_before = defender._stats_manager.stats[1]
    def_def_before = defender._stats_manager.stats[2]

    t.run_move(battle, 0)

    assert defender._stats_manager.stats[1] == def_atk_before
    assert defender._stats_manager.stats[2] == def_def_before


def test_ひかりのかべ_すでにアクティブなら失敗():
    """ひかりのかべ: すでにひかりのかべが有効なら失敗（再設置されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひかりのかべ"])],
        team1=[Pokemon("カビゴン")],
        side0={"ひかりのかべ": 4},
    )
    side = battle.get_side(battle.actives[0])
    t.run_move(battle, 0)

    # カウントは変わらない
    assert side.fields["ひかりのかべ"].is_active
    assert side.fields["ひかりのかべ"].count == 4


def test_ひかりのかべ_自陣営に5ターン設置される():
    """ひかりのかべ: 使用すると自陣営に5ターンのひかりのかべが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひかりのかべ"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[0])
    assert side.fields["ひかりのかべ"].is_active
    assert side.fields["ひかりのかべ"].count == 5


def test_ひっくりかえす_こうげきプラスが反転する():
    """ひっくりかえす: こうげき+2の相手に使用するとこうげきが-2になること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -2


def test_ひっくりかえす_全ランク0なら失敗する():
    """ひっくりかえす: 全ランクが0の場合は技が失敗してランクが変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # ランクはすべてデフォルト0
    t.run_move(battle, 0)

    for v in defender.rank.values():
        assert v == 0


def test_ひっくりかえす_複数ランクが全て反転する():
    """ひっくりかえす: 複数のランク変化がある場合にすべて反転すること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["atk"] = 3
    defender.rank["def"] = -2
    defender.rank["spe"] = 1
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -3
    assert defender.rank["def"] == 2
    assert defender.rank["spe"] == -1


def test_びりびりちくちく_ひるみが発動する():
    """びりびりちくちく: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ライチュウ", move_names=["びりびりちくちく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


@pytest.mark.parametrize(
    "atk_init,def_init,atk_exp,def_exp",
    [
        # 通常: A+1、B+1
        (0, 0, 1, 1),
        # こうげき上限: Aはキャップ、Bは+1
        (6, 0, 6, 1),
        # ぼうぎょ上限: Bはキャップ、Aは+1
        (0, 6, 1, 6),
        # 両方上限: どちらも変化できないので失敗（変化なし）
        (6, 6, 6, 6),
        # 両方上限まで1段階: どちらも上限ぴったりになる
        (5, 5, 6, 6),
        # 最低ランクから上昇
        (-6, -6, -5, -5),
    ],
)
def test_ビルドアップ_発動前後のランク変化(atk_init, def_init, atk_exp, def_exp):
    """ビルドアップ: 発動前後のこうげき・ぼうぎょランクの変化を網羅的に確認する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ビルドアップ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["atk"] = atk_init
    attacker.rank["def"] = def_init
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == atk_exp
    assert attacker.rank["def"] == def_exp


def test_フェアリーロック_すでに有効なら失敗する():
    """フェアリーロック: すでにフェアリーロック状態なら失敗し、カウントは変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"])],
        team1=[Pokemon("カビゴン")],
        field={"フェアリーロック": 1},
        accuracy=100,
    )
    count_before = battle.global_manager.fields["フェアリーロック"].count
    t.run_move(battle, 0)

    assert battle.global_manager.fields["フェアリーロック"].count == count_before


def test_フェアリーロック_使用後にグローバルフィールドが有効になる():
    """フェアリーロック: 使用するとグローバルフィールド「フェアリーロック」が有効になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert battle.global_manager.fields["フェアリーロック"].is_active


def test_フェアリーロック_使用者側が交代できない():
    """フェアリーロック: フェアリーロック中は使用者側のポケモンが交代できない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert not t.can_switch(battle, 0)


def test_ふみつけ_ひるみが発動する():
    """ふみつけ: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ふみつけ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_フラフラダンス_こんらん状態を付与する():
    """フラフラダンス: 相手をこんらん状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フラフラダンス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("こんらん")


def test_フラフラダンス_すでにこんらん状態なら失敗():
    """フラフラダンス: 相手がすでにこんらん状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フラフラダンス"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"こんらん": 3},
        accuracy=100,
    )
    defender = battle.actives[1]
    old_count = defender.volatiles["こんらん"].count
    t.run_move(battle, 0)

    assert defender.has_volatile("こんらん")
    assert defender.volatiles["こんらん"].count == old_count


def test_ほえる_ねをはる状態の相手には失敗する():
    """ほえる: 相手がねをはる状態の場合、強制交代が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほえる"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        volatile1={"ねをはる": 1},
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)

    # ねをはる状態なので交代が発生しない
    assert battle.actives[1] is defender_before


def test_ほえる_控えポケモンがいない場合は失敗する():
    """ほえる: 相手に控えポケモンがいない場合は技が失敗し、交代は発生しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほえる"])],
        team1=[Pokemon("カビゴン")],
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)

    assert battle.actives[1] is defender_before


def test_ほえる_控えポケモンがいる場合に交代が発生する():
    """ほえる: 相手に控えポケモンがいる場合、相手ポケモンがランダムに交代する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほえる"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)

    assert battle.actives[1] is not defender_before


def test_ほおばる_きのみが消費される():
    """ほおばる: 使用後にきのみが消費されアイテムがなくなる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほおばる"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert attacker.item.is_berry()
    t.run_move(battle, 0)

    assert not attacker.item.is_berry()


def test_ほおばる_きのみを持っていない場合は失敗する():
    """ほおばる: きのみを持っていない場合はぼうぎょランクが変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほおばる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert not attacker.item.is_berry()
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 0


def test_ほおばる_きのみを持っている場合はぼうぎょが2段階上がる():
    """ほおばる: きのみを持っている場合はぼうぎょランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほおばる"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 2


def test_ほおばる_ぼうぎょが最大の場合は失敗する():
    """ほおばる: ぼうぎょランクがすでに+6の場合はきのみを消費せず失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほおばる"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.rank["def"] = 6
    t.run_move(battle, 0)

    # 失敗のためランクは変化せず、きのみも消費されない
    assert attacker.rank["def"] == 6
    assert attacker.item.is_berry()


def test_ほおばる_ラムのみでやけどが治る():
    """ほおばる + ラムのみ: やけど状態のポケモンがほおばるを使うとラムのみが発動してやけどが治る

    ラムのみは ON_FORCE_BERRY_TRIGGER で発動する。
    やけどはほおばる使用を妨げないため、技は正常に実行される。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほおばる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # ねむり以外の状態異常（やけど）を付与してからラムのみを持たせる
    # (ailment付与後にアイテムを持たせることで ON_APPLY_AILMENT による即時回復を防ぐ)
    battle.ailment_manager.apply(attacker, "やけど")
    t.change_item(battle, attacker, "ラムのみ")
    assert attacker.ailment.name == "やけど"
    assert attacker.item.is_berry()
    t.run_move(battle, 0)

    # ラムのみが発動してやけどが治る
    assert not attacker.ailment.is_active
    # ラムのみは消費される
    assert not attacker.item.is_berry()
    # ぼうぎょも上がる
    assert attacker.rank["def"] == 2


def test_ホネこんぼう_ひるみが発動する():
    """ホネこんぼう: 10%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カラカラ", move_names=["ホネこんぼう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ほろびのうた_3ターン後に瀕死になる():
    """ほろびのうた: count=3 から3ターン経過するとひんしになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほろびのうた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    t.end_turn(battle)
    assert attacker.alive

    t.end_turn(battle)
    assert attacker.alive

    t.end_turn(battle)
    assert attacker.fainted


def test_ほろびのうた_使用者と相手にvolatileが付与される():
    """ほろびのうた: 使用者・相手ともに count=3 の volatile が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほろびのうた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert attacker.has_volatile("ほろびのうた")
    assert attacker.volatiles["ほろびのうた"].count == 3
    assert defender.has_volatile("ほろびのうた")
    assert defender.volatiles["ほろびのうた"].count == 3


def test_ほろびのうた_全員すでに状態なら失敗():
    """ほろびのうた: 使用者も相手も全員すでにほろびのうた状態なら技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほろびのうた"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"ほろびのうた": 3},
        volatile1={"ほろびのうた": 3},
        accuracy=100,
    )
    attacker = battle.actives[0]
    # 付与済みのカウントを記録
    count_before = attacker.volatiles["ほろびのうた"].count
    t.run_move(battle, 0)

    # カウントが変化していない（技が失敗した）
    assert attacker.volatiles["ほろびのうた"].count == count_before


def test_ほろびのうた_自分だけ状態なら相手に付与できる():
    """ほろびのうた: 使用者がすでにほろびのうた状態でも相手に付与できる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほろびのうた"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"ほろびのうた": 3},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("ほろびのうた")


def test_ぼうぎょしれい_とくぼうが1段階上がる():
    """ぼうぎょしれい: 使用後に自分のとくぼうランクが1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("ビークイン", move_names=["ぼうぎょしれい"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.rank["spd"] == 1


def test_ぼうぎょしれい_ぼうぎょが1段階上がる():
    """ぼうぎょしれい: 使用後に自分のぼうぎょランクが1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("ビークイン", move_names=["ぼうぎょしれい"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.rank["def"] == 1
