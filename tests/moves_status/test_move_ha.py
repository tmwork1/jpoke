"""変化技ハンドラの単体テスト（は行・ビ行）。"""

import pytest
from jpoke import Pokemon
from jpoke.data.move import MOVES
from jpoke.enums import Event, Interrupt
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


def test_はいすいのじん_マジックコートで跳ね返されない():
    """はいすいのじん: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["はいすいのじん"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    mon = battle.actives[0]
    foe = battle.actives[1]

    t.run_move(battle, 0)

    # 跳ね返されず自分の能力が上昇し、にげられない状態も自分に付与される
    assert mon.rank["atk"] == 1
    assert mon.has_volatile("にげられない")
    assert foe.rank["atk"] == 0
    assert not foe.has_volatile("にげられない")


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
    # 失敗のためにげられない状態も付与されない
    assert not mon.has_volatile("にげられない")


def test_ハッピータイム_マジックコートで跳ね返されない():
    """ハッピータイム: 味方の場を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハッピータイム"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    t.run_move(battle, 0)

    assert battle.move_executor.move_applied


def test_ハッピータイム_まもるで防がれない():
    """ハッピータイム: 味方の場を対象とする技のため、相手のまもるに関係なく成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハッピータイム"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    t.run_move(battle, 0)

    assert battle.move_executor.move_applied


def test_ハッピータイム_使用してもHPやランクなど戦闘状態が変化しない():
    """ハッピータイム: 効果のないわざのため、使用してもHP・ランクに一切変化がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハッピータイム"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    attacker_hp = attacker.hp
    defender_hp = defender.hp

    t.run_move(battle, 0)

    assert battle.move_executor.move_applied
    assert attacker.hp == attacker_hp
    assert defender.hp == defender_hp
    assert all(v == 0 for v in attacker.rank.values())
    assert all(v == 0 for v in defender.rank.values())
    assert not attacker.ailment.is_active
    assert not defender.ailment.is_active


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


def test_はねやすめ_マジックコートで跳ね返されない():
    """はねやすめ: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ムクホーク", move_names=["はねやすめ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    hp_before = mon.hp
    foe_hp_before = foe.hp

    t.run_move(battle, 0)

    assert mon.hp > hp_before
    assert foe.hp == foe_hp_before


def test_はねやすめ_まもるで防がれない():
    """はねやすめ: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ムクホーク", move_names=["はねやすめ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    hp_before = mon.hp

    t.run_move(battle, 0)

    assert mon.hp > hp_before
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


def test_はねる_じゅうりょく状態では失敗する():
    """はねる: gravity_restrictedフラグにより、じゅうりょく状態では失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はねる"])],
        team1=[Pokemon("カビゴン")],
        field={"じゅうりょく": 5},
    )

    t.run_move(battle, 0)

    assert not battle.move_executor.move_success


def test_はねる_マジックコートで跳ね返されない():
    """はねる: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はねる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    attacker_hp = attacker.hp
    defender_hp = defender.hp

    t.run_move(battle, 0)

    assert battle.move_executor.move_applied
    assert attacker.hp == attacker_hp
    assert defender.hp == defender_hp


def test_はねる_まもるで防がれない():
    """はねる: 自分を対象とする技のため、相手のまもるに関係なく成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はねる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )

    t.run_move(battle, 0)

    assert battle.move_executor.move_applied


def test_はねる_使用してもHPやランクなど戦闘状態が変化しない():
    """はねる: 効果のないわざのため、使用してもHP・ランクに一切変化がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はねる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    attacker_hp = attacker.hp
    defender_hp = defender.hp

    t.run_move(battle, 0)

    assert battle.move_executor.move_applied
    assert attacker.hp == attacker_hp
    assert defender.hp == defender_hp
    assert all(v == 0 for v in attacker.rank.values())
    assert all(v == 0 for v in defender.rank.values())
    assert not attacker.ailment.is_active
    assert not defender.ailment.is_active


def test_ハバネロエキス_PPは16():
    """ハバネロエキス: チャンピオンズでのPPは16（docs/champions/move_list.txt準拠）。"""
    assert MOVES["ハバネロエキス"].pp == 16


def test_ハバネロエキス_こうげき最大かつぼうぎょ最小なら失敗():
    """ハバネロエキス: こうげきが+6かつぼうぎょが-6の場合、技全体が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハバネロエキス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["atk"] = 6
    defender.rank["def"] = -6
    t.run_move(battle, 0)

    assert defender.rank["atk"] == 6
    assert defender.rank["def"] == -6
    assert battle.move_executor.move_success is False


def test_ハバネロエキス_必中で命中率に依存せず当たる():
    """ハバネロエキス: 必中技のため、命中率0%環境でも必ず命中する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハバネロエキス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["atk"] == 2
    assert defender.rank["def"] == -2


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


def test_はらだいこ_HPが最大HPの半分以下なら失敗():
    """はらだいこ: 現在HPが最大HPの半分以下の場合は失敗し、HPもランクも変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はらだいこ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp // 2  # ちょうど半分でも失敗する
    hp_before = attacker.hp
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 0
    assert attacker.hp == hp_before


def test_はらだいこ_あまのじゃくならこうげきランクが最低まで下がる():
    """はらだいこ: 特性あまのじゃくの場合はランク変化が反転し、こうげきランクが最低(-6)まで下がる。
    このとき失敗せずHPは通常通り消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あまのじゃく", move_names=["はらだいこ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == -6
    assert attacker.hp == max_hp - (max_hp // 2)


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


def test_はらだいこ_まもるで防がれない():
    """はらだいこ: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はらだいこ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 6
    assert attacker.hp == max_hp - (max_hp // 2)


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


def test_バトンタッチ_ちょうはつは引き継がれない():
    """バトンタッチ: ちょうはつ状態は交代先に引き継がれない（原作Wikiの記載通り）。

    通常はちょうはつ状態の効果でバトンタッチ自体（変化技）を使用できないため、
    ON_STATUS_HIT ハンドラを直接発火してバトンタッチ成立後の引き継ぎスナップショットのみを検証する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "ちょうはつ", count=3)

    ctx = t.build_context(battle, atk_idx=0)
    ctx.move.register_handlers(battle.events, attacker)
    battle.events.emit(Event.ON_STATUS_HIT, ctx, True)
    ctx.move.unregister_handlers(battle.events, attacker)

    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)
    new_mon = battle.actives[0]
    assert not new_mon.has_volatile("ちょうはつ")


def test_バトンタッチ_とくせいなしは特性がprotectedのポケモンには引き継がれない():
    """バトンタッチ: とくせいなし状態は、バトン先の特性がARシステム等protectedの場合は消える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"]),
               Pokemon("ネクロズマ", ability_name="ARシステム")],
        team1=[Pokemon("カビゴン")],
        volatile0={"とくせいなし": 3},
        accuracy=100,
    )
    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    new_mon = battle.actives[0]
    assert not new_mon.has_volatile("とくせいなし")
    assert new_mon.ability.enabled


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


def test_バトンタッチ_ほろびのうたの残カウントが交代先に引き継がれる():
    """バトンタッチ: ほろびのうたの残カウントが交代先ポケモンに引き継がれる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile0={"ほろびのうた": 3},
        accuracy=100,
    )
    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    new_mon = battle.actives[0]
    assert new_mon.volatiles["ほろびのうた"].count == 3


def test_バトンタッチ_ほろびのうたを引き継いでも交代退場処理中はひんしにならない():
    """バトンタッチ: ほろびのうた状態を交代先に引き継ぐ際、交代元がひんしにならない

    ON_VOLATILE_END はカウント0による自然解除と交代退場処理の両方で発火するため、
    ガードがないと交代元ポケモンが誤ってひんしになる（handlers/volatile.py の
    ほろびのうた_faint 参照）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile0={"ほろびのうた": 3},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    assert not attacker.fainted
    assert attacker.hp > 0


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
    "かいふくふうじ",
    "きゅうしょアップ",
    "こんらん",
    "でんじふゆう",
    "とくせいなし",
    "ねをはる",
    "のろい",
    "ほろびのうた",
    "やどりぎのタネ",
])
def test_バトンタッチ_引き継ぎ対象volatileが交代先に引き継がれる(volatile_name):
    """バトンタッチ: 引き継ぎ対象の揮発性状態が交代先ポケモンに引き継がれる

    docs/wiki/moves/バトンタッチ.html「状態変化の引き継ぎ」表の第9世代列が○のもの。
    """
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
    "あめまみれ",
    "いちゃもん",
    "おんねん",
    "しおづけ",
    "じゅうでん",
    "たくわえる",
    "タールショット",
    "ちいさくなる",
    "にげられない",
    "ねむけ",
    "バインド",
    "ふういん",
    "まるくなる",
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
    expected_a = (attacker._stats[1] + defender._stats[1]) // 2
    expected_c = (attacker._stats[3] + defender._stats[3]) // 2
    t.run_move(battle, 0)

    assert attacker._stats[1] == expected_a
    assert defender._stats[1] == expected_a
    assert attacker._stats[3] == expected_c
    assert defender._stats[3] == expected_c


def test_パワーシェア_ぼうぎょとくぼうは変化しない():
    """パワーシェア: ぼうぎょ・とくぼうの実数値は変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワーシェア"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    atk_b_before = attacker._stats[2]
    atk_d_before = attacker._stats[4]
    def_b_before = defender._stats[2]
    def_d_before = defender._stats[4]
    t.run_move(battle, 0)

    assert attacker._stats[2] == atk_b_before
    assert attacker._stats[4] == atk_d_before
    assert defender._stats[2] == def_b_before
    assert defender._stats[4] == def_d_before


def test_パワーシェア_マジックコートで跳ね返されない():
    """パワーシェア: unreflectableフラグを持つため、マジックコート状態の相手に使っても跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワーシェア"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    expected_a = (attacker._stats[1] + defender._stats[1]) // 2
    t.run_move(battle, 0)

    # 跳ね返されず、使用者側にも効果が発動する（平均化される）
    assert attacker._stats[1] == expected_a
    assert defender._stats[1] == expected_a


def test_パワーシェア_まもるで防がれる():
    """パワーシェア: まもる状態の相手に使うと防がれ、実数値が変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワーシェア"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    atk_a_before = attacker._stats[1]
    def_a_before = defender._stats[1]
    t.run_move(battle, 0)

    assert attacker._stats[1] == atk_a_before
    assert defender._stats[1] == def_a_before


def test_パワーシェア_みがわり状態の相手には効果が発動しない():
    """パワーシェア: bypass_substituteフラグを持たないため、みがわり状態の相手には防がれる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワーシェア"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"みがわり": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    atk_a_before = attacker._stats[1]
    def_a_before = defender._stats[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("みがわり")
    assert attacker._stats[1] == atk_a_before
    assert defender._stats[1] == def_a_before


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


def test_パワーシェア_交代すると実数値がリセットされる():
    """パワーシェア: 実数値の変更は交代でリセットされ、種族値ベースの値に戻ること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワーシェア"]), Pokemon("コラッタ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    a_before = attacker._stats[1]
    c_before = attacker._stats[3]
    t.run_move(battle, 0)

    # パワーシェアの効果で実数値が変化していることを確認
    assert attacker._stats[1] != a_before
    assert attacker._stats[3] != c_before

    # 交代すると種族値ベースの実数値に戻る
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)

    assert attacker._stats[1] == a_before
    assert attacker._stats[3] == c_before


def test_パワーシェア_相手の回避ランクが高くても必ず命中する():
    """パワーシェア: 必中技のため、相手の回避ランクが高くても必ず命中する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワーシェア"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.modify_stats(defender, {"evasion": 6}, source=defender)
    expected_a = (attacker._stats[1] + defender._stats[1]) // 2
    t.run_move(battle, 0)

    assert attacker._stats[1] == expected_a
    assert defender._stats[1] == expected_a


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


def test_パワースワップ_PPと必中フラグが正しい():
    """パワースワップ: PP=12（Championsの正）、accuracy=None（必中）、
    unreflectable・bypass_substituteフラグを持つこと"""
    move_data = MOVES["パワースワップ"]
    assert move_data.pp == 12
    assert move_data.accuracy is None
    assert "unreflectable" in move_data.flags
    assert "bypass_substitute" in move_data.flags


def test_パワースワップ_マジックコートで跳ね返されない():
    """パワースワップ: unreflectableフラグを持つため、マジックコート状態の相手に使っても跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワースワップ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.rank["atk"] = 2
    defender.rank["atk"] = -1
    t.run_move(battle, 0)

    # 跳ね返されず、使用者側のランクが相手の値に変わる
    assert attacker.rank["atk"] == -1
    assert defender.rank["atk"] == 2


def test_パワースワップ_まもるで防がれる():
    """パワースワップ: まもる状態の相手には防がれ、ランクは入れ替わらないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワースワップ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.rank["atk"] = 2
    defender.rank["atk"] = -1
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 2
    assert defender.rank["atk"] == -1


def test_パワースワップ_みがわり状態の相手にも効果が発動する():
    """パワースワップ: bypass_substituteフラグを持つため、みがわり状態の相手にも効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワースワップ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"みがわり": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.rank["atk"] = 2
    defender.rank["atk"] = -1
    t.run_move(battle, 0)

    assert defender.has_volatile("みがわり")
    assert attacker.rank["atk"] == -1
    assert defender.rank["atk"] == 2


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
    atk_a_before = attacker._stats[1]
    atk_c_before = attacker._stats[3]
    def_a_before = defender._stats[1]
    def_c_before = defender._stats[3]
    t.run_move(battle, 0)

    assert attacker._stats[1] == atk_a_before
    assert attacker._stats[3] == atk_c_before
    assert defender._stats[1] == def_a_before
    assert defender._stats[3] == def_c_before


def test_パワースワップ_相手の回避率が高くても必ず命中する():
    """パワースワップ: 必中技のため、相手の回避率ランクが高くても必ず命中する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワースワップ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.modify_stats(defender, {"evasion": 6}, source=defender)
    attacker.rank["atk"] = 2
    defender.rank["atk"] = -1
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == -1
    assert defender.rank["atk"] == 2


def test_パワートリック_2回使用で元の値に戻る():
    """パワートリック: 2回使用するとこうげきとぼうぎょの実数値が元に戻ること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワートリック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    atk_original = mon._stats[1]
    def_original = mon._stats[2]

    t.run_move(battle, 0)
    t.run_move(battle, 0)

    assert mon._stats[1] == atk_original
    assert mon._stats[2] == def_original


def test_パワートリック_PPは12():
    """パワートリック: チャンピオンズでのPPは12（docs/champions/move_list.txt準拠）。"""
    assert MOVES["パワートリック"].pp == 12


def test_パワートリック_こうげきとぼうぎょが入れ替わる():
    """パワートリック: 使用後にこうげきとぼうぎょの実数値が入れ替わること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワートリック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    atk_before = mon._stats[1]
    def_before = mon._stats[2]

    t.run_move(battle, 0)

    assert mon._stats[1] == def_before
    assert mon._stats[2] == atk_before


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


def test_パワートリック_対象はself():
    """パワートリック: 対象は自分（target="self"）。foeのままだとまもる・マジックコートに誤って阻害される"""
    move_data = MOVES["パワートリック"]
    assert move_data.target == "self"


def test_パワートリック_相手の実数値は変化しない():
    """パワートリック: 使用者の入れ替えのみで、相手のこうげき・ぼうぎょ実数値は変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワートリック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    def_atk_before = defender._stats[1]
    def_def_before = defender._stats[2]

    t.run_move(battle, 0)

    assert defender._stats[1] == def_atk_before
    assert defender._stats[2] == def_def_before


def test_ひかりのかべ_PPは20():
    """ひかりのかべ: チャンピオンズでのPPは20（docs/champions/move_list.txt準拠）。"""
    assert MOVES["ひかりのかべ"].pp == 20


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


def test_ひっくりかえす_あまのじゃくの影響を受けない():
    """ひっくりかえす: あまのじゃく特性の相手に使ってもランク変動の符号は反転処理されないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン", ability_name="あまのじゃく")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -2


def test_ひっくりかえす_クリアチャームでも防げない():
    """ひっくりかえす: 持ち物クリアチャームでもランク反転は防げないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン", item_name="クリアチャーム")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -2


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


def test_ひっくりかえす_しろいきりでも防げない():
    """ひっくりかえす: 相手側のしろいきり状態でもランク反転は防げないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン")],
        side1={"しろいきり": 5},
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -2


def test_ひっくりかえす_たんじゅんの影響を受けない():
    """ひっくりかえす: たんじゅん特性の相手に使ってもランク変動が2倍にならないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン", ability_name="たんじゅん")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -2


def test_ひっくりかえす_だっしゅつパックが発動しない():
    """ひっくりかえす: ランクが下がっても、だっしゅつパックによる交代は発動しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン", item_name="だっしゅつパック"), Pokemon("ゲンガー")],
        accuracy=100,
    )
    state1 = battle._player_states[1]
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -2
    assert state1.active_index == 0
    assert defender.has_item("だっしゅつパック")


def test_ひっくりかえす_びんじょうが発動しない():
    """ひっくりかえす: 相手のランクが上がっても、使用者のびんじょうは発動しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="びんじょう", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender.rank["atk"] = -2
    t.run_move(battle, 0)

    assert defender.rank["atk"] == 2
    assert attacker.rank["atk"] == 0


def test_ひっくりかえす_まけんきが発動しない():
    """ひっくりかえす: ランクが下がっても、まけんきによるこうげき上昇は発動しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン", ability_name="まけんき")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -2


def test_ひっくりかえす_マジックコートで反射される():
    """ひっくりかえす: マジックコート状態の相手に使うと反射され、使用者のランクが反転すること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker, defender = battle.actives
    attacker.rank["atk"] = 2
    t.run_move(battle, 0)

    # 反射され、使用者自身のランクが反転する。相手のランクは変化しない
    assert attacker.rank["atk"] == -2
    assert defender.rank["atk"] == 0


def test_ひっくりかえす_まもるで防がれる():
    """ひっくりかえす: まもる状態の相手には防がれ、ランクは変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    t.run_move(battle, 0)

    assert defender.rank["atk"] == 2


def test_ひっくりかえす_みがわり状態の相手には防がれる():
    """ひっくりかえす: みがわり状態の相手には防がれ、ランクは変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    defender.rank["atk"] = 2
    t.run_move(battle, 0)

    assert defender.rank["atk"] == 2


def test_ひっくりかえす_ものまねハーブが発動しない():
    """ひっくりかえす: 相手のランクが上がっても、使用者のものまねハーブは発動しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ものまねハーブ", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender.rank["def"] = -1
    t.run_move(battle, 0)

    assert defender.rank["def"] == 1
    assert attacker.rank["def"] == 0
    assert attacker.has_item("ものまねハーブ")


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


@pytest.mark.parametrize("d_ability", ["クリアボディ", "ミラーアーマー"])
def test_ひっくりかえす_能力低下防止特性でも防げない(d_ability: str):
    """ひっくりかえす: クリアボディ/ミラーアーマーなどのランク低下防止特性でも防げないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひっくりかえす"])],
        team1=[Pokemon("カビゴン", ability_name=d_ability)],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -2


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


def test_ビルドアップ_マジックコートで跳ね返されない():
    """ビルドアップ: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ビルドアップ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["def"] == 1
    assert defender.rank["atk"] == 0
    assert defender.rank["def"] == 0


def test_ビルドアップ_まもるで防がれない():
    """ビルドアップ: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ビルドアップ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["def"] == 1


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


def test_ふういん_すでにふういん状態なら失敗する():
    """ふういん: すでにふういん状態の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふういん"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"ふういん": 1},
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False


def test_ふういん_マジックコートで跳ね返されない():
    """ふういん: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふういん"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert mon.has_volatile("ふういん")
    assert not foe.has_volatile("ふういん")


def test_ふういん_まもるで防がれない():
    """ふういん: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふういん"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.has_volatile("ふういん")


def test_ふういん_使用者がふういん状態になる():
    """ふういん: 使用すると自分がふういん状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふういん"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.has_volatile("ふういん")


def test_フェアリーロック_ゴーストタイプも交代できない():
    """フェアリーロック: 通常の交代禁止と異なりゴーストタイプも例外なく交代できなくなる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"])],
        team1=[Pokemon("ゲンガー"), Pokemon("ヤドン")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert not t.can_switch(battle, 1)


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


def test_フェアリーロック_マジックコートで跳ね返されない():
    """フェアリーロック: 全体の場を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert battle.global_manager.fields["フェアリーロック"].is_active


def test_フェアリーロック_まもるで防がれない():
    """フェアリーロック: 全体の場を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert battle.global_manager.fields["フェアリーロック"].is_active


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


def test_フェアリーロック_相手側も交代できない():
    """フェアリーロック: 両陣営のポケモンが交代できなくなる（相手側も対象）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert not t.can_switch(battle, 1)


def test_フェザーダンス_PPは16():
    """フェザーダンス: チャンピオンズでのPPは16（docs/champions/move_list.txt準拠）。"""
    assert MOVES["フェザーダンス"].pp == 16


def test_フェザーダンス_defenderのこうげきが2段階下がる():
    """フェザーダンス: 相手（defender）のこうげきが2段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェザーダンス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.rank["atk"] == -2


def test_フェザーダンス_マジックコートで跳ね返される():
    """フェザーダンス: マジックコートで跳ね返され、使用者のこうげきが2段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェザーダンス"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.rank["atk"] == -2
    assert defender.rank["atk"] == 0


def test_フェザーダンス_まもるで防がれる():
    """フェザーダンス: まもるで防がれ、ランクが変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェザーダンス"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.rank["atk"] == 0


def test_ふきとばし_かぜのりで無効化される():
    """ふきとばし: 相手が特性かぜのりの場合、無効化されてこうげきが1段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふきとばし"])],
        team1=[Pokemon("ピカチュウ", ability_name="かぜのり"), Pokemon("カビゴン")],
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)

    assert battle.actives[1] is defender_before
    assert defender_before.rank["atk"] == 1


def test_ふきとばし_きゅうばんで無効化される():
    """ふきとばし: 相手が特性きゅうばんの場合、強制交代が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふきとばし"])],
        team1=[Pokemon("ピカチュウ", ability_name="きゅうばん"), Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert battle.actives[1] is defender


def test_ふきとばし_ねをはる状態の相手には失敗する():
    """ふきとばし: 相手がねをはる状態の場合、強制交代が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふきとばし"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        volatile1={"ねをはる": 1},
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)

    assert battle.actives[1] is defender_before


def test_ふきとばし_マジックコートで跳ね返り使用者が交代する():
    """ふきとばし: マジックコートで跳ね返されると、使用者側が強制的に交代させられる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふきとばし"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker_before = battle.actives[0]
    t.run_move(battle, 0)

    assert battle.actives[0] is not attacker_before


def test_ふきとばし_まもるを貫通する():
    """ふきとばし: まもる状態の相手にも強制交代が発生する（まもるを貫通する）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふきとばし"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        volatile1={"まもる": 1},
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)

    assert battle.actives[1] is not defender_before


def test_ふきとばし_みがわりを貫通する():
    """ふきとばし: みがわり状態の相手にも強制交代が発生する（みがわりを貫通する）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふきとばし"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        volatile1={"みがわり": 1},
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)

    assert battle.actives[1] is not defender_before


def test_ふきとばし_控えポケモンがいない場合は失敗する():
    """ふきとばし: 相手に控えポケモンがいない場合は技が失敗し、交代は発生しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふきとばし"])],
        team1=[Pokemon("カビゴン")],
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)

    assert battle.actives[1] is defender_before


def test_ふきとばし_相手が強制交代する():
    """ふきとばし: 相手に控えポケモンがいる場合、相手ポケモンがランダムに交代する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ふきとばし"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)

    assert battle.actives[1] is not defender_before


def test_ふしょくガス_かたやぶりならねんちゃく持ちからも消失させられる():
    """ふしょくガス: 使用者がかたやぶりの場合、ねんちゃく持ちの相手からも持ち物を消失させられる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ふしょくガス"])],
        team1=[Pokemon("マタドガス", ability_name="ねんちゃく", item_name="たべのこし")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_item()


def test_ふしょくガス_すりぬけならみがわり状態の相手にも効果を発揮する():
    """ふしょくガス: 使用者がすりぬけの場合、みがわり状態の相手にも技が命中し
    持ち物を消失させられる。"""
    battle = t.start_battle(
        team0=[Pokemon("ドククラゲ", ability_name="すりぬけ", move_names=["ふしょくガス"])],
        team1=[Pokemon("カビゴン", item_name="たべのこし")],
        volatile1={"みがわり": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_item()


def test_ふしょくガス_ねんちゃく持ちの相手からは持ち物を消失させられない():
    """ふしょくガス: 特性ねんちゃくの相手からは持ち物を消失させられない。"""
    battle = t.start_battle(
        team0=[Pokemon("ドククラゲ", move_names=["ふしょくガス"])],
        team1=[Pokemon("マタドガス", ability_name="ねんちゃく", item_name="たべのこし")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_item("たべのこし")


def test_ふしょくガス_まもるで防がれる():
    """ふしょくガス: まもる状態の相手には効果が発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ドククラゲ", move_names=["ふしょくガス"])],
        team1=[Pokemon("カビゴン", item_name="たべのこし")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_item("たべのこし")


def test_ふしょくガス_みがわり状態の相手には無効():
    """ふしょくガス: みがわり状態の相手には技自体が無効化され、持ち物は消失しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ドククラゲ", move_names=["ふしょくガス"])],
        team1=[Pokemon("カビゴン", item_name="たべのこし")],
        volatile1={"みがわり": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_item("たべのこし")


def test_ふしょくガス_専用道具は消失させられない():
    """ふしょくガス: ザシアンとくちたけんの組み合わせ等、種族+持ち物ロックされた
    専用道具は消失させられない。"""
    battle = t.start_battle(
        team0=[Pokemon("ドククラゲ", move_names=["ふしょくガス"])],
        team1=[Pokemon("ザシアン(けんのおう)", item_name="くちたけん")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_item("くちたけん")


def test_ふしょくガス_相手が持ち物を持たない場合も技は成功扱いになる():
    """ふしょくガス: 相手が持ち物を持たない場合でも、技自体は失敗にならない
    （溶かせる持ち物がないだけで、技のPP消費・成否には影響しない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ドククラゲ", move_names=["ふしょくガス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert not battle.actives[1].has_item()


def test_ふしょくガス_相手の持ち物を消失させる():
    """ふしょくガス: 命中すると相手の持ち物を消失させる。ダメージは発生しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ドククラゲ", move_names=["ふしょくガス"])],
        team1=[Pokemon("カビゴン", item_name="たべのこし")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)

    assert not defender.has_item()
    assert defender.hp == hp_before


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


def test_フラフラダンス_マジックコートで跳ね返されない():
    """フラフラダンス: unreflectableフラグを持つため、マジックコート状態の相手に使っても跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フラフラダンス"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 跳ね返されず、相手にこんらんが付与される
    assert defender.has_volatile("こんらん")
    assert not attacker.has_volatile("こんらん")


def test_へびにらみ_PPは20():
    """へびにらみ: チャンピオンズでのPPは20（docs/champions/move_list.txt準拠）。"""
    assert MOVES["へびにらみ"].pp == 20


def test_へびにらみ_でんきタイプには無効():
    """へびにらみ: 対象がでんきタイプの場合は無効になる（まひ無効）"""
    battle = t.start_battle(
        team0=[Pokemon("アーボック", move_names=["へびにらみ"])],
        team1=[Pokemon("ライチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert not battle.actives[1].ailment.is_active


def test_へびにらみ_まひ付与():
    """へびにらみ: 相手をまひ状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("アーボック", move_names=["へびにらみ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert battle.actives[1].ailment.name == "まひ"


def test_ほえる_きゅうばんで無効化される():
    """ほえる: 相手が特性きゅうばんの場合、強制交代が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほえる"])],
        team1=[Pokemon("ピカチュウ", ability_name="きゅうばん"), Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert battle.actives[1] is defender


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


def test_ほえる_マジックコートで跳ね返り使用者が交代する():
    """ほえる: マジックコートで跳ね返されると、使用者側が強制的に交代させられる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほえる"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker_before = battle.actives[0]
    t.run_move(battle, 0)

    assert battle.actives[0] is not attacker_before


def test_ほえる_まもるを貫通する():
    """ほえる: まもる状態の相手にも強制交代が発生する（まもるを貫通する）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほえる"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        volatile1={"まもる": 1},
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)

    assert battle.actives[1] is not defender_before


def test_ほえる_みがわりを貫通する():
    """ほえる: みがわり状態の相手にも強制交代が発生する（音技のためみがわりを貫通する）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほえる"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        volatile1={"みがわり": 1},
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)

    assert battle.actives[1] is not defender_before


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


def test_ほおばる_あまのじゃくでぼうぎょ最大でも成功する():
    """ほおばる + あまのじゃく: ぼうぎょランクがすでに+6でも、
    あまのじゃくの効果で上昇が下降に反転するため成功してきのみを消費しぼうぎょが下がる
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あまのじゃく",
                       move_names=["ほおばる"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.rank["def"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 4
    assert not attacker.item.is_berry()


def test_ほおばる_あまのじゃくでぼうぎょ最小なら失敗する():
    """ほおばる + あまのじゃく: ぼうぎょランクがすでに-6の場合、
    あまのじゃくの反転効果で下降方向に上限があるため失敗しきのみも消費されない
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あまのじゃく",
                       move_names=["ほおばる"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.rank["def"] = -6
    t.run_move(battle, 0)

    # 失敗のためランクは変化せず、きのみも消費されない
    assert attacker.rank["def"] == -6
    assert attacker.item.is_berry()


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


def test_ほたるび_とくこうが3段階上がる():
    """ほたるび: 自分の『とくこう』ランクが3段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほたるび"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["spa"] == 3


def test_ほたるび_とくこうが最大の場合は失敗する():
    """ほたるび: とくこうランクがすでに+6の場合は変化せず失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほたるび"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["spa"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["spa"] == 6


def test_ほたるび_自分対象のためまもるで防がれない():
    """ほたるび: 自分を対象とする技のため、相手のまもるがあっても効果は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほたるび"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["spa"] == 3


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


def test_ほろびのうた_PPは8():
    """ほろびのうた: チャンピオンズでのPPは8（docs/champions/move_list.txt準拠）。"""
    assert MOVES["ほろびのうた"].pp == 8


def test_ほろびのうた_まもる状態の相手にも効果が発動する():
    """ほろびのうた: unprotectableフラグを持つため、まもる状態の相手にも効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほろびのうた"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert attacker.has_volatile("ほろびのうた")
    assert defender.has_volatile("ほろびのうた")


def test_ほろびのうた_みがわりを貫通して付与される():
    """ほろびのうた: soundフラグを持つため、みがわり状態の相手にも効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほろびのうた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)

    assert defender.has_volatile("ほろびのうた")
    assert defender.volatiles["みがわり"].hp == 999


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


@pytest.mark.parametrize(
    "def_init,spd_init,def_exp,spd_exp",
    [
        # 通常: 防御+1、特防+1
        (0, 0, 1, 1),
        # 防御上限: 防御はキャップ、特防は+1
        (6, 0, 6, 1),
        # 特防上限: 特防はキャップ、防御は+1
        (0, 6, 1, 6),
        # 両方上限: どちらも変化できないので失敗（変化なし）
        (6, 6, 6, 6),
        # 両方上限まで1段階: どちらも上限ぴったりになる
        (5, 5, 6, 6),
        # 最低ランクから上昇
        (-6, -6, -5, -5),
    ],
)
def test_ぼうぎょしれい_発動前後のランク変化(def_init, spd_init, def_exp, spd_exp):
    """ぼうぎょしれい: 発動前後のぼうぎょ・とくぼうランクの変化を網羅的に確認する"""
    battle = t.start_battle(
        team0=[Pokemon("ビークイン", move_names=["ぼうぎょしれい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["def"] = def_init
    attacker.rank["spd"] = spd_init
    t.run_move(battle, 0)

    assert attacker.rank["def"] == def_exp
    assert attacker.rank["spd"] == spd_exp


def test_ぼうぎょしれい_自分対象のためまもるで防がれない():
    """ぼうぎょしれい: 自分を対象とする技のため、相手のまもるがあっても効果は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ビークイン", move_names=["ぼうぎょしれい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 1
    assert attacker.rank["spd"] == 1
