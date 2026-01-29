from functools import partial
from jpoke.core.event import Event, Handler
from .models import AilmentData
from jpoke.handlers import common, ailment as h


AILMENTS: dict[str, AilmentData] = {
    "": AilmentData(),
    "どく": AilmentData(
        handlers={
            Event.ON_TURN_END_4: h.AilmentHandler(
                partial(
                    common.modify_hp, target_spec="target:self", r=-1/8
                ),
                subject_spec="target:self",
            )
        }
    ),
    "もうどく": AilmentData(
        handlers={
            Event.ON_TURN_END_4: h.AilmentHandler(
                h.もうどく,
                subject_spec="target:self",
            )
        }
    ),
    "まひ": AilmentData(),
    "やけど": AilmentData(),
    "ねむり": AilmentData(),
    "こおり": AilmentData(),
}
