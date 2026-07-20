"""状態異常ハンドラの単体テスト"""
import enum

import pytest

import jpoke.core.battle as battle_module
from jpoke.core.handler import Handler
from jpoke.core.player import Player
from jpoke.enums import Event, Interrupt
from jpoke.model import Pokemon

from . import test_utils as t

# 共有されていても問題ない型（不変オブジェクト・設計上共有する参照）
_ATOMIC_TYPES = (str, int, float, bool, bytes, type(None), frozenset, enum.Enum)

def _is_shared_ok(obj) -> bool:
    """コピー間で同一オブジェクトを共有してよいかを判定する。"""
    if isinstance(obj, _ATOMIC_TYPES):
        return True
    if callable(obj) and not hasattr(obj, "__dict__"):
        # 関数・メソッド・組み込み呼び出し可能オブジェクト
        return True
    cls = type(obj)
    module = getattr(cls, "__module__", "")
    # 図鑑・技・特性・アイテム等の静的データは共有が正
    if module.startswith("jpoke.data"):
        return True
    # Player（およびそのサブクラス）と Handler 定義はコピー間で共有する設計
    if isinstance(obj, (Player, Handler)):
        return True
    if callable(obj):
        return True
    return False

def _find_shared_mutables(old, new, path="battle", seen=None, findings=None):
    """コピー元とコピー先のオブジェクトグラフを並行に歩き、
    可変オブジェクトが共有されているパスを列挙する。"""
    if seen is None:
        seen = set()
    if findings is None:
        findings = []

    pair = (id(old), id(new))
    if pair in seen:
        return findings
    seen.add(pair)

    if old is None and new is None:
        return findings

    if old is new:
        if not isinstance(old, tuple) and not _is_shared_ok(old):
            findings.append(f"{path}: {type(old).__name__} が共有されている")
            return findings
        if not isinstance(old, tuple):
            return findings
        # 不変コンテナ（tuple）は中身を検査する

    if isinstance(old, (list, tuple)):
        if len(old) == len(new):
            for i, (o, n) in enumerate(zip(old, new)):
                _find_shared_mutables(o, n, f"{path}[{i}]", seen, findings)
        else:
            findings.append(f"{path}: 要素数が異なる ({len(old)} != {len(new)})")
        return findings

    if isinstance(old, dict):
        if set(map(id, old)) == set(map(id, new)) or set(old) == set(new):
            for key in old:
                _find_shared_mutables(
                    old[key], new[key], f"{path}[{key!r}]", seen, findings
                )
        return findings

    if isinstance(old, (set, frozenset)) or _is_shared_ok(old):
        return findings

    # 通常のオブジェクト: __dict__ を並行に歩く
    old_vars = getattr(old, "__dict__", None)
    new_vars = getattr(new, "__dict__", None)
    if old_vars and new_vars is not None:
        for key in old_vars:
            if key in new_vars:
                _find_shared_mutables(
                    old_vars[key], new_vars[key], f"{path}.{key}", seen, findings
                )
    return findings


def test_copy_logsFalseでdeepcopy中に例外が発生しても複製元のログが復元される():
    """copy_logs=False の実装は deepcopy 実行前に複製元の event_logger/command_log を
    一時的に空へ差し替え、完了後に finally で復元する。deepcopy 自体が例外を送出した
    場合でも、finally によって複製元のログが元通り復元されることを確認する（r7-8回帰）。"""
    old = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("フシギダネ")],
        accuracy=100,
    )
    t.run_move(old, 0)
    orig_event_logger = old.event_logger
    orig_command_log = old.command_log
    orig_logs = list(old.event_logger.logs)
    assert orig_logs

    def boom(*args, **kwargs):
        raise RuntimeError("deepcopy failure (test)")

    real_deepcopy = battle_module.deepcopy
    battle_module.deepcopy = boom
    try:
        with pytest.raises(RuntimeError):
            old.copy(copy_logs=False)
    finally:
        battle_module.deepcopy = real_deepcopy

    # 複製元のログは同一オブジェクトのまま、内容も変わっていない
    assert old.event_logger is orig_event_logger
    assert old.command_log is orig_command_log
    assert old.event_logger.logs == orig_logs


def test_copy_logsFalseで複製元のログが変更されずかつ複製先への書き込みが波及しない():
    """copy_logs=False で複製した後、複製元のログ内容が変わらないこと、
    かつ複製先へ書き込んでも複製元へ波及しないことを確認する（r7-8回帰）。"""
    old = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("フシギダネ")],
        accuracy=100,
    )
    t.run_move(old, 0)
    old_logs_before = list(old.event_logger.logs)

    new = old.copy(copy_logs=False)

    # 複製直後、複製元のログは変更されていない
    assert old.event_logger.logs == old_logs_before

    # 複製先へ書き込んでも複製元は汚染されない
    t.run_move(new, 0)
    assert new.event_logger.logs
    assert old.event_logger.logs == old_logs_before


def test_copy_logsFalseで複製先のログが空になる():
    """copy_logs=False の場合、複製先の event_logger/command_log は
    対戦開始からの履歴を引き継がず空で始まることを確認する（r7-8回帰）。"""
    old = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("フシギダネ")],
        accuracy=100,
    )
    t.run_move(old, 0)
    assert old.event_logger.logs

    new = old.copy(copy_logs=False)

    assert new.event_logger.logs == []
    assert new.command_log == []
    # 複製先は複製元と独立した新規のログオブジェクトを持つ（共有参照ではない）
    assert new.event_logger is not old.event_logger
    assert new.command_log is not old.command_log


def test_copy_logsTrueで従来通りログの全履歴が引き継がれる():
    """copy_logs=True（既定）の場合、event_logger/command_log の
    対戦開始からの全履歴が複製先に引き継がれることを確認する（r7-8回帰）。"""
    old = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("フシギダネ")],
        accuracy=100,
    )
    t.run_move(old, 0)
    assert old.event_logger.logs

    new = old.copy()

    assert len(new.event_logger.logs) == len(old.event_logger.logs)
    assert new.event_logger is not old.event_logger
    assert new.event_logger.logs == old.event_logger.logs


def test_mon():
    """pokemonのコピーが正しく行われることを確認する。"""
    old = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="たべのこし"), Pokemon("ヒトカゲ")],
        team1=[Pokemon("フシギダネ")],
    )
    new = old.copy()

    assert new is not old
    assert new.actives[0] is not old.actives[0]
    assert new.actives[0].item.name == "たべのこし"
    assert new.actives[0].item is not old.actives[0].item
    assert new._player_states[0].team[0] is not old._player_states[0].team[0]

    old_handler = old.events.handlers[Event.ON_TURN_END][0]
    new_handler = new.events.handlers[Event.ON_TURN_END][0]
    assert old_handler is not new_handler
    assert new_handler.registered_subject is new.actives[0]

    # コピー後のEventContextでハンドラが正しく除去されることを確認する
    t.run_switch(new, 0, 1)
    assert new.actives[0].name == "ヒトカゲ"
    assert new.events.handlers == {}


def test_terrain():
    """地形のコピーが正しく行われることを確認する。"""
    old = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("フシギダネ")],
        terrain=("グラスフィールド", 2),
    )
    old.actives[0].hp = 1
    assert Event.ON_TURN_END in old.events.handlers

    new = old.copy()
    assert new.terrain is not old.terrain

    t.end_turn(new)
    assert new.terrain.count == 1
    assert old.terrain.count == 2
    assert old.actives[0].hp == 1
    assert new.actives[0].hp > 1


def test_weather():
    """天候のコピーが正しく行われることを確認する。"""
    old = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("フシギダネ")],
        weather=("すなあらし", 2),
    )
    new = old.copy()
    assert new.weather is not old.weather

    # newの天候が正しく機能することを確認する
    t.end_turn(new)
    assert new.weather.count == 1
    assert old.weather.count == 2
    assert new.actives[0].hp < new.actives[0].max_hp
    assert old.actives[0].hp == old.actives[0].max_hp


def test_コピー後に可変状態が共有されない():
    """Battle.copy() 後、元と複製の間で可変オブジェクトが共有されないことを
    オブジェクトグラフ走査で機械的に検証する（新規属性の追加にも自動追従する）。"""
    old = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", item_name="たべのこし", move_names=["たいあたり"]),
            Pokemon("ヒトカゲ"),
        ],
        team1=[Pokemon("フシギダネ", move_names=["やどりぎのタネ"])],
        weather=("すなあらし", 3),
        terrain=("グラスフィールド", 3),
        accuracy=100,
    )
    t.run_move(old, 0)

    new = old.copy()

    findings = _find_shared_mutables(old, new)
    assert not findings, (
        "コピー間で共有されている可変オブジェクト:\n" + "\n".join(findings)
    )


def test_木探索用の観測でswitchフェーズ中の相手コマンドがrequired_command_typeでフィルタされる():
    """相手のベンチが公開済みでも、switch フェーズ中に required_command_type が
    "move" の間は観測される相手の合法手に SWITCH コマンドが混入しないことを確認する。

    修正前は公開状況（revealed）のみでフィルタしており、木探索が
    battle.get_available_commands(opponent) をそのまま itertools.product() 等に
    渡すと sim.step() の validate_command() に弾かれて ValueError になっていた
    （.internal/review/code/tree_search.md CRIT-1）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とんぼがえり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("ゼニガメ", move_names=["たいあたり"]), Pokemon("カメックス")],
        accuracy=100,
    )
    player0, player1 = battle.players
    # player1のベンチ（カメックス）と技（たいあたり）が既に公開済みという想定
    battle.player_states[player1].team[1].revealed = True
    battle.actives[1].moves[0].revealed = True
    # player0が先攻でこのターンの行動順が確定している想定
    battle.turn_controller.action_order = [0, 1]
    # 通常のターン開始時にresolve_command("action")が記録するスナップショットを再現する
    # （ベンチが生存しているためSWITCH_xも含む）
    battle.player_states[player1].last_available_commands = (
        battle.command_manager.available_action_commands(player1)
    )

    t.run_move(battle, 0)
    assert battle.player_states[player0].interrupt == Interrupt.PIVOT

    captured = {}
    original_choose = player0.choose_command

    def spy_choose(b):
        if b.phase == "switch":
            opponent = b.opponent(player0)
            captured["commands"] = b.get_available_commands(opponent)
            captured["required_command_type"] = b.player_states[opponent].required_command_type
        return original_choose(b)

    player0.choose_command = spy_choose

    battle.switch_manager.run_interrupt_switch(Interrupt.PIVOT)

    assert captured["required_command_type"] == "move"
    assert captured["commands"]
    assert all(cmd.is_move for cmd in captured["commands"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
