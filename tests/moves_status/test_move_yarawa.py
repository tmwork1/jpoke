"""変化技ハンドラの単体テスト（や・ら・わ行）。"""

import pytest

from jpoke import Pokemon
from .. import test_utils as t


def test_ねがいごと_かいふくふうじ状態では使用できない():
    """ねがいごと: heal フラグを持つため、かいふくふうじ状態では使用（選択）できず失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねがいごと"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"かいふくふうじ": 3},
        accuracy=100,
    )
    mon = battle.actives[0]

    t.run_move(battle, 0)

    assert not battle.move_executor.action_success
    assert not battle.get_side(mon).get("ねがいごと").is_active


def test_ねがいごと_使用者の最大HPの半分を次のターン終了時に回復する():
    """ねがいごと: 技を使用すると次のターン終了時に使用者の最大HPの半分（切り捨て）が回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねがいごと"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    max_hp = mon.max_hp
    battle.modify_hp(mon, v=-(max_hp - 1))
    hp_before = mon.hp

    t.run_move(battle, 0)
    field = battle.get_side(mon).get("ねがいごと")
    assert field.is_active
    assert field.heal == max_hp // 2

    # 1ターン目（使用ターン）終了: まだ回復しない
    t.end_turn(battle)
    assert mon.hp == hp_before

    # 2ターン目終了: 回復が発動しフィールドが解除される
    t.end_turn(battle)
    assert mon.hp == hp_before + max_hp // 2
    assert not field.is_active


def test_ねがいごと_重複設置は失敗する():
    """ねがいごと: すでに設置済みなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねがいごと"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]

    # 1回目: 設置成功（count=2）
    t.run_move(battle, 0)
    assert battle.get_side(mon).get("ねがいごと").is_active
    count_after_first = battle.get_side(mon).get("ねがいごと").count

    # 2回目: 失敗（フィールドはまだ有効）
    t.run_move(battle, 0)
    # カウントはリセットされず変化しない（重複設置されていない）
    assert battle.get_side(mon).get("ねがいごと").count == count_after_first


@pytest.mark.parametrize(
    "item_name",
    ["こだわりスカーフ", "こだわりハチマキ", "こだわりメガネ"]
)
def test_ねごと_こだわり系アイテムはねごと自体でロックされる(item_name):
    """ねごと: こだわり系アイテムはねごとで選ばれた技ではなく「ねごと」自体でロックされる（第五世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["ねごと", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("ねむり", 3),
        accuracy=100,
    )
    mon = battle.actives[0]

    t.run_move(battle, 0, 0)

    assert mon.has_volatile("こだわり")
    assert mon.volatiles["こだわり"].move_name == "ねごと"


def test_ねごと_ねごと自身のPPのみ消費する():
    """ねごと: ねごと自身のPPのみ消費し、選ばれた技のPPは消費しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねごと", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("ねむり", 3),
        accuracy=100,
    )
    mon = battle.actives[0]
    negoto = mon.moves[0]
    taiatari = mon.moves[1]

    t.run_move(battle, 0, 0)

    assert negoto.pp == 11, "ねごとのPPは1消費される"
    assert taiatari.pp == 35, "選ばれた技のPPは消費されない"


def test_ねごと_ねむりカウントは1ターンに1回のみ消費される():
    """ねごと: サブ実行された技の ON_TRY_ACTION でねむりカウントが二重に消費されない
    （ねごと自身の分の1回のみ消費される）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねごと", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("ねむり", 3),
        accuracy=100,
    )
    mon = battle.actives[0]

    t.run_move(battle, 0, 0)

    assert mon.ailment.count == 2, "ねむりカウントは1ターンに1回のみ消費される"


def test_ねごと_ねむり状態でない場合は失敗するがPPは消費する():
    """ねごと: ねむり状態でない場合は ON_TRY_MOVE_1 で失敗するが、ねごと自身のPPは消費される
    （PP消費は ON_TRY_ACTION 通過後・ON_TRY_MOVE_1 到達前に行われるため）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねごと", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    negoto = mon.moves[0]

    t.run_move(battle, 0, 0)

    assert negoto.pp == 11, "ねむり状態でない失敗時もねごとのPPは消費される"


def test_ねごと_候補技がすべてnon_negotoの場合は失敗():
    """ねごと: 覚えている技がすべて non_negoto ラベル付きの場合（ねごとのみ）は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねごと"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("ねむり", 3),
        accuracy=100,
    )
    mon = battle.actives[0]
    negoto = mon.moves[0]
    defender = battle.actives[1]
    hp_before = defender.hp

    t.run_move(battle, 0, 0)

    assert negoto.pp == 11, "失敗してもねごとのPPは消費される"
    assert defender.hp == hp_before, "候補技なしの場合はダメージを与えない"


def test_ねごと_変化技を選んでも無限再帰にならない():
    """ねごと: 選ばれた技が変化技（status技）の場合でも RecursionError 等を起こさず正常に実行される

    ねごと自身のON_STATUS_HITハンドラを解除せずに選んだ技を実行すると、
    ネストしたrun_move内で再度ON_STATUS_HITが発火した際にねごと_select_and_execute
    が多重発火し無限再帰してしまう回帰を防ぐテスト。
    候補技を非攻撃技（なきごえ）のみにすることで選択結果を決定的にしている。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねごと", "なきごえ"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("ねむり", 3),
        accuracy=100,
    )
    mon = battle.actives[0]
    negoto = mon.moves[0]
    nakigoe = mon.moves[1]
    defender = battle.actives[1]

    t.run_move(battle, 0, 0)  # ピカチュウ: ねごと（候補はなきごえのみ）

    assert battle.move_executor.move_applied
    assert defender.rank["atk"] == -1  # なきごえが実行されカビゴンのこうげきが下がる
    assert negoto.pp == 11, "ねごとのPPは1消費される"
    assert nakigoe.pp == 40, "選ばれた技のPPは消費されない"


def test_ねごと_残りPPが0の技を選んでもわるあがきにならない():
    """ねごと: 選ばれた技の残りPPが0でも成功し、わるあがきに置き換わらない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねごと", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("ねむり", 3),
        accuracy=100,
    )
    mon = battle.actives[0]
    taiatari = mon.moves[1]
    taiatari.pp = 0
    defender = battle.actives[1]
    hp_before = defender.hp

    t.run_move(battle, 0, 0)

    assert defender.hp < hp_before, "PP0のたいあたりがそのまま実行されダメージを与える"
    assert taiatari.pp == 0, "選ばれた技のPPは消費されない（0のまま）"


def test_ねごと_溜め技は候補から除外される():
    """ねごと: 溜め技（ソーラービーム等）は選ばれない技のため、候補がなければ失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねごと", "ソーラービーム"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("ねむり", 3),
        accuracy=100,
    )
    mon = battle.actives[0]
    negoto = mon.moves[0]
    defender = battle.actives[1]
    hp_before = defender.hp

    t.run_move(battle, 0, 0)

    assert defender.hp == hp_before, "溜め技は候補から除外され、他に候補がないため失敗する"
    assert negoto.pp == 11, "失敗してもねごとのPPは消費される"


def test_ねごと_選ばれた技が実行されダメージを与える():
    """ねごと: ねむり中に選ばれた技が実際に実行されてダメージを与える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねごと", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("ねむり", 3),
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp

    t.run_move(battle, 0, 0)

    assert defender.hp < hp_before, "ねごとで選ばれた技がダメージを与える"


def test_ねむる_HP全回復する():
    """ねむる: 使用後に HP が最大HP になること"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    hp_before = mon.hp
    assert hp_before < mon.max_hp

    t.run_move(battle, 0)

    assert mon.hp == mon.max_hp


def test_ねむる_HP満タンでは失敗する():
    """ねむる: HP が最大HPのときは失敗すること"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    assert mon.hp == mon.max_hp

    t.run_move(battle, 0)

    # HP 満タンなので失敗 → ねむり状態にならない
    assert not mon.has_ailment("ねむり")


def test_ねむる_PPはchampions仕様で8():
    """ねむる: championsルールによりPPは8（docs/champions/move_list.txt準拠）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.moves[0].pp == 8


def test_ねむる_すでにねむり状態では失敗する():
    """ねむる: すでにねむり状態のときは失敗すること"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("ねむり", 3),
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    hp_before = mon.hp

    t.run_move(battle, 0)

    # すでにねむり状態なので失敗 → HP も回復しない
    # ねむりカウントは ON_TRY_ACTION でターン経過するため count は変化する可能性がある
    assert mon.hp == hp_before
    assert mon.has_ailment("ねむり")


def test_ねむる_ぜったいねむりのゆめうつつ状態では失敗しHPも回復しない():
    """ねむる: 特性ぜったいねむりによるゆめうつつ状態（uncurable）は上書きできず、
    技全体が失敗しHPも回復しない"""
    battle = t.start_battle(
        team0=[Pokemon("ネッコアラ", ability_name="ぜったいねむり", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    assert mon.ailment.name == "ゆめうつつ"
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    hp_before = mon.hp

    t.run_move(battle, 0)

    assert not battle.move_executor.move_success
    assert mon.hp == hp_before
    assert mon.ailment.name == "ゆめうつつ"


@pytest.mark.parametrize("ability_name", ["やるき", "ふみん", "スイートベール", "きよめのしお"])
def test_ねむる_ねむり無効特性では失敗しHPも回復しない(ability_name: str):
    """ねむる: やるき/ふみん/スイートベール/きよめのしお等ねむり無効特性を持つ場合、
    ねむり付与自体に失敗するため技全体が失敗し、HPも回復しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name=ability_name, move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    hp_before = mon.hp

    t.run_move(battle, 0)

    assert not battle.move_executor.move_success
    assert mon.hp == hp_before
    assert not mon.has_ailment("ねむり")


def test_ねむる_ねむり状態になる():
    """ねむる: 使用後に count=3 のねむり状態になること（Champions仕様: ねむる固定count=3）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))

    t.run_move(battle, 0)

    assert mon.has_ailment("ねむり")
    assert mon.ailment.count == 3


def test_ねむる_リミットシールドのりゅうせいのすがたでは失敗しHPも回復しない():
    """ねむる: リミットシールドのりゅうせいのすがたでは状態異常にならないため、
    ねむるは技全体が失敗しHPも回復しない"""
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    assert mon.name == "メテノ(りゅうせい)"
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    hp_before = mon.hp

    t.run_move(battle, 0)

    assert not battle.move_executor.move_success
    assert mon.hp == hp_before
    assert not mon.has_ailment("ねむり")


def test_ねむる_リーフガードのにほんばれ下では失敗しHPも回復しない():
    """ねむる: リーフガード特性のポケモンがにほんばれ下で使用すると失敗し、HPも回復しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="リーフガード", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    hp_before = mon.hp

    t.run_move(battle, 0)

    assert not battle.move_executor.move_success
    assert mon.hp == hp_before
    assert not mon.has_ailment("ねむり")


def test_ねむる_既存の状態異常が解除される():
    """ねむる: どく状態のまま使用すると状態異常が解除された後にねむり状態になること"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("どく", None),
        accuracy=100,
    )
    mon = battle.actives[0]
    assert mon.has_ailment("どく")
    battle.modify_hp(mon, v=-(mon.max_hp // 2))

    t.run_move(battle, 0)

    assert not mon.has_ailment("どく")
    assert mon.has_ailment("ねむり")


def test_ねむる_相手がさわぐ状態のときは失敗しHPも回復しない():
    """ねむる: 場に（相手も含めて）さわぐ状態のポケモンがいるときは失敗し、HPも回復しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"さわぐ": 2},
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    hp_before = mon.hp

    t.run_move(battle, 0)

    assert not battle.move_executor.move_success
    assert mon.hp == hp_before
    assert not mon.has_ailment("ねむり")


def test_ねむる_相手のマジックコートで跳ね返されない():
    """ねむる: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    hp_before = mon.hp

    t.run_move(battle, 0)

    assert battle.move_executor.move_success
    assert mon.hp > hp_before
    assert mon.has_ailment("ねむり")
    assert not foe.has_ailment("ねむり")


def test_ねむる_相手のまもるで防がれない():
    """ねむる: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ねむる"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-(mon.max_hp // 2))
    hp_before = mon.hp

    t.run_move(battle, 0)

    assert battle.move_executor.move_success
    assert mon.hp > hp_before
    assert mon.has_ailment("ねむり")


def test_のろい_ゴーストタイプ_HP1でも呪いは成功し相手にのろい付与():
    """のろい（呪い）: 使用者がHP1でも呪いは成功し、使用者がひんしになっても相手にのろい状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["のろい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    defender = battle.actives[1]

    # HPを1にする
    battle.modify_hp(mon, v=-(mon.max_hp - 1))
    assert mon.hp == 1

    t.run_move(battle, 0)

    # 使用者はひんし
    assert not mon.alive
    # 相手にのろい状態が付与されている
    assert defender.has_volatile("のろい")


def test_のろい_ゴーストタイプ_HP消費と相手へのろい付与():
    """のろい（呪い）: ゴーストタイプが使うと最大HPの半分を消費し相手にのろい状態を付与する"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["のろい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    defender = battle.actives[1]
    max_hp = mon.max_hp
    t.run_move(battle, 0)

    assert mon.hp == max_hp - max_hp // 2
    assert defender.has_volatile("のろい")


def test_のろい_ゴーストタイプ_すでにのろい状態なら失敗():
    """のろい（呪い）: 相手がすでにのろい状態なら失敗し、HPは消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["のろい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"のろい": 1},
        accuracy=100,
    )
    mon = battle.actives[0]
    hp_before = mon.hp
    t.run_move(battle, 0)

    # 失敗のためHPは消費されない
    assert mon.hp == hp_before


def test_のろい_ゴーストタイプ以外_こうげきぼうぎょ上がりすばやさ下がる():
    """のろい（鈍い）: 非ゴーストタイプが使うと こうげく+1・ぼうぎょ+1・すばやさ-1"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["のろい"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)

    assert mon.rank["atk"] == 1
    assert mon.rank["def"] == 1
    assert mon.rank["spe"] == -1


def test_のろい_のろい状態のポケモンはターン終了時に最大HPの1_4ダメージ():
    """のろい状態: ターン終了時に最大HPの1/4ダメージを受ける"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["のろい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    max_hp = defender.max_hp

    # のろい状態を付与
    t.run_move(battle, 0)
    assert defender.has_volatile("のろい")
    hp_after_curse = defender.hp

    # ターン終了処理
    t.end_turn(battle)

    assert defender.hp == hp_after_curse - max_hp // 4


def test_ハロウィン_ゴーストタイプが付与される():
    """ハロウィン: 使用後に defender が「ゴースト」タイプになること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハロウィン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert not defender.has_type("ゴースト")
    t.run_move(battle, 0)

    assert defender.has_type("ゴースト")


def test_ハロウィン_すでにゴーストタイプなら失敗():
    """ハロウィン: 相手がすでにゴーストタイプなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハロウィン"])],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # ゴーストタイプには付与されない
    assert not defender.has_volatile("ハロウィン")


def test_ハロウィン_ハロウィン状態を付与する():
    """ハロウィン: 相手にハロウィン状態を付与する（ゴーストタイプが追加される）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハロウィン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("ハロウィン")


def test_ハロウィン_交代後にゴーストタイプがリセットされる():
    """ハロウィン: 交代後に added_types がリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ハロウィン"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドラン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_type("ゴースト")

    # 交代後はゴーストタイプが消えること
    t.run_switch(battle, 1, 1)
    assert not defender.has_type("ゴースト")
    assert not defender.has_volatile("ハロウィン")


def test_やどりぎのタネ_すでにやどりぎ状態なら失敗():
    """やどりぎのタネ: 相手がすでにやどりぎのタネ状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["やどりぎのタネ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"やどりぎのタネ": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    old_count = defender.volatiles["やどりぎのタネ"].count
    t.run_move(battle, 0)

    # カウントは変わらない（重複付与されない）
    assert defender.has_volatile("やどりぎのタネ")
    assert defender.volatiles["やどりぎのタネ"].count == old_count


def test_やどりぎのタネ_やどりぎのタネ状態を付与する():
    """やどりぎのタネ: 相手をやどりぎのタネ状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["やどりぎのタネ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("やどりぎのタネ")


def test_ゆきげしき_おおひでり中は失敗する():
    """ゆきげしき: おおひでり中は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ゆきげしき"])],
        team1=[Pokemon("カビゴン")],
        weather=("おおひでり", 99),
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "おおひでり"


def test_ゆきげしき_天気がゆきになる():
    """ゆきげしき: 使用後に天気がゆきになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ゆきげしき"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "ゆき"
    assert battle.weather.count == 5


def test_リサイクル_アイテムを失ったことがない場合は失敗する():
    """リサイクル: アイテムを一度も失っていない場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["リサイクル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    assert not mon.has_item()
    assert mon.last_lost_item_name == ""

    t.run_move(battle, 0)

    # アイテムを失ったことがないので失敗 → アイテムは取得されない
    assert not mon.has_item()


def test_リサイクル_アイテムを持っている場合は失敗する():
    """リサイクル: すでにアイテムを持っている場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["リサイクル"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    assert mon.has_item()

    t.run_move(battle, 0)

    # アイテムを持っているので失敗 → アイテムは変化しない
    assert mon.item.name == "オボンのみ"


def test_リサイクル_アイテム喪失後に取り戻す():
    """リサイクル: remove_item でアイテムを失った後にリサイクルで元のアイテムが戻る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["リサイクル"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    # アイテムを失わせる
    battle.item_manager.remove_item(mon)
    assert not mon.has_item()
    assert mon.last_lost_item_name == "オボンのみ"

    t.run_move(battle, 0)

    # リサイクルでオボンのみが戻る
    assert mon.item.name == "オボンのみ"


def test_リサイクル_すりかえ後はlast_lost_item_nameが設定されず失敗する():
    """リサイクル: すりかえ（両者がアイテムを持つ場合）後は last_lost_item_name がセットされないため失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["リサイクル"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン", item_name="たべのこし")],
        accuracy=100,
    )
    mon = battle.actives[0]
    # 両者アイテムありの状態ですりかえを模倣（swap_items）
    battle.item_manager.swap_items()
    # すりかえ後はピカチュウがたべのこしを持ち、last_lost_item_name は空のまま
    assert mon.item.name == "たべのこし"
    assert mon.last_lost_item_name == ""

    t.run_move(battle, 0)

    # last_lost_item_name が空なので失敗 → アイテムは変化しない
    assert mon.item.name == "たべのこし"


def test_リサイクル_どろぼうで奪われた道具は取り戻せない():
    """リサイクル: take_item（どろぼう相当）で奪われた道具は場に存在し続けるため復元できない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["リサイクル"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    # どろぼう相当の奪取をtake_itemで再現する（foeがmonの道具を奪う）
    battle.item_manager.take_item(mon)
    assert foe.item.name == "オボンのみ"
    assert not mon.has_item()
    assert mon.last_lost_item_name == ""

    t.run_move(battle, 0)

    # last_lost_item_name が空なので失敗 → monはアイテムを取り戻せない
    assert not mon.has_item()


def test_リサイクル_消費したきのみを取り戻す():
    """リサイクル: きのみを消費した後にリサイクルで元のきのみが戻る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["リサイクル"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    # HPを50%以下に下げてオボンのみを自動消費させる
    # modify_hp内でON_HP_CHANGEDが自動発火されオボンのみが消費される
    mon.hp = mon.max_hp // 2 + 1
    battle.modify_hp(mon, v=-1)

    # きのみが消費されたことを確認
    assert not mon.has_item()
    assert mon.last_lost_item_name == "オボンのみ"

    t.run_move(battle, 0)

    # リサイクルでオボンのみが戻る
    assert mon.item.name == "オボンのみ"
    assert mon.last_lost_item_name == "オボンのみ"


def test_わたほうし_相手のすばやさ1段階下がる():
    """わたほうし: 使用すると相手のすばやさランクが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["わたほうし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["spe"] == -2
