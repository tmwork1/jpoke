from jpoke.core.event import Event, Handler
from .models import AilmentData
from jpoke.handlers import ailment as hdl


AILMENTS: dict[str, AilmentData] = {
    "": AilmentData(),
    "どく": AilmentData(
        handlers={Event.ON_TURN_END_4: Handler(hdl.どく, subject_spec="source:self")},
    ),
    "もうどく": AilmentData(
        handlers={Event.ON_TURN_END_4: Handler(hdl.もうどく, subject_spec="source:self")},
    ),
    "まひ": AilmentData(),
    "やけど": AilmentData(),
    "ねむり": AilmentData(),
    "こおり": AilmentData(),
}
