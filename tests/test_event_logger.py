import pytest

from jpoke.core.event_logger import EventLog
from jpoke.enums import LogCode


@pytest.mark.parametrize("log", list(LogCode))
def test_event_log_render_covers_all_log_codes(log: LogCode):
    event = EventLog(turn=1, idx=0, log=log, payload={})
    text = event.render()
    assert isinstance(text, str)


def test_event_log_render_without_payload_uses_base_text():
    event = EventLog(turn=1, idx=0, log=LogCode.GAME_STARTED)
    assert event.render() == "バトル開始"


def test_event_log_render_with_reason_suffix():
    event = EventLog(
        turn=1,
        idx=0,
        log=LogCode.MOVE_FAILED,
        payload={"reason": "ねむり"},
    )
    assert event.render() == "技は失敗した [ねむり]"
