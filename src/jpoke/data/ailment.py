from jpoke.core.event import Event, Handler
from .models import AilmentData
from jpoke.handlers import ailment as hdl


AILMENTS: dict[str, AilmentData] = {
    "": AilmentData(),
    "どく": AilmentData(
        handlers={Event.ON_TURN_END_4: Handler(hdl.どく)},
    ),
    "もうどく": AilmentData(
        handlers={Event.ON_TURN_END_4: Handler(hdl.もうどく)},
    ),
    "まひ": AilmentData(),
    "やけど": AilmentData(),
    "ねむり": AilmentData(),
    "こおり": AilmentData(),
}
