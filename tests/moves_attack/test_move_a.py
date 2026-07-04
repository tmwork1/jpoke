"""攻撃技ハンドラの単体テスト（あ行）。"""

import pytest
from unittest.mock import MagicMock
from jpoke import Pokemon
from .. import test_utils as t


def test_3ぼんのや_ひるみが発動する():
    """3ぼんのや: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["3ぼんのや"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_3ぼんのや_ぼうぎょ低下が発動する():
    """3ぼんのや: 50%で相手のぼうぎょを1段階下げる（ひるみとは独立判定）。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["3ぼんのや"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["def"] == -1


def test_3ぼんのや_急所ランクが1():
    """3ぼんのや: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["3ぼんのや"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_3ぼんのや_急所ランクが1_乱数大で急所なし():
    """3ぼんのや: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["3ぼんのや"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


def test_アイアンヘッド_ひるみが発動する():
    """アイアンヘッド: 20%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["アイアンヘッド"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_アイアンローラー_フィールドありのとき命中してフィールドが解除される():
    """アイアンローラー: フィールドが存在するとき命中してダメージを与え、フィールドを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["アイアンローラー"])],
        team1=[Pokemon("カビゴン")],
        terrain=("エレキフィールド", 5),
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True
    assert defender.hp < hp_before
    assert not battle.terrain.is_active


def test_アイアンローラー_フィールドなしのとき失敗する():
    """アイアンローラー: フィールドが存在しない場合は失敗し、ダメージを与えない。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", move_names=["アイアンローラー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False
    assert defender.hp == hp_before


def test_アイススピナー_フィールドありのとき命中してフィールドが解除される():
    """アイススピナー: フィールドが存在するとき命中してダメージを与え、フィールドを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["アイススピナー"])],
        team1=[Pokemon("カビゴン")],
        terrain=("グラスフィールド", 5),
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True
    assert defender.hp < hp_before
    assert not battle.terrain.is_active


def test_アイススピナー_フィールドなしでも命中する():
    """アイススピナー: フィールドが存在しない場合でも使用でき、ダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["アイススピナー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True
    assert defender.hp < hp_before


def test_アクアカッター_急所ランクが1():
    """アクアカッター: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("サメハダー", move_names=["アクアカッター"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_アクアカッター_急所ランクが1_乱数大で急所なし():
    """アクアカッター: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("サメハダー", move_names=["アクアカッター"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


def test_アクアジェット_相手にダメージを与える():
    """アクアジェット: 優先度+1の先制物理技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ラプラス", move_names=["アクアジェット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_アクアテール_相手にダメージを与える():
    """アクアテール: 追加効果なしの物理みず技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["アクアテール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_アクセルブレイク_効果抜群のとき威力が4_3倍になる():
    """アクセルブレイク: 効果抜群（ノーマルに2倍）のとき威力が4/3倍（100→133）になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["アクセルブレイク"])],
        team1=[Pokemon("カビゴン")],   # ノーマル: かくとう2倍
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 133


def test_アクセルブレイク_等倍のとき威力倍率なし():
    """アクセルブレイク: 等倍（でんきに1倍）のときは威力補正なし（100のまま）。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["アクセルブレイク"])],
        team1=[Pokemon("ピカチュウ")],   # でんき: かくとう等倍
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 100


def test_アクセルロック_相手にダメージを与える():
    """アクセルロック: 優先度+1の先制物理技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ガマゲロゲ", move_names=["アクセルロック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_あくのはどう_ひるみが発動する():
    """あくのはどう: 20%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["あくのはどう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_アシストパワー_ランク上昇なしのとき基本威力20():
    """アシストパワー: ランク上昇がないとき基本威力20のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["アシストパワー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 20


def test_アシストパワー_ランク上昇合計1段階で威力40():
    """アシストパワー: A+1のとき威力が40（20 + 20*1）になる。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["アシストパワー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.modify_stats(attacker, {"atk": 1}, source=attacker)
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 40


def test_アシストパワー_ランク上昇合計3段階で威力80():
    """アシストパワー: A+2, B+1 の合計+3のとき威力が80（20 + 20*3）になる。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["アシストパワー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.modify_stats(attacker, {"atk": 2, "def": 1}, source=attacker)
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 80


def test_アシストパワー_ランク低下はカウントしない():
    """アシストパワー: A-1 があっても正の合計がゼロならば威力は20のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["アシストパワー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.modify_stats(attacker, {"atk": -1}, source=attacker)
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 20


def test_あなをほる_1ターン目は地中に潜りHPが変わらない():
    """あなをほる: 1ターン目はチャージ（あなをほる揮発状態）になり、相手へのダメージはない。"""
    battle = t.start_battle(
        team0=[Pokemon("ディグダ", move_names=["あなをほる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender_hp_before = defender.hp
    t.run_move(battle, 0)
    assert attacker.has_volatile("あなをほる")
    assert defender.hp == defender_hp_before


def test_あなをほる_2ターン目に攻撃して揮発状態が解除される():
    """あなをほる: 2ターン目に攻撃が発動し、揮発状態が解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("ディグダ", move_names=["あなをほる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 1ターン目: チャージ
    t.run_move(battle, 0)
    assert attacker.has_volatile("あなをほる")
    hp_before = defender.hp
    # 2ターン目: 攻撃
    t.run_move(battle, 0)
    assert not attacker.has_volatile("あなをほる")
    assert defender.hp < hp_before


def test_あなをほる_じしんは地中の相手に命中し威力が2倍になる():
    """あなをほる状態の相手にじしんを使うと命中し威力補正が2倍（8192）になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ディグダ", move_names=["じしん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "あなをほる", count=1)
    t.run_move(battle, 0)
    assert battle.move_executor.move_success
    assert battle.damage_calculator.power_modifier == 8192


def test_あなをほる_じしんマグニチュード以外は命中しない():
    """あなをほる状態の相手にじしん・マグニチュード以外の技は命中しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "あなをほる", count=1)
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


def test_あなをほる_チャージ中は一般技が命中しない():
    """あなをほる状態の相手に一般技は命中しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ディグダ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "あなをほる", count=1)
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success


@pytest.mark.skip(reason="マグニチュードは未実装")
def test_あなをほる_マグニチュードは地中の相手に命中し威力が2倍になる():
    """あなをほる状態の相手にマグニチュードを使うと命中し威力補正が2倍（8192）になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ディグダ", move_names=["マグニチュード"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "あなをほる", count=1)
    t.run_move(battle, 0)
    assert battle.move_executor.move_success
    assert battle.damage_calculator.power_modifier == 8192


def test_あばれる_あばれる状態中はON_HITで揮発状態を再付与しない():
    """あばれる: あばれる揮発状態がある場合ON_HITで再付与を試みない（countが2のまま維持される）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["あばれる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # 事前にcount=2の揮発状態を付与
    battle.volatile_manager.apply(attacker, "あばれる", count=2, source=attacker, move_name="あばれる")
    assert attacker.volatiles["あばれる"].count == 2
    # あばれるを使う（ON_HITで再付与を試みるが、has_volatileチェックで弾かれる）
    t.run_move(battle, 0)
    # countが1に減っているだけで、2ターン分減ったりしていない
    if attacker.has_volatile("あばれる"):
        assert attacker.volatiles["あばれる"].count == 1
    else:
        # count=1だったのでON_DAMAGE_HITでtickしてcountが0になりこんらんが付与された
        assert attacker.has_volatile("こんらん")


def test_あばれる_カウント終了後にこんらんが付与される():
    """あばれる: カウントが0になった後にこんらん状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["あばれる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # countを1に設定して次の命中でカウント終了させる
    battle.volatile_manager.apply(attacker, "あばれる", count=1, source=attacker, move_name="あばれる")
    t.run_move(battle, 0)
    # あばれる揮発状態が解除されてこんらんが付与されている
    assert not attacker.has_volatile("あばれる")
    assert attacker.has_volatile("こんらん")


def test_あばれる_初回命中時にあばれる揮発状態が付与される():
    """あばれる: 初回命中時にあばれる揮発状態（強制行動）が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["あばれる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("あばれる")


def test_アフロブレイク_使用後に攻撃者が反動ダメージを受ける():
    """アフロブレイク: 与えたダメージの1/4を攻撃者が反動として受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["アフロブレイク"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_アフロブレイク_反動ダメージが与ダメの4分の1になる():
    """アフロブレイク: 反動量は max(1, int(与ダメ * 1/4)) で計算される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["アフロブレイク"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_damage(battle, 100)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    # max(1, int(100 * 1/4)) = 25
    assert attacker.hp == hp_before - 25


def test_あやしいかぜ_全能力1段階上昇が発動する():
    """あやしいかぜ: 確率10%の副作用でA/B/C/D/Sが各1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["あやしいかぜ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        secondary_chance=1.0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["atk"] == 1
    assert attacker.rank["def"] == 1
    assert attacker.rank["spa"] == 1
    assert attacker.rank["spd"] == 1
    assert attacker.rank["spe"] == 1


def test_いかりのまえば_最低1ダメージ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いかりのまえば"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.hp == 0


@pytest.mark.parametrize(
    ("defender_hp", "expected_damage"),
    [
        (100, 50),
        (101, 50),
    ],
)
def test_いかりのまえば_相手HP半分のダメージ(defender_hp: int, expected_damage: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いかりのまえば"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender.hp = defender_hp
    t.run_move(battle, 0)
    assert defender.hp == defender_hp - expected_damage


def test_いじげんホール_まもる状態の相手にダメージを与える():
    """いじげんホール: unprotectableフラグを持つため、まもる状態の相手を貫通してダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["いじげんホール"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_いじげんホール_みがわり状態の相手の本体にダメージを与える():
    """いじげんホール: bypass_substituteフラグを持つため、みがわり状態の相手の本体にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["いじげんホール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    # みがわりにHPを設定（貫通しなければこのHPが削られる）
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)
    # bypass_substitute技はみがわりを無視して本体にダメージを与えるため、本体HPが減る
    assert defender.hp < hp_before
    # みがわりのHPは変化しない
    assert defender.volatiles["みがわり"].hp == 999


def test_いじげんラッシュ_防御1段階低下が発動する():
    """いじげんラッシュ: 命中時に使用者のBが1段階低下する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("イーブイ", move_names=["いじげんラッシュ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["def"] == -1


def test_いてつくしせん_こおりが発動する():
    """いてつくしせん: 10%でこおりを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["いてつくしせん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "こおり"


def test_イナズマドライブ_効果抜群のとき威力が4_3倍になる():
    """イナズマドライブ: 効果抜群（みずに2倍）のとき威力が4/3倍（100→133）になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ジバコイル", move_names=["イナズマドライブ"])],
        team1=[Pokemon("カメックス")],   # みず: でんき2倍
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 133


def test_イナズマドライブ_等倍のとき威力倍率なし():
    """イナズマドライブ: 等倍（ノーマルに1倍）のときは威力補正なし（100のまま）。"""
    battle = t.start_battle(
        team0=[Pokemon("ジバコイル", move_names=["イナズマドライブ"])],
        team1=[Pokemon("カビゴン")],   # ノーマル: でんき等倍
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 100


def test_いにしえのうた_ねむりが発動しない():
    """いにしえのうた: 追加効果不発時はねむり状態にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いにしえのうた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_いにしえのうた_ねむりが発動する():
    """いにしえのうた: 10%の確率で相手をねむり状態にする。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いにしえのうた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "ねむり"


def test_いのちがけ_与ダメージは現在HPで使用者はひんし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いのちがけ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.hp = 40
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp - 40
    assert attacker.hp == 0


def test_いびき_ひるみが発動する():
    """いびき: 30%でひるみを付与する。ねむり状態でないと使えない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いびき"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("ねむり", 3),
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_いわなだれ_ひるみが発動する():
    """いわなだれ: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("イワーク", move_names=["いわなだれ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ウェザーボール_ばんのうがさ持ちははれでもノーマルタイプのまま():
    """ウェザーボール: 使用者がばんのうがさを持つ場合、はれ中でもノーマルタイプのまま。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ばんのうがさ", move_names=["ウェザーボール"])],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "ノーマル"


def test_ウェザーボール_天候なし時ノーマルタイプになる():
    """ウェザーボール: 天候がないとき、ノーマルタイプのまま。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ウェザーボール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "ノーマル"


@pytest.mark.parametrize("weather_name, expected_type", [
    ("はれ", "ほのお"),
    ("おおひでり", "ほのお"),
    ("あめ", "みず"),
    ("おおあめ", "みず"),
    ("すなあらし", "いわ"),
    ("ゆき", "こおり"),
])
def test_ウェザーボール_天候に応じてタイプが変化する(weather_name: str, expected_type: str):
    """ウェザーボール: 天候が有効なとき、天候に対応するタイプに変化する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ウェザーボール"])],
        team1=[Pokemon("カビゴン")],
        weather=(weather_name, 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == expected_type


def test_ウェザーボール_天候時威力が2倍になる():
    """ウェザーボール: 天候が有効なとき威力が2倍（50→100）になる。"""
    # 天候なし: ノーマルタイプ・威力50
    battle_no = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ウェザーボール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender_no = battle_no.actives[1]
    hp_before_no = defender_no.hp
    t.fix_random(battle_no, 0.0)
    t.run_move(battle_no, 0)
    damage_no = hp_before_no - defender_no.hp

    # すなあらし: いわタイプ・威力100（ノーマルへの等倍）
    battle_yes = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ウェザーボール"])],
        team1=[Pokemon("カビゴン")],
        weather=("すなあらし", 5),
        accuracy=100,
    )
    defender_yes = battle_yes.actives[1]
    hp_before_yes = defender_yes.hp
    t.fix_random(battle_yes, 0.0)
    t.run_move(battle_yes, 0)
    damage_yes = hp_before_yes - defender_yes.hp

    assert damage_yes > damage_no


def test_ウェーブタックル_使用後に攻撃者が反動ダメージを受ける():
    """ウェーブタックル: 与えたダメージの1/3を攻撃者が反動として受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ウェーブタックル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_うたかたのアリア_まひ状態の相手には影響しない():
    """うたかたのアリア: まひ状態の相手に使っても、まひは治らない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["うたかたのアリア"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("まひ", None),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_うたかたのアリア_やけど状態の相手のやけどが治る():
    """うたかたのアリア: 命中時に防御側のやけどを治す。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["うたかたのアリア"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("やけど", None),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_うちおとす_ひこうタイプの浮遊が無効化される():
    """うちおとす: 命中後にひこうタイプの相手の浮遊状態が無効化される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["うちおとす"])],
        team1=[Pokemon("ポッポ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert battle.query.is_floating(defender)
    t.run_move(battle, 0)
    assert not battle.query.is_floating(defender)


def test_うちおとす_命中後に揮発状態が付与される():
    """うちおとす: 命中時に相手に "うちおとす" 揮発性状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["うちおとす"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("うちおとす")


def test_ウッドハンマー_使用後に攻撃者が反動ダメージを受ける():
    """ウッドハンマー: 与えたダメージの1/3を攻撃者が反動として受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ウッドハンマー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_ウッドホーン_使用後に攻撃者のHPが回復する():
    """ウッドホーン: 与えたダメージの半分だけ攻撃者のHPを回復する（heal_ratio=0.5）。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["ウッドホーン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp > hp_before


def test_ウッドホーン_回復量が与ダメの半分になる():
    """ウッドホーン: 回復量は int(与えたダメージ * 0.5) で計算される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ウッドホーン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_damage(battle, 100)
    attacker.hp = 1
    t.run_move(battle, 0)
    # int(100 * 0.5) = 50
    assert attacker.hp == 1 + 50


def test_うっぷんばらし_ランクが下がったとき威力2倍():
    """うっぷんばらし: そのターン中にランクが下げられていたとき威力2倍。"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["うっぷんばらし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # ターン内でランクを下げる
    attacker.stat_lowered_this_turn = True
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_うっぷんばらし_ランクが下がっていないとき通常威力():
    """うっぷんばらし: ランクが下がっていないとき威力補正なし。"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["うっぷんばらし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_うらみつらみ_こうげき1段階低下が発動する():
    """うらみつらみ: 100%の確率で相手のこうげきを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["うらみつらみ"])],
        team1=[Pokemon("フーディン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["atk"] == -1


def test_エアカッター_急所ランクが1():
    """エアカッター: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("ファイヤー", move_names=["エアカッター"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_エアカッター_急所ランクが1_乱数大で急所なし():
    """エアカッター: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("ファイヤー", move_names=["エアカッター"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


def test_エアスラッシュ_ひるみが発動する():
    """エアスラッシュ: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ファイヤー", move_names=["エアスラッシュ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_エレキボール_比率0のとき威力40():
    """エレキボール: 攻撃者S // 防御者S が 0 のとき威力40。
    カビゴン(S=50) vs ピカチュウ(S=110) → 比率0 → 威力40。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["エレキボール"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 40


def test_エレキボール_比率1のとき威力60():
    """エレキボール: 攻撃者S // 防御者S が 1 のとき威力60。
    ピカチュウ(S=110) vs ピカチュウ(S=110) → 比率1 → 威力60。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["エレキボール"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 60


def test_エレキボール_比率2のとき威力80():
    """エレキボール: 攻撃者S // 防御者S が 2 のとき威力80。
    ピカチュウ(S=110) vs カビゴン(S=50) → 比率2 → 威力80。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["エレキボール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 80


def test_エレキボール_比率3のとき威力120():
    """エレキボール: 攻撃者S // 防御者S が 3 のとき威力120。
    ライコウ(S=135) vs ヤドン(S=35) → 比率3 → 威力120。
    """
    battle = t.start_battle(
        team0=[Pokemon("ライコウ", move_names=["エレキボール"])],
        team1=[Pokemon("ヤドン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 120


def test_エレキボール_比率4以上のとき威力150():
    """エレキボール: 攻撃者S // 防御者S が 4 以上のとき威力150。
    ジュカイン(S=140) vs ヤドン(S=35) → 比率4 → 威力150。
    """
    battle = t.start_battle(
        team0=[Pokemon("ジュカイン", move_names=["エレキボール"])],
        team1=[Pokemon("ヤドン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 150


def test_エレクトロビーム_1ターン目にとくこうが上昇する():
    """エレクトロビーム: 1ターン目にとくこうが1段階上昇する（追加効果ではないため必ず発動）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["エレクトロビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]

    # 1ターン目: とくこう+1、ダメージなし
    t.run_move(battle, 0)
    assert attacker.rank["spa"] == 1


def test_エレクトロビーム_2ターンで攻撃する():
    """エレクトロビーム: 1ターン目はダメージなしで揮発状態を付与し、2ターン目にダメージを与えて揮発状態を解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["エレクトロビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp

    # 1ターン目: 揮発状態付与のみ、ダメージなし
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert attacker.has_volatile("エレクトロビーム")

    # 2ターン目: ダメージあり、揮発状態解除
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert not attacker.has_volatile("エレクトロビーム")


def test_エレクトロビーム_あめとパワフルハーブ両方所持時は天候優先で消費されない():
    """エレクトロビーム: あめによる溜めスキップがパワフルハーブの消費より優先される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="パワフルハーブ", move_names=["エレクトロビーム"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp

    # あめによるスキップで1ターンで攻撃するが、パワフルハーブは消費されない
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert attacker.has_item()
    assert attacker.rank["spa"] == 1


def test_エレクトロビーム_あめ時1ターンで攻撃してとくこうが上昇する():
    """エレクトロビーム+あめ: 天気があめのとき溜めをスキップして1ターンで攻撃する。とくこうも+1される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["エレクトロビーム"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp

    # 1ターンで攻撃（あめによるスキップ）
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert not attacker.has_volatile("エレクトロビーム")
    assert attacker.rank["spa"] == 1


def test_エレクトロビーム_ばんのうがさ持ちはあめでも2ターンかかる():
    """エレクトロビーム: 使用者がばんのうがさを持つ場合、あめでも溜めをスキップしない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ばんのうがさ", move_names=["エレクトロビーム"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp

    # 1ターン目: ばんのうがさによりあめの恩恵を受けず、揮発状態を付与してダメージなし
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert attacker.has_volatile("エレクトロビーム")

    # 2ターン目: ダメージあり
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_エレクトロビーム_パワフルハーブ使用時1ターンで攻撃してとくこうが上昇する():
    """エレクトロビーム+パワフルハーブ: 1ターンで攻撃できる。とくこうも+1される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="パワフルハーブ", move_names=["エレクトロビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp

    # 1ターンで攻撃（パワフルハーブ消費）
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert not attacker.has_item()
    assert attacker.rank["spa"] == 1


def test_オクタンほう_命中率1段階低下が発動する():
    """オクタンほう: 50%の確率で相手の命中率を1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("オクタン", move_names=["オクタンほう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["accuracy"] == -1


def test_おしゃべり_こんらんが発動する():
    """おしゃべり: 100%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("プリン", move_names=["おしゃべり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_おどろかす_ひるみが発動する():
    """おどろかす: 30%でひるみを付与する。ゴーストタイプのため非ノーマル・非エスパーに有効。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["おどろかす"])],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_おはかまいり_味方ひんし0のとき威力50():
    """おはかまいり: 味方にひんしがいないとき基本威力50。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["おはかまいり"]), Pokemon("カビゴン")],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 50


def test_おはかまいり_味方ひんし1のとき威力100():
    """おはかまいり: 味方1体がひんしのとき威力100（50 × 2）。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["おはかまいり"]), Pokemon("カビゴン"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
    )
    player0 = battle.players[0]
    bench = battle.player_states[player0].bench
    bench[0].hp = 0  # カビゴンをひんし状態にする
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 100


def test_おはかまいり_味方ひんし2のとき威力150():
    """おはかまいり: 味方2体がひんしのとき威力150（50 × 3）。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["おはかまいり"]), Pokemon("カビゴン"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
    )
    player0 = battle.players[0]
    bench = battle.player_states[player0].bench
    bench[0].hp = 0  # カビゴンをひんし状態にする
    bench[1].hp = 0  # ピカチュウをひんし状態にする
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 150


def test_オーラウイング_素早さ1段階上昇が発動する():
    """オーラウイング: 命中時に使用者のSが1段階上昇する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ジバコイル", move_names=["オーラウイング"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["spe"] == 1
