"""タイプ相性の公開関数 `get_type_effectiveness` のテスト。"""
from jpoke import Pokemon, TYPE_MODIFIER, get_type_effectiveness

from . import test_utils as t


def test_get_type_effectiveness_attack_typeがタイプなしなら常に1倍():
    assert get_type_effectiveness("", ["くさ", "どく"]) == 1.0


def test_get_type_effectiveness_battleのcalc_damagesと整合する():
    # でんき技はじめんタイプに無効。Battle経由の実ダメージ計算と
    # 静的な相性表参照の公開関数の結果が整合していることを確認する
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[Pokemon("ディグダ")],
    )
    attacker, defender = battle.actives
    damages = battle.calc_damages(attacker, defender, "でんきショック")
    assert all(d == 0 for d in damages)
    assert get_type_effectiveness("でんき", defender.data.types) == 0.0


def test_get_type_effectiveness_defense_typesが空なら1倍():
    assert get_type_effectiveness("ほのお", []) == 1.0


def test_get_type_effectiveness_defense_typesにタイプなしを含めても結果が変わらない():
    # みず技はくさタイプに0.5倍。タイプなし要素を混ぜても等倍扱いされるため結果は変わらない
    without_empty = get_type_effectiveness("みず", ["くさ"])
    with_empty = get_type_effectiveness("みず", ["くさ", ""])
    assert with_empty == without_empty == 0.5


def test_get_type_effectiveness_タイプなし技かつ相手がステラでもKeyErrorにならず1倍():
    # TYPE_MODIFIER[""] にはステラのキーが存在しないため、二段.get()フォールバックが
    # 効いていないと KeyError になる回帰テスト
    assert get_type_effectiveness("", ["ステラ"]) == 1.0


def test_get_type_effectiveness_トップレベルからimportできる():
    assert get_type_effectiveness("でんき", ["みず"]) == TYPE_MODIFIER["でんき"]["みず"]


def test_get_type_effectiveness_単タイプの半減は0_5倍():
    assert get_type_effectiveness("ほのお", ["みず"]) == 0.5


def test_get_type_effectiveness_単タイプの弱点は2倍():
    assert get_type_effectiveness("ほのお", ["くさ"]) == 2.0


def test_get_type_effectiveness_単タイプの無効は0倍():
    assert get_type_effectiveness("でんき", ["じめん"]) == 0.0


def test_get_type_effectiveness_複合タイプで片方が無効なら全体が0倍():
    # でんき技はじめんに無効、いわには等倍だが片方でも0倍なら全体が0倍
    assert get_type_effectiveness("でんき", ["いわ", "じめん"]) == 0.0


def test_get_type_effectiveness_複合タイプの0_25倍():
    # ほのお技はみず・いわどちらにも0.5倍のため合計0.25倍
    assert get_type_effectiveness("ほのお", ["みず", "いわ"]) == 0.25


def test_get_type_effectiveness_複合タイプの4倍():
    # いわ技はほのお・ひこうどちらにも2倍のため合計4倍
    assert get_type_effectiveness("いわ", ["ほのお", "ひこう"]) == 4.0
