"""攻撃技ハンドラの単体テスト（ま行）。"""

from jpoke import Pokemon
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
    assert defender.rank["spe"] == -1


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


def test_ミラーショット_命中率1段階低下が発動する():
    """ミラーショット: 30%の確率で相手の命中率を1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ジバコイル", move_names=["ミラーショット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["accuracy"] == -1


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


def test_ムーンフォース_とくこう1段階低下が発動する():
    """ムーンフォース: 30%の確率で相手のとくこうを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ニンフィア", move_names=["ムーンフォース"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["spa"] == -1


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
    assert attacker.rank["spa"] == 1


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
    assert attacker.rank["spa"] == 1


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
