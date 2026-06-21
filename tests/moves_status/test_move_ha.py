"""変化技ハンドラの単体テスト（は行・ビ行）。"""

from jpoke import Pokemon
from jpoke.enums import Interrupt
from .. import test_utils as t


def test_はきだす_カウント0で失敗する():
    """はきだす: たくわえていない（カウント0）なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はきだす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)

    assert defender.hp == hp_before


def test_はきだす_カウント1で威力100():
    # TODO : カウント1~3をパラメタライズですべてテストする
    """はきだす: たくわえカウント1のとき威力100でダメージを与える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はきだす"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 1},
        accuracy=100,
    )
    # 威力100相当で必ずダメージが入る
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)

    assert defender.hp < hp_before


def test_はきだす_カウント3で最大威力300():
    """はきだす: たくわえカウント3のとき威力300でダメージを与える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はきだす"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 3},
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)

    assert defender.hp < hp_before


def test_はきだす_命中後にたくわえる状態が消える():
    """はきだす: 命中後にたくわえる揮発状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はきだす"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 2},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert not attacker.has_volatile("たくわえる")


def test_はきだす_命中後にランクが元に戻る():
    # TODO : test_はきだす_命中後にたくわえる状態が消える、と統合
    """はきだす: 命中後にたくわえた回数分だけぼうぎょとくぼうが下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はきだす"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 2},
        accuracy=100,
    )
    attacker = battle.actives[0]
    # たくわえカウント2相当のランクを事前に設定
    attacker.rank["B"] = 2
    attacker.rank["D"] = 2
    t.run_move(battle, 0)

    assert attacker.rank["B"] == 0
    assert attacker.rank["D"] == 0


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
    # TODO : これは揮発状態の仕様なので技側でテストすべきではない
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
    # TODO : これは揮発状態の仕様なので技側でテストすべきではない
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
    # TODO : これは揮発状態の仕様なので技側でテストすべきではない
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
    # TODO : これは揮発状態の仕様なので技側でテストすべきではない
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


def test_ハバネロエキス_こうげき2段階上がる():
    # TODO : 発動前後の状態の組み合わせをパラメタライズで網羅的にテストする
    """ハバネロエキス: 相手のこうげきランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハバネロエキス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert defender.rank["A"] == 0
    t.run_move(battle, 0)

    assert defender.rank["A"] == 2


def test_ハバネロエキス_こうげき最大かつぼうぎょ最低なら失敗():
    """ハバネロエキス: こうげきが+6かつぼうぎょが-6なら技が失敗しランクは変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハバネロエキス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["A"] = 6
    defender.rank["B"] = -6
    t.run_move(battle, 0)

    assert defender.rank["A"] == 6
    assert defender.rank["B"] == -6


def test_ハバネロエキス_こうげき最大でもぼうぎょは下がる():
    """ハバネロエキス: こうげきがすでに+6でも、ぼうぎょは2段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハバネロエキス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["A"] = 6
    t.run_move(battle, 0)

    assert defender.rank["A"] == 6
    assert defender.rank["B"] == -2


def test_ハバネロエキス_ぼうぎょ2段階下がる():
    """ハバネロエキス: 相手のぼうぎょランクが2段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハバネロエキス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert defender.rank["B"] == 0
    t.run_move(battle, 0)

    assert defender.rank["B"] == -2


def test_ハバネロエキス_ぼうぎょ最低でもこうげきは上がる():
    """ハバネロエキス: ぼうぎょがすでに-6でも、こうげきは2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハバネロエキス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["B"] = -6
    t.run_move(battle, 0)

    assert defender.rank["A"] == 2
    assert defender.rank["B"] == -6


def test_はらだいこ_こうげきすでに最大なら失敗():
    """はらだいこ: こうげきランクがすでに+6なら失敗し、HPは消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はらだいこ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["A"] = 6
    hp_before = attacker.hp
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 6
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

    assert attacker.rank["A"] == 6
    assert attacker.hp == max_hp - (max_hp // 2)


def test_バトンタッチ_こんらんが交代先に引き継がれる():
    # TODO : 揮発状態の引き継ぎ可否をパラメタライズで網羅的にテストする
    """バトンタッチ: こんらん状態が交代先ポケモンに引き継がれる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile0={"こんらん": 3},
        accuracy=100,
    )
    t.run_move(battle, 0)
    battle.run_interrupt_switch(Interrupt.PIVOT)

    new_mon = battle.actives[0]
    assert new_mon.has_volatile("こんらん")


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
    battle.run_interrupt_switch(Interrupt.PIVOT)

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
    attacker.rank["A"] = 3
    attacker.rank["S"] = 2

    t.run_move(battle, 0)
    battle.run_interrupt_switch(Interrupt.PIVOT)

    new_mon = battle.actives[0]
    assert new_mon.rank["A"] == 3
    assert new_mon.rank["S"] == 2


def test_バトンタッチ_交代が実行される():
    # TODO : 他のテストですでに検証されているので不要
    """バトンタッチ: PIVOT 後に交代コマンドを処理すると控えが場に出る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    raichu = battle.player_states[battle.players[0]].team[1]
    t.run_move(battle, 0)
    battle.run_interrupt_switch(Interrupt.PIVOT)

    assert battle.actives[0] is raichu


def test_バトンタッチ_引き継ぎ対象外のvolatileは引き継がれない():
    """バトンタッチ: にげられないなど引き継ぎ対象外の volatile は交代先に引き継がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["バトンタッチ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile0={"にげられない": 3},
        accuracy=100,
    )
    t.run_move(battle, 0)
    battle.run_interrupt_switch(Interrupt.PIVOT)

    new_mon = battle.actives[0]
    assert not new_mon.has_volatile("にげられない")


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

    assert attacker.rank["A"] == 0
    assert attacker.rank["C"] == 0
    assert defender.rank["A"] == 0
    assert defender.rank["C"] == 0


def test_パワーシェア_使用者と相手のこうげきが平均化される():
    # TODO : こうげき・とくこうの平均化をパラメタライズで網羅的にテストする。ガードシェアも同様。
    """パワーシェア: 使用者と相手のこうげき実数値が平均値（切り捨て）になること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワーシェア"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 使用前の平均値を計算
    expected_a = (attacker._stats_manager.stats[1] + defender._stats_manager.stats[1]) // 2
    t.run_move(battle, 0)

    assert attacker._stats_manager.stats[1] == expected_a
    assert defender._stats_manager.stats[1] == expected_a


def test_パワーシェア_使用者と相手のとくこうが平均化される():
    """パワーシェア: 使用者と相手のとくこう実数値が平均値（切り捨て）になること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワーシェア"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 使用前の平均値を計算
    expected_c = (attacker._stats_manager.stats[3] + defender._stats_manager.stats[3]) // 2
    t.run_move(battle, 0)

    assert attacker._stats_manager.stats[3] == expected_c
    assert defender._stats_manager.stats[3] == expected_c


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
    attacker.rank["A"] = 2
    attacker.rank["C"] = -1
    defender.rank["A"] = -3
    defender.rank["C"] = 1
    t.run_move(battle, 0)

    # 入れ替わった後のランクを確認
    assert attacker.rank["A"] == -3
    assert attacker.rank["C"] == 1
    assert defender.rank["A"] == 2
    assert defender.rank["C"] == -1


def test_パワースワップ_BDランクは変化しない():
    """パワースワップ: ぼうぎょ・とくぼうのランクは変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["パワースワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.rank["B"] = 3
    attacker.rank["D"] = 2
    defender.rank["B"] = -1
    defender.rank["D"] = -2
    t.run_move(battle, 0)

    # ぼうぎょ・とくぼうは変化しない
    assert attacker.rank["B"] == 3
    assert attacker.rank["D"] == 2
    assert defender.rank["B"] == -1
    assert defender.rank["D"] == -2


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

    assert attacker.rank["A"] == 0
    assert attacker.rank["C"] == 0
    assert defender.rank["A"] == 0
    assert defender.rank["C"] == 0


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
    mon.rank["A"] = 2
    mon.rank["B"] = -1

    t.run_move(battle, 0)

    assert mon.rank["A"] == 2
    assert mon.rank["B"] == -1


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


def test_ビルドアップ_こうげきとぼうぎょ1段階ずつ上がる():
    # TODO : 発動前後の状態の組み合わせをパラメタライズで網羅的にテストする
    """ビルドアップ: 使用すると自分のこうげきとぼうぎょランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ビルドアップ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["A"] == 0
    assert attacker.rank["B"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 1
    assert attacker.rank["B"] == 1


def test_ビルドアップ_こうげき最大でもぼうぎょは上昇する():
    """ビルドアップ: こうげきがすでに+6でも、ぼうぎょは上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ビルドアップ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["A"] = 6
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 6
    assert attacker.rank["B"] == 1


def test_フェアリーロック_ゴーストタイプも交代できない():
    # TODO : これはフィールドの責務なので技側でテストすべきではない
    """フェアリーロック: ゴーストタイプのポケモンも交代できない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert not t.can_switch(battle, 0)


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


def test_フェアリーロック_ターン終了でフィールドが解除される():
    # TODO : これはフィールドの責務なので技側でテストすべきではない
    """フェアリーロック: ターン終了後にグローバルフィールドが解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.global_manager.fields["フェアリーロック"].is_active

    t.end_turn(battle)
    assert not battle.global_manager.fields["フェアリーロック"].is_active


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
    # TODO : これはフィールドの責務なので技側でテストすべきではない
    """フェアリーロック: フェアリーロック中は相手側のポケモンも交代できない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    assert not t.can_switch(battle, 1)


def test_フェアリーロック_解除後は交代できる():
    # TODO : これはフィールドの責務なので技側でテストすべきではない
    """フェアリーロック: フィールド解除後は双方が交代できるようになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["フェアリーロック"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    t.end_turn(battle)

    assert t.can_switch(battle, 0)
    assert t.can_switch(battle, 1)


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


def test_ほえる_きゅうばん特性で無効化される():
    # TODO : これは特性きゅうばんの責務なので技側でテストすべきではない
    """ほえる: 相手がきゅうばん特性を持つ場合、強制交代が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほえる"])],
        team1=[Pokemon("カビゴン", ability_name="きゅうばん"), Pokemon("ヤドン")],
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)

    assert battle.actives[1] is defender_before


def test_ほえる_ねをはる状態の相手には失敗する():
    # TODO : これは揮発状態の仕様なので技側でテストすべきではない
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


def test_ほおばる_HP閾値より上ではオボンのみの回復が発動しない():
    # TODO : ほおばるの仕様として、きのみ本来の発動条件を無視して効果を得るため、オボンのみの回復効果を得られる。仕様書から見直す。
    """ほおばる: HPが閾値（50%）より上の場合はオボンのみの回復効果は発動しない（きのみ消費のみ）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほおばる"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # HPを満タンのままにする（閾値より上）
    assert attacker.hp == attacker.max_hp
    hp_before = attacker.hp
    t.run_move(battle, 0)

    # HPは変化しないがきのみは消費され、ぼうぎょは上がる
    assert attacker.hp == hp_before
    assert not attacker.item.is_berry()
    assert attacker.rank["B"] == 2


def test_ほおばる_HP閾値以下でオボンのみの回復が発動する():
    """ほおばる: HPが閾値（50%）以下のときオボンのみの回復効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほおばる"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # HPを50%以下に直接設定（modify_hpを使うとオボンのみが先に発動してしまうため）
    attacker.hp = attacker.max_hp // 4
    hp_before = attacker.hp
    t.run_move(battle, 0)

    # オボンのみの回復（最大HPの1/4）が発動し、HPが増加している
    assert attacker.hp > hp_before


def test_ほおばる_オボンのみでHP半分以下なら回復する():
    """ほおばる + オボンのみ: HP1/2以下ならオボンのみが通常通り発動してHPが回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほおばる"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # HPを50%以下に直接設定
    attacker.hp = attacker.max_hp // 4
    hp_before = attacker.hp
    t.run_move(battle, 0)

    # オボンのみの回復効果が発動する（HP閾値以下のため）
    assert attacker.hp > hp_before
    # オボンのみは消費される
    assert not attacker.item.is_berry()
    # ぼうぎょも上がる
    assert attacker.rank["B"] == 2


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

    assert attacker.rank["B"] == 0


def test_ほおばる_きのみを持っている場合はぼうぎょが2段階上がる():
    """ほおばる: きのみを持っている場合はぼうぎょランクが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほおばる"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["B"] == 2


def test_ほおばる_キーのみでこんらんが治る():
    # TODO : 通常ほおばるを使う前にきのみが発動してしまうため、このようなテストは不要。同種のテストも削除する。
    """ほおばる + キーのみ: こんらん状態のポケモンがほおばるを使うとキーのみが発動してこんらんが治る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほおばる"], item_name="キーのみ")],
        team1=[Pokemon("カビゴン")],
        volatile0={"こんらん": 3},
        accuracy=100,
    )
    # こんらんによる行動失敗を防ぐ（確率的に行動失敗しないよう固定）
    battle.test_option.trigger_volatile = False
    attacker = battle.actives[0]
    assert attacker.has_volatile("こんらん")
    t.run_move(battle, 0)

    # キーのみが発動してこんらんが治る
    assert not attacker.has_volatile("こんらん")
    # キーのみは消費される
    assert not attacker.item.is_berry()
    # ぼうぎょも上がる
    assert attacker.rank["B"] == 2


def test_ほおばる_ぼうぎょが最大の場合は失敗する():
    """ほおばる: ぼうぎょランクがすでに+6の場合はきのみを消費せず失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほおばる"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.rank["B"] = 6
    t.run_move(battle, 0)

    # 失敗のためランクは変化せず、きのみも消費されない
    assert attacker.rank["B"] == 6
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
    assert attacker.rank["B"] == 2


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


def test_ほろびのうた_ターン終了でカウントが減少する():
    # TODO : これは揮発状態の責務なので技側でテストすべきではない
    """ほろびのうた: ターン終了ごとに count が1ずつ減少する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほろびのうた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.volatiles["ほろびのうた"].count == 3

    t.end_turn(battle)
    assert attacker.volatiles["ほろびのうた"].count == 2

    t.end_turn(battle)
    assert attacker.volatiles["ほろびのうた"].count == 1


def test_ほろびのうた_使用者にもvolatileが付与される():
    """ほろびのうた: 使用者自身にも count=3 の volatile が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほろびのうた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("ほろびのうた")
    assert attacker.volatiles["ほろびのうた"].count == 3


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


def test_ほろびのうた_相手にもvolatileが付与される():
    # TODO : 使用者の付与テストと統合
    """ほろびのうた: 相手にも count=3 の volatile が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほろびのうた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("ほろびのうた")
    assert defender.volatiles["ほろびのうた"].count == 3


def test_ほろびのうた_相手も3ターン後に瀕死になる():
    # TODO : これは揮発状態の責務なので技側でテストすべきではない
    """ほろびのうた: 相手も count=3 から3ターン経過するとひんしになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほろびのうた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    t.end_turn(battle)
    assert defender.alive

    t.end_turn(battle)
    assert defender.alive

    t.end_turn(battle)
    assert defender.fainted


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
