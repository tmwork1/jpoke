"""EventLogger/EventLog の一般的な挙動のテスト（機械的検証観点の回帰テストを含む）。

回帰テストの由来: docs/review/code/event_log_audit.md
"""
from jpoke import Pokemon
from jpoke.enums import LogCode

from . import test_utils as t


def test_STAT_CHANGE_BLOCKEDにdisplay_reason付きのpayloadが記録される():
    """status_manager.modify_stats: ランクが変化しない場合のSTAT_CHANGE_BLOCKEDに
    display_reasonを持つpayloadが記録されること
    （回帰テスト: event_log_audit。修正前はpayload=Noneで理由が一切分からなかった）
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.boosts["atk"] = 6
    battle.modify_stats(mon, {"atk": 1}, source=mon, reason="つるぎのまい")

    logs = [
        log for log in battle.event_logger.logs
        if log.log == LogCode.STAT_CHANGE_BLOCKED
    ]
    assert len(logs) == 1
    assert logs[0].payload is not None
    assert logs[0].payload.display_reason == "つるぎのまい"


def test_seqが記録順に連番で採番される():
    """EventLog.seq: 記録順に0始まりの連番が振られること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)

    logs = battle.event_logger.logs
    assert len(logs) >= 2
    seqs = [log.seq for log in logs]
    assert seqs == sorted(seqs)
    assert seqs == list(range(len(logs)))
