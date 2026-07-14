"""揮発性状態ハンドラの単体テスト（ハ〜ワ行）"""
import pytest
from jpoke import Pokemon
from jpoke.enums import Command, LogCode
from .. import test_utils as t


def test_バインド_ゴーストタイプは交代可能():
    """バインド: ゴーストタイプは第六世代以降バインド状態でも交代できる"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"バインド": 99},
    )
    assert battle.query.can_switch(battle.players[0])


def test_バインド_ターン経過でダメージ():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"バインド": 2},
    )
    mon = battle.actives[0]
    expected_damage = mon.max_hp // 8

    # 1ターン目の終了時にダメージ
    t.end_turn(battle)
    assert mon.has_volatile("バインド")
    assert mon.hp == mon.max_hp - expected_damage

    # 解除されるターンにはダメージを受けない
    t.end_turn(battle)
    assert not mon.has_volatile("バインド")
    assert mon.hp == mon.max_hp - expected_damage


def test_バインド_マジックガードでダメージ無効():
    """バインド: マジックガード特性を持つポケモンはターン終了ダメージを受けない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        volatile0={"バインド": 2},
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


def test_バインド_交代不可():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"バインド": 99},
    )
    assert not battle.query.can_switch(battle.players[0])


def test_バインド_発生源が交代すると解除():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"バインド": 99},
    )
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 1)
    assert not battle.actives[1].has_volatile("バインド")


def test_ひるみ_ターン終了で解除():
    """ひるみ: ターン終了後にひるみ状態が解除される（1ターン限り）"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ひるみ": 1}
    )
    mon = battle.actives[0]
    assert mon.has_volatile("ひるみ")
    t.end_turn(battle)
    assert not mon.has_volatile("ひるみ")


def test_ひるみ_行動不能():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"ひるみ": 1}
    )
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is False


def test_ふういん_交代で解除される():
    """ふういん状態のポケモンが交代すると封印が解除され、相手は共通技を使える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"]), Pokemon("カビゴン")],
        volatile1={"ふういん": 1},
    )
    # 交代前: 共通技は使えない
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is False
    # ふういん状態のポケモン（team1）を交代する
    t.run_switch(battle, 1, 1)
    # 交代後: ふういん状態は解除されているので共通技を使える
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is True


def test_ふういん_共通技は使えない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile1={"ふういん": 1},
    )
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is False


def test_ふういん_非共通技は使える():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile1={"ふういん": 1},
    )
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is True


def test_ほろびのうた_count3から3ターンで減少し瀕死():
    """ほろびのうた: count=3 から3ターン経過するとカウントが減少し瀕死になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ほろびのうた": 3},
    )
    mon = battle.actives[0]

    t.end_turn(battle)
    assert mon.volatiles["ほろびのうた"].count == 2
    assert mon.alive

    t.end_turn(battle)
    assert mon.volatiles["ほろびのうた"].count == 1
    assert mon.alive

    t.end_turn(battle)
    assert not mon.has_volatile("ほろびのうた")
    assert mon.fainted


def test_ほろびのうた_ターン経過で瀕死():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ほろびのうた": 2}
    )
    mon = battle.actives[0]

    t.end_turn(battle)
    assert mon.volatiles["ほろびのうた"].count == 1
    assert mon.alive

    t.end_turn(battle)
    assert not mon.has_volatile("ほろびのうた")
    assert mon.fainted


def test_ほろびのうた_マジックガードでも瀕死():
    """ほろびのうた: マジックガード特性を持つポケモンも瀕死になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ほろびのうた": 1}
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.fainted


def test_ほろびのうた_交代で解除():
    """ほろびのうた: 交代するとほろびのうた状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ほろびのうた": 3}
    )
    mon = battle.actives[0]
    assert mon.has_volatile("ほろびのうた")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("ほろびのうた")


def test_ほろびのうた_別の揮発性状態の解除では瀕死にならない():
    """ほろびのうた: ちょうはつなど別の揮発性状態が自然解除されても、
    ほろびのうたのカウントが0になるまでは瀕死にならない（回帰テスト）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ほろびのうた": 3, "ちょうはつ": 1},
    )
    mon = battle.actives[0]

    t.end_turn(battle)
    # ちょうはつは1ターンで自然解除されるが、ほろびのうたのカウントは2で瀕死にならない
    assert not mon.has_volatile("ちょうはつ")
    assert mon.volatiles["ほろびのうた"].count == 2
    assert mon.alive


def test_マジックコート_unreflectableフラグを持つじこあんじは跳ね返さない():
    """マジックコート: unreflectableフラグを持つじこあんじは跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこあんじ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender.boosts["atk"] = 2
    t.run_move(battle, 0)
    # 跳ね返されず、通常通り自分のランクが相手のランクにコピーされる
    assert attacker.boosts["atk"] == 2


def test_マジックコート_unreflectableフラグを持つスキルスワップは跳ね返さない():
    """マジックコート: unreflectableフラグを持つスキルスワップは跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["スキルスワップ"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    # 跳ね返されず、通常通り特性が入れ替わる
    assert attacker.ability.name == "めんえき"
    assert defender.ability.name == "せいでんき"


def test_マジックコート_unreflectableフラグを持つなりきりは跳ね返さない():
    """マジックコート: unreflectableフラグを持つなりきりは跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["なりきり"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    # 跳ね返されず、通常通り相手の特性がコピーされる
    assert attacker.ability.name == "めんえき"


def test_マジックコート_unreflectableフラグを持つ技は跳ね返さない():
    """マジックコート: unreflectableフラグを持つうつしえは跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["うつしえ"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    # 跳ね返されず、通常通り相手の特性がコピーされる
    assert attacker.ability.name == "めんえき"


def test_マジックコート_ターン終了で解除():
    """マジックコート: ターン終了時に解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"マジックコート": 1},
    )
    mon = battle.actives[0]
    assert mon.has_volatile("マジックコート")
    t.end_turn(battle)
    assert not mon.has_volatile("マジックコート")


def test_マジックコート_交代で解除():
    """マジックコート: 交代時に解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"マジックコート": 1},
    )
    mon = battle.actives[0]
    assert mon.has_volatile("マジックコート")
    t.run_switch(battle, 0, 1)
    assert not mon.has_volatile("マジックコート")


def test_マジックコート_変化技を跳ね返す():
    """マジックコート: 相手に向けた変化技（にらみつける）を跳ね返す"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にらみつける"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 技使用前のランク確認
    assert attacker.boosts["def"] == 0
    assert defender.boosts["def"] == 0
    # 0番（ピカチュウ側）がにらみつけるを使う
    t.run_move(battle, 0)
    # マジックコートで跳ね返されるため、attacker（技使用者）の防御が下がる
    assert attacker.boosts["def"] == -1
    assert defender.boosts["def"] == 0


def test_マジックコート_攻撃技は跳ね返さない():
    """マジックコート: 攻撃技は跳ね返さない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    # 攻撃技なので跳ね返されず defender にダメージが入る
    assert defender.hp < hp_before


def test_まもる_みきりでもまもる状態になる():
    """みきり: 使用するとまもる揮発性状態が付与され、攻撃を防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["みきり"])],
    )
    _, defender = battle.actives
    # みきりでまもる volatileが付与されることを確認
    t.run_move(battle, 1)
    assert defender.has_volatile("まもる")
    # まもる状態なので攻撃技が通らない
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


def test_まもる_相手自身が対象の技は無効化しない():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["つるぎのまい"])],
    )
    battle.volatile_manager.apply(battle.actives[1], "まもる", count=1)
    t.run_move(battle, 0)
    assert battle.move_executor.move_success


@pytest.mark.parametrize("volatile_name", [
    "まもる", "トーチカ", "キングシールド", "スレッドトラップ", "かえんのまもり"
])
def test_まもる系_ターン終了で解除(volatile_name):
    battle = t.start_battle(team1=[Pokemon("ピカチュウ")], team0=[Pokemon("ピカチュウ")])
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, volatile_name, count=1)
    t.end_turn(battle)
    assert not mon.has_volatile(volatile_name)


@pytest.mark.parametrize("volatile_name", [
    "まもる", "トーチカ", "キングシールド", "スレッドトラップ", "かえんのまもり"
])
def test_まもる系_攻撃技を無効化(volatile_name):
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.volatile_manager.apply(battle.actives[1], volatile_name, count=1)
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


@pytest.mark.parametrize("volatile_name,blocks_status", [
    ("まもる", True),
    ("トーチカ", True),
    ("キングシールド", False),
    ("スレッドトラップ", False),
    ("かえんのまもり", False),
])
def test_まもる系_相手対象変化技への反応(volatile_name, blocks_status):
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["キノコのほうし"])],
    )
    battle.volatile_manager.apply(battle.actives[1], volatile_name, count=1)
    t.run_move(battle, 0)
    assert battle.move_executor.move_success == (not blocks_status)


def test_まるくなる():
    """まるくなる: ころがる・アイスボールの威力が2倍になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ころがる"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"まるくなる": 1},
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.power_modifier


def test_まるくなる_他技は倍にならない():
    """まるくなる: ころがる以外では威力変化なし"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile0={"まるくなる": 1}
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_みがわり_攻撃によりみがわりのHPが減る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=100)
    volatile = defender.volatiles["みがわり"]
    t.fix_damage(battle, 30)
    t.run_move(battle, 1)
    assert volatile.hp == 100 - 30
    assert defender.hp == defender.max_hp


def test_みがわり_無効化():
    """みがわり: 技を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["キノコのほうし"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"みがわり": 1},
    )
    t.run_move(battle, 0)
    assert not battle.move_executor.move_applied


def test_みがわり_破壊():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=1)
    t.run_move(battle, 1)
    assert not defender.has_volatile("みがわり")


def test_みがわり_音技は貫通する():
    """みがわり: 音技はみがわりを貫通して本体にダメージを与える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["エコーボイス"])],
        team1=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    # みがわりにHPを設定（貫通しなければこのHPが削られる）
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)
    # 音技はみがわりを無視して本体にダメージを与えるため、本体HPが減る
    assert defender.hp < hp_before
    # みがわりのHPは変化しない
    assert defender.volatiles["みがわり"].hp == 999


def test_みちづれ_倒しきれなければ不発():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile1={"みちづれ": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 1)
    assert attacker.alive
    assert defender.alive


def test_みちづれ_次ターン行動で解除():
    """みちづれ状態は自身が行動すると解除され、その後は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        volatile1={"みちづれ": 1},
    )
    attacker, defender = battle.actives
    # 1ターン目: みちづれ持ち（ピカチュウ）が技を使う → ON_TRY_ACTION で解除
    t.run_move(battle, 1)
    # みちづれ状態が解除されていることを確認
    assert not defender.has_volatile("みちづれ")
    # 2ターン目: カビゴンがたいあたりでピカチュウをひんしにしても、みちづれは発動しない
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.alive


def test_みちづれ_発動条件を満たせば両者ひんし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"みちづれ": 1},
    )
    attacker, defender = battle.actives
    defender.hp = 1  # 確実にひんしになるようにHPを1にする
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.fainted
    assert battle.judge_winner() is battle.players[0]


def test_めいちゅうアップ_命中率が1_2倍になり消費される():
    """めいちゅうアップ: 次の技の命中率が1.2倍になり、発動後は状態が解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ", move_names=["ハイドロポンプ"])],
        volatile1={"めいちゅうアップ": None},
    )
    mon = battle.actives[1]
    move = t.run_move(battle, 1)
    assert battle.move_executor.accuracy == move.accuracy * 4915 // 4096
    assert not mon.has_volatile("めいちゅうアップ")


def test_めいちゅうアップ_外れても消費される():
    """めいちゅうアップ: 技が外れた場合でも効果は消費される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ", move_names=["ハイドロポンプ"])],
        volatile1={"めいちゅうアップ": None},
    )
    mon = battle.actives[1]
    t.fix_random(battle, 0.97)  # 補正後命中率95に対し97で外れる
    t.run_move(battle, 1)
    assert battle.move_executor.move_missed
    assert not mon.has_volatile("めいちゅうアップ")


def test_メロメロ_同性に効かない():
    """メロメロ技: 同性ポケモンには効かない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メロメロ"], gender="male")],
        team1=[Pokemon("ピカチュウ", gender="male")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.has_volatile("メロメロ")


def test_メロメロ_性別不明に効かない():
    """メロメロ技: 性別不明ポケモンには効かない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メロメロ"], gender="male")],
        team1=[Pokemon("ピカチュウ", gender="")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.has_volatile("メロメロ")


def test_メロメロ_異性に効く():
    """メロメロ技: 異性ポケモンにはメロメロ状態を付与できる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メロメロ"], gender="male")],
        team1=[Pokemon("ピカチュウ", gender="female")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.has_volatile("メロメロ")


def test_メロメロ_行動不能():
    """メロメロ: 50%で行動不能になる"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"メロメロ": 1},
    )
    # 行動不能を強制
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success


def test_メロメロ_行動可能():
    """メロメロ: 行動可能（永続効果維持）"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"メロメロ": 1},
    )
    # 行動を許可
    battle.test_option.trigger_volatile = False
    t.run_move(battle, 0)
    assert battle.move_executor.action_success


def test_やどりぎのタネ():
    """やどりぎのタネ: ターン終了時ダメージ"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"やどりぎのタネ": 1}
    )
    from_mon, to_mon = battle.actives
    to_mon.hp = 1
    t.end_turn(battle)
    damage = from_mon.max_hp - from_mon.hp
    assert damage == from_mon.max_hp // 8
    assert to_mon.hp == 1 + damage


def test_やどりぎのタネ_くさタイプに失敗():
    """やどりぎのタネ技: くさタイプのポケモンには失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["やどりぎのタネ"])],
        team1=[Pokemon("フシギダネ")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.has_volatile("やどりぎのタネ")


def test_やどりぎのタネ_ヘドロえきでかいふくふうじの相手にもダメージを与える():
    """やどりぎのタネ: 回復側がかいふくふうじ状態でも、回復は阻止されるがヘドロえきのダメージ効果は発動する"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability_name="ヘドロえき")],
        volatile0={"やどりぎのタネ": 1},
        volatile1={"かいふくふうじ": 5},
    )
    from_mon, to_mon = battle.actives
    to_hp_before = to_mon.hp
    t.end_turn(battle)
    expected_drain = from_mon.max_hp // 8
    assert from_mon.hp == from_mon.max_hp - expected_drain
    # かいふくふうじにより通常の回復は発生しないが、ヘドロえきのダメージ効果は発動する
    assert to_mon.hp == to_hp_before - expected_drain


def test_やどりぎのタネ_ヘドロえきで回復がダメージに変換():
    """やどりぎのタネ: ヘドロえき持ちがやどりぎ状態のとき、回復側がダメージを受ける"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability_name="ヘドロえき")],
        volatile0={"やどりぎのタネ": 1},
    )
    from_mon, to_mon = battle.actives
    to_hp_before = to_mon.hp
    t.end_turn(battle)
    expected_drain = from_mon.max_hp // 8
    # やどりぎ状態のポケモンはダメージを受ける
    assert from_mon.hp == from_mon.max_hp - expected_drain
    # ヘドロえきにより回復がダメージに変換される
    assert to_mon.hp == to_hp_before - expected_drain


def test_やどりぎのタネ_マジックガードでダメージ無効():
    """やどりぎのタネ: マジックガード特性を持つポケモンはダメージを受けない。回復も発生しない"""
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ", ability_name="マジックガード")],
        volatile0={"やどりぎのタネ": 1},
    )
    from_mon, to_mon = battle.actives
    to_hp_before = to_mon.hp
    t.end_turn(battle)
    # マジックガード持ちはダメージなし
    assert from_mon.hp == from_mon.max_hp
    # 回復も発生しない
    assert to_mon.hp == to_hp_before


def test_やどりぎのタネ_回復側が交代すると新しい位置のポケモンが回復する():
    """やどりぎのタネ: 回復先は「使用者がいた場所」であり、使用者自身の交代後は
    その場所にいる新しいポケモンが回復する。"""
    battle = t.start_battle(
        team1=[Pokemon("ワンリキー"), Pokemon("マンキー")],
        team0=[Pokemon("カビゴン")],
        volatile0={"やどりぎのタネ": 1}
    )
    target_mon = battle.actives[0]
    old_healer = battle.actives[1]
    t.run_switch(battle, 1, 1)
    new_healer = battle.actives[1]
    assert new_healer is not old_healer
    # 回復量を観測できるよう、あらかじめHPを減らしておく
    new_healer.hp = new_healer.max_hp // 2
    new_healer_hp_before = new_healer.hp

    t.end_turn(battle)

    damage = target_mon.max_hp // 8
    assert target_mon.hp == target_mon.max_hp - damage
    # 交代先（現在その場所にいるポケモン）が回復する
    assert new_healer.hp == new_healer_hp_before + damage
    # ベンチに退いた元の使用者は回復しない
    assert old_healer.hp == old_healer.max_hp


def test_やどりぎのタネ_回復先満タンでも対象のHPは減る():
    battle = t.start_battle(
        team1=[Pokemon("ピカチュウ")],
        team0=[Pokemon("ピカチュウ")],
        volatile0={"やどりぎのタネ": 1}
    )
    target_mon, heal_mon = battle.actives
    heal_hp = heal_mon.hp
    t.end_turn(battle)
    assert target_mon.hp == target_mon.max_hp - target_mon.max_hp // 8
    assert heal_mon.hp == heal_hp


def test_リチャージ_動けないログがリチャージ解除ログより先に記録される():
    """seed=19 (LogInconsistency@volatile.py:リチャージ_block_action:1428) の回帰テスト。

    リチャージ_block_action は、「動けない」ログ（LogCode.ACTION_BLOCKED）を出す前に
    battle.volatile_manager.remove(mon, "リチャージ") を呼んでいたため、
    VolatileManager.remove 内部で記録される「リチャージが解除された」ログ
    （LogCode.VOLATILE_REMOVED）の方が先に記録され、ログを時系列順に読むと
    リチャージ状態が解除された直後に「動けない[リチャージ]」ログが続くという
    矛盾が生じていた。

    修正後は ACTION_BLOCKED ログを先に記録してから揮発性状態を解除するため、
    ACTION_BLOCKED ログの方が VOLATILE_REMOVED ログより先に記録されることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"リチャージ": 1},
    )
    mon = battle.actives[0]

    t.run_move(battle, 0)

    assert not mon.has_volatile("リチャージ")
    assert battle.move_executor.action_success is False

    logs = battle.event_logger.logs
    blocked_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.ACTION_BLOCKED)
    removed_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.VOLATILE_REMOVED)
    # 修正前は removed_idx < blocked_idx になっていた
    assert blocked_idx < removed_idx


def test_ロックオン_ターン経過で解除():
    """ロックオン: count=1 でターン終了後に揮発状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ロックオン": 1},
    )
    mon = battle.actives[0]
    assert mon.has_volatile("ロックオン")
    t.end_turn(battle)
    assert not mon.has_volatile("ロックオン")


def test_ロックオン_交代で解除():
    """ロックオン: 相手が交代するとロックオン状態が解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        volatile0={"ロックオン": 2},
    )
    mon = battle.actives[0]
    assert mon.has_volatile("ロックオン")
    # 相手が交代するとロックオン状態が解除される
    t.run_switch(battle, 1, 1)
    assert not mon.has_volatile("ロックオン")


def test_ロックオン_必中化():
    """ロックオン状態で技を使うと命中率が None（必中）になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ロックオン": 1},
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None


def test_使える技がなければわるあがきになる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うたう"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"じごくづき": 2}
    )
    with battle.phase_context("action"):
        commands = battle.get_available_commands(battle.players[0])
    assert commands == [Command.STRUGGLE]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
