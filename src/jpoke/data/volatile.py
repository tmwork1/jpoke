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
            # 複雑な実装が必要なため後回し
        }
    ),
    "アクアリング": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(common.heal_hp, from_="source:self", r=1/16),
                subject_spec="source:self",
                priority=10,
            ),
        }
    ),
    "あめまみれ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.あめまみれ_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "アンコール": VolatileData(
        handlers={
            # TODO: アンコールのハンドラを実装
            # 技選択時に同じ技を強制する処理（複雑なため後回し）
        }
    ),
    "うちおとす": VolatileData(
        handlers={
            # 飛行タイプとふゆう特性を無効化（常駐効果）
            # 技の効果で適用されるため、ハンドラは不要
        }
    ),
    "かいふくふうじ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.かいふくふうじ_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "かなしばり": VolatileData(
        handlers={
            Event.ON_BEFORE_MOVE: h.VolatileHandler(
                h.かなしばり_before_move,
                subject_spec="target:self",
                log="on_success",
                priority=200
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.かなしばり_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "急所ランク": VolatileData(
        handlers={
            # TODO: 急所ランクのハンドラを実装
            # 急所率計算に影響（ダメージ計算システムと連携するため後回し）
        }
    ),
    "こんらん": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.こんらん_action,
                subject_spec="target:self",
                log="on_success",
                priority=110
            ),
        }
    ),
    "しおづけ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(common.drain_hp, from_="source:self", r=1/8),
                subject_spec="source:self",
                priority=90,
            ),
        }
    ),
    "じごくずき": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.じごくずき_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "じゅうでん": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.じゅうでん_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "たくわえる": VolatileData(
        handlers={
            # TODO: たくわえるのハンドラを実装
            # 防御ランク上昇の管理が必要（複雑なため後回し）
        }
    ),
    "ちょうはつ": VolatileData(
        handlers={
            Event.ON_BEFORE_MOVE: h.VolatileHandler(
                h.ちょうはつ_before_move,
                subject_spec="target:self",
                log="on_success",
                priority=200
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.ちょうはつ_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "でんじふゆう": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.でんじふゆう_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "にげられない": VolatileData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.にげられない_check_trapped,
                subject_spec="source:self",
                log="on_success",
                priority=200
            ),
        }
    ),
    "ねむけ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.ねむけ_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "ねをはる": VolatileData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.ねをはる_check_trapped,
                subject_spec="source:self",
                log="on_success",
                priority=200
            ),
        }
    ),
    "のろい": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(common.drain_hp, from_="source:self", r=1/4),
                subject_spec="source:self",
                priority=70,
            ),
        }
    ),
    "バインド": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.バインド_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=70
            ),
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.バインド_before_switch,
                subject_spec="source:self",
                log="on_success",
                priority=200
            ),
        }
    ),
    "ほろびのうた": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.ほろびのうた_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=110
            ),
        }
    ),
    "みちづれ": VolatileData(
        handlers={
            # TODO: みちづれのハンドラを実装
            # ひんしイベントで相手をひんしにする（複雑なため後回し）
        }
    ),
    "メロメロ": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.メロメロ_action,
                subject_spec="target:self",
                log="on_success",
                priority=130
            ),
        }
    ),
    "やどりぎのタネ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(common.drain_hp, from_="source:self", r=1/8),
                subject_spec="source:self",
                priority=20,
            ),
        }
    ),
}


common_setup()
