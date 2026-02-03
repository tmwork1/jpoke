from functools import partial
from jpoke.core.event import Event, Handler
from .models import AilmentData
from jpoke.handlers import common, ailment as h


AILMENTS: dict[str, AilmentData] = {
    "": AilmentData(),
    "どく": AilmentData(
        handlers={
            Event.ON_TURN_END_3: h.AilmentHandler(
                partial(
                    common.modify_hp, target_spec="target:self", r=-1/8
                ),
                subject_spec="target:self",
                priority=30,
            )
        }
    ),
    "もうどく": AilmentData(
        handlers={
            Event.ON_TURN_END_3: h.AilmentHandler(
                h.もうどく,
                subject_spec="target:self",
                priority=30,
            )
        }
    ),
    "まひ": AilmentData(
        handlers={
            Event.ON_CALC_SPEED: h.AilmentHandler(
                h.まひ_speed,
                subject_spec="target:self",
                log="never",
            ),
            Event.ON_TRY_ACTION: h.AilmentHandler(
                h.まひ_action,
                subject_spec="target:self",
                log="never",
                priority=120,
            )
        }
    ),
    "やけど": AilmentData(
        handlers={
            Event.ON_CALC_BURN_MODIFIER: h.AilmentHandler(
                h.やけど_burn,
                subject_spec="attacker:self",
                log="never",
            ),
            Event.ON_TURN_END_3: h.AilmentHandler(
                h.やけど_damage,
                subject_spec="target:self",
                priority=40,
            )
        }
    ),
    "ねむり": AilmentData(
        handlers={
            Event.ON_TRY_ACTION: h.AilmentHandler(
                h.ねむり_action,
                subject_spec="target:self",
                log="never",
                priority=10,
            )
        }
    ),
    "こおり": AilmentData(
        handlers={
            Event.ON_TRY_ACTION: h.AilmentHandler(
                h.こおり_action,
                subject_spec="target:self",
                log="never",
                priority=10,
            )
        }
    ),
}
