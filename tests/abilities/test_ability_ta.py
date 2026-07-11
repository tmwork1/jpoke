"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.enums import LogCode
from jpoke.types import Type, AilmentName, WeatherName, Gender

from .. import test_utils as t


def test_たいねつ_やけどダメージ半減():
    """たいねつ: やけどのターン終了時ダメージが通常の半分（最大HPの1/32、最低1）になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="たいねつ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど")
    t.end_turn(battle)
    assert mon.hp == mon.max_hp - max(1, mon.max_hp // 32)


def test_たいねつ_やけどダメージ最低1保証():
    """たいねつ: 半減後に端数切り捨てで0になる場合でも最低1ダメージは受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="たいねつ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    # max_hp=20 のとき通常やけどダメージは20//16=1。たいねつの最低1保証がなければ
    # 1を0.5倍した結果0になってしまう。
    mon._stats_manager._stats[0] = 20
    mon.hp = 20
    battle.ailment_manager.apply(mon, "やけど")
    t.end_turn(battle)
    assert mon.hp == 19


def test_たんじゅん_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="たんじゅん")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].rank["atk"] == -1


def test_たんじゅん_能力変化量が2倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="たんじゅん")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives

    stats = {"atk": 1, "def": -2, "spa": 3, "spd": -4, "spe": 1, "accuracy": -2, "evasion": 3}
    battle.modify_stats(target, stats, source=source)
    for stat, change in stats.items():
        assert target.rank[stat] == max(-6, min(6, change * 2))


def test_ターボブレイズ_かがくへんかガス解除後に特性発動ログが再度記録される():
    """ターボブレイズ: かたやぶりと同様、かがくへんかガスの効果が切れて特性が
    再有効化されたときに場に出たときのログが再度記録される。"""
    battle = t.start_battle(
        team0=[Pokemon("ドガース", ability_name="かがくへんかガス"), Pokemon("コラッタ")],
        team1=[Pokemon("レシラム", ability_name="ターボブレイズ")],
    )
    mon = battle.actives[1]
    assert not mon.ability.enabled

    def count_triggered() -> int:
        return sum(
            1 for log in battle.event_logger.logs
            if log.log == LogCode.ABILITY_TRIGGERED
            and log.idx == 1
            and log.payload is not None
            and getattr(log.payload, "ability", None) == "ターボブレイズ"
        )

    assert count_triggered() == 0

    t.run_switch(battle, 0, 1)
    assert mon.ability.enabled
    assert count_triggered() == 1


def test_ターボブレイズ_がんじょうを無視して一撃で倒す():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="がんじょう")],
        team1=[Pokemon("レシラム", ability_name="ターボブレイズ", move_names=["じしん"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].hp == 0


def test_ターボブレイズ_プリズムアーマーは無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("レシラム", ability_name="ターボブレイズ", move_names=["じしん"])],
        team1=[Pokemon("コイル", ability_name="プリズムアーマー")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.damage_modifier


def test_ターボブレイズ_場に出たときに特性開示():
    battle = t.start_battle(
        team0=[Pokemon("レシラム", ability_name="ターボブレイズ")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.actives[0].ability.revealed


def test_ダウンロード_ランク補正を考慮して比較する():
    """防御・特防の比較にはランク補正込みの実数値を使う。

    フシギダネは素の実数値では防御<特防だが、特防のランクを-6まで下げると
    ランク補正後は防御の方が上回るため、攻撃ではなく特攻が上がる。
    """
    battle = t.start_battle(
        team0=[Pokemon("コイキング"), Pokemon("ピカチュウ", ability_name="ダウンロード")],
        team1=[Pokemon("フシギダネ")],
    )
    battle.actives[1].rank["spd"] = -6
    mon = t.run_switch(battle, 0, 1)
    assert mon.rank["atk"] == 0
    assert mon.rank["spa"] == 1


def test_ダウンロード_ワンダールームでランク補正のみ入れ替えて比較する():
    """ワンダールーム下では実数値は据え置いたまま、防御・特防のランク補正のみを入れ替えて比較する。

    フシギダネの防御ランクを+6・特防ランクを-6にすると、通常の比較（ランク補正も入れ替えない）
    では防御実数値×防御ランク補正＞特防実数値×特防ランク補正となり特攻が上がってしまうが、
    ワンダールーム下ではランク補正のみが入れ替わるため、
    防御実数値×特防ランク補正＜特防実数値×防御ランク補正となり攻撃が上がる。
    """
    battle = t.start_battle(
        team0=[Pokemon("コイキング"), Pokemon("ピカチュウ", ability_name="ダウンロード")],
        team1=[Pokemon("フシギダネ")],
        field={"ワンダールーム": 99},
    )
    battle.actives[1].rank["def"] = 6
    battle.actives[1].rank["spd"] = -6
    mon = t.run_switch(battle, 0, 1)
    assert mon.rank["atk"] == 1
    assert mon.rank["spa"] == 0


def test_ダウンロード_上げる能力が既に最大なら発動しない():
    """上げる能力のランクが既に+6の場合、ランクは変化せず特性発動ログも記録されない。"""
    battle = t.start_battle(
        team0=[Pokemon("コイキング"), Pokemon("ピカチュウ", ability_name="ダウンロード")],
        team1=[Pokemon("フシギダネ")],  # 防御<特防のためこうげきが上がる想定
    )
    mon = battle.player_states[battle.players[0]].team[1]
    mon.rank["atk"] = 6

    def count_triggered() -> int:
        return sum(
            1 for log in battle.event_logger.logs
            if log.log == LogCode.ABILITY_TRIGGERED
            and log.payload is not None
            and getattr(log.payload, "ability", None) == "ダウンロード"
        )

    t.run_switch(battle, 0, 1)
    assert mon.rank["atk"] == 6
    assert count_triggered() == 0


@pytest.mark.parametrize(
    "foe_name, stat",
    [
        ("フシギダネ", "atk"),
        ("ゼニガメ", "spa"),
        ("ウインディ", "spa"),  # BD同じならCアップ
    ],
)
def test_ダウンロード_能力アップ(foe_name, stat):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ダウンロード")],
        team1=[Pokemon(foe_name)],
    )
    assert battle.actives[0].rank[stat] == 1


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_だっぴ_ターン終了時に状態異常を回復する(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("コラッタ", ability_name="だっぴ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=(ailment_name, None),
    )
    mon = battle.actives[0]

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        t.end_turn(battle)
    finally:
        battle.random.random = orig_random

    assert not mon.ailment.is_active


def test_だっぴ_状態異常がなければ何も起きない():
    """だっぴ: 状態異常がないときは何も起きない（エラーにならない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="だっぴ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert not mon.ailment.is_active


def test_だっぴ_発動ターンはどくダメージを受けない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="だっぴ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("どく", None),
    )
    mon = battle.actives[0]

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        t.end_turn(battle)
    finally:
        battle.random.random = orig_random

    assert mon.hp == mon.max_hp


def test_だっぴ_非発動時は状態異常が残る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="だっぴ")],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("どく", None),
    )
    mon = battle.actives[0]

    orig_random = battle.random.random
    battle.random.random = lambda: 1
    try:
        t.end_turn(battle)
    finally:
        battle.random.random = orig_random

    assert mon.ailment.is_active


def test_ダルマモード_HP1_2以下で場に出た直後は変化しない():
    """発動にはターン終了まで待つ必要があり、場に出た瞬間には変化しない。"""
    darmanitan = Pokemon("ヒヒダルマ(ノーマル)", ability_name="ダルマモード")
    darmanitan.hp = darmanitan.max_hp // 2
    battle = t.start_battle(
        team0=[darmanitan],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ヒヒダルマ(ノーマル)"
    t.end_turn(battle)
    assert mon.name == "ヒヒダルマ(ダルマ)"


def test_ダルマモード_ターン終了時にHP1_2以下ならダルマのすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("ヒヒダルマ(ノーマル)", ability_name="ダルマモード")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    t.end_turn(battle)
    assert mon.name == "ヒヒダルマ(ダルマ)"


def test_ダルマモード_ターン終了時にHP1_2超なら元のすがたに戻る():
    battle = t.start_battle(
        team0=[Pokemon("ヒヒダルマ(ダルマ)", ability_name="ダルマモード")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2 + 1
    t.end_turn(battle)
    assert mon.name == "ヒヒダルマ(ノーマル)"


def test_ダルマモード_交代するとノーマルのすがたに戻る():
    battle = t.start_battle(
        team0=[Pokemon("ヒヒダルマ(ダルマ)", ability_name="ダルマモード"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    t.run_switch(battle, 0, 1)
    assert mon.name == "ヒヒダルマ(ノーマル)"


def test_ダークオーラ_あく技以外には効果がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ダークオーラ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.power_modifier


def test_ダークオーラ_かたやぶりでも威力補正は無効化されない():
    """現行世代ではかたやぶりの効果がある技はダークオーラの影響を受ける（無視されない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ダークオーラ")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["あくのはどう"])],
    )
    t.run_move(battle, 1)
    assert 5448 == battle.damage_calculator.power_modifier


def test_ダークオーラ_登場時に特性開示():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ダークオーラ")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.actives[0].ability.revealed is True


def test_ダークオーラ_相手のあく技威力も5448_4096倍になる():
    """ダークオーラの効果対象は場にいるポケモン全員のため、敵のあく技威力も上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ダークオーラ")],
        team1=[Pokemon("ピカチュウ", move_names=["あくのはどう"])],
    )
    t.run_move(battle, 1)
    assert 5448 == battle.damage_calculator.power_modifier


def test_ダークオーラ_自分のあく技威力が5448_4096倍になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ダークオーラ", move_names=["あくのはどう"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 5448 == battle.damage_calculator.power_modifier


def test_ちからずく_いっちょうあがりは追加効果がなくても威力が1_3倍になる():
    """いっちょうあがり: 追加効果は無いがちからずく対象フラグを持つため、威力が1.3倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからずく", move_names=["いっちょうあがり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier
    assert attacker.rank["atk"] == 0


def test_ちからずく_ねっとうで相手のこおりを治せない():
    """ちからずく: ねっとうはみずタイプでこおり解凍効果を持つが、
    ほのおタイプ由来の効果ではなく追加効果扱いのため、ちからずくで発動しなくなる。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", ability_name="ちからずく", move_names=["ねっとう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=0.0,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "こおり")
    t.run_move(battle, 0)
    assert defender.ailment.name == "こおり"
    assert 5325 == battle.damage_calculator.power_modifier


def test_ちからずく_ハイドロスチームでも相手のこおりを治せる():
    """ちからずく: ハイドロスチームはちからずくの対象技ではないため、
    ちからずく所持でも威力は上がらず、相手のこおりを治す効果は通常通り発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", ability_name="ちからずく", move_names=["ハイドロスチーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.ailment_manager.apply(defender, "こおり")
    t.run_move(battle, 0)
    assert not defender.ailment.is_active
    assert 4096 == battle.damage_calculator.power_modifier


def test_ちからずく_追加効果が発動せず威力が1_3倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからずく", move_names=["アクアステップ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier
    assert attacker.rank["spe"] == 0


def test_ちからもち_イカサマで攻撃するときも2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからもち", move_names=["イカサマ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.atk_modifier


def test_ちからもち_イカサマを受けるときは補正なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからもち")],
        team1=[Pokemon("ピカチュウ", move_names=["イカサマ"])],
    )
    t.run_move(battle, 1)
    assert 4096 == battle.damage_calculator.atk_modifier


def test_ちからもち_こんらん自傷ダメージには補正なし():
    """ちからもち: こんらんの自傷ダメージには攻撃補正がかからない（第五世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからもち")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2},
    )
    attacker = battle.actives[0]
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_modifier == 4096
    assert attacker.hp < attacker.max_hp


def test_ちからもち_パワートリック状態で物理技を使うと入れ替わった防御が2倍になる():
    """ちからもち: パワートリックで入れ替わった実数値（元の防御）が物理技のダメージ計算で2倍になる"""
    battle = t.start_battle(
        team0=[
            Pokemon(
                "ピカチュウ",
                ability_name="ちからもち",
                move_names=["パワートリック", "たいあたり"],
            )
        ],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    t.run_move(battle, 0, move_idx=1)
    assert 8192 == battle.damage_calculator.atk_modifier


def test_ちからもち_ボディプレスで自分の防御を2倍にする():
    """ちからもち: ボディプレス使用時は自分の防御実数値を2倍にしてダメージを与える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからもち", move_names=["ボディプレス"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert 8192 == battle.damage_calculator.atk_modifier


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("たいあたり",  8192),
        ("でんきショック", 4096)
    ]
)
def test_ちからもち_物理技で攻撃補正2倍(move_name: str, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちからもち", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert expected_modifier == battle.damage_calculator.atk_modifier


def test_ちくでん_HP満タン時は回復せず無効化のみ():
    """ちくでん: HPが満タンのときは回復せず、でんき技の無効化のみ発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちくでん")],
        team1=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    defender, attacker = battle.actives
    t.run_move(battle, 1)
    assert defender.hp == defender.max_hp
    assert defender.ability.revealed


def test_ちくでん_でんき変化技も無効化して回復する():
    """ちくでん: でんきタイプの変化技を受けても無効化し、最大HPの1/4回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちくでん")],
        team1=[Pokemon("ゼブライカ", move_names=["でんじは"])],
        accuracy=100,
    )
    defender, attacker = battle.actives
    defender.hp = 1
    t.run_move(battle, 1)
    assert defender.hp == 1 + defender.max_hp // 4
    assert not defender.ailment.is_active


def test_ちくでん_まひ無効より先に発動して回復する():
    """ちくでん: でんきタイプの自身はでんじは等でまひ無効となるが、
    その無効化より先にちくでんが発動してHPが回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("ライチュウ", ability_name="ちくでん", move_names=["でんじは"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんじは"])],
        accuracy=100,
    )
    defender, attacker = battle.actives
    defender.hp = 1
    t.run_move(battle, 1)
    assert defender.hp == 1 + defender.max_hp // 4
    assert not defender.ailment.is_active


def test_ちどりあし_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちどりあし")],
        team1=[Pokemon("カビゴン", ability_name="かたやぶり", move_names=["たいあたり"])],
        volatile0={"こんらん": 3}
    )
    t.run_move(battle, 1)
    assert battle.move_executor.accuracy == 100


def test_ちどりあし_こんらんでないとき変化なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちどりあし")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.move_executor.accuracy == 100


def test_ちどりあし_こんらん中命中率が半減する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちどりあし")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        volatile0={"こんらん": 3}
    )
    t.run_move(battle, 1)
    assert battle.move_executor.accuracy == 50


def test_ちょすい_HP満タンならみず技無効化のみで回復しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちょすい")],
        team1=[Pokemon("ピカチュウ", move_names=["なみのり"])],
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.hp == mon.max_hp
    assert mon.ability.revealed


def test_ちょすい_かいふくふうじ状態でも無効化はできるが回復はできない():
    """ちょすい: かいふくふうじ状態でもみず技の無効化（ダメージ0）はできるが、
    第五世代以降の仕様のためHPの回復はできない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちょすい")],
        team1=[Pokemon("カビゴン", move_names=["なみのり"])],
        volatile0={"かいふくふうじ": 3},
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.hp == 1
    assert mon.ability.revealed


def test_ちょすい_マジックコートで跳ね返された変化技を受けると回復する():
    """ちょすい: 自分が使ったみずタイプの変化技が相手のマジックコートで跳ね返され、
    跳ね返った技を自分自身が受けた場合はちょすいが発動して回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちょすい", move_names=["みずびたし"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    mon.hp = 1
    t.run_move(battle, 0)
    assert mon.hp == 1 + mon.max_hp // 4
    assert foe.types == ["ノーマル"]


def test_ちょすい_マジックコート状態では変化技を跳ね返し回復しない():
    """ちょすい: マジックコート状態のちょすい持ちがみずタイプの変化技を受けても、
    先に跳ね返されるためちょすいは発動せず回復しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちょすい")],
        team1=[Pokemon("カビゴン", move_names=["みずびたし"])],
        volatile0={"マジックコート": 1},
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.hp == 1
    assert not mon.ability.revealed


def test_ちょすい_まもるで防がれたときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちょすい")],
        team1=[Pokemon("カビゴン", move_names=["なみのり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    battle.volatile_manager.apply(mon, "まもる", count=1)
    t.run_move(battle, 1)
    assert mon.hp == 1
    assert not mon.ability.revealed


def test_ちょすい_みがわり状態の攻撃技でも発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちょすい")],
        team1=[Pokemon("カビゴン", move_names=["なみのり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "みがわり", count=mon.max_hp // 4)
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.hp == 1 + mon.max_hp // 4
    assert mon.has_volatile("みがわり")


def test_ちょすい_みずタイプの変化技も無効化する():
    """ちょすい: みずびたしのようなみずタイプの変化技を受けても無効化し、タイプは変わらない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちょすい")],
        team1=[Pokemon("カビゴン", move_names=["みずびたし"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.hp == 1 + mon.max_hp // 4
    assert mon.types == ["でんき"]


def test_ちょすい_みず技を無効化してHPが減っていれば1_4回復():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちょすい")],
        team1=[Pokemon("ピカチュウ", move_names=["なみのり"])],
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.hp == 1 + mon.max_hp // 4
    assert mon.ability.revealed


def test_ちょすい_場を対象とするみず技には発動しない():
    """ちょすい: あまごいなど場を対象とするみず技には発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あまごい"])],
        team1=[Pokemon("カビゴン", ability_name="ちょすい")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.weather.name == "あめ"
    assert defender.hp == defender.max_hp
    assert not defender.ability.revealed


def test_ちょすい_自分自身を対象とするみず技には発動しない():
    """ちょすい: アクアリングなど自分自身を対象とするみず技には発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちょすい", move_names=["アクアリング"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.has_volatile("アクアリング")


def test_ちょすい_連続技を受けても回復は1回のみ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ちょすい")],
        team1=[Pokemon("カビゴン", move_names=["すいりゅうれんだ"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.hp == 1 + mon.max_hp // 4


@pytest.mark.parametrize(
    "name, tera_type, move_name, expected_modifier",
    [
        ("ピカチュウ", "", "でんきショック", 4096 * 2),
        ("ピカチュウ", "でんき", "でんきショック", 4096 * 2.25),
        ("ピカチュウ", "", "ひのこ", 4096),
        # テラスタイプが元タイプと不一致で、技タイプがテラスタイプと一致 → 2.0倍
        ("ピカチュウ", "ほのお", "ひのこ", 4096 * 2),
        # テラスタルにより失った元タイプ（元タイプ一致だがテラスタイプ不一致）の技には
        # 効果が発動せず、STABは1.5倍のまま（2.0倍に補正されない）
        ("ピカチュウ", "ほのお", "でんきショック", 4096 * 1.5),
        # ステラタイプへのテラスタルでは効果が発動しない
        # （ステラ補正込みの初回STAB 2.0倍のまま変化しない）
        ("ピカチュウ", "ステラ", "でんきショック", 4096 * 2),
    ]
)
def test_てきおうりょく_STAB補正(name: str, tera_type: Type, move_name: str, expected_modifier: float):
    battle = t.start_battle(
        team0=[Pokemon(name, ability_name="てきおうりょく", tera_type=tera_type, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    if tera_type:
        battle.actives[0].terastallize()
    t.run_move(battle, 0)
    assert battle.damage_calculator.atk_type_modifier == expected_modifier


def test_テクニシャン_アクロバット_道具を持っていないとき変動後威力で補正がかからない():
    """アクロバットは道具を持っていないとき技自身の効果で威力が110に変動する。
    テクニシャンは変動後の威力（110）で判定するため、60を超えて対象外になる。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="テクニシャン", move_names=["アクロバット"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    # 8192(4096*2) = アクロバット自身の道具無し補正(2倍)のみ。テクニシャンの1.5倍は乗らない。
    assert battle.damage_calculator.power_modifier == 8192
    assert battle.damage_calculator.final_power == 110


def test_テクニシャン_アクロバット_道具を持っているとき変動前威力で補正がかかる():
    """アクロバットは道具を持っているとき威力55のまま変動しないため、テクニシャンの
    補正（1.5倍）がかかる。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="テクニシャン", move_names=["アクロバット"],
                       item_name="いのちのたま")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144
    assert battle.damage_calculator.final_power == 82


def test_テクニシャン_こんらんの自傷では威力上昇しない():
    """こんらんによる自傷ダメージ（内部技"_こんらん"、威力40）はテクニシャンの対象外。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="テクニシャン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2},
    )
    battle.test_option.trigger_volatile = True
    battle.step()
    assert battle.damage_calculator.power_modifier == 4096


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("たいあたり", 6144),  # 威力40の技は1.5倍
        ("すてみタックル", 4096),  # 威力 > 60の技
        ("タネマシンガン", 6144),  # 連続技
    ]
)
def test_テクニシャン_威力補正(move_name, expected_modifier):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="テクニシャン", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == expected_modifier


def test_てつのこぶし_パンチグローブと累積して1_32倍になる():
    battle = t.start_battle(
        team0=[
            Pokemon(
                "ピカチュウ",
                ability_name="てつのこぶし",
                item_name="パンチグローブ",
                move_names=["マッハパンチ"],
            )
        ],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    # てつのこぶし(4915/4096) と パンチグローブ(4506/4096) が乗算されて累積する
    # 4096 * 4915 // 4096 * 4506 // 4096 = 5406（約1.32倍）
    assert battle.damage_calculator.power_modifier == 5406


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("マッハパンチ", 4915),
        ("でんきショック", 4096)
    ]
)
def test_てつのこぶし_パンチ技以外は補正なし(move_name: str, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てつのこぶし", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert expected_modifier == battle.damage_calculator.power_modifier


def test_テラスシェル_HP満タンでないと発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="テラスシェル")],
    )
    defender = battle.actives[1]
    defender.hp = defender.max_hp - 1
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier


def test_テラスシェル_かたやぶりで無効():
    """テラスシェル: かたやぶり持ちの技はテラスシェルの半減を貫通する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="テラスシェル")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.def_type_modifier


def test_テラスシェル_相性0倍の無効化技には発動しない():
    """テラスシェル: タイプ相性で無効(0倍)になる技を受けたときは特性が発動せず、そのまま無効になる。

    無効化技はダメージ計算そのものに入らず「タイプ無効」で失敗するため、
    damage_calculator は使われない（HPが減らないことと特性が発動しないことで確認する）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],  # ノーマル技
        team1=[Pokemon("ゲンガー", ability_name="テラスシェル")],  # ゴーストはノーマル技を無効化
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp
    assert not defender.ability.revealed


@pytest.mark.parametrize(
    "defender_name, move_name, expected",
    [
        ("コイル", "なみのり", 4096*0.5),       # x1 -> x1/2
        ("コイル", "ひのこ", 4096*0.5),       # x2 -> x1/2
        ("コイル", "じしん", 4096*0.5),           # x4 -> x1/2
        ("コイル", "でんきショック", 4096*0.5),   # x1/2 -> x1/2
        ("コイル", "バレットパンチ", 4096*0.25),   # x1/4 -> x1/4
    ]
)
def test_テラスシェル_等倍以上を半減(defender_name, move_name, expected):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon(defender_name, ability_name="テラスシェル")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.def_type_modifier == expected


def test_テラスチェンジ_かがくへんかガスが発動中でも発動する():
    """テラスチェンジ: 既にかがくへんかガスが発動している場に繰り出したときも発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("テラパゴス(ノーマル)", ability_name="テラスチェンジ")],
        team1=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
    )
    t.run_switch(battle, player_idx=0, new_idx=1)
    mon = battle.actives[0]
    assert mon.name == "テラパゴス(テラスタル)"


def test_テラスチェンジ_登場時にテラスタルフォルムになる():
    battle = t.start_battle(
        team0=[Pokemon("テラパゴス(ノーマル)", ability_name="テラスチェンジ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "テラパゴス(テラスタル)"


def test_テラボルテージ_かがくへんかガス解除後に特性発動ログが再度記録される():
    """テラボルテージ: かたやぶりと同様、かがくへんかガスの効果が切れて特性が
    再有効化されたときに場に出たときのログが再度記録される。"""
    battle = t.start_battle(
        team0=[Pokemon("ドガース", ability_name="かがくへんかガス"), Pokemon("コラッタ")],
        team1=[Pokemon("ゼクロム", ability_name="テラボルテージ")],
    )
    mon = battle.actives[1]
    assert not mon.ability.enabled

    def count_triggered() -> int:
        return sum(
            1 for log in battle.event_logger.logs
            if log.log == LogCode.ABILITY_TRIGGERED
            and log.idx == 1
            and log.payload is not None
            and getattr(log.payload, "ability", None) == "テラボルテージ"
        )

    assert count_triggered() == 0

    t.run_switch(battle, 0, 1)
    assert mon.ability.enabled
    assert count_triggered() == 1


def test_テラボルテージ_がんじょうを無視して一撃で倒す():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="がんじょう")],
        team1=[Pokemon("ゼクロム", ability_name="テラボルテージ", move_names=["じしん"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].hp == 0


def test_テラボルテージ_プリズムアーマーは無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ゼクロム", ability_name="テラボルテージ", move_names=["じしん"])],
        team1=[Pokemon("コイル", ability_name="プリズムアーマー")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.damage_modifier


def test_テラボルテージ_場に出たときに特性開示():
    battle = t.start_battle(
        team0=[Pokemon("ゼクロム", ability_name="テラボルテージ")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.actives[0].ability.revealed


def test_てんきや_エアロック中はフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("ポワルン", ability_name="てんきや")],
        team1=[Pokemon("ピカチュウ", ability_name="エアロック")],
        weather=("はれ", 5)
    )
    mon = battle.actives[0]
    assert mon.name == "ポワルン"


def test_てんきや_かがくへんかガス発動中はフォルムチェンジしない():
    """てんきや: かがくへんかガスで特性が無効化されている間は天候が変わってもフォルムチェンジしない。"""
    battle = t.start_battle(
        team0=[Pokemon("ポワルン", ability_name="てんきや")],
        team1=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
    )
    mon = battle.actives[0]
    assert mon.name == "ポワルン"

    battle.weather_manager.apply("あめ", 5)
    assert mon.name == "ポワルン"


def test_てんきや_かがくへんかガス解除時に即座にフォルムチェンジする():
    """てんきや: かがくへんかガスの効果が切れて特性が再有効化された瞬間、
    その時点の天候に対応したフォルムへ即座にフォルムチェンジする。"""
    battle = t.start_battle(
        team0=[Pokemon("ポワルン", ability_name="てんきや")],
        team1=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
    )
    mon = battle.actives[0]
    battle.weather_manager.apply("あめ", 5)
    assert mon.name == "ポワルン"

    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    assert mon.name == "ポワルン(あまみず)"


@pytest.mark.parametrize(
    "weather, form",
    [
        ("はれ", "ポワルン(たいよう)"),
        ("おおひでり", "ポワルン(たいよう)"),
        ("あめ", "ポワルン(あまみず)"),
        ("おおあめ", "ポワルン(あまみず)"),
        ("ゆき", "ポワルン(ゆきぐも)"),
    ],
)
def test_てんきや_フォルムチェンジ(weather: WeatherName, form: str):
    battle = t.start_battle(
        team0=[Pokemon("ポワルン", ability_name="てんきや")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather, 5),
    )
    mon = battle.actives[0]
    assert mon.name == form


def test_てんきや_フォルムチェンジ時にみずびたしを解消する():
    """てんきや: フォルムチェンジが発生すると、みずびたしによるタイプ変化を解消して
    天候に対応したタイプに戻る。"""
    battle = t.start_battle(
        team0=[Pokemon("ポワルン", ability_name="てんきや")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "みずびたし")
    assert mon.types == ["みず"]

    battle.weather_manager.apply("はれ", 5)
    assert mon.name == "ポワルン(たいよう)"
    assert mon.types == ["ほのお"]
    assert not mon.has_volatile("みずびたし")


def test_てんきや_ポワルン以外は天候変化でもフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てんきや")],
        team1=[Pokemon("コラッタ")],
        weather=("あめ", 5),
    )
    mon = battle.actives[0]
    assert mon.name == "ピカチュウ"

    battle.weather_manager.apply("はれ", 5)
    assert mon.name == "ピカチュウ"


def test_てんきや_天候なしで通常フォルム():
    battle = t.start_battle(
        team0=[Pokemon("ポワルン", ability_name="てんきや")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ポワルン"


def test_てんきや_天候変化で即座にフォルムチェンジ():
    battle = t.start_battle(
        team0=[Pokemon("ポワルン", ability_name="てんきや")],
        team1=[Pokemon("ピカチュウ")],
        weather=("あめ", 5),
    )
    mon = battle.actives[0]
    assert mon.name == "ポワルン(あまみず)"

    battle.weather_manager.apply("はれ", 5)
    assert mon.name == "ポワルン(たいよう)"


@pytest.mark.parametrize("evasion_rank", [3, -3])
def test_てんねん_攻撃側は相手の回避率ランク補正を無視する(evasion_rank):
    """てんねん攻撃側: 相手の回避率ランクが上昇・下降していても命中率が変わらない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てんねん", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.actives[1].rank["evasion"] = evasion_rank
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


@pytest.mark.parametrize(
    "move_name, stat",
    [
        ("たいあたり", "def"),
        ("ひのこ", "spd"),
    ]
)
def test_てんねん_攻撃側は防御ランク補正を無視する(move_name, stat):
    """てんねん攻撃側: 防御ランク+2でも防御の実効値がランクなし（+0）と同じになる。

    急所に当たると防御ランク補正が無効化され対照確認が崩れるため、
    random.random() を固定して急所を発生させない。
    """
    # てんねんなし: 防御ランク+2でfinal_defenseが上昇する
    without_ten = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    without_ten.random.random = lambda: 0.9
    without_ten.actives[1].rank[stat] = 2
    t.run_move(without_ten, 0)
    defense_with_rank = without_ten.damage_calculator.final_defense

    # ランクなし: 通常の防御値
    without_rank = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    without_rank.random.random = lambda: 0.9
    t.run_move(without_rank, 0)
    defense_without_rank = without_rank.damage_calculator.final_defense

    # てんねんあり: 防御ランク+2でもランクなしと同じ防御値になる
    with_ten = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てんねん", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    with_ten.random.random = lambda: 0.9
    with_ten.actives[1].rank[stat] = 2
    t.run_move(with_ten, 0)
    defense_tennen = with_ten.damage_calculator.final_defense

    assert defense_with_rank > defense_without_rank  # ランクあり > ランクなし（対照確認）
    assert defense_tennen == defense_without_rank  # てんねんはランクを無視する


@pytest.mark.parametrize(
    "move_name, stat",
    [
        ("たいあたり", "atk"),
        ("ひのこ", "spa"),
    ]
)
def test_てんねん_防御側はACランク無視(move_name, stat):
    """てんねん防御側: 攻撃ランク+2でも攻撃の実効値がランクなし（+0）と同じになる。"""
    # てんねんなし: 攻撃ランク+2でfinal_attackが上昇する
    without_ten = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    without_ten.actives[0].rank[stat] = 2
    t.run_move(without_ten, 0)
    attack_with_rank = without_ten.damage_calculator.final_attack

    # ランクなし: 通常の攻撃値
    without_rank = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(without_rank, 0)
    attack_without_rank = without_rank.damage_calculator.final_attack

    # てんねんあり: 攻撃ランク+2でもランクなしと同じ攻撃値になる
    with_ten = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="てんねん")],
        accuracy=100,
    )
    with_ten.actives[0].rank[stat] = 2
    t.run_move(with_ten, 0)
    attack_tennen = with_ten.damage_calculator.final_attack

    assert attack_with_rank > attack_without_rank  # ランクあり > ランクなし（対照確認）
    assert attack_tennen == attack_without_rank  # てんねんはランクを無視する


@pytest.mark.parametrize("accuracy_rank", [3, -3])
def test_てんねん_防御側は相手の命中率ランク補正を無視する(accuracy_rank):
    """てんねん防御側: 相手の命中率ランクが上昇・下降していても命中率が変わらない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="てんねん")],
    )
    battle.actives[0].rank["accuracy"] = accuracy_rank
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


def test_てんのめぐみ_発動率が50パーセント以上の技は100パーセントになる():
    """てんのめぐみ: 追加効果発動率が50%以上の技（チャージビーム70%）は2倍計算後に
    100%へ上限で丸められる。乱数0.99は元の70%では外れるが、てんのめぐみありでは
    100%になるため必ず発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てんのめぐみ", move_names=["チャージビーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.99
    t.run_move(battle, 0)
    assert battle.actives[0].rank["spa"] == 1


def test_てんのめぐみ_追加効果確率が2倍になる():
    """てんのめぐみ: 20%追加効果が2倍（40%）になることを、シャドーボールを使って確認する。
    乱数0.35はてんのめぐみなし（20%）では発動しないが、てんのめぐみあり（40%）では発動する。"""
    # てんのめぐみなし: 乱数0.35ではD低下が発動しない（境界: 0.20未満で発動）
    without_megumi = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["シャドーボール"])],
        team1=[Pokemon("ゼニガメ")],
        accuracy=100,
    )
    without_megumi.random.random = lambda: 0.35
    t.run_move(without_megumi, 0)
    assert without_megumi.actives[1].rank["spd"] == 0

    # てんのめぐみあり: 乱数0.35でD低下が発動する（確率2倍で境界: 0.40未満で発動）
    with_megumi = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="てんのめぐみ", move_names=["シャドーボール"])],
        team1=[Pokemon("ゼニガメ")],
        accuracy=100,
    )
    with_megumi.random.random = lambda: 0.35
    t.run_move(with_megumi, 0)
    assert with_megumi.actives[1].rank["spd"] == -1


def test_でんきにかえる_被弾でじゅうでん状態になる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="でんきにかえる")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].has_volatile("じゅうでん")


def test_でんきにかえる_こらえるで実ダメージ0でも発動する():
    """でんきにかえる: こらえるでHP1のまま耐えた（実ダメージ0）ときも発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="でんきにかえる")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    holder = battle.actives[0]
    holder.hp = 1
    battle.volatile_manager.apply(holder, "こらえる")
    t.fix_damage(battle, 9999)

    t.run_move(battle, 1)

    assert holder.hp == 1
    assert not holder.fainted
    assert holder.has_volatile("じゅうでん")


def test_でんきにかえる_ひんしになったときは発動しない():
    """でんきにかえる: その攻撃技でひんしになったときは発動しない
    （スカーレット・バイオレット Ver.1.2.0 以降の仕様）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="でんきにかえる")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.fix_damage(battle, defender.max_hp)

    t.run_move(battle, 1)

    assert defender.fainted
    assert not defender.has_volatile("じゅうでん")


def test_でんきにかえる_みがわりに阻まれたときは発動しない():
    """でんきにかえる: みがわり状態で攻撃を防いだときは発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="でんきにかえる")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    holder = battle.actives[0]
    battle.volatile_manager.apply(holder, "みがわり", hp=999)

    t.run_move(battle, 1)

    assert not holder.has_volatile("じゅうでん")


def test_とうそうしん_こんらん自傷ダメージには補正なし():
    """とうそうしん: こんらんの自傷ダメージには威力補正がかからない（第五世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="とうそうしん", gender="male")],
        team1=[Pokemon("カビゴン", gender="male")],
        volatile0={"こんらん": 2},
    )
    attacker = battle.actives[0]
    battle.test_option.trigger_volatile = True
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096
    assert attacker.hp < attacker.max_hp


@pytest.mark.parametrize(
    "gendar0, gendar1, expected_modifier",
    [
        ("male", "male", 5120),
        ("female", "female", 5120),
        ("male", "female", 3072),
        ("male", "", 4096),
        ("", "", 4096),
    ]
)
def test_とうそうしん_威力補正(gendar0: Gender, gendar1: Gender, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="とうそうしん", move_names=["たいあたり"], gender=gendar0)],
        team1=[Pokemon("カビゴン", gender=gendar1)],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert expected_modifier == battle.damage_calculator.power_modifier


def test_とびだすなかみ_KOされなければダメージなし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="とびだすなかみ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.fainted
    assert attacker.hp == attacker.max_hp


def test_とびだすなかみ_KOされると攻撃者に反撃ダメージ():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="とびだすなかみ")],
    )
    attacker, defender = battle.actives
    t.fix_damage(battle, 999)
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.hp == attacker.max_hp - defender.max_hp


def test_とびだすなかみ_多段技では最初のヒット前HPが基準():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["すいりゅうれんだ"])],
        team1=[Pokemon("ピカチュウ", ability_name="とびだすなかみ")],
    )
    attacker, defender = battle.actives
    t.fix_damage(battle, 50)
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.hp == attacker.max_hp - defender.max_hp


def test_とびだすなかみ_攻撃者がじばくで先にひんしなら発動しない():
    """とびだすなかみ: じばく等で攻撃者がすでにひんしになって場にいない場合は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じばく"])],
        team1=[Pokemon("ピカチュウ", ability_name="とびだすなかみ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.fix_damage(battle, 999)
    t.run_move(battle, 0)
    assert attacker.fainted
    assert defender.fainted
    assert not defender.ability.revealed


def test_とびだすなかみ_攻撃者のみがわりを無視してダメージを与える():
    """とびだすなかみ: 攻撃者がみがわり状態でも、その実HPに直接ダメージを与える。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="とびだすなかみ")],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(attacker, "みがわり", hp=999)
    t.fix_damage(battle, 999)
    t.run_move(battle, 0)
    assert defender.fainted
    assert attacker.hp == attacker.max_hp - defender.max_hp
    assert attacker.has_volatile("みがわり")


def test_とびだすなかみ_状態異常ダメージのひんしでは発動しない():
    """とびだすなかみ: 攻撃技以外（どく等）のダメージでひんしになった場合は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ", ability_name="とびだすなかみ")],
    )
    attacker, defender = battle.actives
    battle.modify_hp(defender, v=-(defender.max_hp - 1))
    battle.ailment_manager.apply(defender, "どく")
    t.end_turn(battle)
    assert defender.fainted
    assert not defender.ability.revealed
    assert attacker.hp == attacker.max_hp


@pytest.mark.parametrize(
    "move_name, result",
    [
        ("たいあたり", True),
        ("でんきショック", True),
        ("すなかけ", False),
    ]
)
def test_とびだすハバネロ_被弾するとやけどにする(move_name: str, result: bool):
    """とびだすハバネロ: 攻撃技のダメージを受けた後、攻撃者をやけど状態にする。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="とびだすハバネロ")],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert attacker.has_ailment("やけど") is result


@pytest.mark.parametrize(
    "move_name, result",
    [
        ("たいあたり", True),
        ("でんきショック", False),
    ]
)
def test_とれないにおい_接触した相手の特性を上書き(move_name: str, result: bool):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("カビゴン", ability_name="とれないにおい")],
        accuracy=100,
    )
    attacker, _ = battle.actives
    assert attacker.ability.name != "とれないにおい"
    t.run_move(battle, 0)
    assert (attacker.ability.name == "とれないにおい") is result


def test_トレース_uncopyable特性だと不発():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="トレース")],
        team1=[Pokemon("ピカチュウ", ability_name="トレース")],
    )
    assert battle.actives[0].ability.base_name == "トレース"
    assert battle.actives[0].ability.revealed is False  # 不発なので False のまま


def test_トレース_いかくをコピーすると即発動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="トレース")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    assert battle.actives[0].ability.base_name == "いかく"
    assert battle.actives[1].rank["atk"] == -1


def test_トレース_交代で元の特性に戻る():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="トレース"),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )

    tracer = battle.player_states[battle.players[0]].team[0]
    assert tracer.ability.base_name == "いかく"

    t.run_switch(battle, 0, 1)
    assert tracer.ability.base_name == "トレース"


@pytest.mark.parametrize("roll, expected_count", [(2, 2), (5, 5)])
def test_どくくぐつ_こんらんの継続ターンは2から5ターン(roll: int, expected_count: int):
    """どくくぐつ: 付与されるこんらんは通常のこんらん技と同じ2〜5ターン継続する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくくぐつ")],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    battle.random.randint = lambda a, b: roll
    assert battle.ailment_manager.apply(defender, "どく", source=attacker)
    assert defender.volatiles["こんらん"].count == expected_count


def test_どくくぐつ_スキルスワップは失敗する():
    """どくくぐつ: この特性に対するスキルスワップは失敗する（上書き自体は可能）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["スキルスワップ"], ability_name="いかく")],
        team1=[Pokemon("カビゴン", ability_name="どくくぐつ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.ability.base_name == "いかく"
    assert defender.ability.base_name == "どくくぐつ"


@pytest.mark.parametrize(
    "ailment_name, result",
    [
        ("どく", True),
        ("もうどく", True),
        ("まひ", False),
    ]
)
def test_どくくぐつ_どく付与時にこんらん付与(ailment_name: AilmentName, result: bool):
    """どくくぐつ: どく付与と同時に相手がこんらんになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくくぐつ")],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    assert battle.ailment_manager.apply(defender, ailment_name, source=attacker)
    assert defender.has_volatile("こんらん") is result


def test_どくくぐつ_既にこんらん状態なら追加付与されず特性バーも表示されない():
    """どくくぐつ: 相手がすでにこんらん状態の場合、こんらんは上書きされず特性バーも表示されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくくぐつ")],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "こんらん", count=3)
    assert battle.ailment_manager.apply(defender, "どく", source=attacker)
    assert defender.volatiles["こんらん"].count == 3  # 上書きされない
    assert attacker.ability.revealed is False  # どくくぐつの特性バーは表示されない


def test_どくくぐつ_自傷での毒付与ではこんらんしない():
    """どくくぐつ: どくどくだま・どくびし等の自傷（source と target が同一）ではこんらんしない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくくぐつ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    assert battle.ailment_manager.apply(mon, "どく", source=mon)
    assert not mon.has_volatile("こんらん")


def test_どくげしょう_こらえるでHP1のまま耐えたときも発動する():
    """どくげしょう: こらえるでHP1のまま耐えた（実HPダメージ0）ときも発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="どくげしょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = 1
    battle.volatile_manager.apply(defender, "こらえる")
    t.fix_damage(battle, 9999)

    t.run_move(battle, 1)

    assert defender.hp == 1
    foe_side = battle.get_side(battle.players[1])
    assert foe_side.get("どくびし").count == 1


def test_どくげしょう_みがわりに阻まれたときは発動しない():
    """どくげしょう: みがわりに攻撃を防がれたとき（実HPダメージ0）は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="どくげしょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)

    t.run_move(battle, 1)

    foe_side = battle.get_side(battle.players[1])
    assert foe_side.get("どくびし").count == 0


def test_どくげしょう_物理技をくらうとどくびしを設置():
    """どくげしょう: どくびし1層のとき被弾すると2層になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ハガネール", ability_name="どくげしょう")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    foe_side = battle.get_side(battle.players[1])
    for i in range(3):
        t.run_move(battle, 1)
        assert foe_side.get("どくびし").count == min(2, i+1)
    assert battle.actives[0].ability.revealed


def test_どくげしょう_特殊技では発動しない():
    """どくげしょう: 特殊技を受けても発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="どくげしょう")],
        team1=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
    )
    t.run_move(battle, 1)
    foe_side = battle.get_side(battle.players[1])
    assert foe_side.get("どくびし").count == 0
    assert not battle.actives[0].ability.revealed


def test_どくげしょう_直接攻撃でない物理技でも発動する():
    """どくげしょう: 直接攻撃でない物理技（じしん）を受けても発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="どくげしょう")],
        team1=[Pokemon("ピカチュウ", move_names=["じしん"])],
    )
    t.run_move(battle, 1)
    foe_side = battle.get_side(battle.players[1])
    assert foe_side.get("どくびし").count == 1


def test_どくしゅ_どく付与():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくしゅ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    _, defender = battle.actives

    orig_random = battle.random.random
    battle.random.random = lambda: 0.0
    try:
        t.run_move(battle, 0)
    finally:
        battle.random.random = orig_random

    assert defender.has_ailment("どく")


def test_どくしゅ_パンチグローブ所持時はパンチ技に発動しない():
    battle = t.start_battle(
        team0=[Pokemon(
            "ピカチュウ",
            ability_name="どくしゅ",
            item_name="パンチグローブ",
            move_names=["ほのおのパンチ"],
        )],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    _, defender = battle.actives

    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)

    # ほのおのパンチ自体の追加効果でやけどになるが、パンチグローブで接触技でなくなるため
    # どくしゅ由来のどく状態にはならない
    assert not defender.has_ailment("どく")


def test_どくしゅ_みがわりに阻まれたときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくしゅ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    _, defender = battle.actives
    battle.volatile_manager.apply(defender, "みがわり", hp=999)

    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)

    assert not defender.ailment.is_active


def test_どくしゅ_りんぷん所持相手には発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくしゅ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="りんぷん")],
    )
    _, defender = battle.actives

    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)

    assert not defender.ailment.is_active


def test_どくしゅ_特性発動が記録される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくしゅ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives

    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)

    assert defender.has_ailment("どく")
    assert attacker.ability.revealed


def test_どくしゅ_連続攻撃技は1発ごとに発動判定がある():
    """ダブルアタック(2回攻撃)で resolve_secondary_chance の呼び出し回数を数え、
    ヒットごとに独立した発動判定が行われることを確認する（命中判定・急所判定でも
    battle.random.random() が呼ばれるため、単純な乱数呼び出し回数では判定できない）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくしゅ", move_names=["ダブルアタック"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )

    count = 0
    orig_resolve_secondary_chance = battle.resolve_secondary_chance

    def counting_resolve_secondary_chance(ctx, chance):
        nonlocal count
        count += 1
        return orig_resolve_secondary_chance(ctx, chance)

    battle.resolve_secondary_chance = counting_resolve_secondary_chance
    t.fix_random(battle, 0.5)  # どくの発動確率(30%)を外れる値にして状態異常の重複判定を避ける
    t.run_move(battle, 0)

    assert count == 2


def test_どくしゅ_非接触技では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("イーブイ", ability_name="どくしゅ", move_names=["はどうだん"])],
        team1=[Pokemon("ピカチュウ")],
    )
    _, defender = battle.actives

    battle.random.random = lambda: 0.0
    t.run_move(battle, 0)

    assert not defender.ailment.is_active


def test_どくのくさり_30パーセントでもうどくを付与する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくのくさり", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.29)
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "もうどく"


def test_どくのくさり_おんみつマント所持相手には発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくのくさり", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="おんみつマント")],
        accuracy=100,
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_どくのくさり_こらえるでHP1のまま耐えたときも発動する():
    """どくのくさり: こらえるでHP1のまま耐えた（実HPダメージ0）ときも発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくのくさり", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = 1
    battle.volatile_manager.apply(defender, "こらえる")
    t.fix_damage(battle, 9999)
    t.fix_random(battle, 0.0)

    t.run_move(battle, 0)

    assert defender.hp == 1
    assert defender.ailment.name == "もうどく"


def test_どくのくさり_どくタイプの相手には発動しない():
    """どくのくさり: もうどく状態にできない相手（どくタイプ）には発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくのくさり", move_names=["たいあたり"])],
        team1=[Pokemon("ベトベトン")],
        accuracy=100,
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_どくのくさり_みがわりに阻まれたときは発動しない():
    """どくのくさり: みがわりに攻撃を防がれたとき（実HPダメージ0）は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくのくさり", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.fix_random(battle, 0.0)

    t.run_move(battle, 0)

    assert not defender.ailment.is_active


def test_どくのくさり_りんぷん所持相手には発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくのくさり", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="りんぷん")],
        accuracy=100,
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_どくのくさり_直接攻撃でない技でも発動する():
    """どくのくさり: 直接攻撃でない技（はどうだん）でも発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくのくさり", move_names=["はどうだん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "もうどく"


def test_どくのくさり_確率外ではもうどくにならない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくのくさり", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_damage(battle, 1)
    t.fix_random(battle, 0.31)
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_どくのトゲ_こらえるでHP1のまま耐えたときも発動する():
    """どくのトゲ: こらえるでHP1のまま耐えた（実HPダメージ0）ときも発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="どくのトゲ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    defender.hp = 1
    battle.volatile_manager.apply(defender, "こらえる")
    t.fix_damage(battle, 9999)
    t.fix_random(battle, 0.0)

    t.run_move(battle, 1)

    assert defender.hp == 1
    attacker = battle.actives[1]
    assert attacker.has_ailment("どく")


def test_どくのトゲ_みがわりに阻まれたときは発動しない():
    """どくのトゲ: みがわりに攻撃を防がれたとき（実HPダメージ0）は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="どくのトゲ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.fix_random(battle, 0.0)

    t.run_move(battle, 1)

    attacker = battle.actives[1]
    assert not attacker.ailment.is_active


def test_どくぼうそう_どく状態でない場合は倍率なし():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくぼうそう", move_names=["ねっとう"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


@pytest.mark.parametrize(
    "move_name, expected_modifier",
    [
        ("たいあたり", 6144),
        ("でんきショック", 4096),
    ]
)
def test_どくぼうそう_どく状態で物理技の威力が1_5倍(move_name: str, expected_modifier: int):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくぼうそう", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("どく", None),
    )
    t.run_move(battle, 0)
    assert expected_modifier == battle.damage_calculator.power_modifier


def test_どくぼうそう_もうどく状態で物理技の威力が1_5倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくぼうそう", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("もうどく", None),
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 6144


def test_どしょく_HP満タンなら無効化のみで回復しない():
    battle = t.start_battle(
        team0=[Pokemon("ミミズズ", ability_name="どしょく")],
        team1=[Pokemon("カビゴン", move_names=["じしん"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.hp == mon.max_hp
    assert mon.ability.revealed


def test_どしょく_クリアチャーム所持でもどしょくが優先発動する():
    """どしょく: クリアチャーム所持で命中ランク低下自体が無効なはずのすなかけでも、
    ランク低下無効化より先にどしょくが発動して技自体を無効化し回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("ミミズズ", ability_name="どしょく", item_name="クリアチャーム")],
        team1=[Pokemon("カビゴン", move_names=["すなかけ"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.hp == 1 + mon.max_hp // 4
    assert mon.ability.revealed


def test_どしょく_じめん変化技も無効化して回復する():
    """どしょく: すなかけのようなじめんタイプの変化技を受けても無効化し、最大HPの1/4回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("ミミズズ", ability_name="どしょく")],
        team1=[Pokemon("カビゴン", move_names=["すなかけ"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.hp == 1 + mon.max_hp // 4
    assert mon.rank["accuracy"] == 0


def test_どしょく_まきびしなど場を対象とした技には発動しない():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("ミミズズ", ability_name="どしょく", move_names=["まきびし"])],
    )
    t.run_move(battle, 1)
    assert battle.side_managers[0].fields["まきびし"].is_active
    assert not battle.actives[1].ability.revealed


def test_どしょく_まもるで防がれたときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ミミズズ", ability_name="どしょく")],
        team1=[Pokemon("カビゴン", move_names=["じしん"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    battle.volatile_manager.apply(mon, "まもる", count=1)
    t.run_move(battle, 1)
    assert mon.hp == 1
    assert not mon.ability.revealed


def test_どしょく_みがわり状態でじめん技を受けても発動して回復する():
    battle = t.start_battle(
        team0=[Pokemon("ミミズズ", ability_name="どしょく")],
        team1=[Pokemon("カビゴン", move_names=["じしん"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "みがわり", count=mon.max_hp // 4)
    mon.hp = mon.max_hp // 2
    hp_before = mon.hp
    t.run_move(battle, 1)
    assert mon.hp == hp_before + mon.max_hp // 4
    assert mon.has_volatile("みがわり")


def test_どしょく_連続攻撃技も無効化するが回復は1回のみ():
    battle = t.start_battle(
        team0=[Pokemon("ミミズズ", ability_name="どしょく")],
        team1=[Pokemon("カビゴン", move_names=["ボーンラッシュ"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.hp == 1 + mon.max_hp // 4


def test_どんかん_いかくを無効化する():
    """どんかん: いかくによるこうげきランク低下を無効化する（第八世代以降）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どんかん")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    assert battle.actives[0].rank["atk"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
