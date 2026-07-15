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
    mon.set_evs_at(0, 10)  # HP努力値
    return mon


def test_観測でcopy_logsFalse指定時に複製元のログが変更されない():
    """copy_logs=False で観測用コピーを作った後も、複製元 battle のログ内容が
    変わらないことを確認する（r10-5回帰）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("フシギダネ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    observer, _ = battle.players
    logs_before = list(battle.event_logger.logs)
    command_log_before = list(battle.command_log)

    obs = battle.build_observation(observer, copy_logs=False)

    assert battle.event_logger.logs == logs_before
    assert battle.command_log == command_log_before
    assert battle.event_logger is not obs.event_logger

    # 複製先へ書き込んでも複製元は汚染されない
    t.run_move(obs, 0)
    assert obs.event_logger.logs
    assert battle.event_logger.logs == logs_before


def test_観測でcopy_logsFalse指定時に複製先のログが空になる():
    """build_observation(observer, copy_logs=False) の場合、複製先の
    event_logger/command_log は対戦開始からの履歴を引き継がず空で始まることを
    確認する（r10-5回帰）。observation_builder.build() が Battle.copy() と同じ
    「ログを一時的に空へ差し替えてから deepcopy する」最適化を再利用しているか
    が検証対象。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("フシギダネ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    observer, _ = battle.players
    assert battle.event_logger.logs

    obs = battle.build_observation(observer, copy_logs=False)

    assert obs.event_logger.logs == []
    assert obs.command_log == []
    # 複製先は複製元と独立した新規のログオブジェクトを持つ（共有参照ではない）
    assert obs.event_logger is not battle.event_logger
    assert obs.command_log is not battle.command_log


def test_観測でcopy_logs省略時は従来通り全履歴が引き継がれる():
    """copy_logs を省略した場合（既定 True）、従来通り event_logger/command_log の
    対戦開始からの全履歴が観測用コピーに引き継がれることを確認する（r10-5回帰）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("フシギダネ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    observer, _ = battle.players
    assert battle.event_logger.logs

    obs = battle.build_observation(observer)

    assert len(obs.event_logger.logs) == len(battle.event_logger.logs)
    assert obs.event_logger is not battle.event_logger
    assert obs.event_logger.logs == battle.event_logger.logs


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
    assert masked._evs == [0] * 6


def test_観測で相手の未テラスタルのテラスタイプが基本タイプに隠蔽される():
    """テラスタル前は実際のテラスタイプではなく基本タイプが observer から見える。"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ")],
        team1=[_build_hidden_pokemon()],
    )
    observer, _ = battle.players
    opponent = battle.actives[1]
    assert not opponent.is_terastallized
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


def test_観測済みの盤面でもcopy_logsが伝播する():
    """is_observation() が真の盤面（既に観測用コピー済みの Battle）に対して
    build_observation() を呼んだ場合、self.copy(copy_logs=copy_logs) 経由で
    copy_logs が正しく伝播することを確認する（r10-5回帰）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("フシギダネ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    observer, _ = battle.players

    obs = battle.build_observation(observer)
    assert obs.is_observation()
    assert obs.event_logger.logs

    # copy_logs=False: 既に観測済みの盤面をさらに複製してもログを引き継がない
    obs_no_logs = obs.build_observation(observer, copy_logs=False)
    assert obs_no_logs.event_logger.logs == []
    assert obs_no_logs.command_log == []
    assert obs.event_logger.logs  # 複製元（観測済み盤面）は変更されない

    # copy_logs=True（既定）: 観測済みの盤面からでも全履歴が引き継がれる
    obs_with_logs = obs.build_observation(observer)
    assert obs_with_logs.event_logger.logs == obs.event_logger.logs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
