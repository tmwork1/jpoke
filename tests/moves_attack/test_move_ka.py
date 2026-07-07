"""攻撃技ハンドラの単体テスト（か行）。"""

import pytest
from jpoke import Pokemon
from jpoke.enums import Command, Interrupt
from .. import test_utils as t


def test_かいりき_相手にダメージを与える():
    """かいりき: 追加効果なしの物理ノーマル技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かいりき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_カウンター_みがわりに当たったダメージは参照されない():
    """カウンター: みがわりが被弾したダメージは物理ダメージとして記録されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["カウンター"])],
        team1=[Pokemon("カビゴン", move_names=["ひっかく"])],
        accuracy=100,
        volatile0={"みがわり": 1},
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 相手の物理技をみがわりで受ける
    t.run_move(battle, 1)
    assert attacker.last_physical_damage_received == 0
    hp_before = defender.hp
    # カウンターは失敗するはず
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_カウンター_物理ダメージを受けていないとき失敗する():
    """カウンター: そのターン物理ダメージを受けていない場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["カウンター"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_カウンター_物理技ダメージを2倍返しする():
    """カウンター: 物理技で受けたダメージの2倍を相手に与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["カウンター"])],
        team1=[Pokemon("カビゴン", move_names=["ひっかく"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 相手の物理技を受ける
    t.run_move(battle, 1)
    phys_dmg = attacker.last_physical_damage_received
    assert phys_dmg > 0
    hp_before = defender.hp
    # カウンターで2倍返し
    t.run_move(battle, 0)
    assert defender.hp == hp_before - phys_dmg * 2


def test_カウンター_特殊ダメージのみ受けたとき失敗する():
    """カウンター: そのターン特殊ダメージのみ受けた場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["カウンター"])],
        team1=[Pokemon("カビゴン", move_names=["かえんほうしゃ"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    # 相手の特殊技を受ける
    t.run_move(battle, 1)
    hp_before = defender.hp
    # カウンターは失敗するはず
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_カウンター_連続技を受けた場合は最後の1回分のダメージのみ参照する():
    """カウンター: 連続技を受けた場合、合計ではなく最後の1回分のダメージを2倍にする。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["カウンター"])],
        team1=[Pokemon("カビゴン", move_names=["ダブルアタック"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.fix_damage(battle, 10)
    # 相手の連続技（2回攻撃）を受ける
    t.run_move(battle, 1)
    assert attacker.hits_taken == 2
    # 合計(20)ではなく最後の1回分(10)のみが記録される
    assert attacker.last_physical_damage_received == 10
    hp_before = defender.hp
    # カウンターは最後の1回分(10)の2倍=20だけを返す
    t.run_move(battle, 0)
    assert defender.hp == hp_before - 20


def test_かえんぐるま_こおり状態で使うと解凍されて攻撃できる():
    """かえんぐるま: こおり状態でも使用でき、使うと解凍される。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["かえんぐるま"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # こおり状態を付与してから使用
    t.apply_ailment(battle, 0, "こおり")
    assert attacker.ailment.name == "こおり"
    hp_before = defender.hp
    t.run_move(battle, 0)
    # こおりが解除されてダメージを与えられる
    assert not attacker.ailment.is_active
    assert battle.move_executor.move_success is True
    assert defender.hp < hp_before


def test_かえんぐるま_やけどが発動する():
    """かえんぐるま: 10%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["かえんぐるま"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_かえんだん_やけどが発動する():
    """かえんだん: 30%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["かえんだん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_かえんほうしゃ_こおり状態の相手に当てると解凍する():
    """かえんほうしゃ: ほのおタイプの攻撃技のため、被弾した相手のこおりを解凍する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["かえんほうしゃ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "こおり")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active


def test_かえんほうしゃ_やけどが発動する():
    """かえんほうしゃ: 10%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["かえんほうしゃ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_かえんボール_こおり状態で使うと解凍されて攻撃できる():
    """かえんボール: こおり状態でも使用でき、使うと解凍される。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["かえんボール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # こおり状態を付与してから使用
    t.apply_ailment(battle, 0, "こおり")
    assert attacker.ailment.name == "こおり"
    hp_before = defender.hp
    t.run_move(battle, 0)
    # こおりが解除されてダメージを与えられる
    assert not attacker.ailment.is_active
    assert battle.move_executor.move_success is True
    assert defender.hp < hp_before


def test_かえんボール_やけどが発動する():
    """かえんボール: 10%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["かえんボール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_かかとおとし_いしあたまでも失敗反動ダメージを受ける():
    """かかとおとし: reason=self_costのためいしあたまでも防げない。"""
    battle = t.start_battle(
        team0=[Pokemon("ゴンベ", ability_name="いしあたま", move_names=["かかとおとし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    expected_damage = max(1, attacker.max_hp // 2)
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_damage


def test_かかとおとし_こんらんが発動する():
    """かかとおとし: 30%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かかとおとし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


@pytest.mark.parametrize("roll, expected_count", [(3, 3), (5, 5)])
def test_かかとおとし_こんらんの継続ターンは3から5ターン(roll: int, expected_count: int):
    """かかとおとし: 通常のこんらん技(2〜5ターン)と異なり3〜5ターン継続する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かかとおとし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    battle.random.randint = lambda a, b: roll
    t.run_move(battle, 0)
    assert battle.actives[1].volatiles["こんらん"].count == expected_count


def test_かかとおとし_命中時は失敗反動ダメージを受けない():
    """かかとおとし: 命中したときはON_MISSが発火しないため失敗反動はない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かかとおとし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    # 命中時は使用者のHPは変わらない（反動なし）
    assert attacker.hp == hp_before


def test_かかとおとし_外れたとき失敗反動ダメージを受ける():
    """かかとおとし: 外れたとき自分の最大HPの1/2ダメージを受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かかとおとし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    expected_damage = max(1, attacker.max_hp // 2)
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_damage


def test_かかとおとし_外れた場合こんらんが発動しない():
    """かかとおとし: 外れた場合はON_DAMAGE_HITが発火しないためこんらんが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かかとおとし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    # 外れた場合はこんらんが付与されない
    assert not battle.actives[1].has_volatile("こんらん")


def test_かかとおとし_確率外れでこんらんが発動しない():
    """かかとおとし: secondary_chance=0.0のとき（確率外れ）こんらんを付与しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かかとおとし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("こんらん")


def test_かげうち_相手にダメージを与える():
    """かげうち: 優先度+1の先制物理技で相手にダメージを与える。ゴーストタイプはエスパータイプに有効。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["かげうち"])],
        team1=[Pokemon("ミュウツー")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_かげぬい_ちからずくで威力上昇しにげられない状態は付与されない():
    """かげぬい: ちからずく使用時は威力が1.3倍になる代わりに、にげられない状態が付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ジュナイパー", ability_name="ちからずく", move_names=["かげぬい"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier
    assert not battle.actives[1].has_volatile("にげられない")


def test_かげぬい_にげられない状態を付与する():
    """かげぬい: 追加効果として、相手をにげられない状態にする。"""
    battle = t.start_battle(
        team0=[Pokemon("ジュナイパー", move_names=["かげぬい"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("にげられない")


def test_かげぬい_りんぷんの相手にはにげられない状態が付与されない():
    """かげぬい: 相手の特性がりんぷんの場合、にげられない状態は付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ジュナイパー", move_names=["かげぬい"])],
        team1=[Pokemon("ピカチュウ", ability_name="りんぷん")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("にげられない")


def test_かげぬい_相手にダメージを与える():
    """かげぬい: 追加効果ありの物理ゴースト技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ジュナイパー", move_names=["かげぬい"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_かぜおこし_相手にダメージを与える():
    """かぜおこし: 追加効果なしの特殊ひこう技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピジョット", move_names=["かぜおこし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_かたきうち_味方がひんしになっていない場合威力は上がらない():
    """かたきうち: 味方が一度もひんしになっていない場合、威力は基本値70のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["かたきうち"]), Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 70


def test_かたきうち_味方がひんしになってから2ターン経過すると威力は上がらない():
    """かたきうち: 味方がひんしになってから2ターン以上経過している場合、威力は上がらない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["かたきうち"]), Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player0 = battle.players[0]
    bench = battle.player_states[player0].bench
    battle.modify_hp(bench[0], v=-bench[0].max_hp)  # ピカチュウをひんしにする（このターン）
    battle.turn += 2  # 2ターン進める
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 70


def test_かたきうち_味方が前のターンにひんしになると威力が2倍になる():
    """かたきうち: 味方が前のターンにひんしになっていた場合、威力が2倍(140)になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["かたきうち"]), Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player0 = battle.players[0]
    bench = battle.player_states[player0].bench
    battle.modify_hp(bench[0], v=-bench[0].max_hp)  # ピカチュウをひんしにする（このターン）
    battle.turn += 1  # 次のターンに進める
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 140


def test_かたきうち_相手がひんしになっても威力は上がらない():
    """かたきうち: 相手側のポケモンがひんしになっても、自分側の記録には影響しないため威力は上がらない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["かたきうち"])],
        team1=[Pokemon("カビゴン"), Pokemon("ピカチュウ")],
        accuracy=100,
    )
    player1 = battle.players[1]
    bench1 = battle.player_states[player1].bench
    battle.modify_hp(bench1[0], v=-bench1[0].max_hp)  # 相手のピカチュウをひんしにする（このターン）
    battle.turn += 1  # 次のターンに進める
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 70


def test_カタストロフィ_こらえるで1HP残る():
    """カタストロフィ: 固定ダメージの計算がこらえるより先に行われ、瀕死を防げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["カタストロフィ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        volatile1={"こらえる": 1},
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.hp == 1
    assert not defender.fainted


def test_カタストロフィ_ゴーストタイプにも通常通り命中する():
    """カタストロフィ: あくタイプの技のため、いかりのまえば(ノーマル技)と異なりゴーストタイプにも命中する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["カタストロフィ"])],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_カタストロフィ_みがわりは本体HP基準でダメージを計算する():
    """カタストロフィ: みがわりの残りHPではなく本体の残りHPを基準にダメージを計算し、
    みがわりのHPを上限として肩代わりされる（本体HPは減らない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["カタストロフィ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "みがわり", hp=50)
    hp_before = defender.hp
    t.run_move(battle, 0)
    # 本体HPを基準にした半減ダメージ(117)はみがわりのHP(50)を上回るため、みがわりが解除される
    assert not defender.has_volatile("みがわり")
    # 超過分は本体に持ち越されず、本体HPは変化しない
    assert defender.hp == hp_before


def test_カタストロフィ_最低1ダメージ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["カタストロフィ"])],
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
def test_カタストロフィ_相手HP半分のダメージ(defender_hp: int, expected_damage: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["カタストロフィ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender.hp = defender_hp
    t.run_move(battle, 0)
    assert defender.hp == defender_hp - expected_damage


def test_かふんだんご_相手にダメージを与える():
    """かふんだんご: シングルバトルには味方が存在しないため、常に相手を対象とした
    追加効果なしの特殊むし技として扱われる。"""
    battle = t.start_battle(
        team0=[Pokemon("アブリボン", move_names=["かふんだんご"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_かみくだく_ぼうぎょ1段階低下が発動しない():
    """かみくだく: 追加効果不発時はぼうぎょランクが変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["かみくだく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["def"] == 0


def test_かみくだく_ぼうぎょ1段階低下が発動する():
    """かみくだく: 20%の確率で相手のぼうぎょを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["かみくだく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["def"] == -1


def test_かみくだく_相手にダメージを与える():
    """かみくだく: 物理あく技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["かみくだく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_かみつく_ひるみが発動する():
    """かみつく: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", move_names=["かみつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_かみなり_あめ中は必中になる():
    """かみなり: あめ天候中は命中率70でも通常なら外れる乱数で命中する。

    かみなりの命中率は70。random.random()=0.85 のとき 100*0.85=85>70 で本来は外れるが、
    あめ中はON_MODIFY_ACCURACYでNoneが返り必中になるため、命中してHPが減る。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かみなり"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    # random.random()=0.85 は命中率70未満ではない（85>70）ので通常は外れる
    battle.random.random = lambda: 0.85
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_かみなり_にほんばれ中は命中率が50になる():
    """かみなり: にほんばれ（はれ）天候中は命中率が50になる。

    random.random()=0.6 のとき 100*0.6=60 は通常の命中率70未満だが、
    はれ中は命中率が50になるため60>50で外れる。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かみなり"])],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
    )
    battle.random.random = lambda: 0.6
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_かみなり_まひが発動する():
    """かみなり: 30%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かみなり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_かみなりあらし_あめ中は必中になる():
    """かみなりあらし: あめ天候中は命中率80でも通常なら外れる乱数で命中する。

    かみなりあらしの命中率は80。random.random()=0.9 のとき 100*0.9=90>80 で本来は外れるが、
    あめ中はON_MODIFY_ACCURACYでNoneが返り必中になるため、命中してHPが減る。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かみなりあらし"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    # random.random()=0.9 は命中率80未満ではない（90>80）ので通常は外れる
    battle.random.random = lambda: 0.9
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_かみなりあらし_まひが発動する():
    """かみなりあらし: 20%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かみなりあらし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_かみなりのキバ_ひるみが発動する():
    """かみなりのキバ: 10%でひるみを付与する（まひとは独立判定）。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", move_names=["かみなりのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_かみなりのキバ_まひが発動する():
    """かみなりのキバ: 10%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", move_names=["かみなりのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_かみなりパンチ_まひが発動する():
    """かみなりパンチ: 10%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かみなりパンチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_からげんき_ねごと経由の使用では威力が上がらない():
    """からげんき: ねむり状態でねごと経由に使用しても威力は上がらない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ねごと", "からげんき"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("ねむり", 3),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_からげんき_まひ状態でも威力2倍():
    """からげんき: まひ状態（やけど以外の状態異常）でも威力2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["からげんき"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("まひ", None),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_からげんき_やけどの攻撃半減を無効化する():
    """からげんき: やけど状態でも攻撃が半減しない（burn_modifier=4096）。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["からげんき"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("やけど", None),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.burn_modifier == 4096


def test_からげんき_ゆめうつつ状態では威力が上がらない():
    """からげんき: ゆめうつつ状態（ぜったいねむり相当）では威力が上がらない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["からげんき"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("ゆめうつつ", None),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_からげんき_状態異常なしのとき通常威力():
    """からげんき: 使用者が状態異常でないとき威力補正なし。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["からげんき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_からげんき_状態異常のとき威力2倍():
    """からげんき: 使用者が状態異常のとき威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["からげんき"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("やけど", None),
        accuracy=100,
    )
    battle.random.random = lambda: 0.9
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_からみつく_すばやさ低下が発動する():
    """からみつく: 10%で相手のすばやさを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["からみつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["spe"] == -1


def test_かわらわり_オーロラベールを解除する():
    """かわらわり: 命中時に相手側のオーロラベールを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かわらわり"])],
        team1=[Pokemon("カビゴン")],
        side1={"オーロラベール": 1},
        accuracy=100,
    )
    assert battle.side_managers[1].fields["オーロラベール"].is_active
    t.run_move(battle, 0)
    assert not battle.side_managers[1].fields["オーロラベール"].is_active


def test_かわらわり_ひかりのかべを解除する():
    """かわらわり: 命中時に相手側のひかりのかべを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かわらわり"])],
        team1=[Pokemon("カビゴン")],
        side1={"ひかりのかべ": 1},
        accuracy=100,
    )
    assert battle.side_managers[1].fields["ひかりのかべ"].is_active
    t.run_move(battle, 0)
    assert not battle.side_managers[1].fields["ひかりのかべ"].is_active


def test_かわらわり_まもるで防がれたとき壁を解除しない():
    """かわらわり: まもるで無効化された場合はリフレクターを解除しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かわらわり"])],
        team1=[Pokemon("カビゴン")],
        side1={"リフレクター": 1},
        volatile1={"まもる": 1},
        accuracy=100,
    )
    assert battle.side_managers[1].fields["リフレクター"].is_active
    t.run_move(battle, 0)
    assert battle.side_managers[1].fields["リフレクター"].is_active


def test_かわらわり_リフレクターがあってもダメージは軽減されない():
    """かわらわり: 壁はダメージ計算前に解除されるため、このターンのダメージ自体は軽減されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かわらわり"])],
        team1=[Pokemon("カビゴン")],
        side1={"リフレクター": 1},
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 4096


def test_かわらわり_リフレクターを解除する():
    """かわらわり: 命中時に相手側のリフレクターを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かわらわり"])],
        team1=[Pokemon("カビゴン")],
        side1={"リフレクター": 1},
        accuracy=100,
    )
    assert battle.side_managers[1].fields["リフレクター"].is_active
    t.run_move(battle, 0)
    assert not battle.side_managers[1].fields["リフレクター"].is_active


def test_かわらわり_命中が外れたとき壁を解除しない():
    """かわらわり: 命中判定に外れた場合はリフレクターを解除しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かわらわり"])],
        team1=[Pokemon("カビゴン")],
        side1={"リフレクター": 1},
        accuracy=0,
    )
    assert battle.side_managers[1].fields["リフレクター"].is_active
    t.run_move(battle, 0)
    assert battle.side_managers[1].fields["リフレクター"].is_active


def test_かわらわり_壁3種を同時に解除する():
    """かわらわり: 命中時にリフレクター・ひかりのかべ・オーロラベールを同時に解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かわらわり"])],
        team1=[Pokemon("カビゴン")],
        side1={"リフレクター": 1, "ひかりのかべ": 1, "オーロラベール": 1},
        accuracy=100,
    )
    assert battle.side_managers[1].fields["リフレクター"].is_active
    assert battle.side_managers[1].fields["ひかりのかべ"].is_active
    assert battle.side_managers[1].fields["オーロラベール"].is_active
    t.run_move(battle, 0)
    assert not battle.side_managers[1].fields["リフレクター"].is_active
    assert not battle.side_managers[1].fields["ひかりのかべ"].is_active
    assert not battle.side_managers[1].fields["オーロラベール"].is_active


def test_かわらわり_壁がなくても動作する():
    """かわらわり: 相手側に壁が張られていない場合もエラーなく動作する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かわらわり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_がむしゃら_ゴーストタイプに無効():
    """がむしゃら: ノーマル技のためゴーストタイプにはダメージを与えられない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["がむしゃら"])],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    attacker.hp = 30
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before


@pytest.mark.parametrize(
    ("attacker_hp", "defender_hp"),
    [
        (80, 60),  # 相手HP<自分HP
        (50, 50),  # 相手HP=自分HP
    ],
)
def test_がむしゃら_相手HPが自分以下の場合は失敗する(attacker_hp: int, defender_hp: int):
    """がむしゃら: 相手の残りHPが自分の残りHP以下の場合、無効化されたときと同様に技が失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["がむしゃら"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.hp = attacker_hp
    defender.hp = defender_hp
    t.run_move(battle, 0)
    assert defender.hp == defender_hp
    assert attacker.failed_or_immobile_last_turn


@pytest.mark.parametrize(
    ("attacker_hp", "defender_hp", "expected_damage"),
    [
        (30, 100, 70),
    ],
)
def test_がむしゃら_相手HPとの差分ダメージ(attacker_hp: int, defender_hp: int, expected_damage: int):
    """がむしゃら: 相手の残りHPから自分の残りHPを引いた分の固定ダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["がむしゃら"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.hp = attacker_hp
    defender.hp = defender_hp
    t.run_move(battle, 0)
    battle.print_logs()
    assert defender.hp == defender_hp - expected_damage


def test_ガリョウテンセイ_ちからずくは無関係で発動する():
    """ガリョウテンセイ: 自分のランクを下げる確定効果はちからずくの対象外のため、
    ちからずく所持時も威力上昇なし・ぼうぎょととくぼうの低下は通常通り発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("レックウザ", ability_name="ちからずく", move_names=["ガリョウテンセイ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    attacker = battle.actives[0]
    assert attacker.rank["def"] == -1
    assert attacker.rank["spd"] == -1
    assert battle.damage_calculator.power_modifier == 4096


def test_ガリョウテンセイ_ぼうぎょととくぼう1段階低下が発動する():
    """ガリョウテンセイ: 技が成功すると確定で自分の『ぼうぎょ』『とくぼう』ランクが1段階ずつ下がる。"""
    battle = t.start_battle(
        team0=[Pokemon("レックウザ", move_names=["ガリョウテンセイ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    attacker = battle.actives[0]
    assert attacker.rank["def"] == -1
    assert attacker.rank["spd"] == -1


def test_がんせきアックス_ステルスロック設置済みのとき攻撃は成功する():
    """がんせきアックス: 相手陣営がステルスロック設置済みでも攻撃は成功する。"""
    battle = t.start_battle(
        team0=[Pokemon("イシヘンジン", move_names=["がんせきアックス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        side1={"ステルスロック": 1},
    )
    defender = battle.actives[1]
    side = battle.get_side(defender)
    hp_before = defender.hp
    t.run_move(battle, 0)
    # 攻撃は成功してダメージを与える
    assert defender.hp < hp_before
    # ステルスロックは設置済みのまま
    assert side.fields["ステルスロック"].is_active


def test_がんせきアックス_命中後にダメージを与える():
    """がんせきアックス: 命中すると相手に通常通りダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("イシヘンジン", move_names=["がんせきアックス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_がんせきアックス_命中後に相手陣営がステルスロック状態になる():
    """がんせきアックス: 命中後に相手陣営がステルスロック状態になる。"""
    battle = t.start_battle(
        team0=[Pokemon("イシヘンジン", move_names=["がんせきアックス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    side = battle.get_side(battle.actives[1])
    t.run_move(battle, 0)
    assert side.fields["ステルスロック"].is_active


def test_がんせきふうじ_すばやさ低下が発動する():
    """がんせきふうじ: 100%の確率で相手のすばやさを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("イシヘンジン", move_names=["がんせきふうじ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["spe"] == -1


def test_がんせきふうじ_ちからずくで威力上昇しすばやさ低下は発動しない():
    """がんせきふうじ: ちからずく使用時は威力が1.3倍になる代わりに、すばやさ低下が発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("イシヘンジン", ability_name="ちからずく", move_names=["がんせきふうじ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier
    assert battle.actives[1].rank["spe"] == 0


def test_がんせきほう_まもるで防がれた場合はリチャージ状態にならない():
    """がんせきほう: まもるで防がれた場合はリチャージ揮発状態が付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["がんせきほう"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_volatile("リチャージ")


def test_がんせきほう_交代するとリチャージ状態が解除される():
    """がんせきほう: リチャージ状態中に交代するとリチャージ揮発状態が解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["がんせきほう"]), Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("リチャージ")
    t.run_switch(battle, 0, 1)
    assert not attacker.has_volatile("リチャージ")


def test_がんせきほう_命中後にリチャージ状態が付与される():
    """がんせきほう: 命中後に使用者にリチャージ揮発状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["がんせきほう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("リチャージ")


def test_がんせきほう_外れた場合はリチャージ状態にならない():
    """がんせきほう: 外れた場合はリチャージ揮発状態が付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["がんせきほう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_volatile("リチャージ")


def test_がんせきほう_次ターン行動不能になる():
    """がんせきほう: 次のターンはリチャージ状態により行動不能になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["がんせきほう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 1ターン目: 技を使用してリチャージ状態を付与
    battle.step()
    assert attacker.has_volatile("リチャージ")
    defender_hp_after_t1 = defender.hp
    # 2ターン目: リチャージ状態で行動不能のため相手HPが変化しない
    battle.step()
    assert not attacker.has_volatile("リチャージ")
    assert defender.hp == defender_hp_after_t1


def test_きあいだま_とくぼう1段階低下が発動しない():
    """きあいだま: 追加効果不発時はとくぼうランクが変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["きあいだま"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["spd"] == 0


def test_きあいだま_とくぼう1段階低下が発動する():
    """きあいだま: 10%の確率で相手のとくぼうを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["きあいだま"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["spd"] == -1


def test_きあいだま_相手にダメージを与える():
    """きあいだま: 特殊かくとう技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["きあいだま"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_きあいパンチ_HP1でみねうちを受けると失敗():
    """きあいパンチ: HPが1のときにみねうちを受けてダメージが0でも不発になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きあいパンチ"])],
        team1=[Pokemon("カビゴン", move_names=["みねうち"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    before_foe_hp = battle.actives[1].hp

    battle.step()

    assert battle.actives[1].hp == before_foe_hp
    assert attacker.hp == 1


def test_きあいパンチ_ばけのかわで肩代わりすると失敗():
    """きあいパンチ: ばけのかわで攻撃ダメージを肩代わりした場合も不発になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ばけのかわ", move_names=["きあいパンチ"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
    )
    attacker = battle.actives[0]
    before_foe_hp = battle.actives[1].hp

    battle.step()

    assert battle.actives[1].hp == before_foe_hp
    assert attacker.ability.enabled is False


def test_きあいパンチ_みがわりへの被弾では中断しない():
    """きあいパンチ: みがわりが被弾しても使用者は中断されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きあいパンチ"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
    )
    battle.volatile_manager.apply(battle.actives[0], "みがわり", hp=999)
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp

    battle.step()

    assert battle.actives[1].hp < before_foe_hp
    assert battle.actives[0].hp == before_ally_hp


def test_きあいパンチ_不発時はPPを消費しない():
    """きあいパンチ: 不発した場合、第五世代以降の仕様に従いPPを消費しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きあいパンチ"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
    )
    attacker = battle.actives[0]
    pp_before = attacker.moves[0].pp

    battle.step()

    assert attacker.moves[0].pp == pp_before


def test_きあいパンチ_攻撃ダメージを受けると失敗():
    """きあいパンチ: 行動前に攻撃ダメージを受けた場合は不発。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きあいパンチ"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
    )
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp

    battle.step()

    assert battle.actives[1].hp == before_foe_hp
    assert battle.actives[0].hp < before_ally_hp


def test_きあいパンチ_行動前にダメージを受けず成功():
    """きあいパンチ: 行動前に被弾していなければ成功する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["きあいパンチ"])],
        team1=[Pokemon("ピカチュウ", move_names=["はねる"])],
    )
    before_foe_hp = battle.actives[1].hp

    battle.step()

    assert battle.actives[1].hp < before_foe_hp


def test_きしかいせい_HP1のとき威力200():
    """きしかいせい: HP が1（X=0）のとき最大威力200。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["きしかいせい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 200


def test_きしかいせい_HP極少のとき威力150():
    """きしかいせい: HP が極少（X=2）のとき威力150。
    カビゴン max_hp=235, hp=10 → x=2 → 威力150。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["きしかいせい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 10  # x = 10*48//235 = 2 → 威力150
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 150


def test_きしかいせい_HP満タンのとき威力20():
    """きしかいせい: HPが満タン（X=48 ≥ 33）のとき威力20。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["きしかいせい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp  # 満タン
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 20


def test_きしかいせい_HP約10パーセントのとき威力100():
    """きしかいせい: HP 10% 付近（X=5）のとき威力100。
    カビゴン max_hp=235, hp=26 → x=5 → 威力100（X=4になると威力150）。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["きしかいせい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 26  # x = 26*48//235 = 5 → 威力100
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 100


def test_きしかいせい_HP約35パーセントのとき威力80():
    """きしかいせい: HP 35% 付近（X=16）のとき威力80。
    カビゴン max_hp=235, hp=82 → x=16 → 威力80。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["きしかいせい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 82  # x = 82*48//235 = 16 → 威力80
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 80


def test_きしかいせい_HP約68パーセントのとき威力40():
    """きしかいせい: HP 68% 付近（X=32）のとき威力40。
    カビゴン max_hp=235, hp=160 → x=32 → 威力40。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["きしかいせい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 160  # x = 160*48//235 = 32 → 威力40
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 40


def test_きまぐレーザー_30パーセントで威力2倍():
    """きまぐレーザー: 乱数が0.3未満のとき威力が2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["きまぐレーザー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.29
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 8192


def test_きまぐレーザー_70パーセントで威力等倍():
    """きまぐレーザー: 乱数が0.3以上のとき威力補正なし。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["きまぐレーザー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.3
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_きゅうけつ_使用後に攻撃者のHPが回復する():
    """きゅうけつ: 与えたダメージの半分だけ攻撃者のHPを回復する（heal_ratio=0.5）。"""
    battle = t.start_battle(
        team0=[Pokemon("スコルピ", move_names=["きゅうけつ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp > hp_before


def test_きょけんとつげき_フェアリータイプに無効化されたとき状態は付与されない():
    """きょけんとつげき: フェアリータイプに技が無効化された場合、状態は付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("セグレイブ", move_names=["きょけんとつげき"])],
        team1=[Pokemon("ニンフィア")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_volatile("きょけんとつげき")


def test_きょけんとつげき_まもるで防がれたとき状態は付与されない():
    """きょけんとつげき: まもるで無効化された場合、状態は付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("セグレイブ", move_names=["きょけんとつげき"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_volatile("きょけんとつげき")


def test_きょけんとつげき_命中時に自身へ状態を付与する():
    """きょけんとつげき: 技が命中すると使用者に「きょけんとつげき」状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("セグレイブ", move_names=["きょけんとつげき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("きょけんとつげき")


def test_きょけんとつげき_外れたとき状態は付与されない():
    """きょけんとつげき: 技が外れた場合、状態は付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("セグレイブ", move_names=["きょけんとつげき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_volatile("きょけんとつげき")


def test_きょけんとつげき状態_ダメージ固定技は2倍にならない():
    """きょけんとつげき状態: いのちがけ等のダメージ固定技は威力計算を経由しないため2倍にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いのちがけ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"きょけんとつげき": None},
        accuracy=100,
    )
    attacker, defender = battle.actives
    attacker.hp = 40
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before - 40


def test_きょけんとつげき状態_まひで行動不能になっても解除される():
    """きょけんとつげき状態: まひ等で行動不能になった場合でも、自身の行動開始時に状態は解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"きょけんとつげき": None},
    )
    attacker = battle.actives[0]
    battle.ailment_manager.apply(attacker, "まひ")
    battle.test_option.trigger_ailment = True
    t.run_move(battle, 0)
    assert not battle.move_executor.action_success
    assert not attacker.has_volatile("きょけんとつげき")


def test_きょけんとつげき状態_次の行動開始時に解除される():
    """きょけんとつげき状態: 自身の次の行動が始まると状態が解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"きょけんとつげき": None},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_volatile("きょけんとつげき")


def test_きょけんとつげき状態_相手の技が必中になる():
    """きょけんとつげき状態: 相手からの技は回避ランクに関係なく必ず命中する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"きょけんとつげき": None},
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy is None


def test_きょけんとつげき状態_相手の技のダメージが2倍になる():
    """きょけんとつげき状態: 相手から受ける技のダメージが2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"きょけんとつげき": None},
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 8192


def test_きょじゅうざん_相手にダメージを与える():
    """きょじゅうざん: 追加効果なしの物理はがね技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["きょじゅうざん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_きょじゅうだん_相手にダメージを与える():
    """きょじゅうだん: 追加効果なしの物理はがね技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["きょじゅうだん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_キラースピン_おんみつマントの相手にはどくを付与できないが場の状態は解除する():
    """キラースピン: 相手がおんみつマントを持つ場合、どく付与は無効化されるが場の状態解除は発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["キラースピン"])],
        team1=[Pokemon("カビゴン", item_name="おんみつマント")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    side = battle.get_side(attacker)
    side.apply("まきびし", count=1)
    t.run_move(battle, 0)
    assert not side.get("まきびし").is_active
    assert not battle.actives[1].ailment.is_active


def test_キラースピン_ステルスロックを解除する():
    """キラースピン: 命中時に使用者のサイドのステルスロックを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["キラースピン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    side = battle.get_side(attacker)
    side.apply("ステルスロック", count=1)
    t.run_move(battle, 0)
    assert not side.get("ステルスロック").is_active


def test_キラースピン_ちからずくでは場の状態解除もどく付与も発動しない():
    """キラースピン: 使用者がちからずくの場合、場の状態解除・どく付与のいずれも発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", ability_name="ちからずく", move_names=["キラースピン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    side = battle.get_side(attacker)
    side.apply("まきびし", count=1)
    battle.volatile_manager.apply(attacker, "バインド", count=4, source=battle.actives[1])
    t.run_move(battle, 0)
    assert side.get("まきびし").is_active
    assert attacker.has_volatile("バインド")
    assert not battle.actives[1].ailment.is_active


def test_キラースピン_どくが発動する():
    """キラースピン: 100%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["キラースピン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_キラースピン_バインドを解除する():
    """キラースピン: 命中時に使用者のバインド状態を解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["キラースピン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "バインド", count=4, source=battle.actives[1])
    t.run_move(battle, 0)
    assert not attacker.has_volatile("バインド")


def test_キラースピン_まきびしを解除する():
    """キラースピン: 命中時に使用者のサイドのまきびしを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["キラースピン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    side = battle.get_side(attacker)
    side.apply("まきびし", count=1)
    t.run_move(battle, 0)
    assert not side.get("まきびし").is_active


def test_キラースピン_やどりぎのタネを解除する():
    """キラースピン: 命中時に使用者のやどりぎのタネ状態を解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["キラースピン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "やどりぎのタネ", source=battle.actives[1])
    t.run_move(battle, 0)
    assert not attacker.has_volatile("やどりぎのタネ")


def test_きりさく_急所ランクが1():
    """きりさく: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["きりさく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_きりさく_急所ランクが1_乱数大で急所なし():
    """きりさく: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["きりさく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


def test_きりさく_相手にダメージを与える():
    """きりさく: 追加効果なしの物理ノーマル技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["きりさく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ギガインパクト_まもるで防がれた場合はリチャージ状態にならない():
    """ギガインパクト: まもるで防がれた場合はリチャージ揮発状態が付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ギガインパクト"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_volatile("リチャージ")


def test_ギガインパクト_交代するとリチャージ状態が解除される():
    """ギガインパクト: リチャージ状態中に交代するとリチャージ揮発状態が解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ギガインパクト"]), Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("リチャージ")
    t.run_switch(battle, 0, 1)
    assert not attacker.has_volatile("リチャージ")


def test_ギガインパクト_命中後にリチャージ状態が付与される():
    """ギガインパクト: 命中後に使用者にリチャージ揮発状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ギガインパクト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("リチャージ")


def test_ギガインパクト_外れた場合はリチャージ状態にならない():
    """ギガインパクト: 外れた場合はリチャージ揮発状態が付与されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ギガインパクト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_volatile("リチャージ")


def test_ギガインパクト_次ターン行動不能になる():
    """ギガインパクト: 次のターンはリチャージ状態により行動不能になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ギガインパクト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.step()
    assert attacker.has_volatile("リチャージ")
    defender_hp_after_t1 = defender.hp
    battle.step()
    assert not attacker.has_volatile("リチャージ")
    assert defender.hp == defender_hp_after_t1


def test_ギガインパクト_相手をひんしにしてもリチャージ状態が付与される():
    """ギガインパクト: 相手をひんしにした場合でもリチャージ揮発状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ギガインパクト"])],
        team1=[Pokemon("ピッピ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.fix_damage(battle, defender.hp)
    t.run_move(battle, 0)
    assert not defender.alive
    assert attacker.has_volatile("リチャージ")


def test_ギガドレイン_使用後に攻撃者のHPが回復する():
    """ギガドレイン: 与えたダメージの半分だけ攻撃者のHPを回復する（heal_ratio=0.5）。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["ギガドレイン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp > 1


def test_ギガドレイン_回復量が与ダメの半分になる():
    """ギガドレイン: 回復量は int(与えたダメージ * 0.5) で計算される。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["ギガドレイン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_damage(battle, 100)
    attacker.hp = 1
    t.run_move(battle, 0)
    # int(100 * 0.5) = 50
    assert attacker.hp == 1 + 50


def test_ぎんいろのかぜ_全能力1段階上昇が発動する():
    """ぎんいろのかぜ: 確率10%でA/B/C/D/Sが各1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["ぎんいろのかぜ"])],
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


def test_クイックターン_ダメージを与える():
    """クイックターン: 通常通りダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["クイックターン"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_クイックターン_ちょすいで無効化されると交代しない():
    """クイックターン: みずタイプ技のため、ちょすいで無効化されると交代も発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["クイックターン"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ラグラージ", ability_name="ちょすい")],
        accuracy=100,
    )
    player = battle.players[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp >= hp_before
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_クイックターン_まもるで防がれた場合は交代しない():
    """クイックターン: まもるで防がれた場合、ダメージも交代も発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["クイックターン"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    player = battle.players[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_クイックターン_命中しなかった場合は交代しない():
    """クイックターン: 命中しなかった場合、交代は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["クイックターン"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    player = battle.players[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_クイックターン_控えがいない場合は交代しない():
    """クイックターン: 控えに戦えるポケモンがいない場合、ダメージは与えるが交代は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["クイックターン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert battle.player_states[player].interrupt == Interrupt.NONE


def test_クイックターン_攻撃後に交代可能状態になる():
    """クイックターン: 攻撃後、控えがいれば PIVOT が設定され交代できる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["クイックターン"]), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    player = battle.players[0]
    t.run_move(battle, 0)
    assert battle.player_states[player].interrupt == Interrupt.PIVOT

    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)
    assert battle.actives[0].name == "ライチュウ"


def test_クイックターン_相手を倒した場合でも交代する():
    """クイックターン: 相手を倒した場合でも、使用者は交代可能状態になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["クイックターン"]), Pokemon("ライチュウ")],
        team1=[Pokemon("コイキング")],
        accuracy=100,
    )
    player = battle.players[0]
    battle.actives[1].hp = 1
    t.run_move(battle, 0)
    assert battle.actives[1].fainted
    assert battle.player_states[player].interrupt == Interrupt.PIVOT


def test_くさのちかい_威力80():
    """くさのちかい: 威力は80(第六世代以降)。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["くさのちかい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 80


def test_くさのちかい_追加効果なしでダメージのみ():
    """くさのちかい: 追加効果を持たず、通常通りダメージのみ与える。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["くさのちかい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_くさむすび_100kg以上200kg未満のとき威力100():
    """くさむすび: 相手の体重が100kg以上200kg未満のとき威力100。
    ユキノオー(135.5kg) → 威力100。
    """
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["くさむすび"])],
        team1=[Pokemon("ユキノオー")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 100


def test_くさむすび_10kg以上25kg未満のとき威力40():
    """くさむすび: 相手の体重が10kg以上25kg未満のとき威力40。
    コダック(19.6kg) → 威力40。
    """
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["くさむすび"])],
        team1=[Pokemon("コダック")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 40


def test_くさむすび_10kg未満のとき威力20():
    """くさむすび: 相手の体重が10kg未満のとき威力20。
    ピカチュウ(6.0kg) → 威力20。
    """
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["くさむすび"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 20


def test_くさむすび_200kg以上のとき威力120():
    """くさむすび: 相手の体重が200kg以上のとき威力120。
    カビゴン(460.0kg) → 威力120。
    """
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["くさむすび"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 120


def test_くさむすび_25kg以上50kg未満のとき威力60():
    """くさむすび: 相手の体重が25kg以上50kg未満のとき威力60。
    マリルリ(28.5kg) → 威力60。
    """
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["くさむすび"])],
        team1=[Pokemon("マリルリ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 60


def test_くさむすび_50kg以上100kg未満のとき威力80():
    """くさむすび: 相手の体重が50kg以上100kg未満のとき威力80。
    バクフーン(79.5kg) → 威力80。
    """
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["くさむすび"])],
        team1=[Pokemon("バクフーン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 80


def test_くさわけ_素早さ1段階上昇が発動する():
    """くさわけ: 命中時に使用者のSが1段階上昇する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["くさわけ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["spe"] == 1


def test_くちばしキャノン_ほのおタイプの相手はやけどにならない():
    """くちばしキャノン: 接触してきた相手がほのおタイプの場合、やけど耐性によりやけど状態にできない。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["くちばしキャノン"])],
        accuracy=100,
    )
    attacker_of_contact = battle.actives[0]
    battle.step()
    assert not attacker_of_contact.ailment.is_active


def test_くちばしキャノン_ぼうごパットを持つ相手はやけどにならない():
    """くちばしキャノン: 接触技の使用者がぼうごパットを持つ場合、接触反応効果である
    やけど付与は発動しない（ぼうごパットの発動メッセージも流れない仕様）。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"], item_name="ぼうごパット")],
        team1=[Pokemon("ピカチュウ", move_names=["くちばしキャノン"])],
        accuracy=100,
    )
    attacker_of_contact = battle.actives[0]
    battle.step()
    assert not attacker_of_contact.ailment.is_active


def test_くちばしキャノン_まひで行動不能でもやけどは発動する():
    """くちばしキャノン: 使用者がまひで行動できない場合でも、加熱自体は行動可否の判定とは
    独立して行われるため、技発動前に接触技を受けていればやけど効果は発動する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ケンタロス", move_names=["くちばしキャノン"])],
        accuracy=100,
    )
    attacker_of_contact = battle.actives[0]
    user = battle.actives[1]
    battle.ailment_manager.apply(user, "まひ")
    battle.test_option.trigger_ailment = True
    battle.step()
    assert battle.move_executor.action_success is False
    assert attacker_of_contact.ailment.name == "やけど"


def test_くちばしキャノン_みがわりで防いだ場合はやけどにならない():
    """くちばしキャノン: 使用者がみがわり状態のとき接触技をみがわりで防いだ場合、
    使用者自身はダメージを受けていない扱いとなりやけど効果は発動しない。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["くちばしキャノン"])],
        volatile1={"みがわり": 1},
        accuracy=100,
    )
    attacker_of_contact = battle.actives[0]
    battle.step()
    assert not attacker_of_contact.ailment.is_active


def test_くちばしキャノン_接触技を受けると攻撃者がやけどになる():
    """くちばしキャノン: 技が発動する前に接触技を受けると攻撃者をやけど状態にする。

    くちばしキャノン側（チームindex=1）は優先度-3で後攻。
    相手（チームindex=0）は先に接触技たいあたりで攻撃するため、
    ON_TRY_MOVE_1 の時点で contact_hitter が記録されており、やけどを付与する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", move_names=["くちばしキャノン"])],
        accuracy=100,
    )
    attacker_of_contact = battle.actives[0]
    battle.step()
    assert attacker_of_contact.ailment.name == "やけど"


def test_くちばしキャノン_相手の優先度がより低い場合はやけどにならない():
    """くちばしキャノン: 相手の技の優先度がくちばしキャノン(-3)より低い場合、
    使用者の加熱終了(攻撃実行)後に接触されるためやけど効果は発動しない。
    """
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ドラゴンテール"])],
        team1=[Pokemon("ピカチュウ", move_names=["くちばしキャノン"])],
        accuracy=100,
    )
    attacker_of_contact = battle.actives[0]
    battle.step()
    assert not attacker_of_contact.ailment.is_active


def test_くちばしキャノン_非接触技を受けてもやけどにならない():
    """くちばしキャノン: 非接触技を受けた場合はやけど状態にならない。

    相手が非接触技（10まんボルト）を使う場合は contact_hitter が記録されない。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
        team1=[Pokemon("ラプラス", move_names=["くちばしキャノン"])],
        accuracy=100,
    )
    attacker_of_special = battle.actives[0]
    battle.step()
    assert not attacker_of_special.ailment.is_active


def test_くらいつく_ちからずくでも威力上昇せず効果は発動する():
    """くらいつく: 効果は追加効果とみなされないため、ちからずくでも威力は上がらず効果は発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("カジリガメ", ability_name="ちからずく", move_names=["くらいつく"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096
    assert battle.actives[0].has_volatile("にげられない")
    assert battle.actives[1].has_volatile("にげられない")


def test_くらいつく_既ににげられない状態の場合双方ともにげられない状態にならない():
    """くらいつく: 相手がすでににげられない状態の場合、お互いに（再度）にげられない状態にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カジリガメ", move_names=["くらいつく"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"にげられない": 1},
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert not battle.actives[0].has_volatile("にげられない")


def test_くらいつく_相手がゴーストタイプの場合双方ともにげられない状態にならない():
    """くらいつく: 相手がゴーストタイプの場合、お互いににげられない状態にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カジリガメ", move_names=["くらいつく"])],
        team1=[Pokemon("ゲンガー")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert not battle.actives[0].has_volatile("にげられない")
    assert not battle.actives[1].has_volatile("にげられない")


def test_くらいつく_相手がりんぷんでも効果は発動する():
    """くらいつく: 効果は追加効果とみなされないため、相手の特性がりんぷんでも効果は発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("カジリガメ", move_names=["くらいつく"])],
        team1=[Pokemon("ピカチュウ", ability_name="りんぷん")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[0].has_volatile("にげられない")
    assert battle.actives[1].has_volatile("にげられない")


def test_くらいつく_相手と自分の両方をにげられない状態にする():
    """くらいつく: 命中時、相手と自分の両方をにげられない状態にする。"""
    battle = t.start_battle(
        team0=[Pokemon("カジリガメ", move_names=["くらいつく"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[0].has_volatile("にげられない")
    assert battle.actives[1].has_volatile("にげられない")


def test_くらいつく_相手にダメージを与える():
    """くらいつく: 物理あく技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カジリガメ", move_names=["くらいつく"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_くらいつく_相手をひんしにした場合使用者はにげられない状態にならない():
    """くらいつく: この技で相手をひんしにした場合、使用者はにげられない状態にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カジリガメ", move_names=["くらいつく"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    battle.actives[1].hp = 1
    t.run_move(battle, 0)
    assert battle.actives[1].fainted
    assert not battle.actives[0].has_volatile("にげられない")


def test_くらいつく_自分がゴーストタイプの場合双方ともにげられない状態にならない():
    """くらいつく: 自分（使用者）がゴーストタイプの場合、お互いににげられない状態にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["くらいつく"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert not battle.actives[0].has_volatile("にげられない")
    assert not battle.actives[1].has_volatile("にげられない")


def test_クラブハンマー_急所ランクが1():
    """クラブハンマー: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("キングラー", move_names=["クラブハンマー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_クラブハンマー_急所ランクが1_乱数大で急所なし():
    """クラブハンマー: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("キングラー", move_names=["クラブハンマー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


def test_クラブハンマー_相手にダメージを与える():
    """クラブハンマー: 追加効果なしの物理みず技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("キングラー", move_names=["クラブハンマー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_クリアスモッグ_クリアボディを無視してリセットする():
    """クリアスモッグ: 相手の特性クリアボディ（ランク低下防止）を無視してリセットする。"""
    battle = t.start_battle(
        team0=[Pokemon("ベトベトン", move_names=["クリアスモッグ"])],
        team1=[Pokemon("カビゴン", ability_name="クリアボディ")],
    )
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    t.run_move(battle, 0)
    assert defender.rank["atk"] == 0


def test_クリアスモッグ_すりぬけならみがわりを貫通してリセットする():
    """クリアスモッグ: 使用者がすりぬけ特性の場合、みがわりを無視してダメージとランクリセットが発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ベトベトン", ability_name="すりぬけ", move_names=["クリアスモッグ"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=50)
    defender.rank["atk"] = 2
    t.run_move(battle, 0)
    assert defender.has_volatile("みがわり")
    assert defender.rank["atk"] == 0


def test_クリアスモッグ_ダメージを与える():
    """クリアスモッグ: どく特殊・威力50のダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ベトベトン", move_names=["クリアスモッグ"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_クリアスモッグ_まもるで防がれるとリセットされない():
    """クリアスモッグ: まもるで防がれた場合、ダメージもランクリセットも発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ベトベトン", move_names=["クリアスモッグ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert defender.rank["atk"] == 2


def test_クリアスモッグ_みがわりに防がれるとリセットされない():
    """クリアスモッグ: みがわりに防がれた場合、実ダメージが0のためランクリセットは発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ベトベトン", move_names=["クリアスモッグ"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=50)
    defender.rank["atk"] = 2
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert defender.rank["atk"] == 2


def test_クリアスモッグ_相手の上がったランクをリセットする():
    """クリアスモッグ: ダメージを与えた相手の上がったランクを±0にリセットする。"""
    battle = t.start_battle(
        team0=[Pokemon("ベトベトン", move_names=["クリアスモッグ"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    defender.rank["atk"] = 2
    defender.rank["spe"] = 1
    t.run_move(battle, 0)
    assert defender.rank["atk"] == 0
    assert defender.rank["spe"] == 0


def test_クリアスモッグ_相手の下がったランクをリセットする():
    """クリアスモッグ: ダメージを与えた相手の下がったランクを±0にリセットする。"""
    battle = t.start_battle(
        team0=[Pokemon("ベトベトン", move_names=["クリアスモッグ"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    defender.rank["def"] = -2
    defender.rank["accuracy"] = -1
    t.run_move(battle, 0)
    assert defender.rank["def"] == 0
    assert defender.rank["accuracy"] == 0


def test_クリアスモッグ_自分のランクは変化しない():
    """クリアスモッグ: くろいきりと異なり、使用者自身のランクはリセットされない。"""
    battle = t.start_battle(
        team0=[Pokemon("ベトベトン", move_names=["クリアスモッグ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.rank["atk"] = 2
    t.run_move(battle, 0)
    assert attacker.rank["atk"] == 2


def test_クロスサンダー_クロスフレイムがまもるで防がれた場合威力は上がらない():
    """クロスサンダー: 直前のクロスフレイムがまもるで防がれた場合、命中していないため威力は上がらない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["クロスサンダー"])],
        team1=[Pokemon("カビゴン", move_names=["クロスフレイム"])],
        volatile0={"まもる": 1},
        accuracy=100,
    )
    t.run_move(battle, 1)  # 相手のクロスフレイムはまもるで防がれる
    t.run_move(battle, 0)  # 自分がクロスサンダーを使用する
    assert battle.damage_calculator.final_power == 100


def test_クロスサンダー_ターンをまたぐと効果は持続しない():
    """クロスサンダー: 前のターンにクロスフレイムが命中していても、ターンをまたぐと威力は上がらない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["クロスサンダー"])],
        team1=[Pokemon("カビゴン", move_names=["クロスフレイム"])],
        accuracy=100,
    )
    t.run_move(battle, 1)  # 相手がクロスフレイムを命中させる（このターン）
    battle.turn += 1  # 次のターンに進める
    t.run_move(battle, 0)  # 自分がクロスサンダーを使用する
    assert battle.damage_calculator.final_power == 100


def test_クロスサンダー_直前がクロスフレイム以外の技の場合威力は上がらない():
    """クロスサンダー: 直前に成功した技がクロスフレイムでない場合、威力は上がらない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["クロスサンダー"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    t.run_move(battle, 1)  # 相手がたいあたりを使用する
    t.run_move(battle, 0)  # 自分がクロスサンダーを使用する
    assert battle.damage_calculator.final_power == 100


def test_クロスサンダー_直前にクロスフレイムが命中すると威力2倍になる():
    """クロスサンダー: 同じターン中に直前でクロスフレイムが命中していた場合、威力が2倍(200)になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["クロスサンダー"])],
        team1=[Pokemon("カビゴン", move_names=["クロスフレイム"])],
        accuracy=100,
    )
    t.run_move(battle, 1)  # 相手がクロスフレイムを命中させる
    t.run_move(battle, 0)  # 自分がクロスサンダーを使用する
    assert battle.damage_calculator.final_power == 200


def test_クロスサンダー_直前に何も成功していない場合威力は上がらない():
    """クロスサンダー: このターン中に何も技が成功していない場合、威力は基本値100のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["クロスサンダー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 100


def test_クロスチョップ_急所ランクが1():
    """クロスチョップ: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["クロスチョップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_クロスチョップ_急所ランクが1_乱数大で急所なし():
    """クロスチョップ: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["クロスチョップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


def test_クロスチョップ_相手にダメージを与える():
    """クロスチョップ: 追加効果なしの物理かくとう技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["クロスチョップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_クロスフレイム_こおり状態で使うと解凍されて攻撃できる():
    """クロスフレイム: こおり状態でも使用でき、使うと解凍される。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["クロスフレイム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # こおり状態を付与してから使用
    t.apply_ailment(battle, 0, "こおり")
    assert attacker.ailment.name == "こおり"
    hp_before = defender.hp
    t.run_move(battle, 0)
    # こおりが解除されてダメージを与えられる
    assert not attacker.ailment.is_active
    assert battle.move_executor.move_success is True
    assert defender.hp < hp_before


def test_クロスポイズン_どくが発動する():
    """クロスポイズン: 10%でどくを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["クロスポイズン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "どく"


def test_クロスポイズン_急所ランクが1():
    """クロスポイズン: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["クロスポイズン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_クロスポイズン_急所ランクが1_乱数大で急所なし():
    """クロスポイズン: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["クロスポイズン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


def test_クロロブラスト_いしあたまで反動を受けない():
    """クロロブラスト: 特性いしあたまでも反動ダメージを無効化できる
    （てっていこうせん・ビックリヘッドはいしあたまでは防げないが、本技は防げる点に注意）。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", ability_name="いしあたま", move_names=["クロロブラスト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_before
    assert defender.hp < defender.max_hp


def test_クロロブラスト_マジックガードで反動を受けない():
    """クロロブラスト: 特性マジックガードでは反動ダメージを受けない。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", ability_name="マジックガード", move_names=["クロロブラスト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_before
    assert defender.hp < defender.max_hp


def test_クロロブラスト_まもるで防がれると反動を受けない():
    """クロロブラスト: まもるで防がれた場合、反動ダメージを受けない。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["クロロブラスト"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_before


def test_クロロブラスト_命中して実ダメージ0でも反動を受ける():
    """クロロブラスト: こらえる等で実ダメージが0でも、技が成功していれば反動ダメージを受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["クロロブラスト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender.hp = 1
    battle.volatile_manager.apply(defender, "こらえる")
    t.fix_damage(battle, 9999)
    expected_cost = (attacker.max_hp + 1) // 2
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert defender.hp == 1
    assert attacker.hp == hp_before - expected_cost


def test_クロロブラスト_命中しなかったとき反動を受けない():
    """クロロブラスト: 命中しなかった場合、反動ダメージを受けない。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["クロロブラスト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_before


def test_クロロブラスト_命中時に最大HPの半分切り上げの反動を受ける():
    """クロロブラスト: 命中後に自分の最大HPの1/2（切り上げ）を反動ダメージとして受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["クロロブラスト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert attacker.max_hp % 2 == 1  # 前提: 最大HPが奇数であること（切り上げ確認のため）
    expected_cost = (attacker.max_hp + 1) // 2
    floor_cost = attacker.max_hp // 2
    assert expected_cost != floor_cost
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_cost


def test_クロロブラスト_相手へのダメージ適用後に反動を受ける():
    """クロロブラスト: 反動は相手へのダメージ適用より後に処理されるため、反動でHPが0になっても
    相手への攻撃自体は成立している。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["クロロブラスト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 反動でちょうど0になるように設定
    attacker.hp = (attacker.max_hp + 1) // 2
    t.run_move(battle, 0)
    assert attacker.hp == 0
    assert defender.hp < defender.max_hp


def test_グラススライダー_グラスフィールドでなければ優先度は0():
    """グラススライダー: グラスフィールドでなければ優先度は0のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("ゴリランダー", move_names=["グラススライダー"])],
        team1=[Pokemon("カビゴン")],
    )
    assert 0 == t.calc_move_priority(battle, 0)


def test_グラススライダー_グラスフィールドでも浮いていると優先度は0のまま():
    """グラススライダー: グラスフィールドでも使用者が浮いていれば優先度は上がらない。"""
    battle = t.start_battle(
        team0=[Pokemon("ゴリランダー", ability_name="ふゆう", move_names=["グラススライダー"])],
        team1=[Pokemon("カビゴン")],
        terrain=("グラスフィールド", 5),
    )
    assert 0 == t.calc_move_priority(battle, 0)


def test_グラススライダー_グラスフィールドで優先度が1になる():
    """グラススライダー: グラスフィールドかつ接地時は優先度が+1される。"""
    battle = t.start_battle(
        team0=[Pokemon("ゴリランダー", move_names=["グラススライダー"])],
        team1=[Pokemon("カビゴン")],
        terrain=("グラスフィールド", 5),
    )
    assert 1 == t.calc_move_priority(battle, 0)


def test_グラススライダー_相手にダメージを与える():
    """グラススライダー: 追加効果なしの物理くさ技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ゴリランダー", move_names=["グラススライダー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_グロウパンチ_攻撃1段階上昇が発動する():
    """グロウパンチ: 命中時に使用者のAが1段階上昇する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["グロウパンチ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["atk"] == 1


def test_けたぐり_10kg未満のとき威力20():
    """けたぐり: 相手の体重が10kg未満のとき威力20。
    ピカチュウ(6.0kg) → 威力20。
    """
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["けたぐり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 20


def test_けたぐり_200kg以上のとき威力120():
    """けたぐり: 相手の体重が200kg以上のとき威力120。
    カビゴン(460.0kg) → 威力120。
    """
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["けたぐり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 120


def test_げきりん_カウント終了後にこんらんが付与される():
    """げきりん: カウントが0になった後にこんらん状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー", move_names=["げきりん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "あばれる", count=1, source=attacker, move_name="げきりん")
    t.run_move(battle, 0)
    assert not attacker.has_volatile("あばれる")
    assert attacker.has_volatile("こんらん")


def test_げきりん_初回命中時にあばれる揮発状態が付与される():
    """げきりん: 初回命中時にあばれる揮発状態（強制行動）が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー", move_names=["げきりん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("あばれる")


def test_ゲップ_きのみ未食では失敗する():
    """ゲップ: ate_berry=False の状態で使うと失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("アーボック", move_names=["ゲップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert not attacker.ate_berry
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False


def test_ゲップ_きのみ消費後は発動する():
    """ゲップ: きのみを食べて ate_berry=True になった後は発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("アーボック", item_name="オレンのみ", move_names=["ゲップ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # きのみを消費してate_berryをセットする
    battle.item_manager.consume_item(attacker)
    assert attacker.ate_berry
    defender_hp_before = battle.actives[1].hp
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True
    assert battle.actives[1].hp < defender_hp_before


def test_ゲップ_やきつくすで焼かれたきのみでは使えない():
    """ゲップ: やきつくすで相手のきのみが焼かれても ate_berry はセットされない。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["やきつくす"])],
        team1=[Pokemon("アーボック", item_name="オレンのみ", move_names=["ゲップ"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    # やきつくすでアーボックのきのみを焼く
    t.run_move(battle, 0)
    assert not defender.item.is_berry()
    assert not defender.ate_berry
    # アーボックがゲップを使っても失敗する
    t.run_move(battle, 1)
    assert battle.move_executor.move_success is False


def test_ゲップ_交代後も使えること():
    """ゲップ: きのみを食べた後に交代しても ate_berry はリセットされない。"""
    battle = t.start_battle(
        team0=[
            Pokemon("アーボック", item_name="オレンのみ", move_names=["ゲップ"]),
            Pokemon("カビゴン", move_names=["ゲップ"]),
        ],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    # きのみを消費してate_berryをセットする
    battle.item_manager.consume_item(attacker)
    assert attacker.ate_berry
    # 控えのカビゴンと交代
    t.run_switch(battle, 0, 1)
    # アーボックに戻す
    t.run_switch(battle, 0, 0)
    assert battle.actives[0] is attacker
    assert attacker.ate_berry
    defender_hp_before = battle.actives[1].hp
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is True
    assert battle.actives[1].hp < defender_hp_before


def test_げんしのちから_全能力1段階上昇が発動する():
    """げんしのちから: 確率10%でA/B/C/D/Sが各1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("プテラ", move_names=["げんしのちから"])],
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


def test_こうげきしれい_急所ランクが1():
    """こうげきしれい: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["こうげきしれい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_こうげきしれい_急所ランクが1_乱数大で急所なし():
    """こうげきしれい: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["こうげきしれい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


def test_こうげきしれい_相手にダメージを与える():
    """こうげきしれい: 追加効果なしの物理むし技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["こうげきしれい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_こうそくスピン_おんみつマントの相手でも素早さが上昇し場の状態を解除する():
    """こうそくスピン: 相手がおんみつマントを持っていても解除・素早さ上昇は発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こうそくスピン"])],
        team1=[Pokemon("カビゴン", item_name="おんみつマント")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    side = battle.get_side(attacker)
    side.apply("まきびし", count=1)
    t.run_move(battle, 0)
    assert not side.get("まきびし").is_active
    assert attacker.rank["spe"] == 1


def test_こうそくスピン_ちからずくでは場の状態解除も素早さ上昇も発動しない():
    """こうそくスピン: 使用者がちからずくの場合、解除・素早さ上昇のいずれも発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからずく", move_names=["こうそくスピン"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    side = battle.get_side(attacker)
    side.apply("まきびし", count=1)
    battle.volatile_manager.apply(attacker, "バインド", count=4, source=battle.actives[1])
    t.run_move(battle, 0)
    assert side.get("まきびし").is_active
    assert attacker.has_volatile("バインド")
    assert attacker.rank["spe"] == 0


def test_こうそくスピン_バインドを解除する():
    """こうそくスピン: 命中時に使用者のバインド状態を解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こうそくスピン"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "バインド", count=4, source=battle.actives[1])
    t.run_move(battle, 0)
    assert not attacker.has_volatile("バインド")


def test_こうそくスピン_まきびしを解除する():
    """こうそくスピン: 命中時に使用者のサイドのまきびしを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こうそくスピン"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    side = battle.get_side(attacker)
    side.apply("まきびし", count=1)
    t.run_move(battle, 0)
    assert not side.get("まきびし").is_active


def test_こうそくスピン_やどりぎのタネを解除する():
    """こうそくスピン: 命中時に使用者のやどりぎのタネ状態を解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こうそくスピン"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "やどりぎのタネ", source=battle.actives[1])
    t.run_move(battle, 0)
    assert not attacker.has_volatile("やどりぎのタネ")


def test_こうそくスピン_素早さ1段階上昇が発動する():
    """こうそくスピン: 命中時に使用者のSが1段階上昇する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こうそくスピン"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["spe"] == 1


def test_こおりのいぶき_確定急所():
    """こおりのいぶき: 急所ランク3のため乱数によらず常に急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["こおりのいぶき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、急所は確定ランク3で必ず発生
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_こおりのキバ_こおりが発動する():
    """こおりのキバ: 10%でこおりを付与する（ひるみとは独立判定）。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", move_names=["こおりのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "こおり"


def test_こおりのキバ_こおりとひるみが同時に発動する():
    """こおりのキバ: 2つの追加効果はそれぞれ独立に判定されるため、同時に発動しうる。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", move_names=["こおりのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    defender = battle.actives[1]
    assert defender.ailment.name == "こおり"
    assert defender.has_volatile("ひるみ")


def test_こおりのキバ_ひるみが発動する():
    """こおりのキバ: 10%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", move_names=["こおりのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_こおりのつぶて_相手にダメージを与える():
    """こおりのつぶて: 優先度+1の先制物理技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["こおりのつぶて"])],
        team1=[Pokemon("フリーザー")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_こおりのつぶて_素早さが低い側でも優先度により先制する():
    """こおりのつぶて: 優先度+1のため、素早さが低いポケモンでも先制して行動する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["こおりのつぶて"])],
        team1=[Pokemon("フリーザー", move_names=["たいあたり"])],
        accuracy=100,
    )
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[0]


def test_こがらしあらし_あめ中は必中になる():
    """こがらしあらし: あめ天候中は命中率80でも通常なら外れる乱数で命中する。

    こがらしあらしの命中率は80。random.random()=0.9 のとき 100*0.9=90>80 で本来は外れるが、
    あめ中はON_MODIFY_ACCURACYでNoneが返り必中になるため、命中してHPが減る。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こがらしあらし"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    # random.random()=0.9 は命中率80未満ではない（90>80）ので通常は外れる
    battle.random.random = lambda: 0.9
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_こがらしあらし_すばやさが下がる():
    """こがらしあらし: 30%で相手のすばやさランクを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["こがらしあらし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["spe"] == -1


def test_こごえるかぜ_すばやさが下がる():
    """こごえるかぜ: 100%の確率で相手のすばやさランクを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["こごえるかぜ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["spe"] == -1


def test_こごえるかぜ_ちからずくで威力上昇しすばやさダウンは発動しない():
    """こごえるかぜ: ちからずく使用時は威力が1.3倍になる代わりにすばやさダウンが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", ability_name="ちからずく", move_names=["こごえるかぜ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier
    assert battle.actives[1].rank["spe"] == 0


def test_こごえるかぜ_相手にダメージを与える():
    """こごえるかぜ: 相手にダメージを与える特殊技。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["こごえるかぜ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_こごえるせかい_すばやさが下がる():
    """こごえるせかい: 100%の確率で相手のすばやさランクを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["こごえるせかい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["spe"] == -1


def test_こごえるせかい_ちからずくで威力上昇しすばやさダウンは発動しない():
    """こごえるせかい: ちからずく使用時は威力が1.3倍になる代わりにすばやさダウンが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", ability_name="ちからずく", move_names=["こごえるせかい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier
    assert battle.actives[1].rank["spe"] == 0


def test_こごえるせかい_相手にダメージを与える():
    """こごえるせかい: 相手にダメージを与える特殊技。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["こごえるせかい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_こなゆき_こおりが発動する():
    """こなゆき: 10%でこおりを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["こなゆき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "こおり"


def test_このは_相手にダメージを与える():
    """このは: 追加効果なしの物理くさ技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["このは"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ころがる_5回目の命中で強制行動が終了する():
    """ころがる: countが4の状態で命中すると揮発状態が解除され、強制行動が終了する。"""
    battle = t.start_battle(
        team0=[Pokemon("イシツブテ", move_names=["ころがる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "ころがる", count=4, source=attacker, move_name="ころがる")
    t.run_move(battle, 0)
    assert not attacker.has_volatile("ころがる")


def test_ころがる_おやこあいでは連続攻撃にならない():
    """ころがる: おやこあいを持っていても2ヒットにならず、揮発状態のcountは1のまま。"""
    battle = t.start_battle(
        team0=[Pokemon("イシツブテ", ability_name="おやこあい", move_names=["ころがる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hits_taken == 1
    assert attacker.volatiles["ころがる"].count == 1


def test_ころがる_初回命中時にころがる揮発状態が付与される():
    """ころがる: 初回命中時にころがる揮発状態（強制行動・count=1）が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("イシツブテ", move_names=["ころがる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("ころがる")
    assert attacker.volatiles["ころがる"].count == 1


def test_ころがる_命中するたびに威力が2倍になる():
    """ころがる: 揮発状態のcountに応じて威力補正が2^count倍になる（count=2なら4倍）。"""
    battle = t.start_battle(
        team0=[Pokemon("イシツブテ", move_names=["ころがる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "ころがる", count=2, source=attacker, move_name="ころがる")
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096 * 4


def test_ころがる_外れると強制行動が解除される():
    """ころがる: 継続中に技が外れると、ターン終了時に強制行動状態が解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("イシツブテ", move_names=["ころがる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=0,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "ころがる", count=2, source=attacker, move_name="ころがる")
    t.run_move(battle, 0)
    assert attacker.has_volatile("ころがる")  # ミス直後は揮発状態が残っている
    t.end_turn(battle)
    assert not attacker.has_volatile("ころがる")


def test_ころがる_技固定():
    """ころがる: 強制行動中はCommand.FORCEDが返り、解決後の技がころがるになる。"""
    battle = t.start_battle(
        team0=[Pokemon("イシツブテ", move_names=["ころがる", "たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "ころがる", count=1, source=attacker, move_name="ころがる")
    with battle.phase_context("action"):
        assert battle.get_available_commands(battle.players[0]) == [Command.FORCED]
    move = battle.command_manager.resolve_move_from_command(battle.players[0], Command.FORCED)
    assert move.name == "ころがる"


def test_ころがる_継続中の命中でcountが増加する():
    """ころがる: 揮発状態がある状態で命中すると、countが+1される。"""
    battle = t.start_battle(
        team0=[Pokemon("イシツブテ", move_names=["ころがる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "ころがる", count=1, source=attacker, move_name="ころがる")
    t.run_move(battle, 0)
    assert attacker.has_volatile("ころがる")
    assert attacker.volatiles["ころがる"].count == 2


def test_こんげんのはどう_相手にダメージを与える():
    """こんげんのはどう: 追加効果なしの特殊みず技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("グラードン", move_names=["こんげんのはどう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_こんらん_マイペース持ちには付与されない():
    """こんらん系追加効果: マイペース特性を持つ相手はこんらん状態にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かかとおとし"])],
        team1=[Pokemon("カビゴン", ability_name="マイペース")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("こんらん")


def test_こんらん_ミストフィールド中は付与されない():
    """こんらん系追加効果: ミストフィールド展開中は接地した相手がこんらん状態にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["かかとおとし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
        terrain=("ミストフィールド", 5),
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("こんらん")


def test_コールドフレア_やけどが発動する():
    """コールドフレア: 30%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("キュレム", move_names=["コールドフレア"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_ゴッドバード_ひるみが発動する():
    """ゴッドバード: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ファイヤー", move_names=["ゴッドバード"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_ゴーストダイブ_2ターンで攻撃する():
    """1ターン目はダメージを与えず、2ターン目にダメージを与えて揮発状態が解除される"""
    battle = t.start_battle(
        # ノーマルタイプはゴースト無効なのでどくタイプを使用
        team0=[Pokemon("ゲンガー", move_names=["ゴーストダイブ"])],
        team1=[Pokemon("ドガース")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp

    # 1ターン目: 揮発状態付与のみ、ダメージなし
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert battle.actives[0].has_volatile("シャドーダイブ")

    # 2ターン目: ダメージあり、揮発状態解除
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert not battle.actives[0].has_volatile("シャドーダイブ")


def test_ゴーストダイブ_まもる中の相手にダメージを与えられる():
    """ゴーストダイブはまもる状態を貫通する（unprotectable ラベル）"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["ゴーストダイブ"])],
        team1=[Pokemon("ドガース")],
    )
    defender = battle.actives[1]
    initial_hp = defender.hp
    battle.volatile_manager.apply(defender, "まもる", count=1)
    # 溜めターン
    t.run_move(battle, 0)
    assert battle.actives[0].has_volatile("シャドーダイブ")
    # 攻撃ターン（まもる状態の相手に攻撃）
    t.run_move(battle, 0)
    assert not battle.actives[0].has_volatile("シャドーダイブ")
    assert battle.move_executor.move_success
    assert defender.hp < initial_hp


def test_ゴールドラッシュ_特攻1段階低下が発動する():
    """ゴールドラッシュ: 命中時に使用者のCが1段階低下する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ゴールドラッシュ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["spa"] == -1
