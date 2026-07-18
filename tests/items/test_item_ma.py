"""アイテムハンドラの単体テスト"""
import pytest
from jpoke import Pokemon
from .. import test_utils as t


def test_マゴのみ_HP満タンでもおちゃかいで強制発動しこんらんする():
    """マゴのみ: HPが満タンでおちゃかいにより強制消費された場合、回復量が0でも
    嫌いな味の性格ならこんらんが付与される（回復量とこんらん判定は独立。
    fuzz_logのseed=2777で検出されたバグの回帰テスト）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おちゃかい"], item_name="マゴのみ", nature="なまいき")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    assert mon.hp == mon.max_hp
    t.run_move(battle, 0)
    assert mon.hp == mon.max_hp
    assert not mon.has_item()
    assert mon.has_volatile("こんらん")


def test_マゴのみ_HP満タン未満の強制発動では回復とこんらんの両方が機能する():
    """マゴのみ: HPが満タン未満（かつ通常のHP閾値は満たさない）状態でおちゃかいにより
    強制消費された場合、従来通り回復とこんらん付与の両方が発生する（回帰確認）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おちゃかい"], item_name="マゴのみ", nature="なまいき")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    hp_before = mon.max_hp - 1
    mon.hp = hp_before
    t.run_move(battle, 0)
    # 回復量は最大HPの1/3だが、満タンを超える分は切り詰められる
    assert mon.hp == min(mon.max_hp, hp_before + mon.max_hp // 3)
    assert mon.hp > hp_before
    assert not mon.has_item()
    assert mon.has_volatile("こんらん")


def test_マゴのみ_それ以外の性格ではこんらんしない():
    """マゴのみ: あまい味が嫌いでない性格では発動してもこんらんしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="マゴのみ", nature="まじめ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()
    assert not mon.has_volatile("こんらん")


@pytest.mark.parametrize(
    "nature",
    ["ゆうかん", "れいせい", "のんき", "なまいき"]
)
def test_マゴのみ_はやさが上がりにくい性格でこんらんする(nature):
    """マゴのみ: あまい味が嫌いな性格（はやさが上がりにくい）は発動と同時にこんらんする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="マゴのみ", nature=nature)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()
    assert mon.has_volatile("こんらん")


def test_ミクルのみ_HP25以下でなければフラグが立たない():
    """HP が 25% より多い状態で減っただけではフラグは立たない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ミクルのみ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    battle.modify_hp(mon, v=-1)
    assert mon.item.count == 0
    assert mon.has_item()


def test_ミクルのみ_HP25以下でフラグが立つ():
    """HP が 25% 超から 25% 以下に下がった瞬間にフラグが立ちアイテムが revealed になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ミクルのみ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.item.count == 1
    assert mon.item.revealed is True
    assert mon.has_item()  # 消費は次の技使用時


def test_ミクルのみ_こんらんの自傷では発動しない():
    """ミクルのみ: こんらんの自傷ダメージ(reason=self_attack)でHPが1/4以下になっても
    フラグが立たない（第五世代以降の仕様）。その後、自傷以外のダメージで改めて1/4以下に
    なるとフラグが立つ。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ミクルのみ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1, reason="self_attack")
    assert mon.item.count == 0
    assert mon.has_item(), "こんらんの自傷ダメージでアイテムが消費された"

    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.item.count == 1


def test_ミクルのみ_一撃必殺技には倍率が適用されないが消費される():
    """ミクルのみ: 一撃必殺技には命中率倍率が適用されないが、効果自体は消費される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ミクルのみ", move_names=["じわれ"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy
    assert not mon.has_item()


def test_ミクルのみ_命中判定のない変化技を使うと消費される():
    """ミクルのみ: 命中率がNone(必中)の変化技を使った場合、ON_MODIFY_ACCURACYが
    発火しないため通常は消費判定が行われないが、行動完了時に効果が消費される。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ミクルのみ", move_names=["つるぎのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.item.count == 1
    t.run_move(battle, 0)
    assert not mon.has_item()


def test_ミクルのみ_技が外れても消費される():
    """ミクルのみ: 技が外れた場合でも効果は消費される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ミクルのみ", move_names=["ハイドロポンプ"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    t.fix_random(battle, 0.97)  # 補正後命中率95に対し97で外れる
    t.run_move(battle, 0)
    assert battle.move_executor.move_missed
    assert not mon.has_item()


def test_ミクルのみ_次の技の命中率が1_2倍になり消費される():
    """ミクルのみ: フラグが立った状態で技を使うと命中率が1.2倍になり消費される。
    2回目の技では通常の命中率に戻ることも合わせて確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ミクルのみ", move_names=["ハイドロポンプ"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.item.count == 1

    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy * 4915 // 4096
    assert not mon.has_item()

    # 消費済みのため2回目の技では通常の命中率に戻る
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


def test_ミクルのみ_瀕死になったときはフラグが立たない():
    """ミクルのみ: ダメージでHPが0(ひんし)になったときはフラグが立たず消費もされない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ミクルのみ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.hp = 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == 0
    assert mon.fainted
    assert mon.item.count == 0
    assert mon.has_item()


def test_ミクルのみ_行動不能のときは効果が持続する():
    """ミクルのみ: ねむり等で行動できなかった場合、効果は消費されず持続する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ミクルのみ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.item.count == 1
    t.apply_ailment(battle, player_idx=0, ailment_name="ねむり", count=3)
    t.run_move(battle, 0)
    assert mon.item.count == 1
    assert mon.has_item()


def test_メトロノーム_タイプ相性で無効化されるとリセット():
    """メトロノーム: タイプ相性により無効化された場合カウントは0にリセットされる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.item.count = 3
    mon.item.move_name = "たいあたり"
    t.run_move(battle, 0)
    assert mon.item.count == 0


def test_メトロノーム_ねむり中は行動できずカウント維持():
    """メトロノーム: ねむりなどで技が出せなかったときはカウントを維持する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.item.count = 3
    mon.item.move_name = "たいあたり"
    t.apply_ailment(battle, player_idx=0, ailment_name="ねむり", count=3)
    t.run_move(battle, 0)
    assert mon.item.count == 3
    assert mon.item.move_name == "たいあたり"


def test_メトロノーム_まもるで防がれるとリセット():
    """メトロノーム: まもるで防がれた場合カウントは0にリセットされる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.item.count = 3
    mon.item.move_name = "たいあたり"
    t.run_move(battle, 0)
    assert mon.item.count == 0


def test_メトロノーム_ミスするとリセット():
    """メトロノーム: 技が命中しなかった場合カウントは0にリセットされる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    mon = battle.actives[0]
    mon.item.count = 3
    mon.item.move_name = "たいあたり"
    t.run_move(battle, 0)
    assert mon.item.count == 0


def test_メトロノーム_別技でリセット():
    """メトロノーム: 違う技を使うとカウントリセット"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり", "でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.item.count = 3
    mon.item.move_name = "たいあたり"
    t.run_move(battle, 0, 1)
    assert mon.item.count == 1
    assert mon.item.move_name == "でんきショック"


@pytest.mark.parametrize("uses,expected_modifier", [
    (1, 4096),  # 初回は補正なし
    (2, 4915),  # 2回目: 1.2倍
    (3, 5734),  # 3回目: 1.4倍
    (6, 8191),  # 6回目: 2倍（上限）
    (7, 8191),  # 7回目以降: 上限変わらず
])
def test_メトロノーム_連続使用_補正係数(uses, expected_modifier):
    """メトロノーム: 連続使用回数に応じた補正係数"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メトロノーム", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    for _ in range(uses):
        t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == expected_modifier


def test_メンタルハーブ_いちゃもんを即解除():
    """メンタルハーブ: いちゃもん付与時に即解除する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メンタルハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "いちゃもん", source=battle.actives[1])
    assert not mon.has_volatile("いちゃもん")
    assert not mon.has_item()


@pytest.mark.parametrize("volatile_name, kwargs", [
    ("メロメロ", {}),
    ("アンコール", {"move_name": "たいあたり"}),
    ("かなしばり", {"move_name": "たいあたり"}),
    ("ちょうはつ", {}),
    ("かいふくふうじ", {}),
])
def test_メンタルハーブ_対象の揮発状態を即解除(volatile_name, kwargs):
    """メンタルハーブ: メロメロ・アンコール・かなしばり・ちょうはつ・かいふくふうじ付与時に即解除する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メンタルハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, volatile_name, source=battle.actives[1], **kwargs)
    assert not mon.has_volatile(volatile_name)
    assert not mon.has_item()


def test_メンタルハーブ_対象外の揮発状態には反応しない():
    """メンタルハーブ: 対象外の揮発状態（こんらん等）では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="メンタルハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "こんらん", source=battle.actives[1])
    assert mon.has_volatile("こんらん")
    assert mon.has_item()


def test_ものしりメガネ_物理技には補正なし():
    """ものしりメガネ: 物理技には補正しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ものしりメガネ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ものしりメガネ_特殊技1_1倍():
    """ものしりメガネ: 特殊技の威力を1.1倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ものしりメガネ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4505


def test_ものまねハーブ_びんじょうでの上昇はコピーしない():
    """ものまねハーブ: 相手のびんじょうによるコピーで上がった分は再度コピーしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ものまねハーブ")],
        team1=[Pokemon("ピカチュウ", ability_name="びんじょう")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    # mon自身がランクを上げる → foeのびんじょうが発動してfoeも+2上がるが、
    # そのびんじょうによる上昇をmonのものまねハーブが再度コピーしてはいけない
    battle.modify_stats(mon, {"atk": +2})
    assert mon.boosts["atk"] == 2
    assert foe.boosts["atk"] == 2
    assert mon.has_item()


def test_ものまねハーブ_びんじょうで最大まで上がったときは発動しない():
    """ものまねハーブ: びんじょうによるコピーで既に最大まで上がった場合はものまねハーブは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="びんじょう", item_name="ものまねハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    mon.boosts["atk"] = 5
    battle.modify_stats(foe, {"atk": +2})
    assert mon.boosts["atk"] == 6
    assert mon.has_item()


def test_ものまねハーブ_びんじょう所持者は2回上昇する():
    """ものまねハーブ: 特性がびんじょうである場合、びんじょうの後にものまねハーブも発動して2回上昇する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="びんじょう", item_name="ものまねハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    battle.modify_stats(foe, {"atk": +1})
    assert mon.boosts["atk"] == 2
    assert not mon.has_item()


def test_ものまねハーブ_ランクが最大のとき発動しない():
    """ものまねハーブ: 自分のランクが既に最大のときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ものまねハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    mon.boosts["atk"] = 6
    battle.modify_stats(foe, {"atk": +2})
    assert mon.boosts["atk"] == 6
    assert mon.has_item()


def test_ものまねハーブ_相手のランク上昇をコピー():
    """ものまねハーブ: 相手のランク上昇をそのままコピーする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ものまねハーブ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    battle.modify_stats(foe, {"atk": +2})
    assert mon.boosts["atk"] == 2
    assert not mon.has_item()


def test_モモンのみ_どく付与直後に即時回復する():
    """モモンのみ: どく付与直後（ON_APPLY_AILMENT）にターン終了を待たず即座に回復し消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どくガス"])],
        team1=[Pokemon("カビゴン", item_name="モモンのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not defender.ailment.is_active
    assert not defender.has_item()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
