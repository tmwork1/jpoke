"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.data.item import ITEMS
from jpoke.data.signature_items import MEMORY_TO_TYPE
from jpoke.enums import Command
from jpoke.types import Stat, WeatherName, TerrainName

from .. import test_utils as t

AR_SYSTEM_MEMORY_CASES = [
    (memory_item_name, expected_type)
    for memory_item_name, expected_type in MEMORY_TO_TYPE.items()
    if memory_item_name in ITEMS
]

ability_weather_defaultcount = [
    ("あめふらし", "あめ", 5),
    ("ひでり", "はれ", 5),
    ("すなおこし", "すなあらし", 5),
    ("ゆきふらし", "ゆき", 5),
    ("おわりのだいち", "おおひでり", 1),
    ("はじまりのうみ", "おおあめ", 1),
    ("デルタストリーム", "らんきりゅう", 1),
]
abilities = [x[0] for x in ability_weather_defaultcount]
weathers = [x[1] for x in ability_weather_defaultcount]
normal_weathers = weathers[:4]
strong_weathers = weathers[4:]


def test_ARシステム_はたきおとすは相手の道具に影響されない():
    """一方的な除去（is_exchange=False）では、相手がメモリを持っていても判定に影響しない"""
    battle = t.start_battle(
        team0=[Pokemon("シルヴァディ", ability_name="ARシステム", item_name="いのちのたま")],
        team1=[Pokemon("ピカチュウ", item_name="フェアリーメモリ")],
    )
    target, source = battle.actives
    assert battle.item_manager.can_change_item(target=target, source=source)


@pytest.mark.parametrize(
    "memory_item_name, expected_type",
    AR_SYSTEM_MEMORY_CASES,
)
def test_ARシステム_メモリで対応タイプになる(memory_item_name: str, expected_type: str):
    battle = t.start_battle(
        team0=[Pokemon("シルヴァディ", ability_name="ARシステム", item_name=memory_item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type == expected_type
    assert mon.ability.revealed is False  # ARシステムは開示されない


def test_ARシステム_メモリなしでタイプ変更なし():
    battle = t.start_battle(
        team0=[Pokemon("シルヴァディ", ability_name="ARシステム")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.ability_override_type is None
    assert mon.ability.revealed is False  # メモリなしは不発なので False


def test_ARシステム_メモリなしなら自分の道具変更は防がれない():
    battle = t.start_battle(
        team0=[Pokemon("シルヴァディ", ability_name="ARシステム", item_name="いのちのたま")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives
    assert battle.item_manager.can_change_item(target=target, source=source)


def test_ARシステム_相手がメモリを持たなければ通常の道具変更を防がない():
    """交換判定であっても、自分・相手ともメモリを持たなければ道具変更は妨げられない"""
    battle = t.start_battle(
        team0=[Pokemon("シルヴァディ", ability_name="ARシステム")],
        team1=[Pokemon("ピカチュウ", item_name="いのちのたま")],
    )
    target, source = battle.actives
    assert battle.item_manager.can_change_item(target=target, source=source, is_exchange=True)


def test_ARシステム_相手がメモリを持つ場合トリックすりかえ相当の交換が失敗する():
    """相手がメモリを持っている場合、自分がメモリを持っていなくても道具交換自体が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("シルヴァディ", ability_name="ARシステム")],
        team1=[Pokemon("ピカチュウ", item_name="フェアリーメモリ")],
    )
    target, source = battle.actives
    before = [mon.item.name for mon in battle.actives]
    assert not battle.item_manager.swap_items()
    assert [mon.item.name for mon in battle.actives] == before


def test_ARシステム_自分のメモリの奪取交換を防ぐ():
    battle = t.start_battle(
        team0=[Pokemon("シルヴァディ", ability_name="ARシステム", item_name="ファイトメモリ")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives
    assert not battle.item_manager.can_change_item(target=target, source=source)


def test_アイスフェイス_エアロック中はゆき変化でフォルムチェンジしない():
    battle = t.start_battle(
        team0=[Pokemon("コオリッポ(ナイス)", ability_name="アイスフェイス")],
        team1=[Pokemon("ラティアス", ability_name="エアロック")],
    )
    mon = battle.actives[0]
    battle.weather_manager.apply("ゆき", 5)
    assert mon.name == "コオリッポ(ナイス)"


def test_アイスフェイス_かたやぶりで物理技のダメージを防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("コオリッポ(アイス)", ability_name="アイスフェイス")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert defender.name == "コオリッポ(アイス)"


def test_アイスフェイス_かたやぶりのゆきげしきでは戻れない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ゆきげしき"])],
        team1=[Pokemon("コオリッポ(ナイス)", ability_name="アイスフェイス")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert battle.raw_weather.name == "ゆき"
    assert defender.name == "コオリッポ(ナイス)"


def test_アイスフェイス_ナイスフェイスでは物理技を防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("コオリッポ(ナイス)", ability_name="アイスフェイス")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp


def test_アイスフェイス_ゆきが発生するとアイスフェイスに戻る():
    battle = t.start_battle(
        team0=[Pokemon("コオリッポ(ナイス)", ability_name="アイスフェイス")],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.weather_manager.apply("ゆき", 5)
    assert battle.actives[0].name == "コオリッポ(アイス)"


def test_アイスフェイス_ゆき状態の場に登場するとアイスフェイスに戻る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("コオリッポ(ナイス)", ability_name="アイスフェイス")],
        team1=[Pokemon("ピカチュウ")],
        weather=("ゆき", 5),
    )
    mon = battle.player_states[battle.players[0]].team[1]
    assert mon.name == "コオリッポ(ナイス)"  # ベンチではまだナイスフェイス
    t.run_switch(battle, 0, 1)
    assert battle.actives[0].name == "コオリッポ(アイス)"


def test_アイスフェイス_物理技を無効にしてフォルムチェンジ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("コオリッポ(アイス)", ability_name="アイスフェイス")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp == defender.max_hp
    assert defender.name == "コオリッポ(ナイス)"


def test_アイスフェイス_特殊技のダメージを防がない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("コオリッポ(アイス)", ability_name="アイスフェイス")],
    )
    _, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hp < defender.max_hp
    assert defender.name == "コオリッポ(アイス)"


def test_アイスボディ_かいふくふうじ中は回復しない():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="アイスボディ")],
        team1=[Pokemon("ピカチュウ")],
        weather=("ゆき", 5),
        volatile0={"かいふくふうじ": 3},
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_アイスボディ_ノーてんき下では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="アイスボディ")],
        team1=[Pokemon("ピカチュウ", ability_name="ノーてんき")],
        weather=("ゆき", 5),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_アイスボディ_ゆき以外では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="アイスボディ")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_アイスボディ_同ターンに瀕死になったポケモンは回復しない():
    """アイスボディ: 同ターン中の攻撃で先にHPが0になったポケモンは、
    ターン終了時のアイスボディ回復を受けずに瀕死のままとなる"""
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="アイスボディ"), Pokemon("コラッタ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        weather=("ゆき", 5),
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.hp == 0
    assert mon.fainted
    t.end_turn(battle)
    assert mon.hp == 0
    assert mon.fainted


def test_あくしゅう_一撃必殺技には効果がない():
    """あくしゅう: 一撃必殺技には効果が無い（追加の乱数判定が発生しないことで確認する）

    きあいのタスキで耐えた場合の挙動も合わせて確認する。
    """
    def count_random_calls(has_ability: bool) -> int:
        kwargs = {"ability_name": "あくしゅう"} if has_ability else {}
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", move_names=["じわれ"], **kwargs)],
            team1=[Pokemon("ピカチュウ", item_name="きあいのタスキ")],
            accuracy=100,
        )
        count = 0

        def counting_random() -> float:
            nonlocal count
            count += 1
            return 0.5

        battle.random.random = counting_random
        t.run_move(battle, 0)
        assert battle.actives[1].hp == 1
        return count

    assert count_random_calls(True) == count_random_calls(False)


def test_あくしゅう_元々ひるみ効果がある技には重複しない():
    """あくしゅう: 元々ひるみの追加効果がある技（エアスラッシュ等）には
    重複して効果が発動しない（追加の乱数判定が発生しないことで確認する）"""
    def count_random_calls(has_ability: bool) -> int:
        kwargs = {"ability_name": "あくしゅう"} if has_ability else {}
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", move_names=["エアスラッシュ"], **kwargs)],
            team1=[Pokemon("ピカチュウ")],
            accuracy=100,
        )
        count = 0

        def counting_random() -> float:
            nonlocal count
            count += 1
            return 0.5

        battle.random.random = counting_random
        t.run_move(battle, 0)
        return count

    assert count_random_calls(True) == count_random_calls(False)


def test_あくしゅう_攻撃時10パーセントでひるみを付与する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あくしゅう", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    t.fix_damage(battle, 1)
    battle.random.random = lambda: 0.09
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_あくしゅう_確率外ではひるみを付与しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あくしゅう", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
    )
    t.fix_damage(battle, 1)
    battle.random.random = lambda: 0.11
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("ひるみ")


def test_あとだし_あとだし同士では素早さの高い方が先攻():
    """あとだし: 双方があとだしを持つ場合、後攻ティアが同じになるため素早さの高い方が先攻になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あとだし", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="あとだし", move_names=["たいあたり"])],
    )
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[0]  # 素早さで勝るピカチュウが先攻


def test_あとだし_せんせいのツメ発動で効果が無くなる():
    """あとだし: せんせいのツメが発動すると後攻ティア補正が相殺され、素早さの高い方が先攻になる。"""
    battle = t.start_battle(
        team0=[Pokemon(
            "ピカチュウ", ability_name="あとだし", item_name="せんせいのツメ",
            move_names=["たいあたり"],
        )],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.fix_random(battle, 0.0)  # < 0.2 → せんせいのツメ発動
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[0]  # 素早さで勝るピカチュウが先攻（あとだし効果は相殺）


def test_あとだし_トリックルームでも後攻():
    """あとだし: トリックルーム状態でも最後に行動する（素早さ逆転の影響を受けない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あとだし")],
        team1=[Pokemon("ピカチュウ")],
        field={"トリックルーム": 5},
    )
    order = t.get_action_order(battle)
    assert order[-1] == battle.actives[0]


def test_あとだし_同優先度で最後に行動():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あとだし")],
        team1=[Pokemon("ピカチュウ")],
    )
    order = t.get_action_order(battle)
    assert order[-1] == battle.actives[0]


def test_あとだし_技優先度が優先される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あとだし", move_names=["でんこうせっか"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    order = t.get_action_order(battle)
    assert order[0] == battle.actives[0]


def test_アナライズ_こんらんの自傷では威力上昇しない():
    """アナライズ: 後攻でも、こんらんによる自傷ダメージ（内部技"_こんらん"）には
    威力補正がかからない。
    """
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="アナライズ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"こんらん": 2},
    )
    battle.test_option.trigger_volatile = True
    battle.step()
    assert 4096 == battle.damage_calculator.power_modifier


def test_アナライズ_先攻なら威力据え置き():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="アナライズ", move_names=["でんきショック"])],
        team1=[Pokemon("コイル")],
    )
    battle.step()
    assert 4096 == battle.damage_calculator.power_modifier


def test_アナライズ_後攻なら威力上昇():
    battle = t.start_battle(
        team0=[Pokemon("コイル", ability_name="アナライズ", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ")],
    )
    battle.step()
    assert 5325 == battle.damage_calculator.power_modifier


def test_アナライズ_相手が交代した場合は威力上昇():
    """アナライズ: 自分より速い場合でも、相手がその場で交代した場合は
    行動順として相手（交代）→自分（技）の順になるため威力補正がかかる。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="アナライズ", move_names=["でんきショック"])],
        team1=[Pokemon("カビゴン"), Pokemon("コイル")],
    )
    t.reserve_command(battle, command0=Command.MOVE_0, command1=Command.SWITCH_1)
    battle.step()
    assert 5325 == battle.damage_calculator.power_modifier


def test_あまのじゃく_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あまのじゃく")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[0].boosts["atk"] == -1


def test_あまのじゃく_相手の能力を下げる技は反転しない():
    """あまのじゃくは自分自身が対象（target）のランク変化のみ反転する。
    相手の能力を下げる技を使った場合は自分がsource側なので反転しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あまのじゃく", move_names=["なきごえ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert battle.actives[1].boosts["atk"] == -1
    assert battle.actives[0].boosts["atk"] == 0


def test_あまのじゃく_能力変化の符号反転():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あまのじゃく")],
        team1=[Pokemon("ピカチュウ")],
    )
    target, source = battle.actives

    stats = {"atk": 1, "def": -2, "spa": 3, "spd": -4, "spe": 1, "accuracy": -2, "evasion": 3}
    battle.modify_stats(target, stats, source=source)
    for stat, change in stats.items():
        assert target.boosts[stat] == max(-6, min(6, -change))


def test_あめうけざら_あめ以外では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="あめうけざら")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5),
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, v=-50, reason="")
    before = mon.hp
    t.end_turn(battle)
    assert mon.hp == before


def test_あめうけざら_かいふくふうじ中は回復しない():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="あめうけざら")],
        team1=[Pokemon("ピカチュウ")],
        weather=("あめ", 5),
        volatile0={"かいふくふうじ": 3},
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_あめうけざら_ノーてんき下では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="あめうけざら")],
        team1=[Pokemon("ピカチュウ", ability_name="ノーてんき")],
        weather=("あめ", 5),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_あめうけざら_ばんのうがさ所持時は発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="あめうけざら", item_name="ばんのうがさ")],
        team1=[Pokemon("ピカチュウ")],
        weather=("あめ", 5),
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_あめうけざら_同ターンに瀕死になったポケモンは回復しない():
    """あめうけざら: 同ターン中の攻撃で先にHPが0になったポケモンは、
    ターン終了時のあめうけざら回復を受けずに瀕死のままとなる"""
    battle = t.start_battle(
        team0=[Pokemon("ヤドン", ability_name="あめうけざら"), Pokemon("コラッタ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        weather=("あめ", 5),
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.hp == 0
    assert mon.fainted
    t.end_turn(battle)
    assert mon.hp == 0
    assert mon.fainted


def test_アロマベール_あくびは防がない():
    """アロマベール: メンタル系以外の状態変化(あくびのねむけ)は防がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="アロマベール")],
        team1=[Pokemon("カビゴン", move_names=["あくび"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.actives[0].has_volatile("ねむけ")


def test_アロマベール_かたやぶりで無効化されない():
    """アロマベール: かたやぶりで狙われたメンタル攻撃は防げない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="アロマベール")],
        team1=[Pokemon("カビゴン", ability_name="かたやぶり", move_names=["ちょうはつ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)
    assert battle.actives[0].has_volatile("ちょうはつ")


def test_アロマベール_のろわれボディの接触時付与を防ぐ():
    """アロマベール: 特性のろわれボディによるかなしばり付与も防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="のろわれボディ")],
        team1=[Pokemon("ピカチュウ", ability_name="アロマベール", move_names=["たいあたり"])],
    )
    battle.random.random = lambda: 0.0  # 確率操作
    t.run_move(battle, 1)
    assert not battle.actives[1].has_volatile("かなしばり")


def test_アロマベール_メロメロボディの接触時付与を防ぐ():
    """アロマベール: 特性メロメロボディによるメロメロ付与も防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メロメロボディ", gender="female")],
        team1=[Pokemon("カビゴン", ability_name="アロマベール", move_names=["たいあたり"], gender="male")],
    )
    battle.random.random = lambda: 0.0  # 確率操作
    t.run_move(battle, 1)
    assert not battle.actives[1].has_volatile("メロメロ")


def test_いかく_みがわり状態の相手には無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みがわり"])],
        team1=[Pokemon("コラッタ"), Pokemon("カビゴン", ability_name="いかく")],
    )
    t.run_move(battle, 0)
    t.run_switch(battle, 1, 1)
    assert battle.actives[0].boosts["atk"] == 0


def test_いかく_登場時に相手攻撃1段階ダウン():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    assert battle.actives[0].boosts["atk"] == -1


def test_いかく_設置技のダメージで瀕死になった場合は発動しない():
    """設置技の効果は特性より前に発動するため、場に出た直後に設置技ダメージで
    瀕死になった場合は入場特性（いかく）が発動しない。
    （一次情報: .internal/spec/abilities/エレキメイカー.md
    「場に出た直後に設置技のダメージでひんしになった場合、エレキメイカーは発動しない」
    と同様の仕様がいかく等の入場特性全般に適用される）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン", ability_name="いかく")],
        team1=[Pokemon("ピカチュウ")],
        side0={"ステルスロック": 1},
    )
    entrant = battle.player_states[battle.players[0]].team[1]
    entrant.hp = 1
    t.run_switch(battle, 0, 1)
    assert entrant.fainted
    assert battle.actives[1].boosts["atk"] == 0


def test_いかく_設置技のダメージで瀕死にならなければ発動する():
    """設置技のダメージを受けても瀕死にならなければ、従来通り入場特性が発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン", ability_name="いかく")],
        team1=[Pokemon("ピカチュウ")],
        side0={"ステルスロック": 1},
    )
    entrant = battle.player_states[battle.players[0]].team[1]
    t.run_switch(battle, 0, 1)
    assert not entrant.fainted
    assert battle.actives[1].boosts["atk"] == -1


def test_いかりのこうら_HP半分超から半分以下でACSアップBDダウン():
    """いかりのこうら: HPが半分を下回ったとき A/C/S↑1、B/D↓1。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのこうら")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 2
    t.fix_damage(battle, 3)  # 半分以上削る
    t.run_move(battle, 1)

    assert defender.hp <= defender.max_hp // 2
    assert defender.boosts["atk"] == 1
    assert defender.boosts["spa"] == 1
    assert defender.boosts["spe"] == 1
    assert defender.boosts["def"] == -1
    assert defender.boosts["spd"] == -1


def test_いかりのこうら_さまようたましいで多段技のヒット途中に特性を獲得しても正しく判定する():
    """いかりのこうら: さまようたましいでコンタクト技のヒット途中に本特性を獲得した場合、
    1発目の時点ではまだ特性を持っておらずハンドラが呼ばれないため、獲得後最初のヒット
    （このケースでは2発目）を受ける前のHPを基準に判定する
    （かつてはこのケースで基準HPが未設定のまま最終ヒットで参照されAttributeErrorになっていた）。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="さまようたましい")],
        team1=[Pokemon("ピカチュウ", ability_name="いかりのこうら", move_names=["トリプルアクセル"])],
        accuracy=100,
        damage_roll="max",
    )
    t.fix_random(battle, 0.99)  # 急所を回避する
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]
    power_sequence = move.data.multi_hit["power_sequence"]

    expected_damages = []
    for power in power_sequence:
        move.base_power = power
        expected_damages.append(battle.roll_damage(attacker, defender, move, critical=False))

    # 2発目終了時点（＝特性獲得後最初のヒット直前）ではまだ半分を上回るように調整する。
    half = defender.max_hp // 2
    start_hp = half + expected_damages[0] + expected_damages[1] // 2 + 1
    defender.hp = start_hp
    assert (start_hp - expected_damages[0]) * 2 > defender.max_hp  # 2発目直前では下回らない
    assert (start_hp - sum(expected_damages)) * 2 <= defender.max_hp  # 3発目で下回る

    t.run_move(battle, 1)

    assert defender.alive
    assert defender.ability.base_name == "いかりのこうら"
    assert attacker.ability.base_name == "さまようたましい"
    assert defender.hp == start_hp - sum(expected_damages)
    assert defender.boosts["atk"] == 1
    assert defender.boosts["spa"] == 1
    assert defender.boosts["spe"] == 1
    assert defender.boosts["def"] == -1
    assert defender.boosts["spd"] == -1


def test_いかりのこうら_さまようたましいで特性獲得時点で既に半分以下なら発動しない():
    """いかりのこうら: さまようたましいでコンタクト技のヒット途中に本特性を獲得した時点
    （このケースでは2発目直前）で既にHPが半分以下の場合は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="さまようたましい")],
        team1=[Pokemon("ピカチュウ", ability_name="いかりのこうら", move_names=["トリプルアクセル"])],
        accuracy=100,
        damage_roll="max",
    )
    t.fix_random(battle, 0.99)  # 急所を回避する
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]
    power_sequence = move.data.multi_hit["power_sequence"]

    expected_damages = []
    for power in power_sequence:
        move.base_power = power
        expected_damages.append(battle.roll_damage(attacker, defender, move, critical=False))

    half = defender.max_hp // 2
    start_hp = half + expected_damages[0]
    defender.hp = start_hp
    assert (start_hp - expected_damages[0]) * 2 <= defender.max_hp  # 2発目直前で既に半分以下

    t.run_move(battle, 1)

    assert defender.alive
    assert defender.ability.base_name == "いかりのこうら"
    assert defender.boosts["atk"] == 0
    assert defender.boosts["def"] == 0


def test_いかりのこうら_ひんし時は発動しない():
    """いかりのこうら: 瀕死になった場合は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのこうら"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2 + 1
    t.fix_damage(battle, defender.max_hp)
    t.run_move(battle, 1)

    assert defender.fainted
    assert defender.boosts["atk"] == 0


def test_いかりのこうら_被弾前HPが半分以下なら発動しない():
    """いかりのこうら: すでにHP半分以下のときは発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのこうら")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    defender.hp = defender.max_hp // 2
    t.fix_damage(battle, 1)
    t.run_move(battle, 1)

    assert defender.boosts["atk"] == 0


def test_いかりのこうら_連続攻撃技は最終ヒット後にまとめて判定する():
    """いかりのこうら: 連続攻撃技の途中でHPが半分を下回っても、全ヒットが終わるまで発動しない。

    途中のヒットで発動してしまうと ぼうぎょ が下がり、後続ヒットのダメージが
    本来より大きくなってしまう。1発目を受ける前のHPを基準にまとめて判定されることを、
    ランク補正前提で計算したダメージ合計と実際の被ダメージ量を比較して確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのこうら")],
        team1=[Pokemon("ピカチュウ", move_names=["トリプルアクセル"])],
        accuracy=100,
        damage_roll="max",
    )
    t.fix_random(battle, 0.99)  # 急所を回避する
    defender = battle.actives[0]
    attacker = battle.actives[1]
    move = attacker.moves[0]
    power_sequence = move.data.multi_hit["power_sequence"]

    # ランク変化前提のダメージを事前計算する（正しい実装では3発目もこの値になるはず）。
    expected_damages = []
    for power in power_sequence:
        move.base_power = power
        expected_damages.append(battle.roll_damage(attacker, defender, move, critical=False))

    # 2発目終了時点でHPが半分を下回るように調整する。
    half = defender.max_hp // 2
    start_hp = half + expected_damages[0] + expected_damages[1] // 2 + 1
    defender.hp = start_hp
    assert (start_hp - expected_damages[0]) * 2 > defender.max_hp  # 1発目では下回らない
    assert (start_hp - expected_damages[0] - expected_damages[1]) * 2 <= defender.max_hp  # 2発目で下回る

    t.run_move(battle, 1)

    # 3発目のダメージがぼうぎょダウン前提で計算されていれば、実際の被ダメージ合計が
    # ランク変化前提の合計より大きくなってしまう。ここが一致することで、
    # 全ヒット終了後にまとめて判定されていることを確認する。
    assert defender.alive
    assert defender.hp == start_hp - sum(expected_damages)
    assert defender.boosts["atk"] == 1
    assert defender.boosts["def"] == -1


def test_いかりのつぼ_A最大のとき急所被弾でも変化なし():
    """いかりのつぼ: こうげきランクがすでに最大のときは急所被弾しても発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのつぼ")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックフラワー"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    defender.boosts["atk"] = 6
    t.run_move(battle, 1)

    assert battle.move_executor.critical is True
    assert defender.boosts["atk"] == 6


def test_いかりのつぼ_急所でない被弾は発動しない():
    """いかりのつぼ: 急所でない被弾ではこうげきランクが変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのつぼ")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    battle.random.random = lambda: 1.0  # 急所が発生しない乱数
    defender = battle.actives[0]
    t.run_move(battle, 1)
    assert defender.boosts["atk"] == 0


def test_いかりのつぼ_急所被弾でこうげき最大():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのつぼ")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックフラワー"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.run_move(battle, 1)

    assert battle.move_executor.critical is True
    assert defender.boosts["atk"] == 6


def test_いかりのつぼ_被弾して瀕死になった場合はこうげきが上がらない():
    """いかりのつぼ: 急所被弾で瀕死になった場合、自分自身のランク変化は発動しない
    （へんしょく・ぎゃくじょう等の既存特性と同じ規約）。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いかりのつぼ")],
        team1=[Pokemon("ピカチュウ", move_names=["トリックフラワー"])],
        accuracy=100,
    )
    defender = battle.actives[0]
    t.fix_damage(battle, defender.max_hp)
    t.run_move(battle, 1)

    assert battle.move_executor.critical is True
    assert defender.fainted is True
    assert defender.boosts["atk"] == 0


def test_いしあたま_はかいこうせんのリチャージは防げない():
    """いしあたま: はかいこうせんは反動ダメージを伴わない技のため、
    HPは減らないがリチャージによる行動不能は通常通り発生する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="いしあたま", move_names=["はかいこうせん"])],
        team1=[Pokemon("ヤドン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp
    assert attacker.has_volatile("リチャージ")


def test_いしあたま_わるあがきの反動ダメージは防げない():
    """いしあたま: わるあがきの反動は通常の反動技と異なる仕様のため無効化されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ゴンベ", ability_name="いしあたま", move_names=["わるあがき"])],
        team1=[Pokemon("ヤドン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    hp_before = attacker.hp
    t.run_move(battle, 0)
    assert attacker.hp < hp_before


def test_いしあたま_反動技を使っても反動ダメージを受けない():
    battle = t.start_battle(
        team0=[Pokemon("ゴンベ", ability_name="いしあたま", move_names=["すてみタックル"])],
        team1=[Pokemon("ヤドン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_いたずらごころ_あくタイプ相手には変化技が無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いたずらごころ", move_names=["でんじは"])],
        team1=[Pokemon("ヘルガー")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    # あくタイプ相手には変化技が無効化されるため、まひが付与されない
    assert not defender.ailment.is_active
    assert battle.move_executor.move_applied is False


def test_いたずらごころ_変化技の優先度が1上がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いたずらごころ", move_names=["でんじは"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]

    assert attacker.moves[0].priority == 0
    assert battle.speed_calculator.calc_move_priority(attacker, attacker.moves[0]) == 1


def test_いたずらごころ_自己対象の変化技はあくタイプ相手でも成功する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いたずらごころ", move_names=["かえんのまもり"])],
        team1=[Pokemon("ヘルガー")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    # 自己対象の変化技はあくタイプ相手でも成功するため、かえんのまもり状態になる
    assert battle.move_executor.move_applied is True
    assert attacker.has_volatile("かえんのまもり")


def test_いたずらごころ_自陣営対象の変化技はあくタイプ相手でも成功する():
    """場（自陣営）を対象とする変化技は、相手を対象としないためあくタイプに無効化されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いたずらごころ", move_names=["おいかぜ"])],
        team1=[Pokemon("ヘルガー")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    side = battle.get_side(battle.actives[0])
    assert battle.move_executor.move_applied is True
    assert side.fields["おいかぜ"].is_active


def test_いろめがね_いまひとつのダメージが2倍():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いろめがね", move_names=["むしのていこう"])],
        team1=[Pokemon("ピジョン")],
    )
    t.run_move(battle, 0)
    # むし技はひこうタイプに半減（いまひとつ）のため、いろめがねが発動しダメージ補正が2倍になる
    assert battle.damage_calculator.def_type_modifier == 2048
    assert 8192 == battle.damage_calculator.damage_modifier


def test_いろめがね_効果抜群のときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いろめがね", move_names=["むしのていこう"])],
        team1=[Pokemon("ケーシィ")],
    )
    t.run_move(battle, 0)
    # むし技はエスパータイプに抜群のため、いろめがねは発動しない
    assert battle.damage_calculator.def_type_modifier == 8192
    assert 4096 == battle.damage_calculator.damage_modifier


def test_いろめがね_等倍のときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いろめがね", move_names=["むしのていこう"])],
        team1=[Pokemon("ライチュウ")],
    )
    t.run_move(battle, 0)
    # むし技はでんきタイプに等倍のため、いろめがねは発動しない
    assert battle.damage_calculator.def_type_modifier == 4096
    assert 4096 == battle.damage_calculator.damage_modifier


def test_いろめがね_複合タイプで最終的に等倍になるときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いろめがね", move_names=["むしのていこう"])],
        team1=[Pokemon("フシギダネ")],
    )
    t.run_move(battle, 0)
    # むし技はくさタイプに抜群・どくタイプに半減で、最終的な相性は等倍になるため発動しない
    assert battle.damage_calculator.def_type_modifier == 4096
    assert 4096 == battle.damage_calculator.damage_modifier


def test_うなぎのぼり_かたやぶりでじめん技が通る():
    """うなぎのぼり: かたやぶり持ちの相手のじめん技は無効化できない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うなぎのぼり")],
        team1=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["じしん"])],
    )
    defender, _ = battle.actives
    t.run_move(battle, 1)
    assert defender.hp < defender.max_hp


def test_うなぎのぼり_じめん技が通らない():
    """うなぎのぼり: じめんタイプの攻撃技を無効化する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うなぎのぼり")],
        team1=[Pokemon("ピカチュウ", move_names=["じしん"])],
    )
    defender, _ = battle.actives
    t.run_move(battle, 1)
    assert defender.hp == defender.max_hp


@pytest.mark.parametrize(
    "name, stat",
    [
        ("ウインディ", "atk"),
        ("ピカチュウ", "spe"),
    ]
)
def test_うなぎのぼり_倒すと最高実数値の能力が上がる(name: str, stat: Stat):
    """うなぎのぼり: 攻撃技で倒すと最高実数値の能力が1段階上がる。"""
    battle = t.start_battle(
        team0=[Pokemon(name, ability_name="うなぎのぼり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.run_move(battle, 0)

    assert attacker.boosts[stat] == 1


def test_うなぎのぼり_浮いている():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うなぎのぼり")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.query.is_floating(battle.actives[0])


def test_うのミサイル_ウッウ以外では発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うのミサイル", move_names=["なみのり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.name == "ピカチュウ"


def test_うのミサイル_うのみのすがたで攻撃を受けると通常に戻りぼうぎょが下がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ウッウ(うのみ)", ability_name="うのミサイル")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.name == "ウッウ"
    assert attacker.boosts["def"] == -1
    assert attacker.hp == attacker.max_hp - attacker.max_hp // 4


def test_うのミサイル_ダイビング2ターン目がまもるで無効化されてもフォルムチェンジは維持される():
    """うのミサイル: ダイビング2ターン目の攻撃がまもるで無効化されてもフォルムチェンジは維持される。"""
    battle = t.start_battle(
        team0=[Pokemon("ウッウ", ability_name="うのミサイル", move_names=["ダイビング"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert mon.name == "ウッウ(うのみ)"

    battle.volatile_manager.apply(defender, "まもる", count=1)
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp == hp_before
    assert mon.name == "ウッウ(うのみ)"


def test_うのミサイル_ダイビングの溜めターンで成功するとフォルムチェンジする():
    """うのミサイル: ダイビングは1ターン目の溜める行動が成功した時点でフォルムチェンジする。"""
    battle = t.start_battle(
        team0=[Pokemon("ウッウ", ability_name="うのミサイル", move_names=["ダイビング"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.name == "ウッウ(うのみ)"


def test_うのミサイル_なみのりが命中するとHP半分以下でまるのみのすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("ウッウ", ability_name="うのミサイル", move_names=["なみのり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    t.run_move(battle, 0)
    assert mon.name == "ウッウ(まるのみ)"


def test_うのミサイル_なみのりが命中するとHP半分超でうのみのすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("ウッウ", ability_name="うのミサイル", move_names=["なみのり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.name == "ウッウ(うのみ)"


def test_うのミサイル_まるのみのすがたで攻撃を受けると通常に戻りまひになる():
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ウッウ(まるのみ)", ability_name="うのミサイル")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.name == "ウッウ"
    assert attacker.has_ailment("まひ")


def test_うのミサイル_みがわりで防いだ場合は吐き出しが発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ウッウ(うのみ)", ability_name="うのミサイル")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    before_attacker_hp = attacker.hp
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)
    assert defender.name == "ウッウ(うのみ)"
    assert attacker.hp == before_attacker_hp


def test_うのミサイル_交代するとフォルムが通常のすがたに戻る():
    battle = t.start_battle(
        team0=[Pokemon("ウッウ(うのみ)", ability_name="うのミサイル"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "ウッウ(うのみ)"
    t.run_switch(battle, 0, 1)
    assert mon.name == "ウッウ"


def test_うのミサイル_瀕死交代でもフォルムが通常のすがたに戻る():
    """瀕死になったうのミサイル持ちが交代する際も、通常の交代と同様に通常の
    すがたへ戻す（Handler.allow_fainted_subjectの回帰テスト。fuzz_log seed=1183参照）。"""
    battle = t.start_battle(
        team0=[Pokemon("ウッウ(うのみ)", ability_name="うのミサイル"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.modify_hp(mon, -mon.hp)
    assert mon.fainted
    t.run_switch(battle, 0, 1)
    assert mon.name == "ウッウ"


def test_うのミサイル_致命打でも発動する():
    """うのミサイル: 攻撃を受けてウッウがひんしになったときも獲物を吐き出して
    ダメージと効果を与える（fuzz_log横断監査。.internal/spec/abilities/うのミサイル.md）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ウッウ(うのみ)", ability_name="うのミサイル")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.fix_damage(battle, 9999)

    t.run_move(battle, 0)

    assert defender.fainted
    assert defender.name == "ウッウ"
    assert attacker.boosts["def"] == -1
    assert attacker.hp == attacker.max_hp - attacker.max_hp // 4


def test_うるおいボイス_ノーマル以外のタイプの音技もみずタイプに変換する():
    """サイコノイズ（エスパータイプの音技）もみずタイプに変換される。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", ability_name="うるおいボイス", move_names=["サイコノイズ"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "みず"


def test_うるおいボイス_ノーマル音技をみずタイプに変換する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うるおいボイス", move_names=["ハイパーボイス"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "みず"


def test_うるおいボイス_非音技には適用されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うるおいボイス", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "ノーマル"


def test_うるおいボイス_音技の変化技もみずタイプに変換される():
    """ほろびのうた（音技の変化技）もみずタイプに変換され、ちょすい等で防げるようになる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うるおいボイス", move_names=["ほろびのうた"])],
        team1=[Pokemon("カビゴン", ability_name="ちょすい")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_type == "みず"
    assert not battle.actives[1].has_volatile("ほろびのうた")


def test_うるおいボディ_あめが止むターンでは発動しない():
    """うるおいボディ: あめが止むターン（天候カウントが0になるターン）では発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うるおいボディ")],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 1),
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど")
    t.end_turn(battle)
    assert battle.weather.name == ""
    assert mon.ailment.is_active


@pytest.mark.parametrize("weather_name, expected_recovered", [
    ("あめ", True),
    ("おおあめ", True),
    ("はれ", False),
])
def test_うるおいボディ_天候別に状態異常を回復する(weather_name: WeatherName, expected_recovered: bool):
    """うるおいボディ: あめ・おおあめ中は状態異常を回復し、はれ中は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うるおいボディ")],
        team1=[Pokemon("カビゴン")],
        weather=(weather_name, 5),
    )
    mon = battle.actives[0]
    battle.ailment_manager.apply(mon, "やけど")
    t.end_turn(battle)
    assert mon.ailment.is_active == (not expected_recovered)


def test_うるおいボディ_状態異常がなければ何も起きない():
    """うるおいボディ: 状態異常がないときは何も起きない（エラーにならない）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="うるおいボディ")],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 5),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert not mon.ailment.is_active


def test_エアロック_すなあらしのターン終了ダメージが無効化される():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ", ability_name="エアロック")],
        weather=("すなあらし", 5),
    )
    mon = battle.actives[0]
    t.end_turn(battle)
    assert mon.hp == mon.max_hp


@pytest.mark.parametrize(
    "weather_name",
    weathers
)
def test_エアロック_天候と強天候を無効化する(weather_name: WeatherName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="エアロック")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather_name, 5),
    )
    assert battle.weather.name == ""


@pytest.mark.parametrize(
    "initial_terrain",
    [
        "グラスフィールド",
        "サイコフィールド",
        "ミストフィールド",
    ],
)
def test_エレキメイカー_別フィールドを上書きする(initial_terrain: TerrainName):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="エレキメイカー")],
        team1=[Pokemon("ピカチュウ")],
        terrain=(initial_terrain, 5),
    )
    t.run_switch(battle, 0, 1)
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5
    assert battle.actives[0].ability.revealed


def test_エレキメイカー_特性再有効化時にも発動する():
    """エレキメイカー: かがくへんかガス解除後に特性が再有効化されると再発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="エレキメイカー")],
        team1=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
    )
    mon = battle.actives[0]
    # かがくへんかガスにより特性が無効化されているのでフィールドは展開されていない
    assert battle.terrain.name == ""
    # かがくへんかガスの無効化を解除すると特性が再発動してエレキフィールドが展開される
    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5


def test_エレキメイカー_設置技のダメージで瀕死になった場合は発動しない():
    """エレキメイカー: 場に出た直後に設置技のダメージでひんしになった場合は発動しない
    （一次情報: .internal/spec/abilities/エレキメイカー.md）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ピカチュウ", ability_name="エレキメイカー")],
        team1=[Pokemon("ピカチュウ")],
        side0={"ステルスロック": 1},
    )
    entrant = battle.player_states[battle.players[0]].team[1]
    entrant.hp = 1
    t.run_switch(battle, 0, 1)
    assert entrant.fainted
    assert battle.terrain.name == ""


def test_えんかく_直接攻撃でさめはだが発動しない():
    """えんかく所持者が直接攻撃を使っても、相手のさめはだが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="えんかく", move_names=["たいあたり"])],
        team1=[Pokemon("ウインディ", ability_name="さめはだ")],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_えんかく_直接攻撃でもふもふのダメージ半減が発動しない():
    """えんかく所持者が接触技を使っても、相手のもふもふによるダメージ半減が発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="えんかく", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
    )
    t.run_move(battle, 0)
    assert 4096 == battle.damage_calculator.damage_modifier


def test_えんかく_直接攻撃でわるいてぐせが発動しない():
    """えんかく所持者が直接攻撃を使っても、相手のわるいてぐせが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="えんかく", item_name="たべのこし",
                       move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="わるいてぐせ")],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert attacker.has_item()


def test_おうごんのからだ_おちゃかいは自分への効果のみ防ぐ():
    """おちゃかい: おうごんのからだ所持者は自分のきのみの強制消費のみ防ぎ、使用者のきのみは通常通り消費される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おちゃかい"], item_name="オボンのみ")],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ", item_name="オボンのみ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not attacker.item.is_berry()
    assert defender.item.is_berry()


def test_おうごんのからだ_かたやぶりで無効():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["なきごえ"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied is True


def test_おうごんのからだ_ほろびのうたは自分への付与のみ防ぐ():
    """ほろびのうた: おうごんのからだ所持者は自分への状態付与のみ防ぎ、使用者には通常通り付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほろびのうた"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied
    assert attacker.has_volatile("ほろびのうた")
    assert not defender.has_volatile("ほろびのうた")


def test_おうごんのからだ_場が対象の技は無効化しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["にほんばれ"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied is True


def test_おうごんのからだ_攻撃技は無効化しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied
    assert not battle.actives[1].ability.revealed


def test_おうごんのからだ_相手の変化技を無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert not battle.move_executor.move_applied
    assert battle.actives[1].ability.revealed is True


def test_おうごんのからだ_自分が使うおちゃかいは自分の特性で防がれない():
    """おうごんのからだ所持ポケモン自身がおちゃかいを使った場合、自身のきのみは消費される。"""
    battle = t.start_battle(
        team0=[Pokemon("サーフゴー", ability_name="おうごんのからだ", move_names=["おちゃかい"],
                       item_name="オボンのみ")],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.item.is_berry()


def test_おうごんのからだ_自分対象の変化技は無効化しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つるぎのまい"])],
        team1=[Pokemon("サーフゴー", ability_name="おうごんのからだ")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.move_applied


def test_おどりこ_まもるで防がれた場合は発動しない():
    """おどりこ: 相手の踊り技がまもるで防がれた場合は発動しない"""
    dancer = Pokemon("コラッタ", move_names=["アクアステップ"], nature="ようき")
    dancer.set_evs({"spe": 32})
    battle = t.start_battle(
        team0=[dancer],
        team1=[Pokemon("オドリドリ(めらめら)", ability_name="おどりこ", move_names=["まもる"])],
    )
    player0, player1 = battle.players
    odoriko = battle.actives[1]
    hp_before = odoriko.hp
    battle.step({player0: Command.get_move_command(0), player1: Command.get_move_command(0)})
    assert odoriko.hp == hp_before


def test_おどりこ_命中しなかった場合は発動しない():
    """おどりこ: 相手の踊り技が命中しなかった場合は発動しない"""
    dancer = Pokemon("コラッタ", move_names=["アクアステップ"], nature="ようき")
    dancer.set_evs({"spe": 32})
    battle = t.start_battle(
        team0=[dancer],
        team1=[Pokemon("オドリドリ(めらめら)", ability_name="おどりこ", move_names=["はねる"])],
        accuracy=0,
    )
    player0, player1 = battle.players
    odoriko = battle.actives[1]
    hp_before = odoriko.hp
    battle.step({player0: Command.get_move_command(0), player1: Command.get_move_command(0)})
    assert odoriko.hp == hp_before


def test_おどりこ_踊り技成功時に同じ技をコピーする():
    """おどりこ: 自分以外が踊り技(dance フラグ)を成功させた直後、同じ技を自分も使う"""
    dancer = Pokemon("コラッタ", move_names=["つるぎのまい"], nature="ようき")
    dancer.set_evs({"spe": 32})
    battle = t.start_battle(
        team0=[dancer],
        team1=[Pokemon("オドリドリ(めらめら)", ability_name="おどりこ", move_names=["はねる"])],
    )
    player0, player1 = battle.players
    odoriko = battle.actives[1]
    battle.step({player0: Command.get_move_command(0), player1: Command.get_move_command(0)})
    assert odoriko.boosts["atk"] == 2


def test_おみとおし_アイテムありの相手のアイテムが公開される():
    """おみとおし: 場に出たとき相手のアイテムが公開される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おみとおし")],
        team1=[Pokemon("ピカチュウ", item_name="たべのこし")],
    )
    foe = battle.actives[1]
    assert foe.item.revealed
    assert battle.actives[0].ability.revealed


def test_おみとおし_アイテムなしの相手には発動しない():
    """おみとおし: 相手がアイテムを持っていなければ発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おみとおし")],
        team1=[Pokemon("ピカチュウ")],
    )
    foe = battle.actives[1]
    assert not foe.item.revealed


def test_おみとおし_ぶきようでアイテム無効化中でも公開される():
    """おみとおし: ぶきようでアイテム効果が無効化されていても、持っている事実は公開される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おみとおし")],
        team1=[Pokemon("ピカチュウ", ability_name="ぶきよう", item_name="たべのこし")],
    )
    foe = battle.actives[1]
    assert foe.item.revealed


def test_おもかげやどし_オーガポン以外は発動しない():
    """おもかげやどし: オーガポン以外のポケモンには発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おもかげやどし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    # どのランクも変化しない
    for stat in ("atk", "def", "spa", "spd", "spe"):
        assert mon.boosts[stat] == 0


def test_おもかげやどし_テラスタル時に能力が上昇する():
    """おもかげやどし: テラスタル時にフォルムに対応する能力が1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(みどり)", ability_name="おもかげやどし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    # 登場時の発動状態をリセットして、テラスタル起因の発動のみを検証する
    # （実機では実際にテラスタルするまでこの特性を持たないため、登場時点では未発動の状態を再現する）
    mon.boosts["spe"] = 0
    mon.ability.activated_since_switch_in = False
    # テラスタルコマンドを予約して step でテラスタルフェーズを実行する
    t.reserve_command(battle, Command.TERASTAL_0, Command.MOVE_0)
    battle.step()
    assert mon.is_terastallized
    assert mon.boosts["spe"] == 1


@pytest.mark.parametrize(
    "form_name, expected_stat",
    [
        ("オーガポン(みどり)", "spe"),
        ("オーガポン(いど)", "spd"),
        ("オーガポン(かまど)", "atk"),
        ("オーガポン(いしずえ)", "def"),
    ],
)
def test_おもかげやどし_フォルムに対応した能力が1段上昇する(form_name: str, expected_stat: Stat):
    """おもかげやどし: フォルムに応じた能力が1段階上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon(form_name, ability_name="おもかげやどし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.boosts[expected_stat] == 1


def test_おもかげやどし_交代して再登場すると再発動する():
    """おもかげやどし: 交代して再び場に出たときに再度能力が上昇する。"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(みどり)", ability_name="おもかげやどし"), Pokemon("コイル")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.boosts["spe"] == 1
    # 一度引っ込める（交代でランクはリセットされる）
    t.run_switch(battle, 0, 1)
    assert mon.boosts["spe"] == 0  # 交代後はリセット
    # 再登場するとおもかげやどしが再発動して+1
    t.run_switch(battle, 0, 0)
    assert mon.boosts["spe"] == 1


def test_おもかげやどし_場に出るたびに1回しか発動しない():
    """おもかげやどし: 場に出てから既に発動している場合、かがくへんかガスの発動・解除が起きても再発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(みどり)", ability_name="おもかげやどし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    # 登場時に発動済み
    assert mon.boosts["spe"] == 1
    # かがくへんかガスの発動・解除が起きても再発動しない
    battle.add_ability_disabled_reason(mon, "かがくへんかガス")
    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    assert mon.boosts["spe"] == 1


def test_おもかげやどし_特性再有効化時にも発動する():
    """おもかげやどし: かがくへんかガス解除後に特性が再有効化されると再発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("オーガポン(みどり)", ability_name="おもかげやどし")],
        team1=[Pokemon("ピカチュウ", ability_name="かがくへんかガス")],
    )
    mon = battle.actives[0]
    # かがくへんかガスにより特性が無効化されているので S は上昇していない
    assert mon.boosts["spe"] == 0
    # かがくへんかガスの無効化を解除すると特性が再発動してS+1
    battle.remove_ability_disabled_reason(mon, "かがくへんかガス")
    assert mon.boosts["spe"] == 1


def test_おやこあい_1ヒット目でみがわりが破壊された場合2ヒット目は本体に通常通り当たる():
    """おやこあい: 1ヒット目でみがわりが消滅した場合、2ヒット目はみがわりを介さず
    本体に直接ダメージが入る（連続攻撃技の一般仕様。.internal/spec/moves/連続技.md
    5.1「みがわり破壊後は残りヒットが本体に適用される」）。上記の回帰バグ修正
    （value>0チェックの追加）が、この既存の正常系挙動を壊していないことを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おやこあい", move_names=["アクアステップ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "みがわり", hp=40)
    t.fix_damage(battle, 40)
    before_hp = defender.hp
    t.run_move(battle, 0)
    # 1ヒット目（40ダメージ）でみがわりがちょうど消滅する
    assert not defender.has_volatile("みがわり")
    # 2ヒット目（1/4減衰後 40//4=10）は本体に通常通り適用される
    assert defender.hp == before_hp - 10
    assert defender.hits_taken == 1


def test_おやこあい_2ヒット目は端数切り捨てでも最低1ダメージ保証():
    """おやこあい: 1ヒット目のダメージが小さく1/4が0になる場合でも、2ヒット目は最低1ダメージ入る。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おやこあい", move_names=["アクアステップ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    # 1ヒット目のダメージを3に固定 → 3//4=0になってしまうが、最低1ダメージが保証される
    t.fix_damage(battle, 3)
    t.run_move(battle, 0)
    attacker, defender = battle.actives
    assert defender.hits_taken == 2
    assert defender.hp == defender.max_hp - 3 - 1


def test_おやこあい_がむしゃらには適用しない():
    """おやこあい: がむしゃらはHP変動の有無に関わらずいかなる状況でも連続攻撃にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おやこあい", move_names=["がむしゃら"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.hp = 30
    defender.hp = 100
    t.run_move(battle, 0)
    assert defender.hits_taken == 1
    assert defender.hp == 100 - (100 - 30)


def test_おやこあい_ころがるには適用しない():
    """おやこあい: ころがるは数ターン継続する強制行動技のため、連続攻撃にならない。"""
    battle = t.start_battle(
        team0=[Pokemon("イシツブテ", ability_name="おやこあい", move_names=["ころがる"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hits_taken == 1
    assert attacker.volatiles["ころがる"].count == 1


def test_おやこあい_みがわりで完全にブロックされたダメージは本体に漏れない():
    """おやこあい: みがわりが両方のヒットを吸収しきる場合、本体HPは一切減少しない。

    みがわり_block_damage（ON_MODIFY_MOVE_DAMAGE priority=20）はおやこあい_reduce_second_damage
    （同priority=100）より先に実行され、2ヒット目もvalue=0を返す。この0に対して
    「最低1ダメージ保証」（max(1, value//4)）を無条件適用すると、みがわりで完全に
    防がれたはずのダメージが本体に漏れてしまう回帰バグを防ぐテスト（fuzz_log seed=127）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おやこあい", move_names=["アクアステップ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.fix_damage(battle, 40)
    t.run_move(battle, 0)
    # 本体HPは1ヒット目・2ヒット目ともみがわりに完全に肩代わりされ、一切減少しない
    assert defender.hp == defender.max_hp
    assert defender.hits_taken == 0
    # みがわりのHPからは両ヒット分（40+40）が正しく差し引かれる
    assert defender.volatiles["みがわり"].hp == 999 - 40 - 40


def test_おやこあい_単発攻撃が2ヒットする():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おやこあい", move_names=["アクアステップ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    # ダメージ計算結果を固定
    t.fix_damage(battle, 40)
    t.run_move(battle, 0)
    attacker, defender = battle.actives
    assert defender.hits_taken == 2
    assert defender.hp == defender.max_hp - 40 - 10
    assert attacker.boosts["spe"] == 2


def test_おやこあい_既存連続技には適用しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="おやこあい", move_names=["すいりゅうれんだ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.hits_taken == 3


def test_オーラブレイク_登場時に特性開示():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="オーラブレイク")],
        team1=[Pokemon("ピカチュウ")],
    )
    assert battle.actives[0].ability.revealed is True


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("フェアリーオーラ", "ムーンフォース"),
        ("ダークオーラ", "あくのはどう"),
    ]
)
def test_オーラブレイク_相手の攻撃を0_75倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name="オーラブレイク")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.power_modifier


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("フェアリーオーラ", "ムーンフォース"),
        ("ダークオーラ", "あくのはどう"),
    ]
)
def test_オーラブレイク_自分の攻撃を0_75倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name)],
        team1=[Pokemon("ピカチュウ", ability_name="オーラブレイク", move_names=[move_name])],
    )
    t.run_move(battle, 1)
    assert 3072 == battle.damage_calculator.power_modifier


def test_かわりもの_場に出た瞬間に正面の相手に変身する():
    """かわりもの: 場に出た瞬間、正面の相手のタイプ・特性・技・実数値・ランク・性別・体重に変身する"""
    battle = t.start_battle(
        team0=[Pokemon("メタモン", ability_name="かわりもの", move_names=["はねる"])],
        team1=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["でんこうせっか"])],
    )
    mon, target = battle.actives
    assert mon.types == target.types
    assert mon.ability.name == "せいでんき"
    assert [m.name for m in mon.moves] == [m.name for m in target.moves]
    assert mon.has_volatile("へんしん")


def test_かわりもの_相手がみがわり状態なら発動しない():
    """かわりもの: 対象がみがわり状態の場合は発動しない"""
    battle = t.start_battle(
        team0=[
            Pokemon("メタモン", ability_name="かわりもの", move_names=["はねる"]),
            Pokemon("フシギダネ", move_names=["はねる"]),
        ],
        team1=[Pokemon("ピカチュウ", move_names=["みがわり"])],
    )
    # メタモンを一旦退避させ、相手にみがわりを張らせてから出し直す
    t.run_switch(battle, 0, 1)
    t.run_move(battle, 1, 0)  # みがわり
    mon = t.run_switch(battle, 0, 0)
    assert mon.ability.name == "かわりもの"


def test_かわりもの_スキルスワップで得ても変身しない():
    """かわりもの: スキルスワップ/さまようたましいでこの特性を得ることはできるが、
    特性の効果（変身）は発動しない（.internal/spec/abilities/かわりもの.md）。
    かわりものはEvent.ON_ABILITY_ENABLEDに登録されていないため、
    battle.ability_manager.swap_ability()経由のON_ABILITY_ENABLED発火では
    かわりものが発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["スキルスワップ"])],
        team1=[Pokemon("フシギダネ", ability_name="しんりょく", move_names=["はねる"])],
    )
    mon, target = battle.actives
    battle.change_ability(target, "かわりもの")
    t.run_move(battle, 0, 0)  # スキルスワップ
    assert mon.ability.name == "かわりもの"
    assert target.ability.name == "せいでんき"
    assert mon.types == ["でんき"]  # 変身していない
    assert not mon.has_volatile("へんしん")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
