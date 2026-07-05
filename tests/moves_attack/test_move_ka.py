"""攻撃技ハンドラの単体テスト（か行）。"""

import pytest
from jpoke import Pokemon
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


def test_かみなり_まひが発動する():
    """かみなり: 10%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かみなり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


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


@pytest.mark.parametrize(
    ("attacker_hp", "defender_hp", "expected_damage"),
    [
        (30, 100, 70),
        (80, 60, 0),
    ],
)
def test_がむしゃら_相手HPとの差分ダメージ(attacker_hp: int, defender_hp: int, expected_damage: int):
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
    """きしかいせい: HP 10% 付近（X=4）のとき威力100（X=5で100、X=4で150）。
    カビゴン max_hp=235, hp=24 → x=4 → 威力150。
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


def test_クロロブラスト_HP消費が最大HPの半分である():
    """クロロブラスト: 使用前に自分の最大HPの1/2を消費する。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["クロロブラスト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    expected_cost = max(1, attacker.max_hp // 2)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp == hp_before - expected_cost


def test_クロロブラスト_HP消費後HP0でも相手にダメージを与える():
    """クロロブラスト: HP消費後にHP0になっても攻撃は相手に届く。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["クロロブラスト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # HP消費でちょうど0になるように設定
    attacker.hp = attacker.max_hp // 2
    t.run_move(battle, 0)
    assert attacker.hp == 0
    assert defender.hp < defender.max_hp


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
    """こおりのキバ: 10%でこおりかひるみのどちらか一方を付与する。ランダム固定でこおりを選択。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", move_names=["こおりのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    # random.random() < 0.5 でこおり、>= 0.5 でひるみを選択するため、0.0 に固定してこおりを確定
    battle.random.random = lambda: 0.0
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "こおり"


def test_こおりのキバ_ひるみが発動する():
    """こおりのキバ: 単一乱数で 0.5<=r<1.0 の場合はひるみを付与する（こおりとの排他制御）。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", move_names=["こおりのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    # r=0.7 のとき base*0.5=0.5 を超えるのでこおりには進まず、r<base=1.0 でひるみを選択
    battle.random.random = lambda: 0.7
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")
    assert not battle.actives[1].ailment.is_active


def test_こおりのキバ_同時発動しない():
    """こおりのキバ: こおりとひるみは排他的で、同時に付与されることはない。"""
    battle = t.start_battle(
        team0=[Pokemon("アルセウス", move_names=["こおりのキバ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    battle.random.random = lambda: 0.0
    t.run_move(battle, 0)
    defender = battle.actives[1]
    # こおりが付いていればひるみはない
    assert defender.ailment.name == "こおり"
    assert not defender.has_volatile("ひるみ")


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
