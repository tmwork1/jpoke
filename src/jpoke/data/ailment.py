from jpoke.core.event import Event, Handler
from .models import AilmentData
from jpoke.handlers import ailment as hdl


AILMENTS: dict[str, AilmentData] = {
    "": AilmentData(),
    "どく": AilmentData(
        handlers={
        }
    ),
    "もうどく": AilmentData(
        handlers={
        }
    ),
    "まひ": AilmentData(),
    "やけど": AilmentData(),
    "ねむり": AilmentData(),
    "こおり": AilmentData(),
}
