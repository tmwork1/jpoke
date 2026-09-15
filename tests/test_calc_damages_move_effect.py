"""ダメージ問い合わせにおける技前処理の回帰テスト。"""
from __future__ import annotations

import pytest

from jpoke import Pokemon
from jpoke.model import Move

from . import test_utils as t


def test_calc_damagesでMoveとハンドラ登録を復元する():
    """問い合わせで可変技を使ってもMove状態とイベント登録を残さない。"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", tera_type="でんき", move_names=["テラバースト"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    attacker.terastallize()
    move = attacker.moves[0]
    original_type, original_category = move.type, move.category
    battle.calc_damages(attacker, defender, move)
    assert (move.type, move.category) == (original_type, original_category)
    assert all(event not in battle.events.handlers for event in move.data.handlers)


def test_calc_lethalでスキン系とウェザーボールを反映する():
    """致死率計算も外部問い合わせ経由で技タイプ・固有威力補正を反映する。"""
    skin_battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="スカイスキン")],
        team1=[Pokemon("ゲンガー")],
    )
    weather_battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 5),
    )
    assert t.calc_lethal(
        skin_battle, player_idx=0, moves=Move("たいあたり"), max_attack=1
    )[0].max_damage > 0
    assert t.calc_lethal(
        weather_battle, player_idx=0, moves=Move("ウェザーボール"), max_attack=1
    )[0].max_damage > t.calc_lethal(
        t.start_battle(team0=[Pokemon("カビゴン")], team1=[Pokemon("カビゴン")]),
        player_idx=0,
        moves=Move("ウェザーボール"),
        max_attack=1,
    )[0].max_damage


def test_アクロバット_calc_damagesでもちもの有無を反映する():
    """アクロバットは道具なし時に威力が2倍になる。"""
    no_item = t.start_battle(
        team0=[Pokemon("チルタリス", move_names=["アクロバット"])],
        team1=[Pokemon("カビゴン")],
    )
    with_item = t.start_battle(
        team0=[Pokemon("チルタリス", item_name="たべのこし", move_names=["アクロバット"])],
        team1=[Pokemon("カビゴン")],
    )
    assert max(no_item.calc_damages(*no_item.actives, "アクロバット")) > max(
        with_item.calc_damages(*with_item.actives, "アクロバット")
    )


@pytest.mark.parametrize("weather_name", ["はれ", "あめ", "すなあらし", "ゆき"])
def test_ウェザーボール_calc_damagesで天候を反映する(weather_name: str):
    """天候時のウェザーボールは、天候なし時と異なるダメージになる。"""
    weather_battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ウェザーボール"])],
        team1=[Pokemon("カビゴン")],
        weather=(weather_name, 5),
    )
    plain_battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ウェザーボール"])],
        team1=[Pokemon("カビゴン")],
    )
    assert weather_battle.calc_damages(
        *weather_battle.actives, "ウェザーボール"
    ) != plain_battle.calc_damages(*plain_battle.actives, "ウェザーボール")


@pytest.mark.parametrize(
    ("ability_name", "move_name"),
    [("かたやぶり", "たいあたり"), ("", "シャドーレイ")],
)
def test_かたやぶり系_calc_damagesでマルチスケイルを無効化して復元する(
    ability_name: str,
    move_name: str,
):
    """問い合わせ中だけマルチスケイルを無効化し、終了後に有効へ戻す。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("カイリュー", ability_name="マルチスケイル")],
    )
    plain = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("カイリュー")],
    )
    assert battle.calc_damages(*battle.actives, move_name) == plain.calc_damages(
        *plain.actives, move_name
    )
    assert battle.actives[1].ability.enabled


@pytest.mark.parametrize(
    ("ability_name", "move_name"),
    [
        ("スカイスキン", "たいあたり"),
        ("フェアリースキン", "たいあたり"),
        ("フリーズスキン", "たいあたり"),
        ("ノーマルスキン", "ひのこ"),
    ],
)
def test_スキン系_calc_damagesで相性とタイプ一致を反映する(
    ability_name: str,
    move_name: str,
):
    """各スキン系の変換後タイプで、素のノーマル技とは異なる値を返す。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("フシギバナ")],
    )
    base = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("フシギバナ")],
    )
    assert battle.calc_damages(*battle.actives, move_name) != base.calc_damages(
        *base.actives, move_name
    )


@pytest.mark.parametrize(
    ("ability_name", "expected_effective"),
    [
        ("スカイスキン", True),
        ("フェアリースキン", True),
        ("フリーズスキン", True),
        # ノーマルスキンはノーマル技を変換しないため、ゴーストへは引き続き無効。
        ("ノーマルスキン", False),
    ],
)
def test_スキン系_ゴーストへのノーマル技を変換後タイプで計算する(
    ability_name: str,
    expected_effective: bool,
):
    """ゴーストへの問い合わせでも、各特性の実際の変換規則を適用する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=["たいあたり"])],
        team1=[Pokemon("ゲンガー")],
    )
    damages = battle.calc_damages(*battle.actives, "たいあたり")
    assert (max(damages) > 0) is expected_effective


def test_スケイルショット_技実行後にハンドラを残さない():
    """連続技の実行後、技データ由来のハンドラがEventManagerに残らない。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス", move_names=["スケイルショット"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    move = battle.actives[0].moves[0]
    t.fix_random(battle, 0.9)
    t.run_move(battle, 0)
    assert all(event not in battle.events.handlers for event in move.data.handlers)


def test_たいあたり_calc_damagesは前処理なしで同じ結果になる():
    """ハンドラを持たない技は早期リターンにより内部実装と完全に一致する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    assert battle.calc_damages(attacker, defender, "たいあたり") == (
        battle.damage_calculator.calc_damages(attacker, defender, Move("たいあたり"))
    )


def test_テラバースト_calc_damagesで実数値により分類を切り替える():
    """テラスタル中のテラバーストはA/Cの高い方を使って計算する。"""
    physical = t.start_battle(
        team0=[Pokemon("カイリキー", tera_type="でんき", move_names=["テラバースト"])],
        team1=[Pokemon("カビゴン")],
    )
    special = t.start_battle(
        team0=[Pokemon("フーディン", tera_type="でんき", move_names=["テラバースト"])],
        team1=[Pokemon("カビゴン")],
    )
    physical.actives[0].terastallize()
    special.actives[0].terastallize()
    physical.calc_damages(*physical.actives, "テラバースト")
    physical_attack = physical.damage_calculator.final_attack
    special.calc_damages(*special.actives, "テラバースト")
    special_attack = special.damage_calculator.final_attack
    assert physical_attack == physical.actives[0].stats["atk"]
    assert special_attack == special.actives[0].stats["spa"]


def test_メトロノームとたくわえる_calc_damagesで回数を変えない():
    """問い合わせはON_END_MOVEを発火せず、実使用時の副作用を起こさない。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="メトロノーム", move_names=["たいあたり", "はきだす"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 2},
    )
    attacker, defender = battle.actives
    item_count = attacker.item.count
    stockpile_count = attacker.volatiles["たくわえる"].count
    battle.calc_damages(attacker, defender, "たいあたり")
    battle.calc_damages(attacker, defender, "はきだす")
    assert attacker.item.count == item_count
    assert attacker.volatiles["たくわえる"].count == stockpile_count
