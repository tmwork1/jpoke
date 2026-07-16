from jpoke.enums import DomainEvent, Event, LethalEvent
from jpoke.core.lethal import LethalHandler
from jpoke.handlers import field as h
from jpoke.handlers import lethal as l
from ..models import FieldData

TERRAIN: dict[str, FieldData] = {
    "エレキフィールド": FieldData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.FieldHandler(
                h.エレキフィールド_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_BEFORE_APPLY_AILMENT: h.FieldHandler(
                h.エレキフィールド_prevent_sleep,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.FieldHandler(
                h.エレキフィールド_prevent_nemuke,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.tick_terrain,
                subject_spec="source:self",
                priority=140,
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
            ),
        },
    ),
    "グラスフィールド": FieldData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.FieldHandler(
                h.グラスフィールド_power_modifier,
                subject_spec="attacker:self",
            ),
            DomainEvent.ON_MODIFY_MOVE_PRIORITY: h.FieldHandler(
                h.グラスフィールド_boost_move_priority,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END: [
                h.FieldHandler(
                    h.グラスフィールド_heal,
                    subject_spec="source:self",
                    priority=60,
                ),
                h.FieldHandler(
                    h.tick_terrain,
                    subject_spec="source:self",
                    priority=140,
                    allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
                ),
            ]
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(func=l.グラスフィールド_heal)
        }
    ),
    "サイコフィールド": FieldData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.FieldHandler(
                h.サイコフィールド_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_TRY_MOVE_1: h.FieldHandler(
                h.サイコフィールド_block_priority_move,
                priority=100,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.tick_terrain,
                subject_spec="source:self",
                priority=140,
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
            ),
        },
    ),
    "ミストフィールド": FieldData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.FieldHandler(
                h.ミストフィールド_power_modifier,
                subject_spec="defender:self",
            ),
            Event.ON_BEFORE_APPLY_AILMENT: h.FieldHandler(
                h.ミストフィールド_prevent_ailment,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.FieldHandler(
                h.ミストフィールド_prevent_confusion,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.tick_terrain,
                subject_spec="source:self",
                priority=140,
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
            ),
        },
    ),
}
