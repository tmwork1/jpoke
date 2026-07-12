"""攻撃技ハンドラの単体テスト（ま行）。"""

from jpoke import Pokemon
from jpoke.data.move import MOVES
from .. import test_utils as t


def test_じたばた_HP1のとき威力200():
    """じたばた: HP が1（X=0）のとき最大威力200。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じたばた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 200


def test_じたばた_HP極少のとき威力150():
    """じたばた: HP が極少（X=2）のとき威力150。
    カビゴン max_hp=235, hp=10 → x=2 → 威力150。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じたばた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 10  # x = 10*48//235 = 2 → 威力150
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 150


def test_じたばた_HP満タンのとき威力20():
    """じたばた: HPが満タン（X=48 ≥ 33）のとき威力20。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じたばた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp  # 満タン
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 20


def test_じたばた_HP約10パーセントのとき威力100():
    """じたばた: HP 10% 付近（X=5）のとき威力100。
    カビゴン max_hp=235, hp=26 → x=5 → 威力100（X=4になると威力150）。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じたばた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 26  # x = 26*48//235 = 5 → 威力100
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 100


def test_じたばた_HP約35パーセントのとき威力80():
    """じたばた: HP 35% 付近（X=16）のとき威力80。
    カビゴン max_hp=235, hp=82 → x=16 → 威力80。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じたばた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 82  # x = 82*48//235 = 16 → 威力80
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 80


def test_じたばた_HP約68パーセントのとき威力40():
    """じたばた: HP 68% 付近（X=32）のとき威力40。
    カビゴン max_hp=235, hp=160 → x=32 → 威力40。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じたばた"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 160  # x = 160*48//235 = 32 → 威力40
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 40


def test_ついばむ_きのみを奪って攻撃者がHP回復する():
    """ついばむ: defenderのオボンのみを奪い、attackerがHP回復する（むしくいと同一効果）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピジョット", move_names=["ついばむ"])],
        team1=[Pokemon("カビゴン", item_name="オボンのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.hp = 1
    t.run_move(battle, 0)
    # attackerがオボンのみを得て発動し、HPが回復している
    assert attacker.hp > 1
    # defenderはオボンのみを失っている
    assert not defender.has_item()


def test_まきつく_ダメージを与える():
    """まきつく: 命中時に相手にダメージを与える物理ノーマル技。"""
    battle = t.start_battle(
        team0=[Pokemon("アーボック", move_names=["まきつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_まきつく_バインド中はターン終了時にダメージを受ける():
    """まきつく: バインド状態のターン終了時に相手が最大HPの1/8のダメージを受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("アーボック", move_names=["まきつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    hp_after_attack = defender.hp
    t.end_turn(battle)
    expected_damage = defender.max_hp // 8
    assert defender.hp == hp_after_attack - expected_damage


def test_まきつく_命中後にバインド状態になる():
    """まきつく: 命中時に相手がバインド揮発状態になり交代不能になる。"""
    battle = t.start_battle(
        team0=[Pokemon("アーボック", move_names=["まきつく"]), Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_volatile("バインド")
    assert not t.can_switch(battle, 1)


def test_マグマストーム_ダメージを与える():
    """マグマストーム: 命中時に相手にダメージを与える特殊ほのお技。"""
    battle = t.start_battle(
        team0=[Pokemon("ヒードラン", move_names=["マグマストーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_マグマストーム_バインド中はターン終了時にダメージを受ける():
    """マグマストーム: バインド状態のターン終了時に相手が最大HPの1/8のダメージを受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("ヒードラン", move_names=["マグマストーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    hp_after_attack = defender.hp
    t.end_turn(battle)
    expected_damage = defender.max_hp // 8
    assert defender.hp == hp_after_attack - expected_damage


def test_マグマストーム_命中後にバインド状態になる():
    """マグマストーム: 命中時に相手がバインド揮発状態になり交代不能になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ヒードラン", move_names=["マグマストーム"]), Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_volatile("バインド")
    assert not t.can_switch(battle, 1)


def test_マジカルアクセル_こんらんが発動する():
    """マジカルアクセル: 30%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["マジカルアクセル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_マジカルアクセル_確率外れでこんらんが発動しない():
    """マジカルアクセル: 確率が外れたとき（secondary_chance=0.0）こんらんを付与しない。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["マジカルアクセル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("こんらん")


def test_マジカルシャイン_相手にダメージを与える():
    """マジカルシャイン: 追加効果なしの特殊フェアリー技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ニンフィア", move_names=["マジカルシャイン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_マジカルフレイム_secondary_effectフラグを持つ():
    """マジカルフレイム: ちからずくとの相互作用のためsecondary_effectフラグを持つこと。"""
    move_data = MOVES["マジカルフレイム"]
    assert "secondary_effect" in move_data.flags


def test_マジカルフレイム_ちからずくで威力上昇しとくこう低下は発動しない():
    """マジカルフレイム: ちからずく使用時は威力が1.3倍になる代わりに、とくこう低下が発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", ability_name="ちからずく", move_names=["マジカルフレイム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier
    assert battle.actives[1].boosts["spa"] == 0


def test_マジカルフレイム_とくこう1段階低下が発動する():
    """マジカルフレイム: 100%の確率で相手のとくこうを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["マジカルフレイム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].boosts["spa"] == -1


def test_マジカルリーフ_相手にダメージを与える():
    """マジカルリーフ: 追加効果なしの特殊くさ技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["マジカルリーフ"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_マジカルリーフ_相手の回避率が高くても必ず命中する():
    """マジカルリーフ: 自分の命中率、相手の回避率に関係なく必ず命中する。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギバナ", move_names=["マジカルリーフ"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"evasion": 6}, source=defender)
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_マッドショット_すばやさ低下が発動する():
    """マッドショット: 100%の確率で相手のすばやさを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ヌマクロー", move_names=["マッドショット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].boosts["spe"] == -1


def test_マッドショット_ちからずくで威力上昇しすばやさ低下は発動しない():
    """マッドショット: ちからずく使用時は威力が1.3倍になる代わりに、すばやさ低下が発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ヌマクロー", ability_name="ちからずく", move_names=["マッドショット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier
    assert battle.actives[1].boosts["spe"] == 0


def test_マッハパンチ_相手にダメージを与える():
    """マッハパンチ: 優先度+1の先制物理技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["マッハパンチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_マッハパンチ_素早さで劣っていても先制する():
    """マッハパンチ: 優先度+1のため、素早さで劣っていても相手より先に行動できる。

    カビゴン（素早さで劣る）がマッハパンチを使い、
    ピカチュウ（素早さで勝る）が10まんボルトを使う場合、
    優先度の高いマッハパンチが先に発動しHP1のピカチュウを先に倒すため、
    ピカチュウは行動できずカビゴンはダメージを受けない。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["マッハパンチ"])],
        team1=[Pokemon("ピカチュウ", move_names=["10まんボルト"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender.hp = 1
    attacker_hp_before = attacker.hp
    battle.step()
    assert not defender.alive
    assert attacker.hp == attacker_hp_before


def test_まとわりつく_ダメージを与える():
    """まとわりつく: 命中時に相手にダメージを与える特殊むし技。"""
    battle = t.start_battle(
        team0=[Pokemon("アリアドス", move_names=["まとわりつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_まとわりつく_バインド中はターン終了時にダメージを受ける():
    """まとわりつく: バインド状態のターン終了時に相手が最大HPの1/8のダメージを受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("アリアドス", move_names=["まとわりつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    hp_after_attack = defender.hp
    t.end_turn(battle)
    expected_damage = defender.max_hp // 8
    assert defender.hp == hp_after_attack - expected_damage


def test_まとわりつく_命中後にバインド状態になる():
    """まとわりつく: 命中時に相手がバインド揮発状態になり交代不能になる。"""
    battle = t.start_battle(
        team0=[Pokemon("アリアドス", move_names=["まとわりつく"]), Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_volatile("バインド")
    assert not t.can_switch(battle, 1)


def test_ミストバースト_HP消費後も攻撃が相手に届く():
    """ミストバースト: ON_PAY_HPはヒット処理より前に発火するため、HP0でも攻撃が相手に届く。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミストバースト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_ミストバースト_しめりけ持ちには技が失敗する():
    """ミストバースト: labels=["explosion"]のため、しめりけ持ちには技が失敗する。ON_PAY_HPは発火しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミストバースト"])],
        team1=[Pokemon("ニョロモ", ability_name="しめりけ")],
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert battle.move_executor.move_success is False
    assert attacker.hp == hp_before


def test_ミストバースト_フィールドなしのとき威力補正なし():
    """ミストバースト: ミストフィールドが発動していない場合、威力補正はない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミストバースト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ミストバースト_ミストフィールドかつ自分接地で威力1_5倍になる():
    """ミストバースト: 使用者がミストフィールドの効果を受けている場合、威力が1.5倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミストバースト"])],
        team1=[Pokemon("カビゴン")],
        terrain=("ミストフィールド", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144


def test_ミストバースト_使用後に攻撃者がひんしになる():
    """ミストバースト: ON_PAY_HPで現在HPを全消費し、技使用後に使用者がひんし状態になる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミストバースト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == 0
    assert not attacker.alive


def test_ミストバースト_自分が浮遊している場合は威力補正が乗らない():
    """ミストバースト: ミストフィールド中でも自分が浮いている場合、地面にいないため威力補正は乗らない。"""
    battle = t.start_battle(
        team0=[Pokemon("ロトム", ability_name="ふゆう", move_names=["ミストバースト"])],
        team1=[Pokemon("カビゴン")],
        terrain=("ミストフィールド", 5),
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_ミストボール_ちからずくで威力上昇しとくこう低下は発動しない():
    """ミストボール: ちからずく使用時は威力が1.3倍になる代わりに、とくこう低下が発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ラティアス", ability_name="ちからずく", move_names=["ミストボール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier
    assert battle.actives[1].boosts["spa"] == 0


def test_ミストボール_とくこう低下が発動する():
    """ミストボール: 50%の確率で相手のとくこうを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ラティアス", move_names=["ミストボール"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].boosts["spa"] == -1


def test_ミストボール_ぼうだん持ちには技が無効化される():
    """ミストボール: 弾のわざのため、特性『ぼうだん』所持者には無効化される。"""
    battle = t.start_battle(
        team0=[Pokemon("ラティアス", move_names=["ミストボール"])],
        team1=[Pokemon("カビゴン", ability_name="ぼうだん")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_みずあめボム_あめまみれでターンごとに素早さが低下する():
    """みずあめボム: あめまみれ状態のポケモンはターン終了時に素早さが1段階下がる。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["みずあめボム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_volatile("あめまみれ")
    t.end_turn(battle)
    # あめまみれのターン終了処理でSが1段階下がる
    assert defender.boosts["spe"] == -1


def test_みずあめボム_あめまみれ揮発状態が付与される():
    """みずあめボム: 100%の確率で相手をあめまみれ揮発状態（3ターン）にする。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["みずあめボム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("あめまみれ")


def test_みずしゅりけん_相手にダメージを与える():
    """みずしゅりけん: 優先度+1の先制特殊技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲッコウガ", move_names=["みずしゅりけん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_みずしゅりけん_複数ヒットする():
    """みずしゅりけん: 2～5回連続でヒットする複数ヒット技である。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲッコウガ", move_names=["みずしゅりけん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    assert 2 <= hit_count <= 5


def test_みずでっぽう_相手にダメージを与える():
    """みずでっぽう: 追加効果のない通常攻撃技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_みずのちかい_威力80():
    """みずのちかい: 威力は80(第六世代以降)。"""
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", move_names=["みずのちかい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 80


def test_みずのちかい_追加効果なしでダメージのみ():
    """みずのちかい: 追加効果を持たず、通常通りダメージのみ与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", move_names=["みずのちかい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_みずのはどう_こんらんが発動する():
    """みずのはどう: 20%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", move_names=["みずのはどう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_みだれづき_相手にダメージを与える():
    """みだれづき: 追加効果のない通常攻撃技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["みだれづき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_みだれづき_複数ヒットする():
    """みだれづき: 2～5回連続でヒットする複数ヒット技である。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["みだれづき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    assert 2 <= hit_count <= 5


def test_みだれひっかき_相手にダメージを与える():
    """みだれひっかき: ヒットした分だけ相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["みだれひっかき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_みだれひっかき_複数ヒットする():
    """みだれひっかき: 2～5回連続でヒットする複数ヒット技である。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["みだれひっかき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    assert 2 <= hit_count <= 5


def test_みねうち_HP1のとき_ダメージが0になる():
    """みねうち: 相手のHPがすでに1のとき、ダメージ0で倒さない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["みねうち"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = 1
    t.run_move(battle, 0)
    assert defender.hp == 1


def test_みねうち_HP1以上の相手に使うと必ずHP1を残す():
    """みねうち: 与えるダメージを defender.hp - 1 に制限して必ずHP1を残す。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["みねうち"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # 大きなダメージを固定して、実際にはHP-1に抑えられることを確認
    t.fix_damage(battle, defender.max_hp * 10)
    t.run_move(battle, 0)
    assert defender.hp == 1


def test_みねうち_防御側が素早くてもがんじょうは発動しない():
    """みねうち: HP満タンの相手をHP1にする際、みねうちの効果が優先されて
    がんじょうは発動しない（防御側が攻撃側より素早い場合でも成立することを確認）。"""
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", move_names=["みねうち"])],
        team1=[Pokemon("サンダース", ability_name="がんじょう")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.fix_damage(battle, defender.max_hp * 10)
    t.run_move(battle, 0)
    assert defender.hp == 1
    # がんじょうが発動していれば ability.revealed が True になる
    assert not defender.ability.revealed


def test_みねうち_防御側が素早くてもきあいのタスキは消費されない():
    """みねうち: HP満タンの相手をHP1にする際、みねうちの効果が優先されて
    きあいのタスキは消費されない（防御側が攻撃側より素早い場合でも成立することを確認）。"""
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", move_names=["みねうち"])],
        team1=[Pokemon("サンダース", item_name="きあいのタスキ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.fix_damage(battle, defender.max_hp * 10)
    t.run_move(battle, 0)
    assert defender.hp == 1
    assert defender.item.name == "きあいのタスキ"


def test_みらいよち_2ターン後に相手にダメージが入る():
    """みらいよち: 使用から2ターン後のターン終了時に相手へダメージが発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["みらいよち"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    t.end_turn(battle)  # count: 2 → 1、まだダメージなし
    assert defender.hp == hp_before
    t.end_turn(battle)  # count: 1 → 0 → フィールド解除 → ダメージ発生
    assert defender.hp < hp_before


def test_みらいよち_2回連続使用で失敗する():
    """みらいよち: 相手陣にすでにフィールドが存在する場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["みらいよち"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)  # 1回目: 成功してフィールド設置
    t.run_move(battle, 0)  # 2回目: フィールド存在により失敗
    assert battle.move_executor.move_success is False


def test_みらいよち_はめつのねがいと独立して動作する():
    """みらいよち と はめつのねがい は別フィールドであり、同時に有効化できる。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["みらいよち", "はめつのねがい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    foe_side = battle.get_side(battle.actives[1])
    t.run_move(battle, 0, 0)  # みらいよち
    t.run_move(battle, 0, 1)  # はめつのねがい
    # 両フィールドが同時に有効化されていること
    assert foe_side.get("みらいよち").is_active
    assert foe_side.get("はめつのねがい").is_active


def test_みらいよち_使用ターンには攻撃が発動しない():
    """みらいよち: 使用ターンには即時攻撃が発動せず、相手にダメージを与えない。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["みらいよち"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_ミラーコート_まねっこでコピーできる():
    """ミラーコート: SVではまねっこでコピー可能（カウンターとは異なる）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["10まんボルト", "まねっこ"])],
        team1=[Pokemon("カビゴン", move_names=["ミラーコート"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 命中は通過（50 < 100）、0.5 >= 0.1 なので10まんボルトの追加効果（まひ）は発生しない
    t.fix_random(battle, 0.5)
    # ピカチュウ: 10まんボルトでカビゴンに特殊ダメージ
    t.run_move(battle, 0, move_idx=0)
    # カビゴン: ミラーコートで反撃し、成功して最後の使用技になる（ピカチュウが特殊ダメージを受ける）
    t.run_move(battle, 1)
    assert attacker.last_special_damage_received > 0
    hp_before = defender.hp
    # ピカチュウ: まねっこ（ミラーコートをコピー）→ 成功するはず
    t.run_move(battle, 0, move_idx=1)
    assert battle.move_executor.move_applied
    assert defender.hp < hp_before


def test_ミラーコート_みがわりに当たったダメージは参照されない():
    """ミラーコート: みがわりが被弾したダメージは特殊ダメージとして記録されない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミラーコート"])],
        team1=[Pokemon("カビゴン", move_names=["かえんほうしゃ"])],
        accuracy=100,
        volatile0={"みがわり": 1},
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 相手の特殊技をみがわりで受ける
    t.run_move(battle, 1)
    assert attacker.last_special_damage_received == 0
    hp_before = defender.hp
    # ミラーコートは失敗するはず
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_ミラーコート_物理ダメージのみ受けたとき失敗する():
    """ミラーコート: そのターン物理ダメージのみ受けた場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミラーコート"])],
        team1=[Pokemon("カビゴン", move_names=["ひっかく"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    # 相手の物理技を受ける
    t.run_move(battle, 1)
    hp_before = defender.hp
    # ミラーコートは失敗するはず
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_ミラーコート_特殊ダメージを2倍返しする():
    """ミラーコート: 受けた特殊ダメージの2倍を相手に与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミラーコート"])],
        team1=[Pokemon("カビゴン", move_names=["かえんほうしゃ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # 相手の特殊技を受ける
    t.run_move(battle, 1)
    special_dmg = attacker.last_special_damage_received
    assert special_dmg > 0
    hp_before = defender.hp
    # ミラーコートで2倍返し
    t.run_move(battle, 0)
    assert defender.hp == hp_before - special_dmg * 2


def test_ミラーコート_特殊ダメージを受けていないとき失敗する():
    """ミラーコート: そのターン特殊ダメージを受けていない場合は失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミラーコート"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before


def test_ミラーコート_連続技を受けた場合は最後の1回分のダメージのみ参照する():
    """ミラーコート: 連続技を受けた場合、合計ではなく最後の1回分のダメージを2倍にする。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミラーコート"])],
        team1=[Pokemon("カビゴン", move_names=["ツインビーム"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.fix_damage(battle, 10)
    # 相手の連続技（2回攻撃）を受ける
    t.run_move(battle, 1)
    assert attacker.hits_taken == 2
    # 合計(20)ではなく最後の1回分(10)のみが記録される
    assert attacker.last_special_damage_received == 10
    hp_before = defender.hp
    # ミラーコートは最後の1回分(10)の2倍=20だけを返す
    t.run_move(battle, 0)
    assert defender.hp == hp_before - 20


def test_ミラーショット_命中率1段階低下が発動する():
    """ミラーショット: 30%の確率で相手の命中率を1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ジバコイル", move_names=["ミラーショット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].boosts["accuracy"] == -1


def test_みわくのボイス_ランクが上がった相手にこんらんが付与される():
    """みわくのボイス: そのターンにランクが上昇した相手をこんらん状態にする。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["みわくのボイス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # 事前にdefenderのランクを上げてstat_raised_this_turnをTrueにする
    battle.modify_stats(defender, {"atk": 1}, source=defender)
    assert defender.stat_raised_this_turn
    t.run_move(battle, 0)
    assert defender.has_volatile("こんらん")


def test_みわくのボイス_ランクが上がっていない相手にはこんらんが付与されない():
    """みわくのボイス: そのターンにランクが上昇していない相手にはこんらんを付与しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["みわくのボイス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert not defender.stat_raised_this_turn
    t.run_move(battle, 0)
    assert not defender.has_volatile("こんらん")


def test_むしくい_defenderがアイテムなしのとき追加効果なし():
    """むしくい: defenderがアイテムを持たない場合、追加効果は発生しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイロス", move_names=["むしくい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    # attackerはアイテムを得ていない
    assert not attacker.has_item()
    # attackerのHPは回復していない
    assert attacker.hp == 1


def test_むしくい_きのみを奪って攻撃者がHP回復する():
    """むしくい: defenderのオボンのみを奪い、attackerがHP回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイロス", move_names=["むしくい"])],
        team1=[Pokemon("カビゴン", item_name="オボンのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    # attackerのHPを低くして回復を確認できるようにする
    attacker.hp = 1
    t.run_move(battle, 0)
    # attackerがオボンのみを得て発動し、HPが回復している
    assert attacker.hp > 1
    # defenderはオボンのみを失っている
    assert not defender.has_item()


def test_むしくい_きのみ以外のアイテムは奪わない():
    """むしくい: defenderがきのみ以外のアイテムを持つ場合、奪取は発生しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイロス", move_names=["むしくい"])],
        team1=[Pokemon("カビゴン", item_name="シルクのスカーフ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    # defenderはシルクのスカーフを持ったまま
    assert defender.has_item("シルクのスカーフ")


def test_むしくい_タンガのみを効果抜群で受けた場合ダメージ半減が優先されきのみを奪えない():
    """むしくい: defenderがタンガのみを持ち効果抜群で受ける場合、ダメージ計算時にタンガのみが
    先に消費されてダメージが半減し、命中後のきのみ強奪効果は不発になる。
    """
    battle = t.start_battle(
        team0=[Pokemon("カイロス", move_names=["むしくい"])],
        team1=[Pokemon("エーフィ", item_name="タンガのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.hp = 1
    t.run_move(battle, 0)
    # タンガのみの効果でダメージが半減している
    assert battle.damage_calculator.damage_modifier == 2048
    # タンガのみは既に消費されており、むしくいには奪われない
    assert not defender.has_item()
    # attackerはきのみを得ておらずHPも回復していない
    assert not attacker.has_item()
    assert attacker.hp == 1


def test_むしくい_ねんちゃく持ちから奪えない():
    """むしくい: defenderがねんちゃく持ちのとき奪取が失敗し、attackerのHPは回復しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイロス", move_names=["むしくい"])],
        team1=[Pokemon("カビゴン", ability_name="ねんちゃく", item_name="オボンのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.hp = 1
    t.run_move(battle, 0)
    # attackerのHPは回復していない（奪取失敗）
    assert attacker.hp == 1
    # defenderはオボンのみを保持している
    assert defender.has_item("オボンのみ")


def test_むしくい_ねんちゃく持ちをひんしにさせた場合は奪える():
    """むしくい: defenderがねんちゃく持ちでも、この技でひんしにさせた場合は奪取できる
    （第五世代以降の仕様）。HP閾値に依存しないラムのみで検証する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カイロス", move_names=["むしくい"])],
        team1=[Pokemon("カビゴン", ability_name="ねんちゃく", item_name="ラムのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.ailment_manager.apply(attacker, "まひ")
    battle.test_option.trigger_ailment = False  # まひによる行動不能を発生させない
    defender.hp = 1
    t.run_move(battle, 0)
    # defenderはこの技でひんしになり、ラムのみを奪われている
    assert defender.fainted
    assert not defender.has_item()
    # attackerがラムのみを得て消費し、まひが回復している
    assert not attacker.has_item()
    assert attacker.ailment.name == ""


def test_むしくい_みがわりに防がれた場合はきのみを食べられない():
    """むしくい: defenderがみがわり状態のとき、実体のきのみを奪えない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイロス", move_names=["むしくい"])],
        team1=[Pokemon("カビゴン", item_name="オボンのみ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    attacker.hp = 1
    t.run_move(battle, 0)
    # defenderはオボンのみを保持したまま
    assert defender.has_item("オボンのみ")
    # attackerはきのみを得ておらずHPも回復していない
    assert not attacker.has_item()
    assert attacker.hp == 1


def test_むしのさざめき_とくぼう1段階低下が発動しない():
    """むしのさざめき: 追加効果不発時はとくぼうランクが変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("モルフォン", move_names=["むしのさざめき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].boosts["spd"] == 0


def test_むしのさざめき_とくぼう1段階低下が発動する():
    """むしのさざめき: 10%の確率で相手のとくぼうを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("モルフォン", move_names=["むしのさざめき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].boosts["spd"] == -1


def test_むしのさざめき_みがわりを貫通して本体にダメージを与える():
    """むしのさざめき: soundフラグを持つため、みがわり状態の相手の本体にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("モルフォン", move_names=["むしのさざめき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
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


def test_むしのさざめき_相手にダメージを与える():
    """むしのさざめき: 特殊むし技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("モルフォン", move_names=["むしのさざめき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_むしのていこう_secondary_effectフラグを持つ():
    """むしのていこう: ちからずくとの相互作用のためsecondary_effectフラグを持つこと。"""
    move_data = MOVES["むしのていこう"]
    assert "secondary_effect" in move_data.flags


def test_むしのていこう_とくこう1段階低下が発動する():
    """むしのていこう: 100%の確率で相手のとくこうを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("モルフォン", move_names=["むしのていこう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].boosts["spa"] == -1


def test_むねんのつるぎ_使用後に攻撃者のHPが回復する():
    """むねんのつるぎ: 与えたダメージの半分だけ攻撃者のHPを回復する（heal_ratio=0.5）。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["むねんのつるぎ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp > hp_before


def test_むねんのつるぎ_回復量の端数は切り上げになる():
    """むねんのつるぎ: 他のドレイン技と異なり、回復量の端数は切り上げになる。

    与ダメ101のとき、他のドレイン技なら int(101 * 0.5) = 50 だが、
    むねんのつるぎは切り上げのため 51 になる。
    """
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["むねんのつるぎ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_damage(battle, 101)
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + 51


def test_ムーンフォース_とくこう1段階低下が発動する():
    """ムーンフォース: 10%の確率で相手のとくこうを1段階下げる（Championsで30%→10%に変更）。"""
    battle = t.start_battle(
        team0=[Pokemon("ニンフィア", move_names=["ムーンフォース"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].boosts["spa"] == -1


def test_ムーンフォース_基準確率0_1で発動しない():
    """ムーンフォース: 乱数0.1は境界値0.1以上のため発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ニンフィア", move_names=["ムーンフォース"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.1)  # 0.1 >= 0.1 → 発動しない
    t.run_move(battle, 0)
    assert battle.actives[1].boosts["spa"] == 0


def test_ムーンフォース_基準確率0_1で発動する():
    """ムーンフォース: チャンピオンズ基準の発動確率は0.1(=境界0.1未満で発動)。secondary_chanceを上書きせず既定値で判定する。"""
    battle = t.start_battle(
        team0=[Pokemon("ニンフィア", move_names=["ムーンフォース"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.09)  # 0.09 < 0.1 → 発動
    t.run_move(battle, 0)
    assert battle.actives[1].boosts["spa"] == -1


def test_メガトンキック_相手にダメージを与える():
    """メガトンキック: 追加効果なしの物理ノーマル技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メガトンキック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_メガトンパンチ_相手にダメージを与える():
    """メガトンパンチ: 追加効果なしの物理ノーマル技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["メガトンパンチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_メガドレイン_使用後に攻撃者のHPが回復する():
    """メガドレイン: 与えたダメージの半分だけ攻撃者のHPを回復する（heal_ratio=0.5）。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["メガドレイン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp > hp_before


def test_メガホーン_相手にダメージを与える():
    """メガホーン: 追加効果なしの物理むし技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ヘラクロス", move_names=["メガホーン"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_めざめるダンス_ステラテラスタル中は元のタイプ1を参照する():
    """めざめるダンス: ステラタイプにテラスタルしている場合は元のタイプ1を参照する。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", tera_type="ステラ", move_names=["めざめるダンス"])],
        team1=[Pokemon("コダック")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.terastallize()
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "くさ"


def test_めざめるダンス_テラスタル中はテラスタイプを参照する():
    """めざめるダンス: テラスタル中はその時のタイプ1（テラスタイプ）を参照する。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", tera_type="ほのお", move_names=["めざめるダンス"])],
        team1=[Pokemon("フシギダネ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.terastallize()
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "ほのお"


def test_めざめるダンス_使用者のタイプ1と同じタイプになる():
    """めざめるダンス: 使用者のタイプ1と同じタイプの技になる。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["めざめるダンス"])],  # タイプ1=くさ
        team1=[Pokemon("コダック")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "くさ"


def test_メタルクロー_こうげき1段階上昇が発動しない():
    """メタルクロー: 追加効果不発時はこうげきランクが変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ハッサム", move_names=["メタルクロー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.boosts["atk"] == 0


def test_メタルクロー_こうげき1段階上昇が発動する():
    """メタルクロー: 10%の確率で自分のこうげきを1段階上げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ハッサム", move_names=["メタルクロー"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.boosts["atk"] == 1


def test_メタルクロー_タイプ威力命中PPが仕様通り():
    """メタルクロー: はがねタイプの物理直接攻撃技で、威力50・命中95・PP35を持つ。"""
    move_data = MOVES["メタルクロー"]
    assert move_data.type == "はがね"
    assert move_data.category == "physical"
    assert move_data.power == 50
    assert move_data.accuracy == 95
    assert move_data.pp == 35
    assert "contact" in move_data.flags
    assert "secondary_effect" in move_data.flags


def test_メテオドライブ_もふもふのダメージ軽減を無視する():
    """メテオドライブ: 相手の特性を無視するため、もふもふによる接触技の被ダメ半減が発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ハッサム", move_names=["メテオドライブ"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 4096


def test_メテオドライブ_攻撃後に相手の特性が有効に戻る():
    """メテオドライブ: 攻撃終了後は相手の特性の無効化が解除される。"""
    battle = t.start_battle(
        team0=[Pokemon("ハッサム", move_names=["メテオドライブ"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.ability.enabled is True


def test_メテオビーム_1ターン目にとくこうが上昇する():
    """メテオビーム: 1ターン目にとくこうが1段階上昇する（追加効果ではないため必ず発動）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["メテオビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]

    # 1ターン目: とくこう+1
    t.run_move(battle, 0)
    assert attacker.boosts["spa"] == 1


def test_メテオビーム_2ターンで攻撃する():
    """メテオビーム: 1ターン目はダメージなしで揮発状態を付与し、2ターン目にダメージを与えて揮発状態を解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["メテオビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp

    # 1ターン目: 揮発状態付与のみ、ダメージなし
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert attacker.has_volatile("メテオビーム")

    # 2ターン目: ダメージあり、揮発状態解除
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert not attacker.has_volatile("メテオビーム")


def test_メテオビーム_ちからずくでも威力は上がらずとくこうは上昇する():
    """メテオビーム: 追加効果に分類されないため、ちからずくを持っていても威力は上がらず、
    とくこう上昇は通常通り発動する。"""
    battle_with = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ちからずく", move_names=["メテオビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle_without = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["メテオビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    # ダメージ乱数・急所判定を固定し、威力補正の有無だけの差を見られるようにする
    t.fix_random(battle_with, 0.9)
    t.fix_random(battle_without, 0.9)
    attacker_with = battle_with.actives[0]
    attacker_without = battle_without.actives[0]

    # 1ターン目: とくこう+1 のみ（ちからずくの有無に関わらず発動）
    t.run_move(battle_with, 0)
    t.run_move(battle_without, 0)
    assert attacker_with.boosts["spa"] == 1
    assert attacker_without.boosts["spa"] == 1

    # 2ターン目: ちからずくの有無でダメージ量が変わらない（威力補正なし）
    hp_before_with = battle_with.actives[1].hp
    hp_before_without = battle_without.actives[1].hp
    t.run_move(battle_with, 0)
    t.run_move(battle_without, 0)
    damage_with = hp_before_with - battle_with.actives[1].hp
    damage_without = hp_before_without - battle_without.actives[1].hp
    assert damage_with == damage_without


def test_メテオビーム_パワフルハーブ使用時1ターンで攻撃してとくこうが上昇する():
    """メテオビーム+パワフルハーブ: 1ターンで攻撃できる。とくこうも+1される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="パワフルハーブ", move_names=["メテオビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp

    # 1ターンで攻撃
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert not attacker.has_item()
    assert attacker.boosts["spa"] == 1


def test_もえあがるいかり_ひるみが発動する():
    """もえあがるいかり: 20%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ヘルガー", move_names=["もえあがるいかり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_もえつきる_こおり状態でほのおタイプでないポケモンが使うと解凍されず行動もできない():
    """もえつきる: ほのおタイプを持たないポケモンがこおり状態で使うと、
    もえつきる自体のこおり解凍効果は発動せず、通常のこおり判定（未解凍なら行動不能）に従う。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["もえつきる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.apply_ailment(battle, 0, "こおり", count=None)  # count指定でtickによる自動解除を防ぐ
    battle.test_option.trigger_ailment = False  # こおり_action側のランダム解凍を無効化
    assert attacker.ailment.name == "こおり"
    hp_before = defender.hp
    t.run_move(battle, 0)
    # もえつきるのこおり解凍効果が誤発動しないため、こおり状態のまま行動できない
    assert not battle.move_executor.action_success
    assert attacker.ailment.name == "こおり"
    assert defender.hp == hp_before


def test_もえつきる_こおり状態で使うと解凍されて攻撃できる():
    """もえつきる: こおり状態でも使用でき、使うと解凍される。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["もえつきる"])],
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


def test_もえつきる_テラスタルほのお中でも成功しタイプ除去が記録される():
    """もえつきる: テラスタル（ほのお）中でも成功し、ほのおタイプの除去が記録される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["もえつきる"], tera_type="ほのお")],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.terastallize()
    assert attacker.has_type("ほのお")  # テラスタルでほのおタイプを持つ
    hp_before = defender.hp
    t.run_move(battle, 0)
    # テラスタル中でも成功してダメージあり、除去が記録される
    assert battle.move_executor.move_success is True
    assert defender.hp < hp_before
    assert "ほのお" in attacker.removed_types


def test_もえつきる_ほのおタイプでないポケモンが使うと技が失敗する():
    """もえつきる: ほのおタイプを持たないポケモンが使うと技が失敗する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["もえつきる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    # 技が失敗してダメージなし
    assert battle.move_executor.move_success is False
    assert defender.hp == hp_before


def test_もえつきる_ほのおタイプのポケモンが使うと成功し攻撃後にほのおタイプでなくなる():
    """もえつきる: ほのおタイプのポケモンが使うと成功し、攻撃後にほのおタイプが除去される。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["もえつきる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    assert attacker.has_type("ほのお")
    hp_before = defender.hp
    t.run_move(battle, 0)
    # 技が成功してダメージあり、ほのおタイプが除去されている
    assert battle.move_executor.move_success is True
    assert defender.hp < hp_before
    assert not attacker.has_type("ほのお")
    assert "ほのお" in attacker.removed_types
