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


def test_まわしげり_ひるみが発動する():
    """まわしげり: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["まわしげり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


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
    assert defender.rank["S"] == -1


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


def test_ミラーショット_命中率1段階低下が発動する():
    """ミラーショット: 30%の確率で相手の命中率を1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("ジバコイル", move_names=["ミラーショット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["ACC"] == -1


def test_みわくのボイス_ランクが上がった相手にこんらんが付与される():
    """みわくのボイス: そのターンにランクが上昇した相手をこんらん状態にする。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["みわくのボイス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # 事前にdefenderのランクを上げてstat_raised_this_turnをTrueにする
    battle.modify_stats(defender, {"A": 1}, source=defender)
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
    assert battle.actives[1].rank["C"] == -1


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
    assert attacker.rank["C"] == 1


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
    assert attacker.rank["C"] == 1
