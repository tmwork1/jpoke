"""観測（情報隠蔽）に関するテスト。

`Battle.build_observation()` / `observation_builder` は bot 対戦の公平性の要であり、
observer 視点のコピーに相手の非公開情報（未公開の技・アイテム・特性・テラスタイプ・
性格・努力値等）が含まれないことを保証する必要がある。
"""
import pytest

from jpoke.model import Pokemon

from . import test_utils as t

def _build_hidden_pokemon() -> Pokemon:
    """非公開情報を多く持つポケモンを構築する（すべて revealed=False の初期状態）。"""
    mon = Pokemon(
        "ピカチュウ",
        nature="ようき",
        ability_name="せいでんき",   # ピカチュウは2種の特性を持つため隠蔽対象になる
        item_name="たべのこし",
        move_names=["でんこうせっか", "10まんボルト"],
        tera_type="ほのお",          # 基本タイプ（でんき）と異なるテラスタイプ
    )
    mon.set_effort_at(0, 10)  # HP努力値
    return mon


def test_観測で相手の性格と努力値が隠蔽される():
    """性格・努力値は常に非公開情報として無補正（まじめ・努力値0）に隠蔽される。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[_build_hidden_pokemon()],
    )
    observer, _ = battle.players

    obs = battle.build_observation(observer)
    masked = obs.player_states[obs.opponent(observer)].team[0]

    assert masked._nature == "まじめ"
    assert masked._effort == [0] * 6


def test_観測で相手のHP割合が維持される():
    """努力値マスキングで最大HPが変わっても、observerに見えるHP割合は実際の値と一致する（絶対量ではない）。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[_build_hidden_pokemon()],
    )
    observer, _ = battle.players
    opponent = battle.actives[1]
    real_max_hp = opponent.max_hp
    battle.modify_hp(opponent, v=-(real_max_hp // 3))
    real_hp = opponent.hp

    obs = battle.build_observation(observer)
    masked = obs.player_states[obs.opponent(observer)].team[0]

    assert masked.max_hp != real_max_hp  # 前提: 努力値マスキングで最大HPが変わる
    assert masked.hp != real_hp  # 絶対量をそのまま維持すると割合がずれてしまう
    assert abs(masked.hp / masked.max_hp - real_hp / real_max_hp) < 0.01


def test_観測で相手の未テラスタルのテラスタイプが基本タイプに隠蔽される():
    """テラスタル前は実際のテラスタイプではなく基本タイプが observer から見える。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[_build_hidden_pokemon()],
    )
    observer, _ = battle.players
    opponent = battle.actives[1]
    assert not opponent.terastallized
    assert opponent.tera_type == "ほのお"  # 本来のテラスタイプ（非公開）

    obs = battle.build_observation(observer)
    masked = obs.player_states[obs.opponent(observer)].team[0]

    assert masked.tera_type == masked.base_types[0]
    assert masked.tera_type != "ほのお"


def test_観測で相手の未公開の技が隠蔽され公開済みの技のみ見える():
    """revealed=False の技はリストから除外され、公開済みの技のみ observer から見える。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[_build_hidden_pokemon()],
    )
    observer, _ = battle.players
    opponent = battle.actives[1]
    # 1本目の技のみ公開済みという状況を再現する
    opponent.moves[0].revealed = True
    assert not opponent.moves[1].revealed

    obs = battle.build_observation(observer)
    masked = obs.player_states[obs.opponent(observer)].team[0]

    masked_names = [m.name for m in masked.moves]
    assert masked_names == ["でんこうせっか"]
    assert "10まんボルト" not in masked_names


def test_観測で相手の非公開アイテムが隠蔽される():
    """revealed=False のアイテムは observer 視点で空（未判明）になる。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[_build_hidden_pokemon()],
    )
    observer, _ = battle.players
    opponent = battle.actives[1]
    assert not opponent.item.revealed  # 前提: まだ公開されていない

    obs = battle.build_observation(observer)
    masked = obs.player_states[obs.opponent(observer)].team[0]

    assert masked.item.name == ""
    assert masked.item.base_name == ""


def test_観測で相手の非公開特性が隠蔽される():
    """revealed=False かつ複数特性を持つ場合、特性名が observer 視点で空になる。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[_build_hidden_pokemon()],
    )
    observer, _ = battle.players
    opponent = battle.actives[1]
    assert not opponent.ability.revealed  # 前提: まだ公開されていない

    obs = battle.build_observation(observer)
    masked = obs.player_states[obs.opponent(observer)].team[0]

    assert masked.ability.name == ""
    assert masked.ability.base_name == ""


def test_観測は自分自身の情報を隠蔽しない():
    """build_observation は相手側のみを隠蔽し、observer 自身のチームは変化しない。"""
    battle = t.start_battle(
        team0=[_build_hidden_pokemon()],
        team1=[Pokemon("フシギダネ")],
    )
    observer, _ = battle.players

    obs = battle.build_observation(observer)
    own = obs.player_states[observer].team[0]

    assert own.item.name == "たべのこし"
    assert own.ability.name == "せいでんき"
    assert [m.name for m in own.moves] == ["でんこうせっか", "10まんボルト"]
    assert own.tera_type == "ほのお"
    assert own._nature == "ようき"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
