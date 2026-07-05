"""攻撃技ハンドラの単体テスト（さ行）。"""

import pytest
from jpoke import Pokemon
from .. import test_utils as t


def test_10まんばりき_相手にダメージを与える():
    """10まんばりき: 追加効果なしの物理じめん技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["10まんばりき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_10まんボルト_まひが発動しない():
    """10まんボルト: secondary_chanceが0のときまひを付与しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_10まんボルト_まひが発動する():
    """10まんボルト: 10%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_Gのちから_じゅうりょくなしでは通常威力():
    """Gのちから: じゅうりょくがない場合は威力補正が1.0倍（4096）のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["Gのちから"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_Gのちから_ぼうぎょ1段階低下が発動する():
    """Gのちから: 100%の確率で相手のぼうぎょを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["Gのちから"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["def"] == -1


def test_サイケこうせん_こんらんが発動する():
    """サイケこうせん: 10%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["サイケこうせん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_サイコファング_まもるで防がれたとき壁を解除しない():
    """サイコファング: まもるで無効化された場合はリフレクターを解除しない。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["サイコファング"])],
        team1=[Pokemon("カビゴン")],
        side1={"リフレクター": 1},
        volatile1={"まもる": 1},
        accuracy=100,
    )
    assert battle.side_managers[1].fields["リフレクター"].is_active
    t.run_move(battle, 0)
    assert battle.side_managers[1].fields["リフレクター"].is_active


def test_サイコファング_リフレクターを解除する():
    """サイコファング: 命中時に相手側のリフレクターを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["サイコファング"])],
        team1=[Pokemon("カビゴン")],
        side1={"リフレクター": 1},
        accuracy=100,
    )
    assert battle.side_managers[1].fields["リフレクター"].is_active
    t.run_move(battle, 0)
    assert not battle.side_managers[1].fields["リフレクター"].is_active


def test_さばきのつぶて_せいれいプレートでフェアリータイプになる():
    """さばきのつぶて: せいれいプレートを持っているとき技のタイプがフェアリーになる。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", item_name="せいれいプレート", move_names=["さばきのつぶて"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "フェアリー"


def test_さばきのつぶて_プレートなしはノーマルタイプのまま():
    """さばきのつぶて: プレートを持っていないとき技のタイプはノーマルのまま。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", move_names=["さばきのつぶて"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "ノーマル"


def test_さばきのつぶて_マジックルーム中はプレートを持っていてもノーマルタイプになる():
    """さばきのつぶて: マジックルーム状態でアイテムが無効化されている間はノーマルタイプになる。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", item_name="せいれいプレート", move_names=["さばきのつぶて"])],
        team1=[Pokemon("カビゴン")],
        field={"マジックルーム": 5},
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "ノーマル"


def test_さわぐ_命中したときさわぐ揮発性状態を付与する():
    """さわぐ: 命中したときは使用者にさわぐ揮発性状態（count=3）を付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さわぐ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("さわぐ")
    assert attacker.volatiles["さわぐ"].count == 3


def test_さわぐ_外れたときさわぐ状態を付与しない():
    """さわぐ: 命中しなかったときはさわぐ揮発性状態を付与しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さわぐ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_volatile("さわぐ")


def test_サンダーダイブ_命中時は失敗反動ダメージを受けない():
    """サンダーダイブ: 命中したときはON_MISSが発火しないため失敗反動はない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["サンダーダイブ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    # 命中時は使用者のHPは変わらない（反動なし）
    assert attacker.hp == hp_before


def test_サンダーダイブ_外れたとき失敗反動ダメージを受ける():
    """サンダーダイブ: 外れたとき自分の最大HPの1/2ダメージを受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["サンダーダイブ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    expected_damage = max(1, attacker.max_hp // 2)
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_damage


def test_サンダーダイブ_外れて残HPが半分未満でもひんしになる():
    """サンダーダイブ: 残HPが失敗反動ダメージ未満でもひんし処理が行われる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["サンダーダイブ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    # 残HPを1にしてから外す → 失敗反動でひんしになる
    battle.modify_hp(attacker, v=-(attacker.hp - 1), reason="self_cost", source=attacker)
    assert attacker.hp == 1
    t.run_move(battle, 0)
    assert not attacker.alive


@pytest.mark.parametrize(("attacker_name", "expected"), [
    ("カイリキー", "physical"),
    ("フーディン", "special"),
])
def test_シェルアームズ_AがCより高いとき物理技になる(attacker_name: str, expected: str):
    """シェルアームズ: 補正込みAがCより高いとき物理技、そうでなければ特殊技として計算する。"""
    battle = t.start_battle(
        team0=[Pokemon(attacker_name, move_names=["シェルアームズ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)
    assert battle.move_executor.resolve_move_category(attacker, move) == expected
    move.unregister_handlers(battle.events, attacker)


def test_シェルアームズ_どくが発動する():
    """シェルアームズ: 20%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["シェルアームズ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_しおづけ_しおづけ揮発状態が付与される():
    """しおづけ: 100%の確率で相手をしおづけ揮発状態にする。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["しおづけ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("しおづけ")


def test_しおづけ_ターン終了後にダメージを受ける():
    """しおづけ: しおづけ状態付与後、ターン終了時に最大HPの1/16のダメージを受ける（カビゴンはみず・はがねタイプではない）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["しおづけ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    max_hp = defender.max_hp
    t.run_move(battle, 0)
    hp_after_hit = defender.hp
    # しおづけ状態付与後、ターン終了時ダメージが発生する
    t.end_turn(battle)
    assert hp_after_hit - defender.hp == max_hp // 16


def test_しおふき_HP半分のとき威力約75():
    """しおふき: 使用者のHPが半分のとき威力が約75になる。
    modifier = floor(half_hp * 4096 / max_hp) ≈ 2039、final_power = round_half_down(150 * 2039 / 4096) = 75。
    """
    battle = t.start_battle(
        team0=[Pokemon("カイオーガ", move_names=["しおふき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp // 2
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power < 150
    assert battle.damage_calculator.final_power >= 1


def test_しおふき_HP満タンのとき威力150():
    """しおふき: 使用者のHPが満タンのとき威力150（modifier=4096）。"""
    battle = t.start_battle(
        team0=[Pokemon("カイオーガ", move_names=["しおふき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp  # 満タン
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 150


def test_しおみず_相手HPが半分より多いとき威力補正なし():
    """しおみず: 相手の現在HPが最大HPの半分より多いとき威力補正なし。"""
    battle = t.start_battle(
        team0=[Pokemon("カイオーガ", move_names=["しおみず"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp  # 満タン
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_しおみず_相手HPが半分以下のとき威力2倍():
    """しおみず: 相手の現在HPが最大HPの半分以下（境界値含む）のとき威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイオーガ", move_names=["しおみず"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2  # ちょうど半分（境界値）
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_シグナルビーム_こんらんが発動する():
    """シグナルビーム: 10%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["シグナルビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_したでなめる_まひが発動する():
    """したでなめる: 30%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["したでなめる"])],
        team1=[Pokemon("リザードン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_しっとのほのお_ランクが上がった相手にやけどが付与される():
    """しっとのほのお: そのターンにランクが上昇した相手をやけど状態にする。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["しっとのほのお"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # 事前にdefenderのランクを上げてstat_raised_this_turnをTrueにする
    battle.modify_stats(defender, {"atk": 1}, source=defender)
    assert defender.stat_raised_this_turn
    t.run_move(battle, 0)
    assert defender.ailment.name == "やけど"


def test_しっとのほのお_ランクが上がっていない相手にはやけどが付与されない():
    """しっとのほのお: そのターンにランクが上昇していない相手にはやけどを付与しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["しっとのほのお"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert not defender.stat_raised_this_turn
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


def test_しっぺがえし_先攻のとき通常威力():
    """しっぺがえし: 先攻で行動する場合、威力補正なし。
    ピカチュウ(高速)がしっぺがえし、カビゴン(低速)がはねるでターンを進めると
    ピカチュウが先攻になるため power_modifier = 4096 になる。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["しっぺがえし"])],
        team1=[Pokemon("カビゴン", move_names=["はねる"])],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    battle.step()
    assert battle.damage_calculator.power_modifier == 4096


def test_しっぺがえし_後攻のとき威力2倍():
    """しっぺがえし: 同ターン後攻で行動する場合、威力が2倍になる。
    カビゴン(低速)がしっぺがえし、ピカチュウ(高速)がはねるでターンを進めると
    カビゴンが後攻になるため power_modifier = 8192 になる。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["しっぺがえし"])],
        team1=[Pokemon("ピカチュウ", move_names=["はねる"])],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    battle.step()
    assert battle.damage_calculator.power_modifier == 8192


def test_しねんのずつき_ひるみが発動する():
    """しねんのずつき: 20%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["しねんのずつき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_シャカシャカほう_やけどが発動する():
    """シャカシャカほう: 20%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["シャカシャカほう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_シャカシャカほう_やけど追加効果も発動する():
    """シャカシャカほう: ドレイン回復と同時に20%でやけども付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["シャカシャカほう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_シャカシャカほう_使用後に攻撃者のHPが回復する():
    """シャカシャカほう: 与えたダメージの半分だけ攻撃者のHPを回復する（heal_ratio=0.5）。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["シャカシャカほう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp > hp_before


def test_シャドーボーン_ぼうぎょ1段階低下が発動する():
    """シャドーボーン: 20%の確率で相手のぼうぎょを1段階下げる。ゴーストタイプはエスパータイプに有効。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["シャドーボーン"])],
        team1=[Pokemon("ミュウツー")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["def"] == -1


def test_シャドーレイ_ハードロックの効果抜群軽減を無視する():
    """シャドーレイ: 相手の特性を無視するため、ハードロックによる効果抜群ダメージ軽減が発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["シャドーレイ"])],
        team1=[Pokemon("ミュウツー", ability_name="ハードロック")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 4096


def test_シャドーレイ_攻撃後に相手の特性が有効に戻る():
    """シャドーレイ: 攻撃終了後は相手の特性の無効化が解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["シャドーレイ"])],
        team1=[Pokemon("ミュウツー", ability_name="ハードロック")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.ability.enabled is True


def test_しんくうは_相手にダメージを与える():
    """しんくうは: 優先度+1の先制特殊技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["しんくうは"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_しんそく_相手にダメージを与える():
    """しんそく: 優先度+2の先制物理技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("エーフィ", move_names=["しんそく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_しんぴのちから_特攻1段階上昇が発動する():
    """しんぴのちから: 命中時に使用者のCが1段階上昇する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["しんぴのちから"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["spa"] == 1


def test_ジェットパンチ_相手にダメージを与える():
    """ジェットパンチ: 優先度+1の先制物理技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["ジェットパンチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_じごくぐるま_使用後に攻撃者が反動ダメージを受ける():
    """じごくぐるま: 与えたダメージの1/4を攻撃者が反動として受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["じごくぐるま"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_じごくぐるま_反動ダメージが与ダメの4分の1になる():
    """じごくぐるま: 反動量は max(1, int(与ダメ * 1/4)) で計算される。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["じごくぐるま"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_damage(battle, 100)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    # max(1, int(100 * 1/4)) = 25
    assert attacker.hp == hp_before - 25


def test_じごくづき_2ターン後にじごくづき揮発状態が解除される():
    """じごくづき: 付与したじごくづき揮発状態は2ターン後（count=2）に解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["じごくづき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_volatile("じごくづき")
    # 1ターン終了後はまだ揮発状態が続く
    t.end_turn(battle)
    assert defender.has_volatile("じごくづき")
    # 2ターン終了後は揮発状態が解除される
    t.end_turn(battle)
    assert not defender.has_volatile("じごくづき")


def test_じごくづき_じごくづき状態の相手は音技を使えない():
    """じごくづき: 命中後、同ターン内に相手が音技を使おうとするとON_TRY_ACTIONでブロックされる。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["じごくづき"])],
        team1=[Pokemon("カビゴン", move_names=["ハイパーボイス"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_volatile("じごくづき")
    # カビゴンがハイパーボイス（音技）を使おうとするとブロックされる
    t.run_move(battle, 1)
    assert not battle.move_executor.action_success


def test_じごくづき_命中後にじごくづき揮発状態が付与される():
    """じごくづき: 命中後、相手がじごくづき揮発状態になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["じごくづき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_volatile("じごくづき")


def test_じだんだ_タイプ相性で無効化された場合威力2倍になる():
    """じだんだ: 前のターンにタイプ相性(ひこうタイプ)で技が無効化された場合も、威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じだんだ"])],
        team1=[Pokemon("ピジョット"), Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False
    t.end_turn(battle)

    # 無効化されないポケモンに交代してから、じだんだを再度使用
    t.run_switch(battle, 1, 1)
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_じだんだ_まひで行動不能だった場合威力2倍になる():
    """じだんだ: 前のターンにまひで行動できなかった場合、威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じだんだ"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("まひ", None),
        accuracy=100,
    )
    battle.test_option.trigger_ailment = True
    t.run_move(battle, 0)
    assert battle.move_executor.action_success is False
    t.end_turn(battle)

    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_じだんだ_まもるで防がれた場合威力2倍になる():
    """じだんだ: 前のターンに相手のまもるで防がれた場合、威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じだんだ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False
    t.end_turn(battle)

    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_じだんだ_交代直後は前のターンの失敗を引き継がない():
    """じだんだ: 交代して控えに下がった後、再度出てきたときは前の失敗状態を引き継がない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じだんだ"]), Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.failed_or_immobile_last_turn
    t.end_turn(battle)

    # 控えに下がってから、再度出す
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    assert not attacker.failed_or_immobile_last_turn

    battle.test_option.accuracy = 100
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_じだんだ_技が外れた場合威力2倍になる():
    """じだんだ: 前のターンに技が外れた場合、威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じだんだ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_missed
    t.end_turn(battle)

    battle.test_option.accuracy = 100
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_じだんだ_通常成功時は次のターン威力2倍にならない():
    """じだんだ: 前のターンに技が通常通り成功した場合、威力補正はかからない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じだんだ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    t.end_turn(battle)

    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_じばく_HP消費後も攻撃が相手に届く():
    """じばく: ON_PAY_HPはヒット処理より前に発火するため、HP0でも攻撃が相手に届く。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じばく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_じばく_しめりけ持ちには技が失敗する():
    """じばく: labels=["explosion"]のため、しめりけ持ちには技が失敗する。ON_PAY_HPは発火しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じばく"])],
        team1=[Pokemon("ニョロモ", ability_name="しめりけ")],
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False
    assert attacker.hp == hp_before


def test_じばく_使用後に攻撃者がひんしになる():
    """じばく: ON_PAY_HPで現在HPを全消費し、技使用後に使用者がひんし状態になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じばく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == 0
    assert not attacker.alive


def test_ジャイロボール_まひで実効素早さが半減すると威力が増加する():
    """ジャイロボール: まひにより攻撃側の実効素早さが半減すると威力が増加する。

    カビゴン(S=50、まひ適用後実効S=25) vs ピカチュウ(S=110) → 威力111。
    まひなし同組み合わせ(実効S=50) → 威力56。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ジャイロボール"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.apply_ailment(battle, 0, "まひ")
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 111


def test_ジャイロボール_威力の上限は150():
    """ジャイロボール: 計算結果が150を超える場合は150で頭打ちになる（ヤドンS=35 vs レジエレキS=220）。"""
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", move_names=["ジャイロボール"])],
        team1=[Pokemon("レジエレキ")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 150


def test_ジャイロボール_速い攻撃側が遅い防御側に対して低い威力になる():
    """ジャイロボール: 攻撃側S(110) > 防御側S(35) のとき威力8（floor(25×35÷110)+1）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ジャイロボール"])],
        team1=[Pokemon("ヤドン")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 8


def test_ジャイロボール_遅い攻撃側が速い防御側に対して高い威力になる():
    """ジャイロボール: 攻撃側S(35) < 防御側S(110) のとき威力79（floor(25×110÷35)+1）。"""
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", move_names=["ジャイロボール"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 79


def test_じゃどくのくさり_もうどくが発動する():
    """じゃどくのくさり: 50%でもうどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["じゃどくのくさり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "もうどく"


def test_じゃれつく_こうげき1段階低下が発動する():
    """じゃれつく: 10%の確率で相手のこうげきを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ニンフィア", move_names=["じゃれつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["atk"] == -1


def test_じんつうりき_ひるみが発動する():
    """じんつうりき: 10%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["じんつうりき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_すいとる_使用後に攻撃者のHPが回復する():
    """すいとる: 与えたダメージの半分だけ攻撃者のHPを回復する（heal_ratio=0.5）。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["すいとる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp > hp_before


def test_スイープビンタ_複数ヒットする():
    """スイープビンタ: 2～5回連続でヒットする複数ヒット技である。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["スイープビンタ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    assert 2 <= hit_count <= 5


def test_スケイルショット_最終ヒット時にぼうぎょマイナス1_すばやさプラス1():
    """スケイルショット: 全ヒット終了後に使用者のぼうぎょが1段階下がり、すばやさが1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["スケイルショット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["def"] == -1
    assert attacker.rank["spe"] == 1


def test_スケイルショット_複数ヒットする():
    """スケイルショット: 2～5回連続でヒットする複数ヒット技である。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["スケイルショット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    assert 2 <= hit_count <= 5


def test_スチームバースト_やけどが発動する():
    """スチームバースト: 30%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["スチームバースト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_すてみタックル_使用後に攻撃者が反動ダメージを受ける():
    """すてみタックル: 与えたダメージの1/3を攻撃者が反動として受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["すてみタックル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_スパーク_まひが発動する():
    """スパーク: 30%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スパーク"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_スモッグ_どくが発動する():
    """スモッグ: 40%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["スモッグ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_ずつき_ひるみが発動する():
    """ずつき: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ずつき"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_せいなるつるぎ_相手のぼうぎょランクを無視する():
    """せいなるつるぎ: 相手のぼうぎょランクが上がっていてもダメージが変わらない。"""
    battle1 = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["せいなるつるぎ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle1.random.random = lambda: 0.9
    mon1 = battle1.actives[1]
    battle1.modify_stats(mon1, {"def": 6}, source=mon1)
    hp_before = mon1.hp
    t.run_move(battle1, 0)
    damage_with_b6 = hp_before - mon1.hp

    battle2 = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["せいなるつるぎ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle2.random.random = lambda: 0.9
    mon2 = battle2.actives[1]
    hp_before2 = mon2.hp
    t.run_move(battle2, 0)
    damage_no_rank = hp_before2 - mon2.hp

    assert damage_with_b6 == damage_no_rank


def test_せいなるつるぎ_相手のぼうぎょランク低下も無視する():
    """せいなるつるぎ: 相手のぼうぎょランクが下がっていてもダメージが変わらない。"""
    battle1 = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["せいなるつるぎ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle1.random.random = lambda: 0.9
    mon1 = battle1.actives[1]
    battle1.modify_stats(mon1, {"def": -6}, source=mon1)
    hp_before = mon1.hp
    t.run_move(battle1, 0)
    damage_with_neg = hp_before - mon1.hp

    battle2 = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["せいなるつるぎ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle2.random.random = lambda: 0.9
    mon2 = battle2.actives[1]
    hp_before2 = mon2.hp
    t.run_move(battle2, 0)
    damage_no_rank = hp_before2 - mon2.hp

    assert damage_with_neg == damage_no_rank


def test_せいなるほのお_やけどが発動する():
    """せいなるほのお: 50%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ビクティニ", move_names=["せいなるほのお"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_そらをとぶ_2ターンで攻撃する():
    """そらをとぶ: 1ターン目はダメージを与えず揮発状態を付与し、2ターン目にダメージを与えて揮発状態を解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["そらをとぶ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp

    # 1ターン目: 揮発状態付与のみ、ダメージなし
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert "そらをとぶ" in attacker.volatiles

    # 2ターン目: ダメージあり、揮発状態解除
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert "そらをとぶ" not in attacker.volatiles


def test_そらをとぶ_かみなりは命中する():
    """そらをとぶ: そらをとぶ状態でもかみなりは命中する（許可リスト技）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["かみなり"])],
        team1=[Pokemon("カビゴン", move_names=["そらをとぶ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    # 1ターン目: defenderがそらをとぶ（揮発状態付与）
    t.run_move(battle, 1)
    assert "そらをとぶ" in defender.volatiles

    # かみなりが命中する
    t.run_move(battle, 0)
    assert battle.move_executor.move_success
    assert defender.hp < defender.max_hp


def test_そらをとぶ_空中は通常技を回避する():
    """そらをとぶ: 1ターン目のそらをとぶ中は通常技を受けない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["そらをとぶ"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp

    # 1ターン目: そらをとぶを使用（揮発状態付与）
    t.run_move(battle, 0)
    # 相手のたいあたりはミスする
    t.run_move(battle, 1)
    assert attacker.hp == hp_before
