"""`Battle` の公開API（`active_side_fields` / Player 検証）に対する単体テスト。

- `Battle.active_side_fields()`: `battle.get_side(...).fields.values()` を
  `is_active` で絞り込む処理を外部コードに書かせず公開メソッド経由にするためのテスト。
- `Battle.__init__` の Player 検証: `Player` の hashability・同一性ベース `__eq__` が
  崩れているサブクラスを渡した場合に、分かりやすいメッセージ付きの `TypeError` が
  送出されることを確認する。
"""
from dataclasses import dataclass, field

import pytest

from jpoke import Battle, Player, Pokemon
from . import test_utils as t

def _make_team() -> list[Pokemon]:
    """Player検証テスト用の最小構成チームを作る。"""
    return [Pokemon("ピカチュウ", move_names=["たいあたり"])]

@dataclass
class _UnhashablePlayer(Player):
    """`eq=False` を指定していない `@dataclass` の Player サブクラス。

    dataclass はデフォルト（`eq=True`, `frozen=False`）だと `__hash__` を
    自動的に `None` にするため、意図せず unhashable になる典型例として使う。
    """
    username: str = ""
    team: list = field(default_factory=list)

@dataclass(eq=False)
class _HashableEqFalsePlayer(Player):
    """`@dataclass(eq=False)` を指定した Player サブクラス。

    `__eq__` が生成されないため `Player`（`object`）由来の同一性ベース比較・
    ハッシュがそのまま使われ、Battle に渡しても問題なく構築できることを確認する用途。
    """
    username: str = ""
    team: list = field(default_factory=list)

@dataclass(frozen=True)
class _ValueEqPlayer(Player):
    """値ベースの `__eq__`/`__hash__` を持つ Player サブクラス。

    `team` は `compare=False` にして比較対象から除外しているため、
    `username` が同じ2インスタンスは互いに `==` で等しくなる
    （＝同一性ベース比較が崩れている状態を再現する）。
    """
    username: str = ""
    team: list = field(default_factory=list, compare=False)


def test_Player_dataclass_eq_False指定サブクラスは正常にBattleを構築できる():
    """`@dataclass(eq=False)` の Player サブクラスは同一性ベースの比較・ハッシュを
    保持するため、Battle を問題なく構築できることを確認する"""
    player1 = _HashableEqFalsePlayer(username="P1", team=_make_team())
    player2 = _HashableEqFalsePlayer(username="P2", team=_make_team())

    battle = Battle(player1, player2)

    assert battle.players == (player1, player2)


def test_Player_eq指定なしのdataclassサブクラスを渡すとハッシュ不可を説明するTypeErrorが送出される():
    """`@dataclass` のみ（eq=False未指定）の Player サブクラスは __hash__ が
    None になるため、原因を説明する TypeError が送出されることを確認する"""
    player1 = _UnhashablePlayer(username="P1", team=_make_team())
    player2 = Player(username="P2")
    player2.team = _make_team()

    with pytest.raises(TypeError, match="ハッシュ可能"):
        Battle(player1, player2)


def test_Player_値ベースのeqを持つPlayer同士を渡すとTypeErrorが送出される():
    """互いに `==` で等しくなってしまう（値ベースの __eq__ を持つ）Player を
    渡すと、区別可能性の問題を説明する TypeError が送出されることを確認する"""
    player1 = _ValueEqPlayer(team=_make_team())
    player2 = _ValueEqPlayer(team=_make_team())
    assert player1 == player2  # 前提: 値ベースの eq により等値になる

    with pytest.raises(TypeError, match="区別可能"):
        Battle(player1, player2)


def test_active_side_fields_PlayerとPokemonのどちらを渡しても同じ結果になる():
    """source に Player を渡した場合と、その場に出ているPokemonを渡した場合で
    結果が一致することを確認する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
        side0={"リフレクター": 5},
    )

    by_player = battle.active_side_fields(battle.players[0])
    by_pokemon = battle.active_side_fields(battle.actives[0])

    assert by_player == by_pokemon
    assert {f.name for f in by_player} == {"リフレクター"}


def test_active_side_fields_何も張っていない場合は空リストを返す():
    """サイドフィールドを何も設置していない状態では空リストが返ることを確認する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )

    assert battle.active_side_fields(battle.players[0]) == []


def test_active_side_fields_壁や設置技を張った状態でアクティブなものだけ返す():
    """リフレクターとまきびしを張った状態で、その2つだけが返ることを確認する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
        side0={"リフレクター": 5, "まきびし": 1},
    )

    fields = battle.active_side_fields(battle.players[0])

    assert {f.name for f in fields} == {"リフレクター", "まきびし"}
    assert all(f.is_active for f in fields)


def test_active_side_fields_非アクティブなFieldが混ざらない():
    """設置していないサイドフィールドの Field（name が空文字列）が
    戻り値に含まれないことを確認する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
        side0={"リフレクター": 5},
    )

    fields = battle.active_side_fields(battle.players[0])

    # get_side().fields は全SideFieldName分のFieldを常時保持しているため、
    # 設置していないフィールドが1つでもあれば全件より返り値の方が少なくなる
    assert len(fields) < len(battle.get_side(battle.players[0]).fields)
    assert all(f.name != "" for f in fields)
