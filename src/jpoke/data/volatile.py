from functools import partial

from jpoke.utils.enums import Event
from jpoke.handlers import common, volatile as h
from .models import VolatileData


def common_setup() -> None:
    """
    各VOLATILEのハンドラにログ用のテキスト（名前）を設定する。

    この関数は、VOLATILESディクショナリ内の全てのVolatileDataに対して、
    各イベントハンドラにlog_text属性として状態名を設定します。
    これにより、ハンドラ実行時のログ出力で状態名を表示できます。

    呼び出しタイミング: モジュール初期化時（ファイル末尾）
    """
    for name, data in VOLATILES.items():
        for event in data.handlers:
            data.handlers[event].log_text = name


VOLATILES: dict[str, VolatileData] = {
    "": VolatileData(),
    "みがわり": VolatileData(
        handlers={
            # TODO: みがわりのハンドラを実装
            # みがわりが攻撃を受ける、技を防ぐなどの処理
        }
    ),
    "アクアリング": VolatileData(
        handlers={
            # TODO: アクアリングのハンドラを実装
        }
    ),
    "あめまみれ": VolatileData(
        handlers={
            # TODO: あめまみれのハンドラを実装
        }
    ),
    "アンコール": VolatileData(
        handlers={
            # TODO: アンコールのハンドラを実装
            # 技選択時に同じ技を強制する処理
        }
    ),
    "うちおとす": VolatileData(
        handlers={
            # TODO: うちおとすのハンドラを実装
        }
    ),
    "かいふくふうじ": VolatileData(
        handlers={
            # TODO: かいふくふうじのハンドラを実装
        }
    ),
    "かなしばり": VolatileData(
        handlers={
            Event.ON_BEFORE_MOVE: h.VolatileHandler(
                h.かなしばり_before_move,
                subject_spec="target:self",
                priority=200
            ),
            Event.ON_TURN_END_5: h.VolatileHandler(
                h.かなしばり_turn_end,
                subject_spec="source:self",
                log="never"
            ),
        }
    ),
    "急所ランク": VolatileData(
        handlers={
            # TODO: 急所ランクのハンドラを実装
        }
    ),
    "こんらん": VolatileData(
        handlers={
            Event.ON_BEFORE_ACTION: h.VolatileHandler(
                h.こんらん_action,
                subject_spec="target:self",
                priority=200
            ),
        }
    ),
    "しおづけ": VolatileData(
        handlers={
            # TODO: しおづけのハンドラを実装
        }
    ),
    "じごくずき": VolatileData(
        handlers={
            # TODO: じごくずきのハンドラを実装
        }
    ),
    "じゅうでん": VolatileData(
        handlers={
            # TODO: じゅうでんのハンドラを実装
        }
    ),
    "たくわえる": VolatileData(
        handlers={
            # TODO: たくわえるのハンドラを実装
        }
    ),
    "ちょうはつ": VolatileData(
        handlers={
            Event.ON_BEFORE_MOVE: h.VolatileHandler(
                h.ちょうはつ_before_move,
                subject_spec="target:self",
                priority=200
            ),
            Event.ON_TURN_END_5: h.VolatileHandler(
                h.ちょうはつ_turn_end,
                subject_spec="source:self",
                log="never"
            ),
        }
    ),
    "でんじふゆう": VolatileData(
        handlers={
            # TODO: でんじふゆうのハンドラを実装
        }
    ),
    "にげられない": VolatileData(
        handlers={
            # TODO: にげられないのハンドラを実装
        }
    ),
    "ねむけ": VolatileData(
        handlers={
            # TODO: ねむけのハンドラを実装
        }
    ),
    "ねをはる": VolatileData(
        handlers={
            # TODO: ねをはるのハンドラを実装
        }
    ),
    "のろい": VolatileData(
        handlers={
            # TODO: のろいのハンドラを実装
        }
    ),
    "バインド": VolatileData(
        handlers={
            Event.ON_TURN_END_4: h.VolatileHandler(
                h.バインド_turn_end,
                subject_spec="source:self"
            ),
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.バインド_before_switch,
                subject_spec="source:self",
                log="never",
                priority=200
            ),
        }
    ),
    "ほろびのうた": VolatileData(
        handlers={
            # TODO: ほろびのうたのハンドラを実装
        }
    ),
    "みちづれ": VolatileData(
        handlers={
            # TODO: みちづれのハンドラを実装
        }
    ),
    "メロメロ": VolatileData(
        handlers={
            Event.ON_BEFORE_ACTION: h.VolatileHandler(
                h.メロメロ_action,
                subject_spec="target:self",
                priority=200
            ),
        }
    ),
    "やどりぎのタネ": VolatileData(
        handlers={
            Event.ON_TURN_END_4: h.VolatileHandler(
                partial(common.drain_hp, from_="source:self", r=1/8),
                subject_spec="source:self",
            ),
        }
    ),
}


common_setup()
