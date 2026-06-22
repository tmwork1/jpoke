"""変化技ハンドラの単体テスト（さ行・サ行）。"""

import pytest
from jpoke import Pokemon
from jpoke.enums import Interrupt
from .. import test_utils as t


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
    battle.run_interrupt_switch(Interrupt.PIVOT)

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
    battle.run_interrupt_switch(Interrupt.PIVOT)

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


def test_じこあんじ_相手のランクが全て0のとき自分のランクも全て0になる():
    """じこあんじ: 相手のランクが全て0のとき、自分のランクも全て0になること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこあんじ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # 使用者にランクをあらかじめ設定しておく
    attacker.rank["A"] = 3
    attacker.rank["B"] = -2
    attacker.rank["C"] = 1
    t.run_move(battle, 0)

    for stat in ("A", "B", "C", "D", "S", "ACC", "EVA"):
        assert attacker.rank[stat] == 0


def test_じこあんじ_相手のランクは変化しない():
    """じこあんじ: 使用後も相手のランクは変化しないこと"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこあんじ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.rank["A"] = 2
    defender.rank["C"] = -3
    t.run_move(battle, 0)

    assert defender.rank["A"] == 2
    assert defender.rank["C"] == -3


def test_じこあんじ_相手のランク変化を自分にコピーする():
    """じこあんじ: 相手の全ランク変化（A/B/C/D/S/ACC/EVA）を自分にコピーすること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じこあんじ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender.rank["A"] = 2
    defender.rank["B"] = -1
    defender.rank["C"] = 3
    defender.rank["D"] = -2
    defender.rank["S"] = 1
    defender.rank["ACC"] = -1
    defender.rank["EVA"] = 2
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 2
    assert attacker.rank["B"] == -1
    assert attacker.rank["C"] == 3
    assert attacker.rank["D"] == -2
    assert attacker.rank["S"] == 1
    assert attacker.rank["ACC"] == -1
    assert attacker.rank["EVA"] == 2


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

    assert attacker.rank["B"] == 1
    assert attacker.rank["D"] == 1


def test_じばそうさ_プラス以外の特性では失敗する():
    """じばそうさ: 使用者の特性がプラス/マイナスでない場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["じばそうさ"], ability_name="せいでんき")],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["B"] == 0
    assert attacker.rank["D"] == 0


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
    assert attacker.rank["A"] == -1
    assert defender.rank["A"] == 0
    t.run_move(battle, 0)

    assert attacker.ability.name == "いかく"
    # スキルスワップでいかくを取得→再活性化→defenderのこうげきが-1
    assert defender.rank["A"] == -1


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
    assert defender.rank["A"] == 0
    assert defender.rank["C"] == 0
    # 交代フラグも立たない
    assert battle.player_states[player].interrupt == Interrupt.NONE


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

    assert defender.rank["A"] == -1
    assert defender.rank["C"] == -1
    battle.run_interrupt_switch(Interrupt.PIVOT)
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

    assert defender.rank["A"] == -1
    assert defender.rank["C"] == -1
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_スピードスワップ_すばやさ実数値が入れ替わる():
    """スピードスワップ: 使用者と相手のすばやさ実数値が入れ替わる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スピードスワップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    a_spd_before = attacker.stats["S"]
    d_spd_before = defender.stats["S"]

    t.run_move(battle, 0)

    assert attacker.stats["S"] == d_spd_before
    assert defender.stats["S"] == a_spd_before


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

    assert attacker.rank["S"] == 0
    assert defender.rank["S"] == 0


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
    attacker.rank["S"] = 2
    a_spd_base = attacker.stats["S"]
    d_spd_base = defender.stats["S"]

    t.run_move(battle, 0)

    # 実数値（ランクなし）が入れ替わっている
    assert attacker.stats["S"] == d_spd_base
    assert defender.stats["S"] == a_spd_base
    # ランク変化はそのまま（スワップされていない）
    assert attacker.rank["S"] == 2
    assert defender.rank["S"] == 0


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
    a_spd_before = attacker.stats["S"]
    d_spd_before = defender.stats["S"]
    assert a_spd_before == d_spd_before

    t.run_move(battle, 0)

    # 値は同じだが技は失敗していない（実数値は変化なし）
    assert attacker.stats["S"] == d_spd_before
    assert defender.stats["S"] == a_spd_before


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

    assert attacker.rank["A"] == 2
    assert attacker.rank["C"] == 2


def test_せいちょう_通常時こうげきととくこう1段階上がる():
    """せいちょう: 通常天候ではこうげきととくこうランクが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["せいちょう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 1
    assert attacker.rank["C"] == 1


def test_そうでん_そうでん状態が相手に付与される():
    """そうでん: 使用すると相手にそうでん揮発状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["そうでん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("そうでん")


def test_ソウルビート_全能力1段階上がりHP3分の1消費():
    """ソウルビート: 使用すると全能力が1段階ずつ上がり最大HPの1/3が消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ソウルビート"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.rank["A"] == 1
    assert attacker.rank["B"] == 1
    assert attacker.rank["C"] == 1
    assert attacker.rank["D"] == 1
    assert attacker.rank["S"] == 1
    assert attacker.hp == max_hp - (max_hp // 3)
