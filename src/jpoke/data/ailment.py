from jpoke.enums import DomainEvent, Event, LethalEvent
from jpoke.core.lethal import LethalHandler
from jpoke.handlers import ailment as h
from jpoke.handlers import lethal as l
from .models import AilmentData


def common_setup():
    """共通のセットアップ処理"""
    for name in AILMENTS:
        # name属性をセット
        AILMENTS[name].name = name


AILMENTS: dict[str, AilmentData] = {
    "": AilmentData(),
    "どく": AilmentData(
        handlers={
            Event.ON_TURN_END: h.AilmentHandler(
                h.どく_damage,
                subject_spec="source:self",
                priority=90,
            )
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(
                func=l.どく_damage,
                subject="defender",
            )
        }
    ),
    "もうどく": AilmentData(
        handlers={
            Event.ON_TURN_END: h.AilmentHandler(
                h.もうどく_damage,
                subject_spec="source:self",
                priority=90,
            )
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(
                func=l.もうどく_damage,
                subject="defender",
            )
        }
    ),
    "まひ": AilmentData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.AilmentHandler(
                h.まひ_speed,
                subject_spec="source:self",
            ),
            Event.ON_TRY_ACTION: h.AilmentHandler(
                h.まひ_action,
                subject_spec="attacker:self",
                priority=120,
            )
        }
    ),
    "やけど": AilmentData(
        handlers={
            Event.ON_CALC_BURN_MODIFIER: h.AilmentHandler(
                h.やけど_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END: h.AilmentHandler(
                h.やけど_damage,
                subject_spec="source:self",
                priority=100,
            )
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(
                func=l.やけど_damage,
                subject="defender",
            )
        }
    ),
    "ねむり": AilmentData(
        is_sleep=True,
        handlers={
            Event.ON_TRY_ACTION: h.AilmentHandler(
                h.ねむり_check_action,
                subject_spec="attacker:self",
                priority=10,
            ),
        }
    ),
    "こおり": AilmentData(
        handlers={
            Event.ON_TRY_ACTION: h.AilmentHandler(
                h.こおり_action,
                subject_spec="attacker:self",
                priority=10,
            ),
            Event.ON_DAMAGE_HIT: h.AilmentHandler(
                h.こおり_cure_by_thaw_move,
                subject_spec="defender:self",
                allow_fainted_subject=True,  # 解凍対象がほのお技でひんしになった場合でも解凍自体は発生する
            )
        }
    ),
    "ゆめうつつ": AilmentData(
        is_sleep=True,
        uncurable=True,
    ),
}


common_setup()
