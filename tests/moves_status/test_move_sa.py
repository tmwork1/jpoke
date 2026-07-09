"""変化技ハンドラの単体テスト（さ行・サ行）。"""

import pytest
from jpoke import Pokemon
from jpoke.data.move import MOVES
from jpoke.enums import Interrupt, LogCode
from jpoke.utils.math import round_half_down
from .. import test_utils as t


def test_３ぼんのや_ひるみが発動する():
    """３ぼんのや: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("バンギラス", move_names=["3ぼんのや"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_さいきのいのり_ひんし状態の味方がいない場合は失敗する():
    """さいきのいのり: ひんし状態の味方（控え）がいない場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいきのいのり"]), Pokemon("カビゴン")],
        team1=[Pokemon("フシギバナ")],
    )
    ally = battle.player_states[battle.players[0]].team[1]

    t.run_move(battle, 0)

    assert ally.hp == ally.max_hp


def test_さいきのいのり_ひんし状態の味方を最大HPの半分回復して復活させる():
    """さいきのいのり: ひんし状態の味方（控え）を最大HPの1/2（切り捨て）回復して復活させる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいきのいのり"]), Pokemon("カビゴン")],
        team1=[Pokemon("フシギバナ")],
    )
    ally = battle.player_states[battle.players[0]].team[1]
    battle.faint(ally)
    assert ally.hp == 0

    t.run_move(battle, 0)

    assert ally.hp == ally.max_hp // 2
    assert ally.alive


def test_さいきのいのり_複数ひんしがいる場合は選出順で最初の味方を復活させる():
    """さいきのいのり: 複数のひんし状態の味方がいる場合、選出順で最初のポケモンを復活させる。"""
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", move_names=["さいきのいのり"]),
            Pokemon("カビゴン"),
            Pokemon("ライチュウ"),
        ],
        team1=[Pokemon("フシギバナ")],
    )
    state = battle.player_states[battle.players[0]]
    first_ally, second_ally = state.team[1], state.team[2]
    battle.faint(first_ally)
    battle.faint(second_ally)

    t.run_move(battle, 0)

    assert first_ally.alive
    assert second_ally.hp == 0


def test_さいはい_まもるで防がれる():
    """さいはい: 対象がまもる状態のときは防がれ、相手のPPは消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいはい"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    move = defender.moves[0]
    t.run_move(battle, 1)
    pp_after_first_use = move.pp
    battle.volatile_manager.apply(defender, "まもる", count=1)

    t.run_move(battle, 0)

    assert move.pp == pp_after_first_use


def test_さいはい_わるあがきは指示できない():
    """さいはい: 相手の直前の技がわるあがきの場合は指示できず失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいはい"])],
        team1=[Pokemon("カビゴン", move_names=["わるあがき"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 1)
    assert defender.executed_move.name == "わるあがき"
    hp_after_first_hit = attacker.hp

    t.run_move(battle, 0)

    # さいはいは失敗し、わるあがきによる追加ダメージは発生しない
    assert attacker.hp == hp_after_first_hit


def test_さいはい_相手が技を使っていない場合は失敗():
    """さいはい: 相手がまだ技を使っていない場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいはい"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    move = defender.moves[0]
    pp_before = move.pp

    t.run_move(battle, 0)

    assert move.pp == pp_before
    assert defender.executed_move is None


def test_さいはい_相手の技のPPがすでに0の場合は失敗():
    """さいはい: 相手の直前の技のPPがすでに0の場合は失敗する（わるあがきに自動置換されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいはい"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    move = defender.moves[0]
    t.run_move(battle, 1)
    move.modify_pp(-move.pp)
    assert move.pp == 0

    t.run_move(battle, 0)

    assert move.pp == 0
    assert defender.executed_move.name == "たいあたり"


def test_さいはい_相手の直前の技をもう一度使わせる():
    """さいはい: 相手が直前に使用した技を、相手のPPを消費してもう一度使わせる。

    再実行された技の宛先はさいはいの使用者になるため、使用者が2回分のダメージを受ける。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいはい"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    move = defender.moves[0]
    # カビゴンにたいあたりを使わせてexecuted_moveを設定する
    t.run_move(battle, 1)
    pp_after_first_use = move.pp
    hp_after_first_hit = attacker.hp

    # さいはいで指示する
    t.run_move(battle, 0)

    # 相手（カビゴン）のPPがもう1消費される
    assert move.pp == pp_after_first_use - 1
    # さいはいの使用者（ピカチュウ）が再度ダメージを受ける
    assert attacker.hp < hp_after_first_hit


def test_さいみんじゅつ_ねむり付与():
    """さいみんじゅつ: 相手をねむり状態にする（accuracy=100で固定）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_ailment("ねむり")


def test_さむいギャグ_すでにゆきで交代先もいない場合は完全失敗():
    """さむいギャグ: すでにゆきかつ控えポケモンがいない場合は技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さむいギャグ"])],
        team1=[Pokemon("カビゴン")],
        weather=("ゆき", 3),
    )
    t.run_move(battle, 0)

    # ゆきのカウントは変わらない
    assert battle.weather.count == 3
    # 交代フラグも立たない
    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_さむいギャグ_すでにゆき状態でも交代可能なら成功():
    """さむいギャグ: すでにゆき状態でも控えポケモンがいれば交代割り込みが設定される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さむいギャグ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        weather=("ゆき", 5),
    )
    t.run_move(battle, 0)

    # ゆきは変わらないが交代フラグは立つ
    assert battle.weather.name == "ゆき"
    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.PIVOT


def test_さむいギャグ_ゆきが5ターン発生しInterruptが設定される():
    """さむいギャグ: 天候がゆきに変わり、交代割り込みフラグが設定される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さむいギャグ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    assert battle.weather.name == "ゆき"
    assert battle.weather.count == 5
    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.PIVOT


def test_さむいギャグ_交代が実行される():
    """さむいギャグ: 交代コマンドが処理されると控えポケモンが場に出る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さむいギャグ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    raichu = battle.player_states[battle.players[0]].team[1]
    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    assert battle.actives[0] is raichu


def test_さむいギャグ_交代先がいなくてもゆき変更成功なら技は成功する():
    """さむいギャグ: 控えポケモンがいなくても天候をゆきに変えられれば技は成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さむいギャグ"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    assert battle.weather.name == "ゆき"
    assert battle.weather.count == 5
    # 交代フラグは立たない
    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_さむいギャグ_強天候下ではゆき変更は失敗するが交代のみ発動する():
    """さむいギャグ: おおひでり等の永続天候下ではゆきへの変更は失敗するが、交代先がいれば交代は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さむいギャグ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        weather=("おおひでり", 99),
    )
    t.run_move(battle, 0)

    # 天候はおおひでりのまま変わらない
    assert battle.weather.name == "おおひでり"
    # 交代フラグは立つ
    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.PIVOT


def test_しっぽきり_HP半分以下なら失敗():
    """しっぽきり: 使用者のHPが最大HPの半分以下の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["しっぽきり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    # HP を最大HPの半分ちょうどに設定
    battle.modify_hp(attacker, -(max_hp - max_hp // 2))
    assert attacker.hp == max_hp // 2
    t.run_move(battle, 0)

    # みがわりは生成されない
    assert not attacker.has_volatile("みがわり")
    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_しっぽきり_みがわりとそのHPが交代先に引き継がれる():
    """しっぽきり: 生成したみがわりとそのHPが交代先ポケモンに引き継がれる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["しっぽきり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    migawari_hp = max_hp // 4
    raichu = battle.player_states[battle.players[0]].team[1]

    t.run_move(battle, 0)
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    new_mon = battle.actives[0]
    assert new_mon is raichu
    # 交代先にみがわりが引き継がれている
    assert new_mon.has_volatile("みがわり")
    # みがわりのHPは使用者の最大HPの1/4（切り捨て）
    assert new_mon.volatiles["みがわり"].hp == migawari_hp


def test_しっぽきり_みがわり中は失敗():
    """しっぽきり: 使用者がすでにみがわり状態の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["しっぽきり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"みがわり": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    # みがわりは上書きされない
    assert attacker.has_volatile("みがわり")
    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_しっぽきり_控えがいない場合は失敗():
    """しっぽきり: 交代できる控えポケモンがいない場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["しっぽきり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    # みがわりは生成されない
    assert not attacker.has_volatile("みがわり")
    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_しっぽきり_消費コストちょうどでも失敗する():
    """しっぽきり: HPが消費コスト（最大HPの半分・切り上げ）ちょうどの場合、
    支払うとHPが0になってしまうため失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["しっぽきり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    cost = (max_hp + 1) // 2
    battle.modify_hp(attacker, -(attacker.hp - cost))
    assert attacker.hp == cost
    t.run_move(battle, 0)

    # みがわりは生成されない
    assert not attacker.has_volatile("みがわり")
    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_しっぽきり_消費コストより1多いHPなら成功する():
    """しっぽきり: HPが消費コストより1多い場合は成功し、HPが1残る"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["しっぽきり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    cost = (max_hp + 1) // 2
    battle.modify_hp(attacker, -(attacker.hp - (cost + 1)))
    assert attacker.hp == cost + 1
    t.run_move(battle, 0)

    assert attacker.hp == 1
    assert attacker.has_volatile("みがわり")
    player = battle.players[0]
    assert battle.player_states[player].interrupt == Interrupt.PIVOT


def test_しっぽをふる_ぼうぎょが1段階下がる():
    """しっぽをふる: 使用すると相手のぼうぎょが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しっぽをふる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["def"] == -1


def test_しっぽをふる_ぼうぎょが最低値のとき変化なし():
    """しっぽをふる: ぼうぎょランクがすでに-6のときはランクが変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しっぽをふる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"def": -6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.rank["def"] == -6


def test_しびれごな_くさタイプに無効化される():
    """しびれごな: 草タイプの相手にはまひ状態を付与できない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しびれごな"])],
        team1=[Pokemon("フシギバナ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_ailment("まひ")


def test_しびれごな_まひ付与():
    """しびれごな: 相手をまひ状態にする（accuracy=100で固定）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しびれごな"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_ailment("まひ")


def test_しょうりのまい_こうげきぼうぎょすばやさが1段階ずつ上がる():
    """しょうりのまい: 使用すると自分のこうげき・ぼうぎょ・すばやさランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しょうりのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.rank["atk"] == 0
    assert attacker.rank["def"] == 0
    assert attacker.rank["spe"] == 0
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["def"] == 1
    assert attacker.rank["spe"] == 1


def test_しろいきり_すでにアクティブなら失敗():
    """しろいきり: すでにしろいきりが有効なら失敗（再設置されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しろいきり"])],
        team1=[Pokemon("カビゴン")],
        side0={"しろいきり": 4},
    )
    side = battle.get_side(battle.actives[0])
    t.run_move(battle, 0)

    # カウントは変わらない
    assert side.fields["しろいきり"].is_active
    assert side.fields["しろいきり"].count == 4


def test_しろいきり_自陣営に5ターン設置される():
    """しろいきり: 使用すると自陣営に5ターンのしろいきりが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しろいきり"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[0])
    assert side.fields["しろいきり"].is_active
    assert side.fields["しろいきり"].count == 5


def test_しろいきり_設置後に相手の能力低下技を防ぐ():
    """しろいきり: 使用後、相手の能力ランク低下技の効果を防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しろいきり"])],
        team1=[Pokemon("カビゴン", move_names=["なきごえ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    t.run_move(battle, 1)

    assert attacker.rank["atk"] == 0


def test_しんぴのまもり_すでにアクティブなら失敗():
    """しんぴのまもり: すでにしんぴのまもりが有効なら失敗（再設置されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しんぴのまもり"])],
        team1=[Pokemon("カビゴン")],
        side0={"しんぴのまもり": 4},
    )
    side = battle.get_side(battle.actives[0])
    t.run_move(battle, 0)

    # カウントは変わらない
    assert side.fields["しんぴのまもり"].is_active
    assert side.fields["しんぴのまもり"].count == 4


def test_しんぴのまもり_自陣営に5ターン設置される():
    """しんぴのまもり: 使用すると自陣営に5ターンのしんぴのまもりが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しんぴのまもり"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[0])
    assert side.fields["しんぴのまもり"].is_active
    assert side.fields["しんぴのまもり"].count == 5


def test_シンプルビーム_protectedフラグ持ちに失敗():
    """シンプルビーム: アイスフェイス（protectedフラグ持ち）の相手には失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["シンプルビーム"])],
        team1=[Pokemon("カビゴン", ability_name="アイスフェイス")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 特性は変化しない
    assert defender.ability.name == "アイスフェイス"


def test_シンプルビーム_交代後に元の特性に戻る():
    """シンプルビーム: 特性をたんじゅんに変えられた後に交代すると元の特性に戻る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["シンプルビーム"])],
        team1=[
            Pokemon("カビゴン", ability_name="めんえき"),
            Pokemon("ラッキー", ability_name="しぜんかいふく"),
        ],
        accuracy=100,
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    assert defender_before.ability.name == "たんじゅん"

    # 交代で元の特性に戻ることを確認
    t.run_switch(battle, 1, 1)
    assert defender_before.ability.name == "めんえき"


def test_シンプルビーム_通常特性をたんじゅんに変更():
    """シンプルビーム: 通常特性（せいでんき等）の相手に使うと特性が「たんじゅん」に変わる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["シンプルビーム"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.ability.name == "たんじゅん"


def test_じこあんじ_しろいハーブでマイナスランクを打ち消す():
    """じこあんじ: コピー結果に負のランクが含まれる場合、しろいハーブが発動してランクを0に戻す"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="しろいハーブ", move_names=["じこあんじ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender.rank["atk"] = -2
    defender.rank["spa"] = 1
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 0
    assert attacker.rank["spa"] == 1
    assert not attacker.has_item()


def test_じこあんじ_だっしゅつパックは発動しない():
    """じこあんじ: 直接代入によりランクが下がっても、だっしゅつパックは発動しない"""
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", item_name="だっしゅつパック", move_names=["じこあんじ"]),
            Pokemon("ライチュウ"),
        ],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["atk"] = -2
    state0 = battle._player_states[0]
    t.run_move(battle, 0)

    assert state0.active_index == 0
    assert state0.team[0].has_item()


def test_じこあんじ_まもる状態の相手にも効果が発動する():
    """じこあんじ: unprotectableフラグを持つため、まもる状態の相手にも効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこあんじ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 2


def test_じこあんじ_みがわり状態の相手にも効果が発動する():
    """じこあんじ: bypass_substituteフラグを持つため、みがわり状態の相手にも効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこあんじ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"みがわり": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 2


def test_じこあんじ_命中判定を行わず必ず命中する():
    """じこあんじ: 必中技であり、命中判定自体を行わない（回避ランクの影響を受けない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこあんじ"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    assert battle.move_executor.accuracy is None


def test_じこあんじ_急所ランクをコピーする():
    """じこあんじ: 相手のきゅうしょアップ状態（急所ランク）も第六世代以降コピーする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこあんじ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender.critical_rank = 2
    t.run_move(battle, 0)

    assert attacker.critical_rank == 2
    assert attacker.has_volatile("きゅうしょアップ")


def test_じこあんじ_相手のランクが全て0のとき自分のランクも全て0になる():
    """じこあんじ: 相手のランクが全て0のとき、自分のランクも全て0になること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこあんじ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # 使用者にランクをあらかじめ設定しておく
    attacker.rank["atk"] = 3
    attacker.rank["def"] = -2
    attacker.rank["spa"] = 1
    t.run_move(battle, 0)

    for stat in ("atk", "def", "spa", "spd", "spe", "accuracy", "evasion"):
        assert attacker.rank[stat] == 0


def test_じこあんじ_相手のランクは変化しない():
    """じこあんじ: 使用後も相手のランクは変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこあんじ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    defender.rank["spa"] = -3
    t.run_move(battle, 0)

    assert defender.rank["atk"] == 2
    assert defender.rank["spa"] == -3


def test_じこあんじ_相手のランク変化を自分にコピーする():
    """じこあんじ: 相手の全ランク変化（A/B/C/D/S/ACC/EVA）を自分にコピーすること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこあんじ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    defender.rank["def"] = -1
    defender.rank["spa"] = 3
    defender.rank["spd"] = -2
    defender.rank["spe"] = 1
    defender.rank["accuracy"] = -1
    defender.rank["evasion"] = 2
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 2
    assert attacker.rank["def"] == -1
    assert attacker.rank["spa"] == 3
    assert attacker.rank["spd"] == -2
    assert attacker.rank["spe"] == 1
    assert attacker.rank["accuracy"] == -1
    assert attacker.rank["evasion"] == 2


def test_じこあんじ_相手の急所ランクが0なら自分の急所ランクも消える():
    """じこあんじ: 自分が事前にきゅうしょアップ状態でも、相手の急所ランクが0ならクリアされる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこあんじ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.critical_rank = 2
    t.run_move(battle, 0)

    assert attacker.critical_rank == 0
    assert not attacker.has_volatile("きゅうしょアップ")


def test_じこさいせい_マジックコートで跳ね返されない():
    """じこさいせい: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこさいせい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    attacker.hp = 1
    defender_hp = defender.hp
    t.run_move(battle, 0)
    assert attacker.hp > 1
    assert defender.hp == defender_hp


def test_じこさいせい_まもるで防がれない():
    """じこさいせい: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこさいせい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp > 1


def test_じこさいせい_まんたんなら失敗():
    """じこさいせい: HPが最大値のときは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこさいせい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_じこさいせい_最大HPの半分回復する():
    """じこさいせい: 自分のHPを最大HPの1/2分回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこさいせい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + attacker.max_hp // 2


@pytest.mark.parametrize(
    "ability_name",
    ["プラス", "マイナス"]
)
def test_じばそうさ_プラスマイナス特性ならぼうぎょとくぼう1段階上昇(ability_name):
    """じばそうさ: プラス/マイナス特性の使用者はぼうぎょ・とくぼうランクがそれぞれ1段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じばそうさ"], ability_name=ability_name)],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 1
    assert attacker.rank["spd"] == 1


def test_じばそうさ_プラス以外の特性では失敗する():
    """じばそうさ: 使用者の特性がプラス/マイナスでない場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じばそうさ"], ability_name="せいでんき")],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 0
    assert attacker.rank["spd"] == 0


def test_じばそうさ_相手がちくでんでも無効化されない():
    """じばそうさ: 自分自身が対象の技のため、相手のちくでん等でんき技吸収特性に影響されず発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じばそうさ"], ability_name="プラス")],
        team1=[Pokemon("チョンチー", ability_name="ちくでん")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 1
    assert attacker.rank["spd"] == 1


def test_じばそうさ_相手がみがわり状態でも効果がある():
    """じばそうさ: 自分自身が対象の技のため、相手のみがわり状態に影響されず発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じばそうさ"], ability_name="プラス")],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["def"] == 1
    assert attacker.rank["spd"] == 1


def test_ジャングルヒール_HPが4分の1回復する():
    """ジャングルヒール: 最大HPの1/4を回復する(小数点以下切り捨て)"""
    battle = t.start_battle(
        team0=[Pokemon("ザルード", move_names=["ジャングルヒール"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 4)


def test_ジャングルヒール_HP満タンかつ無状態異常だと失敗する():
    """ジャングルヒール: HPが満タンかつ状態異常もない場合は技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ザルード", move_names=["ジャングルヒール"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    assert not attacker.ailment.is_active
    t.run_move(battle, 0)

    assert battle.move_executor.move_success is False


def test_ジャングルヒール_HP満タンでも状態異常があれば成功する():
    """ジャングルヒール: HPが満タンでも状態異常があれば技は成功し、状態異常のみ治す"""
    battle = t.start_battle(
        team0=[Pokemon("ザルード", move_names=["ジャングルヒール"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("まひ", None),
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    assert attacker.ailment.is_active
    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)

    assert battle.move_executor.move_success is True
    assert not attacker.ailment.is_active
    assert attacker.hp == attacker.max_hp


def test_ジャングルヒール_かいふくふうじ中は回復が無効化される():
    """ジャングルヒール: かいふくふうじ状態のとき回復が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ザルード", move_names=["ジャングルヒール"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"かいふくふうじ": 3},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1


def test_ジャングルヒール_マジックコートで跳ね返されない():
    """ジャングルヒール: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ザルード", move_names=["ジャングルヒール"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    attacker.hp = 1
    defender_hp = defender.hp
    t.run_move(battle, 0)

    assert attacker.hp > 1
    assert defender.hp == defender_hp


def test_ジャングルヒール_まもるで防がれない():
    """ジャングルヒール: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ザルード", move_names=["ジャングルヒール"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp > 1


@pytest.mark.parametrize("ailment_name", ["どく", "まひ", "やけど"])
def test_ジャングルヒール_状態異常を治す(ailment_name):
    """ジャングルヒール: 使用者の状態異常を治す"""
    battle = t.start_battle(
        team0=[Pokemon("ザルード", move_names=["ジャングルヒール"])],
        team1=[Pokemon("カビゴン")],
        ailment0=(ailment_name, None),
    )
    attacker = battle.actives[0]
    assert attacker.ailment.is_active
    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)

    assert not attacker.ailment.is_active


def test_じゅうでん_じゅうでん状態付与ととくぼう上昇():
    """じゅうでん: 自分にじゅうでん状態を付与し、とくぼうを1段階上げる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じゅうでん"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("じゅうでん")
    assert attacker.rank["spd"] == 1


def test_じゅうでん_とくぼうランク最大でも状態は付与される():
    """じゅうでん: とくぼうランクが最大でもじゅうでん状態は付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じゅうでん"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["spd"] = 6
    t.run_move(battle, 0)

    assert attacker.has_volatile("じゅうでん")
    assert attacker.rank["spd"] == 6


def test_じゅうりょく_PPは8():
    """じゅうりょく: チャンピオンズでのPPは8（docs/champions/move_list.txt準拠）。"""
    assert MOVES["じゅうりょく"].pp == 8


def test_じゅうりょく_すでに発動中なら失敗する():
    """じゅうりょく: すでに場が『じゅうりょく』状態のときは再使用しても失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じゅうりょく"])],
        team1=[Pokemon("カビゴン")],
        field={"じゅうりょく": 3},
    )
    t.run_move(battle, 0)
    field = battle.get_global_field("じゅうりょく")
    assert field.count == 3


def test_じゅうりょく_マジックコートで跳ね返されない():
    """じゅうりょく: 全体の場を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じゅうりょく"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    t.run_move(battle, 0)
    assert battle.get_global_field("じゅうりょく").is_active


def test_じゅうりょく_まもるで防がれない():
    """じゅうりょく: 全体の場を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じゅうりょく"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    t.run_move(battle, 0)
    assert battle.get_global_field("じゅうりょく").is_active


def test_じゅうりょく_場が発動する():
    """じゅうりょく: 使用すると場が『じゅうりょく』状態になり、5ターン継続する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じゅうりょく"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    field = battle.get_global_field("じゅうりょく")
    assert field.is_active
    assert field.count == 5


def test_じんつうりき_ひるみが発動する():
    """じんつうりき: 10%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["じんつうりき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


@pytest.mark.parametrize("a_ability,d_ability", [
    ("アイスフェイス", "めんえき"),   # 使用者の特性がprotected
    ("めんえき", "アイスフェイス"),   # 対象の特性がprotected
])
def test_スキルスワップ_protectedなら失敗(a_ability, d_ability):
    """スキルスワップ: 使用者または対象の特性がprotectedフラグを持つ場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スキルスワップ"], ability_name=a_ability)],
        team1=[Pokemon("カビゴン", ability_name=d_ability)],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 特性は入れ替わらない
    assert attacker.ability.name == a_ability
    assert defender.ability.name == d_ability


def test_スキルスワップ_いかく取得で相手のこうげきが下がる():
    """スキルスワップ: スキルスワップでいかくを取得すると再活性化し相手のこうげきが下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スキルスワップ"], ability_name="せいでんき")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # バトル開始時にいかくが発動してattackerのこうげきが-1されている
    assert attacker.rank["atk"] == -1
    assert defender.rank["atk"] == 0
    t.run_move(battle, 0)

    assert attacker.ability.name == "いかく"
    # スキルスワップでいかくを取得→再活性化→defenderのこうげきが-1
    assert defender.rank["atk"] == -1


def test_スキルスワップ_かたやぶり使用者でもprotected特性が相手にあれば失敗():
    """スキルスワップ: かたやぶりを持っていても対象の特性がprotectedなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スキルスワップ"], ability_name="かたやぶり")],
        team1=[Pokemon("カビゴン", ability_name="アイスフェイス")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 特性は入れ替わらない
    assert attacker.ability.name == "かたやぶり"
    assert defender.ability.name == "アイスフェイス"


def test_スキルスワップ_交代後に元の特性に戻る():
    """スキルスワップ: 特性を入れ替えられたポケモンが交代すると元の特性に戻る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スキルスワップ"], ability_name="せいでんき")],
        team1=[
            Pokemon("カビゴン", ability_name="めんえき"),
            Pokemon("ラッキー", ability_name="しぜんかいふく"),
        ],
        accuracy=100,
    )
    defender_before = battle.actives[1]
    t.run_move(battle, 0)
    assert defender_before.ability.name == "せいでんき"

    # 交代で元の特性に戻ることを確認
    t.run_switch(battle, 1, 1)
    assert defender_before.ability.name == "めんえき"


def test_スキルスワップ_同一特性どうしのスワップも成功する():
    """スキルスワップ: 第九世代では同一特性どうしのスワップも成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スキルスワップ"], ability_name="せいでんき")],
        team1=[Pokemon("カビゴン", ability_name="せいでんき")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 両者とも同じ特性のまま（入れ替えは成功している）
    assert attacker.ability.name == "せいでんき"
    assert defender.ability.name == "せいでんき"


def test_スキルスワップ_対象がみがわり状態でも成功する():
    """スキルスワップ: 対象がみがわり状態であっても特性の入れ替えは成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スキルスワップ"], ability_name="せいでんき")],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        volatile1={"みがわり": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert attacker.ability.name == "めんえき"
    assert defender.ability.name == "せいでんき"


def test_スキルスワップ_通常発動で特性が入れ替わる():
    """スキルスワップ: 通常の使用で使用者と対象の特性が入れ替わる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スキルスワップ"], ability_name="せいでんき")],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert attacker.ability.name == "めんえき"
    assert defender.ability.name == "せいでんき"


def test_すてゼリフ_クリアボディで完全阻止されたとき交代しない():
    """すてゼリフ: クリアボディで全ランク低下が阻止された場合は交代も発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["すてゼリフ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン", ability_name="クリアボディ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    player = battle.players[0]
    t.run_move(battle, 0)

    # ランク低下なし
    assert defender.rank["atk"] == 0
    assert defender.rank["spa"] == 0
    # 交代フラグも立たない
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_すてゼリフ_とらわれ状態でも交代できる():
    """すてゼリフ: にげられない状態でもとらわれを無視してPIVOTが設定される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["すてゼリフ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile0={"にげられない": 3},
        accuracy=100,
    )
    player = battle.players[0]
    t.run_move(battle, 0)

    # とらわれ状態でも交代が発動する
    assert battle.player_states[player].interrupt == Interrupt.PIVOT


def test_すてゼリフ_交代と同時にランク低下する():
    """すてゼリフ: 相手のこうげく・とくこうが1段階低下し、その後自分が交代する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["すてゼリフ"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    raichu = battle.player_states[battle.players[0]].team[1]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -1
    assert defender.rank["spa"] == -1
    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)
    assert battle.actives[0] is raichu


def test_すてゼリフ_控えがいない場合はランク低下のみ():
    """すてゼリフ: 控えポケモンがいない場合はランク低下のみ発生し交代は発生しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["すてゼリフ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    player = battle.players[0]
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -1
    assert defender.rank["spa"] == -1
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_すなあつめ_エアロックですなあらしが無効化されると半分回復になる():
    """すなあつめ: 場にエアロック持ちがいてすなあらしが無効化されている場合、回復量は1/2のまま"""
    battle = t.start_battle(
        team0=[Pokemon("シロデスナ", move_names=["すなあつめ"])],
        team1=[Pokemon("ボーマンダ", ability_name="エアロック")],
        weather=("すなあらし", 5),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 2)


def test_すなあつめ_すなあらしでは最大HPの2732_4096回復する():
    """すなあつめ: すなあらし状態では最大HPの2732/4096(≒2/3)回復する（五捨五超入で丸め）"""
    battle = t.start_battle(
        team0=[Pokemon("シロデスナ", move_names=["すなあつめ"])],
        team1=[Pokemon("カビゴン")],
        weather=("すなあらし", 5),
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + round_half_down(attacker.max_hp * 2732 / 4096)


@pytest.mark.parametrize("weather_arg", [
    ("はれ", 5),
    ("あめ", 5),
    ("ゆき", 5),
])
def test_すなあつめ_すなあらし以外の天候では回復量が下がらない(weather_arg):
    """すなあつめ: すなあらし以外の天候（はれ/あめ/ゆき）でも回復量は1/2のまま下がらない"""
    battle = t.start_battle(
        team0=[Pokemon("シロデスナ", move_names=["すなあつめ"])],
        team1=[Pokemon("カビゴン")],
        weather=weather_arg,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 2)


def test_すなあつめ_マジックコートで跳ね返されない():
    """すなあつめ: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("シロデスナ", move_names=["すなあつめ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    attacker.hp = 1
    defender_hp = defender.hp
    t.run_move(battle, 0)
    assert attacker.hp > 1
    assert defender.hp == defender_hp


def test_すなあつめ_まもるで防がれない():
    """すなあつめ: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("シロデスナ", move_names=["すなあつめ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp > 1


def test_すなあつめ_まんたんなら失敗():
    """すなあつめ: HPが最大値のときは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("シロデスナ", move_names=["すなあつめ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_すなあつめ_通常天候では最大HPの半分回復する():
    """すなあつめ: 通常天候では最大HPの1/2回復する"""
    battle = t.start_battle(
        team0=[Pokemon("シロデスナ", move_names=["すなあつめ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 2)


def test_すなあらし_天気がすなあらしになる():
    """すなあらし: 使用後に天気がすなあらしになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["すなあらし"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "すなあらし"
    assert battle.weather.count == 5


def test_すなかけ_まもるで防がれる():
    """すなかけ: まもるで効果が防がれ、命中率ランクが変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["すなかけ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        volatile1={"まもる": 1},
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["accuracy"] == 0


def test_すなかけ_相手の命中率が1段階下がる():
    """すなかけ: 相手の命中率ランクが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["すなかけ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["accuracy"] == -1


def test_スピードスワップ_すばやさ実数値が入れ替わる():
    """スピードスワップ: 使用者と相手のすばやさ実数値が入れ替わる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スピードスワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    a_spd_before = attacker.stats["spe"]
    d_spd_before = defender.stats["spe"]

    t.run_move(battle, 0)

    assert attacker.stats["spe"] == d_spd_before
    assert defender.stats["spe"] == a_spd_before


def test_スピードスワップ_ランク変化は行われない():
    """スピードスワップ: 実数値の入れ替えのみでランク変化は発生しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スピードスワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    t.run_move(battle, 0)

    assert attacker.rank["spe"] == 0
    assert defender.rank["spe"] == 0


def test_スピードスワップ_ランク変化後の実数値は入れ替わらない():
    """スピードスワップ: ランク変化はスワップされない（実数値のみ）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スピードスワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 攻撃者のすばやさランクを事前に上げておく
    attacker.rank["spe"] = 2
    a_spd_base = attacker.stats["spe"]
    d_spd_base = defender.stats["spe"]

    t.run_move(battle, 0)

    # 実数値（ランクなし）が入れ替わっている
    assert attacker.stats["spe"] == d_spd_base
    assert defender.stats["spe"] == a_spd_base
    # ランク変化はそのまま（スワップされていない）
    assert attacker.rank["spe"] == 2
    assert defender.rank["spe"] == 0


def test_スピードスワップ_双方すばやさ同値でも成功する():
    """スピードスワップ: 双方のすばやさが同値でも失敗せず成功する"""
    # 同じポケモン同士でも成功する（失敗しない）
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スピードスワップ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    a_spd_before = attacker.stats["spe"]
    d_spd_before = defender.stats["spe"]
    assert a_spd_before == d_spd_before

    t.run_move(battle, 0)

    # 値は同じだが技は失敗していない（実数値は変化なし）
    assert attacker.stats["spe"] == d_spd_before
    assert defender.stats["spe"] == a_spd_before


def test_すりかえ_こだわり系アイテムを入手してもロックされない():
    """すりかえ: 自身の効果でこだわり系アイテムを新たに入手しても、すりかえにロックされない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["すりかえ"], item_name="たべのこし")],
        team1=[Pokemon("カビゴン", item_name="こだわりハチマキ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.item.name == "こだわりハチマキ"
    assert not attacker.has_volatile("こだわり")


def test_すりかえ_マジックコートで跳ね返されない():
    """すりかえ: マジックコート・マジックミラーで跳ね返されない（トリックと同様の例外仕様）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["すりかえ"], item_name="たべのこし")],
        team1=[Pokemon("カビゴン", item_name="オボンのみ")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # 跳ね返されていれば MOVE_REFLECTED ログが記録される
    assert not any(log.log == LogCode.MOVE_REFLECTED for log in battle.event_logger.logs)
    assert attacker.item.name == "オボンのみ"
    assert defender.item.name == "たべのこし"


def test_すりかえ_両者がアイテムを持っていないとき失敗():
    """すりかえ: 両者ともアイテムを持っていない場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["すりかえ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not attacker.has_item()
    assert not defender.has_item()


def test_すりかえ_両者のアイテムが入れ替わる():
    """すりかえ: 使用者と相手のアイテムを入れ替える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["すりかえ"], item_name="たべのこし")],
        team1=[Pokemon("カビゴン", item_name="オボンのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert attacker.item.name == "オボンのみ"
    assert defender.item.name == "たべのこし"


def test_すりかえ_既にロックされていた場合も解除される():
    """すりかえ: 既にこだわりでロックされていた場合も、すりかえの使用でロックが解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["すりかえ"], item_name="こだわりスカーフ")],
        team1=[Pokemon("カビゴン", item_name="たべのこし")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "こだわり", source=attacker, move_name="すりかえ")
    assert attacker.has_volatile("こだわり")

    t.run_move(battle, 0)

    assert attacker.item.name == "たべのこし"
    assert not attacker.has_volatile("こだわり")


@pytest.mark.parametrize("a_item,d_item,expected_a,expected_d", [
    ("たべのこし", None, None, "たべのこし"),  # 使用者のみアイテム持ち
    (None, "オボンのみ", "オボンのみ", None),   # 相手のみアイテム持ち
])
def test_すりかえ_片方のみアイテムを持つとき入れ替わる(a_item, d_item, expected_a, expected_d):
    """すりかえ: 使用者または相手のみアイテムを持つ場合も入れ替えが成功する。"""
    a_kwargs = {"item_name": a_item} if a_item else {}
    d_kwargs = {"item_name": d_item} if d_item else {}
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["すりかえ"], **a_kwargs)],
        team1=[Pokemon("カビゴン", **d_kwargs)],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    if expected_a is None:
        assert not attacker.has_item()
    else:
        assert attacker.item.name == expected_a
    if expected_d is None:
        assert not defender.has_item()
    else:
        assert defender.item.name == expected_d


def test_ずつき_ひるみが発動する():
    """ずつき: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ずつき"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_せいちょう_たんじゅんで晴れ中4段階上がる():
    """せいちょう: 使用者がたんじゅんの場合、にほんばれ状態ではランク変化量が2倍の4段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="たんじゅん", move_names=["せいちょう"])],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 4
    assert attacker.rank["spa"] == 4


def test_せいちょう_ノーてんきで晴れでも1段階のみ():
    """せいちょう: 場にノーてんき持ちがいる場合、にほんばれ状態でも1段階のみ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["せいちょう"])],
        team1=[Pokemon("カビゴン", ability_name="ノーてんき")],
        weather=("はれ", 5),
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["spa"] == 1


@pytest.mark.parametrize("weather", ["はれ", "おおひでり"])
def test_せいちょう_はれ系天候でこうげきととくこう2段階上がる(weather):
    """せいちょう: はれ・おおひでり中はこうげきととくこうランクが2段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["せいちょう"])],
        team1=[Pokemon("カビゴン")],
        weather=(weather, 5),
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 2
    assert attacker.rank["spa"] == 2


def test_せいちょう_ばんのうがさで晴れでも1段階のみ():
    """せいちょう: 使用者がばんのうがさを持つ場合、にほんばれ状態でも1段階のみ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["せいちょう"], item_name="ばんのうがさ")],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["spa"] == 1


def test_せいちょう_マジックコートで跳ね返されない():
    """せいちょう: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["せいちょう"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["spa"] == 1


def test_せいちょう_まもるで防がれない():
    """せいちょう: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["せいちょう"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["spa"] == 1


def test_せいちょう_通常時こうげきととくこう1段階上がる():
    """せいちょう: 通常天候ではこうげきととくこうランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["せいちょう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["spa"] == 1


def test_そうでん_そのターン相手の技がでんきタイプに変換される():
    """そうでん: 命中した相手がそのターンに使う技がでんきタイプに変換される

    そうでん状態はターン終了時に解除されるため battle.step() 後に揮発状態を
    直接確認できない。そこで、じめんタイプ（でんきタイプ技を無効化）の
    ドサイドンをそうでん使用者にし、相手のたいあたり（ノーマル）がでんきタイプに
    変換されて無効化されることをHPの変化で確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ドサイドン", move_names=["そうでん"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker_hp = attacker.hp
    battle.step()

    assert attacker.hp == attacker_hp


def test_そうでん_マジックコートで跳ね返されない():
    """そうでん: 変化技だが例外的にマジックコートで跳ね返されない

    仮に跳ね返された場合、そうでんの使用者自身がそうでん状態になり
    相手のたいあたり（ノーマル）はでんきタイプに変換されずダメージを受ける。
    正しく跳ね返されなければ、使用者はじめんタイプのため、でんきタイプに
    変換された相手のたいあたりを無効化してダメージを受けない。
    """
    battle = t.start_battle(
        team0=[Pokemon("ドサイドン", move_names=["そうでん"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker_hp = attacker.hp
    battle.step()

    assert attacker.hp == attacker_hp


def test_そうでん_相手がすでに行動済みの場合は失敗する():
    """そうでん: 相手がそうでんより先に行動していた場合は失敗する

    ゲンガー（素早さ130）がでんこうせっか（優先度+1）を使い、
    ピカチュウ（素早さ90）がそうでんを使う場合、ゲンガーが先行するため
    ゲンガー行動後にそうでんを使うと失敗する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["そうでん"])],
        team1=[Pokemon("ゲンガー", move_names=["でんこうせっか"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.step()

    assert not defender.has_volatile("そうでん")


def test_ソウルビート_全能力1段階上がりHP3分の1消費():
    """ソウルビート: 使用すると全能力が1段階ずつ上がり最大HPの1/3が消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ソウルビート"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["def"] == 1
    assert attacker.rank["spa"] == 1
    assert attacker.rank["spd"] == 1
    assert attacker.rank["spe"] == 1
    assert attacker.hp == max_hp - (max_hp // 3)
