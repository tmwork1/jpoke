"""攻撃技ハンドラの単体テスト（や行・ら行・わ行）。"""

from jpoke import Pokemon
from .. import test_utils as t


def test_Vジェネレート_防御特防素早さが各1段階低下する():
    """Vジェネレート: 命中時に使用者のB/D/Sが各1段階低下する（確率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ビクティニ", move_names=["Vジェネレート"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.rank["B"] == -1
    assert attacker.rank["D"] == -1
    assert attacker.rank["S"] == -1


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


def test_やまあらし_確定急所():
    """やまあらし: 急所ランク3のため乱数によらず常に急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("ヒノアラシ", move_names=["やまあらし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、急所は確定ランク3で必ず発生
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_ゆめくい_ねむり状態でない相手には失敗する():
    """ゆめくい: 相手がねむり状態でない場合は失敗し、攻撃者のHPは変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ゆめくい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before_attacker = attacker.hp
    hp_before_defender = defender.hp
    t.run_move(battle, 0)
    # 失敗するので攻撃者のHPは変化なし、防御者もダメージなし
    assert attacker.hp == hp_before_attacker
    assert defender.hp == hp_before_defender


def test_ゆめくい_ねむり状態の相手にのみ命中しHPを回復する():
    """ゆめくい: 相手がねむり状態のとき命中し、与えたダメージの半分だけHPを回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ゆめくい"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("ねむり", 3),
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp > hp_before


def test_らいげき_まひが発動する():
    """らいげき: 20%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ライコウ", move_names=["らいげき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_りゅうのいぶき_まひが発動する():
    """りゅうのいぶき: 30%でまひを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["りゅうのいぶき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_りゅうのはどう_相手にダメージを与える():
    """りゅうのはどう: 追加効果なしの特殊ドラゴン技で相手にダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["りゅうのはどう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before


def test_りんごさん_とくぼう1段階低下が発動する():
    """りんごさん: 100%の確率で相手のとくぼうを1段階下げる。"""
    battle = t.start_battle(
        team0=[Pokemon("マホイップ", move_names=["りんごさん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].rank["D"] == -1


def test_リーフブレード_急所ランクが1():
    """リーフブレード: 急所ランク+1のため乱数0で急所が発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("ジュカイン", move_names=["リーフブレード"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.move_executor.critical is True


def test_リーフブレード_急所ランクが1_乱数大で急所なし():
    """リーフブレード: 乱数が急所閾値以上のとき急所にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("ジュカイン", move_names=["リーフブレード"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 命中は通過（50 < 100）、0.5 >= 1/8 なので急所なし
    t.run_move(battle, 0)
    assert battle.move_executor.critical is False


def test_レイジングブル_ケンタロスパルデア闘はかくとうタイプになる():
    """レイジングブル: ケンタロス（パルデア闘）が使用するとかくとうタイプになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ケンタロス(パルデア闘)", move_names=["レイジングブル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "かくとう"


def test_レイジングブル_ケンタロス水フォルムはみずタイプになる():
    """レイジングブル: ケンタロス（パルデア水）が使用するとみずタイプになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ケンタロス(パルデア水)", move_names=["レイジングブル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "みず"


def test_レイジングブル_ケンタロス炎フォルムはほのおタイプになる():
    """レイジングブル: ケンタロス（パルデア炎）が使用するとほのおタイプになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ケンタロス(パルデア炎)", move_names=["レイジングブル"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "ほのお"


def test_レイジングブル_ひかりのかべを解除する():
    """レイジングブル: 命中時に相手側のひかりのかべを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("ケンタロス(パルデア闘)", move_names=["レイジングブル"])],
        team1=[Pokemon("カビゴン")],
        side1={"ひかりのかべ": 1},
        accuracy=100,
    )
    assert battle.side_managers[1].fields["ひかりのかべ"].is_active
    t.run_move(battle, 0)
    assert not battle.side_managers[1].fields["ひかりのかべ"].is_active


def test_レイジングブル_リフレクターを解除する():
    """レイジングブル: 命中時に相手側のリフレクターを解除する。"""
    battle = t.start_battle(
        team0=[Pokemon("ケンタロス(パルデア闘)", move_names=["レイジングブル"])],
        team1=[Pokemon("カビゴン")],
        side1={"リフレクター": 1},
        accuracy=100,
    )
    assert battle.side_managers[1].fields["リフレクター"].is_active
    t.run_move(battle, 0)
    assert not battle.side_managers[1].fields["リフレクター"].is_active


def test_れいとうパンチ_こおりが発動する():
    """れいとうパンチ: 10%でこおりを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["れいとうパンチ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "こおり"


def test_れいとうビーム_こおりが発動する():
    """れいとうビーム: 10%でこおりを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フリーザー", move_names=["れいとうビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "こおり"


def test_れんごく_やけどが発動する():
    """れんごく: 100%でやけどを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン", move_names=["れんごく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_ロッククライム_こんらんが発動する():
    """ロッククライム: 20%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["ロッククライム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")


def test_ロックブラスト_複数ヒットする():
    """ロックブラスト: 2～5回連続でヒットする複数ヒット技である。"""
    battle = t.start_battle(
        team0=[Pokemon("イワーク", move_names=["ロックブラスト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    assert 2 <= hit_count <= 5


def test_ワイルドボルト_使用後に攻撃者が反動ダメージを受ける():
    """ワイルドボルト: 与えたダメージの1/4を攻撃者が反動として受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ワイルドボルト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_ワイルドボルト_反動ダメージが与ダメの4分の1になる():
    """ワイルドボルト: 反動量は max(1, int(与ダメ * 1/4)) で計算される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ワイルドボルト"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.fix_damage(battle, 100)
    hp_before = attacker.hp
    t.run_move(battle, 0)
    # max(1, int(100 * 1/4)) = 25
    assert attacker.hp == hp_before - 25


def test_ワンダースチーム_こんらんが発動する():
    """ワンダースチーム: 20%でこんらんを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ワンダースチーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("こんらん")
