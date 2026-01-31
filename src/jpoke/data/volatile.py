from functools import partial
from jpoke.core.event import Event, Handler
from .models import VolatileData
from jpoke.handlers import common, volatile as h


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
            # TODO: かなしばりのハンドラを実装
        }
    ),
    "急所ランク": VolatileData(
        handlers={
            # TODO: 急所ランクのハンドラを実装
        }
    ),
    "こんらん": VolatileData(
        handlers={
            # TODO: こんらんのハンドラを実装
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
            # TODO: ちょうはつのハンドラを実装
            # 変化技の使用を防ぐ処理
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
            # TODO: バインド系技のハンドラを実装
            # ターン終了時のダメージ、交代制限など
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
            # TODO: メロメロのハンドラを実装
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
